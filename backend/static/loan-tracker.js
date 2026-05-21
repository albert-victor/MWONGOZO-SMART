/**
 * HESLB loan guidance + demo tracker â€” GET /loan/guidance, POST /loan/track.
 */
(function (global) {
  "use strict";

  var STORAGE_KEY = "mwongozo-loan-profile";
  var CHECKLIST_KEY = "mwongozo-loan-checklist";
  var EXAM_CTX_KEY = "mwongozo-exam-context";
  var DEMO_REF = "HSL-2026-00127";
  var DEMO_FORM_PRESETS = {
    "HSL-2026-00127": {
      heslb_reference: "HSL-2026-00127",
      exam_number: "S0123/0027/2024",
      exam_level: "a_level",
      selected_programme: "Bachelor of Science in Computer Science",
      selected_university: "University of Dar es Salaam",
      nin: "19950101123456789012",
      special_categories: { low_income: true },
    },
    "HSL-2026-00482": {
      heslb_reference: "HSL-2026-00482",
      exam_number: "P0412/0182/2024",
      exam_level: "a_level",
      selected_programme: "Bachelor of Education",
      selected_university: "University of Dodoma",
      nin: "19960215123456789012",
      special_categories: {
        orphan: true,
        low_income: true,
        single_parent_household: true,
      },
    },
    "HSL-2026-00991": {
      heslb_reference: "HSL-2026-00991",
      exam_number: "S0788/0091/2023",
      exam_level: "a_level",
      selected_programme: "Bachelor of Commerce (Accountancy)",
      selected_university: "Mzumbe University",
      nin: "19930815123456789012",
      special_categories: { low_income: true },
    },
  };
  var loanCatalogLoaded = false;
  var guidanceLoadedLevel = "";
  var activeLoanTab = "guidance";

  function lang() {
    return document.body.getAttribute("data-ui-lang") === "en" ? "en" : "sw";
  }

  function t(sw, en) {
    return lang() === "en" ? en : sw;
  }

  function $(id) {
    return document.getElementById(id);
  }

  function readProfile() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (_e) {
      return null;
    }
  }

  function saveProfile(payload) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
    } catch (_e) {}
  }

  function readExamContext() {
    try {
      var raw = sessionStorage.getItem(EXAM_CTX_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (_e) {
      return null;
    }
  }

  function readChecklistState() {
    try {
      var raw = localStorage.getItem(CHECKLIST_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch (_e) {
      return {};
    }
  }

  function saveChecklistItem(id, checked) {
    var state = readChecklistState();
    state[id] = !!checked;
    try {
      localStorage.setItem(CHECKLIST_KEY, JSON.stringify(state));
    } catch (_e) {}
  }

  function examLevelFromContext(ctx) {
    if (!ctx) return null;
    if (ctx.exam_level === "o_level" || ctx.exam_level === "a_level") return ctx.exam_level;
    var src = String(ctx.source || "").toLowerCase();
    if (src.indexOf("csee") !== -1) return "o_level";
    if (src.indexOf("acsee") !== -1) return "a_level";
    return null;
  }

  function syncExamLevelSelects(level) {
    if ($("loanGuidanceLevel")) $("loanGuidanceLevel").value = level;
    if ($("loanExamLevel")) $("loanExamLevel").value = level;
  }

  function setLoanTab(tab) {
    activeLoanTab = tab === "tracker" ? "tracker" : "guidance";
    document.querySelectorAll("[data-loan-tab]").forEach(function (btn) {
      var on = btn.getAttribute("data-loan-tab") === activeLoanTab;
      btn.classList.toggle("is-active", on);
      btn.setAttribute("aria-selected", on ? "true" : "false");
    });
    document.querySelectorAll("[data-loan-pane]").forEach(function (pane) {
      pane.classList.toggle("hidden", pane.getAttribute("data-loan-pane") !== activeLoanTab);
    });
    if (activeLoanTab === "guidance") loadGuidance(getGuidanceLevel());
  }

  function getGuidanceLevel() {
    var sel = $("loanGuidanceLevel");
    return sel && sel.value === "a_level" ? "a_level" : "o_level";
  }

  function prefillFromExamContext() {
    var ctx = readExamContext();
    if (!ctx) return;
    var level = examLevelFromContext(ctx);
    if (level) syncExamLevelSelects(level);
    var saved = readProfile() || {};
    if (ctx.exam_number && !saved.exam_number) saved.exam_number = ctx.exam_number;
    if (level && !saved.exam_level) saved.exam_level = level;
    fillForm(saved);
    var hint = $("loanGuidancePrefillHint");
    if (hint && ctx.exam_number) {
      hint.hidden = false;
      hint.textContent = t(
        "Nambari ya mtihani imejazwa kutoka matokeo yako: " + ctx.exam_number,
        "Exam number prefilled from your results: " + ctx.exam_number
      );
    }
  }

  function escapeHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  /** Strip "(demo)" from API copy — not shown in UI. */
  function cleanLabel(s) {
    return String(s || "")
      .replace(/\s*\(demo\)/gi, "")
      .replace(/\s*,\s*demo\b/gi, "")
      .trim();
  }

  function displayText(s) {
    return escapeHtml(cleanLabel(s));
  }

  function riskLabel(flag) {
    var map = {
      nin_verification_pending: t("NIN haijathibitishwa", "NIN not verified"),
      nin_pending: t("NIN inasubiri", "NIN pending"),
      private_institution: t("Chuo binafsi — angalia miongozo ya HESLB", "Private institution — check HESLB guidance"),
      low_funding_priority_course: t("Programu na kipaumbele cha chini cha ufadhili", "Low funding priority programme"),
      late_submission_risk: t("Hatari ya ucheleweshaji wa maombi", "Late submission risk"),
      moderate_priority_course: t("Kipaumbele wastani cha programu", "Moderate programme priority"),
    };
    return map[flag] || flag;
  }

  function stageLabel(stage) {
    var map = {
      account: t("Akaunti", "Account"),
      profile: t("Wasifu", "Profile"),
      submitted: t("Imewasilishwa", "Submitted"),
      verification: t("Uthibitisho", "Verification"),
      batch: t("Batch", "Batch"),
      appeal: t("Rufaa", "Appeal"),
    };
    return map[stage] || stage;
  }

  function timelineIconForStatus(status, iconFromApi) {
    var raw = String(iconFromApi || "").trim();
    if (raw.indexOf("fa-") === 0) return raw;
    if (status === "complete") return "fa-circle-check";
    if (status === "in_progress" || status === "pending") return "fa-hourglass-half";
    return "fa-lock";
  }

  function faIconHtml(iconClass, wrapClass) {
    var cls = String(iconClass || "fa-circle")
      .replace(/^fa-solid\s+/i, "")
      .trim();
    if (cls.indexOf("fa-") !== 0) cls = "fa-" + cls;
    return (
      '<span class="loan-fa-icon' +
      (wrapClass ? " " + wrapClass : "") +
      '"><i class="fa-solid ' +
      escapeHtml(cls) +
      '" aria-hidden="true"></i></span>'
    );
  }

  function statusItemHtml(kind, textHtml, tag) {
    tag = tag || "li";
    var icons = {
      ok: "fa-circle-check",
      pending: "fa-hourglass-half",
      warn: "fa-triangle-exclamation",
      off: "fa-circle",
      clock: "fa-clock",
      lock: "fa-lock",
    };
    return (
      "<" +
      tag +
      ' class="loan-status-item loan-status-item--' +
      escapeHtml(kind) +
      '">' +
      faIconHtml(icons[kind] || icons.off, "loan-status-item__icon") +
      '<span class="loan-status-item__body">' +
      textHtml +
      "</span></" +
      tag +
      ">"
    );
  }

  function alertIconForLevel(level) {
    if (level === "urgent") return "fa-bell";
    if (level === "ok" || level === "success") return "fa-circle-check";
    if (level === "warn" || level === "warning") return "fa-triangle-exclamation";
    return "fa-circle-info";
  }

  function collectFormPayload() {
    var form = $("loanTrackForm");
    if (!form) return {};
    var fd = new FormData(form);
    var special = {
      orphan: !!form.querySelector('[name="orphan"]:checked'),
      disability: !!form.querySelector('[name="disability"]:checked'),
      low_income: !!form.querySelector('[name="low_income"]:checked'),
      single_parent_household: !!form.querySelector('[name="single_parent_household"]:checked'),
    };
    return {
      exam_level: fd.get("exam_level") || "a_level",
      exam_number: String(fd.get("exam_number") || "").trim(),
      selected_programme: String(fd.get("selected_programme") || "").trim(),
      selected_university: String(fd.get("selected_university") || "").trim(),
      heslb_reference: String(fd.get("heslb_reference") || "").trim(),
      nin: String(fd.get("nin") || "").trim(),
      special_categories: special,
      language: lang(),
    };
  }

  function fillForm(payload) {
    var form = $("loanTrackForm");
    if (!form || !payload) return;
    if ($("loanExamLevel")) $("loanExamLevel").value = payload.exam_level || "a_level";
    if ($("loanExamNumber")) $("loanExamNumber").value = payload.exam_number || "";
    if ($("loanProgramme")) $("loanProgramme").value = payload.selected_programme || "";
    if ($("loanInstitution")) $("loanInstitution").value = payload.selected_university || "";
    if ($("loanHeslbRef")) $("loanHeslbRef").value = payload.heslb_reference || "";
    if ($("loanNin")) $("loanNin").value = payload.nin || "";
    var sc = payload.special_categories || {};
    ["orphan", "disability", "low_income", "single_parent_household"].forEach(function (key) {
      var el = form.querySelector('[name="' + key + '"]');
      if (el) el.checked = !!sc[key];
    });
  }

  function loadCatalogHints() {
    if (loanCatalogLoaded || typeof MwongozoApi === "undefined") return;
    loanCatalogLoaded = true;
    MwongozoApi.fetchJson("/programmes", { method: "GET" })
      .then(function (rows) {
        var progList = $("loanProgrammeList");
        var instSet = {};
        var instList = $("loanInstitutionList");
        if (!progList || !instList) return;
        var names = [];
        rows.forEach(function (r) {
          if (r.name && names.indexOf(r.name) === -1) names.push(r.name);
          if (r.institution_name) instSet[r.institution_name] = 1;
        });
        names.sort().slice(0, 400).forEach(function (n) {
          progList.insertAdjacentHTML("beforeend", '<option value="' + escapeHtml(n) + '">');
        });
        Object.keys(instSet)
          .sort()
          .forEach(function (n) {
            instList.insertAdjacentHTML("beforeend", '<option value="' + escapeHtml(n) + '">');
          });
      })
      .catch(function () {});
  }

  function renderOfficialLinks(links) {
    var ul = $("loanOfficialLinks");
    if (!ul || !links) return;
    ul.className = "loan-link-grid";
    ul.innerHTML = buildLinkPortfolio(links).replace(/^<ul class="loan-link-grid">|<\/ul>$/g, "");
  }

  var GUIDANCE_NAV = [
    { id: "overview", icon: "fa-compass", sw: "Muhtasari", en: "Overview" },
    { id: "pathway", icon: "fa-road", sw: "Njia", en: "Pathway" },
    { id: "learn", icon: "fa-book-open", sw: "Mafunzo", en: "Guides" },
    { id: "documents", icon: "fa-folder-open", sw: "Nyaraka", en: "Documents" },
    { id: "faq", icon: "fa-circle-question", sw: "Maswali", en: "FAQ" },
  ];

  var TRACKER_NAV = [
    { id: "summary", icon: "fa-chart-line", sw: "Muhtasari", en: "Summary" },
    { id: "progress", icon: "fa-route", sw: "Maendeleo", en: "Progress" },
    { id: "profile", icon: "fa-user-check", sw: "Wasifu", en: "Profile" },
    { id: "support", icon: "fa-life-ring", sw: "Msaada", en: "Support" },
  ];

  var activeGuidanceSection = "overview";
  var activeTrackerView = "summary";
  var trackerNavBuilt = false;

  function linkIconFor(url) {
    var u = String(url || "").toLowerCase();
    if (u.indexOf("olas") !== -1) return "fa-laptop";
    if (u.indexOf("nida") !== -1) return "fa-id-card";
    if (u.indexOf("rita") !== -1) return "fa-certificate";
    if (u.indexOf("necta") !== -1) return "fa-graduation-cap";
    if (u.indexOf("heslb") !== -1) return "fa-landmark";
    return "fa-arrow-up-right-from-square";
  }

  function linkLogoSrc(url, link) {
    if (link && link.logo) return link.logo;
    var u = String(url || "").toLowerCase();
    if (u.indexOf("olas") !== -1 || u.indexOf("heslb") !== -1) return "/static/partners/heslb.png";
    if (u.indexOf("nida") !== -1) return "/static/partners/nida.png";
    if (u.indexOf("rita") !== -1) return "/static/partners/rita.png";
    if (u.indexOf("necta") !== -1) return "/static/partners/necta.png";
    return "";
  }

  function buildSubnavHtml(items, attr, activeId) {
    return items
      .map(function (item) {
        var label = lang() === "en" ? item.en : item.sw;
        var on = item.id === activeId ? " is-active" : "";
        return (
          '<button type="button" class="loan-subnav__btn' +
          on +
          '" data-' +
          attr +
          '="' +
          escapeHtml(item.id) +
          '" role="tab" aria-selected="' +
          (on ? "true" : "false") +
          '"><i class="fa-solid ' +
          escapeHtml(item.icon) +
          '" aria-hidden="true"></i> ' +
          escapeHtml(label) +
          "</button>"
        );
      })
      .join("");
  }

  function setGuidanceSection(id) {
    activeGuidanceSection = id;
    var root = $("loanGuidanceRoot");
    if (!root) return;
    root.querySelectorAll("[data-loan-section]").forEach(function (panel) {
      panel.classList.toggle("is-active", panel.getAttribute("data-loan-section") === id);
    });
    root.querySelectorAll("[data-guidance-section]").forEach(function (btn) {
      var on = btn.getAttribute("data-guidance-section") === id;
      btn.classList.toggle("is-active", on);
      btn.setAttribute("aria-selected", on ? "true" : "false");
    });
  }

  function setTrackerView(id) {
    activeTrackerView = id;
    var dash = $("loanDashboard");
    if (!dash) return;
    dash.querySelectorAll(".loan-tracker-view").forEach(function (view) {
      view.classList.toggle("is-active", view.getAttribute("data-tracker-view") === id);
    });
    dash.querySelectorAll("[data-tracker-nav]").forEach(function (btn) {
      var on = btn.getAttribute("data-tracker-nav") === id;
      btn.classList.toggle("is-active", on);
      btn.setAttribute("aria-selected", on ? "true" : "false");
    });
  }

  function buildTrackerSubnav() {
    if (trackerNavBuilt) return;
    var nav = $("loanTrackerSubnav");
    if (!nav) return;
    trackerNavBuilt = true;
    nav.innerHTML = buildSubnavHtml(TRACKER_NAV, "tracker-nav", activeTrackerView);
    nav.querySelectorAll("[data-tracker-nav]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        setTrackerView(btn.getAttribute("data-tracker-nav"));
      });
    });
  }

  function bindGuidanceSubnav(root) {
    root.querySelectorAll("[data-guidance-section]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        setGuidanceSection(btn.getAttribute("data-guidance-section"));
      });
    });
  }

  function buildLinkPortfolio(links) {
    if (!links || !links.length) return "";
    return (
      '<ul class="loan-link-grid">' +
      links
        .map(function (l) {
          var icon = linkIconFor(l.url);
          var logoSrc = linkLogoSrc(l.url, l);
          var iconHtml = logoSrc
            ? '<span class="loan-link-card__icon loan-link-card__icon--logo"><img src="' +
              escapeHtml(logoSrc) +
              '" alt="" width="40" height="40" loading="lazy" decoding="async" /></span>'
            : '<span class="loan-link-card__icon"><i class="fa-solid ' +
              icon +
              '" aria-hidden="true"></i></span>';
          return (
            '<li><a class="loan-link-card" href="' +
            escapeHtml(l.url) +
            '" target="_blank" rel="noopener noreferrer">' +
            iconHtml +
            '<span class="loan-link-card__label">' +
            escapeHtml(l.label) +
            "</span>" +
            '<span class="loan-link-card__arrow"><i class="fa-solid fa-arrow-up-right-from-square" aria-hidden="true"></i></span>' +
            "</a></li>"
          );
        })
        .join("") +
      "</ul>"
    );
  }


  function buildStepCards(steps) {
    if (!steps || !steps.length) return "";
    return (
      '<ol class="loan-steps-grid">' +
      steps
        .map(function (step) {
          var summary = step.summary || step.detail || "";
          var detail = step.summary && step.detail && step.summary !== step.detail ? step.detail : "";
          var readMore = step.read_more
            ? '<details class="loan-step-readmore"><summary>' +
              escapeHtml(t("Soma zaidi", "Read more")) +
              '</summary><div class="loan-step-readmore__body">' +
              escapeHtml(step.read_more) +
              "</div></details>"
            : "";
          return (
            '<li class="loan-step-card"><span class="loan-step-card__num">' +
            escapeHtml(String(step.step)) +
            '</span><strong>' +
            escapeHtml(step.title) +
            '</strong><p class="loan-step-card__summary">' +
            escapeHtml(summary) +
            "</p>" +
            (detail ? '<p class="loan-step-card__detail">' + escapeHtml(detail) + "</p>" : "") +
            readMore +
            "</li>"
          );
        })
        .join("") +
      "</ol>"
    );
  }

  function buildPathwayPanel(data) {
    var html = "";
    if (data.pathway_intro) {
      html += '<p class="loan-pathway-intro">' + displayText(data.pathway_intro) + "</p>";
    }
    html += buildStepCards((data.pathway_steps || []).concat(data.olas_steps || []));
    return html;
  }

  function buildFaqPanel(faq) {
    if (!faq || !faq.length) return "";
    var groups = {};
    var order = [];
    faq.forEach(function (item) {
      var cat = item.category || t("Maswali", "Questions");
      if (!groups[cat]) {
        groups[cat] = [];
        order.push(cat);
      }
      groups[cat].push(item);
    });
    var html = '<div class="loan-faq-list">';
    order.forEach(function (cat) {
      html +=
        '<section class="loan-faq-group"><h4 class="loan-faq-group__title">' +
        escapeHtml(cat) +
        "</h4>";
      groups[cat].forEach(function (item, idx) {
        html +=
          '<details class="loan-faq-item"' +
          (idx === 0 ? " open" : "") +
          '><summary><span class="loan-faq-item__q">' +
          escapeHtml(item.question) +
          '</span></summary><div class="loan-faq-item__a"><p>' +
          escapeHtml(item.answer) +
          "</p></div></details>";
      });
      html += "</section>";
    });
    html += "</div>";
    return html;
  }

  function buildTickCard(cid, text, link, checked) {
    var inner = link
      ? '<a href="' + escapeHtml(link) + '" target="_blank" rel="noopener noreferrer">' + escapeHtml(text) + "</a>"
      : escapeHtml(text);
    return (
      '<li><label class="loan-tick-card' +
      (checked ? " is-done" : "") +
      '">' +
      '<input type="checkbox" data-checklist-id="' +
      escapeHtml(cid) +
      '"' +
      (checked ? " checked" : "") +
      " />" +
      '<span class="loan-tick-card__inner">' +
      '<span class="loan-tick-card__box"><i class="fa-solid fa-check" aria-hidden="true"></i></span>' +
      '<span class="loan-tick-card__text">' +
      inner +
      "</span></span></label></li>"
    );
  }

  function updateChecklistProgress(root) {
    var boxes = root.querySelectorAll("[data-checklist-id]");
    if (!boxes.length) return;
    var done = 0;
    boxes.forEach(function (b) {
      if (b.checked) done += 1;
    });
    var pct = Math.round((done / boxes.length) * 100);
    var ring = root.querySelector(".loan-checklist-progress__ring");
    if (ring) {
      ring.style.setProperty("--p", String(pct));
      var span = ring.querySelector("span");
      if (span) span.textContent = pct + "%";
    }
    var badge = root.querySelector("[data-checklist-count]");
    if (badge) badge.textContent = done + "/" + boxes.length;
  }

  function scrollLoanContentTo(preferredId) {
    var panel = document.querySelector('[data-panel="loan"]');
    if (!panel || panel.classList.contains("hidden")) return;
    var anchor = preferredId ? $(preferredId) : null;
    if (!anchor || anchor.classList.contains("hidden")) {
      anchor =
        panel.querySelector("#loanDashboard:not(.hidden)") ||
        panel.querySelector("#loanTrackerSubnav") ||
        panel.querySelector("#loanGuidanceRoot .loan-subnav") ||
        panel.querySelector("#loanGuidanceRoot") ||
        panel.querySelector(".loan-topbar");
    }
    if (!anchor) return;
    function run(smooth) {
      var top = anchor.getBoundingClientRect().top + window.pageYOffset - 76;
      window.scrollTo({ top: Math.max(0, top), behavior: smooth ? "smooth" : "auto" });
    }
    run(false);
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        run(true);
      });
    });
    setTimeout(function () {
      run(true);
    }, 160);
  }

  function scrollLoanPanelToTop() {
    scrollLoanContentTo(null);
  }

  function fetchGuidance(level) {
    if (typeof MwongozoApi === "undefined") {
      return Promise.reject(new Error("API unavailable"));
    }
    return MwongozoApi.fetchJson(
      "/loan/guidance?exam_level=" +
        encodeURIComponent(level) +
        "&language=" +
        encodeURIComponent(lang()),
      { method: "GET" }
    );
  }

  function renderGuidance(data) {
    var root = $("loanGuidanceRoot");
    if (!root || !data) return;
    var banner = $("loanTransparencyBanner");
    if (banner && data.transparency_banner) banner.textContent = data.transparency_banner;

    var checklistState = readChecklistState();
    var prefix = (data.exam_level || "o") + "_";

    var overviewHtml =
      '<div class="loan-hero">' +
      '<span class="loan-hero__ribbon">' +
      escapeHtml(t("Mwongozo Rasmi", "Official Guidance")) +
      "</span><h3>" +
      displayText(data.title || "") +
      '</h3><p class="muted">' +
      displayText(data.subtitle || "") +
      "</p>" +
      (data.tracker_note ? '<p class="loan-guidance-note">' + displayText(data.tracker_note) + "</p>" : "") +
      buildLinkPortfolio(data.official_links || []) +
      "</div>";

    var pathwayHtml = buildPathwayPanel(data);
    var learnHtml = '<div class="loan-info-grid">';
    (data.sections || []).forEach(function (sec) {
      learnHtml += '<article class="loan-info-card"><h4>' + escapeHtml(sec.title) + "</h4><p>" + escapeHtml(sec.body) + "</p>";
      if (sec.links && sec.links.length) learnHtml += buildLinkPortfolio(sec.links);
      learnHtml += "</article>";
    });
    learnHtml += "</div>";

    var total = (data.document_checklist || []).length;
    var doneCount = 0;
    (data.document_checklist || []).forEach(function (item) {
      if (checklistState[prefix + item.id]) doneCount += 1;
    });
    var pct = total ? Math.round((doneCount / total) * 100) : 0;

    var docsHtml =
      '<div class="loan-checklist-progress">' +
      '<div class="loan-checklist-progress__ring" style="--p:' +
      pct +
      '"><span>' +
      pct +
      '%</span></div>' +
      "<div><strong>" +
      escapeHtml(t("Maandalizi ya nyaraka", "Document preparation")) +
      "</strong>" +
      '<p class="muted small">' +
      escapeHtml(t("Weka alama unapokamilisha.", "Tick when each item is complete.")) +
      ' <span class="loan-subnav__badge" data-checklist-count>' +
      doneCount +
      "/" +
      total +
      "</span></p></div></div>" +
      '<ul class="loan-tick-grid">';
    (data.document_checklist || []).forEach(function (item) {
      docsHtml += buildTickCard(prefix + item.id, item.text, item.link, !!checklistState[prefix + item.id]);
    });
    docsHtml += "</ul>";

    var faqHtml = buildFaqPanel(data.faq || []);

    function panel(id, content) {
      return (
        '<div class="loan-section-panel' +
        (activeGuidanceSection === id ? " is-active" : "") +
        '" data-loan-section="' +
        id +
        '">' +
        content +
        "</div>"
      );
    }

    root.innerHTML =
      '<nav class="loan-subnav" role="tablist">' +
      buildSubnavHtml(GUIDANCE_NAV, "guidance-section", activeGuidanceSection) +
      '</nav><div class="loan-section-viewport">' +
      panel("overview", overviewHtml) +
      panel("pathway", pathwayHtml) +
      panel("learn", learnHtml) +
      panel("documents", docsHtml) +
      panel("faq", faqHtml) +
      "</div>";

        bindGuidanceSubnav(root);
    root.querySelectorAll("[data-checklist-id]").forEach(function (input) {
      input.addEventListener("change", function () {
        saveChecklistItem(input.getAttribute("data-checklist-id"), input.checked);
        var card = input.closest(".loan-tick-card");
        if (card) card.classList.toggle("is-done", input.checked);
        updateChecklistProgress(root);
      });
    });
    scrollLoanContentTo("loanGuidanceRoot");
  }

  function loadGuidance(level, force) {
    var root = $("loanGuidanceRoot");
    if (!root) return;
    if (!force && guidanceLoadedLevel === level && root.querySelector(".loan-section-viewport")) return;
    root.innerHTML =
      '<div class="loan-loading"><i class="fa-solid fa-spinner" aria-hidden="true"></i>' +
      escapeHtml(t("Inapakia mwongozo\u2026", "Loading guidance\u2026")) +
      "</div>";
    try {
      fetchGuidance(level)
        .then(function (data) {
          guidanceLoadedLevel = level;
          activeGuidanceSection = "overview";
          renderGuidance(data);
        })
        .catch(function (err) {
          var msg =
            err && err.message
              ? err.message
              : t("Imeshindwa kupakia mwongozo.", "Failed to load guidance.");
          root.innerHTML =
            '<div class="loan-error card glass"><p><strong>' +
            escapeHtml(t("Hitilafu", "Error")) +
            '</strong></p><p class="muted">' +
            escapeHtml(msg) +
            "</p></div>";
        });
    } catch (err) {
      root.innerHTML =
        '<p class="muted">' +
        escapeHtml(
          err && err.message ? err.message : t("Imeshindwa kupakia mwongozo.", "Failed to load guidance.")
        ) +
        "</p>";
    }
  }
  function renderDemoHint(refs) {
    var hint = $("loanDemoRefHint");
    if (!hint) return;
    var list = (refs || []).join(", ");
    hint.textContent = t(
      "Mifano ya nambari: " + list + " — chagua kadi hapo juu.",
      "Sample references: " + list + " — pick a card above."
    );
  }

  function demoCardClass(fundingStatus) {
    return "loan-demo-card--" + (fundingStatus || "in_progress");
  }

  function renderDemoStudentPicker(students) {
    var picker = $("loanDemoPicker");
    if (!picker) return;
    if (!students || !students.length) {
      picker.innerHTML =
        '<p class="muted small">' +
        escapeHtml(t("Haipatikani kwa sasa.", "Unavailable right now.")) +
        "</p>";
      return;
    }
    picker.innerHTML =
      '<div class="loan-demo-picker__grid">' +
      students
        .map(function (s) {
          return (
            '<button type="button" class="loan-demo-card ' +
            demoCardClass(s.funding_status) +
            '" data-demo-ref="' +
            escapeHtml(s.reference) +
            '"><span class="loan-demo-card__name">' +
            displayText(s.name) +
            '</span><span class="loan-demo-card__scenario">' +
            displayText(s.scenario) +
            '</span><span class="loan-demo-card__badge">' +
            displayText(s.funding_status_label) +
            '</span><span class="loan-demo-card__meta muted small">' +
            escapeHtml(s.reference) +
            " · " +
            escapeHtml(String(s.completion_percent || 0) + "%") +
            "</span></button>"
          );
        })
        .join("") +
      "</div>";
    picker.querySelectorAll("[data-demo-ref]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        loadDemoByRef(btn.getAttribute("data-demo-ref"));
      });
    });
  }

  function loadDemoByRef(ref) {
    var preset = DEMO_FORM_PRESETS[ref];
    if (!preset) return;
    setLoanTab("tracker");
    fillForm(preset);
    submitLoanForm();
  }

  function renderDemoProfileBanner(dash, data) {
    if (!dash) return;
    var banner = $("loanDemoBanner");
    if (!banner) {
      banner = document.createElement("div");
      banner.id = "loanDemoBanner";
      banner.className = "loan-demo-banner hidden";
      dash.insertBefore(banner, dash.firstChild);
    }
    var dp = data.demo_profile;
    if (!dp) {
      banner.className = "loan-demo-banner hidden";
      banner.innerHTML = "";
      return;
    }
    banner.className =
      "loan-demo-banner loan-demo-banner--" + (dp.funding_status || "in_progress");
    banner.innerHTML =
      '<div class="loan-demo-banner__head">' +
      '<h3 class="loan-demo-banner__name">' +
      escapeHtml(dp.name) +
      '</h3><span class="loan-demo-banner__status">' +
      displayText(dp.funding_status_label) +
      '</span></div><p class="muted small">' +
      displayText(dp.scenario) +
      " · " +
      escapeHtml(dp.reference) +
      "</p>";
    banner.classList.remove("hidden");
  }

  function renderDashboard(data) {
    var dash = $("loanDashboard");
    if (!dash || !data) return;
    dash.classList.remove("hidden");
    buildTrackerSubnav();
    renderDemoProfileBanner(dash, data);
    var initialView = "summary";
    if (data.demo_profile && data.demo_profile.funding_status === "denied") {
      initialView = "support";
    }
    setTrackerView(initialView);

    var ft = data.funding_table || {};
    var today = data.today_actions || [];
    var todayCard = $("loanTodayCard");
    if (todayCard) {
      todayCard.innerHTML =
        '<div class="loan-today-card__head"><span class="loan-today-card__icon"><i class="fa-solid fa-thumbtack" aria-hidden="true"></i></span><div><h3>' +
        escapeHtml(t("Unahitaji leo", "What you need today")) +
        '</h3><p class="muted small">' +
        escapeHtml(t("Hatua 3 za haraka", "Top 3 immediate actions")) +
        "</p></div></div><ul class=\"loan-today-list loan-status-list\">" +
        today
          .map(function (a) {
            return statusItemHtml("ok", escapeHtml(a));
          })
          .join("") +
        "</ol>";
    }

    var metrics = $("loanMetricsRow");
    if (metrics) {
      metrics.innerHTML =
        '<div class="loan-metric glass">' +
        faIconHtml("fa-chart-pie", "loan-metric__icon") +
        '<span class="loan-metric__label">' +
        escapeHtml(t("Ukamilifu", "Completion")) +
        '</span><strong class="loan-metric__value">' +
        escapeHtml(String(data.completion_percent || 0)) +
        '%</strong></div><div class="loan-metric glass">' +
        faIconHtml("fa-hand-holding-dollar", "loan-metric__icon") +
        '<span class="loan-metric__label">' +
        escapeHtml(t("Uwezekano wa ufadhili", "Funding probability")) +
        '</span><strong class="loan-metric__value">' +
        escapeHtml(String(ft.funding_probability || 0)) +
        '%</strong></div><div class="loan-metric glass loan-metric--batch">' +
        faIconHtml("fa-layer-group", "loan-metric__icon") +
        '<span class="loan-metric__label">' +
        escapeHtml(t("Batch", "Batch")) +
        '</span><strong class="loan-metric__value loan-metric__value--sm">' +
        displayText(ft.batch_prediction || "—") +
        "</strong></div>";
    }

    var tbody = $("loanFundingTableBody");
    if (tbody) {
      tbody.innerHTML =
        "<tr><td>" +
        escapeHtml(ft.heslb_reference) +
        "</td><td>" +
        escapeHtml(stageLabel(ft.application_stage)) +
        "</td><td>" +
        escapeHtml(String(ft.completion_percent) + "%") +
        "</td><td>" +
        displayText(ft.batch_prediction) +
        "</td><td><strong>" +
        escapeHtml(String(ft.funding_probability) + "%") +
        "</strong></td><td>" +
        escapeHtml(String(ft.alerts_count)) +
        "</td><td>" +
        escapeHtml(ft.appeal_eligible ? t("Ndiyo", "Yes") : t("Hapana", "No")) +
        "</td></tr>";
    }

    var cf = data.course_funding || {};
    var pri = $("loanCoursePriority");
    if (pri) {
      pri.innerHTML =
        '<p class="loan-priority-msg">' +
        displayText(cf.message || "") +
        '</p><div class="loan-prob-bar" role="progressbar" aria-valuenow="' +
        Math.min(100, cf.funding_probability || 0) +
        '" aria-valuemin="0" aria-valuemax="100"><span style="width:' +
        Math.min(100, cf.funding_probability || 0) +
        '%"></span></div><p class="loan-panel-foot muted small">' +
        faIconHtml("fa-layer-group", "loan-inline-icon") +
        " " +
        escapeHtml(t("Kipaumbele: ", "Priority: ") + (cf.priority || "—")) +
        "</p>";
    }

    var comp = $("loanCompletionBlock");
    if (comp) {
      var pct = data.completion_percent || 0;
      comp.innerHTML =
        '<div class="loan-completion-block">' +
        '<div class="loan-ring" style="--pct:' +
        pct +
        '"><span>' +
        pct +
        '%</span></div>' +
        '<p class="loan-panel-lead muted small">' +
        escapeHtml(t("Kulingana na hatua za OLAS", "Based on OLAS steps")) +
        "</p></div>";
    }

    var tl = $("loanTimeline");
    if (tl) {
      tl.innerHTML = (data.timeline || [])
        .map(function (step) {
          var statusKey = String(step.status || "pending").replace(/_/g, " ");
          return (
            '<li class="loan-timeline__item loan-timeline__item--' +
            escapeHtml(step.status) +
            '">' +
            faIconHtml(timelineIconForStatus(step.status, step.icon), "loan-timeline__icon") +
            '<div class="loan-timeline__body"><div class="loan-timeline__title-row">' +
            '<span class="loan-timeline__step">#' +
            escapeHtml(String(step.step)) +
            "</span>" +
            '<strong class="loan-timeline__title">' +
            escapeHtml(step.title) +
            "</strong></div>" +
            '<span class="loan-timeline__status">' +
            escapeHtml(statusKey) +
            "</span></div></li>"
          );
        })
        .join("");
    }

    var batch = $("loanBatchBlock");
    if (batch && data.batch_prediction) {
      if (data.batch_prediction.preparation_mode) {
        batch.innerHTML =
          '<p class="muted">' +
          escapeHtml(
            t(
              "Uko katika hatua ya maandalizi — Batch itakuwa baada ya kuingia chuo na OLAS.",
              "You are in preparation mode — Batch applies after university admission and OLAS."
            )
          ) +
          "</p>";
      } else {
        var batchProb = data.batch_prediction.batch_one_probability;
        batch.innerHTML =
          "<p><strong>" +
          escapeHtml(t("Batch One Probability:", "Batch One Probability:")) +
          "</strong> " +
          escapeHtml(batchProb == null ? "—" : String(batchProb) + "%") +
          "</p>" +
          (data.batch_prediction.alternative_note
            ? '<p class="muted small">' + displayText(data.batch_prediction.alternative_note) + "</p>"
            : "");
      }
    }

    var conf = $("loanConfidenceBlock");
    if (conf && data.funding_confidence) {
      conf.innerHTML =
        '<div class="loan-conf-value">' +
        faIconHtml("fa-gauge-high", "loan-conf-value__icon") +
        '<span class="loan-conf-value__pct">' +
        escapeHtml(String(data.funding_confidence.percent) + "%") +
        '</span></div><p class="loan-panel-lead muted small">' +
        escapeHtml(t("Imekokotwa kwa:", "Based on:")) +
        '</p><ul class="loan-factor-list">' +
        (data.funding_confidence.factors || [])
          .map(function (f) {
            return statusItemHtml("ok", escapeHtml(f));
          })
          .join("") +
        "</ul>";
    }

    var cit = $("loanCitizenshipBlock");
    if (cit && data.citizenship) {
      cit.innerHTML =
        '<p class="loan-panel-lead">' +
        displayText(data.citizenship.note) +
        '</p><ul class="loan-status-list">' +
        statusItemHtml(
          data.citizenship.nin_valid ? "ok" : "pending",
          escapeHtml(t("NIN sahihi (muundo)", "NIN format valid"))
        ) +
        statusItemHtml(
          data.citizenship.nin_provided ? "ok" : "warn",
          escapeHtml(
            data.citizenship.nin_provided
              ? t("NIN imewekwa", "NIN provided")
              : t("Ongeza NIN", "Add NIN")
          )
        ) +
        "</ul>";
    }

    var spec = $("loanSpecialBlock");
    if (spec && data.special_categories) {
      var sc = data.special_categories;
      spec.innerHTML =
        '<ul class="loan-status-list">' +
        [
          ["orphan", t("Yatima", "Orphan")],
          ["disability", t("Ulemavu", "Disability")],
          ["low_income", t("Kipato cha chini", "Low income")],
          ["single_parent_household", t("Mzazi mmoja", "Single-parent household")],
        ]
          .map(function (pair) {
            return statusItemHtml(sc[pair[0]] ? "ok" : "off", escapeHtml(pair[1]));
          })
          .join("") +
        '</ul><p class="loan-panel-foot muted small">' +
        escapeHtml(
          t("Ongezeko la uwezekano: +", "Probability boost: +") +
            String(sc.boost_percent || 0) +
            "%"
        ) +
        "</p>";
    }

    var alerts = $("loanAlertList");
    if (alerts) {
      alerts.innerHTML = (data.alerts || [])
        .map(function (a) {
          var lvl = a.level || "info";
          return (
            '<li class="loan-alert loan-alert--' +
            escapeHtml(lvl) +
            '">' +
            faIconHtml(alertIconForLevel(lvl), "loan-alert__icon") +
            '<span class="loan-alert__text">' +
            displayText(a.text) +
            "</span></li>"
          );
        })
        .join("");
    }

    var deadlines = $("loanDeadlineList");
    if (deadlines) {
      deadlines.innerHTML = (data.deadline_hints || [])
        .map(function (d) {
          return statusItemHtml("clock", escapeHtml(d.text), "li");
        })
        .join("");
    }

    var risks = $("loanRiskList");
    if (risks) {
      risks.innerHTML = (data.risk_flags || [])
        .map(function (f) {
          return statusItemHtml("warn", escapeHtml(riskLabel(f)));
        })
        .join("");
    }

    var mistakes = $("loanMistakeList");
    if (mistakes) {
      mistakes.innerHTML = (data.common_mistakes || [])
        .map(function (m) {
          return (
            '<li class="loan-mistake-item">' +
            faIconHtml("fa-circle-xmark", "loan-mistake-item__icon") +
            '<span class="loan-mistake-item__body"><strong>' +
            escapeHtml(m.title) +
            "</strong><span> — " +
            escapeHtml(m.detail) +
            "</span></span></li>"
          );
        })
        .join("");
    }

    var schol = $("loanScholarshipBlock");
    if (schol) {
      var html = "";
      if (data.scholarship_note) {
        html += '<p class="loan-scholarship-note">' + escapeHtml(data.scholarship_note) + "</p>";
      }
      html += "<ul>";
      html += (data.scholarship_alternatives || [])
        .map(function (s) {
          var label = lang() === "en" ? s.en : s.sw;
          return (
            '<li><a href="' +
            escapeHtml(s.url) +
            '" target="_blank" rel="noopener noreferrer">' +
            escapeHtml(label) +
            "</a></li>"
          );
        })
        .join("");
      html += "</ul>";
      schol.innerHTML = html;
    }

    var appeal = $("loanAppealBlock");
    if (appeal && data.appeal_guidance) {
      var ag = data.appeal_guidance;
      var eligible = !!ag.appeal_eligibility;
      var reasons = ag.possible_reasons || [];
      var html =
        '<div class="loan-appeal-panel' +
        (eligible ? " loan-appeal-panel--open" : "") +
        '"><p class="loan-appeal-panel__lead">' +
        escapeHtml(
          eligible
            ? t(
                "Rufaa inawezekana — sababu zilizoorodheshwa na hatua zifuatazo hapa chini.",
                "Appeal is open — listed reasons and next steps below."
              )
            : t(
                "Rufaa haihitajiki kwa sasa — fuata taarifa rasmi za HESLB kwenye OLAS.",
                "No appeal needed for now — follow official HESLB notices on OLAS."
              )
        ) +
        "</p>";
      if (reasons.length) {
        html +=
          '<h4 class="small">' +
          escapeHtml(t("Sababu zinazoweza:", "Possible reasons:")) +
          '</h4><ul class="loan-status-list">' +
          reasons
            .map(function (r) {
              return statusItemHtml("warn", displayText(r));
            })
            .join("") +
          "</ul>";
      }
      if ((ag.required_documents || []).length) {
        html +=
          '<h4 class="small">' +
          escapeHtml(t("Nyaraka zinazohitajika:", "Documents often required:")) +
          "</h4><ul>" +
          (ag.required_documents || [])
            .map(function (d) {
              return "<li>" + escapeHtml(d) + "</li>";
            })
            .join("") +
          "</ul>";
      }
      if ((ag.next_steps || []).length) {
        html +=
          '<h4 class="small">' +
          escapeHtml(t("Hatua zinazofuata:", "Next steps:")) +
          "</h4><ol>" +
          (ag.next_steps || [])
            .map(function (s) {
              return "<li>" + escapeHtml(s) + "</li>";
            })
            .join("") +
          "</ol>";
      }
      html += "</div>";
      appeal.innerHTML = html;
    }

    var parent = $("loanParentList");
    if (parent) {
      parent.innerHTML = (data.parent_guidance || [])
        .map(function (g) {
          var text = lang() === "en" ? g.en : g.sw;
          return statusItemHtml("ok", escapeHtml(text));
        })
        .join("");
    }

    var insights = $("loanInsightList");
    if (insights) {
      insights.innerHTML = (data.success_insights || [])
        .map(function (ins) {
          var text = lang() === "en" ? ins.en : ins.sw;
          return statusItemHtml("ok", escapeHtml(text));
        })
        .join("");
    }

    scrollLoanContentTo("loanDashboard");
  }

  function trackLoan(payload) {
    if (typeof MwongozoApi === "undefined") {
      return Promise.reject(new Error("API unavailable"));
    }
    return MwongozoApi.fetchJson("/loan/track", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  function submitLoanForm() {
    var payload = collectFormPayload();
    saveProfile(payload);
    var btn = $("loanTrackSubmit");
    if (btn) btn.disabled = true;
    return trackLoan(payload)
      .then(function (data) {
        renderDashboard(data);
        if (typeof global.addRecentActivity === "function") {
          global.addRecentActivity(
            "loan",
            t("Dashibodi ya HESLB imefunguliwa", "HESLB dashboard opened"),
            payload.heslb_reference || payload.exam_number || ""
          );
        }
      })
      .catch(function (err) {
        if (typeof global.toast === "function") {
          global.toast(err.message || t("Imeshindwa kupakia", "Failed to load"), "warn");
        }
      })
      .finally(function () {
        if (btn) btn.disabled = false;
      });
  }

  var loanBound = false;

  function initLoanTracker() {
    loadCatalogHints();
    prefillFromExamContext();

    if (!loanBound) {
      loanBound = true;
      document.querySelectorAll("[data-loan-tab]").forEach(function (btn) {
        btn.addEventListener("click", function () {
          setLoanTab(btn.getAttribute("data-loan-tab"));
        });
      });
      var guidanceLevel = $("loanGuidanceLevel");
      if (guidanceLevel) {
        guidanceLevel.addEventListener("change", function () {
          syncExamLevelSelects(guidanceLevel.value);
          guidanceLoadedLevel = "";
          loadGuidance(guidanceLevel.value, true);
        });
      }
      var examLevel = $("loanExamLevel");
      if (examLevel) {
        examLevel.addEventListener("change", function () {
          syncExamLevelSelects(examLevel.value);
          if ($("loanGuidanceLevel")) $("loanGuidanceLevel").value = examLevel.value;
          guidanceLoadedLevel = "";
          if (activeLoanTab === "guidance") loadGuidance(examLevel.value, true);
        });
      }
      var form = $("loanTrackForm");
      if (form) {
        form.addEventListener("submit", function (e) {
          e.preventDefault();
          setLoanTab("tracker");
          submitLoanForm();
        });
      }
    }

    setLoanTab(activeLoanTab);

    if (typeof MwongozoApi !== "undefined") {
      MwongozoApi.fetchJson("/loan/demo-references?language=" + lang(), { method: "GET" })
        .then(function (res) {
          renderDemoHint(res.references || []);
          renderDemoStudentPicker(res.students || []);
          renderOfficialLinks([
            {
              label: "HESLB — Application guidelines",
              url: "https://www.heslb.go.tz/application_guideline",
            },
            { label: "OLAS", url: "https://olas.heslb.go.tz/" },
            { label: "NIDA", url: "https://www.nida.go.tz/" },
            { label: "RITA", url: "https://www.rita.go.tz/" },
          ]);
        })
        .catch(function () {
          renderDemoHint([DEMO_REF, "HSL-2026-00482", "HSL-2026-00991"]);
          renderDemoStudentPicker([
            {
              reference: "HSL-2026-00127",
              name: "Amina Mwanga",
              scenario: t("Njiani — uthibitisho", "Mid-way — verification"),
              funding_status: "in_progress",
              funding_status_label: t("Njiani", "In progress"),
              completion_percent: 54,
            },
            {
              reference: "HSL-2026-00482",
              name: "Baraka Komba",
              scenario: t("Amekamilisha — alipatiwa mkopo", "Completed — funded"),
              funding_status: "approved",
              funding_status_label: t("Alipatiwa mkopo", "Funded"),
              completion_percent: 100,
            },
            {
              reference: "HSL-2026-00991",
              name: "Neema Sudi",
              scenario: t("Amekamilisha — hakupangiwa, rufaa", "Completed — appeal"),
              funding_status: "denied",
              funding_status_label: t("Hakupangiwa — rufaa", "Not allocated — appeal"),
              completion_percent: 100,
            },
          ]);
        });
    }

    var saved = readProfile();
    if (saved) fillForm(saved);
  }

  global.initLoanTracker = initLoanTracker;
})(typeof window !== "undefined" ? window : globalThis);
