(function () {
  "use strict";

  /** Single letter: Albert → A, email albert@x.com → A */
  function initialFromUser(user) {
    if (!user) return "?";
    var name = (user.full_name || "").trim();
    if (name) return name.charAt(0).toUpperCase();
    var email = (user.email || "").trim();
    if (email) return email.charAt(0).toUpperCase();
    return "?";
  }

  function bindMenu(menu, user) {
    var trigger = menu.querySelector(".auth-user-menu__trigger");
    var dropdown = menu.querySelector(".auth-user-menu__dropdown");
    var avatar = menu.querySelector("[data-auth-initials]");
    var logoutBtn = menu.querySelector("[data-auth-logout]");
    var letter = initialFromUser(user);
    var isAdmin = user.role === "admin";

    if (avatar) {
      avatar.textContent = letter;
      avatar.classList.toggle("auth-user-menu__avatar--admin", isAdmin);
    }
    if (trigger) {
      trigger.setAttribute("aria-label", "Akaunti: " + letter);
      trigger.title = "Akaunti";
    }

    if (!trigger || !dropdown) return;

    function closeMenu() {
      menu.classList.remove("is-open");
      trigger.setAttribute("aria-expanded", "false");
      dropdown.hidden = true;
    }

    function toggleMenu() {
      var open = menu.classList.toggle("is-open");
      trigger.setAttribute("aria-expanded", open ? "true" : "false");
      dropdown.hidden = !open;
    }

    if (!trigger.dataset.bound) {
      trigger.dataset.bound = "1";
      trigger.addEventListener("click", function (e) {
        e.stopPropagation();
        toggleMenu();
      });
    }

    if (!menu.dataset.outsideBound) {
      menu.dataset.outsideBound = "1";
      document.addEventListener("click", function (e) {
        if (!menu.contains(e.target)) closeMenu();
      });
      document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") closeMenu();
      });
    }

    if (logoutBtn && !logoutBtn.dataset.bound) {
      logoutBtn.dataset.bound = "1";
      logoutBtn.addEventListener("click", async function () {
        logoutBtn.disabled = true;
        try {
          await fetch("/auth/logout", {
            method: "POST",
            credentials: "include",
          });
        } catch (_e) {}
        window.location.reload();
      });
    }
  }

  function setAuthUi(user) {
    var guests = document.querySelectorAll(".auth-guest-actions");
    var menus = document.querySelectorAll(".auth-user-menu");
    var loggedIn = !!(user && user.id);

    guests.forEach(function (el) {
      el.hidden = loggedIn;
    });
    menus.forEach(function (menu) {
      menu.hidden = !loggedIn;
      if (loggedIn) bindMenu(menu, user);
    });

    window.__MWONGOZO_USER__ = loggedIn ? user : null;
    document.querySelectorAll(".auth-only-nav").forEach(function (el) {
      el.classList.toggle("hidden", !loggedIn);
      el.hidden = !loggedIn;
    });
    document.dispatchEvent(
      new CustomEvent("mwongozo:auth", { detail: { user: loggedIn ? user : null } })
    );
  }

  async function refreshAuthSession() {
    try {
      var response = await fetch("/auth/me", { credentials: "include" });
      var data = await response.json().catch(function () {
        return {};
      });
      if (data.authenticated && data.user) {
        setAuthUi(data.user);
      } else {
        setAuthUi(null);
      }
    } catch (_e) {
      setAuthUi(null);
    }
  }

  window.MwongozoAuth = {
    refresh: refreshAuthSession,
    initialFromUser: initialFromUser,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", refreshAuthSession);
  } else {
    refreshAuthSession();
  }
})();
