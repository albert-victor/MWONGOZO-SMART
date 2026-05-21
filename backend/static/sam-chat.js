/**
 * SAM — rule-based assistant for MWONGOZO SMART (no external LLM).
 * Full product context, Kiswahili/English FAQs, typing indicator, greeting replies.
 */
(function (global) {
  "use strict";

  var SYSTEM_CONTEXT = {
    name_sw: "MWONGOZO SMART",
    name_en: "MWONGOZO SMART",
    role_sw:
      "Mfumo wa mwongozo wa kujiunga vyuo nchini Tanzania: matokeo (NECTA), mapendekezo kulingana na Mwongozo wa TCU, orodha ya vyuo, na mwongozo wa mkopo HESLB.",
    role_en:
      "Tanzania university admission guide: NECTA results, TCU guidebook-based recommendations, institution directory, and HESLB loan guidance.",
    apis: [
      "GET / — ukurasa wa nyumbani",
      "GET /health — hali ya mfumo",
      "GET /meta — idadi ya programme na vyuo",
      "POST /recommend — mapendekezo kutoka matokeo",
      "POST /student/results/lookup — CSEE/ACSEE kutoka NECTA au TETEA",
      "POST /student/results/recommend — lookup + mapendekezo",
      "GET /institutions — orodha ya vyuo",
      "POST /loan/track — fuatilia mkopo (demo)",
    ],
    data_sw:
      "Programme ~558, vyuo ~65, SQLite cache kwa matokeo yaliyotafutwa awali, Mwongozo TCU 2025/2026.",
    data_en: "~558 programmes, ~65 institutions, SQLite cache for past exam lookups, TCU 2025/2026 guidebook.",
    limits_sw:
      "Si tovuti rasmi ya TCU/NECTA/HESLB. Akaunti na OLAS halisi ni demo. Mapendekezo ni mwongozo wa eligibility, si uhakika wa kuchaguliwa.",
    limits_en:
      "Not the official TCU/NECTA/HESLB site. Login and OLAS tracking are demo. Recommendations are eligibility guidance, not admission guarantees.",
  };

  var TOPICS = [
    {
      id: "start",
      icon: "fa-rocket",
      chip_sw: "Jinsi ya kuanza?",
      chip_en: "How to start?",
      title_sw: "Jinsi ya kuanza",
      title_en: "How to get started",
      keywords: ["anza", "start", "begin", "karibu", "kuanza", "hatua"],
      answer_sw:
        "1) Fungua **Matokeo** → chagua Form 4 (CSEE) au Form 6 (ACSEE).\n2) Pakua matokeo kutoka **NECTA** au jaza alama kwa mkono.\n3) Bofya **Pata Recommendations**.\n4) Kwa mkopo: **Mkopo & HESLB** → Mwongozo.\n5) Kwa vyuo: **Vyuo & programme** (orodha ya kuchunguza).",
      answer_en:
        "1) Open **Results** → Form 4 (CSEE) or Form 6 (ACSEE).\n2) **Fetch NECTA** or enter grades manually.\n3) Click **Get Recommendations**.\n4) Loans: **Loan & HESLB** → Guidance.\n5) Browse: **Universities & programmes**.",
    },
    {
      id: "greeting",
      chip_sw: "SAM ni nani?",
      chip_en: "Who is SAM?",
      title_sw: "SAM ni nani",
      title_en: "Who is SAM",
      keywords: ["sam", "msaidizi", "bot", "nani", "who"],
      answer_sw:
        "Mimi ni **SAM** (Smart Admission Mate) — msaidizi wa ndani wa **MWONGOZO SMART**. Ninajibu kuhusu NECTA, TCU, mapendekezo, vyuo, na HESLB kwa mujibu wa mfumo huu — si ChatGPT wa nje.",
      answer_en:
        "I'm **SAM** (Smart Admission Mate), the in-app guide for **MWONGOZO SMART**. I explain NECTA, TCU, recommendations, universities, and HESLB based on this system — not an external AI.",
    },
    {
      id: "necta",
      chip_sw: "Jinsi ya pakua NECTA?",
      chip_en: "Fetch NECTA how?",
      title_sw: "Kupakia matokeo NECTA",
      title_en: "Loading NECTA results",
      keywords: ["necta", "cno", "nambari", "index", "tetea", "matokeo", "pakua", "form 4", "form 6"],
      answer_sw:
        "Chagua **Form 4** au **Form 6**, weka **mwaka** halisi, kisha **nambari ya mtihani** (mf. S0123/0027/2024). Bofya **Pakua matokeo kutoka NECTA**. Mfumo hutumia NECTA online (miaka mipya) au **TETEA** (miaka ya zamani). Matokeo yaliyotafutwa hifadhiwa kwenye cache — ukishapakia mara moja, yanapatikana hata mtandao ukichelewa.",
      answer_en:
        "Pick **Form 4** or **Form 6**, enter the correct **year**, then **index number** (e.g. S0123/0027/2024). Click **Fetch from NECTA**. Uses NECTA online (recent years) or **TETEA** (archive). Past lookups are **cached** for offline fallback.",
    },
    {
      id: "necta-format",
      chip_sw: "Muundo wa nambari NECTA",
      chip_en: "NECTA number format",
      title_sw: "Nambari ya mtihani (CNO)",
      title_en: "Exam index number",
      keywords: ["muundo", "format", "s0140", "namba", "cno", "index"],
      answer_sw:
        "Muundo: **KITUO/NAMBA/MWAKA** — mfano `S0140/0012/2024` au `S0140-0012`. Kituo ni herufi + namba (S0140), namba ya mtihani ndani ya shule, mwaka wa mtihani.",
      answer_en:
        "Format: **CENTRE/NUMBER/YEAR** — e.g. `S0140/0012/2024`. Centre code + candidate serial + exam year.",
    },
    {
      id: "recommend",
      chip_sw: "Mapendekezo yanafanyaje?",
      chip_en: "How recommendations work?",
      title_sw: "Mapendekezo ya programu",
      title_en: "Programme recommendations",
      keywords: ["recommend", "programme", "eligible", "tcu", "alama", "points", "pata"],
      answer_sw:
        "Backend inachambua matokeo dhidi ya **Mwongozo wa TCU**: kwanza **kanuni za eligibility** (masomo, alama, combination), kisha **upangaji**. Unapata programme zilizokidhi na zile za borderline. Si uhakika wa kuchaguliwa — ni mwongozo.",
      answer_en:
        "The engine checks **TCU guidebook rules** (subjects, points, combination) then **ranks** matches. You see eligible and borderline programmes. This is guidance, not a guarantee of admission.",
    },
    {
      id: "combination",
      chip_sw: "Combination (PCM, HGK)",
      chip_en: "Combinations (PCM, HGK)",
      title_sw: "Combination na masomo",
      title_en: "Combination and subjects",
      keywords: ["combination", "pcm", "hgk", "pcb", "hgk", "masomo", "a-level"],
      answer_sw:
        "Kwa A-Level chagua combination (PCM, PCB, HGK, n.k.). Combination ya sanaa/humanities **haiwezi** kufungua baadhi ya programme za STEM/health — mfumo huonyesha hilo kwenye mapendekezo.",
      answer_en:
        "For A-Level pick your combination (PCM, PCB, HGK, etc.). Arts/humanities combos **block** some STEM/health routes — the engine reflects that in results.",
    },
    {
      id: "o-level",
      chip_sw: "Form 4 na degree",
      chip_en: "Form 4 and degree",
      title_sw: "O-Level na shahada",
      title_en: "O-Level and bachelor routes",
      keywords: ["form 4", "o-level", "csee", "degree", "bachelor", "shahada", "division"],
      answer_sw:
        "Kwa **CSEE (Form 4)**, mfumo hulinganisha zaidi njia za **certificate/diploma** — si kuingia moja kwa moja shahada kama A-Level. Angalia division na masomo kwenye fomu.",
      answer_en:
        "For **CSEE (Form 4)**, matching focuses on **certificate/diploma** pathways — not direct bachelor entry like A-Level. Check division and subjects on the form.",
    },
    {
      id: "directory",
      chip_sw: "Tofauti vyuo vs mapendekezo",
      chip_en: "Directory vs recommendations",
      title_sw: "Vyuo & programme",
      title_en: "University directory",
      keywords: ["chuo", "university", "directory", "vyuo", "orodha", "institution"],
      answer_sw:
        "**Vyuo & programme** = orodha ya kuchunguza (mkoa, umma/binafsi). **Mapendekezo** = kulingana na matokeo yako. API: `GET /institutions`.",
      answer_en:
        "**Universities & programmes** = browse list by region/ownership. **Recommendations** = based on your grades. API: `GET /institutions`.",
    },
    {
      id: "heslb",
      chip_sw: "Mkopo HESLB / OLAS",
      chip_en: "HESLB loan / OLAS",
      title_sw: "Mkopo wa HESLB",
      title_en: "HESLB loan",
      keywords: ["heslb", "mkopo", "olas", "loan", "nida", "rita", "batch"],
      answer_sw:
        "Fungua **Mkopo & HESLB** → **Mwongozo** (viungo rasmi: heslb.go.tz, OLAS, NIDA, RITA). **Fuatilia (demo)** si OLAS halisi — ni mfano tu. Thibitisha deadline kila mwaka kwenye tovuti ya HESLB.",
      answer_en:
        "Open **Loan & HESLB** → **Guidance** (official links). **Track (demo)** is not live OLAS. Always confirm deadlines on HESLB's site.",
    },
    {
      id: "names",
      chip_sw: "Majina na NIDA",
      chip_en: "Names and NIDA",
      title_sw: "Majina na vyeti",
      title_en: "Names and certificates",
      keywords: ["jina", "name", "nida", "rita", "nin", "cheti"],
      answer_sw:
        "Makosa ya kawaida: majina tofauti kwenye NIDA, RITA, na NECTA. Rekebisha **kabla** ya OLAS. NIN tarakimu 20.",
      answer_en:
        "Common issue: mismatched names on NIDA, RITA, and NECTA. Fix **before** OLAS. NIN is 20 digits.",
    },
    {
      id: "account",
      chip_sw: "Kuingia / akaunti",
      chip_en: "Login / account",
      title_sw: "Akaunti",
      title_en: "Account",
      keywords: ["ingia", "login", "account", "akaunti", "demo"],
      answer_sw:
        "Unaweza kutumia mfumo **bila kuingia**. Kitufe cha Ingia ni **demo ya UI** — hakuna akaunti halisi ya backend bado.",
      answer_en:
        "You can use the app **without logging in**. Login is a **UI demo** — no real backend accounts yet.",
    },
    {
      id: "errors",
      chip_sw: "NECTA haifanyi kazi",
      chip_en: "NECTA not working",
      title_sw: "Hitilafu / NECTA",
      title_en: "Errors / NECTA",
      keywords: ["error", "hitilafu", "fail", "mtandao", "offline", "cache"],
      answer_sw:
        "Angalia intaneti, mwaka na CNO. Jaribu tena baada ya dakika — matokeo yaliyopatikana hapo awali yanaweza kutoka **cache**. Onyesha upya ukurasa (Ctrl+Shift+R).",
      answer_en:
        "Check internet, year, and CNO. Retry later — previous successful lookups may load from **cache**. Hard refresh (Ctrl+Shift+R).",
    },
    {
      id: "official",
      chip_sw: "Viungo rasmi",
      chip_en: "Official links",
      title_sw: "Viungo rasmi",
      title_en: "Official links",
      keywords: ["rasmi", "official", "tovuti", "link", "necta.go", "tcu"],
      answer_sw:
        "NECTA: necta.go.tz · TCU: tcu.go.tz · HESLB: heslb.go.tz · OLAS: olas.heslb.go.tz · NIDA · RITA. MWONGOZO SMART haibadili sera zao.",
      answer_en:
        "NECTA, TCU, HESLB, OLAS, NIDA, RITA — use their official sites for binding decisions.",
    },
    {
      id: "tcu",
      chip_sw: "TCU Guidebook ni nini?",
      chip_en: "What is TCU Guidebook?",
      title_sw: "TCU Guidebook",
      title_en: "TCU Guidebook",
      keywords: ["tcu", "guidebook", "mwongozo", "viwango"],
      answer_sw:
        "**TCU** inachapisha Mwongozo wa Uchaguzi wa Vyuo. MWONGOZO SMART hutumia data ya programme na masharti kutoka mwongozo huo (2025/2026) — si badala ya portal rasmi ya TCU.",
      answer_en:
        "**TCU** publishes the university admission guidebook. This app uses programme requirements from that guide — not a replacement for TCU's official portal.",
    },
    {
      id: "points",
      chip_sw: "Alama za TCU (points)",
      chip_en: "TCU points",
      title_sw: "Alama za TCU",
      title_en: "TCU points",
      keywords: ["point", "alama", "principal", "gpa", "aggregate"],
      answer_sw:
        "A-Level: huhesabu **point** kutoka masomo kuu (kawaida hadi 3). O-Level: division na idadi ya masomo yaliyopita. Kila programme ina **minimum points** kwenye orodha.",
      answer_en:
        "A-Level: **points** from principal subjects (typically top 3). O-Level: passes and division. Each programme has a **minimum points** threshold.",
    },
    {
      id: "saved",
      chip_sw: "Kuhifadhi mapendekezo",
      chip_en: "Save recommendations",
      title_sw: "Kuhifadhi",
      title_en: "Saving",
      keywords: ["save", "hifadhi", "bookmark", "penda"],
      answer_sw:
        "Unaweza **kuhifadhi programme** kutoka jedwali la matokeo (hifadhi kwenye kivinjari chako). Angalia **Nyumbani** kwa shughuli za hivi karibuni.",
      answer_en:
        "You can **save programmes** from the results table (stored in your browser). Check **Home** for recent activity.",
    },
    {
      id: "language",
      chip_sw: "Lugha SW / EN",
      chip_en: "Language SW / EN",
      title_sw: "Lugha",
      title_en: "Language",
      keywords: ["lugha", "language", "english", "kiswahili", "sw", "en"],
      answer_sw:
        "Badilisha **SW / EN** juu ya ukurasa. SAM hujibu kwa lugha uliyochagua.",
      answer_en:
        "Switch **SW / EN** at the top. SAM replies in your selected language.",
    },
    {
      id: "privacy",
      chip_sw: "Faragha ya data",
      chip_en: "Data privacy",
      title_sw: "Faragha",
      title_en: "Privacy",
      keywords: ["faragha", "privacy", "data", "salama"],
      answer_sw:
        "Matokeo unayoweka hutumika kwa mapendekezo na cache ya lookup kwenye seva yako/mahali pa kutekeleza. Usishiriki nambari ya mtihani na watu usiowaamini.",
      answer_en:
        "Grades you enter are used for recommendations and local lookup cache on your deployment. Do not share index numbers with untrusted parties.",
    },
    {
      id: "api",
      chip_sw: "API za mfumo",
      chip_en: "System APIs",
      title_sw: "API za backend",
      title_en: "Backend APIs",
      keywords: ["api", "endpoint", "backend", "post", "get"],
      answer_sw:
        "Muhimu: `POST /recommend`, `POST /student/results/lookup`, `GET /meta`, `GET /institutions`, `POST /loan/track` (demo). Angalia `/docs` ikiwa FastAPI docs zimewashwa.",
      answer_en:
        "Key routes: `POST /recommend`, `POST /student/results/lookup`, `GET /meta`, `GET /institutions`, `POST /loan/track` (demo).",
    },
  ];

  var GREETINGS = [
    {
      test: function (t) {
        return /^(hujambo|habari|mambo|salama|shikamoo|jambo|niaje|sasa|uko je|habari yako)/i.test(t);
      },
      sw: "Hujambo! Mimi ni **SAM** — niko salama na tayari kukusaidia kuhusu NECTA, TCU, mapendekezo, vyuo, na HESLB. Una swali gani?",
      en: "Hello! I'm **SAM** — I'm here and ready to help with NECTA, TCU, recommendations, universities, and HESLB. What would you like to know?",
    },
    {
      test: function (t) {
        return /^(hi|hello|hey|good morning|good afternoon|good evening|how are you|how r u)/i.test(t);
      },
      sw: "Hello! I'm **SAM** — niko tayari (I'm ready). How can I help you with university admission in Tanzania today?",
      en: "Hi! I'm **SAM** — doing well and ready to help. Ask me about NECTA, TCU, programmes, or HESLB loans.",
    },
    {
      test: function (t) {
        return /(habari yako|how are you|hali gani|unaendeleaje|uko poa)/i.test(t);
      },
      sw: "Nzuri, asante! Mimi ni msaidizi wa kompyuta — sina hisia kama mtu, lakini mfumo unafanya kazi vizuri. Nikusaidieje kuhusu maombi ya chuo?",
      en: "I'm doing well, thanks! I'm a guided assistant — the system is running fine. How can I help with your admission steps?",
    },
    {
      test: function (t) {
        return /^(asante|thanks|thank you|nashukuru)/i.test(t);
      },
      sw: "Karibu sana! Ukiwa na swali lingine kuhusu matokeo, TCU, au mkopo, andika tu.",
      en: "You're welcome! Ask anytime about results, TCU, or loans.",
    },
    {
      test: function (t) {
        return /^(kwaheri|bye|goodbye|baadaye|see you)/i.test(t);
      },
      sw: "Kwaheri! Kila la heri na maombi yako ya elimu ya juu.",
      en: "Goodbye! Best of luck with your higher education applications.",
    },
  ];

  function lang() {
    return document.body && document.body.getAttribute("data-ui-lang") === "en" ? "en" : "sw";
  }

  function t(sw, en) {
    return lang() === "en" ? en : sw;
  }

  function escapeHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function formatAnswer(text) {
    return escapeHtml(text).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/\n/g, "<br />");
  }

  function packTopic(topic) {
    return {
      id: topic.id,
      title: lang() === "en" ? topic.title_en : topic.title_sw,
      chip: lang() === "en" ? topic.chip_en : topic.chip_sw,
      answer: lang() === "en" ? topic.answer_en : topic.answer_sw,
      keywords: topic.keywords || [],
    };
  }

  function matchGreeting(text) {
    var trimmed = String(text || "").trim().toLowerCase();
    if (!trimmed) return null;
    for (var i = 0; i < GREETINGS.length; i++) {
      if (GREETINGS[i].test(trimmed)) {
        return lang() === "en" ? GREETINGS[i].en : GREETINGS[i].sw;
      }
    }
    return null;
  }

  function matchTopic(text) {
    var lower = String(text || "").toLowerCase();
    var best = null;
    var bestScore = 0;
    TOPICS.forEach(function (topic) {
      var score = 0;
      (topic.keywords || []).forEach(function (kw) {
        if (lower.indexOf(kw) !== -1) score += 2;
      });
      var hay = (
        topic.title_sw +
        " " +
        topic.title_en +
        " " +
        (topic.chip_sw || "") +
        " " +
        (topic.chip_en || "")
      ).toLowerCase();
      if (hay.indexOf(lower) !== -1) score += 3;
      if (score > bestScore) {
        bestScore = score;
        best = topic;
      }
    });
    return bestScore > 0 ? best : null;
  }

  function composeReply(text, opts) {
    opts = opts || {};
    var greeting = matchGreeting(text);
    if (greeting) {
      return { html: formatAnswer(greeting), plain: greeting, kind: "greeting" };
    }
    var topic = opts.forceTopic || matchTopic(text);
    if (topic) {
      var p = packTopic(topic);
      return { html: formatAnswer(p.answer), plain: p.answer, kind: "topic", topicId: topic.id };
    }
    var lower = String(text || "").toLowerCase();
    if (lower.indexOf("mfumo") !== -1 || lower.indexOf("system") !== -1 || lower.indexOf("backend") !== -1) {
      var ctx =
        lang() === "en"
          ? "**" +
            SYSTEM_CONTEXT.name_en +
            "**: " +
            SYSTEM_CONTEXT.role_en +
            "\n\n**Data:** " +
            SYSTEM_CONTEXT.data_en +
            "\n\n**Note:** " +
            SYSTEM_CONTEXT.limits_en +
            "\n\n**APIs:** " +
            SYSTEM_CONTEXT.apis.join(", ")
          : "**" +
            SYSTEM_CONTEXT.name_sw +
            "**: " +
            SYSTEM_CONTEXT.role_sw +
            "\n\n**Data:** " +
            SYSTEM_CONTEXT.data_sw +
            "\n\n**Kumbuka:** " +
            SYSTEM_CONTEXT.limits_sw +
            "\n\n**API:** " +
            SYSTEM_CONTEXT.apis.join(", ");
      return { html: formatAnswer(ctx), plain: ctx, kind: "context" };
    }
    var fallback = t(
      "Samahani, sijaelewa kabisa. Chagua swali hapa chini, au jaribu maneno: **NECTA**, **TCU**, **combination**, **HESLB**, **vyuo**. Unaweza pia kuandika *hujambo*.",
      "I did not quite catch that. Tap a quick question below, or try: **NECTA**, **TCU**, **combination**, **HESLB**, **universities**. You can also say *hello*."
    );
    return { html: formatAnswer(fallback), plain: fallback, kind: "fallback" };
  }

  function typingDelayMs(text) {
    var len = String(text || "").length;
    return Math.min(1400, Math.max(420, 280 + len * 4));
  }

  var DOCK_FEATURED_IDS = ["start", "necta", "recommend", "heslb", "tcu"];

  function createMessenger(logEl, typingEl, scrollEl) {
    if (!logEl) {
      return {
        pushUser: function () {},
        showTyping: function () {},
        hideTyping: function () {},
        reply: function () {},
      };
    }

    var scrollTarget = scrollEl || logEl;

    function scroll() {
      if (!scrollTarget) return;
      scrollTarget.scrollTop = scrollTarget.scrollHeight;
    }

    function pushUser(text) {
      var wrap = document.createElement("div");
      wrap.className = "sam-msg sam-msg--user";
      wrap.innerHTML =
        '<div class="sam-msg__bubble">' +
        escapeHtml(text) +
        '</div><span class="sam-msg__meta">' +
        escapeHtml(t("Wewe", "You")) +
        "</span>";
      logEl.appendChild(wrap);
      scroll();
    }

    function showTyping() {
      if (!typingEl) return;
      typingEl.hidden = false;
      scroll();
    }

    function hideTyping() {
      if (!typingEl) return;
      typingEl.hidden = true;
    }

    function pushBotHtml(html) {
      hideTyping();
      var wrap = document.createElement("div");
      wrap.className = "sam-msg sam-msg--bot";
      wrap.innerHTML =
        '<div class="sam-msg__bubble">' +
        html +
        '</div><span class="sam-msg__meta">SAM · ' +
        escapeHtml(t("mwongozo", "guide")) +
        "</span>";
      logEl.appendChild(wrap);
      scroll();
    }

    function reply(text, opts, done) {
      opts = opts || {};
      var composed = composeReply(text, opts);
      showTyping();
      var delay = typingDelayMs(composed.plain);
      setTimeout(function () {
        pushBotHtml(composed.html);
        if (typeof done === "function") done(composed);
      }, delay);
    }

    function replyFromTopicId(topicId, done) {
      var topic = TOPICS.filter(function (x) {
        return x.id === topicId;
      })[0];
      if (!topic) return;
      pushUser(packTopic(topic).title);
      showTyping();
      var p = packTopic(topic);
      setTimeout(function () {
        pushBotHtml(formatAnswer(p.answer));
        if (typeof done === "function") done({ kind: "topic", topicId: topicId });
      }, typingDelayMs(p.answer));
    }

    return {
      pushUser: pushUser,
      showTyping: showTyping,
      hideTyping: hideTyping,
      pushBotHtml: pushBotHtml,
      reply: reply,
      replyFromTopicId: replyFromTopicId,
      scroll: scroll,
    };
  }

  function shortLabel(topic) {
    var p = packTopic(topic);
    var chip = p.chip || p.title;
    if (chip.length > 28) return chip.slice(0, 26) + "…";
    return chip;
  }

  function renderChips(container, onPick) {
    if (!container) return;
    container.innerHTML = "";
    var strip = document.createElement("div");
    strip.className = "sam-quick__strip";
    TOPICS.slice(0, 8).forEach(function (topic) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "sam-chip";
      btn.textContent = shortLabel(topic);
      btn.addEventListener("click", function () {
        if (typeof onPick === "function") onPick(topic.id, shortLabel(topic));
      });
      strip.appendChild(btn);
    });
    container.appendChild(strip);
  }

  function renderDockQuick(container, onPick) {
    if (!container) return;
    container.innerHTML = "";

    var strip = document.createElement("div");
    strip.className = "sam-quick__strip";
    strip.setAttribute("role", "group");
    strip.setAttribute("aria-label", t("Maswali ya haraka", "Quick questions"));

    DOCK_FEATURED_IDS.forEach(function (id) {
      var topic = TOPICS.filter(function (x) {
        return x.id === id;
      })[0];
      if (!topic) return;
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "sam-quick__btn";
      btn.textContent = shortLabel(topic);
      btn.addEventListener("click", function () {
        if (typeof onPick === "function") onPick(topic.id);
      });
      strip.appendChild(btn);
    });

    var moreBtn = document.createElement("button");
    moreBtn.type = "button";
    moreBtn.className = "sam-quick__btn sam-quick__btn--more";
    moreBtn.textContent = t("Zaidi", "More");
    moreBtn.setAttribute("aria-expanded", "false");

    var morePanel = document.createElement("div");
    morePanel.className = "sam-quick__more";

    TOPICS.forEach(function (topic) {
      if (DOCK_FEATURED_IDS.indexOf(topic.id) !== -1) return;
      var link = document.createElement("button");
      link.type = "button";
      link.className = "sam-quick__link";
      link.textContent = shortLabel(topic);
      link.addEventListener("click", function () {
        morePanel.classList.remove("is-open");
        moreBtn.classList.remove("is-open");
        moreBtn.setAttribute("aria-expanded", "false");
        if (typeof onPick === "function") onPick(topic.id);
      });
      morePanel.appendChild(link);
    });

    moreBtn.addEventListener("click", function () {
      var open = !morePanel.classList.contains("is-open");
      morePanel.classList.toggle("is-open", open);
      moreBtn.classList.toggle("is-open", open);
      moreBtn.setAttribute("aria-expanded", open ? "true" : "false");
    });

    container.appendChild(strip);
    container.appendChild(moreBtn);
    container.appendChild(morePanel);
  }

  function welcomeHtml() {
    return formatAnswer(
      t(
        "Hujambo! Mimi **SAM** — msaidizi wa MWONGOZO SMART. Uliza chochote kuhusu NECTA, TCU, mapendekezo, vyuo, au HESLB. Tumia vitufe hapa chini au andika ujumbe wako.",
        "Hi! I'm **SAM**, your MWONGOZO SMART guide. Ask about NECTA, TCU, recommendations, universities, or HESLB. Use the buttons below or type your message."
      )
    );
  }

  function initDock(options) {
    options = options || {};
    var fab = document.getElementById(options.fabId || "fabChat");
    var dock = document.getElementById(options.dockId || "chatDock");
    var closeBtn = document.getElementById(options.closeId || "chatDockClose");
    var sendBtn = document.getElementById(options.sendId || "chatDockSend");
    var input = document.getElementById(options.inputId || "chatDockInput");
    var log = document.getElementById(options.logId || "chatDockMessages");
    var quick = document.getElementById(options.quickId || "chatDockQuick");
    var typing = document.getElementById(options.typingId || "chatDockTyping");
    var body = dock.querySelector(".chat-dock__body");
    if (!fab || !dock) return null;

    var messenger = createMessenger(log, typing, body);
    var introKey = "mwongozo-sam-dock-v3";

    function onQuickPick(topicId) {
      messenger.replyFromTopicId(topicId);
      if (input) input.focus();
    }

    renderDockQuick(quick, onQuickPick);

    function openDock() {
      dock.classList.add("is-open");
      dock.setAttribute("aria-hidden", "false");
      fab.setAttribute("aria-expanded", "true");
      if (!sessionStorage.getItem(introKey) && log) {
        sessionStorage.setItem(introKey, "1");
        messenger.pushBotHtml(welcomeHtml());
      }
      if (input) input.focus();
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
    dock.querySelectorAll("[data-chat-close]").forEach(function (el) {
      el.addEventListener("click", closeDock);
    });

    function send() {
      if (!input) return;
      var text = input.value.trim();
      if (!text) return;
      messenger.pushUser(text);
      input.value = "";
      messenger.reply(text);
    }

    if (sendBtn) sendBtn.addEventListener("click", send);
    if (input) {
      input.addEventListener("keydown", function (e) {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          send();
        }
      });
    }

    return { messenger: messenger, open: openDock, close: closeDock };
  }

  global.SamChat = {
    SYSTEM_CONTEXT: SYSTEM_CONTEXT,
    TOPICS: TOPICS,
    lang: lang,
    t: t,
    formatAnswer: formatAnswer,
    packTopic: packTopic,
    composeReply: composeReply,
    matchTopic: matchTopic,
    createMessenger: createMessenger,
    renderChips: renderChips,
    renderDockQuick: renderDockQuick,
    welcomeHtml: welcomeHtml,
    initDock: initDock,
    getQuickQuestions: function () {
      return TOPICS.map(function (topic) {
        return packTopic(topic);
      });
    },
  };
})(typeof window !== "undefined" ? window : globalThis);
