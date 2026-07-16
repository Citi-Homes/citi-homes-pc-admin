(function () {
  function csvCell(value) {
    const text = String(value || "").trim();
    return /[",\n\r]/.test(text) ? '"' + text.replaceAll('"', '""') + '"' : text;
  }

  function visiblePageTitle() {
    return document.querySelector("#pageTitle")?.textContent?.trim() || "";
  }

  function cleanNumericImportValue(value) {
    const text = String(value || "").trim().replaceAll(",", "");
    const match = text.match(/-?\d+(\.\d+)?/);
    return match ? Number(match[0]) : null;
  }

  function normalizeImportHeader(value) {
    return String(value || "").trim().toLowerCase().replace(/[_-]+/g, " ").replace(/\s+/g, " ");
  }

  function titleizeImportColumn(value) {
    return String(value || "").replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());
  }

  function looksLikeImportDate(value) {
    const text = String(value || "").trim();
    return /^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$/.test(text) ||
      /^\d{4}[/-]\d{1,2}[/-]\d{1,2}$/.test(text) ||
      /^\d{1,2}\s+[A-Za-z]{3,}\s+\d{2,4}$/.test(text);
  }

  function cleanRecruitmentImportValue(column, value) {
    const numericColumns = new Set([
      "gcc_experience",
      "total_experience",
      "current_salary",
      "expected_salary",
      "notice_period"
    ]);

    if (!numericColumns.has(column)) return String(value || "").trim();

    const numberValue = cleanNumericImportValue(value);
    return numberValue === null ? "" : numberValue;
  }

  function patchRecruitmentImporter() {
    const importColumns = {
      recruitment: ["candidate", "position", "source", "mobile", "location", "gcc_experience", "total_experience", "current_salary", "expected_salary", "notice_period", "interview_date", "status"]
    };

    const aliases = {
      candidate: ["candidate", "candidate name", "full name", "applicant", "applicant name", "name"],
      position: ["position", "job title", "role", "designation"],
      source: ["source", "cv source", "recruitment source"],
      mobile: ["mobile", "phone", "contact number"],
      location: ["location", "city", "current location"],
      gcc_experience: ["gcc experience", "gcc exp"],
      total_experience: ["total experience", "experience"],
      current_salary: ["current salary", "salary"],
      expected_salary: ["expected salary", "expected"],
      notice_period: ["notice period", "notice"],
      interview_date: ["interview date", "date"],
      status: ["status", "stage"]
    };

    window.mapImportRows = function mapImportRows(table, rawRows) {
      const cols = importColumns[table] || [];
      const header = (rawRows[0] || []).map(normalizeImportHeader);
      return rawRows.slice(1).map((rawRow) => {
        const row = {};
        cols.forEach((column) => {
          const labels = [column, titleizeImportColumn(column), ...(aliases[column] || [])].map(normalizeImportHeader);
          const index = labels.map((label) => header.indexOf(label)).find((match) => match >= 0);
          if (index === undefined) return;
          const value = String(rawRow[index] || "").trim();
          const cleanedValue = table === "recruitment" ? cleanRecruitmentImportValue(column, value) : value;
          if (cleanedValue !== "") row[column] = cleanedValue;
        });
        if (!row.status && table === "recruitment") row.status = "Applied";
        return row;
      }).filter((row) => row.candidate && !looksLikeImportDate(row.candidate));
    };
  }

  function addEmployeeExportButton() {
    const tools = document.querySelector("#pageTools");
    if (!tools || visiblePageTitle() !== "Employee Master") return;
    if (tools.querySelector("[data-export-employees]")) return;

    const button = document.createElement("button");
    button.type = "button";
    button.className = "pill";
    button.dataset.exportEmployees = "true";
    button.textContent = "Export Employee Master Data";
    tools.appendChild(button);
  }

  function reorderRecruitmentButtons() {
    const tools = document.querySelector("#pageTools");
    if (!tools || visiblePageTitle() !== "Recruitment Tracker") return;
    const importButton = tools.querySelector("[data-import='recruitment']");
    const templateButton = tools.querySelector("[data-recruitment-template]");
    if (importButton && templateButton && importButton.nextElementSibling !== templateButton) {
      importButton.after(templateButton);
    }
  }

  function exportVisibleTable(filenamePrefix, emptyMessage) {
    const table = document.querySelector("#dataTable");
    if (!table) {
      alert("Table is not available.");
      return;
    }

    const headers = [...table.querySelectorAll("thead th")].map((cell) => cell.textContent.trim());
    const rows = [...table.querySelectorAll("tbody tr")].map((row) => (
      [...row.querySelectorAll("td")].map((cell) => {
        const field = cell.querySelector("input, select, textarea");
        return field ? field.value : cell.textContent.trim();
      })
    ));

    if (!headers.length || !rows.length || rows.every((row) => row.join("").includes("No records found"))) {
      alert(emptyMessage);
      return;
    }

    const lines = [headers, ...rows].map((row) => row.map(csvCell).join(","));
    const blob = new Blob(["\uFEFF" + lines.join("\n")], { type: "text/csv;charset=utf-8" });
    const link = document.createElement("a");
    const href = URL.createObjectURL(blob);
    link.href = href;
    link.download = filenamePrefix + "-" + new Date().toISOString().slice(0, 10) + ".csv";
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(href), 1000);
  }

  document.addEventListener("click", (event) => {
    if (event.target.closest("[data-export-employees]")) {
      event.preventDefault();
      exportVisibleTable("employee-master", "No employee records available to export.");
    }
  });

  const observer = new MutationObserver(() => {
    addEmployeeExportButton();
    reorderRecruitmentButtons();
    patchRecruitmentImporter();
  });
  observer.observe(document.body, { childList: true, subtree: true });
  addEmployeeExportButton();
  reorderRecruitmentButtons();
  patchRecruitmentImporter();
})();
