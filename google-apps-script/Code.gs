/**
 * Thursday Studio — Influencer Daily Updates (Web Sync)
 * Google Apps Script Web App Endpoint
 * 
 * Target Google Sheet: Influencer Daily Updates (Web Sync)
 * Spreadsheet ID: 1gTRC7_DmnW8ehz-3-zHsQqZRQrc6qc6iRxOjmLA6Wsw
 * Tab: Updates
 * Columns: Timestamp | Job Name | Notion Page ID | New Status | Sub Status | Note | Processed
 */

var SPREADSHEET_ID = "1gTRC7_DmnW8ehz-3-zHsQqZRQrc6qc6iRxOjmLA6Wsw";
var TAB_NAME = "Updates";

/**
 * Handle HTTP POST requests from index.html (GitHub Pages)
 */
function doPost(e) {
  var lock = LockService.getScriptLock();
  try {
    // Wait up to 30 seconds for concurrent requests
    lock.waitLock(30000);
  } catch (lockErr) {
    return createJsonResponse({
      status: "error",
      message: "Server is busy. Please try again."
    });
  }

  try {
    var ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    var sheet = ss.getSheetByName(TAB_NAME);

    // If tab doesn't exist, create it with standard headers
    if (!sheet) {
      sheet = ss.insertSheet(TAB_NAME);
      sheet.appendRow(["Timestamp", "Job Name", "Notion Page ID", "New Status", "Sub Status", "Note", "Processed"]);
      sheet.getRange("A1:G1").setFontWeight("bold");
    }

    var payload = {};
    if (e && e.postData && e.postData.contents) {
      try {
        payload = JSON.parse(e.postData.contents);
      } catch (jsonErr) {
        // Fallback for form-encoded or raw string
        payload = { raw: e.postData.contents };
      }
    } else if (e && e.parameter) {
      payload = e.parameter;
    }

    // Default timestamp formatted in ICT (Asia/Bangkok, GMT+7)
    var timestamp = payload.timestamp || Utilities.formatDate(new Date(), "Asia/Bangkok", "yyyy-MM-dd'T'HH:mm:ssXXX");
    var jobName = payload.jobName || "";
    var notionPageId = payload.notionPageId || "";
    var newStatus = payload.newStatus || "";
    var subStatus = payload.subStatus || "";
    var note = payload.note || "";
    var processed = false; // Always FALSE for new influencer updates

    // Append new row into Updates tab (Columns A to G)
    sheet.appendRow([
      timestamp,
      jobName,
      notionPageId,
      newStatus,
      subStatus,
      note,
      processed
    ]);

    return createJsonResponse({
      status: "ok",
      message: "Update recorded successfully",
      record: {
        timestamp: timestamp,
        jobName: jobName,
        notionPageId: notionPageId,
        newStatus: newStatus,
        subStatus: subStatus,
        note: note,
        processed: processed
      }
    });

  } catch (err) {
    return createJsonResponse({
      status: "error",
      message: err.toString()
    });
  } finally {
    lock.releaseLock();
  }
}

/**
 * Handle HTTP GET requests (Health check / Ping)
 */
function doGet(e) {
  return createJsonResponse({
    status: "ok",
    service: "Thursday Studio Influencer Sync Endpoint",
    message: "Endpoint is active and ready to receive updates.",
    currentTime: Utilities.formatDate(new Date(), "Asia/Bangkok", "yyyy-MM-dd'T'HH:mm:ssXXX")
  });
}

/**
 * Helper to build JSON responses compatible with ContentService
 */
function createJsonResponse(data) {
  return ContentService.createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}
