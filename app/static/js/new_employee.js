"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("[data-new-employee-form]");
  const feedback = document.querySelector("[data-employee-feedback]");
  const credentials = document.querySelector("[data-credentials]");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = form.querySelector("button");
    button.disabled = true;
    feedback.className = "form-feedback";
    feedback.textContent = "Creating employee...";
    credentials.hidden = true;
    try {
      const response = await fetch("/api/employees", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(Object.fromEntries(new FormData(form))),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok || body.success === false) {
        const details = Object.values(body.errors || {}).join(" ");
        throw new Error(details || body.message || "Employee creation failed.");
      }
      const employee = body.data.employee;
      const loginId = body.data.credentials.login_id;
      const temporaryPassword = body.data.credentials.temporary_password;
      feedback.className = "form-feedback success";
      feedback.textContent = "Employee created successfully. Save these credentials now.";
      credentials.hidden = false;
      credentials.replaceChildren();
      const heading = document.createElement("h2");
      heading.textContent = "One-time credentials";
      credentials.append(heading);
      [
        `${employee.first_name} ${employee.last_name}`,
        `Login ID: ${loginId}`,
        `Temporary password: ${temporaryPassword}`,
      ].forEach((text) => {
        const line = document.createElement("p");
        line.textContent = text;
        credentials.append(line);
      });
      form.reset();
    } catch (error) {
      feedback.className = "form-feedback error";
      feedback.textContent = error.message;
    } finally {
      button.disabled = false;
    }
  });
});
