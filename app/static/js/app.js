(function initSidebar() {
  const sidebar = document.getElementById("sidebar");
  const page = document.getElementById("page");
  const openBtn = document.getElementById("sidebar-open");
  const toggleBtn = document.getElementById("sidebar-toggle");
  if (!sidebar || !page || !openBtn || !toggleBtn) return;

  function setCollapsed(collapsed) {
    sidebar.classList.toggle("collapsed", collapsed);
    page.classList.toggle("sidebar-collapsed", collapsed);
    openBtn.classList.toggle("visible", collapsed);
    localStorage.setItem("sidebar-collapsed", collapsed ? "true" : "false");
  }

  const stored = localStorage.getItem("sidebar-collapsed");
  const initialCollapsed = stored === null ? window.innerWidth <= 720 : stored === "true";
  setCollapsed(initialCollapsed);

  toggleBtn.addEventListener("click", () => setCollapsed(true));
  openBtn.addEventListener("click", () => setCollapsed(false));
})();

(function initThemeSwitcher() {
  const buttons = document.querySelectorAll("[data-theme-option]");
  if (!buttons.length) return;

  function currentTheme() {
    return document.documentElement.getAttribute("data-theme") === "light" ? "light" : "dark";
  }

  function applyActive() {
    const theme = currentTheme();
    buttons.forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.themeOption === theme);
    });
  }

  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      if (btn.dataset.themeOption === "light") {
        document.documentElement.setAttribute("data-theme", "light");
      } else {
        document.documentElement.removeAttribute("data-theme");
      }
      localStorage.setItem("theme", btn.dataset.themeOption);
      applyActive();
    });
  });

  applyActive();
})();

(function initAuthForms() {
  function showError(form, message) {
    const errorEl = form.querySelector(".auth-error");
    if (!errorEl) return;
    errorEl.textContent = message;
    errorEl.classList.add("visible");
  }

  function setLoading(form, loading) {
    const btn = form.querySelector("button[type='submit']");
    if (btn) btn.disabled = loading;
  }

  const signupForm = document.getElementById("signup-form");
  if (signupForm) {
    signupForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      setLoading(signupForm, true);
      const data = new FormData(signupForm);
      const email = data.get("email");
      const password = data.get("password");

      try {
        const createRes = await fetch("/users", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: data.get("username"), email, password }),
        });
        if (!createRes.ok) {
          const body = await createRes.json().catch(() => ({}));
          showError(signupForm, body.detail || "could not create account.");
          setLoading(signupForm, false);
          return;
        }

        const loginRes = await fetch("/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });
        if (!loginRes.ok) {
          window.location.href = "/login";
          return;
        }
        window.location.href = "/";
      } catch (err) {
        showError(signupForm, "something went wrong. try again.");
        setLoading(signupForm, false);
      }
    });
  }

  const loginForm = document.getElementById("login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      setLoading(loginForm, true);
      const data = new FormData(loginForm);

      try {
        const res = await fetch("/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: data.get("email"), password: data.get("password") }),
        });
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          showError(loginForm, body.detail || "invalid email or password.");
          setLoading(loginForm, false);
          return;
        }
        window.location.href = "/";
      } catch (err) {
        showError(loginForm, "something went wrong. try again.");
        setLoading(loginForm, false);
      }
    });
  }

  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      logoutBtn.disabled = true;
      try {
        await fetch("/logout", { method: "POST" });
      } finally {
        window.location.href = "/signup";
      }
    });
  }
})();

document.addEventListener("click", (event) => {
  const copyBtn = event.target.closest("[data-copy]");
  if (copyBtn) {
    const text = copyBtn.getAttribute("data-copy");
    navigator.clipboard.writeText(text).then(() => {
      const original = copyBtn.textContent;
      copyBtn.textContent = "Copied";
      copyBtn.classList.add("copied");
      setTimeout(() => {
        copyBtn.textContent = original;
        copyBtn.classList.remove("copied");
      }, 1500);
    });
    return;
  }

  const editBtn = event.target.closest("[data-edit-toggle]");
  if (editBtn) {
    const row = editBtn.closest(".url-row");
    row.classList.add("editing");
    row.querySelector(".edit-form").classList.add("active");
    row.querySelector(".edit-form input[type='url']").focus();
    return;
  }

  const cancelBtn = event.target.closest("[data-edit-cancel]");
  if (cancelBtn) {
    const row = cancelBtn.closest(".url-row");
    row.classList.remove("editing");
    row.querySelector(".edit-form").classList.remove("active");
    return;
  }

  const deleteBtn = event.target.closest("[data-delete-toggle]");
  if (deleteBtn) {
    if (deleteBtn.dataset.confirming !== "true") {
      event.preventDefault();
      deleteBtn.dataset.confirming = "true";
      deleteBtn.dataset.originalText = deleteBtn.textContent;
      deleteBtn.textContent = "confirm?";
      deleteBtn.classList.add("danger");
      resetOtherDeleteButtons(deleteBtn);
    }
    // Second click: confirming is already "true", let the form submit normally.
    return;
  }

  // Any click outside an armed delete button resets it.
  resetOtherDeleteButtons(null);
});

function resetOtherDeleteButtons(exceptBtn) {
  document.querySelectorAll('[data-delete-toggle][data-confirming="true"]').forEach((btn) => {
    if (btn !== exceptBtn) {
      btn.textContent = btn.dataset.originalText || "delete";
      btn.dataset.confirming = "false";
      btn.classList.remove("danger");
    }
  });
}
