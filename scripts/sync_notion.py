#!/usr/bin/env python3
"""
Thursday Studio — Daily Notion Sync Script
Fetches latest jobs, production calendar tasks, and daily notes from Notion API
and updates index.html for daily GitHub Pages auto-deploy.
"""

import os
import sys
import re
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

# Thai Localization Helpers
THAI_MONTHS = [
    '', 'ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
    'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'
]
THAI_DAYS = ['จันทร์', 'อังคาร', 'พุธ', 'พฤหัสบดี', 'ศุกร์', 'เสาร์', 'อาทิตย์']

ICT_TZ = timezone(timedelta(hours=7))

def get_now_ict():
    return datetime.now(ICT_TZ)

def format_thai_date(dt_str, include_year=False):
    if not dt_str:
        return ''
    try:
        parts = dt_str.split('T')[0].split('-')
        year = int(parts[0])
        month = int(parts[1])
        day = int(parts[2])
        month_name = THAI_MONTHS[month]
        if include_year:
            return f"{day} {month_name} {year + 543 if year < 2500 else year}"
        return f"{day} {month_name}"
    except Exception:
        return dt_str

def get_rich_text(prop):
    if not prop:
        return ''
    ptype = prop.get('type')
    if ptype == 'title':
        items = prop.get('title', [])
    elif ptype == 'rich_text':
        items = prop.get('rich_text', [])
    else:
        return ''
    return ''.join([item.get('plain_text', '') for item in items]).strip()

def get_select(prop):
    if not prop:
        return ''
    ptype = prop.get('type')
    if ptype == 'select':
        sel = prop.get('select')
        return sel.get('name', '') if sel else ''
    if ptype == 'status':
        stat = prop.get('status')
        return stat.get('name', '') if stat else ''
    return ''

def get_number(prop):
    if not prop:
        return 0
    return prop.get('number') or 0

def get_date(prop):
    if not prop:
        return None
    d = prop.get('date')
    if not d:
        return None
    return d.get('start')

def notion_api_request(endpoint, token, method='GET', payload=None):
    url = f"https://api.notion.com/v1/{endpoint}"
    headers = {
        'Authorization': f'Bearer {token}',
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    }
    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='ignore')
        print(f"Notion API error [{e.code}] on {endpoint}: {err_body}", file=sys.stderr)
        raise

def fetch_all_database_pages(database_id, token):
    pages = []
    has_more = True
    next_cursor = None
    clean_id = database_id.replace('-', '')
    while has_more:
        body = {}
        if next_cursor:
            body['start_cursor'] = next_cursor
        res = notion_api_request(f"databases/{clean_id}/query", token, method='POST', payload=body)
        pages.extend(res.get('results', []))
        has_more = res.get('has_more', False)
        next_cursor = res.get('next_cursor')
    return pages

def fetch_page_blocks(page_id, token):
    clean_id = page_id.replace('-', '')
    blocks = []
    has_more = True
    next_cursor = None
    while has_more:
        url = f"blocks/{clean_id}/children"
        if next_cursor:
            url += f"?start_cursor={next_cursor}"
        res = notion_api_request(url, token, method='GET')
        blocks.extend(res.get('results', []))
        has_more = res.get('has_more', False)
        next_cursor = res.get('next_cursor')
    return blocks

