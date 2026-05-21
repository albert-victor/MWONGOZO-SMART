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
      escapeHtml(t("DEMO + Mwongozo Rasmi", "DEMO + Official Guidance")) +
      "</span><h3>" +
      escapeHtml(data.title || "") +
      '</h3><p class="muted">' +
      escapeHtml(data.subtitle || "") +
      "</p>" +
      (data.tracker_note ? '<p class="loan-guidance-note">' + escapeHtml(data.tracker_note) + "</p>" : "") +
      buildLinkPortfolio(data.official_links || []) +
      "</div>";

    var pathwayHtml = buildStepCards((data.pathway_steps || []).concat(data.olas_steps || []));
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
  }

  function loadGuidance(level, force) {
    var root = $("loanGuidanceRoot");
    if (!root) return;
    if (!force && guidanceLoadedLevel === level && root.querySelector(".loan-section-viewport")) return;
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
        root.innerHTML =
          '<p class="muted">' + escapeHtml(t("Imeshindwa kupakia mwongozo.", "Failed to load guidance.")) + "</p>";
      });
  }
