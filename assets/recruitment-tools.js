(function () {
  function csvCell(value) {
    const text = String(value || "").trim();
    return /[",\n\r]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
  }

  function visiblePageTitle() {
    return document.querySelector("#pageTitle")?.textContent?.trim() || "";
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
    const blob = new Blob([`\uFEFF${lines.join("\n")}`], { type: "text/csv;charset=utf-8" });
    const link = document.createElement("a");
    const href = URL.createObjectURL(blob);
    link.href = href;
    link.download = `${filenamePrefix}-${new Date().toISOString().slice(0, 10)}.csv`;
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

  const observer = new MutationObserver(addEmployeeExportButton);
  observer.observe(document.body, { childList: true, subtree: true });
  addEmployeeExportButton();
})();
