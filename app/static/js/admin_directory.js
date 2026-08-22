/* Dayflow Admin Employee Directory controller (Member 3).
 *
 * Mount this in the shared Admin template with:
 *   <section data-employee-directory data-employees-endpoint="/api/employees">
 *     <input data-employee-search type="search">
 *     <div data-employee-feedback></div>
 *     <div data-employee-grid></div>
 *   </section>
 *
 * The employee API must return a safe list of card fields: id, first_name,
 * last_name, job_title, department, profile_image_path (optional), and
 * current_status. current_status is rendered as supplied by the backend.
 */
(function () {
  "use strict";

  const statusLabels = {
    LEAVE: "On leave",
    PRESENT: "Present",
    CHECKED_OUT: "Checked Out",
    ABSENT: "Absent",
    NOT_CHECKED_IN: "Not checked in",
  };

  function node(tag, content, className) {
    const result = document.createElement(tag);
    if (content !== undefined && content !== null) result.textContent = content;
    if (className) result.className = className;
    return result;
  }

  function setFeedback(root, content, type) {
    const target = root.querySelector("[data-employee-feedback]");
    if (!target) return;
    target.textContent = content || "";
    target.className = `employee-feedback ${type || ""}`;
  }

  function initials(employee) {
    return `${employee.first_name || ""}`.slice(0, 1) + `${employee.last_name || ""}`.slice(0, 1);
  }

  function renderCard(employee, detailsPath) {
    const card = node("button", undefined, "employee-card");
    card.type = "button";
    card.setAttribute("aria-label", `View ${employee.first_name || ""} ${employee.last_name || ""}`.trim());

    const avatar = node("div", initials(employee).toUpperCase(), "employee-card__avatar");
    if (employee.profile_image_path) {
      const image = document.createElement("img");
      image.src = employee.profile_image_path;
      image.alt = "";
      avatar.replaceChildren(image);
    }
    const fullName = `${employee.first_name || ""} ${employee.last_name || ""}`.trim() || "Unnamed employee";
    const content = node("div", undefined, "employee-card__content");
    content.append(node("h3", fullName));
    content.append(node("p", employee.job_title || "No job title"));
    content.append(node("p", employee.department || "No department"));

    const suppliedStatus = String(employee.current_status || "NOT_CHECKED_IN").toUpperCase();
    const status = node(
      "span",
      statusLabels[suppliedStatus] || suppliedStatus,
      `employee-card__status employee-card__status--${suppliedStatus.toLowerCase()}`,
    );
    status.setAttribute("aria-label", `Current status: ${status.textContent}`);
    content.append(status);
    card.append(avatar, content);
    card.addEventListener("click", () => {
      window.location.assign(`${detailsPath.replace(/\/$/, "")}/${encodeURIComponent(employee.id)}`);
    });
    return card;
  }

  async function loadDirectory(root) {
    const endpoint = root.dataset.employeesEndpoint || "/api/employees";
    const detailsPath = root.dataset.employeeDetailsPath || "/employees";
    const searchInput = root.querySelector("[data-employee-search]");
    const grid = root.querySelector("[data-employee-grid]");
    if (!grid) return;
    grid.replaceChildren(node("p", "Loading employees…", "employee-directory__loading"));
    setFeedback(root, "");
    const url = new URL(endpoint, window.location.origin);
    if (searchInput && searchInput.value.trim()) url.searchParams.set("search", searchInput.value.trim());
    try {
      const response = await fetch(url, { credentials: "same-origin" });
      const body = await response.json().catch(() => ({}));
      if (!response.ok || body.success === false) throw new Error(body.message || "Could not load employees");
      const employees = Array.isArray(body.data) ? body.data : (body.data && body.data.items) || [];
      grid.replaceChildren();
      if (!employees.length) {
        grid.append(node("p", "No employees found.", "employee-directory__empty"));
        return;
      }
      employees.forEach((employee) => grid.append(renderCard(employee, detailsPath)));
    } catch (error) {
      grid.replaceChildren(node("p", "Unable to load employee directory.", "employee-directory__error"));
      setFeedback(root, error.message, "error");
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-employee-directory]").forEach((root) => {
      const search = root.querySelector("[data-employee-search]");
      let timer;
      if (search) search.addEventListener("input", () => {
        window.clearTimeout(timer);
        timer = window.setTimeout(() => loadDirectory(root), 200);
      });
      loadDirectory(root);
    });
  });
}());
