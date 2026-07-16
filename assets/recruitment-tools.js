(function () {
  const superUserEmails = new Set(["umer@citihomes.ae"]);

  function currentEmail() {
    for (let index = 0; index < localStorage.length; index += 1) {
      const key = localStorage.key(index);
      const value = localStorage.getItem(key);
      if (!value || !key.toLowerCase().includes("auth")) continue;
      try {
        const parsed = JSON.parse(value);
        const email = parsed?.user?.email || parsed?.session?.user?.email || parsed?.currentSession?.user?.email;
        if (email) return String(email).toLowerCase();
      } catch {}
    }
    return "";
  }

  function isSuperUser() {
    return superUserEmails.has(currentEmail());
  }

  let scheduled = false;
  function schedulePageTools() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => {
      scheduled = false;
      addPageTools();
    });
  }

  function csvCell(value) {
    const text = String(value || "").trim();
    return /[",\n\r]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
  }

  function addPageTools() {
    const pageTitle = document.querySelector("#pageTitle");
    const tools = document.querySelector("#pageTools");
    if (!pageTitle || !tools) return;

    const title = pageTitle.textContent.trim();
    if (title === "Employee Master") {
      addEmployeeExportButton(tools);
      return;
    }

    if (title !== "Recruitment Tracker") return;
    const importButton = tools.querySelector("[data-import='recruitment']");
    const clearButton = tools.querySelector("[data-clear-table]");
    const templateButton = addTemplateButton(tools);
    let button = tools.querySelector("[data-export='recruitment'], [data-export-candidates]");

    if (!button) {
      button = document.createElement("button");
      button.type = "button";
      button.className = "pill";
      button.dataset.exportCandidates = "true";
    }

    button.textContent = "Export Recruitment Data";
    if (templateButton) templateButton.insertAdjacentElement("afterend", button);
    else if (importButton) importButton.insertAdjacentElement("afterend", button);
    else tools.insertBefore(button, clearButton || null);

    if (clearButton) {
      clearButton.textContent = "Clear Recruitment Data";
      clearButton.hidden = !isSuperUser();
      tools.appendChild(clearButton);
    }

    addTemplateButton();
  }

  function addEmployeeExportButton(tools) {
    if (tools.querySelector("[data-export-employees]")) return;
    const button = document.createElement("button");
    button.type = "button";
    button.className = "pill";
    button.dataset.exportEmployees = "true";
    button.textContent = "Export Employee Master Data";
    tools.appendChild(button);
  }

  function addTemplateButton() {
    const pageTitle = document.querySelector("#pageTitle");
    const tools = document.querySelector("#pageTools");
    if (!pageTitle || !tools || pageTitle.textContent.trim() !== "Recruitment Tracker") return null;
    let button = tools.querySelector("[data-recruitment-template]");
    if (button) return button;
    button = document.createElement("button");
    button.type = "button";
    button.className = "pill import-template-button";
    button.dataset.recruitmentTemplate = "true";
    button.textContent = "Import Data Template";
    const importButton = tools.querySelector("[data-import='recruitment']");
    if (importButton) importButton.insertAdjacentElement("afterend", button);
    else tools.appendChild(button);
    return button;
  }

  function exportVisibleTable(filenamePrefix, emptyMessage) {
    const table = document.querySelector("#dataTable");
    if (!table) return alert("Table is not available.");
    const headers = [...table.querySelectorAll("thead th")].map((cell) => cell.textContent.trim());
    const rows = [...table.querySelectorAll("tbody tr")].map((row) => (
      [...row.querySelectorAll("td")].map((cell) => {
        const field = cell.querySelector("input, select");
        return field ? field.value : cell.textContent.trim();
      })
    ));
    if (!rows.length || rows.every((row) => row.join("").includes("No records found"))) {
      alert(emptyMessage);
      return;
    }
    const lines = [headers, ...rows].map((row) => row.map(csvCell).join(","));
    const blob = new Blob([`\uFEFF${lines.join("\n")}`], { type: "text/csv;charset=utf-8" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `${filenamePrefix}-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(link);
    link.click();
    URL.revokeObjectURL(link.href);
    link.remove();
  }

  function exportCandidates() {
    exportVisibleTable("recruitment-candidates", "No candidate records available to export.");
  }

  function exportEmployees() {
    exportVisibleTable("employee-master", "No employee records available to export.");
  }

  function downloadTemplate() {
    const headers = [
      "Candidate",
      "Position",
      "Source",
      "Mobile",
      "Location",
      "GCC Experience",
      "Total Experience",
      "Current Salary",
      "Expected Salary",
      "Notice Period",
      "Interview Date",
      "Status"
    ];
    const sample = [
      "Candidate Name",
      "Position Applied",
      "LinkedIn / Referral / Walk-in",
      "05xxxxxxxx",
      "Abu Dhabi",
      "2 Years",
      "5 Years",
      "5000",
      "7000",
      "30 Days",
      "2026-07-16",
      "Applied"
    ];
    const lines = [headers, sample].map((row) => row.map(csvCell).join(","));
    const blob = new Blob([`\uFEFF${lines.join("\n")}`], { type: "text/csv;charset=utf-8" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "recruitment-import-template.csv";
    document.body.appendChild(link);
    link.click();
    URL.revokeObjectURL(link.href);
    link.remove();
  }

  document.addEventListener("click", (event) => {
    if (event.target.closest("[data-export-candidates], [data-export='recruitment']")) {
      event.preventDefault();
      exportCandidates();
    }
    if (event.target.closest("[data-export-employees]")) {
      event.preventDefault();
      exportEmployees();
    }
    if (event.target.closest("[data-recruitment-template]")) {
      event.preventDefault();
      downloadTemplate();
    }
    setTimeout(schedulePageTools, 50);
  });

  new MutationObserver((mutations) => {
    const shouldUpdate = mutations.some((mutation) => (
      mutation.target.id === "pageTools" ||
      mutation.target.id === "addRecordPanel" ||
      mutation.target.id === "pageTitle" ||
      mutation.target.closest?.("#pageTools, #addRecordPanel, #tablePage")
    ));
    if (shouldUpdate) schedulePageTools();
  }).observe(document.body, { childList: true, subtree: true });
  schedulePageTools();
})();
