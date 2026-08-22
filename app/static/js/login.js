"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("#login-form");
  const feedback = document.querySelector("#login-feedback");
  if (!form) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = form.querySelector("button[type='submit']");
    button.disabled = true;
    feedback.textContent = "";

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          login_id: form.elements.login_id.value.trim(),
          password: form.elements.password.value,
        }),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok || body.success === false) {
        throw new Error(body.message || "Unable to sign in.");
      }

      const user = body.data?.user || {};
      if (user.must_change_password) {
        feedback.textContent = "Password change is required before continuing.";
        return;
      }
      window.location.assign(user.role === "EMPLOYEE" ? "/attendance" : "/admin/employees");
    } catch (error) {
      feedback.textContent = error.message;
    } finally {
      button.disabled = false;
    }
  });
});