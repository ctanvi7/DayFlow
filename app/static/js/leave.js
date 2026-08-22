/* Dayflow Leave UI controller (Member 3). No framework or unsafe HTML injection. */
(function () {
  "use strict";

  const endpoints = { mine: "/api/leaves/me", all: "/api/leaves" };

  async function api(url, options = {}) {
    const response = await fetch(url, {
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok || body.success === false) {
      const error = new Error(body.message || "Request failed");
      error.status = response.status;
      error.details = body.errors || {};
      throw error;
    }
    return body.data;
  }

  function element(tag, text, className) {
    const node = document.createElement(tag);
    if (text !== undefined && text !== null) node.textContent = text;
    if (className) node.className = className;
    return node;
  }

  function setFeedback(root, message, kind = "") {
    const feedback = root.querySelector("[data-leave-feedback]");
    if (!feedback) return;
    feedback.textContent = message || "";
    feedback.className = `leave-feedback ${kind}`;
  }

  function userMessage(error) {
    const details = error.details || {};
    const fieldMessages = Object.values(details).filter(Boolean);
    if (fieldMessages.length) return fieldMessages.join(" ");
    return error.message || "Something went wrong. Please try again.";
  }

  function renderStatus(status) {
    return element("span", status, `leave-status leave-status--${String(status).toLowerCase()}`);
  }

  function renderRows(root, records, admin) {
    const target = root.querySelector("[data-leave-list]");
    if (!target) return;
    target.replaceChildren();
    if (!records.length) {
      target.append(element("p", "No leave requests found.", "leave-empty"));
      return;
    }
    records.forEach((record) => {
      const card = element("article", undefined, "leave-request");
      const heading = admin && record.employee
        ? `${record.employee.first_name} ${record.employee.last_name}`
        : record.leave_type;
      card.append(element("h3", heading));
      card.append(element("p", `${record.leave_type}: ${record.start_date} to ${record.end_date} (${record.days_requested} days)`));
      card.append(renderStatus(record.status));
      if (record.remarks) card.append(element("p", record.remarks, "leave-remarks"));
      if (record.review_comment) card.append(element("p", `Review: ${record.review_comment}`, "leave-review-comment"));
      if (admin && record.status === "PENDING") card.append(renderDecisionControls(root, record));
      target.append(card);
    });
  }

  function renderDecisionControls(root, record) {
    const controls = element("div", undefined, "leave-decision-controls");
    const comment = document.createElement("input");
    comment.type = "text";
    comment.maxLength = 500;
    comment.placeholder = "Review comment (optional)";
    ["APPROVED", "REJECTED"].forEach((status) => {
      const button = element("button", status === "APPROVED" ? "Approve" : "Reject");
      button.type = "button";
      button.addEventListener("click", async () => {
        button.disabled = true;
        try {
          await api(`${endpoints.all}/${record.id}/decision`, {
            method: "PATCH",
            body: JSON.stringify({ status, review_comment: comment.value }),
          });
          setFeedback(root, `Leave request ${status.toLowerCase()}.`, "success");
          await loadAdmin(root);
        } catch (error) {
          setFeedback(root, userMessage(error), "error");
        } finally {
          button.disabled = false;
        }
      });
      controls.append(button);
    });
    controls.prepend(comment);
    return controls;
  }

  async function loadEmployee(root) {
    setFeedback(root, "Loading leave requests…");
    try {
      renderRows(root, await api(endpoints.mine), false);
      setFeedback(root, "");
    } catch (error) {
      setFeedback(root, error.status === 401 || error.status === 403 ? "Your session has expired." : userMessage(error), "error");
    }
  }

  async function loadAdmin(root) {
    const filterForm = root.querySelector("[data-leave-filters]");
    const params = filterForm
      ? new URLSearchParams(new FormData(filterForm))
      : new URLSearchParams();
    setFeedback(root, "Loading leave requests…");
    try {
      renderRows(root, await api(`${endpoints.all}?${params}`), true);
      setFeedback(root, "");
    } catch (error) {
      setFeedback(root, error.status === 401 || error.status === 403 ? "You are not authorized to view leave requests." : userMessage(error), "error");
    }
  }

  function bindEmployee(root) {
    const form = root.querySelector("[data-leave-request-form]");
    if (form) form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const values = Object.fromEntries(new FormData(form));
      try {
        await api(endpoints.all, { method: "POST", body: JSON.stringify(values) });
        form.reset();
        setFeedback(root, "Leave request submitted.", "success");
        await loadEmployee(root);
      } catch (error) {
        setFeedback(root, userMessage(error), "error");
      }
    });
    loadEmployee(root);
  }

  function bindAdmin(root) {
    const filters = root.querySelector("[data-leave-filters]");
    if (filters) filters.addEventListener("input", () => loadAdmin(root));
    loadAdmin(root);
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-leave-screen='employee']").forEach(bindEmployee);
    document.querySelectorAll("[data-leave-screen='admin']").forEach(bindAdmin);
  });
}());
