/* DayFlow sign-in controller. */
(function () {
  "use strict";

  function setMessage(target, message, kind = "") {
    target.textContent = message || "";
    target.className = `form-message ${kind}`;
  }

  document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("[data-login-form]");
    if (!form) return;
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const button = form.querySelector("button[type='submit']");
      const message = form.querySelector("[data-login-message]");
      button.disabled = true;
      setMessage(message, "Signing you in...");
      try {
        const values = Object.fromEntries(new FormData(form));
        const identifier = values.login_id.trim();
        const payload = identifier.includes("@")
          ? { email: identifier, password: values.password }
          : { login_id: identifier, password: values.password };
        const response = await fetch("/api/auth/login", {
          method: "POST",
          credentials: "same-origin",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const body = await response.json().catch(() => ({}));
        if (!response.ok || !body.success) throw new Error(body.message || "Unable to sign in.");
        const user = body.data.user;
        if (user.must_change_password) {
          setMessage(message, "Your password must be changed before continuing.", "error");
          return;
        }
        window.location.assign(["ADMIN", "HR"].includes(user.role) ? "/admin/leaves" : "/leaves");
      } catch (error) {
        setMessage(message, error.message, "error");
      } finally {
        button.disabled = false;
      }
    });
  });
}());
