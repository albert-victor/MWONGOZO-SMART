(function () {
  "use strict";

  var chartRec = null;
  var chartPath = null;
  var overviewCache = null;

  function $(id) {
    return document.getElementById(id);
  }

  function api(path, options) {
    options = options || {};
    return fetch(path, {
      method: options.method || "GET",
      headers: Object.assign({ "Content-Type": "application/json" }, options.headers || {}),
      credentials: "same-origin",
      body: options.body ? JSON.stringify(options.body) : undefined,
    }).then(function (res) {
      return res.json().then(function (data) {
        if (!res.ok) {
          var err = new Error((data && data.detail) || res.statusText);
          err.status = res.status;
          throw err;
        }
        return data;
      });
    });
  }

  function toast(msg) {
    var el = $("adminToast");
    if (!el) return;
    el.textContent = msg;
    el.classList.remove("hidden");
    clearTimeout(toast._t);
    toast._t = setTimeout(function () {
      el.classList.add("hidden");
    }, 3200);
  }

  function animateCount(el, target, suffix) {
    if (!el) return;
    suffix = suffix || "";
    target = Math.max(0, Math.floor(Number(target) || 0));
    var start = performance.now();
    function frame(t) {
      var u = Math.min(1, (t - start) / 900);
      var eased = 1 - (1 - u) * (1 - u);
      el.textContent = String(Math.round(target * eased)) + suffix;
      if (u < 1) requestAnimationFrame(frame);
      else el.textContent = String(target) + suffix;
    }
    requestAnimationFrame(frame);
  }

  function requireAdmin() {
    return api("/auth/me").then(function (data) {
      if (!data.authenticated || !data.user || data.user.role !== "admin") {
        window.location.href = "/auth/admin/login?next=" + encodeURIComponent("/admin");
        return null;
      }
      var user = data.user;
      var avatar = $("adminAvatar");
      var email = $("adminEmail");
      if (avatar) {
        var letter = (user.full_name || user.email || "A").trim().charAt(0).toUpperCase();
        avatar.textContent = letter;
      }
      if (email) email.textContent = user.email;
      return user;
    });
  }

  function renderKpis(data) {
    var cat = data.catalogue || {};
    var users = data.users || {};
    var act = data.activity || {};
    var awards = cat.award_levels || {};

    animateCount(document.querySelector('[data-kpi="institutions"]'), cat.institutions || 0, "");
    animateCount(document.querySelector('[data-kpi="programmes"]'), cat.programmes || 0, "");
    animateCount(document.querySelector('[data-kpi="users"]'), users.total_display || users.total_real || 0, "");
    animateCount(
      document.querySelector('[data-kpi="today"]'),
      act.recommendations_today_display || 0,
      ""
    );

    var subInst = document.querySelector('[data-kpi-sub="institutions"]');
    if (subInst) subInst.textContent = (cat.institutions_in_programmes || 0) + " katika katalogi";

    var subProg = document.querySelector('[data-kpi-sub="programmes"]');
    if (subProg) {
      subProg.textContent =
        (awards.certificate || 0) +
        " cheti · " +
        (awards.diploma || 0) +
        " diploma · " +
        (awards.bachelor || 0) +
        " shahada";
    }

    var subUsers = document.querySelector('[data-kpi-sub="users"]');
    if (subUsers) {
      subUsers.textContent =
        (users.total_real || 0) +
        " halisi · +" +
        (users.new_this_week_display || 0) +
        " wiki hii (demo)";
    }

    var subSess = document.querySelector('[data-kpi-sub="sessions"]');
    if (subSess) {
      subSess.textContent = (act.recommend_sessions_display || 0) + " vipindi (blend)";
    }

    var mode = $("adminDataMode");
    if (mode) mode.textContent = "Live + synthetic · " + (data.generated_at || "");
  }

  function chartColors() {
    var light = document.body.getAttribute("data-theme") === "light";
    return {
      text: light ? "#475569" : "#94a8c4",
      grid: light ? "rgba(15,23,42,0.08)" : "rgba(148,163,184,0.15)",
      line: "#2dd4bf",
      fill: "rgba(45,212,191,0.18)",
      donut: ["#2dd4bf", "#38bdf8", "#f59e0b"],
    };
  }

  function renderCharts(data) {
    if (typeof Chart === "undefined") return;
    var c = chartColors();
    var series = (data.trends && data.trends.daily_recommendations) || [];
    var labels = series.map(function (d) {
      return d.date.slice(5);
    });
    var values = series.map(function (d) {
      return d.value;
    });

    var ctxRec = $("chartRecommendations");
    if (ctxRec) {
      if (chartRec) chartRec.destroy();
      chartRec = new Chart(ctxRec, {
        type: "line",
        data: {
          labels: labels,
          datasets: [
            {
              label: "Mapendekezo",
              data: values,
              borderColor: c.line,
              backgroundColor: c.fill,
              fill: true,
              tension: 0.35,
              pointRadius: 2,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { ticks: { color: c.text }, grid: { color: c.grid } },
            y: { ticks: { color: c.text }, grid: { color: c.grid } },
          },
        },
      });
    }

    var split = (data.trends && data.trends.pathway_split) || {};
    var pathLabels = ["A-Level", "O-Level", "Equivalent"];
    var pathValues = [split.a_level || 0, split.o_level || 0, split.equivalent || 0];
    var ctxPath = $("chartPathways");
    if (ctxPath) {
      if (chartPath) chartPath.destroy();
      chartPath = new Chart(ctxPath, {
        type: "doughnut",
        data: {
          labels: pathLabels,
          datasets: [{ data: pathValues, backgroundColor: c.donut, borderWidth: 0 }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
        },
      });
    }

    var legend = $("pathwayLegend");
    if (legend) {
      legend.innerHTML = pathLabels
        .map(function (lbl, i) {
          return "<li><span>" + lbl + "</span><strong>" + pathValues[i] + "%</strong></li>";
        })
        .join("");
    }
  }

  function renderFreqProgrammes(items) {
    var tbody = $("freqProgrammesTable") && $("freqProgrammesTable").querySelector("tbody");
    if (!tbody) return;
    tbody.innerHTML = (items || [])
      .map(function (row) {
        return (
          "<tr>" +
          "<td><strong>" +
          escapeHtml(row.name) +
          "</strong><br><span class='muted small'>" +
          escapeHtml(row.code) +
          "</span></td>" +
          "<td>" +
          escapeHtml(row.institution_name) +
          "</td>" +
          "<td>" +
          escapeHtml(row.award_level) +
          "</td>" +
          "<td>" +
          row.recommendations +
          "</td>" +
          "</tr>"
        );
      })
      .join("");
  }

  function renderActivity(events) {
    var feed = $("adminActivityFeed");
    if (!feed) return;
    var icons = {
      recommend: "fa-wand-magic-sparkles",
      save: "fa-bookmark",
      lookup: "fa-magnifying-glass",
      register: "fa-user-plus",
      login: "fa-right-to-bracket",
    };
    feed.innerHTML = (events || [])
      .map(function (ev) {
        var icon = icons[ev.type] || "fa-circle";
        return (
          "<li>" +
          "<span class='admin-feed__icon'><i class='fa-solid " +
          icon +
          "'></i></span>" +
          "<div><p class='admin-feed__msg'>" +
          escapeHtml(ev.message) +
          "</p>" +
          "<p class='admin-feed__time'>dakika " +
          ev.minutes_ago +
          " zilizopita</p></div></li>"
        );
      })
      .join("");
  }

  function renderSideLists(data) {
    var awards = (data.catalogue && data.catalogue.award_levels) || {};
    var awardEl = $("awardLevelsList");
    if (awardEl) {
      awardEl.innerHTML = Object.keys(awards)
        .map(function (k) {
          return "<li><span>" + escapeHtml(k) + "</span><span>" + awards[k] + "</span></li>";
        })
        .join("");
    }
    var cats = (data.catalogue && data.catalogue.categories_top) || [];
    var catEl = $("categoriesList");
    if (catEl) {
      catEl.innerHTML = cats
        .map(function (c) {
          return (
            "<li><span>" +
            escapeHtml(c.category) +
            "</span><span>" +
            c.programmes +
            "</span></li>"
          );
        })
        .join("");
    }
    var regions = (data.trends && data.trends.regions_top) || [];
    var regEl = $("regionsList");
    if (regEl) {
      regEl.innerHTML = regions
        .map(function (r) {
          return "<li><span>" + escapeHtml(r.region) + "</span><span>" + r.share + "%</span></li>";
        })
        .join("");
    }
  }

  function loadOverview() {
    return api("/admin/api/overview").then(function (data) {
      overviewCache = data;
      renderKpis(data);
      renderCharts(data);
      renderFreqProgrammes(data.frequent_programmes);
      renderActivity(data.recent_events);
      renderSideLists(data);
    });
  }

  function escapeHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function formatDate(iso) {
    if (!iso) return "—";
    var d = new Date(iso);
    if (isNaN(d.getTime())) return String(iso).slice(0, 10);
    return d.toLocaleDateString("sw-TZ");
  }

  function renderUsers(items) {
    var tbody = $("adminUsersTable") && $("adminUsersTable").querySelector("tbody");
    if (!tbody) return;
    tbody.innerHTML = (items || [])
      .map(function (u) {
        var active = u.is_active !== false;
        return (
          "<tr data-user-id='" +
          u.id +
          "'>" +
          "<td>" +
          escapeHtml(u.email) +
          "</td>" +
          "<td>" +
          escapeHtml(u.full_name || "—") +
          "</td>" +
          "<td><span class='admin-pill admin-pill--role'>" +
          escapeHtml(u.role) +
          "</span></td>" +
          "<td><span class='admin-pill " +
          (active ? "admin-pill--ok" : "admin-pill--off") +
          "'>" +
          (active ? "Hai" : "Imezimwa") +
          "</span></td>" +
          "<td class='muted small'>" +
          formatDate(u.created_at) +
          "</td>" +
          "<td><div class='admin-table__actions'>" +
          "<button type='button' class='btn btn-ghost btn-sm' data-edit-user='" +
          u.id +
          "'><i class='fa-solid fa-pen'></i></button>" +
          (active
            ? "<button type='button' class='btn btn-ghost btn-sm' data-deactivate-user='" +
              u.id +
              "' title='Zima'><i class='fa-solid fa-user-slash'></i></button>"
            : "") +
          "</div></td>" +
          "</tr>"
        );
      })
      .join("");
  }

  function loadUsers() {
    return api("/admin/api/users").then(function (data) {
      renderUsers(data.items || []);
    });
  }

  function openUserModal(mode, user) {
    var modal = $("adminUserModal");
    var title = $("adminUserModalTitle");
    var err = $("adminUserFormError");
    if (err) {
      err.classList.add("hidden");
      err.textContent = "";
    }
    $("adminUserId").value = mode === "edit" ? String(user.id) : "";
    $("adminUserEmail").value = mode === "edit" ? user.email : "";
    $("adminUserName").value = mode === "edit" ? user.full_name || "" : "";
    $("adminUserRole").value = mode === "edit" ? user.role : "student";
    $("adminUserActive").value = user && user.is_active === false ? "0" : "1";
    $("adminUserPassword").value = "";
    $("adminUserPassword").required = mode === "create";
    $("adminUserActiveWrap").style.display = mode === "edit" ? "" : "none";
    if (title) title.textContent = mode === "edit" ? "Hariri mtumiaji" : "Ongeza mtumiaji";
    if (modal && typeof modal.showModal === "function") modal.showModal();
  }

  function closeUserModal() {
    var modal = $("adminUserModal");
    if (modal && typeof modal.close === "function") modal.close();
  }

  function saveUser(ev) {
    ev.preventDefault();
    var err = $("adminUserFormError");
    var id = $("adminUserId").value;
    var payload = {
      email: $("adminUserEmail").value.trim(),
      full_name: $("adminUserName").value.trim(),
      role: $("adminUserRole").value,
    };
    var pw = $("adminUserPassword").value;
    if (pw) payload.password = pw;
    if (id) payload.is_active = $("adminUserActive").value === "1";

    var req = id
      ? api("/admin/api/users/" + id, { method: "PATCH", body: payload })
      : api("/admin/api/users", { method: "POST", body: payload });

    req
      .then(function () {
        closeUserModal();
        toast(id ? "Mtumiaji amesasishwa." : "Mtumiaji ameongezwa.");
        loadUsers();
      })
      .catch(function (e) {
        if (err) {
          err.textContent = e.message || "Hitilafu.";
          err.classList.remove("hidden");
        }
      });
  }

  function deactivateUser(id) {
    if (!window.confirm("Una uhakika unataka kuzima akaunti hii?")) return;
    api("/admin/api/users/" + id, { method: "DELETE" })
      .then(function () {
        toast("Akaunti imezimwa.");
        loadUsers();
      })
      .catch(function (e) {
        toast(e.message || "Imeshindwa.");
      });
  }

  function bindEvents(users) {
    var refresh = $("adminRefresh");
    if (refresh) {
      refresh.addEventListener("click", function () {
        loadOverview().catch(function () {
          toast("Imeshindwa kupakia takwimu.");
        });
        loadUsers();
      });
    }

    var logout = $("adminLogout");
    if (logout) {
      logout.addEventListener("click", function () {
        api("/auth/logout", { method: "POST" }).finally(function () {
          window.location.href = "/auth/admin/login";
        });
      });
    }

    var theme = $("adminThemeToggle");
    if (theme) {
      theme.addEventListener("click", function () {
        var next = document.body.getAttribute("data-theme") === "light" ? "dark" : "light";
        document.body.setAttribute("data-theme", next);
        document.documentElement.setAttribute("data-theme", next);
        if (overviewCache) renderCharts(overviewCache);
      });
    }

    var createBtn = $("adminUserCreateBtn");
    if (createBtn) {
      createBtn.addEventListener("click", function () {
        openUserModal("create", { is_active: true });
      });
    }

    var form = $("adminUserForm");
    if (form) form.addEventListener("submit", saveUser);

    ["adminUserModalClose", "adminUserCancel"].forEach(function (id) {
      var btn = $(id);
      if (btn) btn.addEventListener("click", closeUserModal);
    });

    var usersTable = $("adminUsersTable");
    if (usersTable) {
      usersTable.addEventListener("click", function (ev) {
        var editId = ev.target.closest("[data-edit-user]");
        var delId = ev.target.closest("[data-deactivate-user]");
        if (editId) {
          var uid = editId.getAttribute("data-edit-user");
          api("/admin/api/users")
            .then(function (data) {
              var user = (data.items || []).find(function (u) {
                return String(u.id) === String(uid);
              });
              if (user) openUserModal("edit", user);
            })
            .catch(function () {
              toast("Imeshindwa kupakia mtumiaji.");
            });
        }
        if (delId) deactivateUser(delId.getAttribute("data-deactivate-user"));
      });
    }
  }

  function init() {
    requireAdmin()
      .then(function (user) {
        if (!user) return;
        bindEvents();
        return Promise.all([loadOverview(), loadUsers()]);
      })
      .catch(function () {
        window.location.href = "/auth/admin/login?next=" + encodeURIComponent("/admin");
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