def process_jobs(pages):
    jobs = []
    now = get_now_ict().date()

    for p in pages:
        pid = p.get('id', '').replace('-', '')
        props = p.get('properties', {})

        # Flexible property lookups (Thai with English fallback)
        name = (get_rich_text(props.get('ชื่องาน / แคมเปญ')) or 
                get_rich_text(props.get('Name')) or 
                get_rich_text(props.get('Title')))
        if not name:
            continue

        brand = (get_rich_text(props.get('แบรนด์ / Agency')) or 
                 get_select(props.get('แบรนด์ / Agency')) or 
                 get_rich_text(props.get('Brand')))
        
        status = (get_select(props.get('สถานะ')) or 
                  get_select(props.get('Status')) or 'ดีลงาน')
        
        channel = (get_select(props.get('ช่อง')) or 
                   get_select(props.get('Channel')) or 'phitccc')
        
        budget = (get_number(props.get('ค่าตัว / รายรับ (บาท)')) or 
                  get_number(props.get('Price')) or 
                  get_number(props.get('Budget')))

        raw_filming = get_date(props.get('วันถ่ายทำ'))
        raw_draft = get_date(props.get('วันส่ง Draft 1'))
        raw_post = get_date(props.get('วันโพสต์งาน'))

        filming_str = format_thai_date(raw_filming) if raw_filming else ('ยังไม่ Book วันถ่าย' if status == 'ถ่ายทำ' else '-')
        draft_str = format_thai_date(raw_draft) if raw_draft else ('ไม่ต้องส่งดราฟ' if 'ไม่ต้องส่ง' in name else 'ยังไม่กำหนด')
        post_str = format_thai_date(raw_post) if raw_post else 'ยังไม่กำหนด'

        # Calculate Priority & Urgency
        priority = 3
        priority_label = 'P3 รอคิว'
        urgent = False
        urgent_reason = ''
        unbooked = False
        waiting_parcel = (status == 'รอพัสดุ')
        tomorrow = False

        # Status specific presets
        if status == 'ดีลงาน':
            priority = 3
            priority_label = 'P3 ดีลงาน'
        elif status == 'รับเงิน':
            priority = 3
            priority_label = 'P3 รอรับเงิน'
        elif status == 'ส่งตรวจ':
            priority = 2
            priority_label = 'P2 รอผลตรวจ'
        elif status == 'ตัดต่อ':
            priority = 1
            priority_label = 'P1 ด่วนมาก'
            tomorrow = True
        elif status == 'ถ่ายทำ':
            if not raw_filming:
                unbooked = True
                priority = 2
                priority_label = 'P2 สำคัญ'
            else:
                try:
                    f_date = datetime.strptime(raw_filming.split('T')[0], '%Y-%m-%d').date()
                    diff = (f_date - now).days
                    if diff <= 1:
                        tomorrow = True
                        priority = 1
                        priority_label = 'P1 ด่วนมาก'
                    elif diff <= 7:
                        priority = 2
                        priority_label = 'P2 สำคัญ'
                except Exception:
                    pass

        # Check Draft Urgency
        if raw_draft and status not in ['ส่งตรวจ', 'โพสต์งาน', 'รับเงิน', 'จบงาน']:
            try:
                d_date = datetime.strptime(raw_draft.split('T')[0], '%Y-%m-%d').date()
                days_left = (d_date - now).days
                if days_left < 0:
                    urgent = True
                    urgent_reason = f"เลยกำหนดส่ง Draft 1 มา {abs(days_left)} วัน ({draft_str})"
                    priority = 1
                    priority_label = 'P1 ด่วนมาก'
                elif days_left <= 2:
                    urgent = True
                    urgent_reason = f"ใกล้ถึงกำหนดส่ง Draft 1 ({draft_str})"
                    priority = 1
                    priority_label = 'P1 ด่วนมาก'
                elif days_left <= 7 and unbooked:
                    urgent = True
                    urgent_reason = f"ส่ง Draft 1 วันที่ {draft_str} แต่ยังไม่ Book วันถ่าย"
            except Exception:
                pass

        # If waiting parcel and draft overdue
        if waiting_parcel and raw_draft:
            try:
                d_date = datetime.strptime(raw_draft.split('T')[0], '%Y-%m-%d').date()
                if (d_date - now).days < 0:
                    urgent = True
                    urgent_reason = f"กำหนด Draft เดิม {draft_str} เลยแล้ว ต้องตามพัสดุ"
            except Exception:
                pass

        jobs.append({
            'id': pid,
            'priority': priority,
            'priorityLabel': priority_label,
            'name': name,
            'brand': brand or name,
            'status': status,
            'channel': channel,
            'budget': int(budget),
            'filmingDate': filming_str,
            'draftDate': draft_str,
            'postDate': post_str,
            'tomorrow': tomorrow,
            'urgent': urgent,
            'urgentReason': urgent_reason,
            'unbooked': unbooked,
            'waitingParcel': waiting_parcel,
            'url': f"https://app.notion.com/p/{pid}"
        })

    # Sort: Priority ASC, then Urgent DESC, then Name
    jobs.sort(key=lambda j: (j['priority'], not j['urgent'], j['name']))
    return jobs

def parse_daily_todos(blocks, jobs):
    todos = []
    job_map = {j['name'].lower(): j for j in jobs}

    for b in blocks:
        btype = b.get('type')
        if btype == 'to_do':
            tdata = b.get('to_do', {})
            text = ''.join([item.get('plain_text', '') for item in tdata.get('rich_text', [])]).strip()
            if not text:
                continue

            time_str = 'ทั้งวัน'
            title = text
            detail = ''
            url = 'https://app.notion.com/p/4196e8aac17c81a9842edae564ad1152'

            # Try to parse "Time | Title: Detail" or "Title (note): Detail"
            if '|' in text:
                parts = text.split('|', 1)
                time_str = parts[0].strip()
                rest = parts[1].strip()
                if ':' in rest:
                    tparts = rest.split(':', 1)
                    title = tparts[0].strip()
                    detail = tparts[1].strip()
                else:
                    title = rest
            elif ':' in text:
                tparts = text.split(':', 1)
                title = tparts[0].strip()
                detail = tparts[1].strip()

            # Find matching job URL if applicable
            for jname, job in job_map.items():
                if jname in text.lower() or job['brand'].lower() in text.lower():
                    url = job['url']
                    break

            priority = 'P1' if any(p in title.lower() for p in ['ด่วน', 'ค้าง', 'ถ่ายทำ', 'draft']) else 'P2'

            todos.append({
                'id': f"todo-{len(todos) + 1}",
                'time': time_str,
                'priority': priority,
                'title': title,
                'detail': detail or 'ติดตามและอัปเดตความคืบหน้า',
                'url': url
            })

    return todos

