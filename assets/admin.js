const config = window.CITI_HOMES_SUPABASE || {};
const supabaseReady = Boolean(config.url && config.anonKey && config.anonKey.length > 20);
const client = supabaseReady ? window.supabase.createClient(config.url, config.anonKey) : null;

const pages = [
  { key: "dashboard", label: "Dashboard" },
  { key: "employees", label: "Employee Master", table: "employees", filters: ["All", "Operations", "P&C and Administration", "Procurement"] },
  { key: "recruitment", label: "Recruitment Tracker", table: "recruitment" },
  { key: "interview_evaluation", label: "Interview Evaluation", table: "interview_evaluation" },
  { key: "attendance", label: "Attendance Portal", external: "https://citi-homes.github.io/Attendance.Portal/index.html" },
  { key: "joining_checklist", label: "Joining Checklist", table: "joining_checklist" },
  { key: "leave_management", label: "Leave Management", table: "leave_management" },
  { key: "documents", label: "Visa & Documents", table: "documents" },
  { key: "pantry", label: "Pantry Management", table: "pantry" },
  { key: "utilities", label: "Utility Bills", table: "utilities" },
  { key: "inventory", label: "Office Inventory", table: "inventory" },
  { key: "vendors", label: "Vendor Database", table: "vendors" },
  { key: "tasks", label: "P&C Task Calendar", table: "tasks" }
];

const columns = {
  employees: ["employee_id", "name", "department", "designation", "nationality", "joining_date", "employment_type", "visa_status", "emirates_id_expiry", "passport_expiry", "mobile", "emergency_contact", "status"],
  recruitment: ["candidate", "position", "source", "mobile", "location", "gcc_experience", "total_experience", "current_salary", "expected_salary", "notice_period", "interview_date", "status"],
  interview_evaluation: ["candidate", "position", "department", "interviewer_names", "interview_date", "technical_knowledge", "position_specific_skills", "relevant_experience", "problem_solving_ability", "teamwork", "communication_skills", "confidence_professionalism", "recommended_salary", "final_notice_period", "final_decision", "final_remarks"],
  joining_checklist: ["employee", "offer_letter", "passport_copy", "visa", "emirates_id", "medical", "contract", "insurance", "bank_details", "completed_pct"],
  leave_management: ["employee", "leave_type", "opening_balance", "used", "remaining"],
  documents: ["employee", "document", "expiry_date", "reminder_date", "status"],
  pantry: ["month", "item", "opening", "purchased", "used", "closing", "required_next_month", "cost"],
  utilities: ["utility", "vendor", "invoice_date", "due_date", "amount", "status", "reminder_sent"],
  inventory: ["item", "category", "quantity", "location", "responsible_person", "condition"],
  vendors: ["vendor", "service", "contact_person", "mobile", "contract_status", "renewal_date"],
  tasks: ["task", "frequency", "due_date", "status", "remarks"]
};

const options = {
  department: ["Operations", "P&C and Administration", "Procurement"],
  status: ["Active", "Probation", "Inactive", "Applied", "Screening", "Shortlisted", "Interview Scheduled", "Selected", "Offer Sent", "Joined", "Rejected", "Hold", "Pending", "In Progress", "Completed", "Valid", "Expiring Soon", "Expired"],
  final_decision: ["Strongly recommended", "Recommended", "Recommended with reservations", "Do not recommend"],
  employment_type: ["Employee", "Contract", "Temporary", "Intern"],
  visa_status: ["Not Started", "Processing", "Issued", "Renewal", "On Hold", "Cancelled"],
  contract_status: ["Active", "Pending", "Expired", "Renewal"],
  reminder_sent: ["No", "Yes"]
};

let state = {
  session: null,
  page: "dashboard",
  rows: {},
  activeFilter: "All",
  search: "",
  weather: null
};

const $ = (selector) => document.querySelector(selector);

const displayNames = {
  "umer@citihomes.ae": "Umer Raza"
};

function titleize(value) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function displayNameForEmail(email = "") {
  const normalized = String(email).toLowerCase();
  return displayNames[normalized] || normalized || "Admin";
}

function updateAbuDhabiTime() {
  const formatter = new Intl.DateTimeFormat("en-AE", {
    timeZone: "Asia/Dubai",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true
  });
  $("#abuDhabiTime").textContent = `Abu Dhabi ${formatter.format(new Date())}`;
}

async function loadAbuDhabiWeather() {
  try {
    const response = await fetch("https://api.open-meteo.com/v1/forecast?latitude=24.4539&longitude=54.3773&current=temperature_2m&timezone=Asia%2FDubai");
    if (!response.ok) throw new Error("Weather unavailable");
    const payload = await response.json();
    const value = payload.current?.temperature_2m;
    state.weather = Number.isFinite(value) ? Math.round(value) : null;
  } catch {
    state.weather = null;
  }
  renderAbuDhabiWeather();
}

function renderAbuDhabiWeather() {
  $("#abuDhabiWeather").textContent = state.weather === null ? "Weather --°C" : `Weather ${state.weather}°C`;
}

