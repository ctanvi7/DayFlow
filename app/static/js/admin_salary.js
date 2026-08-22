"use strict";

const salaryFields = [
  ["basic_amount", "Basic"], ["hra_amount", "HRA"],
  ["standard_allowance", "Standard allowance"], ["performance_bonus", "Performance bonus"],
  ["lta_amount", "LTA"], ["fixed_allowance", "Fixed allowance"],
  ["employee_pf", "Employee PF"], ["employer_pf", "Employer PF"],
  ["professional_tax", "Professional tax"],
];

function renderBreakdown(data) {
  const target = document.querySelector("[data-salary-breakdown]");
  target.replaceChildren();
  salaryFields.forEach(([field, label]) => {
    const row = document.createElement("p");
    row.textContent = `${label}: ${data[field] ?? "0.00"}`;
    target.append(row);
  });
}

async function api(url, options = {}) {
  const response = await fetch(url, { credentials: "same-origin", headers: { "Content-Type": "application/json" }, ...options });
  const body = await response.json().catch(() => ({}));
  if (!response.ok || body.success === false) throw new Error(Object.values(body.errors || {}).join(" ") || body.message || "Request failed.");
  return body.data;
}

document.addEventListener("DOMContentLoaded", async () => {
  const selector = document.querySelector("[data-salary-employee]");
  const form = document.querySelector("[data-salary-form]");
  const feedback = document.querySelector("[data-salary-feedback]");
  try {
    const employees = await api("/api/employees");
    employees.forEach((employee) => {
      const option = document.createElement("option");
      option.value = employee.id;
      option.textContent = `${employee.first_name} ${employee.last_name}`;
      selector.append(option);
    });
    form.hidden = !employees.length;
    if (employees.length) await loadSalary(selector.value);
  } catch (error) {
    feedback.className = "form-feedback error";
    feedback.textContent = error.message;
  }

  async function loadSalary(employeeId) {
    try {
      const data = await api(`/api/salaries/${employeeId}`);
      form.hidden = false;
      form.elements.monthly_wage.value = data?.monthly_wage || "";
      if (data) renderBreakdown(data);
      else document.querySelector("[data-salary-breakdown]").replaceChildren();
    } catch (error) {
      feedback.className = "form-feedback error";
      feedback.textContent = error.message;
    }
  }

  selector.addEventListener("change", () => loadSalary(selector.value));
  form.addEventListener("input", () => {
    const wage = Number(form.elements.monthly_wage.value || 0);
    if (!wage) return;
    const basic = wage * 0.5;
    renderBreakdown({ basic_amount: basic.toFixed(2), hra_amount: (basic * 0.5).toFixed(2), standard_allowance: "4167.00", performance_bonus: (basic * 0.0833).toFixed(2), lta_amount: (basic * 0.0833).toFixed(2), fixed_allowance: (wage - basic - basic * 0.5 - 4167 - basic * 0.0833 * 2).toFixed(2), employee_pf: (basic * 0.12).toFixed(2), employer_pf: (basic * 0.12).toFixed(2), professional_tax: "200.00" });
  });
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const data = await api(`/api/salaries/${selector.value}`, { method: "PUT", body: JSON.stringify({ monthly_wage: form.elements.monthly_wage.value }) });
      renderBreakdown(data);
      feedback.className = "form-feedback success";
      feedback.textContent = "Salary saved successfully.";
    } catch (error) {
      feedback.className = "form-feedback error";
      feedback.textContent = error.message;
    }
  });
});
