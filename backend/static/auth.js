(function () {
  "use strict";

  var form = document.getElementById("authForm");
  var tabs = document.querySelectorAll(".auth-tab");
  var titleEl = document.getElementById("authTitle");
  var subEl = document.getElementById("authSub");
  var nameField = document.getElementById("nameField");
  var errorEl = document.getElementById("authError");
  var submitBtn = document.getElementById("authSubmit");
  var mode = "login";

  function setMode(next) {
    mode = next;
    tabs.forEach(function (tab) {
      var active = tab.getAttribute("data-mode") === mode;
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-selected", active ? "true" : "false");
    });
    if (mode === "login") {
      titleEl.textContent = "Karibu tena";
      subEl.textContent = "Welcome back — ingia ili kuendelea na profile yako.";
      nameField.classList.add("hidden");
      submitBtn.querySelector("span").textContent = "Ingia";
      submitBtn.querySelector("i").className = "fa-solid fa-right-to-bracket";
      form.password.setAttribute("autocomplete", "current-password");
    } else {
      titleEl.textContent = "Karibu";
      subEl.textContent = "Welcome — fungua akaunti ya mwanafunzi Mwongozo Smart.";
      nameField.classList.remove("hidden");
      submitBtn.querySelector("span").textContent = "Jisajili";
      submitBtn.querySelector("i").className = "fa-solid fa-user-plus";
      form.password.setAttribute("autocomplete", "new-password");
    }
    errorEl.classList.add("hidden");
    errorEl.textContent = "";
  }

  tabs.forEach(function (tab) {
    tab.addEventListener("click", function () {
      setMode(tab.getAttribute("data-mode") || "login");
    });
  });

  function validateClient() {
    var email = form.email.value.trim();
    var password = form.password.value;
    if (!email || email.indexOf("@") < 1) {
      return "Weka barua pepe sahihi.";
    }
    if (password.length < 8) {
      return "Nenosiri lazima liwe angalau herufi 8.";
    }
    if (mode === "register" && !/[A-Za-z]/.test(password) && !/\d/.test(password)) {
      return "Nenosiri lazima liwe na herufi na nambari.";
    }
    return "";
  }

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    var clientErr = validateClient();
    if (clientErr) {
      errorEl.textContent = clientErr;
      errorEl.classList.remove("hidden");
      return;
    }
    errorEl.classList.add("hidden");
    submitBtn.disabled = true;
    var url = mode === "register" ? "/auth/register" : "/auth/login";
    var body =
      mode === "register"
        ? {
            email: form.email.value.trim(),
            password: form.password.value,
            full_name: form.full_name.value.trim(),
          }
        : {
            email: form.email.value.trim(),
            password: form.password.value,
          };
    try {
      var response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(body),
      });
      var data = await response.json().catch(function () {
        return {};
      });
      if (!response.ok) {
        throw new Error(data.detail || "Ombi limeshindwa.");
      }
      window.location.href = "/";
    } catch (err) {
      errorEl.textContent = err.message || "Hitilafu ya mtandao.";
      errorEl.classList.remove("hidden");
    } finally {
      submitBtn.disabled = false;
    }
  });

  setMode("login");
})();
