"use strict";

const SCHEDULED_WORK_MINUTES = 480;
const BREAK_MINUTES = 60;

// TEMPORARY MOCK DATA
// TODO(Member 2): Replace with GET /api/attendance/me after shared application integration.
const currentDate = new Date();
const currentYear = currentDate.getFullYear();
const currentMonth = currentDate.getMonth();
const employeeId = 1; // TODO(Member 2): Use authenticated employee identity instead of temporary employee_id.
const attendanceRecords = [
  { employee_id: employeeId, attendance_date: isoDate(2), check_in_at: isoDateTime(2, 9, 4), check_out_at: isoDateTime(2, 18, 3), work_minutes: 479, extra_minutes: 0, status: "PRESENT" },
  { employee_id: employeeId, attendance_date: isoDate(5), check_in_at: isoDateTime(5, 8, 54), check_out_at: isoDateTime(5, 18, 38), work_minutes: 524, extra_minutes: 44, status: "PRESENT" },
  { employee_id: employeeId, attendance_date: isoDate(8), check_in_at: null, check_out_at: null, work_minutes: 0, extra_minutes: 0, status: "LEAVE" },
  { employee_id: employeeId, attendance_date: isoDate(12), check_in_at: isoDateTime(12, 9, 12), check_out_at: isoDateTime(12, 14, 10), work_minutes: 238, extra_minutes: 0, status: "HALF_DAY" },
  { employee_id: employeeId, attendance_date: isoDate(15), check_in_at: null, check_out_at: null, work_minutes: 0, extra_minutes: 0, status: "ABSENT" },
];

function isoDate(day) {
  return `${currentYear}-${String(currentMonth + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

function isoDateTime(day, hours, minutes) {
  return new Date(currentYear, currentMonth, day, hours, minutes).toISOString();
}

function formatMinutes(minutes) {
  const safeMinutes = Math.max(0, Number(minutes) || 0);
  return `${Math.floor(safeMinutes / 60)} hours ${safeMinutes % 60} minutes`;
}

function formatTime(value) {
  return value ? new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "—";
}

function formatDate(value) {
  return new Date(`${value}T00:00:00`).toLocaleDateString([], { day: "2-digit", month: "short", year: "numeric" });
}

function statusLabel(status) {
  return status.replace("_", " ").toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function getTodayRecord() {
  return attendanceRecords.find((record) => record.attendance_date === isoDate(currentDate.getDate()));
}

function renderAttendanceHistory() {
  const history = document.querySelector("#attendance-history");
  const emptyState = document.querySelector("#empty-state");
  const records = attendanceRecords
    .filter((record) => new Date(`${record.attendance_date}T00:00:00`).getMonth() === currentMonth)
    .sort((first, second) => second.attendance_date.localeCompare(first.attendance_date));

  history.replaceChildren();
  emptyState.hidden = records.length !== 0;
  records.forEach((record) => {
    const row = document.createElement("tr");
    row.innerHTML = `<td>${formatDate(record.attendance_date)}</td><td>${formatTime(record.check_in_at)}</td><td>${formatTime(record.check_out_at)}</td><td>${formatMinutes(record.work_minutes)}</td><td>${formatMinutes(record.extra_minutes)}</td><td><span class="status-badge ${record.status.toLowerCase().replace("_", "-")}">${statusLabel(record.status)}</span></td>`;
    history.append(row);
  });
}

function updateSummary() {
  // TODO(Member 2): Replace mock monthly summary with backend data when the final API contract is established.
  const totals = attendanceRecords.reduce((summary, record) => {
    summary.workingDays += 1;
    summary.workMinutes += record.work_minutes;
    summary.extraMinutes += record.extra_minutes;
    if (record.status === "PRESENT") summary.present += 1;
    if (record.status === "ABSENT") summary.absent += 1;
    if (record.status === "LEAVE") summary.leave += 1;
    return summary;
  }, { workingDays: 0, present: 0, absent: 0, leave: 0, workMinutes: 0, extraMinutes: 0 });

  document.querySelector("#total-working-days").textContent = totals.workingDays;
  document.querySelector("#present-days").textContent = totals.present;
  document.querySelector("#absent-days").textContent = totals.absent;
  document.querySelector("#leave-days").textContent = totals.leave;
  document.querySelector("#total-work-hours").textContent = formatMinutes(totals.workMinutes);
  document.querySelector("#total-extra-hours").textContent = formatMinutes(totals.extraMinutes);
}

function updateTodayStatus() {
  const record = getTodayRecord();
  const status = record ? record.status : "NOT_CHECKED_IN";
  const badge = document.querySelector("#today-status");
  const checkInButton = document.querySelector("#check-in-button");
  const checkOutButton = document.querySelector("#check-out-button");

  badge.className = `status-badge ${status.toLowerCase().replace("_", "-")}`;
  badge.textContent = status === "NOT_CHECKED_IN" ? "Not checked in" : statusLabel(status);
  document.querySelector("#check-in-time").textContent = formatTime(record?.check_in_at);
  document.querySelector("#check-out-time").textContent = formatTime(record?.check_out_at);
  document.querySelector("#work-hours").textContent = record?.check_out_at ? formatMinutes(record.work_minutes) : "—";
  document.querySelector("#extra-hours").textContent = record?.check_out_at ? formatMinutes(record.extra_minutes) : "—";
  checkInButton.disabled = Boolean(record?.check_in_at);
  checkOutButton.disabled = !record?.check_in_at || Boolean(record?.check_out_at);
}

function handleCheckIn() {
  // TODO(Member 2): Connect Check In button to POST /api/attendance/check-in after authentication integration.
  const now = new Date();
  const record = { employee_id: employeeId, attendance_date: isoDate(now.getDate()), check_in_at: now.toISOString(), check_out_at: null, work_minutes: 0, extra_minutes: 0, status: "PRESENT" };
  const existing = getTodayRecord();
  if (existing) Object.assign(existing, record); else attendanceRecords.push(record);
  document.querySelector("#attendance-feedback").textContent = "Check-in recorded for this demonstration.";
  updateTodayStatus();
  renderAttendanceHistory();
  updateSummary();
}

function handleCheckOut() {
  // TODO(Member 2): Connect Check Out button to POST /api/attendance/check-out after authentication integration.
  const record = getTodayRecord();
  if (!record?.check_in_at) return;
  const checkedOutAt = new Date();
  const elapsedMinutes = Math.floor((checkedOutAt - new Date(record.check_in_at)) / 60000);
  record.check_out_at = checkedOutAt.toISOString();
  record.work_minutes = Math.max(0, elapsedMinutes - BREAK_MINUTES);
  record.extra_minutes = Math.max(0, record.work_minutes - SCHEDULED_WORK_MINUTES);
  document.querySelector("#attendance-feedback").textContent = "Check-out recorded for this demonstration.";
  updateTodayStatus();
  renderAttendanceHistory();
  updateSummary();
}

function initializeDashboard() {
  document.querySelector("#today-date").textContent = currentDate.toLocaleDateString([], { weekday: "long", day: "numeric", month: "long", year: "numeric" });
  document.querySelector("#check-in-button").addEventListener("click", handleCheckIn);
  document.querySelector("#check-out-button").addEventListener("click", handleCheckOut);
  renderAttendanceHistory();
  updateSummary();
  updateTodayStatus();
}

document.addEventListener("DOMContentLoaded", initializeDashboard);