function departmentGroup(value = "") {
  const text = String(value).toLowerCase();
  if (text.includes("procurement")) return "Procurement";
  if (text.includes("p&c") || text.includes("admin") || text.includes("culture")) return "P&C and Administration";
  return "Operations";
}

async function signIn(email, password) {
  if (!client) throw new Error("Supabase anon key is not configured in assets/supabase-config.js.");
  const { data, error } = await client.auth.signInWithPassword({ email, password });
  if (error) throw error;
  await verifyPortalAccess();
  return data.session;
}

async function verifyPortalAccess() {
  const { data, error } = await client
    .from("admin_portal_users")
    .select("role,is_active")
    .eq("is_active", true)
    .maybeSingle();
  if (error) throw new Error("Your login worked, but the administration access rule is not ready yet.");
  if (!data) {
    await client.auth.signOut();
    throw new Error("This account is not approved for the Administration System.");
  }
  return data;
}

async function fetchRows(table) {
  const { data, error } = await client.from(table).select("*").order("id", { ascending: true }).limit(1000);
  if (error) throw error;
  return data || [];
}

async function upsertRow(table, row) {
  const { data, error } = await client.from(table).upsert(row).select().single();
  if (error) throw error;
  return data;
}

async function deleteRow(table, id) {
  const { error } = await client.from(table).delete().eq("id", id);
  if (error) throw error;
}

function renderShell() {
  $("#loginView").hidden = Boolean(state.session);
  $("#appView").hidden = !state.session;
  if (!state.session) return;

  const displayName = displayNameForEmail(state.session.user?.email);
  $("#roleLabel").textContent = `${displayName} · Secure Workspace`;
  $("#navList").innerHTML = pages.map((page) => (
    `<button class="nav-item ${state.page === page.key ? "active" : ""}" data-page="${page.key}">
      <span>${page.label}</span><span>${page.external ? "↗" : ""}</span>
    </button>`
  )).join("");
}

function setTopActions(mode) {
  const dashboardMode = mode === "dashboard";
  $(".topbar").classList.toggle("dashboard-topbar", dashboardMode);
  $(".table-search").hidden = dashboardMode;
  $("#dashboardMeta").hidden = !dashboardMode;
  $("#refreshButton").textContent = dashboardMode ? "Sign out" : "Refresh";
  $("#refreshButton").dataset.action = dashboardMode ? "signout" : "refresh";
  if (dashboardMode) {
    updateAbuDhabiTime();
    renderAbuDhabiWeather();
  }
}

function metric(label, value) {
  return `<article class="metric-card"><span>${label}</span><strong>${value}</strong></article>`;
}

function renderDashboard() {
  $("#dashboard").hidden = false;
  $("#tablePage").hidden = true;
  $("#pageTitle").textContent = "Dashboard";
  setTopActions("dashboard");

  const employeeCount = (state.rows.employees || []).length;
  const recruitmentOpen = (state.rows.recruitment || []).filter((row) => !["Joined", "Rejected"].includes(row.status)).length;
  const documentsDue = (state.rows.documents || []).filter((row) => row.status !== "Valid").length;
  const vendorCount = (state.rows.vendors || []).length;

  $("#dashboard").innerHTML = `
    <div class="summary-grid">
      ${metric("Employees", employeeCount)}
      ${metric("Open Recruitment", recruitmentOpen)}
      ${metric("Document Alerts", documentsDue)}
      ${metric("Vendors", vendorCount)}
    </div>
    <div class="glass empty-state">
      <h3>Citi Homes Administration</h3>
      <p>Manage Operations, P&C and Administration, Procurement, recruitment, attendance, pantry, vendors and office controls from one clean dashboard.</p>
    </div>
  `;
}

function filteredRows(page) {
  const rows = [...(state.rows[page.table] || [])];
  const search = state.search.trim().toLowerCase();
  return rows.filter((row) => {
    const deptOk = page.key !== "employees" || state.activeFilter === "All" || departmentGroup(row.department) === state.activeFilter;
    const searchOk = !search || Object.values(row).join(" ").toLowerCase().includes(search);
    return deptOk && searchOk;
  });
}

function renderTablePage(page) {
  $("#dashboard").hidden = true;
  $("#tablePage").hidden = false;
  $("#pageTitle").textContent = page.label;
  setTopActions("table");

  const rows = filteredRows(page);
  $("#summaryCards").innerHTML = `
    ${metric("Total Records", (state.rows[page.table] || []).length)}
    ${metric("Current View", rows.length)}
    ${metric("Added Today", rows.filter((row) => String(row.created_at || "").startsWith(new Date().toISOString().slice(0, 10))).length)}
    ${metric("Backend", "Supabase")}
  `;

  $("#pageTools").innerHTML = page.filters ? page.filters.map((item) => (
    `<button class="pill ${state.activeFilter === item ? "active" : ""}" data-filter="${item}">${item}</button>`
  )).join("") : "";

  renderTable(page, rows);
  renderForm(page);
}

