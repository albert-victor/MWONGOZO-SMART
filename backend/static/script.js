/* Mwongozo Smart — dashboard UI, forms, recommendations (preserves backend payloads & routes). */
(function () {
  "use strict";

  var boot = window.__MWONGOZO_BOOT__ || {};
  var subjectCatalog = boot.subjectCatalog || [];
  var gradeOptions = boot.gradeOptions || [];
  var samplePayload = boot.samplePayload || {};
  var oLevelSubjectsCatalog = boot.oLevelSubjectsCatalog || [];
  var defaultOLevelSubjects = boot.defaultOLevelSubjects || [];

  var aLevelContainer = document.getElementById("aLevelSubjects");
  var oLevelContainer = document.getElementById("oLevelSubjects");
  var resultsEl = document.getElementById("results");
  var resultSummaryEl = document.getElementById("resultSummary");
  var inputView = document.getElementById("inputView");
  var resultsView = document.getElementById("resultsView");
  var pathwayInput = document.getElementById("pathway");
  var levelPrompt = document.getElementById("levelPrompt");
  var aLevelSection = document.getElementById("aLevelSection");
  var oLevelSection = document.getElementById("oLevelSection");
  var pathwayButtons = document.querySelectorAll("[data-pathway-button]");
  var combinationInput = document.getElementById("combination");
  var themeToggles = document.querySelectorAll(".js-theme-toggle");
  var themeLabels = document.querySelectorAll(".js-theme-label");
  var nectaLookupWrap = document.getElementById("nectaLookupWrap");
  var nectaExamYear = document.getElementById("nectaExamYear");
  var nectaIndexNo = document.getElementById("nectaIndexNo");
  var nectaIndexHint = document.getElementById("nectaIndexHint");
  var nectaLookupMsg = document.getElementById("nectaLookupMsg");
  var nectaFetchBtn = document.getElementById("nectaFetchBtn");
  var formRecommendStatus = document.getElementById("formRecommendStatus");
  var mainWrapInner = document.getElementById("mainWrapInner");
  var landingView = document.getElementById("landingView");
  var dashboardShell = document.getElementById("dashboardShell");
  var toastRoot = document.getElementById("toastRoot");
  var modalRoot = document.getElementById("modalRoot");
  var metaStatsEl = document.getElementById("metaStats");
  var directoryBody = document.getElementById("directoryTableBody");
  var directorySearch = document.getElementById("directorySearch");
  var directoryRegion = document.getElementById("directoryRegion");
  var directoryInstitution = document.getElementById("directoryInstitution");
  var chatMessages = document.getElementById("chatMessages");
  var chatInput = document.getElementById("chatInput");
  var chatSend = document.getElementById("chatSend");

  var directoryRows = [];
  var institutionsByCode = {};

  var resultsPagination = {
    items: [],
    page: 0,
    pageSize: 16,
    directCount: 0,
    reviewCount: 0,
    filters: { query: "", region: "all", category: "all", sort: "confidence_desc" },
    _filteredSorted: [],
  };

  if (typeof customElements !== "undefined" && !customElements.get("mw-result-card")) {
    customElements.define(
      "mw-result-card",
      class extends HTMLElement {
        /* Classic card shell; content from innerHTML set by renderer. */
      }
    );
  }

  var I18N = {
    sw: {
      brand: "MWONGOZO SMART",
      brand_short: "MWONGOZO",
      login_demo: "Ingia",
      cta_start: "Anza sasa",
      cta_dashboard: "Fungua dashboard",
      cta_register: "Sajili (demo)",
      cta_skip: "Ruka landing",
      cta_skip_link: "Ruka landing → fungua dashboard moja kwa moja",
      cta_start_results: "Anza bure — weka matokeo",
      cta_have_account: "Nina akaunti (demo)",
      hero_badge: "Mwongozo rasmi wa kujiunga na vyuo — Tanzania",
      hero_l1: "Pata njia yako kwenda",
      hero_l2: "elimu ya juu",
      hero_l3: " nchini",
      hero_l4: "Tanzania",
      hero_p:
        "Weka matokeo ya A-Level / O-Level, gundua programme unazostahili kulingana na TCU Guidebook, na upate muhtasari wa HESLB — ndani ya mfumo huu.",
      feat_head: "Kwa nini MWONGOZO SMART",
      feat_k1: "Nyumbani",
      feat_t1: "Uchambuzi wa matokeo",
      feat_d1: "Weka alama za ACSEE / CSEE; mfumo unalinganisha na mahitaji rasmi ya TCU kabla ya mapendekezo.",
      feat_k2: "Mapendekezo",
      feat_t2: "Vyuo 90+",
      feat_d2: "Taasisi zilizoidhinishwa na TCU: vyuo vikuu, vyuo binafsi, na taasisi nyingine.",
      feat_k3: "Mkopo",
      feat_t3: "Mwongozo wa HESLB",
      feat_d3: "Hatua za OLAS na nyaraka muhimu — sehemu kamili iko kwenye dashboard.",
      feat_k4: "Msaada",
      feat_t4: "Kisaidizi cha mazungumzo",
      feat_d4: "Maswali kuhusu maombi, NECTA, au TCU — majibu ya haraka (si huduma ya nje ya AI).",
      news_land_title: "Habari, matangazo & deadlines",
      news_land_sub:
        "Fuata TCU, HESLB, na taasisi — tarehe hizi ni mfano wa kielimu; thibitisha kila mwaka kwenye tovuti rasmi.",
      news_1t: "TCU · Mwongozo wa kujiunga",
      news_1d: "Angalia dirisha la maombi la taasisi husika na Guidebook la mwaka unaofuata.",
      news_2t: "Mkopo wa elimu ya juu (HESLB)",
      news_2d: "Fuata tangazo la OLAS; hakikisha majina yanalingana na NIDA kabla ya deadline.",
      news_3date: "NECTA",
      news_3t: "Matokeo ya CSEE / ACSEE",
      news_3d: "Pakua matokeo kwa mwaka na CNO moja kwa moja kwenye dashboard.",
      news_4date: "Taasisi",
      news_4t: "Maombi ya chuo",
      news_4d: "Kila chuo kinaweza kuwa na tarehe tofauti — thibitisha tovuti rasmi ya chuo unachotaka.",
      hero_stat1n: "90+",
      hero_stat1l: "Vyuo vilivyoorodheshwa",
      hero_stat2n: "800+",
      hero_stat2l: "Programme za shahada",
      hero_stat3n: "100%",
      hero_stat3l: "Msingi wa TCU Guidebook",
      hero_stat4n: "Bure",
      hero_stat4l: "Maelezo ya msingi",
      sectors_title: "Sekta muhimu za elimu Tanzania",
      sector_tcu:
        "Tanzania Commission for Universities — viwango vya kujiunga, Guidebook, na usajili wa programme.",
      sector_necta: "Mitihani ya CSEE na ACSEE; matokeo rasmi na historia ya TETEA kwa miaka ya nyuma.",
      sector_heslb: "Bodi ya Mikopo ya Elimu ya Juu — maombi ya mkopo, OLAS, na viwango vya uhitaji.",
      sector_tveta: "Mafunzo ya ufundi na stadi; njia mbadala za kujiunga na taaluma za soko.",
      sector_univ: "Vyuo vikuu, vyuo vya ufundi, na taasisi — programu nyingi zinaweza kuchanganuliwa.",
      sector_quality: "Ufuatiliaji wa ubora, usajili wa vyuo, na usawa wa fursa kwa wanafunzi.",
      stat_tcu: "Guidebook + rules",
      stat_necta: "Rasmi + TETEA",
      stat_levels: "Form 6 & Form 4",
      feat1_t: "Eligibility kwanza",
      feat1_p: "Sheria za TCU kwanza, kisha upangaji — uwazi kwa mwanafunzi na mzazi.",
      feat2_t: "Matokeo halisi",
      feat2_p: "Pakua matokeo NECTA au TETEA; fomu inajazwa kiotomatiki bila kubadili API.",
      feat3_t: "Orodha ya vyuo",
      feat3_p: "Chuja programme kwa mkoa na chuo; maelezo kamili kwenye dirisha la modal.",
      sidebar_foot: "MWONGOZO SMART · TCU & NECTA",
      fab_story: "Tupige story",
      chat_head: "SAM — msaada wa haraka",
      chat_intro: "Majibu ya haraka kuhusu mfumo huu (si huduma ya nje ya AI).",
      chat_ph: "Andika ujumbe…",
      chat_send: "Tuma",
      results_head: "Mapendekezo",
      results_mkoa: "Mkoa",
      results_cat: "Category",
      results_conf: "Confidence",
      results_search_ph: "Tafuta chuo, course…",
      results_more: "Maelezo zaidi",
      results_why: "Kwa nini",
      results_parallel: "Kozi parallel",
      results_rules: "Sheria",
      nav_home: "Nyumbani",
      nav_input: "Matokeo",
      nav_results: "Mapendekezo",
      nav_directory: "Vyuo & programme",
      nav_loan: "Mkopo & HESLB",
      nav_assistant: "Msaada",
      nav_news: "Habari & deadline",
      results_col_rank: "#",
      results_col_inst: "Chuo",
      results_col_prog: "Programme / kozi",
      results_col_region: "Mkoa",
      results_col_cap: "Capacity",
      results_col_pts: "Alama",
      results_col_conf: "Confidence",
      results_col_type: "Aina",
      results_col_actions: "Vitendo",
      results_direct: "Moja kwa moja",
      results_borderline: "Mpaka / parallel",
      results_detail_btn: "Maelezo",
      results_detail_title: "Programme",
      results_quick_all: "Zote",
      results_quick_health: "Afya",
      results_quick_econ: "Uchumi",
      results_quick_law: "Sheria",
      reco_loading: "Inachambua na TCU Guidebook — subiri…",
      reco_success_line: "Imepakuliwa kwa mafanikio",
      necta_loading: "Inapakia kutoka NECTA / TETEA…",
      necta_success_line: "Imepakiwa",
      sam_intro:
        "Hujambo! Mimi ni SAM (Smart Admission Mate). Ninaweza kukusaidia na: kupakia matokeo kutoka NECTA/TETEA, kuelewa mapendekezo ya programme kulingana na TCU, kuchunguza orodha ya vyuo na programme, mwongozo wa HESLB/mkopo, na maswali ya jumla kuhusu mchakato wa maombi. Andika swali lako hapa chini.",
      land_meta_heading: "Takwimu za mfumo",
      land_meta_prog: "Programme zilizopakiwa",
      land_meta_inst: "Taasisi",
      land_meta_intro_sw:
        "Hivi ndivyo mfumo unaougusa leo — takwimu halisi kutoka orodha ya TCU Guidebook iliyopakiwa kwenye seva hii.",
    },
    en: {
      brand: "MWONGOZO SMART",
      brand_short: "MWONGOZO",
      login_demo: "Login",
      cta_start: "Get started",
      cta_dashboard: "Open dashboard",
      cta_register: "Register (demo)",
      cta_skip: "Skip landing",
      cta_skip_link: "Skip landing → open dashboard directly",
      cta_start_results: "Start free — enter results",
      cta_have_account: "I have an account (demo)",
      hero_badge: "Tanzania's university admission guide",
      hero_l1: "Find your path to",
      hero_l2: "higher education",
      hero_l3: " in ",
      hero_l4: "Tanzania",
      hero_p:
        "Enter A-Level / O-Level results, discover programmes you qualify for using the TCU Guidebook, and see HESLB guidance — all in this system.",
      feat_head: "Why MWONGOZO SMART",
      feat_k1: "Home",
      feat_t1: "Smart result analysis",
      feat_d1: "Enter ACSEE / CSEE grades; the engine matches official TCU entry requirements before recommendations.",
      feat_k2: "Recommendations",
      feat_t2: "90+ institutions",
      feat_d2: "TCU-accredited universities, private universities, university colleges, and other institutions.",
      feat_k3: "Loan guide",
      feat_t3: "HESLB guidance",
      feat_d3: "OLAS steps and key documents — full section inside the dashboard.",
      feat_k4: "Assistant",
      feat_t4: "Chat assistant",
      feat_d4: "Ask about admissions, NECTA, or TCU — quick scripted answers (not an external LLM).",
      news_land_title: "News, notices & deadlines",
      news_land_sub:
        "Follow TCU, HESLB, and your target institutions — dates are educational examples; confirm each year on official sites.",
      news_1t: "TCU · Admission guide",
      news_1d: "Check each institution's application window and the Guidebook for the upcoming academic year.",
      news_2t: "Higher education loan (HESLB)",
      news_2d: "Watch OLAS announcements; ensure names match NIDA before deadlines.",
      news_3date: "NECTA",
      news_3t: "CSEE / ACSEE results",
      news_3d: "Fetch results by year and candidate number directly from the MWONGOZO SMART dashboard.",
      news_4date: "Institutions",
      news_4t: "University applications",
      news_4d: "Each university may set different dates — always confirm on the official website.",
      hero_stat1n: "90+",
      hero_stat1l: "Universities listed",
      hero_stat2n: "800+",
      hero_stat2l: "Degree programmes",
      hero_stat3n: "100%",
      hero_stat3l: "Based on TCU Guidebook",
      hero_stat4n: "Free",
      hero_stat4l: "Core guidance",
      sectors_title: "Key sectors in Tanzanian education",
      sector_tcu:
        "Tanzania Commission for Universities — entry standards, the Guidebook, and programme registration.",
      sector_necta: "CSEE and ACSEE examinations; official results and TETEA archives for older years.",
      sector_heslb: "Higher Education Students' Loans Board — loan applications, OLAS, and requirements.",
      sector_tveta: "Technical and vocational training; alternative pathways to market-ready careers.",
      sector_univ: "Public and private universities and colleges — many programmes to compare.",
      sector_quality: "Quality assurance, institutional registration, and equitable access.",
      stat_tcu: "Guidebook + rules",
      stat_necta: "Official + TETEA",
      stat_levels: "Form 6 & Form 4",
      feat1_t: "Eligibility first",
      feat1_p: "TCU rules first, then ranking — clarity for students and guardians.",
      feat2_t: "Authentic results",
      feat2_p: "Fetch NECTA or TETEA results; the form fills without changing your API.",
      feat3_t: "Institution directory",
      feat3_p: "Filter by region and institution; full detail in a modal window.",
      sidebar_foot: "MWONGOZO SMART · TCU & NECTA",
      fab_story: "Let's talk",
      chat_head: "SAM — quick help",
      chat_intro: "Quick answers about this app (not an external AI service).",
      chat_ph: "Type a message…",
      chat_send: "Send",
      results_head: "Recommendations",
      results_mkoa: "Region",
      results_cat: "Category",
      results_conf: "Confidence",
      results_search_ph: "Search institution, course…",
      results_more: "More detail",
      results_why: "Why recommended",
      results_parallel: "Parallel courses",
      results_rules: "Rule trace",
      nav_home: "Home",
      nav_input: "Results",
      nav_results: "Recommendations",
      nav_directory: "Universities & programmes",
      nav_loan: "Loan & HESLB",
      nav_assistant: "Help",
      nav_news: "News & deadlines",
      results_col_rank: "#",
      results_col_inst: "Institution",
      results_col_prog: "Programme",
      results_col_region: "Region",
      results_col_cap: "Capacity",
      results_col_pts: "Points",
      results_col_conf: "Confidence",
      results_col_type: "Type",
      results_col_actions: "Actions",
      results_direct: "Direct",
      results_borderline: "Borderline / parallel",
      results_detail_btn: "Details",
      results_detail_title: "Programme",
      results_quick_all: "All",
      results_quick_health: "Health",
      results_quick_econ: "Economics",
      results_quick_law: "Law",
      reco_loading: "Matching against the TCU guidebook — please wait…",
      reco_success_line: "Fetched successfully",
      necta_loading: "Fetching from NECTA / TETEA…",
      necta_success_line: "Loaded successfully",
      sam_intro:
        "Hi — I'm SAM (Smart Admission Mate). I can help with: fetching NECTA/TETEA results into your form, understanding TCU-based programme recommendations, browsing the institution & programme directory, HESLB / loan guidance, and general questions about how this system works. Type your question below.",
      land_meta_heading: "System stats",
      land_meta_prog: "Programmes loaded",
      land_meta_inst: "Institutions",
      land_meta_intro_en:
        "Here is what this guide is wired to right now — live counts from the TCU programme catalog loaded on this server.",
    },
  };

  function getUiLang() {
    return document.body.getAttribute("data-ui-lang") === "en" ? "en" : "sw";
  }

  function applyI18n() {
    var lang = getUiLang();
    var pack = I18N[lang] || I18N.sw;
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      var k = el.getAttribute("data-i18n");
      if (k && pack[k] != null) el.textContent = pack[k];
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach(function (el) {
      var k = el.getAttribute("data-i18n-placeholder");
      if (k && pack[k] != null) el.setAttribute("placeholder", pack[k]);
    });
    document.documentElement.lang = lang === "en" ? "en" : "sw";
  }

  function setUiLang(lang) {
    document.body.setAttribute("data-ui-lang", lang === "en" ? "en" : "sw");
    localStorage.setItem("mwongozo-ui-lang", lang === "en" ? "en" : "sw");
    document.querySelectorAll("[data-set-lang]").forEach(function (btn) {
      btn.classList.toggle("is-active", btn.getAttribute("data-set-lang") === (lang === "en" ? "en" : "sw"));
    });
    applyI18n();
    updateHeroCaption();
    if (resultsEl && resultsEl.querySelector(".results-bundle")) {
      try {
        renderResultsPageTable();
      } catch (_e) {}
    }
  }

  function updateHeroCaption() {
    var cap = document.getElementById("heroSlideCaption");
    var slide = document.querySelector(".hero-slide.is-active");
    if (!cap || !slide) return;
    var lang = getUiLang();
    var t =
      lang === "en"
        ? slide.getAttribute("data-caption-en") || slide.getAttribute("data-caption-sw") || ""
        : slide.getAttribute("data-caption-sw") || "";
    cap.textContent = t;
  }

  function initHeroSlideshow() {
    var root = document.querySelector(".hero-slideshow");
    if (!root) return;
    var slides = root.querySelectorAll(".hero-slide");
    var dotsWrap = root.querySelector(".hero-slideshow__dots");
    if (!slides.length || !dotsWrap) return;
    dotsWrap.innerHTML = "";
    var idx = 0;
    slides.forEach(function (_s, i) {
      var b = document.createElement("button");
      b.type = "button";
      b.setAttribute("aria-label", "Slide " + (i + 1));
      b.addEventListener("click", function () {
        go(i);
      });
      dotsWrap.appendChild(b);
    });
    var dotBtns = dotsWrap.querySelectorAll("button");
    function go(i) {
      idx = (i + slides.length) % slides.length;
      slides.forEach(function (s, j) {
        s.classList.toggle("is-active", j === idx);
      });
      dotBtns.forEach(function (d, j) {
        d.classList.toggle("is-active", j === idx);
      });
      updateHeroCaption();
    }
    go(0);
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!reduce) {
      setInterval(function () {
        go(idx + 1);
      }, 7000);
    }
  }

  function initFabChatDock() {
    var fab = document.getElementById("fabChat");
    var dock = document.getElementById("chatDock");
    var closeBtn = document.getElementById("chatDockClose");
    var sendBtn = document.getElementById("chatDockSend");
    var input = document.getElementById("chatDockInput");
    var log = document.getElementById("chatDockMessages");
    if (!fab || !dock) return;
    function pushDock(role, text) {
      if (!log) return;
      var d = document.createElement("div");
      d.className = "chat-bubble chat-bubble--" + role;
      d.textContent = text;
      log.appendChild(d);
      log.scrollTop = log.scrollHeight;
    }
    function openDock() {
      dock.classList.add("is-open");
      dock.setAttribute("aria-hidden", "false");
      fab.setAttribute("aria-expanded", "true");
      if (!sessionStorage.getItem("mwongozo-sam-intro") && log) {
        sessionStorage.setItem("mwongozo-sam-intro", "1");
        var pack = I18N[getUiLang()] || I18N.sw;
        pushDock("bot", pack.sam_intro);
      }
    }
    function closeDock() {
      dock.classList.remove("is-open");
      dock.setAttribute("aria-hidden", "true");
      fab.setAttribute("aria-expanded", "false");
    }
    fab.addEventListener("click", function () {
      if (dock.classList.contains("is-open")) closeDock();
      else openDock();
    });
    if (closeBtn) closeBtn.addEventListener("click", closeDock);
    if (sendBtn && input) {
      sendBtn.addEventListener("click", function () {
        var t = input.value.trim();
        if (!t) return;
        pushDock("user", t);
        input.value = "";
        var lower = t.toLowerCase();
        var reply =
          getUiLang() === "en"
            ? "Thanks for reaching out. Use the results form and NECTA fetch for accurate data; this chat gives general guidance only."
            : "Asante kwa kuwasiliana. Tumia fomu ya matokeo na upakiaji wa NECTA kwa data sahihi; mazungumzo haya ni mwongozo wa jumla tu.";
        if (lower.indexOf("tcu") !== -1)
          reply =
            getUiLang() === "en"
              ? "TCU publishes the Guidebook and admission standards for universities in Tanzania."
              : "TCU inachapisha Guidebook na viwango vya kujiunga vyuo nchini.";
        if (lower.indexOf("heslb") !== -1 || lower.indexOf("mkopo") !== -1)
          reply =
            getUiLang() === "en"
              ? "HESLB handles higher-education loans — check OLAS windows and matching names on NIDA."
              : "HESLB inashughulikia mikopo — angalia dirisha la OLAS na majina yanayolingana na NIDA.";
        setTimeout(function () {
          pushDock("bot", reply);
        }, 280);
      });
      input.addEventListener("keydown", function (e) {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          sendBtn.click();
        }
      });
    }
  }

  function toast(message, variant, durationMs) {
    variant = variant || "info";
    durationMs = typeof durationMs === "number" ? durationMs : 4200;
    if (!toastRoot) return;
    var el = document.createElement("div");
    el.className = "toast toast--" + variant;
    el.setAttribute("role", "status");
    if (variant === "success") {
      el.innerHTML =
        '<span class="toast__icon" aria-hidden="true"><i class="fa-solid fa-check"></i></span><span class="toast__text"></span>';
      el.querySelector(".toast__text").textContent = message;
    } else {
      el.textContent = message;
    }
    toastRoot.appendChild(el);
    requestAnimationFrame(function () {
      el.classList.add("toast--show");
    });
    setTimeout(function () {
      el.classList.remove("toast--show");
      setTimeout(function () {
        el.remove();
      }, 380);
    }, durationMs);
  }

  function openModal(title, html) {
    if (!modalRoot) return;
    modalRoot.innerHTML =
      '<div class="modal-backdrop" role="presentation"></div>' +
      '<div class="modal-panel" role="dialog" aria-modal="true" aria-labelledby="mw-modal-title">' +
      '<div class="modal-head"><h2 id="mw-modal-title" class="modal-title"></h2><button type="button" class="btn btn-ghost btn-icon" id="mwModalClose" aria-label="Funga">&times;</button></div>' +
      '<div class="modal-body" id="mwModalBody"></div></div>';
    modalRoot.querySelector(".modal-title").textContent = title;
    modalRoot.querySelector("#mwModalBody").innerHTML = html;
    modalRoot.classList.add("is-open");
    function close() {
      modalRoot.classList.remove("is-open");
      modalRoot.innerHTML = "";
      document.removeEventListener("keydown", onKey);
    }
    function onKey(e) {
      if (e.key === "Escape") close();
    }
    modalRoot.querySelector("#mwModalClose").addEventListener("click", close);
    modalRoot.querySelector(".modal-backdrop").addEventListener("click", close);
    document.addEventListener("keydown", onKey);
  }

  function runStageTransition(updateDom) {
    if (typeof document.startViewTransition === "function") {
      document.startViewTransition(function () {
        updateDom();
      });
    } else {
      updateDom();
    }
  }

  function enterApp() {
    runStageTransition(function () {
      if (landingView) landingView.classList.add("hidden");
      if (dashboardShell) dashboardShell.classList.remove("hidden");
      navigateDash("input");
      localStorage.setItem("mwongozo-entered", "1");
    });
  }

  function goToLanding() {
    runStageTransition(function () {
      if (mainWrapInner) mainWrapInner.classList.remove("wrap-inner--reco-focus");
      if (dashboardShell) dashboardShell.classList.remove("dashboard--results-mode");
      if (dashboardShell) dashboardShell.classList.add("hidden");
      if (landingView) landingView.classList.remove("hidden");
      window.scrollTo(0, 0);
      initLandingMetaAnimation();
    });
  }

  function navigateDash(panel) {
    var showPanel = "main";
    if (panel === "home") showPanel = "home";
    else if (panel === "directory") showPanel = "directory";
    else if (panel === "loan") showPanel = "loan";
    else if (panel === "assistant") showPanel = "assistant";
    else if (panel === "news") showPanel = "news";
    else showPanel = "main";
    document.querySelectorAll("[data-panel]").forEach(function (p) {
      p.classList.toggle("hidden", p.getAttribute("data-panel") !== showPanel);
    });
    document.querySelectorAll("[data-dash-nav]").forEach(function (btn) {
      btn.classList.toggle("is-active", btn.getAttribute("data-dash-nav") === panel);
    });
    if (panel === "input") showInputView();
    if (panel === "results") showResultsView();
    if (panel === "directory" && directoryBody && !directoryBody.dataset.loaded) loadDirectoryData();
    if (panel === "home") loadMetaSummary();
  }

  var landMetaAnimSeq = 0;

  function loadMetaSummary() {
    if (!metaStatsEl) return;
    if (typeof MwongozoApi === "undefined") return;
    MwongozoApi.fetchJson("/meta", { method: "GET" })
      .then(function (m) {
        metaStatsEl.innerHTML =
          '<div class="stat-card glass"><span class="stat-value">' +
          (m.programmes_loaded || "—") +
          '</span><span class="stat-label">Programme zilizopakiwa</span></div>' +
          '<div class="stat-card glass"><span class="stat-value">' +
          (m.institutions_covered && m.institutions_covered.length) +
          '</span><span class="stat-label">Taasisi</span></div>';
      })
      .catch(function () {
        metaStatsEl.innerHTML =
          '<p class="muted small">Haiwezi kupakia takwimu sasa. Jaribu tena baadaye.</p>';
      });
  }

  function animateCountTo(el, target, ms) {
    if (!el) return;
    target = Math.max(0, Math.floor(Number(target) || 0));
    var start = performance.now();
    function frame(t) {
      var u = Math.min(1, (t - start) / ms);
      var eased = 1 - (1 - u) * (1 - u);
      el.textContent = String(Math.round(target * eased));
      if (u < 1) requestAnimationFrame(frame);
      else el.textContent = String(target);
    }
    requestAnimationFrame(frame);
  }

  function runTypewriter(el, fullText, msPerChar, mySeq, done) {
    if (!el) return;
    el.textContent = "";
    var i = 0;
    var tid = setInterval(function () {
      if (mySeq !== landMetaAnimSeq) {
        clearInterval(tid);
        return;
      }
      i += 1;
      el.textContent = fullText.slice(0, i);
      if (i >= fullText.length) {
        clearInterval(tid);
        if (typeof done === "function") done();
      }
    }, msPerChar);
  }

  function initLandingMetaAnimation() {
    var twEl = document.getElementById("landMetaTypewriter");
    var nPro = document.getElementById("landMetaProgs");
    var nInst = document.getElementById("landMetaInst");
    if (!twEl || !nPro || !nInst) return;
    var mySeq = ++landMetaAnimSeq;
    applyI18n();
    var pack = I18N[getUiLang()] || I18N.sw;
    var intro = getUiLang() === "en" ? pack.land_meta_intro_en : pack.land_meta_intro_sw;
    if (!intro) intro = pack.land_meta_intro_en || "";
    nPro.textContent = "0";
    nInst.textContent = "0";
    twEl.textContent = "";
    runTypewriter(twEl, intro, 26, mySeq, function () {
      if (mySeq !== landMetaAnimSeq) return;
      function applyMeta(m) {
        if (mySeq !== landMetaAnimSeq) return;
        var p = Number(m.programmes_loaded) || 0;
        var ins = Array.isArray(m.institutions_covered) ? m.institutions_covered.length : 0;
        animateCountTo(nPro, p, 900);
        animateCountTo(nInst, ins, 900);
      }
      if (typeof MwongozoApi !== "undefined") {
        MwongozoApi.fetchJson("/meta", { method: "GET" }).then(applyMeta).catch(function () {});
      } else {
        fetch("/meta")
          .then(function (r) {
            return r.json();
          })
          .then(applyMeta)
          .catch(function () {});
      }
    });
  }

  function loadDirectoryData() {
    if (!directoryBody || typeof MwongozoApi === "undefined") return;
    directoryBody.innerHTML =
      '<tr><td colspan="5" class="muted">Inapakia orodha ya programme…</td></tr>';
    Promise.all([
      MwongozoApi.fetchJson("/programmes", { method: "GET" }).catch(function () {
        return [];
      }),
      MwongozoApi.fetchJson("/institutions", { method: "GET" }).catch(function () {
        return [];
      }),
    ]).then(function (pair) {
      var programmes = pair[0] || [];
      var insts = pair[1] || [];
      institutionsByCode = {};
      insts.forEach(function (i) {
        institutionsByCode[i.code] = i;
      });
      directoryRows = Array.isArray(programmes) ? programmes : [];
      directoryBody.dataset.loaded = "1";
      if (!directoryRows.length) {
        directoryBody.innerHTML =
          '<tr><td colspan="5" class="muted">Hakuna data — angalia muunganisho wa server.</td></tr>';
        toast("Orodha ya programme haipatikani kwa sasa", "warn");
        return;
      }
      populateDirectoryFilters();
      renderDirectoryTable();
      toast("Orodha ya programme imepakuliwa", "success");
    });
  }

  function populateDirectoryFilters() {
    if (!directoryRegion || !directoryInstitution) return;
    var regions = [
      ...new Set(directoryRows.map(function (r) {
        return r.region;
      }).filter(Boolean)),
    ].sort();
    var instCodes = [
      ...new Set(directoryRows.map(function (r) {
        return r.institution_code;
      }).filter(Boolean)),
    ].sort();
    var regHtml =
      '<option value="all">Mkoa wote</option>' +
      regions
        .map(function (r) {
          return '<option value="' + escapeHtmlAttr(r) + '">' + escapeHtml(r) + "</option>";
        })
        .join("");
    var instHtml =
      '<option value="all">Chuo chote</option>' +
      instCodes
        .map(function (c) {
          var name = (institutionsByCode[c] && institutionsByCode[c].name) || c;
          return '<option value="' + escapeHtmlAttr(c) + '">' + escapeHtml(name) + "</option>";
        })
        .join("");
    directoryRegion.innerHTML = regHtml;
    directoryInstitution.innerHTML = instHtml;
  }

  function filteredDirectoryRows() {
    var q = (directorySearch && directorySearch.value.trim().toLowerCase()) || "";
    var reg = (directoryRegion && directoryRegion.value) || "all";
    var inst = (directoryInstitution && directoryInstitution.value) || "all";
    return directoryRows.filter(function (r) {
      var hay = [
        r.name,
        r.code,
        r.institution_name,
        r.region,
        r.category,
        r.award_level,
      ]
        .join(" ")
        .toLowerCase();
      var okQ = !q || hay.indexOf(q) !== -1;
      var okR = reg === "all" || String(r.region) === reg;
      var okI = inst === "all" || String(r.institution_code) === inst;
      return okQ && okR && okI;
    });
  }

  function renderDirectoryTable() {
    if (!directoryBody) return;
    var rows = filteredDirectoryRows();
    if (!rows.length) {
      directoryBody.innerHTML =
        '<tr><td colspan="5" class="muted">Hakuna matokeo ya kuchujwa.</td></tr>';
      return;
    }
    directoryBody.innerHTML = rows
      .map(function (p) {
        var minp = p.minimum_points != null ? p.minimum_points : "—";
        var code = p.code || "";
        return (
          "<tr class=\"dir-row\" tabindex=\"0\" data-programme-code=\"" +
          escapeHtmlAttr(code) +
          "\">" +
          "<td><strong>" +
          escapeHtml(p.institution_name || "") +
          "</strong><div class=\"small muted\">" +
          escapeHtml(p.institution_code || "") +
          "</div></td>" +
          "<td>" +
          escapeHtml(p.name || "") +
          "</td>" +
          "<td><span class=\"badge\">" +
          escapeHtml(String(p.category || "")) +
          "</span></td>" +
          "<td>" +
          escapeHtml(String(p.region || "")) +
          "</td>" +
          "<td>" +
          escapeHtml(String(minp)) +
          "</td>" +
          "</tr>"
        );
      })
      .join("");
    directoryBody.querySelectorAll(".dir-row").forEach(function (tr) {
      function showDetail() {
        var code = tr.getAttribute("data-programme-code") || "";
        var p = directoryRows.find(function (r) {
          return (r.code || "") === code;
        }) || {};
        var links =
          (p.apply_url &&
            '<p><a class="btn btn-primary" href="' +
            escapeHtmlAttr(p.apply_url) +
            '" target="_blank" rel="noopener">Maombi / tovuti</a></p>') ||
          "";
        openModal(p.name || "Programme", "<div class=\"small muted\">" + escapeHtml(p.code || "") + "</div>" +
          "<p>" +
          escapeHtml(p.institution_name || "") +
          " · " +
          escapeHtml(String(p.region || "")) +
          "</p>" +
          "<ul class=\"modal-list\"><li><strong>Award:</strong> " +
          escapeHtml(String(p.award_level || "")) +
          "</li><li><strong>Duration:</strong> " +
          escapeHtml(String(p.duration_years != null ? p.duration_years : "—")) +
          " miaka</li><li><strong>Min points:</strong> " +
          escapeHtml(String(p.minimum_points != null ? p.minimum_points : "—")) +
          "</li><li><strong>Tier:</strong> " +
          escapeHtml(String(p.competition_tier || "—")) +
          "</li></ul>" +
          links);
      }
      tr.addEventListener("click", showDetail);
      tr.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          showDetail();
        }
      });
    });
  }

  var NECTA_LOOKUP_YEAR_MAX = 2025;
  var NECTA_CSEE_YEAR_MIN = 2003;
  var NECTA_ACSEE_YEAR_MIN = 2005;

  function refreshNectaYearSelect(pathway) {
    if (!nectaExamYear) return;
    var previous = parseInt(nectaExamYear.value, 10);
    nectaExamYear.innerHTML = "";
    var yMin;
    var yMax = NECTA_LOOKUP_YEAR_MAX;
    if (pathway === "o_level") yMin = NECTA_CSEE_YEAR_MIN;
    else if (pathway === "a_level") yMin = NECTA_ACSEE_YEAR_MIN;
    else return;
    for (var y = yMax; y >= yMin; y--) {
      var opt = document.createElement("option");
      opt.value = String(y);
      opt.textContent = String(y);
      nectaExamYear.appendChild(opt);
    }
    var keep = Number.isFinite(previous) && previous >= yMin && previous <= yMax ? previous : yMax;
    nectaExamYear.value = String(keep);
  }

  async function fetchNectaOfficialResults() {
    if (!nectaFetchBtn || !nectaLookupMsg) return;
    var pathway = pathwayInput.value;
    if (!pathway || (pathway !== "o_level" && pathway !== "a_level")) {
      nectaLookupMsg.innerHTML = '<div class="warning">Chagua Form 4 au Form 6 kwanza.</div>';
      toast("Chagua level kwanza", "warn");
      return;
    }
    var year = parseInt(nectaExamYear.value, 10);
    var candidate = nectaIndexNo.value.trim();
    if (!candidate) {
      nectaLookupMsg.innerHTML = '<div class="warning">Weka nambari ya mtihani (CNO).</div>';
      return;
    }
    var L = I18N[getUiLang()] || I18N.sw;
    nectaLookupMsg.innerHTML =
      '<div class="necta-fetch-state necta-fetch-state--loading" role="status"><span class="reco-loading__track reco-loading__track--inline" aria-hidden="true"><span class="reco-loading__bar"></span></span> <span>' +
      escapeHtml(L.necta_loading) +
      "</span></div>";
    nectaFetchBtn.disabled = true;
    try {
      var isCsee = pathway === "o_level";
      var url = "/student/results/lookup";
      var body = {
        exam_type: isCsee ? "csee" : "acsee",
        year: year,
        candidate_number: candidate,
        skip_cache: false,
      };
      var response = await (MwongozoApi
        ? MwongozoApi.fetchWithTimeout(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
          })
        : fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
          }));
      var data = await response.json().catch(function () {
        return {};
      });
      if (!response.ok) throw new Error(MwongozoApi ? MwongozoApi.formatApiError(data) : data.detail || "Request failed");
      var input = data.student_input;
      if (!input) throw new Error("Majibu ya server hayajafanana na matarajio.");
      populateFromPayload(input);
      var rec = data.record || {};
      if (isCsee && rec.division) {
        var div = String(rec.division).toUpperCase();
        var allowed = ["I", "II", "III", "IV"];
        if (allowed.indexOf(div) !== -1) document.getElementById("division").value = div;
      }
      var school = rec.school_name || "";
      var cno = rec.candidate_number || candidate.toUpperCase();
      var divLine = rec.division ? " · Division " + rec.division : "";
      var cp = data.calculated_points || {};
      var ptsNum = isCsee ? cp.total_grade_points : cp.principal_points;
      var ptsLabel = isCsee ? "jumla alama (O-Level)" : "TCU points (makadirio)";
      var pts = typeof ptsNum === "number" ? " · " + ptsLabel + ": " + ptsNum : "";
      var src = rec.data_source ? " · Chanzo: " + rec.data_source : "";
      var L2 = I18N[getUiLang()] || I18N.sw;
      var tick =
        '<span class="necta-success-tick" aria-hidden="true"><i class="fa-solid fa-check"></i></span> ';
      nectaLookupMsg.innerHTML =
        '<div class="necta-fetch-state necta-fetch-state--done success">' +
        tick +
        "<strong>" +
        escapeHtml(L2.necta_success_line) +
        ".</strong> " +
        (school ? school + " · " : "") +
        cno +
        divLine +
        pts +
        src +
        "</div>";
      if (formRecommendStatus) {
        formRecommendStatus.innerHTML =
          '<div class="success small">Masomo yamejazwa kwenye fomu. Unaweza kuondoa au kubadilisha safu; kisha bonyeza <strong>Pata Recommendations</strong>.</div>';
      }
      var targetSection = pathway === "o_level" ? oLevelSection : aLevelSection;
      if (targetSection) targetSection.scrollIntoView({ behavior: "auto", block: "start" });
      toast("Matokeo yamepakuliwa kutoka NECTA/TETEA", "success");
    } catch (err) {
      nectaLookupMsg.innerHTML =
        '<div class="error">' + escapeHtml(err.message || "Imeshindikana") + "</div>";
      toast(err.message || "Hitilafu ya NECTA", "error");
    } finally {
      if (nectaFetchBtn) nectaFetchBtn.disabled = false;
    }
  }

  function setTheme(theme) {
    var nextTheme = theme === "light" ? "light" : "dark";
    document.body.dataset.theme = nextTheme;
    localStorage.setItem("mwongozo-theme", nextTheme);
    var label = nextTheme === "light" ? "Dark mode" : "Light mode";
    themeLabels.forEach(function (el) {
      el.textContent = label;
    });
  }

  function showInputView() {
    if (inputView) inputView.classList.remove("hidden");
    if (resultsView) resultsView.classList.add("hidden");
    if (mainWrapInner) mainWrapInner.classList.remove("wrap-inner--reco-focus");
    if (dashboardShell) dashboardShell.classList.remove("dashboard--results-mode");
    window.scrollTo(0, 0);
  }

  function showResultsView() {
    if (inputView) inputView.classList.add("hidden");
    if (resultsView) resultsView.classList.remove("hidden");
    if (mainWrapInner) mainWrapInner.classList.add("wrap-inner--reco-focus");
    if (dashboardShell) dashboardShell.classList.add("dashboard--results-mode");
    window.scrollTo(0, 0);
  }

  function escapeHtmlAttr(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function subjectRow(preset, level) {
    preset = preset || {};
    level = level || "a";
    var catalog = level === "o" ? oLevelSubjectsCatalog : subjectCatalog;
    var want = (preset.subject || "").trim();
    var inCatalog = want && catalog.indexOf(want) !== -1;
    var subjectOptions = catalog
      .map(function (s) {
        return (
          '<option value="' +
          escapeHtmlAttr(s) +
          '" ' +
          (want === s ? "selected" : "") +
          ">" +
          escapeHtml(s) +
          "</option>"
        );
      })
      .join("");
    if (want && !inCatalog) {
      var label = want + " (kutoka matokeo)";
      subjectOptions =
        '<option value="' +
        escapeHtmlAttr(want) +
        '" selected>' +
        escapeHtml(label) +
        "</option>" +
        subjectOptions;
    }
    var grades = gradeOptions.slice();
    var g = (preset.grade || "").trim();
    if (g && grades.indexOf(g) === -1) grades = grades.concat([g]);
    var gradeHtml = grades
      .map(function (opt) {
        return (
          '<option value="' +
          escapeHtmlAttr(opt) +
          '" ' +
          (g === opt ? "selected" : "") +
          ">" +
          (opt === "" ? "--" : escapeHtml(opt)) +
          "</option>"
        );
      })
      .join("");
    var principalVal = preset.principal === false ? "0" : "1";
    var elective = preset.model === "elective" || preset.principal === false;
    var wrapper = document.createElement("div");
    wrapper.className = "subject-row" + (want && !inCatalog ? " subject-row--extra" : "");
    wrapper.dataset.principal = principalVal;
    wrapper.innerHTML =
      '<select class="subject-name">' +
      subjectOptions +
      '</select><select class="subject-grade">' +
      gradeHtml +
      '</select><select class="subject-model"><option value="core" ' +
      (!elective ? "selected" : "") +
      '>Core</option><option value="elective" ' +
      (elective ? "selected" : "") +
      '>Elective</option></select><button type="button" class="btn btn-danger remove-btn">Ondoa</button>';
    wrapper.querySelector(".remove-btn").addEventListener("click", function () {
      wrapper.remove();
    });
    return wrapper;
  }

  var combinationMap = {
    PCB: ["Physics", "Chemistry", "Biology"],
    PCM: ["Physics", "Chemistry", "Advanced Mathematics"],
    PGM: ["Physics", "Geography", "Advanced Mathematics"],
    CBG: ["Chemistry", "Biology", "Geography"],
    CBN: ["Chemistry", "Biology", "Nutrition"],
    HGE: ["History", "Geography", "Economics"],
    ECA: ["Economics", "Commerce", "Accountancy"],
    CBE: ["Commerce", "Book Keeping", "Economics"],
    HGL: ["History", "Geography", "English Language"],
    HKL: ["History", "Kiswahili", "English Language"],
    HGK: ["History", "Geography", "Kiswahili"],
  };

  function setAlevelByCombination(code) {
    var selected = combinationMap[code] || [];
    aLevelContainer.innerHTML = "";
    var list = selected.length ? selected : ["Physics", "Chemistry", "Biology"];
    list.forEach(function (subject, index) {
      aLevelContainer.appendChild(
        subjectRow({ subject: subject, grade: index === 0 ? "A" : "B", model: "core" }, "a")
      );
    });
  }

  function ensureDefaultRows() {
    if (!aLevelContainer.children.length) {
      setAlevelByCombination(combinationInput.value || "PCB");
    }
    if (!oLevelContainer.children.length) {
      defaultOLevelSubjects.forEach(function (subject) {
        oLevelContainer.appendChild(subjectRow({ subject: subject, grade: "", model: "core" }, "o"));
      });
    }
  }

  function setPathway(pathway) {
    pathwayInput.value = pathway;
    levelPrompt.classList.add("hidden");
    aLevelSection.classList.add("hidden");
    oLevelSection.classList.add("hidden");
    pathwayButtons.forEach(function (btn) {
      btn.classList.remove("is-active");
    });
    var active = Array.prototype.find.call(pathwayButtons, function (btn) {
      return btn.dataset.pathwayButton === pathway;
    });
    if (active) active.classList.add("is-active");
    if (nectaLookupWrap) {
      nectaLookupWrap.classList.remove("hidden");
      nectaLookupMsg.innerHTML = "";
      if (pathway === "o_level") {
        nectaIndexHint.textContent =
          "Form 4 (CSEE): weka nambari ya mwanafunzi kama S1027-0034 (kituo + nambari).";
        nectaIndexNo.placeholder = "S1027-0034";
      } else if (pathway === "a_level") {
        nectaIndexHint.textContent =
          "Form 6 (ACSEE): weka nambari ya mwanafunzi kama S0140-0538 (kituo + nambari).";
        nectaIndexNo.placeholder = "S0140-0538";
      }
    }
    if (pathway === "a_level") aLevelSection.classList.remove("hidden");
    if (pathway === "o_level") {
      oLevelSection.classList.remove("hidden");
      if (!oLevelContainer.children.length) ensureDefaultRows();
    }
    refreshNectaYearSelect(pathway);
  }

  function populateFromPayload(payload) {
    var pathway = payload.pathway || "a_level";
    setPathway(pathway);
    document.getElementById("a_level_scheme").value = payload.a_level_scheme || "2016_plus";
    document.getElementById("combination").value = payload.combination || "";
    document.getElementById("language").value = payload.language || "both";
    document.getElementById("o_language").value = payload.language || "both";
    document.getElementById("division").value = "";
    document.getElementById("result_model").value = "standard";
    aLevelContainer.innerHTML = "";
    oLevelContainer.innerHTML = "";
    (payload.a_level_subjects || []).forEach(function (item) {
      aLevelContainer.appendChild(subjectRow(item, "a"));
    });
    (payload.o_level_subjects || []).forEach(function (item) {
      oLevelContainer.appendChild(subjectRow(item, "o"));
    });
    if (pathway === "a_level" && !aLevelContainer.children.length) {
      setAlevelByCombination(combinationInput.value || "PCB");
    }
    if (pathway === "o_level" && !oLevelContainer.children.length) {
      defaultOLevelSubjects.forEach(function (subject) {
        oLevelContainer.appendChild(subjectRow({ subject: subject, grade: "", model: "core" }, "o"));
      });
    }
  }

  function buildPayload() {
    var pathway = pathwayInput.value || "a_level";
    function readSubjects(container, level) {
      return Array.from(container.querySelectorAll(".subject-row")).map(function (row) {
        return {
          subject: row.querySelector(".subject-name").value,
          grade: row.querySelector(".subject-grade").value,
          principal: row.dataset.principal !== "0",
          level: level,
        };
      });
    }
    return {
      pathway: pathway,
      a_level_scheme: document.getElementById("a_level_scheme").value,
      a_level_subjects: pathway === "a_level" ? readSubjects(aLevelContainer, "a_level") : [],
      o_level_subjects: pathway === "o_level" ? readSubjects(oLevelContainer, "o_level") : [],
      combination: document.getElementById("combination").value || null,
      preferred_regions: [],
      preferred_institutions: [],
      language:
        pathway === "a_level"
          ? document.getElementById("language").value
          : document.getElementById("o_language").value,
      equivalent_qualification: null,
      notes:
        pathway === "o_level"
          ? [
              "Division: " + (document.getElementById("division").value || ""),
              "Result model: " + (document.getElementById("result_model").value || ""),
            ]
          : [],
    };
  }

  function confidenceBandClass(band) {
    var value = String(band || "")
      .trim()
      .toLowerCase();
    if (value === "high") return "confidence-high";
    if (value === "medium") return "confidence-medium";
    if (value === "low") return "confidence-low";
    return "confidence-very-low";
  }

  function renderResultsCompareRows(a, b) {
    var aReview = Boolean(a.__isReview);
    var bReview = Boolean(b.__isReview);
    var aConfidence = Number(a.assessment && a.assessment.confidence != null ? a.assessment.confidence : 0);
    var bConfidence = Number(b.assessment && b.assessment.confidence != null ? b.assessment.confidence : 0);
    var aScore = Number(a.assessment && a.assessment.score != null ? a.assessment.score : 0);
    var bScore = Number(b.assessment && b.assessment.score != null ? b.assessment.score : 0);
    var aPoints = Number(a.assessment && a.assessment.rule_points != null ? a.assessment.rule_points : 0);
    var bPoints = Number(b.assessment && b.assessment.rule_points != null ? b.assessment.rule_points : 0);
    var confidenceDirection =
      String((resultsPagination.filters && resultsPagination.filters.sort) || "confidence_desc") ===
      "confidence_asc"
        ? 1
        : -1;
    return (
      confidenceDirection * (aConfidence - bConfidence) ||
      (aReview - bReview) ||
      bScore - aScore ||
      bPoints - aPoints ||
      Number(a.rank != null ? a.rank : 0) - Number(b.rank != null ? b.rank : 0)
    );
  }

  function renderResultsApplyFilters() {
    var query = String((resultsPagination.filters && resultsPagination.filters.query) || "")
      .trim()
      .toLowerCase();
    var region = String((resultsPagination.filters && resultsPagination.filters.region) || "all")
      .trim()
      .toLowerCase();
    var category = String((resultsPagination.filters && resultsPagination.filters.category) || "all")
      .trim()
      .toLowerCase();
    function isEconomicsCourse(rec) {
      var categoryName = String((rec.programme && rec.programme.category) || "").toLowerCase();
      var courseName = String((rec.programme && rec.programme.name) || "").toLowerCase();
      var tags = ((rec.programme && rec.programme.tags) || []).map(function (tag) {
        return String(tag).toLowerCase();
      });
      return (
        categoryName === "accounting_finance" ||
        courseName.indexOf("economics") !== -1 ||
        courseName.indexOf("finance") !== -1 ||
        courseName.indexOf("banking") !== -1 ||
        tags.some(function (tag) {
          return ["economics", "finance", "banking"].indexOf(tag) !== -1;
        })
      );
    }
    return (resultsPagination.items || []).filter(function (rec) {
      var haystack = [
        rec.programme && rec.programme.institution_name,
        rec.programme && rec.programme.name,
        rec.programme && rec.programme.city,
        rec.programme && rec.programme.region,
        rec.programme && rec.programme.category,
        ...((rec.programme && rec.programme.tags) || []),
        rec.assessment && rec.assessment.why_recommended && rec.assessment.why_recommended[0],
        rec.assessment && rec.assessment.why_borderline && rec.assessment.why_borderline[0],
      ]
        .map(function (value) {
          return String(value || "").toLowerCase();
        })
        .join(" ");
      var matchesQuery = !query || haystack.indexOf(query) !== -1;
      var matchesRegion =
        region === "all" ||
        String((rec.programme && rec.programme.region) || "").toLowerCase() === region;
      var matchesCategory =
        category === "all" ||
        (category === "economics"
          ? isEconomicsCourse(rec)
          : String((rec.programme && rec.programme.category) || "").toLowerCase() === category);
      return matchesQuery && matchesRegion && matchesCategory;
    });
  }

  function buildRecommendLoadingHTML() {
    var L = I18N[getUiLang()] || I18N.sw;
    return (
      '<div class="reco-loading glass" role="status">' +
      '<div class="reco-loading__track" aria-hidden="true"><div class="reco-loading__bar"></div></div>' +
      '<p class="reco-loading__text">' +
      escapeHtml(L.reco_loading) +
      "</p></div>"
    );
  }

  function buildRecDetailHTML(rec) {
    var isReview = Boolean(rec.__isReview);
    var L = I18N[getUiLang()] || I18N.sw;
    var applyUrl = rec.institution_apply_url || rec.institution_website || "";
    var applyLabel = rec.institution_apply_url
      ? rec.cta_label || "Apply Now"
      : rec.institution_website
        ? "Visit Website"
        : rec.cta_label || "Apply Now";
    var explanation = []
      .concat(rec.assessment && rec.assessment.why_recommended ? rec.assessment.why_recommended : [])
      .concat(rec.assessment && rec.assessment.why_borderline ? rec.assessment.why_borderline : [])
      .concat(rec.assessment && rec.assessment.why_not_matched ? rec.assessment.why_not_matched : []);
    var parallel = ((rec.assessment && rec.assessment.parallel_courses) || []).slice(0, 8);
    var ruleTraces = ((rec.assessment && rec.assessment.rule_traces) || []).slice(0, 12);
    var loc = [rec.programme && rec.programme.city, rec.programme && rec.programme.region].filter(Boolean).join(", ");
    var cap =
      rec.programme && rec.programme.capacity != null && rec.programme.capacity !== ""
        ? String(rec.programme.capacity)
        : "—";
    return (
      '<p class="muted small">' +
      escapeHtml((rec.programme && rec.programme.institution_name) + " · " + (rec.programme && rec.programme.name)) +
      "</p>" +
      '<p class="small"><strong>' +
      escapeHtml(L.results_col_cap) +
      ":</strong> " +
      escapeHtml(cap) +
      " · <strong>" +
      escapeHtml(L.results_col_pts) +
      ":</strong> " +
      escapeHtml(String(rec.student_points)) +
      "/" +
      escapeHtml(String(rec.minimum_required_points)) +
      " · <strong>" +
      escapeHtml(L.results_col_type) +
      ":</strong> " +
      escapeHtml(isReview ? L.results_borderline : L.results_direct) +
      "</p>" +
      (loc ? '<p class="small muted">' + escapeHtml(loc) + "</p>" : "") +
      (applyUrl
        ? '<p><a class="btn btn-primary" href="' +
          escapeHtmlAttr(applyUrl) +
          '" target="_blank" rel="noopener noreferrer">' +
          escapeHtml(applyLabel) +
          "</a></p>"
        : "") +
      '<div class="footer-note"><div><strong>' +
      L.results_why +
      ":</strong></div><ul>" +
      (explanation
        .map(function (item) {
          return "<li>" + escapeHtml(item) + "</li>";
        })
        .join("") || "<li>—</li>") +
      '</ul><div><strong>' +
      L.results_parallel +
      ":</strong></div><ul>" +
      (parallel
        .map(function (item) {
          return "<li>" + escapeHtml(item) + "</li>";
        })
        .join("") || "<li>—</li>") +
      '</ul><div><strong>' +
      L.results_rules +
      ":</strong></div><ul>" +
      (ruleTraces
        .map(function (trace) {
          return (
            "<li>" +
            (trace.passed ? "✓" : "✗") +
            " " +
            escapeHtml(trace.label) +
            " (" +
            trace.points +
            ")" +
            "</li>"
          );
        })
        .join("") || "<li>—</li>") +
      "</ul></div>"
    );
  }

  function buildRecommendationTableRowHTML(rec, fidx) {
    var isReview = Boolean(rec.__isReview);
    var L = I18N[getUiLang()] || I18N.sw;
    var applyUrl = rec.institution_apply_url || rec.institution_website || "";
    var conf = Number(rec.assessment && rec.assessment.confidence != null ? rec.assessment.confidence : 0);
    var barW = Math.min(100, Math.max(4, conf)) + "%";
    var typeLabel = isReview ? L.results_borderline : L.results_direct;
    var matchClass = isReview ? "rec-row--review" : "rec-row--direct";
    var applyBtn = applyUrl
      ? '<a class="btn btn-secondary btn-sm rec-apply-link" href="' +
        escapeHtmlAttr(applyUrl) +
        '" target="_blank" rel="noopener noreferrer" title="' +
        escapeHtmlAttr(applyUrl) +
        '"><i class="fa-solid fa-arrow-up-right-from-square" aria-hidden="true"></i></a> '
      : "";
    return (
      '<tr class="rec-row ' +
      matchClass +
      '" data-match="' +
      (isReview ? "review" : "direct") +
      '">' +
      '<td class="rec-td-num">' +
      escapeHtml(String(rec.rank != null ? rec.rank : "—")) +
      "</td>" +
      "<td>" +
      escapeHtml((rec.programme && rec.programme.institution_name) || "") +
      '</td><td class="rec-td-prog"><strong>' +
      escapeHtml((rec.programme && rec.programme.name) || "") +
      '</strong></td><td>' +
      escapeHtml((rec.programme && rec.programme.region) || "—") +
      "</td><td>" +
      escapeHtml(String(rec.student_points)) +
      " / " +
      escapeHtml(String(rec.minimum_required_points)) +
      '</td><td class="rec-td-conf"><div class="rec-mini-bar" title="' +
      escapeHtmlAttr(L.results_conf + " " + conf + "%") +
      '"><span style="width:' +
      barW +
      '"></span></div><span class="rec-conf-meta">' +
      escapeHtml(String(rec.assessment.confidence) + "% · " + String(rec.assessment.confidence_band)) +
      '</span></td><td><span class="rec-pill">' +
      escapeHtml(typeLabel) +
      '</span></td><td class="rec-td-actions">' +
      applyBtn +
      '<button type="button" class="btn btn-secondary btn-sm" data-rec-detail="' +
      fidx +
      '">' +
      escapeHtml(L.results_detail_btn) +
      "</button></td></tr>"
    );
  }

  function renderCombinationPanel(items) {
    if (!items || !items.length) return "";
    return (
      '<div class="combo-grid layout-block">' +
      items
        .map(function (item) {
          return (
            '<div class="combo-card glass"><div class="combo-title"><span>' +
            escapeHtml(item.code) +
            '</span><span class="combo-code">' +
            Math.round((item.confidence || 0) * 100) +
            "%</span></div><div class=\"combo-soft\">" +
            escapeHtml((item.subjects || []).join(" + ")) +
            '</div><div class="combo-soft"><strong>Likely sections:</strong> ' +
            escapeHtml((item.likely_sections || []).join(", ") || "General") +
            '</div><div class="combo-soft">' +
            escapeHtml((item.rationale || []).join(" ")) +
            "</div></div>"
          );
        })
        .join("") +
      "</div>"
    );
  }

  function renderResultsPageTable() {
    var filteredItems = renderResultsApplyFilters().sort(renderResultsCompareRows);
    resultsPagination._filteredSorted = filteredItems;
    var pageSize = resultsPagination.pageSize || 16;
    var totalPages = Math.max(1, Math.ceil(filteredItems.length / pageSize));
    resultsPagination.page = Math.min(Math.max(resultsPagination.page, 0), totalPages - 1);
    var start = resultsPagination.page * pageSize;
    var pageItems = filteredItems.slice(start, start + pageSize);
    var regions = [
      ...new Set(
        (resultsPagination.items || [])
          .map(function (item) {
            return item.programme && item.programme.region;
          })
          .filter(Boolean)
      ),
    ].sort();
    var categories = [
      ...new Set(
        (resultsPagination.items || [])
          .map(function (item) {
            return item.programme && item.programme.category;
          })
          .filter(Boolean)
      ),
    ].sort();
    var f = resultsPagination.filters || {};
    var L = I18N[getUiLang()] || I18N.sw;
    var allRegionsOpt =
      '<option value="all">' + (getUiLang() === "en" ? "All regions" : "Mkoa wote") + "</option>" +
      regions
        .map(function (region) {
          return (
            '<option value="' +
            escapeHtmlAttr(region) +
            '" ' +
            (String(f.region || "all").toLowerCase() === String(region).toLowerCase() ? "selected" : "") +
            ">" +
            escapeHtml(region) +
            "</option>"
          );
        })
        .join("");
    var allCatOpt =
      '<option value="all">' + (getUiLang() === "en" ? "All categories" : "Category zote") + "</option>" +
      categories
        .map(function (category) {
          return (
            '<option value="' +
            escapeHtmlAttr(category) +
            '" ' +
            (String(f.category || "all").toLowerCase() === String(category).toLowerCase() ? "selected" : "") +
            ">" +
            escapeHtml(category) +
            "</option>"
          );
        })
        .join("");
    var thead =
      "<thead><tr>" +
      "<th>" +
      escapeHtml(L.results_col_rank) +
      "</th><th>" +
      escapeHtml(L.results_col_inst) +
      "</th><th>" +
      escapeHtml(L.results_col_prog) +
      "</th><th>" +
      escapeHtml(L.results_col_region) +
      "</th><th>" +
      escapeHtml(L.results_col_pts) +
      "</th><th>" +
      escapeHtml(L.results_col_conf) +
      "</th><th>" +
      escapeHtml(L.results_col_type) +
      "</th><th>" +
      escapeHtml(L.results_col_actions) +
      "</th></tr></thead>";
    var tbody =
      "<tbody>" +
      pageItems
        .map(function (rec, i) {
          return buildRecommendationTableRowHTML(rec, start + i);
        })
        .join("") +
      "</tbody>";
    resultsEl.innerHTML =
      '<div class="results-bundle glass results-bundle--table">' +
      '<div class="results-sticky-toolbar">' +
      '<div class="field"><label for="resultsRegionFilter">' +
      escapeHtml(L.results_mkoa) +
      '</label><select id="resultsRegionFilter">' +
      allRegionsOpt +
      '</select></div><div class="field"><label for="resultsCategoryFilter">' +
      escapeHtml(L.results_cat) +
      '</label><select id="resultsCategoryFilter">' +
      allCatOpt +
      '</select></div><div class="field"><label for="resultsSortFilter">' +
      escapeHtml(L.results_conf) +
      '</label><select id="resultsSortFilter">' +
      '<option value="confidence_desc" ' +
      ((f.sort || "confidence_desc") === "confidence_desc" ? "selected" : "") +
      ">" +
      (getUiLang() === "en" ? "High → low" : "Juu → chini") +
      '</option><option value="confidence_asc" ' +
      ((f.sort || "confidence_desc") === "confidence_asc" ? "selected" : "") +
      ">" +
      (getUiLang() === "en" ? "Low → high" : "Chini → juu") +
      "</option></select></div></div>" +
      '<div class="results-toolbar-row2">' +
      '<input id="resultsSearch" type="search" placeholder="' +
      escapeHtmlAttr(L.results_search_ph) +
      '" value="' +
      escapeHtmlAttr(f.query || "") +
      '" style="flex:1;min-width:160px;max-width:420px;" />' +
      '<button type="button" class="btn btn-secondary" data-quick-category="all">' +
      escapeHtml(L.results_quick_all) +
      '</button><button type="button" class="btn btn-secondary" data-quick-category="health">' +
      escapeHtml(L.results_quick_health) +
      '</button><button type="button" class="btn btn-secondary" data-quick-category="economics">' +
      escapeHtml(L.results_quick_econ) +
      '</button><button type="button" class="btn btn-secondary" data-quick-category="law">' +
      escapeHtml(L.results_quick_law) +
      "</button></div>" +
      '<div class="results-viewport results-viewport--table"><table class="rec-table">' +
      thead +
      tbody +
      '</table></div><div class="pagination-bar">' +
      '<div class="pagination-meta">Page ' +
      (resultsPagination.page + 1) +
      " / " +
      totalPages +
      " · " +
      pageItems.length +
      " / " +
      filteredItems.length +
      '</div><div class="pagination-controls">' +
      '<button type="button" class="btn btn-secondary" id="prevResultsPage" ' +
      (resultsPagination.page <= 0 ? "disabled" : "") +
      '>‹</button>' +
      '<button type="button" class="btn btn-secondary" id="nextResultsPage" ' +
      (resultsPagination.page >= totalPages - 1 ? "disabled" : "") +
      '>›</button></div></div></div>';

    var searchInput = document.getElementById("resultsSearch");
    var regionFilter = document.getElementById("resultsRegionFilter");
    var categoryFilter = document.getElementById("resultsCategoryFilter");
    var sortFilter = document.getElementById("resultsSortFilter");
    var quickCategoryButtons = document.querySelectorAll("[data-quick-category]");
    var prevButton = document.getElementById("prevResultsPage");
    var nextButton = document.getElementById("nextResultsPage");
    if (searchInput) {
      searchInput.addEventListener("input", function () {
        resultsPagination.filters.query = searchInput.value;
        resultsPagination.page = 0;
        renderResultsPageTable();
      });
    }
    if (regionFilter) {
      regionFilter.addEventListener("change", function () {
        resultsPagination.filters.region = regionFilter.value;
        resultsPagination.page = 0;
        renderResultsPageTable();
      });
    }
    if (categoryFilter) {
      categoryFilter.addEventListener("change", function () {
        resultsPagination.filters.category = categoryFilter.value;
        resultsPagination.page = 0;
        renderResultsPageTable();
      });
    }
    if (sortFilter) {
      sortFilter.addEventListener("change", function () {
        resultsPagination.filters.sort = sortFilter.value;
        resultsPagination.page = 0;
        renderResultsPageTable();
      });
    }
    if (prevButton) {
      prevButton.addEventListener("click", function () {
        resultsPagination.page -= 1;
        renderResultsPageTable();
      });
    }
    if (nextButton) {
      nextButton.addEventListener("click", function () {
        resultsPagination.page += 1;
        renderResultsPageTable();
      });
    }
    quickCategoryButtons.forEach(function (button) {
      button.addEventListener("click", function () {
        resultsPagination.filters.category = button.dataset.quickCategory || "all";
        if (categoryFilter) categoryFilter.value = resultsPagination.filters.category;
        resultsPagination.page = 0;
        renderResultsPageTable();
      });
    });
  }

  function renderRecommendations(data) {
    var recommendations = (data.recommendations || []).map(function (rec) {
      return Object.assign({}, rec, { __isReview: false });
    });
    var reviewCandidates = (data.review_candidates || []).map(function (rec) {
      return Object.assign({}, rec, { __isReview: true });
    });
    var allRows = recommendations.concat(reviewCandidates).sort(renderResultsCompareRows);
    resultsPagination.items = allRows;
    resultsPagination.page = 0;
    resultsPagination.directCount = recommendations.length;
    resultsPagination.reviewCount = reviewCandidates.length;
    resultsPagination.filters = { query: "", region: "all", category: "all", sort: "confidence_desc" };
    showResultsView();
    navigateDash("results");
    var comboHtml = renderCombinationPanel(data.combination_suggestions);
    if (!allRows.length) {
      resultSummaryEl.innerHTML = "";
      resultsEl.innerHTML =
        '<div class="results-bundle glass results-bundle--table"><div class="error layout-block">Hakuna programme iliyo eligible kwa input hii.</div>' +
        comboHtml +
        '<p class="footer-note muted small">Jaribu combination nyingine au angalia strict requirements.</p></div>';
      toast("Hakuna programme zilizo eligible", "warn");
      return;
    }
    resultSummaryEl.innerHTML = "";
    renderResultsPageTable();
    var Ldone = I18N[getUiLang()] || I18N.sw;
    toast(Ldone.reco_success_line, "success", 5200);
  }

  function pushChat(role, text) {
    if (!chatMessages) return;
    var wrap = document.createElement("div");
    wrap.className = "chat-bubble chat-bubble--" + role;
    wrap.textContent = text;
    chatMessages.appendChild(wrap);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function handleChatSend() {
    if (!chatInput) return;
    var t = chatInput.value.trim();
    if (!t) return;
    pushChat("user", t);
    chatInput.value = "";
    var lower = t.toLowerCase();
    var reply =
      "Ninaelewa swali lako. Kwa sasa msaada huu ni wa maelezo ya jumla: tumia fomu ya matokeo, thibitisha combination, kisha bonyeza **Pata Recommendations**. Kwa NECTA, tumia mwaka na CNO halisi.";
    if (lower.indexOf("necta") !== -1 || lower.indexOf("nambari") !== -1) {
      reply =
        "Kupakia matokeo: chagua Form 4 au Form 6, weka mwaka na nambari ya mtihani (CNO), kisha **Pakua matokeo kutoka NECTA**. Mfumo hutumia NECTA au TETEA kulingana na mwaka.";
    }
    if (lower.indexOf("heslb") !== -1 || lower.indexOf("mkopo") !== -1) {
      reply =
        "Mkopo: hakikisha majina yanalingana na NIDA, angalia deadline za HESLB, na pakua nyaraka wazi. Sehemu ya **Mkopo & HESLB** ina muhtasari zaidi.";
    }
    setTimeout(function () {
      pushChat("bot", reply);
    }, 320);
  }

  document.getElementById("recommendForm").addEventListener("submit", async function (event) {
    event.preventDefault();
    if (formRecommendStatus) formRecommendStatus.innerHTML = "";
    resultSummaryEl.innerHTML = "";
    resultsEl.innerHTML = buildRecommendLoadingHTML();
    showResultsView();
    navigateDash("results");
    try {
      var payload = buildPayload();
      var response = await (MwongozoApi
        ? MwongozoApi.fetchWithTimeout("/recommend", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          })
        : fetch("/recommend", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          }));
      var data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Request failed");
      renderRecommendations(data);
    } catch (error) {
      resultsEl.innerHTML = '<div class="error layout-block">' + escapeHtml(error.message) + "</div>";
      resultSummaryEl.innerHTML = '<div class="error">' + escapeHtml(error.message) + "</div>";
      toast(error.message || "Hitilafu", "error");
    }
  });

  pathwayButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      setPathway(button.dataset.pathwayButton);
    });
  });
  if (nectaFetchBtn) nectaFetchBtn.addEventListener("click", fetchNectaOfficialResults);
  document.querySelector('[data-add-subject="a"]').addEventListener("click", function () {
    aLevelContainer.appendChild(subjectRow({}, "a"));
  });
  document.querySelector('[data-add-subject="o"]').addEventListener("click", function () {
    oLevelContainer.appendChild(subjectRow({}, "o"));
  });
  document.getElementById("combination").addEventListener("change", function () {
    if (pathwayInput.value === "a_level" && combinationInput.value) setAlevelByCombination(combinationInput.value);
  });
  document.getElementById("loadExample").addEventListener("click", function () {
    populateFromPayload(samplePayload);
    toast("Mfano umejazwa", "success");
  });
  document.getElementById("clearForm").addEventListener("click", function () {
    aLevelContainer.innerHTML = "";
    oLevelContainer.innerHTML = "";
    document.getElementById("a_level_scheme").value = "2016_plus";
    document.getElementById("combination").value = "";
    document.getElementById("language").value = "english";
    document.getElementById("o_language").value = "english";
    document.getElementById("division").value = "";
    document.getElementById("result_model").value = "standard";
    pathwayInput.value = "";
    levelPrompt.classList.remove("hidden");
    aLevelSection.classList.add("hidden");
    oLevelSection.classList.add("hidden");
    pathwayButtons.forEach(function (btn) {
      btn.classList.remove("is-active");
    });
    if (nectaLookupWrap) nectaLookupWrap.classList.add("hidden");
    if (nectaLookupMsg) nectaLookupMsg.innerHTML = "";
    if (nectaIndexNo) nectaIndexNo.value = "";
    if (nectaExamYear) nectaExamYear.innerHTML = "";
    if (formRecommendStatus) formRecommendStatus.innerHTML = "";
    resultSummaryEl.innerHTML = '<div class="muted">Form imeclear. Chagua level kisha ujaze matokeo.</div>';
    resultsEl.innerHTML = "";
    showInputView();
    navigateDash("input");
    toast("Fomu imefutwa", "info");
  });
  themeToggles.forEach(function (btn) {
    btn.addEventListener("click", function () {
      setTheme(document.body.dataset.theme === "light" ? "dark" : "light");
    });
  });
  var backButton = document.getElementById("backToInput");
  if (backButton) {
    backButton.addEventListener("click", function () {
      showInputView();
      navigateDash("input");
    });
  }

  document.querySelectorAll("[data-go-landing]").forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      goToLanding();
    });
  });

  document.querySelectorAll("[data-dash-nav]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      navigateDash(btn.getAttribute("data-dash-nav"));
    });
  });
  var enterBtns = document.querySelectorAll("[data-enter-app]");
  enterBtns.forEach(function (b) {
    b.addEventListener("click", enterApp);
  });
  /* Landing: onyesha kila mara isipokuwa ?app=1. ?panel=… (pamoja na app=1) kwa troubleshooting. */
  var bootParams = new URLSearchParams(location.search);
  var skipLanding = bootParams.get("app") === "1";
  var bootPanel = (bootParams.get("panel") || "").trim().toLowerCase();
  var ALLOW_BOOT_PANEL = {
    home: 1,
    input: 1,
    results: 1,
    directory: 1,
    loan: 1,
    assistant: 1,
    news: 1,
  };
  if (skipLanding) enterApp();

  if (directorySearch)
    directorySearch.addEventListener("input", function () {
      renderDirectoryTable();
    });
  if (directoryRegion)
    directoryRegion.addEventListener("change", function () {
      renderDirectoryTable();
    });
  if (directoryInstitution)
    directoryInstitution.addEventListener("change", function () {
      renderDirectoryTable();
    });

  if (chatSend) chatSend.addEventListener("click", handleChatSend);
  if (chatInput)
    chatInput.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleChatSend();
      }
    });

  document.querySelectorAll("[data-demo-auth]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      toast(
        getUiLang() === "en"
          ? "Sign-in is UI demo only — no backend authentication yet."
          : "Ingia / sajili: demo ya UI pekee — hakuna authentication kwenye backend bado.",
        "info"
      );
    });
  });

  document.querySelectorAll("[data-set-lang]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      setUiLang(btn.getAttribute("data-set-lang") || "sw");
      if (landingView && !landingView.classList.contains("hidden")) {
        try {
          initLandingMetaAnimation();
        } catch (_e) {}
      }
    });
  });

  document.getElementById("recommendForm").reset();
  aLevelContainer.innerHTML = "";
  oLevelContainer.innerHTML = "";
  levelPrompt.classList.remove("hidden");
  setTheme(localStorage.getItem("mwongozo-theme") || "dark");
  if (!skipLanding) {
    showInputView();
  } else {
    showInputView();
    navigateDash("input");
    if (bootPanel && ALLOW_BOOT_PANEL[bootPanel]) {
      navigateDash(bootPanel);
    }
  }
  initHeroSlideshow();
  if (!skipLanding) {
    try {
      initLandingMetaAnimation();
    } catch (_e) {}
  }
  var savedLang = localStorage.getItem("mwongozo-ui-lang");
  if (savedLang === "en" || savedLang === "sw") setUiLang(savedLang);
  else {
    applyI18n();
    updateHeroCaption();
  }
  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-rec-detail]");
    if (!btn || !resultsEl || !resultsEl.contains(btn)) return;
    var idx = parseInt(btn.getAttribute("data-rec-detail"), 10);
    var list = resultsPagination._filteredSorted;
    if (!Number.isFinite(idx) || !list || !list[idx]) return;
    var rec = list[idx];
    var Lm = I18N[getUiLang()] || I18N.sw;
    openModal(Lm.results_detail_title + " · " + ((rec.programme && rec.programme.name) || ""), buildRecDetailHTML(rec));
  });

  initFabChatDock();
})();
