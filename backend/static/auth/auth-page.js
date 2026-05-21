(function () {
  "use strict";

  var body = document.body;
  var portal = body.getAttribute("data-auth-portal") || "student";
  var isAdmin = portal === "admin";
  var form = document.getElementById("authForm");
  if (!form) return;

  var tabs = document.querySelectorAll(".auth-tab");
  var titleEl = document.getElementById("authTitle");
  var subEl = document.getElementById("authSub");
  var nameField = document.getElementById("nameField");
  var errorEl = document.getElementById("authError");
  var submitBtn = document.getElementById("authSubmit");
  var loginUrl = body.getAttribute("data-login-url") || "/auth/login";
  var registerUrl = body.getAttribute("data-register-url") || "/auth/register";
  var successUrl = body.getAttribute("data-success-url") || "/";
  var mode = "login";
  var uiLang = "sw";

  var copy = {
    sw: {
      pageTitleStudent: "Mwongozo Smart — Ingia / Jisajili",
      pageTitleAdmin: "Mwongozo Smart — Admin",
      back: "Rudi",
      loginTitle: "Karibu tena",
      loginSub: "Ingia kwenye Mwongozo Smart — hifadhi matokeo na programme ulizopenda.",
      registerTitle: "Karibu",
      registerSub: "Fungua akaunti yako ya Mwongozo Smart.",
      tabLogin: "Ingia",
      tabRegister: "Jisajili",
      submitLogin: "Ingia",
      submitRegister: "Jisajili",
      adminTitle: "Usimamizi",
      adminSub: "Ingia kwa akaunti ya usimamizi — Mwongozo Smart.",
      labelName: "Jina kamili",
      phName: "Jina lako kamili",
      labelEmail: "Barua pepe",
      phEmail: "wewe@barua.com",
      labelPassword: "Nenosiri",
      phPassword: "Angalau herufi 8",
      linkAdmin: "Ingia kama admin",
      linkStudent: "Mwanafunzi",
      socialAria: "Mitandao ya kijamii",
      langAria: "Lugha",
      errEmail: "Weka barua pepe sahihi.",
      errPasswordLen: "Nenosiri lazima liwe angalau herufi 8.",
      errPasswordMix: "Nenosiri lazima liwe na herufi na nambari.",
      errNetwork: "Hitilafu ya mtandao.",
      errRequest: "Ombi limeshindwa.",
    },
    en: {
      pageTitleStudent: "Mwongozo Smart — Sign in / Register",
      pageTitleAdmin: "Mwongozo Smart — Admin",
      back: "Back",
      loginTitle: "Welcome back",
      loginSub: "Sign in to Mwongozo Smart — save results and programmes you like.",
      registerTitle: "Welcome",
      registerSub: "Create your Mwongozo Smart account.",
      tabLogin: "Sign in",
      tabRegister: "Register",
      submitLogin: "Sign in",
      submitRegister: "Register",
      adminTitle: "Administration",
      adminSub: "Sign in with your admin account — Mwongozo Smart.",
      labelName: "Full name",
      phName: "Your full name",
      labelEmail: "Email",
      phEmail: "you@email.com",
      labelPassword: "Password",
      phPassword: "At least 8 characters",
      linkAdmin: "Sign in as admin",
      linkStudent: "Student",
      socialAria: "Social links",
      langAria: "Language",
      errEmail: "Enter a valid email address.",
      errPasswordLen: "Password must be at least 8 characters.",
      errPasswordMix: "Password must include letters and numbers.",
      errNetwork: "Network error.",
      errRequest: "Request failed.",
    },
  };

  function getUiLang() {
    var stored = localStorage.getItem("mwongozo-ui-lang");
    if (stored === "en" || stored === "sw") return stored;
    return "sw";
  }

  function L(key) {
    var pack = copy[uiLang] || copy.sw;
    return pack[key] != null ? pack[key] : key;
  }

  function applyAuthDarkTheme() {
    document.documentElement.setAttribute("data-theme", "dark");
    body.setAttribute("data-theme", "dark");
    body.classList.add("auth-page--dark");
  }

  function applyAuthLang() {
    document.documentElement.lang = uiLang === "en" ? "en" : "sw";
    body.setAttribute("data-ui-lang", uiLang);

    document.querySelectorAll("[data-auth-i18n-aria]").forEach(function (el) {
      var key = el.getAttribute("data-auth-i18n-aria");
      if (key) el.setAttribute("aria-label", L(key));
    });

    document.querySelectorAll("[data-auth-i18n]").forEach(function (el) {
      var key = el.getAttribute("data-auth-i18n");
      if (!key) return;
      if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") return;
      if (el.querySelector("[data-auth-i18n]")) return;
      el.textContent = L(key);
    });

    document.querySelectorAll("[data-auth-i18n-placeholder]").forEach(function (el) {
      var key = el.getAttribute("data-auth-i18n-placeholder");
      if (key && L(key)) el.setAttribute("placeholder", L(key));
    });

    document.title = L(isAdmin ? "pageTitleAdmin" : "pageTitleStudent");

    document.querySelectorAll("[data-set-lang]").forEach(function (btn) {
      btn.classList.toggle("is-active", btn.getAttribute("data-set-lang") === uiLang);
    });

    if (!isAdmin) setMode(mode);
    else applyAdminCopy();
  }

  function setUiLang(lang) {
    uiLang = lang === "en" ? "en" : "sw";
    localStorage.setItem("mwongozo-ui-lang", uiLang);
    applyAuthLang();
  }

  function setMode(next) {
    if (isAdmin) return;
    mode = next;
    tabs.forEach(function (tab) {
      var tabMode = tab.getAttribute("data-mode") || "login";
      var active = tabMode === mode;
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-selected", active ? "true" : "false");
      tab.textContent = L(tabMode === "register" ? "tabRegister" : "tabLogin");
    });
    if (mode === "login") {
      if (titleEl) titleEl.textContent = L("loginTitle");
      if (subEl) subEl.textContent = L("loginSub");
      if (nameField) nameField.classList.add("hidden");
      if (submitBtn) {
        var span = submitBtn.querySelector("span");
        if (span) span.textContent = L("submitLogin");
        else submitBtn.textContent = L("submitLogin");
      }
      if (form.password) form.password.setAttribute("autocomplete", "current-password");
    } else {
      if (titleEl) titleEl.textContent = L("registerTitle");
      if (subEl) subEl.textContent = L("registerSub");
      if (nameField) nameField.classList.remove("hidden");
      if (submitBtn) {
        var spanR = submitBtn.querySelector("span");
        if (spanR) spanR.textContent = L("submitRegister");
        else submitBtn.textContent = L("submitRegister");
      }
      if (form.password) form.password.setAttribute("autocomplete", "new-password");
    }
    clearError();
  }

  function applyAdminCopy() {
    if (!isAdmin) return;
    if (titleEl) titleEl.textContent = L("adminTitle");
    if (subEl) subEl.textContent = L("adminSub");
    if (submitBtn) {
      var span = submitBtn.querySelector("span");
      if (span) span.textContent = L("submitLogin");
      else submitBtn.textContent = L("submitLogin");
    }
  }

  function clearError() {
    if (!errorEl) return;
    errorEl.classList.add("hidden");
    errorEl.textContent = "";
  }

  function showError(msg) {
    if (!errorEl) return;
    errorEl.textContent = msg;
    errorEl.classList.remove("hidden");
  }

  function validateClient() {
    var email = form.email.value.trim();
    var password = form.password.value;
    if (!email || email.indexOf("@") < 1) {
      return L("errEmail");
    }
    if (password.length < 8) {
      return L("errPasswordLen");
    }
    if (mode === "register" && !(/[A-Za-z]/.test(password) && /\d/.test(password))) {
      return L("errPasswordMix");
    }
    return "";
  }

  applyAuthDarkTheme();
  uiLang = getUiLang();
  applyAuthLang();

  document.querySelectorAll("[data-set-lang]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      setUiLang(btn.getAttribute("data-set-lang"));
    });
  });

  window.addEventListener("storage", function (e) {
    if (e.key === "mwongozo-ui-lang" && (e.newValue === "en" || e.newValue === "sw")) {
      uiLang = e.newValue;
      applyAuthLang();
    }
  });

  if (!isAdmin && tabs.length) {
    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        setMode(tab.getAttribute("data-mode") || "login");
      });
    });
    setMode("login");
  }

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    var clientErr = validateClient();
    if (clientErr) {
      showError(clientErr);
      return;
    }
    clearError();
    submitBtn.disabled = true;
    var url = !isAdmin && mode === "register" ? registerUrl : loginUrl;
    var payload =
      !isAdmin && mode === "register"
        ? {
            email: form.email.value.trim(),
            password: form.password.value,
            full_name: (form.full_name && form.full_name.value.trim()) || "",
          }
        : {
            email: form.email.value.trim(),
            password: form.password.value,
          };
    try {
      var response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      var data = await response.json().catch(function () {
        return {};
      });
      if (!response.ok) {
        var detail = data.detail;
        throw new Error(typeof detail === "string" ? detail : detail || L("errRequest"));
      }
      window.location.href = successUrl;
    } catch (err) {
      showError(err.message || L("errNetwork"));
    } finally {
      submitBtn.disabled = false;
    }
  });

  requestAnimationFrame(function () {
    requestAnimationFrame(function () {
      document.body.classList.add("auth-page--ready");
    });
  });
})();
