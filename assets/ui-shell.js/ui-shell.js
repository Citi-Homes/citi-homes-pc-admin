(function () {
  function normalizeLogoutText() {
    var button = document.getElementById("refreshButton");
    if (button && button.textContent.trim() !== "Logout") button.textContent = "Logout";
  }

  function setupPasswordToggle() {
    var input = document.getElementById("password");
    var button = document.getElementById("passwordToggle");
    if (!input || !button || button.dataset.passwordReady === "true") return;

    button.dataset.passwordReady = "true";
    button.textContent = "Eye";
    button.setAttribute("aria-label", "Hold to show password");
    button.setAttribute("title", "Hold to show password");

    function showPassword(event) {
      if (event) event.preventDefault();
      input.type = "text";
      button.classList.add("password-visible");
    }

    function hidePassword(event) {
      if (event) event.preventDefault();
      input.type = "password";
      button.classList.remove("password-visible");
    }

    button.addEventListener("pointerdown", showPassword);
    button.addEventListener("pointerup", hidePassword);
    button.addEventListener("pointercancel", hidePassword);
    button.addEventListener("pointerleave", hidePassword);
    button.addEventListener("blur", hidePassword);
    button.addEventListener("keydown", function (event) {
      if (event.key === " " || event.key === "Enter") showPassword(event);
    });
    button.addEventListener("keyup", function (event) {
      if (event.key === " " || event.key === "Enter") hidePassword(event);
    });
  }

  function refreshUiHelpers() {
    normalizeLogoutText();
    setupPasswordToggle();
  }

  function markActionButton(button) {
    if (!button || button.classList.contains("action-working") || button.classList.contains("action-done")) return;
    button.dataset.originalText = button.textContent.trim();
    button.classList.add("action-working");
    button.textContent = "";
    window.setTimeout(function () {
      button.classList.remove("action-working");
      button.classList.add("action-done");
      button.textContent = "✓";
    }, 360);
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest("[data-save], [data-delete]");
    if (!button) return;
    markActionButton(button);
  }, true);

  refreshUiHelpers();
  new MutationObserver(refreshUiHelpers).observe(document.body, { childList: true, subtree: true });
})();
