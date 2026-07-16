sanitizeLoginUrl();

const config = window.CITI_HOMES_SUPABASE || {};
const supabaseReady = Boolean(config.url && config.anonKey && config.anonKey.length > 20);
const client = supabaseReady ? window.supabase.createClient(config.url, config.anonKey) : null;

const pages = [
  { key: "dashboard", label: "Dashboard" },
  { key: "employees", label: "Employee Master", table: "employees", filters: ["All", "Operations", "P&C", "Procurement", "Finance"] },
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
  department: ["Operations", "P&C", "Procurement", "Finance"],
  status: ["Active", "Probation", "Inactive", "Applied", "Screening", "Shortlisted", "Interview Scheduled", "Selected", "Offer Sent", "Joined", "Rejected", "Hold", "Pending", "In Progress", "Completed", "Valid", "Expiring Soon", "Expired"],
  final_decision: ["Strongly recommended", "Recommended", "Recommended with reservations", "Do not recommend"],
  employment_type: ["Employee", "Contract", "Temporary", "Intern"],
  visa_status: ["Not Started", "Processing", "Issued", "Renewal", "On Hold", "Cancelled"],
  contract_status: ["Active", "Pending", "Expired", "Renewal"],
  reminder_sent: ["No", "Yes"]
};

const importAliases = {
  recruitment: {
    candidate: ["candidate", "candidate name", "name", "applicant", "applicant name"],
    position: ["position", "job title", "role", "designation", "applied position"],
    source: ["source", "cv source", "recruitment source"],
    mobile: ["mobile", "phone", "contact", "contact number", "mobile number"],
    location: ["location", "city", "current location"],
    gcc_experience: ["gcc experience", "gcc_experience", "gcc exp"],
    total_experience: ["total experience", "total_experience", "experience"],
    current_salary: ["current salary", "current_salary", "salary"],
    expected_salary: ["expected salary", "expected_salary", "expected"],
    notice_period: ["notice period", "notice_period", "notice"],
    interview_date: ["interview date", "interview_date", "date"],
    status: ["status", "stage"]
  }
};

let state = {
  session: null,
  portalUser: null,
  page: "dashboard",
  rows: {},
  activeFilter: "All",
  search: "",
  weather: null,
  savedRows: new Set()
};

const $ = (selector) => document.querySelector(selector);
const wait = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

function sanitizeLoginUrl() {
  const url = new URL(window.location.href);
  if (!url.searchParams.has("email") && !url.searchParams.has("password")) return;
  url.searchParams.delete("email");
  url.searchParams.delete("password");
  window.history.replaceState({}, document.title, `${url.pathname}${url.search}${url.hash}`);
}

const displayNames = {
  "umer@citihomes.ae": "Umer Raza",
  "test@citihomes.ae": "Test Profile"
};

const superUserEmails = new Set(["umer@citihomes.ae"]);
const viewerEmails = new Set(["test@citihomes.ae"]);
const dashboardTables = ["employees", "recruitment", "documents", "utilities"];

function titleize(value) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function displayNameForEmail(email = "") {
  const normalized = String(email).toLowerCase();
  return displayNames[normalized] || normalized || "Admin";
}

function normalizedEmail() {
  return String(state.session?.user?.email || "").toLowerCase();
}

function isSuperUser() {
  return superUserEmails.has(normalizedEmail()) || state.portalUser?.role === "Super User";
}

function isViewer() {
  return viewerEmails.has(normalizedEmail()) || state.portalUser?.role === "Viewer";
}

function canEdit() {
  return !isViewer();
}

function updateAbuDhabiTime() {
  const formatter = new Intl.DateTimeFormat("en-AE", {
    timeZone: "Asia/Dubai",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true
  });
  $("#abuDhabiTime").textContent = formatter.format(new Date());
}

async function loadAbuDhabiWeather() {
  try {
    const payload = await requestJson("https://api.open-meteo.com/v1/forecast?latitude=24.4539&longitude=54.3773&current=temperature_2m&timezone=Asia%2FDubai");
    const value = payload.current?.temperature_2m;
    state.weather = Number.isFinite(value) ? Math.round(value) : null;
  } catch {
    state.weather = null;
  }
  renderAbuDhabiWeather();
}

function requestJson(url) {
  if (typeof fetch === "function") {
    return fetch(url).then((response) => {
      if (!response.ok) throw new Error("Weather unavailable");
      return response.json();
    });
  }
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.open("GET", url, true);
    request.onload = () => {
      if (request.status < 200 || request.status >= 300) {
        reject(new Error("Weather unavailable"));
        return;
      }
      try {
        resolve(JSON.parse(request.responseText));
      } catch (error) {
        reject(error);
      }
    };
    request.onerror = () => reject(new Error("Weather unavailable"));
    request.send();
  });
}

