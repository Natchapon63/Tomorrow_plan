# วิธีติดตั้ง Google Apps Script Web App (Thursday Studio)

ระบบนี้ใช้รับข้อมูลการอัปเดตงานประจำวันจาก `index.html` บน GitHub Pages แล้วนำไปบันทึกลง Google Sheet แท็บ `Updates` อัตโนมัติ เพื่อให้ Managing Officer / Gemini นำไปประมวลผลต่อตอน 00:00 น.

---

### ขั้นตอนการ Deploy (ใช้เวลาไม่เกิน 2 นาที)

1. **เปิด Google Sheet ปลายทาง**:
   👉 [Influencer Daily Updates (Web Sync)](https://docs.google.com/spreadsheets/d/1gTRC7_DmnW8ehz-3-zHsQqZRQrc6qc6iRxOjmLA6Wsw/edit)

2. **เปิด Apps Script**:
   - ไปที่เมนูด้านบน คลิก **ส่วนขยาย (Extensions)** → **Apps Script**

3. **วางโค้ด**:
   - ลบโค้ดเดิมในไฟล์ `Code.gs` ทั้งหมด
   - คัดลอกโค้ดจากไฟล์ [`google-apps-script/Code.gs`](./Code.gs) ไปวางแทนที่
   - กดปุ่ม **บันทึก (Save / รูปแผ่นดิสก์)** หรือกด `Ctrl + S`

4. **ทำการ Deploy เป็น Web App**:
   - คลิกปุ่มสีน้ำเงิน **การทำให้ใช้งานได้ (Deploy)** ที่มุมขวาบน → เลือก **การทำให้ใช้งานได้รายการใหม่ (New deployment)**
   - คลิกรูปฟันเฟือง ⚙️ ด้านซ้ายข้าง "เลือกประเภท" → เลือก **เว็บแอป (Web app)**
   - ตั้งค่าดังนี้:
     - **คำอธิบาย (Description)**: `Thursday Studio Web Sync v1`
     - **ดำเนินการในฐานะ (Execute as)**: `ฉัน (Me / your email)`
     - **ผู้ที่มีสิทธิ์เข้าถึง (Who has access)**: **`ทุกคน (Anyone)`** *(สำคัญมาก: ต้องเลือก Anyone เพื่อให้หน้าเว็บ GitHub Pages ส่งข้อมูลเข้ามาได้โดยไม่ต้องล็อกอิน Google)*
   - คลิกปุ่ม **ทำให้ใช้งานได้ (Deploy)**

5. **ให้สิทธิ์การเข้าถึง (Authorize Access)**:
   - Google จะแสดงหน้าต่างขอสิทธิ์เข้าถึง Sheet
   - คลิก **ตรวจสอบสิทธิ์ (Authorize Access)**
   - เลือกบัญชี Google ของคุณ
   - หากขึ้นเตือน "Google ยังไม่ได้ยืนยันแอปนี้ (Google hasn't verified this app)":
     - คลิก **ขั้นสูง (Advanced)**
     - คลิก **ไปที่ ... (ไม่ปลอดภัย) / Go to ... (unsafe)**
     - คลิก **อนุญาต (Allow)**

6. **คัดลอก Web App URL**:
   - เมื่อ Deploy เสร็จ Google จะให้ URL ที่ลงท้ายด้วย `/exec` เช่น:
     `https://script.google.com/macros/s/AKfycb.../exec`
   - คัดลอก URL นี้มาใส่ในตัวแปร `UPDATE_ENDPOINT_URL` ใน `index.html`
