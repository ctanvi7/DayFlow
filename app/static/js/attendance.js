"use strict";

let attendanceRecords = [];
let currentStatus = "NOT_CHECKED_IN";

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

function statusClass(status) {
  return status.toLowerCase().replace("_", "-");
}

function todayIsoDate() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}

function getTodayRecord() {
  return attendanceRecords.find((record) => record.attendance_date === todayIsoDate());
}

function setFeedback(message, isError = false) {
  const feedback = document.querySelector("#attendance-feedback");
  feedback.textContent = message;
  feedback.classList.toggle("feedback--error", isError);
}

async function requestAttendance(url, options = {}) {
  const response = await fetch(url, {
    headers: { Accept: "application/json", ...options.headers },
    ...options,
  });
  const body = await response.json().catch(() => null);
  if (!response.ok || !body?.success) {
    throw new Error(body?.message || "Unable to update attendance. Please try again.");
  }
  return body.data;
}

function renderAttendanceHistory() {
  const history = document.querySelector("#attendance-history");
  const emptyState = document.querySelector("#empty-state");
  const records = [...attendanceRecords].sort((first, second) => second.attendance_date.localeCompare(first.attendance_date));
  history.replaceChildren();
  emptyState.hidden = records.length !== 0;

  records.forEach((record) => {
    const row = document.createElement("tr");
    row.innerHTML = `<td>${formatDate(record.attendance_date)}</td><td>${formatTime(record.check_in_at)}</td><td>${formatTime(record.check_out_at)}</td><td>${formatMinutes(record.work_minutes)}</td><td>${formatMinutes(record.extra_minutes)}</td><td><span class="status-badge ${statusClass(record.status)}">${statusLabel(record.status)}</span></td>`;
    history.append(row);
  });
}

function updateSummary() {
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
  const badge = document.querySelector("#today-status");
  const checkInButton = document.querySelector("#check-in-button");
  const checkOutButton = document.querySelector("#check-out-button");

  badge.className = `status-badge ${statusClass(currentStatus)}`;
  badge.textContent = currentStatus === "NOT_CHECKED_IN" ? "Not checked in" : statusLabel(currentStatus);
  document.querySelector("#check-in-time").textContent = formatTime(record?.check_in_at);
  document.querySelector("#check-out-time").textContent = formatTime(record?.check_out_at);
  document.querySelector("#work-hours").textContent = record?.check_out_at ? formatMinutes(record.work_minutes) : "—";
  document.querySelector("#extra-hours").textContent = record?.check_out_at ? formatMinutes(record.extra_minutes) : "—";
  checkInButton.disabled = currentStatus === "LEAVE" || Boolean(record?.check_in_at);
  checkOutButton.disabled = currentStatus !== "PRESENT" || !record?.check_in_at || Boolean(record?.check_out_at);
}

async function loadAttendance() {
  const now = new Date();
  const data = await requestAttendance(`/api/attendance/me?year=${now.getFullYear()}&month=${now.getMonth() + 1}`);
  attendanceRecords = data.attendance;
  currentStatus = data.current_status;
  renderAttendanceHistory();
  updateSummary();
  updateTodayStatus();
}

async function handleCheckIn() {
  const button = document.querySelector("#check-in-button");
  button.disabled = true;
  try {
    await requestAttendance("/api/attendance/check-in", { method: "POST" });
    await loadAttendance();
    setFeedback("Checked in successfully.");
  } catch (error) {
    setFeedback(error.message, true);
    updateTodayStatus();
  }
}

async function handleCheckOut() {
  const button = document.querySelector("#check-out-button");
  button.disabled = true;
  try {
    await requestAttendance("/api/attendance/check-out", { method: "POST" });
    await loadAttendance();
    setFeedback("Checked out successfully.");
  } catch (error) {
    setFeedback(error.message, true);
    updateTodayStatus();
  }
}

async function initializeDashboard() {
  const now = new Date();
  document.querySelector("#today-date").textContent = now.toLocaleDateString([], { weekday: "long", day: "numeric", month: "long", year: "numeric" });
  document.querySelector("#check-in-button").addEventListener("click", handleCheckIn);
  document.querySelector("#check-out-button").addEventListener("click", handleCheckOut);
  document.querySelector("#check-in-button").disabled = true;
  document.querySelector("#check-out-button").disabled = true;
  try {
    await loadAttendance();
  } catch (error) {
    setFeedback(error.message, true);
  }
}

document.addEventListener("DOMContentLoaded", initializeDashboard);