function renderAbuDhabiWeather() {
  $("#abuDhabiWeather").textContent = state.weather === null ? "--°C" : `${state.weather}°C`;
}

function departmentGroup(value = "") {
  const text = String(value).toLowerCase();
  if (text.includes("procurement")) return "Procurement";
  if (text.includes("finance")) return "Finance";
  if (text.includes("p&c") || text.includes("admin") || text.includes("culture")) return "P&C";
  return "Operations";
}

async function signIn(email, password) {
  if (!client) throw new Error("Supabase anon key is not configured in assets/supabase-config.js.");
  const { data, error } = await client.auth.signInWithPassword({ email, password });
  if (error) throw error;
  state.portalUser = await verifyPortalAccess();
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

async function clearTable(table) {
  const { error } = await client.from(table).delete().not("id", "is", null);
  if (error) throw error;
}

function renderShell() {
  $("#loginView").hidden = Boolean(state.session);
  $("#appView").hidden = !state.session;
  if (!state.session) return;

  const displayName = displayNameForEmail(state.session.user?.email);
  $("#roleLabel").textContent = displayName;
  $("#accessLabel").textContent = "Team Member";
  $("#accessLabel").classList.remove("super-user-badge", "viewer-badge");
  $("#navList").innerHTML = pages.map((page) => (
    `<button class="nav-item ${state.page === page.key ? "active" : ""}" data-page="${page.key}">
      <span>${page.label}</span><span>${page.external ? "↗" : ""}</span>
    </button>`
  )).join("");
}

function setTopActions() {
  $(".topbar").classList.add("dashboard-topbar");
  $(".table-search").hidden = true;
  $("#dashboardMeta").hidden = false;
  $("#refreshButton").textContent = "Sign out";
  $("#refreshButton").dataset.action = "signout";
  updateAbuDhabiTime();
  renderAbuDhabiWeather();
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
  const utilityBillCount = (state.rows.utilities || []).length;

  $("#dashboard").innerHTML = `
    <div class="summary-grid">
      ${metric("Employees", employeeCount)}
      ${metric("Open Recruitment", recruitmentOpen)}
      ${metric("Document Alerts", documentsDue)}
      ${metric("Utility Bills", utilityBillCount)}
    </div>
    <div class="glass empty-state">
      <h3>Citi Homes Administration</h3>
      <p>Manage Operations, P&C and Administration, Procurement, recruitment, attendance, pantry, utility bills and office controls from one clean dashboard.</p>
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
  `;

  const filterTools = page.filters ? page.filters.map((item) => (
    `<button class="pill ${state.activeFilter === item ? "active" : ""}" data-filter="${item}">${item}</button>`
  )).join("") : "";
  const importTools = page.table === "recruitment" && canEdit()
    ? `<button class="pill import-button" data-import="recruitment">Import Recruitment Data</button>
       <button class="pill import-template-button" data-recruitment-template>Import Data Template</button>
       <button class="pill" data-export="recruitment">Export Candidates CSV</button>
       <button class="pill danger-outline" data-clear-table="recruitment">Clear Recruitment Data</button>
       <input id="recruitmentImportFile" type="file" accept=".csv,.xlsx,.xls" hidden>`
    : "";
  $("#pageTools").innerHTML = filterTools || importTools
    ? `${filterTools}${importTools}`
    : isViewer() ? `<span class="viewer-notice">View only mode</span>` : "";

  renderTable(page, rows);
  renderForm(page);
}

function renderTable(page, rows) {
  const table = $("#dataTable");
  const cols = columns[page.table] || [];
  table.className = page.table === "recruitment" ? "data-table compact-table recruitment-table" : "data-table";
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
            ${canEdit()
              ? `${saveButtonMarkup(page.table, row.id)}<button class="danger" data-delete="${row.id}">Delete</button>`
              : `<span class="view-only-pill">View only</span>`}
          </td>
        </tr>
      `).join("")}
    </tbody>
  `;
}

function saveButtonMarkup(table, id) {
  const saved = state.savedRows.has(`${table}:${id}`);
  return `<button class="save-button ${saved ? "saved" : ""}" data-save="${id}" aria-label="${saved ? "Saved" : "Save record"}">${saved ? "✓" : "Save"}</button>`;
}

function fieldControl(column, value) {
  const safeValue = String(value).replaceAll('"', "&quot;");
  const disabled = canEdit() ? "" : " disabled";
  if (options[column]) {
    return `<select data-field="${column}"${disabled}>${options[column].map((item) => `<option ${String(value) === item ? "selected" : ""}>${item}</option>`).join("")}</select>`;
  }
  const type = column.includes("date") || column.includes("expiry") || column.includes("renewal") ? "date" : "text";
  return `<input data-field="${column}" type="${type}" value="${safeValue}"${disabled}>`;
}

function renderForm(page) {
  const cols = columns[page.table] || [];
  $("#addRecordPanel").open = false;
  $("#addRecordPanel").hidden = isViewer();
  if (isViewer()) {
    $("#recordForm").innerHTML = "";
    return;
  }
  $("#addRecordPanel").hidden = false;
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

async function loadTables(tables, options = {}) {
  const uniqueTables = [...new Set(tables)];
  await Promise.all(uniqueTables.map(async (table) => {
    if (!options.force && state.rows[table]) return;
    state.rows[table] = await fetchRows(table);
  }));
}

async function loadDashboardData(options = {}) {
  await loadTables(dashboardTables, options);
}

async function ensurePageData(page, options = {}) {
  if (!page.table) return;
  await loadTables([page.table], options);
}

async function showPage(key) {
  const page = pages.find((item) => item.key === key) || pages[0];
  if (page.external) {
    window.open(page.external, "_blank", "noopener");
    return;
  }
  state.page = page.key;
  renderShell();
  if (page.key === "dashboard") {
    await loadDashboardData();
    renderDashboard();
  } else {
    await ensurePageData(page);
    renderTablePage(page);
  }
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

function normalizeHeader(value) {
  return String(value || "").trim().toLowerCase().replace(/[_-]+/g, " ").replace(/\s+/g, " ");
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let cell = "";
  let quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    const next = text[index + 1];
    if (char === '"' && quoted && next === '"') {
      cell += '"';
      index += 1;
    } else if (char === '"') {
      quoted = !quoted;
    } else if (char === "," && !quoted) {
      row.push(cell);
      cell = "";
    } else if ((char === "\n" || char === "\r") && !quoted) {
      if (char === "\r" && next === "\n") index += 1;
      row.push(cell);
      if (row.some((value) => String(value).trim() !== "")) rows.push(row);
      row = [];
      cell = "";
    } else {
      cell += char;
    }
  }
  row.push(cell);
  if (row.some((value) => String(value).trim() !== "")) rows.push(row);
  return rows;
}

function loadScript(src) {
  return new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${src}"]`);
    if (existing) {
      existing.addEventListener("load", resolve, { once: true });
      existing.addEventListener("error", reject, { once: true });
      return;
    }
    const script = document.createElement("script");
    script.src = src;
    script.onload = resolve;
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

async function ensureExcelLibrary() {
  if (window.XLSX) return;
  await loadScript("https://unpkg.com/xlsx@0.18.5/dist/xlsx.full.min.js");
  if (!window.XLSX) throw new Error("Excel import library could not load. Please upload CSV or try again.");
}

async function readImportRows(file) {
  if (file.name.toLowerCase().endsWith(".csv")) {
    return parseCsv(await file.text());
  }
  await ensureExcelLibrary();
  const buffer = await file.arrayBuffer();
  const workbook = window.XLSX.read(buffer, { type: "array", cellDates: false });
  const sheet = workbook.Sheets[workbook.SheetNames[0]];
  return window.XLSX.utils.sheet_to_json(sheet, { header: 1, raw: false, defval: "" });
}

function mapImportRows(table, rawRows) {
  const aliases = importAliases[table] || {};
  const tableColumns = columns[table] || [];
  const header = (rawRows[0] || []).map(normalizeHeader);
  return rawRows.slice(1).map((rawRow) => {
    const row = {};
    tableColumns.forEach((column) => {
      const match = [column, titleize(column), ...(aliases[column] || [])].map(normalizeHeader)
        .map((label) => header.indexOf(label))
        .find((index) => index >= 0);
      if (match === undefined) return;
      const value = String(rawRow[match] || "").trim();
      if (value !== "") row[column] = value;
    });
    if (!row.status) row.status = "Applied";
    return row;
  }).filter((row) => Object.keys(row).some((key) => key !== "status") && row.candidate);
}

async function importTableFile(table, file) {
  const rawRows = await readImportRows(file);
  if (rawRows.length < 2) throw new Error("No import rows found.");
  const rows = mapImportRows(table, rawRows);
  if (!rows.length) throw new Error("No valid rows found. Please make sure the file has a Candidate column.");
  const { error } = await client.from(table).insert(rows);
  if (error) throw error;
  return rows.length;
}

function csvCell(value) {
  const text = String(value ?? "");
  return /[",\n\r]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function exportTableCsv(table) {
  const page = pages.find((item) => item.table === table);
  const tableColumns = columns[table] || [];
  const rows = filteredRows(page);
  if (!rows.length) throw new Error("No candidate records available to export.");
  const header = ["Sr. No", ...tableColumns.map(titleize)];
  const lines = [
    header.map(csvCell).join(","),
    ...rows.map((row, index) => [index + 1, ...tableColumns.map((column) => row[column] ?? "")].map(csvCell).join(","))
  ];
  const blob = new Blob([`\uFEFF${lines.join("\n")}`], { type: "text/csv;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `recruitment-candidates-${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(link.href);
}

document.addEventListener("click", async (event) => {
  const pageButton = event.target.closest("[data-page]");
  const filterButton = event.target.closest("[data-filter]");
  const saveButton = event.target.closest("[data-save]");
  const deleteButton = event.target.closest("[data-delete]");
  const importButton = event.target.closest("[data-import]");
  const exportButton = event.target.closest("[data-export]");
  const clearButton = event.target.closest("[data-clear-table]");

  try {
    if (pageButton) await showPage(pageButton.dataset.page);
    if (filterButton) {
      state.activeFilter = filterButton.dataset.filter;
      await showPage(state.page);
    }
    if ((saveButton || deleteButton || importButton || exportButton || clearButton) && !canEdit()) {
      alert("This test profile is view-only.");
      return;
    }
    if (importButton) {
      $("#recruitmentImportFile")?.click();
    }
    if (exportButton) {
      exportTableCsv(exportButton.dataset.export);
    }
    if (clearButton && confirm("This will delete all Recruitment Tracker records. Continue?")) {
      clearButton.disabled = true;
      clearButton.textContent = "Clearing...";
      await clearTable(clearButton.dataset.clearTable);
      state.rows[clearButton.dataset.clearTable] = await fetchRows(clearButton.dataset.clearTable);
      await showPage(state.page);
    }
    if (saveButton) {
      const page = pages.find((item) => item.key === state.page);
      saveButton.disabled = true;
      saveButton.classList.add("saving");
      saveButton.textContent = "";
      const savedRow = await upsertRow(page.table, rowFromElement(saveButton.closest("tr")));
      await wait(650);
      state.savedRows.add(`${page.table}:${savedRow.id}`);
      saveButton.classList.remove("saving");
      saveButton.classList.add("saved");
      saveButton.textContent = "✓";
      await wait(850);
      state.savedRows.delete(`${page.table}:${savedRow.id}`);
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
    await loadDashboardData();
    renderShell();
    renderDashboard();
  } catch (error) {
    $("#loginMessage").textContent = error.message || "Login failed.";
  }
});

function setPasswordVisible(visible) {
  const password = $("#password");
  password.type = visible ? "text" : "password";
  $("#passwordToggle").textContent = visible ? "Hide" : "Show";
}

["mousedown", "touchstart", "pointerdown"].forEach((eventName) => {
  $("#passwordToggle").addEventListener(eventName, (event) => {
    event.preventDefault();
    setPasswordVisible(true);
  });
});

["mouseup", "mouseleave", "blur", "touchend", "touchcancel", "pointerup", "pointerleave", "pointercancel"].forEach((eventName) => {
  $("#passwordToggle").addEventListener(eventName, () => setPasswordVisible(false));
});

$("#logoutButton").addEventListener("click", async () => {
  if (client) await client.auth.signOut();
  state.session = null;
  state.portalUser = null;
  state.rows = {};
  renderShell();
});

$("#refreshButton").addEventListener("click", async () => {
  if ($("#refreshButton").dataset.action === "signout") {
    if (client) await client.auth.signOut();
    state.session = null;
    state.portalUser = null;
    state.rows = {};
    renderShell();
    return;
  }
  if (state.page === "dashboard") await loadDashboardData({ force: true });
  else {
    const page = pages.find((item) => item.key === state.page);
    await ensurePageData(page, { force: true });
  }
  await showPage(state.page);
});

$("#globalSearch").addEventListener("input", async (event) => {
  state.search = event.target.value;
  await showPage(state.page);
});

document.addEventListener("change", async (event) => {
  if (event.target.id !== "recruitmentImportFile") return;
  const file = event.target.files?.[0];
  if (!file) return;
  try {
    const count = await importTableFile("recruitment", file);
    event.target.value = "";
    state.rows.recruitment = await fetchRows("recruitment");
    await showPage("recruitment");
    alert(`${count} recruitment records imported.`);
  } catch (error) {
    alert(error.message || error);
  }
});

$("#recordForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!canEdit()) {
    alert("This test profile is view-only.");
    return;
  }
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
    state.portalUser = await verifyPortalAccess();
    await loadDashboardData();
    await showPage(state.page);
  }
  updateAbuDhabiTime();
  setInterval(updateAbuDhabiTime, 30000);
  loadAbuDhabiWeather();
  setInterval(loadAbuDhabiWeather, 900000);
})();
sanitizeLoginUrl();

const config = window.CITI_HOMES_SUPABASE || {};
const supabaseReady = Boolean(config.url && config.anonKey && config.anonKey.length > 20);
const client = supabaseReady ? window.supabase.createClient(config.url, config.anonKey) : null;

const pages = [
  { key: "dashboard", label: "Dashboard" },
  { key: "employees", label: "Employee Master", table: "employees", filters: ["All", "Operations", "P&C", "Procurement", "Finance"] },
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
  department: ["Operations", "P&C", "Procurement", "Finance"],
  status: ["Active", "Probation", "Inactive", "Applied", "Screening", "Shortlisted", "Interview Scheduled", "Selected", "Offer Sent", "Joined", "Rejected", "Hold", "Pending", "In Progress", "Completed", "Valid", "Expiring Soon", "Expired"],
  final_decision: ["Strongly recommended", "Recommended", "Recommended with reservations", "Do not recommend"],
  employment_type: ["Employee", "Contract", "Temporary", "Intern"],
  visa_status: ["Not Started", "Processing", "Issued", "Renewal", "On Hold", "Cancelled"],
  contract_status: ["Active", "Pending", "Expired", "Renewal"],
  reminder_sent: ["No", "Yes"]
};

const importAliases = {
  recruitment: {
    candidate: ["candidate", "candidate name", "name", "applicant", "applicant name"],
    position: ["position", "job title", "role", "designation", "applied position"],
    source: ["source", "cv source", "recruitment source"],
    mobile: ["mobile", "phone", "contact", "contact number", "mobile number"],
    location: ["location", "city", "current location"],
    gcc_experience: ["gcc experience", "gcc_experience", "gcc exp"],
    total_experience: ["total experience", "total_experience", "experience"],
    current_salary: ["current salary", "current_salary", "salary"],
    expected_salary: ["expected salary", "expected_salary", "expected"],
    notice_period: ["notice period", "notice_period", "notice"],
    interview_date: ["interview date", "interview_date", "date"],
    status: ["status", "stage"]
  }
};

let state = {
  session: null,
  portalUser: null,
  page: "dashboard",
  rows: {},
  activeFilter: "All",
  search: "",
  weather: null,
  savedRows: new Set()
};

const $ = (selector) => document.querySelector(selector);
const wait = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

function sanitizeLoginUrl() {
  const url = new URL(window.location.href);
  if (!url.searchParams.has("email") && !url.searchParams.has("password")) return;
  url.searchParams.delete("email");
  url.searchParams.delete("password");
  window.history.replaceState({}, document.title, `${url.pathname}${url.search}${url.hash}`);
}

const displayNames = {
  "umer@citihomes.ae": "Umer Raza",
  "test@citihomes.ae": "Test Profile"
};

const superUserEmails = new Set(["umer@citihomes.ae"]);
const viewerEmails = new Set(["test@citihomes.ae"]);
const dashboardTables = ["employees", "recruitment", "documents", "utilities"];

function titleize(value) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function displayNameForEmail(email = "") {
  const normalized = String(email).toLowerCase();
  return displayNames[normalized] || normalized || "Admin";
}

function normalizedEmail() {
  return String(state.session?.user?.email || "").toLowerCase();
}

function isSuperUser() {
  return superUserEmails.has(normalizedEmail()) || state.portalUser?.role === "Super User";
}

function isViewer() {
  return viewerEmails.has(normalizedEmail()) || state.portalUser?.role === "Viewer";
}

function canEdit() {
  return !isViewer();
}

function updateAbuDhabiTime() {
  const formatter = new Intl.DateTimeFormat("en-AE", {
    timeZone: "Asia/Dubai",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true
  });
  $("#abuDhabiTime").textContent = formatter.format(new Date());
}

async function loadAbuDhabiWeather() {
  try {
    const payload = await requestJson("https://api.open-meteo.com/v1/forecast?latitude=24.4539&longitude=54.3773&current=temperature_2m&timezone=Asia%2FDubai");
    const value = payload.current?.temperature_2m;
    state.weather = Number.isFinite(value) ? Math.round(value) : null;
  } catch {
    state.weather = null;
  }
  renderAbuDhabiWeather();
}

function requestJson(url) {
  if (typeof fetch === "function") {
    return fetch(url).then((response) => {
      if (!response.ok) throw new Error("Weather unavailable");
      return response.json();
    });
  }
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.open("GET", url, true);
    request.onload = () => {
      if (request.status < 200 || request.status >= 300) {
        reject(new Error("Weather unavailable"));
        return;
      }
      try {
        resolve(JSON.parse(request.responseText));
      } catch (error) {
        reject(error);
      }
    };
    request.onerror = () => reject(new Error("Weather unavailable"));
    request.send();
  });
}

function renderAbuDhabiWeather() {
  $("#abuDhabiWeather").textContent = state.weather === null ? "--°C" : `${state.weather}°C`;
}

function departmentGroup(value = "") {
  const text = String(value).toLowerCase();
  if (text.includes("procurement")) return "Procurement";
  if (text.includes("finance")) return "Finance";
  if (text.includes("p&c") || text.includes("admin") || text.includes("culture")) return "P&C";
  return "Operations";
}

async function signIn(email, password) {
  if (!client) throw new Error("Supabase anon key is not configured in assets/supabase-config.js.");
  const { data, error } = await client.auth.signInWithPassword({ email, password });
  if (error) throw error;
  state.portalUser = await verifyPortalAccess();
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

async function clearTable(table) {
  const { error } = await client.from(table).delete().not("id", "is", null);
  if (error) throw error;
}

function renderShell() {
  $("#loginView").hidden = Boolean(state.session);
  $("#appView").hidden = !state.session;
  if (!state.session) return;

  const displayName = displayNameForEmail(state.session.user?.email);
  $("#roleLabel").textContent = displayName;
  $("#accessLabel").textContent = "Team Member";
  $("#accessLabel").classList.remove("super-user-badge", "viewer-badge");
  $("#navList").innerHTML = pages.map((page) => (
    `<button class="nav-item ${state.page === page.key ? "active" : ""}" data-page="${page.key}">
      <span>${page.label}</span><span>${page.external ? "↗" : ""}</span>
    </button>`
  )).join("");
}

function setTopActions() {
  $(".topbar").classList.add("dashboard-topbar");
  $(".table-search").hidden = true;
  $("#dashboardMeta").hidden = false;
  $("#refreshButton").textContent = "Sign out";
  $("#refreshButton").dataset.action = "signout";
  updateAbuDhabiTime();
  renderAbuDhabiWeather();
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
  const utilityBillCount = (state.rows.utilities || []).length;

  $("#dashboard").innerHTML = `
    <div class="summary-grid">
      ${metric("Employees", employeeCount)}
      ${metric("Open Recruitment", recruitmentOpen)}
      ${metric("Document Alerts", documentsDue)}
      ${metric("Utility Bills", utilityBillCount)}
    </div>
    <div class="glass empty-state">
      <h3>Citi Homes Administration</h3>
      <p>Manage Operations, P&C and Administration, Procurement, recruitment, attendance, pantry, utility bills and office controls from one clean dashboard.</p>
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
  `;

  const filterTools = page.filters ? page.filters.map((item) => (
    `<button class="pill ${state.activeFilter === item ? "active" : ""}" data-filter="${item}">${item}</button>`
  )).join("") : "";
  const importTools = page.table === "recruitment" && canEdit()
    ? `<button class="pill import-button" data-import="recruitment">Import Recruitment Data</button>
       <button class="pill" data-export="recruitment">Export Candidates CSV</button>
       <button class="pill danger-outline" data-clear-table="recruitment">Clear Recruitment Data</button>
       <input id="recruitmentImportFile" type="file" accept=".csv,.xlsx,.xls" hidden>`
    : "";
  $("#pageTools").innerHTML = filterTools || importTools
    ? `${filterTools}${importTools}`
    : isViewer() ? `<span class="viewer-notice">View only mode</span>` : "";

  renderTable(page, rows);
  renderForm(page);
}

function renderTable(page, rows) {
  const table = $("#dataTable");
  const cols = columns[page.table] || [];
  table.className = page.table === "recruitment" ? "data-table compact-table recruitment-table" : "data-table";
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
            ${canEdit()
              ? `${saveButtonMarkup(page.table, row.id)}<button class="danger" data-delete="${row.id}">Delete</button>`
              : `<span class="view-only-pill">View only</span>`}
          </td>
        </tr>
      `).join("")}
    </tbody>
  `;
}

function saveButtonMarkup(table, id) {
  const saved = state.savedRows.has(`${table}:${id}`);
  return `<button class="save-button ${saved ? "saved" : ""}" data-save="${id}" aria-label="${saved ? "Saved" : "Save record"}">${saved ? "✓" : "Save"}</button>`;
}

function fieldControl(column, value) {
  const safeValue = String(value).replaceAll('"', "&quot;");
  const disabled = canEdit() ? "" : " disabled";
  if (options[column]) {
    return `<select data-field="${column}"${disabled}>${options[column].map((item) => `<option ${String(value) === item ? "selected" : ""}>${item}</option>`).join("")}</select>`;
  }
  const type = column.includes("date") || column.includes("expiry") || column.includes("renewal") ? "date" : "text";
  return `<input data-field="${column}" type="${type}" value="${safeValue}"${disabled}>`;
}

function renderForm(page) {
  const cols = columns[page.table] || [];
  $("#addRecordPanel").open = false;
  $("#addRecordPanel").hidden = isViewer();
  if (isViewer()) {
    $("#recordForm").innerHTML = "";
    return;
  }
  $("#addRecordPanel").hidden = false;
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

async function loadTables(tables, options = {}) {
  const uniqueTables = [...new Set(tables)];
  await Promise.all(uniqueTables.map(async (table) => {
    if (!options.force && state.rows[table]) return;
    state.rows[table] = await fetchRows(table);
  }));
}

async function loadDashboardData(options = {}) {
  await loadTables(dashboardTables, options);
}

async function ensurePageData(page, options = {}) {
  if (!page.table) return;
  await loadTables([page.table], options);
}

async function showPage(key) {
  const page = pages.find((item) => item.key === key) || pages[0];
  if (page.external) {
    window.open(page.external, "_blank", "noopener");
    return;
  }
  state.page = page.key;
  renderShell();
  if (page.key === "dashboard") {
    await loadDashboardData();
    renderDashboard();
  } else {
    await ensurePageData(page);
    renderTablePage(page);
  }
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

function normalizeHeader(value) {
  return String(value || "").trim().toLowerCase().replace(/[_-]+/g, " ").replace(/\s+/g, " ");
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let cell = "";
  let quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    const next = text[index + 1];
    if (char === '"' && quoted && next === '"') {
      cell += '"';
      index += 1;
    } else if (char === '"') {
      quoted = !quoted;
    } else if (char === "," && !quoted) {
      row.push(cell);
      cell = "";
    } else if ((char === "\n" || char === "\r") && !quoted) {
      if (char === "\r" && next === "\n") index += 1;
      row.push(cell);
      if (row.some((value) => String(value).trim() !== "")) rows.push(row);
      row = [];
      cell = "";
    } else {
      cell += char;
    }
  }
  row.push(cell);
  if (row.some((value) => String(value).trim() !== "")) rows.push(row);
  return rows;
}

function loadScript(src) {
  return new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${src}"]`);
    if (existing) {
      existing.addEventListener("load", resolve, { once: true });
      existing.addEventListener("error", reject, { once: true });
      return;
    }
    const script = document.createElement("script");
    script.src = src;
    script.onload = resolve;
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

async function ensureExcelLibrary() {
  if (window.XLSX) return;
  await loadScript("https://unpkg.com/xlsx@0.18.5/dist/xlsx.full.min.js");
  if (!window.XLSX) throw new Error("Excel import library could not load. Please upload CSV or try again.");
}

async function readImportRows(file) {
  if (file.name.toLowerCase().endsWith(".csv")) {
    return parseCsv(await file.text());
  }
  await ensureExcelLibrary();
  const buffer = await file.arrayBuffer();
  const workbook = window.XLSX.read(buffer, { type: "array", cellDates: false });
  const sheet = workbook.Sheets[workbook.SheetNames[0]];
  return window.XLSX.utils.sheet_to_json(sheet, { header: 1, raw: false, defval: "" });
}

function mapImportRows(table, rawRows) {
  const aliases = importAliases[table] || {};
  const tableColumns = columns[table] || [];
  const header = (rawRows[0] || []).map(normalizeHeader);
  return rawRows.slice(1).map((rawRow) => {
    const row = {};
    tableColumns.forEach((column) => {
      const match = [column, titleize(column), ...(aliases[column] || [])].map(normalizeHeader)
        .map((label) => header.indexOf(label))
        .find((index) => index >= 0);
      if (match === undefined) return;
      const value = String(rawRow[match] || "").trim();
      if (value !== "") row[column] = value;
    });
    if (!row.status) row.status = "Applied";
    return row;
  }).filter((row) => Object.keys(row).some((key) => key !== "status") && row.candidate);
}

async function importTableFile(table, file) {
  const rawRows = await readImportRows(file);
  if (rawRows.length < 2) throw new Error("No import rows found.");
  const rows = mapImportRows(table, rawRows);
  if (!rows.length) throw new Error("No valid rows found. Please make sure the file has a Candidate column.");
  const { error } = await client.from(table).insert(rows);
  if (error) throw error;
  return rows.length;
}

function csvCell(value) {
  const text = String(value ?? "");
  return /[",\n\r]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function exportTableCsv(table) {
  const page = pages.find((item) => item.table === table);
  const tableColumns = columns[table] || [];
  const rows = filteredRows(page);
  if (!rows.length) throw new Error("No candidate records available to export.");
  const header = ["Sr. No", ...tableColumns.map(titleize)];
  const lines = [
    header.map(csvCell).join(","),
    ...rows.map((row, index) => [index + 1, ...tableColumns.map((column) => row[column] ?? "")].map(csvCell).join(","))
  ];
  const blob = new Blob([`\uFEFF${lines.join("\n")}`], { type: "text/csv;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `recruitment-candidates-${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(link.href);
}

document.addEventListener("click", async (event) => {
  const pageButton = event.target.closest("[data-page]");
  const filterButton = event.target.closest("[data-filter]");
  const saveButton = event.target.closest("[data-save]");
  const deleteButton = event.target.closest("[data-delete]");
  const importButton = event.target.closest("[data-import]");
  const exportButton = event.target.closest("[data-export]");
  const clearButton = event.target.closest("[data-clear-table]");

  try {
    if (pageButton) await showPage(pageButton.dataset.page);
    if (filterButton) {
      state.activeFilter = filterButton.dataset.filter;
      await showPage(state.page);
    }
    if ((saveButton || deleteButton || importButton || exportButton || clearButton) && !canEdit()) {
      alert("This test profile is view-only.");
      return;
    }
    if (importButton) {
      $("#recruitmentImportFile")?.click();
    }
    if (exportButton) {
      exportTableCsv(exportButton.dataset.export);
    }
    if (clearButton && confirm("This will delete all Recruitment Tracker records. Continue?")) {
      clearButton.disabled = true;
      clearButton.textContent = "Clearing...";
      await clearTable(clearButton.dataset.clearTable);
      state.rows[clearButton.dataset.clearTable] = await fetchRows(clearButton.dataset.clearTable);
      await showPage(state.page);
    }
    if (saveButton) {
      const page = pages.find((item) => item.key === state.page);
      saveButton.disabled = true;
      saveButton.classList.add("saving");
      saveButton.textContent = "";
      const savedRow = await upsertRow(page.table, rowFromElement(saveButton.closest("tr")));
      await wait(650);
      state.savedRows.add(`${page.table}:${savedRow.id}`);
      saveButton.classList.remove("saving");
      saveButton.classList.add("saved");
      saveButton.textContent = "✓";
      await wait(850);
      state.savedRows.delete(`${page.table}:${savedRow.id}`);
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
    await loadDashboardData();
    renderShell();
    renderDashboard();
  } catch (error) {
    $("#loginMessage").textContent = error.message || "Login failed.";
  }
});

function setPasswordVisible(visible) {
  const password = $("#password");
  password.type = visible ? "text" : "password";
  $("#passwordToggle").textContent = visible ? "Hide" : "Show";
}

["mousedown", "touchstart", "pointerdown"].forEach((eventName) => {
  $("#passwordToggle").addEventListener(eventName, (event) => {
    event.preventDefault();
    setPasswordVisible(true);
  });
});

["mouseup", "mouseleave", "blur", "touchend", "touchcancel", "pointerup", "pointerleave", "pointercancel"].forEach((eventName) => {
  $("#passwordToggle").addEventListener(eventName, () => setPasswordVisible(false));
});

$("#logoutButton").addEventListener("click", async () => {
  if (client) await client.auth.signOut();
  state.session = null;
  state.portalUser = null;
  state.rows = {};
  renderShell();
});

$("#refreshButton").addEventListener("click", async () => {
  if ($("#refreshButton").dataset.action === "signout") {
    if (client) await client.auth.signOut();
    state.session = null;
    state.portalUser = null;
    state.rows = {};
    renderShell();
    return;
  }
  if (state.page === "dashboard") await loadDashboardData({ force: true });
  else {
    const page = pages.find((item) => item.key === state.page);
    await ensurePageData(page, { force: true });
  }
  await showPage(state.page);
});

$("#globalSearch").addEventListener("input", async (event) => {
  state.search = event.target.value;
  await showPage(state.page);
});

document.addEventListener("change", async (event) => {
  if (event.target.id !== "recruitmentImportFile") return;
  const file = event.target.files?.[0];
  if (!file) return;
  try {
    const count = await importTableFile("recruitment", file);
    event.target.value = "";
    state.rows.recruitment = await fetchRows("recruitment");
    await showPage("recruitment");
    alert(`${count} recruitment records imported.`);
  } catch (error) {
    alert(error.message || error);
  }
});

$("#recordForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!canEdit()) {
    alert("This test profile is view-only.");
    return;
  }
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
    state.portalUser = await verifyPortalAccess();
    await loadDashboardData();
    await showPage(state.page);
  }
  updateAbuDhabiTime();
  setInterval(updateAbuDhabiTime, 30000);
  loadAbuDhabiWeather();
  setInterval(loadAbuDhabiWeather, 900000);
})();
