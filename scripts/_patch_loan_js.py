from pathlib import Path

path = Path("backend/static/loan-tracker.js")
text = path.read_text(encoding="utf-8")

# Fix mojibake
text = text.replace("\u00e2\u20ac\u201d", "\u2014").replace("â€"", "\u2014").replace("â€¦", "\u2026")

helpers = r'''
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
    dash.querySelectorAll("[data-tracker-view]").forEach(function (view) {
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
          return (
            '<li><a class="loan-link-card" href="' +
            escapeHtml(l.url) +
            '" target="_blank" rel="noopener noreferrer">' +
            '<span class="loan-link-card__icon"><i class="fa-solid ' +
            icon +
            '" aria-hidden="true"></i></span>' +
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
          return (
            '<li class="loan-step-card"><span class="loan-step-card__num">' +
            escapeHtml(String(step.step)) +
            '</span><strong>' +
            escapeHtml(step.title) +
            "</strong><p>" +
            escapeHtml(step.detail) +
            "</p></li>"
          );
        })
        .join("") +
      "</ol>"
    );
  }

  function buildTickCard(cid, text, link, checked) {
    var inner =
      link ?
        '<a href="' + escapeHtml(link) + '" target="_blank" rel="noopener noreferrer">' + escapeHtml(text) + "</a>"
      : escapeHtml(text);
    return (
      '<li><label class="loan-tick-card">' +
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

  function updateChecklistProgress(root, prefix) {
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

'''

start = text.index("  function fetchGuidance(level)")
end = text.index("  function renderDemoHint(refs)")

new_render = r'''
  function fetchGuidance(level) {
    if (typeof MwongozoApi === "undefined") {
      return Promise.reject(new Error("API unavailable"));
    }
    return MwongozoApi.fetchJson(
      "/loan/guidance?exam_level=" + encodeURIComponent(level) + "&language=" + encodeURIComponent(lang()),
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
    var allLinks = data.official_links || [];

    var overviewHtml =
      '<div class="loan-hero">' +
      '<span class="loan-hero__ribbon">' +
      escapeHtml(t("DEMO + Mwongozo Rasmi", "DEMO + Official Guidance")) +
      "</span>" +
      "<h3>" +
      escapeHtml(data.title || "") +
      "</h3>" +
      '<p class="muted">' +
      escapeHtml(data.subtitle || "") +
      "</p>" +
      (data.tracker_note ? '<p class="loan-guidance-note">' + escapeHtml(data.tracker_note) + "</p>" : "") +
      buildLinkPortfolio(allLinks) +
      "</motion>";

    overviewHtml = overviewHtml.replace("</motion>", "</div>");

    var pathwaySteps = (data.pathway_steps || []).concat(data.olas_steps || []);
    var pathwayHtml = buildStepCards(pathwaySteps);

    var learnHtml = '<motion class="loan-info-grid">';
    learnHtml = '<motion class="loan-info-grid">';
    learnHtml = '<div class="loan-info-grid">';
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
      '</strong><p class="muted small">' +
      escapeHtml(t("Weka alama unapokamilisha kila kipengele.", "Tick each item when complete.")) +
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

    var faqHtml = '<div class="loan-faq-list">';
    (data.faq || []).forEach(function (item, idx) {
      faqHtml +=
        '<details class="loan-faq-item"' +
        (idx === 0 ? " open" : "") +
        "><summary>" +
        escapeHtml(item.question) +
        "</summary><p>" +
        escapeHtml(item.answer) +
        "</p></details>";
    });
    faqHtml += "</div>";

    var navHtml = buildSubnavHtml(GUIDANCE_NAV, "guidance-section", activeGuidanceSection);

    root.innerHTML =
      '<nav class="loan-subnav" role="tablist">' +
      navHtml +
      '</nav><div class="loan-section-viewport">' +
      '<div class="loan-section-panel' +
      (activeGuidanceSection === "overview" ? " is-active" : "") +
      '" data-loan-section="overview">' +
      overviewHtml +
      "</div>" +
      '<div class="loan-section-panel' +
      (activeGuidanceSection === "pathway" ? " is-active" : "") +
      '" data-loan-section="pathway">' +
      pathwayHtml +
      "</div>" +
      '<div class="loan-section-panel' +
      (activeGuidanceSection === "learn" ? " is-active" : "") +
      '" data-loan-section="learn">' +
      learnHtml +
      "</motion>" +
      '<div class="loan-section-panel' +
      (activeGuidanceSection === "documents" ? " is-active" : "") +
      '" data-loan-section="documents">' +
      docsHtml +
      "</div>" +
      '<div class="loan-section-panel' +
      (activeGuidanceSection === "faq" ? " is-active" : "") +
      '" data-loan-section="faq">' +
      faqHtml +
      "</div></div>";

    root.innerHTML = root.innerHTML.replace(/<\/?motion>/g, function (t) {
      return t.indexOf("/") === 1 ? "</motion>" : "<motion";
    });
    root.innerHTML = root.innerHTML.replace(/<motion>/g, "").replace(/<\/motion>/g, "");
    root.innerHTML = root.innerHTML.replace(/<motion /g, "<div ").replace(/<\/motion>/g, "</div>");

    root.querySelectorAll("[data-guidance-section]").forEach(function (btn) {
      btn.setAttribute("data-guidance-section", btn.getAttribute("data-guidance-section") || btn.getAttribute("data-guidance-section"));
    });
    var nav = root.querySelector(".loan-subnav");
    if (nav) {
      nav.querySelectorAll(".loan-subnav__btn").forEach(function (btn, i) {
        btn.setAttribute("data-guidance-section", GUIDANCE_NAV[i].id);
      });
    }

    bindGuidanceSubnav(root);
    root.querySelectorAll("[data-checklist-id]").forEach(function (input) {
      input.addEventListener("change", function () {
        saveChecklistItem(input.getAttribute("data-checklist-id"), input.checked);
        var card = input.closest(".loan-tick-card");
        if (card) card.classList.toggle("is-done", input.checked);
        updateChecklistProgress(root, prefix);
      });
      var card = input.closest(".loan-tick-card");
      if (card) card.classList.toggle("is-done", input.checked);
    });
  }

  function loadGuidance(level, force) {
    var root = $("loanGuidanceRoot");
    if (!root) return;
    if (!force && guidanceLoadedLevel === level && root.querySelector(".loan-section-viewport")) return;
    root.innerHTML =
      '<div class="loan-loading"><i class="fa-solid fa-spinner" aria-hidden="true"></i>' +
      escapeHtml(t("Inapakia mwongozo\u2026", "Loading guidance\u2026")) +
      "</motion>";
    root.innerHTML = root.innerHTML.replace("</motion>", "</motion>");
    root.innerHTML =
      '<div class="loan-loading"><i class="fa-solid fa-spinner" aria-hidden="true"></i>' +
      escapeHtml(t("Inapakia mwongozo\u2026", "Loading guidance\u2026")) +
      "</motion>";
    root.innerHTML =
      '<div class="loan-loading"><i class="fa-solid fa-spinner" aria-hidden="true"></i>' +
      escapeHtml(t("Inapakia mwongozo\u2026", "Loading guidance\u2026")) +
      "</div>";
    fetchGuidance(level)
      .then(function (data) {
        guidanceLoadedLevel = level;
        activeGuidanceSection = "overview";
        renderGuidance(data);
      })
      .catch(function () {
        root.innerHTML = '<p class="muted">' + escapeHtml(t("Imeshindwa kupakia mwongozo.", "Failed to load guidance.")) + "</p>";
      });
  }

'''

# Clean up botched new_render - write it properly in a file
Path("scripts/_loan_render_snippet.js").write_text("", encoding="utf-8")