def update_index_html(html_path, jobs, todos):
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    now = get_now_ict()
    day_name = THAI_DAYS[now.weekday()]
    month_name = THAI_MONTHS[now.month]
    today_thai = f"วัน{day_name}ที่ {now.day} {month_name} {now.year + 543}"
    storage_key = f"thursday_studio_todo_{now.year}_{now.month:02d}_{now.day:02d}"

    # Replace JOBS array
    jobs_json = json.dumps(jobs, ensure_ascii=False, indent=6)
    content = re.sub(r'const JOBS = \[\s*[\s\S]*?\s*\];', f'const JOBS = {jobs_json};', content)

    # Replace TOMORROW_TODOS array if todos are available
    if todos:
        todos_json = json.dumps(todos, ensure_ascii=False, indent=6)
        content = re.sub(r'const TOMORROW_TODOS = \[\s*[\s\S]*?\s*\];', f'const TOMORROW_TODOS = {todos_json};', content)

    # Replace STORAGE_KEY
    content = re.sub(r"const STORAGE_KEY = 'thursday_studio_todo_[^']+';", f"const STORAGE_KEY = '{storage_key}';", content)

    # Replace Header Title & Subtitle if pattern exists
    content = re.sub(
        r'<h1 class="text-xl sm:text-2xl font-bold text-slate-900">\s*แผนงาน[^\n<]+</h1>',
        f'<h1 class="text-xl sm:text-2xl font-bold text-slate-900">แผนงาน{today_thai} &amp; ระบบส่งอัปเดตงานอินฟลู</h1>',
        content
    )

    # Update job count in Revenue Analytics subtitle
    content = re.sub(
        r'คำนวณอัตโนมัติจากข้อมูลงานทั้งหมด \d+ งาน',
        f'คำนวณอัตโนมัติจากข้อมูลงานทั้งหมด {len(jobs)} งาน',
        content
    )

    # Ensure Chart.js is present in <head>
    if 'cdn.jsdelivr.net/npm/chart.js' not in content:
        content = content.replace(
            '<script src="https://cdn.tailwindcss.com/3.4.17"></script>',
            '<script src="https://cdn.tailwindcss.com/3.4.17"></script>\n  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1"></script>'
        )

    # Ensure renderRevenueCharts(); is called on initial load
    if 'renderRevenueCharts();' not in content and 'function renderRevenueCharts()' in content:
        content = content.replace('renderTable();', 'renderTable();\n    renderRevenueCharts();')

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Successfully updated {html_path} with {len(jobs)} jobs and {len(todos)} todos.")

def main():
    token = os.environ.get('NOTION_TOKEN')
    job_db_id = os.environ.get('NOTION_JOB_TRACKER_DB_ID', '1fa2a0da27c54a50b0eb402d9da913ef')
    daily_notes_id = os.environ.get('NOTION_DAILY_NOTES_ID', '4196e8aa-c17c-81a9-842e-dae564ad1152')
    
    repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    html_path = os.path.join(repo_dir, 'index.html')

    if not os.path.exists(html_path):
        print(f"Error: {html_path} not found!", file=sys.stderr)
        sys.exit(1)

    if not token:
        print("WARNING: NOTION_TOKEN is not set in environment variables.", file=sys.stderr)
        print("Please configure NOTION_TOKEN in GitHub Repository Secrets to enable live Notion sync.", file=sys.stderr)
        print("Skipping sync to protect existing index.html content.")
        sys.exit(0)

    print("Fetching jobs from Notion Database:", job_db_id)
    pages = fetch_all_database_pages(job_db_id, token)
    jobs = process_jobs(pages)
    print(f"Processed {len(jobs)} jobs from Notion.")

    todos = []
    try:
        print("Fetching daily notes from Notion Page:", daily_notes_id)
        blocks = fetch_page_blocks(daily_notes_id, token)
        todos = parse_daily_todos(blocks, jobs)
        print(f"Parsed {len(todos)} todos from Daily Notes.")
    except Exception as e:
        print(f"Note: Could not parse daily notes ({e}), retaining default/existing todos.")

    update_index_html(html_path, jobs, todos)

if __name__ == '__main__':
    main()