function renderTable(page, rows) {
  const table = $("#dataTable");
  const cols = columns[page.table] || [];
  if (!rows.length) {
    table.innerHTML = `<tbody><tr><td class="empty-state">No records found.</td></tr></tbody>`;
    return;
  }
  table.innerHTML = `
    <thead><tr><th>Sr. No</th>${cols.map((col) => `<th>${titleize(col)}</th>`).join("")}<th>Actions</th></tr></thead>
    <tbody>
      ${rows.map((row, index) => `
        <tr data-id="${row.id || ""}">
          <td>${index + 1}</td>
          ${cols.map((col) => `<td>${fieldControl(col, row[col] ?? "")}</td>`).join("")}
          <td class="row-actions">
            <button data-save="${row.id}">Save</button>
            <button class="danger" data-delete="${row.id}">Delete</button>
          </td>
        </tr>
      `).join("")}
    </tbody>
  `;
}

function fieldControl(column, value) {
  const safeValue = String(value).replaceAll('"', "&quot;");
  if (options[column]) {
    return `<select data-field="${column}">${options[column].map((item) => `<option ${String(value) === item ? "selected" : ""}>${item}</option>`).join("")}</select>`;
  }
  const type = column.includes("date") || column.includes("expiry") || column.includes("renewal") ? "date" : "text";
  return `<input data-field="${column}" type="${type}" value="${safeValue}">`;
}

function renderForm(page) {
  const cols = columns[page.table] || [];
  $("#addRecordPanel").open = false;
  $("#recordForm").innerHTML = cols.map((col) => (
    `<label>${titleize(col)}${fieldControl(col, col === "department" ? "Operations" : "")}</label>`
  )).join("") + `<button type="submit">Add Record</button>`;
}

async function loadPageData() {
  const tables = pages.filter((page) => page.table).map((page) => page.table);
  await Promise.all(tables.map(async (table) => {
    state.rows[table] = await fetchRows(table);
  }));
}

async function showPage(key) {
  const page = pages.find((item) => item.key === key) || pages[0];
  if (page.external) {
    window.open(page.external, "_blank", "noopener");
    return;
  }
  state.page = page.key;
  renderShell();
  if (page.key === "dashboard") renderDashboard();
  else renderTablePage(page);
}

function rowFromElement(rowElement) {
  const row = {};
  if (rowElement.dataset.id) row.id = Number(rowElement.dataset.id);
  rowElement.querySelectorAll("[data-field]").forEach((input) => {
    const value = input.value.trim();
    if (value !== "") row[input.dataset.field] = value;
  });
  return row;
}

document.addEventListener("click", async (event) => {
  const pageButton = event.target.closest("[data-page]");
  const filterButton = event.target.closest("[data-filter]");
  const saveButton = event.target.closest("[data-save]");
  const deleteButton = event.target.closest("[data-delete]");

  try {
    if (pageButton) await showPage(pageButton.dataset.page);
    if (filterButton) {
      state.activeFilter = filterButton.dataset.filter;
      await showPage(state.page);
    }
    if (saveButton) {
      const page = pages.find((item) => item.key === state.page);
      await upsertRow(page.table, rowFromElement(saveButton.closest("tr")));
      state.rows[page.table] = await fetchRows(page.table);
      await showPage(state.page);
    }
    if (deleteButton && confirm("Delete this record?")) {
      const page = pages.find((item) => item.key === state.page);
      await deleteRow(page.table, deleteButton.dataset.delete);
      state.rows[page.table] = await fetchRows(page.table);
      await showPage(state.page);
    }
  } catch (error) {
    alert(error.message || error);
  }
});

$("#loginForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  $("#loginMessage").textContent = "";
  try {
    state.session = await signIn($("#username").value, $("#password").value);
    await loadPageData();
    renderShell();
    renderDashboard();
  } catch (error) {
    $("#loginMessage").textContent = error.message || "Login failed.";
  }
});

$("#logoutButton").addEventListener("click", async () => {
  if (client) await client.auth.signOut();
  state.session = null;
  state.rows = {};
  renderShell();
});

$("#refreshButton").addEventListener("click", async () => {
  if ($("#refreshButton").dataset.action === "signout") {
    if (client) await client.auth.signOut();
    state.session = null;
    state.rows = {};
    renderShell();
    return;
  }
  await loadPageData();
  await showPage(state.page);
});

$("#globalSearch").addEventListener("input", async (event) => {
  state.search = event.target.value;
  await showPage(state.page);
});

$("#recordForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const page = pages.find((item) => item.key === state.page);
  const row = rowFromElement(event.currentTarget);
  await upsertRow(page.table, row);
  state.rows[page.table] = await fetchRows(page.table);
  event.currentTarget.reset();
  await showPage(state.page);
});

(async function boot() {
  if (!client) {
    $("#loginMessage").textContent = "Supabase anon key is required before going live.";
    renderShell();
    return;
  }
  const { data } = await client.auth.getSession();
  state.session = data.session;
  renderShell();
  if (state.session) {
    await verifyPortalAccess();
    await loadPageData();
    await showPage(state.page);
  }
  updateAbuDhabiTime();
  setInterval(updateAbuDhabiTime, 30000);
  loadAbuDhabiWeather();
  setInterval(loadAbuDhabiWeather, 900000);
})();
