(function () {
  function csvCell(value) {
    const text = String(value || "").trim();
    return /[",\n\r]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
  }

  function addExportButton() {
    const pageTitle = document.querySelector("#pageTitle");
    const tools = document.querySelector("#pageTools");
    if (!pageTitle || !tools || pageTitle.textContent.trim() !== "Recruitment Tracker") return;
    if (tools.querySelector("[data-export-candidates]")) return;
    const button = document.createElement("button");
    button.type = "button";
    button.className = "pill";
    button.dataset.exportCandidates = "true";
    button.textContent = "Export Candidates CSV";
    const clearButton = tools.querySelector("[data-clear-table]");
    tools.insertBefore(button, clearButton || null);
  }

  function exportCandidates() {
    const table = document.querySelector("#dataTable");
    if (!table) return alert("Recruitment table is not available.");
    const headers = [...table.querySelectorAll("thead th")].map((cell) => cell.textContent.trim());
    const rows = [...table.querySelectorAll("tbody tr")].map((row) => (
      [...row.querySelectorAll("td")].map((cell) => {
        const field = cell.querySelector("input, select");
        return field ? field.value : cell.textContent.trim();
      })
    ));
    if (!rows.length || rows.every((row) => row.join("").includes("No records found"))) {
      alert("No candidate records available to export.");
      return;
    }
    const lines = [headers, ...rows].map((row) => row.map(csvCell).join(","));
    const blob = new Blob([`\uFEFF${lines.join("\n")}`], { type: "text/csv;charset=utf-8" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `recruitment-candidates-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(link);
    link.click();
    URL.revokeObjectURL(link.href);
    link.remove();
  }

  document.addEventListener("click", (event) => {
    if (event.target.closest("[data-export-candidates]")) exportCandidates();
    setTimeout(addExportButton, 50);
  });

  new MutationObserver(addExportButton).observe(document.body, { childList: true, subtree: true });
  addExportButton();
})();
