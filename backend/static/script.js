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
  var homeOverviewStatsEl = document.getElementById("homeOverviewStats");
  var recentActivityListEl = document.getElementById("recentActivityList");
  var savedProgrammesListEl = document.getElementById("savedProgrammesList");
  var savedProgrammesPageListEl = document.getElementById("savedProgrammesPageList");
  var savedRecommendationsListEl = document.getElementById("savedRecommendationsList");
  var savedRecoCountEl = document.getElementById("savedRecoCount");
  var savedProgCountEl = document.getElementById("savedProgCount");
  var savedGuestGateEl = document.getElementById("savedGuestGate");
  var savedPageContentEl = document.getElementById("savedPageContent");
  var saveRecoRunBtn = document.getElementById("saveRecoRunBtn");
  var lastRecommendBundle = null;
  var savedRecommendationsCache = [];
  var lastRecommendInputSnapshot = null;
  var directoryBody = document.getElementById("directoryTableBody");
  var directorySearch = document.getElementById("directorySearch");
  var directoryRegion = document.getElementById("directoryRegion");
  var directoryInstitution = document.getElementById("directoryInstitution");
  var directoryOwnership = document.getElementById("directoryOwnership");
  var directoryCategory = document.getElementById("directoryCategory");
  var directoryAward = document.getElementById("directoryAward");
  var univGrid = document.getElementById("univGrid");
  var univSearch = document.getElementById("univSearch");
  var univRegion = document.getElementById("univRegion");
  var univOwnership = document.getElementById("univOwnership");
  var univKind = document.getElementById("univKind");
  var univResultCount = document.getElementById("univResultCount");
  var progResultCount = document.getElementById("progResultCount");
  var dirInstitutionsPanel = document.getElementById("dirInstitutionsPanel");
  var dirProgrammesPanel = document.getElementById("dirProgrammesPanel");
  var univModal = document.getElementById("univModal");
  var univModalTitle = document.getElementById("univModalTitle");
  var univModalMeta = document.getElementById("univModalMeta");
  var univModalBody = document.getElementById("univModalBody");
  var univModalPreview = document.getElementById("univModalPreview");
  var univModalSource = document.getElementById("univModalSource");
  var univModalProgBtn = document.getElementById("univModalProgBtn");
  var univModalWebLink = document.getElementById("univModalWebLink");
  var univModalInstCode = "";
  var univGridRenderTimer = null;
  var univGridDelegated = false;
  var chatMessages = document.getElementById("chatMessages");
  var chatInput = document.getElementById("chatInput");
  var chatSend = document.getElementById("chatSend");

  var directoryRows = [];
  var institutionList = [];
  var institutionsByCode = {};
  var directoryView = "institutions";
  var homeMeta = { programmes_loaded: 0, institutions_covered: [] };
  var themeAnimTimer = null;

  function readStoredJSON(key, fallback) {
    try {
      var raw = localStorage.getItem(key);
      if (!raw) return fallback;
      var parsed = JSON.parse(raw);
      return parsed == null ? fallback : parsed;
    } catch (_err) {
      return fallback;
    }
  }

  function writeStoredJSON(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (_err) {}
  }

  function apiFetch(url, options) {
    var opts = options || {};
    opts.credentials = "include";
    return fetch(url, opts);
  }

  function getExamContext() {
    try {
      var raw = sessionStorage.getItem("mwongozo-exam-context");
      return raw ? JSON.parse(raw) : null;
    } catch (_err) {
      return null;
    }
  }

  function setExamContext(ctx) {
    try {
      sessionStorage.setItem("mwongozo-exam-context", JSON.stringify(ctx || {}));
    } catch (_err) {}
  }

  function getSavedProgrammes() {
    var items = readStoredJSON("mwongozo-saved-programmes", []);
    return Array.isArray(items) ? items : [];
  }

  function setSavedProgrammes(items) {
    writeStoredJSON("mwongozo-saved-programmes", items);
  }

  function syncSavedProgrammesFromServer() {
    if (!isLoggedIn()) return Promise.resolve();
    return apiFetch("/auth/saved-programmes")
      .then(function (response) {
        return response.json().then(function (data) {
          return { ok: response.ok, status: response.status, data: data };
        });
      })
      .then(function (result) {
        if (result.status === 401) {
          updateAuthOnlyNav();
          renderSavedPage();
          return;
        }
        if (!result.ok || !result.data || !Array.isArray(result.data.items)) return;
        setSavedProgrammes(result.data.items);
        renderHomeDashboard();
        renderSavedPage();
      })
      .catch(function () {});
  }

  function getRecentActivity() {
    var items = readStoredJSON("mwongozo-recent-activity", []);
    return Array.isArray(items) ? items : [];
  }

  function setRecentActivity(items) {
    writeStoredJSON("mwongozo-recent-activity", items);
  }

  function addRecentActivity(kind, title, meta) {
    var items = getRecentActivity();
    items.unshift({
      kind: kind || "info",
      title: title || "",
      meta: meta || "",
      ts: Date.now(),
    });
    setRecentActivity(items.slice(0, 8));
    renderHomeDashboard();
  }

  function toggleSavedProgramme(rec) {
    if (!rec || !rec.programme) return;
    whenAuthReady(function () {
      if (!isLoggedIn()) {
        loginRequiredToast();
        return;
      }
    var code = String(rec.programme.code || "");
    if (!code) return;
    var snapshot = {
      code: code,
      name: rec.programme.name || "",
      institution_name: rec.programme.institution_name || "",
      region: rec.programme.region || "",
      category: rec.programme.category || "",
      apply_url: rec.institution_apply_url || rec.institution_website || "",
      saved_at: Date.now(),
    };
    var items = getSavedProgrammes();
    var idx = items.findIndex(function (item) {
      return String(item.code || "") === code;
    });
    var removing = idx !== -1;
    var request = removing
      ? apiFetch("/auth/saved-programmes/" + encodeURIComponent(code), { method: "DELETE" })
      : apiFetch("/auth/saved-programmes", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ programme_code: code, snapshot: snapshot }),
        });
    request
      .then(function (response) {
        if (response.status === 401) {
          handleSavedApiFailure(response);
          return null;
        }
        if (!response.ok && response.status !== 204) {
          handleSavedApiFailure(response, "Imeshindwa kuhifadhi programme");
          return null;
        }
        return response;
      })
      .then(function (response) {
        if (!response) return;
        if (removing) {
          items.splice(idx, 1);
          setSavedProgrammes(items);
          toast("Programme imeondolewa kwenye saved", "info");
          addRecentActivity("save", rec.programme.name || code, "Removed from saved programmes");
        } else {
          items.unshift(snapshot);
          setSavedProgrammes(items.slice(0, 50));
          toast("Programme imehifadhiwa", "success");
          addRecentActivity("save", rec.programme.name || code, "Saved programmes");
        }
        renderHomeDashboard();
        renderSavedPage();
        renderResultsPageTable();
      })
      .catch(function () {
        toast("Imeshindwa kuhifadhi — angalia muunganisho", "warn");
      });
    });
  }

  function isLoggedIn() {
    return !!(window.__MWONGOZO_USER__ && window.__MWONGOZO_USER__.id);
  }

  function whenAuthReady(fn) {
    if (window.MwongozoAuth && typeof window.MwongozoAuth.refresh === "function") {
      return window.MwongozoAuth.refresh().then(function () {
        return fn();
      });
    }
    return Promise.resolve(fn());
  }

  function handleSavedApiFailure(response, fallbackMessage) {
    if (response && response.status === 401) {
      loginRequiredToast();
      return true;
    }
    toast(fallbackMessage || "Imeshindwa kuhifadhi", "warn");
    return true;
  }

  function loginRequiredToast() {
    var L = I18N[getUiLang()] || I18N.sw;
    toast(L.saved_login_required || "Ingia kwanza", "warn");
  }

  function updateSaveAnalysisButtonState() {
    var hasBundle = !!lastRecommendBundle;
    var tableBtn = document.getElementById("saveRecoAnalysisBtn");
    [saveRecoRunBtn, tableBtn].forEach(function (btn) {
      if (!btn) return;
      btn.disabled = !hasBundle;
    });
  }

  function updateAuthOnlyNav() {
    var loggedIn = isLoggedIn();
    document.querySelectorAll(".auth-only-nav").forEach(function (el) {
      el.classList.toggle("hidden", !loggedIn);
      el.hidden = !loggedIn;
    });
    updateSaveAnalysisButtonState();
  }

  function trimRecForSnapshot(rec) {
    if (!rec) return null;
    return {
      rank: rec.rank,
      programme: {
        code: (rec.programme && rec.programme.code) || "",
        name: (rec.programme && rec.programme.name) || "",
        institution_name: (rec.programme && rec.programme.institution_name) || "",
        institution_code: (rec.programme && rec.programme.institution_code) || "",
        region: (rec.programme && rec.programme.region) || "",
        category: (rec.programme && rec.programme.category) || "",
      },
      student_points: rec.student_points,
      minimum_required_points: rec.minimum_required_points,
      assessment: rec.assessment
        ? {
            confidence: rec.assessment.confidence,
            confidence_band: rec.assessment.confidence_band,
          }
        : {},
      __isReview: Boolean(rec.__isReview),
    };
  }

  function buildRecommendBundlePayload(data, inputSnapshot) {
    var recommendations = (data.recommendations || []).map(function (rec) {
      return trimRecForSnapshot(Object.assign({}, rec, { __isReview: false }));
    });
    var reviewCandidates = (data.review_candidates || []).map(function (rec) {
      return trimRecForSnapshot(Object.assign({}, rec, { __isReview: true }));
    });
    var allRows = recommendations.concat(reviewCandidates);
    var input = inputSnapshot || data.input_snapshot || {};
    var combo = (input.combination || input.a_level_combination || "").toString().toUpperCase();
    var examYear = input.exam_year || input.year || "";
    var titleParts = [combo, examYear].filter(Boolean);
    return {
      title: titleParts.length ? titleParts.join(" · ") : "Recommendations " + new Date().toLocaleDateString(),
      input_snapshot: input,
      results_snapshot: {
        recommendations: recommendations.slice(0, 40),
        review_candidates: reviewCandidates.slice(0, 20),
        combination_suggestions: (data.combination_suggestions || []).slice(0, 6),
        summary: {
          direct_count: recommendations.length,
          review_count: reviewCandidates.length,
          total_count: allRows.length,
        },
      },
      recommend_count: allRows.length,
      direct_count: recommendations.length,
      review_count: reviewCandidates.length,
    };
  }

  function syncSavedRecommendationsFromServer() {
    if (!isLoggedIn()) {
      savedRecommendationsCache = [];
      renderSavedPage();
      return Promise.resolve();
    }
    return apiFetch("/auth/saved-recommendations")
      .then(function (response) {
        return response.json().then(function (data) {
          return { ok: response.ok, status: response.status, data: data };
        });
      })
      .then(function (result) {
        if (result.status === 401) {
          savedRecommendationsCache = [];
          updateAuthOnlyNav();
          renderSavedPage();
          return;
        }
        if (!result.ok || !result.data || !Array.isArray(result.data.items)) return;
        savedRecommendationsCache = result.data.items;
        renderSavedPage();
      })
      .catch(function () {});
  }

  function syncAllSavedFromServer() {
    if (!isLoggedIn()) {
      setSavedProgrammes([]);
      savedRecommendationsCache = [];
      renderSavedPage();
      renderHomeDashboard();
      return Promise.resolve();
    }
    return Promise.all([syncSavedProgrammesFromServer(), syncSavedRecommendationsFromServer()]);
  }

  function formatSavedAtLabel(value) {
    if (!value) return "";
    var stamp = Date.parse(String(value));
    if (!Number.isFinite(stamp)) return String(value);
    try {
      return new Date(stamp).toLocaleString(getUiLang() === "en" ? "en-GB" : "sw-TZ", {
        dateStyle: "medium",
        timeStyle: "short",
      });
    } catch (_e) {
      return new Date(stamp).toLocaleString();
    }
  }

  function renderSavedProgrammesCards(container, items, options) {
    if (!container) return;
    options = options || {};
    var L = I18N[getUiLang()] || I18N.sw;
    if (!items.length) {
      container.innerHTML = '<div class="saved-empty">' + escapeHtml(L.saved_empty_prog) + "</div>";
      return;
    }
    container.innerHTML = items
      .map(function (item) {
        var code = String(item.code || "");
        return (
          '<article class="saved-programme-card" data-saved-prog="' +
          escapeHtmlAttr(code) +
          '">' +
          '<div class="saved-programme-card__title">' +
          escapeHtml(item.name || item.code || "Programme") +
          '</div><div class="saved-programme-card__meta">' +
          escapeHtml(item.institution_name || "") +
          " · " +
          escapeHtml(item.region || "") +
          '</div><div class="saved-programme-card__actions">' +
          '<span class="muted small">' +
          escapeHtml(item.category || "") +
          "</span>" +
          '<div class="btn-group">' +
          (item.apply_url
            ? '<a class="btn btn-secondary btn-sm" href="' +
              escapeHtmlAttr(item.apply_url) +
              '" target="_blank" rel="noopener noreferrer">Open</a>'
            : "") +
          (options.removable
            ? '<button type="button" class="btn btn-secondary btn-sm btn-remove-saved" data-remove-saved="' +
              escapeHtmlAttr(code) +
              '"><i class="fa-solid fa-trash-can" aria-hidden="true"></i></button>'
            : "") +
          "</div></div></article>"
        );
      })
      .join("");
    if (options.removable) {
      container.querySelectorAll("[data-remove-saved]").forEach(function (btn) {
        btn.addEventListener("click", function () {
          var code = btn.getAttribute("data-remove-saved");
          if (!code) return;
          apiFetch("/auth/saved-programmes/" + encodeURIComponent(code), { method: "DELETE" })
            .then(function (response) {
              if (!response.ok) throw new Error("delete failed");
              var itemsNext = getSavedProgrammes().filter(function (item) {
                return String(item.code || "") !== code;
              });
              setSavedProgrammes(itemsNext);
              renderSavedPage();
              renderHomeDashboard();
              if (resultsPagination.items && resultsPagination.items.length) renderResultsPageTable();
              toast("Programme imeondolewa", "info");
            })
            .catch(function () {
              toast("Imeshindwa kuondoa", "warn");
            });
        });
      });
    }
  }

  function renderSavedRecommendationsList() {
    if (!savedRecommendationsListEl) return;
    var L = I18N[getUiLang()] || I18N.sw;
    if (savedRecoCountEl) savedRecoCountEl.textContent = String(savedRecommendationsCache.length);
    if (!savedRecommendationsCache.length) {
      savedRecommendationsListEl.innerHTML = '<div class="saved-empty">' + escapeHtml(L.saved_empty_reco) + "</div>";
      return;
    }
    savedRecommendationsListEl.innerHTML = savedRecommendationsCache
      .map(function (item) {
        var title = item.title || ("Analysis #" + item.id);
        var input = item.input_snapshot || {};
        var pathway = input.pathway || input.level || "";
        return (
          '<article class="saved-reco-card" data-saved-reco-id="' +
          escapeHtmlAttr(String(item.id)) +
          '"><div class="saved-reco-card__head" data-toggle-reco="' +
          escapeHtmlAttr(String(item.id)) +
          '"><div><div class="saved-reco-card__title">' +
          escapeHtml(title) +
          '</div><div class="saved-reco-card__meta">' +
          escapeHtml(formatSavedAtLabel(item.saved_at)) +
          (pathway ? " · " + escapeHtml(String(pathway)) : "") +
          '</div></div><div class="saved-reco-card__badges">' +
          '<span class="saved-reco-badge saved-reco-badge--direct">' +
          escapeHtml(String(item.direct_count || 0)) +
          " direct</span>" +
          '<span class="saved-reco-badge saved-reco-badge--review">' +
          escapeHtml(String(item.review_count || 0)) +
          " borderline</span>" +
          '</div></div><div class="saved-reco-card__body"><div class="saved-reco-card__actions">' +
          '<button type="button" class="btn btn-secondary btn-sm" data-load-reco="' +
          escapeHtmlAttr(String(item.id)) +
          '"><i class="fa-solid fa-table-list" aria-hidden="true"></i> View table</button>' +
          '<button type="button" class="btn btn-secondary btn-sm btn-remove-saved" data-delete-reco="' +
          escapeHtmlAttr(String(item.id)) +
          '"><i class="fa-solid fa-trash-can" aria-hidden="true"></i> Delete</button>' +
          '</div><div class="saved-reco-detail" data-reco-detail="' +
          escapeHtmlAttr(String(item.id)) +
          '"><p class="muted small">Loading…</p></div></div></article>'
        );
      })
      .join("");

    savedRecommendationsListEl.querySelectorAll("[data-toggle-reco]").forEach(function (head) {
      head.addEventListener("click", function (e) {
        if (e.target.closest("[data-delete-reco],[data-load-reco]")) return;
        var card = head.closest(".saved-reco-card");
        if (!card) return;
        var opening = !card.classList.contains("is-open");
        card.classList.toggle("is-open", opening);
        if (opening) loadSavedRecommendationDetail(Number(card.getAttribute("data-saved-reco-id")));
      });
    });

    savedRecommendationsListEl.querySelectorAll("[data-load-reco]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        loadSavedRecommendationDetail(Number(btn.getAttribute("data-load-reco")), true);
      });
    });

    savedRecommendationsListEl.querySelectorAll("[data-delete-reco]").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.stopPropagation();
        deleteSavedRecommendation(Number(btn.getAttribute("data-delete-reco")));
      });
    });
  }

  function loadSavedRecommendationDetail(recoId, openResults) {
    if (!recoId) return;
    apiFetch("/auth/saved-recommendations/" + encodeURIComponent(String(recoId)))
      .then(function (response) {
        return response.json().then(function (data) {
          return { ok: response.ok, data: data };
        });
      })
      .then(function (result) {
        if (!result.ok || !result.data || !result.data.item) throw new Error("missing");
        var item = result.data.item;
        var snap = item.results_snapshot || {};
        var recs = (snap.recommendations || []).concat(snap.review_candidates || []);
        var detailEl = savedRecommendationsListEl && savedRecommendationsListEl.querySelector('[data-reco-detail="' + recoId + '"]');
        if (detailEl) {
          if (!recs.length) {
            detailEl.innerHTML = '<p class="muted small">' + escapeHtml(t("saved_no_programmes")) + "</p>";
          } else {
            detailEl.innerHTML =
              '<table class="saved-reco-mini-table"><thead><tr><th>#</th><th>Institution</th><th>Programme</th><th>Conf.</th></tr></thead><tbody>' +
              recs
                .slice(0, 15)
                .map(function (rec) {
                  var conf = rec.assessment && rec.assessment.confidence != null ? rec.assessment.confidence + "%" : "—";
                  return (
                    "<tr><td>" +
                    escapeHtml(String(rec.rank != null ? rec.rank : "—")) +
                    "</td><td>" +
                    escapeHtml((rec.programme && rec.programme.institution_name) || "") +
                    "</td><td>" +
                    escapeHtml((rec.programme && rec.programme.name) || "") +
                    "</td><td>" +
                    escapeHtml(String(conf)) +
                    "</td></tr>"
                  );
                })
                .join("") +
              "</tbody></table>";
          }
        }
        if (openResults) {
          resultsPagination.items = recs.map(function (rec) {
            return Object.assign({}, rec, { __isReview: Boolean(rec.__isReview) });
          });
          resultsPagination.page = 0;
          resultsPagination.directCount = Number(item.direct_count) || 0;
          resultsPagination.reviewCount = Number(item.review_count) || 0;
          resultsPagination.filters = { query: "", region: "all", category: "all", sort: "confidence_desc" };
          lastRecommendBundle = {
            title: item.title,
            input_snapshot: item.input_snapshot || {},
            results_snapshot: snap,
            recommend_count: item.recommend_count,
            direct_count: item.direct_count,
            review_count: item.review_count,
          };
          showResultsView();
          navigateDash("results");
          renderResultsPageTable();
        }
      })
      .catch(function () {
        toast("Imeshindwa kupakia uchambuzi", "warn");
      });
  }

  function deleteSavedRecommendation(recoId) {
    if (!recoId) return;
    apiFetch("/auth/saved-recommendations/" + encodeURIComponent(String(recoId)), { method: "DELETE" })
      .then(function (response) {
        if (!response.ok) throw new Error("delete failed");
        savedRecommendationsCache = savedRecommendationsCache.filter(function (item) {
          return Number(item.id) !== Number(recoId);
        });
        renderSavedPage();
        toast("Uchambuzi umeondolewa", "info");
      })
      .catch(function () {
        toast("Imeshindwa kuondoa uchambuzi", "warn");
      });
  }

  function renderSavedPage() {
    var loggedIn = isLoggedIn();
    if (savedGuestGateEl) {
      savedGuestGateEl.classList.toggle("hidden", loggedIn);
      savedGuestGateEl.hidden = !loggedIn ? false : true;
    }
    if (savedPageContentEl) {
      savedPageContentEl.classList.toggle("hidden", !loggedIn);
      savedPageContentEl.hidden = !loggedIn;
    }
    if (!loggedIn) return;
    var saved = getSavedProgrammes();
    if (savedProgCountEl) savedProgCountEl.textContent = String(saved.length);
    renderSavedProgrammesCards(savedProgrammesPageListEl, saved, { removable: true });
    if (savedProgrammesListEl) renderSavedProgrammesCards(savedProgrammesListEl, saved.slice(0, 4));
    renderSavedRecommendationsList();
  }

  function saveCurrentRecommendations() {
    whenAuthReady(function () {
      if (!isLoggedIn()) {
        loginRequiredToast();
        return Promise.resolve();
      }
      if (!lastRecommendBundle) {
        toast("Hakuna mapendekezo ya kuhifadhi", "warn");
        return Promise.resolve();
      }
      if (saveRecoRunBtn) saveRecoRunBtn.disabled = true;
      var tableSaveBtn = document.getElementById("saveRecoAnalysisBtn");
      if (tableSaveBtn) tableSaveBtn.disabled = true;
      return apiFetch("/auth/saved-recommendations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(lastRecommendBundle),
      })
        .then(function (response) {
          return response.json().then(function (data) {
            return { ok: response.ok, status: response.status, data: data };
          });
        })
        .then(function (result) {
          if (result.status === 401) {
            handleSavedApiFailure({ status: 401 });
            return;
          }
          if (!result.ok) {
            var detail =
              result.data && result.data.detail
                ? String(result.data.detail)
                : "Imeshindwa kuhifadhi uchambuzi";
            toast(detail, "warn");
            return;
          }
          var L = I18N[getUiLang()] || I18N.sw;
          toast(L.saved_save_ok || "Saved", "success");
          addRecentActivity("save", lastRecommendBundle.title || "Saved analysis", "Recommendation run saved");
          return syncSavedRecommendationsFromServer().then(function () {
            navigateDash("saved");
          });
        })
        .catch(function () {
          var L = I18N[getUiLang()] || I18N.sw;
          toast(L.saved_save_fail || "Save failed", "warn");
        })
        .finally(function () {
          updateSaveAnalysisButtonState();
        });
    });
  }

  function isProgrammeSaved(rec) {
    if (!rec || !rec.programme) return false;
    var code = String(rec.programme.code || "");
    if (!code) return false;
    return getSavedProgrammes().some(function (item) {
      return String(item.code || "") === code;
    });
  }

  function formatRelativeTime(ts) {
    var stamp = Number(ts) || Date.now();
    var diff = Math.max(0, Date.now() - stamp);
    var mins = Math.floor(diff / 60000);
    if (mins < 1) return t("time_just_now");
    if (mins < 60) return mins + t("time_mins_ago");
    var hrs = Math.floor(mins / 60);
    if (hrs < 24) return hrs + t("time_hrs_ago");
    var days = Math.floor(hrs / 24);
    return days + t("time_days_ago");
  }

  function renderHomeDashboard() {
    var saved = getSavedProgrammes();
    var activity = getRecentActivity();
    if (homeOverviewStatsEl) {
      var programmeCount = Number(homeMeta.programmes_loaded) || 0;
      var institutionCount = Array.isArray(homeMeta.institutions_covered) ? homeMeta.institutions_covered.length : 0;
      homeOverviewStatsEl.innerHTML =
        '<div class="overview-stat"><span class="overview-stat__value">' +
        programmeCount +
        '</span><span class="overview-stat__label">' +
        escapeHtml(t("dash_stat_prog")) +
        "</span></div>" +
        '<div class="overview-stat"><span class="overview-stat__value">' +
        institutionCount +
        '</span><span class="overview-stat__label">' +
        escapeHtml(t("dash_stat_inst")) +
        "</span></div>" +
        '<div class="overview-stat"><span class="overview-stat__value">' +
        saved.length +
        '</span><span class="overview-stat__label">' +
        escapeHtml(t("dash_stat_saved_prog")) +
        "</span></div>" +
        '<div class="overview-stat"><span class="overview-stat__value">' +
        (isLoggedIn() ? savedRecommendationsCache.length : "—") +
        '</span><span class="overview-stat__label">' +
        escapeHtml(t("dash_stat_saved_reco")) +
        "</span></div>" +
        '<div class="overview-stat"><span class="overview-stat__value">' +
        activity.length +
        '</span><span class="overview-stat__label">' +
        escapeHtml(t("dash_stat_recent")) +
        "</span></div>";
    }
    if (recentActivityListEl) {
      if (!activity.length) {
        recentActivityListEl.innerHTML = '<li class="activity-empty">' + escapeHtml(t("dash_activity_empty")) + "</li>";
      } else {
        recentActivityListEl.innerHTML = activity
          .slice(0, 5)
          .map(function (item) {
            var kind = String(item.kind || "info").toLowerCase();
            return (
              '<li class="activity-item">' +
              '<span class="activity-item__dot activity-item__dot--' +
              escapeHtmlAttr(kind) +
              '" aria-hidden="true"></span>' +
              '<div><div class="activity-item__title">' +
              escapeHtml(item.title || t("dash_activity_fallback")) +
              '</div><div class="activity-item__meta">' +
              escapeHtml(item.meta || "") +
              " · " +
              escapeHtml(formatRelativeTime(item.ts)) +
              "</div></div></li>"
            );
          })
          .join("");
      }
    }
    if (isLoggedIn()) renderSavedPage();
  }

  var resultsPagination = {
    items: [],
    page: 0,
    pageSize: 24,
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
      cta_register: "Jisajili",
      cta_skip: "Ruka landing",
      cta_skip_link: "Ruka landing → fungua dashboard moja kwa moja",
      cta_start_results: "Anza bure — weka matokeo",
      cta_have_account: "Nina akaunti",
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
        "Fuata TCU, HESLB, na taasisi zako — thibitisha rasmi kila mwaka kwenye tovuti husika.",
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
      hero_stat1n: "60+",
      hero_stat1l: "Vyuo na taasisi",
      hero_stat2n: "400+",
      hero_stat2l: "Programme (shahada, diploma, cheti)",
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
      feat3_p: "Chuja vyuo kwa mkoa, umma/binafsi, na programme kwa category — tofauti na mapendekezo.",
      sidebar_foot: "MWONGOZO SMART · TCU & NECTA",
      fab_story: "Tupige story",
      chat_head: "SAM — msaada wa haraka",
      chat_intro: "Uliza kuhusu NECTA, TCU, vyuo, au HESLB — majibu ya haraka hapa.",
      chat_ph: "Andika ujumbe…",
      chat_typing: "SAM anaandika…",
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
      nav_saved: "Saved & analysis",
      saved_page_title: "Saved & analysis",
      saved_page_sub: "Mapendekezo yako yaliyohifadhiwa na programme ulizoweka bookmark — kwa uchambuzi wa baadaye.",
      saved_go_reco: "Angalia mapendekezo",
      saved_login_title: "Ingia ili kuona saved yako",
      saved_login_sub: "Hifadhi uchambuzi wa mapendekezo na programme kwa akaunti yako.",
      saved_login_cta: "Ingia / Jisajili",
      saved_reco_title: "Saved recommendations",
      saved_reco_sub: "Historia ya uchambuzi wako",
      saved_prog_title: "Saved programmes",
      saved_prog_sub: "Programme ulizoweka bookmark",
      saved_save_run: "Hifadhi uchambuzi",
      saved_save_ok: "Uchambuzi umehifadhiwa",
      saved_save_fail: "Imeshindwa kuhifadhi uchambuzi",
      saved_login_required: "Ingia kwanza ili kuhifadhi",
      saved_empty_reco: "Hakuna uchambuzi ulihifadhiwa bado. Run recommendations kisha bofya Hifadhi uchambuzi.",
      saved_empty_prog: "Hakuna programme iliyohifadhiwa. Bofya bookmark kwenye jedwali la mapendekezo.",
      saved_view_all: "Angalia saved",
      nav_loan: "Mkopo & HESLB",
      loan_title: "Mkopo & HESLB",
      loan_sub: "Mwongozo rasmi wa mkopo, nyaraka, na ufuatiliaji wa maombi.",
      loan_demo_badge: "Mwongozo + ufuatiliaji",
      loan_transparency: "Thibitisha kila hatua kwenye OLAS na heslb.go.tz — data halisi ya HESLB haipatikani hapa.",
      loan_tab_guidance: "Mwongozo",
      loan_tab_tracker: "Fuatilia",
      loan_entry_title: "Anza ufuatiliaji",
      loan_entry_hint: "Weka taarifa zako au jaribu nambari ya mfano ya maombi.",
      loan_exam_level: "Kiwango cha mtihani",
      loan_level_al: "A-Level",
      loan_level_ol: "O-Level",
      loan_exam_no: "Nambari ya mtihani (NECTA)",
      loan_programme: "Programu uliyochagua",
      loan_institution: "Chuo",
      loan_heslb_ref: "Nambari ya maombi HESLB (OLAS)",
      loan_nin: "NIDA / NIN (Nambari ya Utambulisho)",
      loan_special_legend: "Kundi maalum (kama inavyotajwa na miongozo ya HESLB)",
      loan_cat_orphan: "Yatima",
      loan_cat_disability: "Ulemavu",
      loan_cat_income: "Kipato cha chini",
      loan_cat_single: "Familia ya mzazi mmoja",
      loan_track_btn: "Fungua dashibodi ya ufadhili",
      loan_demo_picker_label: "Chagua mfano wa mwanafunzi:",
      loan_disclaimer:
        "Thibitisha kila hatua kwenye OLAS na heslb.go.tz. Majina lazima yalingane na NIDA; cheti cha kuzaliwa kinathibitishwa na RITA kama inavyoelekezwa na HESLB.",
      loan_funding_table: "Jedwali la ufadhili",
      loan_col_ref: "HESLB ref",
      loan_col_stage: "Hatua",
      loan_col_complete: "Ukamilifu",
      loan_col_batch: "Batch",
      loan_col_prob: "Uwezekano",
      loan_col_alerts: "Taarifa",
      loan_col_appeal: "Rufaa",
      loan_course_priority: "Kipaumbele cha programu",
      loan_completion: "Ukamilifu wa maombi",
      loan_timeline: "Ratiba ya hatua",
      loan_batch_pred: "Utabiri wa Batch",
      loan_confidence: "Kiwango cha uhakika wa ufadhili",
      loan_citizenship: "NIDA / Uraia",
      loan_special_panel: "Makundi maalum",
      loan_alerts: "Taarifa & kituo cha hatua",
      loan_risks: "Kuzuia makosa ya kawaida",
      loan_scholarships: "Scholarships & ufadhili mbadala",
      loan_appeal: "Mwongozo wa rufaa",
      loan_parent: "Mwongozo wa mzazi/mlezi",
      loan_no_upload: "Hakuna upakiaji hapa — mwongozo tu.",
      loan_insights: "Mifano ya mafanikio",
      loan_dash_action: "Fuatilia maombi ya HESLB na uwezekano wa ufadhili.",
      nav_assistant: "Msaada",
      help_title: "Kituo cha Msaada",
      help_sub: "SAM — mwongozo wa NECTA, mapendekezo, vyuo, na HESLB.",
      help_badge: "Msaada hai",
      help_hero_title: "Uliza, chagua mada, au enda moja kwa moja",
      help_hero_p: "Majibu ya haraka yaliyopangwa — mwongozo wa vitendo kutoka MWONGOZO SMART.",
      help_search_ph: "Tafuta mada…",
      help_quick_input: "Jaza / pakua NECTA",
      help_quick_results: "Angalia orodha",
      help_quick_dir: "Chunguza programme",
      help_quick_loan: "Mwongozo HESLB",
      help_fallback: "Tumia kichupo Msaada kwa mada zilizopangwa.",
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
        "Hujambo — mimi SAM. NECTA, TCU, vyuo, HESLB: uliza swali, nitakusaidia haraka.",
      partners_label: "Washirika rasmi wa elimu",
      dir_title: "Vyuo Tanzania",
      dir_sub: "Chuja vyuo kwa mkoa, umma/binafsi, na aina — tofauti na mapendekezo ya matokeo yako.",
      dir_tab_univ: "Vyuo",
      dir_tab_prog: "Programme",
      dir_search_univ: "Tafuta chuo",
      dir_search_univ_ph: "Jina, mji, mkoa…",
      dir_search_prog: "Tafuta programme",
      dir_search_prog_ph: "Course, chuo, mkoa…",
      dir_all_regions: "Mkoa wote",
      dir_ownership: "Umiliki",
      dir_all_ownership: "Vyote",
      dir_public: "Umma",
      dir_private: "Binafsi",
      dir_kind: "Aina",
      dir_all_kinds: "Zote",
      dir_kind_univ: "Chuo kikuu",
      dir_kind_college: "Chuo / taasisi",
      dir_kind_other: "Nyingine",
      dir_award: "Kiwango",
      dir_all_awards: "Vyote",
      dir_award_bach: "Shahada",
      dir_award_dip: "Diploma",
      dir_award_cert: "Cheti",
      dir_inst_filter: "Chuo",
      dir_all_inst: "Vyote",
      dir_min_pts: "Min points",
      dir_univ_count: "vyuo",
      dir_prog_count: "programme",
      dir_read_more: "Soma zaidi",
      dir_view_programmes: "Angalia programme",
      dir_official_site: "Tovuti rasmi",
      dir_prog_verified: "programme (TCU)",
      dir_prog_official: "programme (tovuti rasmi)",
      dir_live_loading: "Inapakia kutoka tovuti rasmi…",
      dir_live_partial: "Baadhi ya vyuo vimesasishwa kutoka tovuti rasmi",
      dir_preview_more: "na zaidi",
      nav_directory: "Vyuo Tanzania",
      dash_welcome: "Karibu tena",
      dash_overview: "Muhtasari",
      dash_overview_sub: "Muhtasari wa mfumo",
      dash_next_actions: "Hatua za haraka",
      dash_next_sub: "Hatua za haraka",
      dash_recent: "Shughuli za karibuni",
      dash_recent_sub: "Mambo ya karibuni",
      dash_act_input_title: "Endelea na matokeo",
      dash_act_input_desc: "Jaza matokeo au pakia kutoka NECTA.",
      dash_act_results_title: "Angalia mapendekezo",
      dash_act_results_desc: "Pitia direct na borderline matches.",
      dash_act_dir_title: "Tafuta vyuo",
      dash_act_dir_desc: "Chuja programme kwa mkoa na category.",
      dash_stat_prog: "Programme zilizopakiwa",
      dash_stat_inst: "Taasisi zilizofunikwa",
      dash_stat_saved_prog: "Programme zilizohifadhiwa",
      dash_stat_saved_reco: "Uchambuzi uliohifadhiwa",
      dash_stat_recent: "Hatua za karibuni",
      dash_activity_empty: "Hakuna shughuli bado. Jaribu lookup au mapendekezo.",
      dash_activity_fallback: "Shughuli",
      theme_light_label: "Muonekano mwanga",
      theme_dark_label: "Muonekano giza",
      input_level_title: "Chagua level ya mtumiaji",
      input_level_hint: "Form 4 au Form 6",
      input_pathway_o: "Form 4 / O-Level",
      input_pathway_a: "Form 6 / A-Level",
      input_pathway_note:
        "Chagua level, kisha unaweza <strong>chagua mwaka na nambari ya mtihani</strong> ili kupakia matokeo kutoka NECTA moja kwa moja, au jaza fomu kwa mkono.",
      input_level_prompt: "Bonyeza <strong>Form 4</strong> au <strong>Form 6</strong> ili uanze.",
      input_necta_title: "Angalia matokeo NECTA",
      input_necta_hint: "Mwaka wa mtihani + nambari yako",
      input_necta_year: "Mwaka alio maliza shule",
      input_necta_cno: "Nambari ya mtihani (CNO)",
      input_necta_fetch: "Pakua matokeo kutoka NECTA",
      input_al_title: "Form 6 / A-Level",
      input_al_hint: "Combination na masomo ya principal",
      input_combination: "Combination",
      input_combination_ph: "Chagua combination",
      input_principal: "Masomo ya principal",
      input_add_al: "+ Ongeza somo la A-Level",
      input_ol_title: "Form 4 / O-Level",
      input_ol_hint: "Masomo ya CSEE, grades, na result model",
      input_division: "Division iliyokokotwa",
      input_division_ph: "Chagua division",
      input_result_model: "Result model",
      input_ol_subjects: "Masomo ya NECTA O-Level",
      input_add_ol: "+ Ongeza somo la O-Level",
      btn_get_reco: "Pata mapendekezo",
      btn_load_example: "Pakia mfano",
      btn_clear_form: "Futa fomu",
      results_page_title: "Matokeo",
      results_page_sub: "Mapendekezo yaliyopangwa",
      btn_back_input: "Rudi kwenye fomu",
      result_summary_idle:
        "Chagua level, jaza matokeo, kisha bonyeza <strong>Pata mapendekezo</strong>.",
      input_cleared: "Fomu imefutwa. Chagua level kisha ujaze matokeo.",
      necta_pick_level: "Chagua Form 4 au Form 6 kwanza.",
      necta_enter_cno: "Weka nambari ya mtihani (CNO).",
      meta_load_fail: "Haiwezi kupakia takwimu sasa. Jaribu tena baadaye.",
      dir_loading: "Inapakia vyuo…",
      dir_no_data: "Hakuna data ya vyuo.",
      dir_no_match: "Hakuna vyuo vinavyolingana na vichujio.",
      saved_no_programmes: "Hakuna programme katika snapshot hii.",
      results_all_regions: "Mkoa wote",
      results_all_categories: "Category zote",
      results_sort_high: "Juu → chini",
      results_sort_low: "Chini → juu",
      time_just_now: "Sasa hivi",
      time_mins_ago: " dakika zilizopita",
      time_hrs_ago: " masaa yaliyopita",
      time_days_ago: " siku zilizopita",
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
      cta_register: "Register",
      cta_skip: "Skip landing",
      cta_skip_link: "Skip landing → open dashboard directly",
      cta_start_results: "Start free — enter results",
      cta_have_account: "I have an account",
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
        "Follow TCU, HESLB, and your target institutions — confirm each year on official sites.",
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
      hero_stat1n: "60+",
      hero_stat1l: "Universities & colleges",
      hero_stat2n: "400+",
      hero_stat2l: "Programmes (degree, diploma, cert)",
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
      feat3_p: "Filter universities by region and public/private; browse programmes separately from recommendations.",
      sidebar_foot: "MWONGOZO SMART · TCU & NECTA",
      fab_story: "Let's talk",
      chat_head: "SAM — quick help",
      chat_intro: "Ask about NECTA, TCU, universities, or HESLB — quick answers here.",
      chat_ph: "Type a message…",
      chat_typing: "SAM is typing…",
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
      nav_saved: "Saved & analysis",
      saved_page_title: "Saved & analysis",
      saved_page_sub: "Your saved recommendation runs and bookmarked programmes for later review.",
      saved_go_reco: "View recommendations",
      saved_login_title: "Sign in to view your saved items",
      saved_login_sub: "Save recommendation analyses and programmes to your account.",
      saved_login_cta: "Sign in / Register",
      saved_reco_title: "Saved recommendations",
      saved_reco_sub: "Your analysis history",
      saved_prog_title: "Saved programmes",
      saved_prog_sub: "Programmes you bookmarked",
      saved_save_run: "Save analysis",
      saved_save_ok: "Analysis saved",
      saved_save_fail: "Could not save analysis",
      saved_login_required: "Sign in first to save",
      saved_empty_reco: "No saved analyses yet. Run recommendations then click Save analysis.",
      saved_empty_prog: "No saved programmes yet. Use the bookmark icon on the recommendations table.",
      saved_view_all: "View saved",
      nav_loan: "Loan & HESLB",
      loan_title: "Loan & HESLB",
      loan_sub: "Official loan guidance, documents, and application tracking.",
      loan_demo_badge: "Guidance + tracking",
      loan_transparency: "Confirm every step on OLAS and heslb.go.tz — live HESLB data is not available here.",
      loan_tab_guidance: "Guidance",
      loan_tab_tracker: "Track",
      loan_entry_title: "Start tracking",
      loan_entry_hint: "Enter your details or try a sample application reference.",
      loan_exam_level: "Exam level",
      loan_level_al: "A-Level",
      loan_level_ol: "O-Level",
      loan_exam_no: "Exam number (NECTA)",
      loan_programme: "Selected programme",
      loan_institution: "Institution",
      loan_heslb_ref: "HESLB application reference (OLAS)",
      loan_nin: "NIDA / NIN (National ID)",
      loan_special_legend: "Special categories (as in HESLB guidelines)",
      loan_cat_orphan: "Orphan",
      loan_cat_disability: "Disability",
      loan_cat_income: "Low income",
      loan_cat_single: "Single-parent household",
      loan_track_btn: "Open funding dashboard",
      loan_demo_picker_label: "Choose a sample student:",
      loan_disclaimer:
        "Confirm every step on OLAS and heslb.go.tz. Names must match NIDA; birth certificates certified via RITA as directed by HESLB.",
      loan_funding_table: "Funding table",
      loan_col_ref: "HESLB ref",
      loan_col_stage: "Stage",
      loan_col_complete: "Completion",
      loan_col_batch: "Batch",
      loan_col_prob: "Probability",
      loan_col_alerts: "Alerts",
      loan_col_appeal: "Appeal",
      loan_course_priority: "Course funding priority",
      loan_completion: "Application completion",
      loan_timeline: "Current stage timeline",
      loan_batch_pred: "Predicted batch assignment",
      loan_confidence: "Estimated funding confidence",
      loan_citizenship: "NIDA / citizenship",
      loan_special_panel: "Special categories",
      loan_alerts: "Smart alerts & action center",
      loan_risks: "Common mistakes prevention",
      loan_scholarships: "Scholarship & alternative funding",
      loan_appeal: "Appeal guidance assistant",
      loan_parent: "Parent / guardian guidance",
      loan_no_upload: "No uploads here — guidance only.",
      loan_insights: "Success insights",
      loan_dash_action: "Track HESLB application and funding probability.",
      nav_assistant: "Help",
      help_title: "Help Centre",
      help_sub: "SAM — guidance for NECTA, recommendations, universities, and HESLB.",
      help_badge: "Live help",
      help_hero_title: "Ask, pick a topic, or jump straight in",
      help_hero_p: "Quick structured answers — practical guidance from MWONGOZO SMART.",
      help_search_ph: "Search topics…",
      help_quick_input: "Enter / fetch NECTA",
      help_quick_results: "View list",
      help_quick_dir: "Browse programmes",
      help_quick_loan: "HESLB guidance",
      help_fallback: "Use the Help tab for structured topics.",
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
        "Hi — I'm SAM. Ask about NECTA, TCU, universities, or HESLB — quick guidance here.",
      partners_label: "Official education partners",
      dir_title: "Universities in Tanzania",
      dir_sub: "Filter by region, public/private, and type — separate from your results-based recommendations.",
      dir_tab_univ: "Universities",
      dir_tab_prog: "Programmes",
      dir_search_univ: "Search institution",
      dir_search_univ_ph: "Name, city, region…",
      dir_search_prog: "Search programmes",
      dir_search_prog_ph: "Course, institution, region…",
      dir_all_regions: "All regions",
      dir_ownership: "Ownership",
      dir_all_ownership: "All",
      dir_public: "Public",
      dir_private: "Private",
      dir_kind: "Type",
      dir_all_kinds: "All types",
      dir_kind_univ: "University",
      dir_kind_college: "College / institute",
      dir_kind_other: "Other",
      dir_award: "Award level",
      dir_all_awards: "All levels",
      dir_award_bach: "Bachelor",
      dir_award_dip: "Diploma",
      dir_award_cert: "Certificate",
      dir_inst_filter: "Institution",
      dir_all_inst: "All",
      dir_min_pts: "Min points",
      dir_univ_count: "institutions",
      dir_prog_count: "programmes",
      dir_read_more: "Read more",
      dir_view_programmes: "View programmes",
      dir_official_site: "Official website",
      dir_prog_verified: "programmes (TCU)",
      dir_prog_official: "programmes (official site)",
      dir_live_loading: "Loading from official websites…",
      dir_live_partial: "Some institutions updated from official sites",
      dir_preview_more: "and more",
      nav_directory: "Tanzania universities",
      dash_welcome: "Welcome back",
      dash_overview: "Overview",
      dash_overview_sub: "System snapshot",
      dash_next_actions: "Next actions",
      dash_next_sub: "Quick steps",
      dash_recent: "Recent activity",
      dash_recent_sub: "Latest actions",
      dash_act_input_title: "Continue with results",
      dash_act_input_desc: "Enter results or fetch from NECTA.",
      dash_act_results_title: "View recommendations",
      dash_act_results_desc: "Review direct and borderline matches.",
      dash_act_dir_title: "Browse institutions",
      dash_act_dir_desc: "Filter programmes by region and category.",
      dash_stat_prog: "Programmes loaded",
      dash_stat_inst: "Institutions covered",
      dash_stat_saved_prog: "Saved programmes",
      dash_stat_saved_reco: "Saved analyses",
      dash_stat_recent: "Recent actions",
      dash_activity_empty: "No activity yet. Try a lookup or recommendations.",
      dash_activity_fallback: "Activity",
      theme_light_label: "Light mode",
      theme_dark_label: "Dark mode",
      input_level_title: "Choose exam level",
      input_level_hint: "Form 4 or Form 6",
      input_pathway_o: "Form 4 / O-Level",
      input_pathway_a: "Form 6 / A-Level",
      input_pathway_note:
        "Pick a level, then you can <strong>select year and exam number</strong> to fetch NECTA results automatically, or fill the form manually.",
      input_level_prompt: "Press <strong>Form 4</strong> or <strong>Form 6</strong> to start.",
      input_necta_title: "Check NECTA results",
      input_necta_hint: "Exam year + your number",
      input_necta_year: "Year completed school",
      input_necta_cno: "Exam number (CNO)",
      input_necta_fetch: "Fetch results from NECTA",
      input_al_title: "Form 6 / A-Level",
      input_al_hint: "Combination and principal subjects",
      input_combination: "Combination",
      input_combination_ph: "Select combination",
      input_principal: "Principal subjects",
      input_add_al: "+ Add A-Level subject",
      input_ol_title: "Form 4 / O-Level",
      input_ol_hint: "CSEE subjects, grades, and result model",
      input_division: "Calculated division",
      input_division_ph: "Select division",
      input_result_model: "Result model",
      input_ol_subjects: "NECTA O-Level subjects",
      input_add_ol: "+ Add O-Level subject",
      btn_get_reco: "Get recommendations",
      btn_load_example: "Load example",
      btn_clear_form: "Clear form",
      results_page_title: "Results",
      results_page_sub: "Ranked recommendations",
      btn_back_input: "Back to inputs",
      result_summary_idle:
        "Choose a level, enter results, then press <strong>Get recommendations</strong>.",
      input_cleared: "Form cleared. Choose a level and enter results.",
      necta_pick_level: "Choose Form 4 or Form 6 first.",
      necta_enter_cno: "Enter exam number (CNO).",
      meta_load_fail: "Could not load stats right now. Try again later.",
      dir_loading: "Loading institutions…",
      dir_no_data: "No institution data.",
      dir_no_match: "No institutions match your filters.",
      saved_no_programmes: "No programmes in this snapshot.",
      results_all_regions: "All regions",
      results_all_categories: "All categories",
      results_sort_high: "High → low",
      results_sort_low: "Low → high",
      time_just_now: "Just now",
      time_mins_ago: " min ago",
      time_hrs_ago: " hr ago",
      time_days_ago: "d ago",
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

  function t(key) {
    var pack = I18N[getUiLang()] || I18N.sw;
    return pack[key] != null ? pack[key] : key;
  }

  function applyI18n() {
    var lang = getUiLang();
    var pack = I18N[lang] || I18N.sw;
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      var k = el.getAttribute("data-i18n");
      if (k && pack[k] != null) el.textContent = pack[k];
    });
    document.querySelectorAll("[data-i18n-html]").forEach(function (el) {
      var k = el.getAttribute("data-i18n-html");
      if (k && pack[k] != null) el.innerHTML = pack[k];
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach(function (el) {
      var k = el.getAttribute("data-i18n-placeholder");
      if (k && pack[k] != null) el.setAttribute("placeholder", pack[k]);
    });
    document.documentElement.lang = lang === "en" ? "en" : "sw";
    refreshThemeLabels();
    if (resultSummaryEl && resultSummaryEl.dataset.idle === "1") {
      resultSummaryEl.innerHTML = t("result_summary_idle");
    }
    var comboFirst = document.querySelector("#combination option[value='']");
    if (comboFirst) comboFirst.textContent = t("input_combination_ph");
  }

  function refreshThemeLabels() {
    var theme = document.body.dataset.theme === "light" ? "light" : "dark";
    var label = theme === "light" ? t("theme_dark_label") : t("theme_light_label");
    themeLabels.forEach(function (el) {
      el.textContent = label;
    });
  }

  function setUiLang(lang) {
    document.body.setAttribute("data-ui-lang", lang === "en" ? "en" : "sw");
    localStorage.setItem("mwongozo-ui-lang", lang === "en" ? "en" : "sw");
    document.querySelectorAll("[data-set-lang]").forEach(function (btn) {
      btn.classList.toggle("is-active", btn.getAttribute("data-set-lang") === (lang === "en" ? "en" : "sw"));
    });
    applyI18n();
    try {
      renderHomeDashboard();
    } catch (_e) {}
    try {
      initFabChatLabelAnimation();
    } catch (_e) {}
    try {
      initNewsPortfolio();
      initScrollMotion();
    } catch (_e) {}
    if (resultsEl && resultsEl.querySelector(".results-bundle")) {
      try {
        renderResultsPageTable();
      } catch (_e) {}
    }
    if (typeof window.refreshHelpLang === "function") window.refreshHelpLang();
    var dockQuick = document.getElementById("chatDockQuick");
    if (dockQuick && window.SamChat && window.__samDock && window.__samDock.messenger) {
      window.SamChat.renderDockQuick(dockQuick, function (topicId) {
        window.__samDock.messenger.replyFromTopicId(topicId);
      });
    }
  }

  var HERO_BG = {
    "hero-slide--1": { url: "/static/hero/1.jpg", pos: "center 30%" },
    "hero-slide--2": { url: "/static/hero/2.jpg", pos: "center 20%" },
    "hero-slide--3": { url: "/static/hero/3.jpg", pos: "center 35%" },
    "hero-slide--4": { url: "/static/hero/4.jpg", pos: "center 25%" },
    "hero-slide--5": { url: "/static/hero/5.jpg", pos: "center 15%" },
    "hero-slide--6": { url: "/static/hero/6.jpg", pos: "center 25%" },
    "hero-slide--7": { url: "/static/hero/7.jpg", pos: "center 20%" },
  };

  function heroSlideMeta(slide) {
    for (var i = 0; i < slide.classList.length; i++) {
      var cls = slide.classList[i];
      if (HERO_BG[cls]) return HERO_BG[cls];
    }
    return null;
  }

  function loadHeroSlideBg(slide) {
    if (!slide || slide.dataset.bgLoaded === "1") return;
    var meta = heroSlideMeta(slide);
    if (!meta) return;
    slide.dataset.bgLoaded = "1";
    slide.style.backgroundImage = 'url("' + meta.url + '")';
    slide.style.backgroundPosition = meta.pos;
    slide.classList.add("is-bg-ready");
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
      loadHeroSlideBg(slides[idx]);
      var nxt = slides[(idx + 1) % slides.length];
      if (nxt) setTimeout(function () { loadHeroSlideBg(nxt); }, 400);
    }
    go(0);
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!reduce) {
      setInterval(function () {
        go(idx + 1);
      }, 9600);
    }
  }

  function initLazyMedia() {
    var nodes = document.querySelectorAll("[data-bg]");
    if (!nodes.length) return;
    function applyBg(el) {
      if (el.dataset.bgApplied === "1") return;
      var url = el.getAttribute("data-bg");
      if (!url) return;
      el.dataset.bgApplied = "1";
      el.style.backgroundImage = 'url("' + url + '")';
      el.style.backgroundSize = "cover";
      el.style.backgroundPosition = "center";
    }
    if (!("IntersectionObserver" in window)) {
      nodes.forEach(applyBg);
      return;
    }
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          applyBg(entry.target);
          io.unobserve(entry.target);
        });
      },
      { rootMargin: "120px 0px", threshold: 0.01 }
    );
    nodes.forEach(function (el) {
      el.classList.add("is-lazy-media");
      io.observe(el);
    });
  }

  function initPageEntrance() {
    var landing = document.getElementById("landingView");
    if (!landing || landing.classList.contains("hidden")) return;
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) return;
    landing.classList.add("landing--enter");
    requestAnimationFrame(function () {
      landing.classList.add("landing--enter-go");
    });
    setTimeout(function () {
      landing.classList.remove("landing--enter", "landing--enter-go");
    }, 1200);
  }

  function tagScrollMotionTargets() {
    var landing = document.getElementById("landingView");
    var dashboard = document.getElementById("dashboardShell");

    function mark(el, delayMs) {
      if (!el || el.classList.contains("sr")) return;
      if (el.closest('[data-panel="assistant"]')) return;
      el.classList.add("sr");
      if (delayMs != null) el.style.setProperty("--sr-delay", delayMs + "ms");
    }

    function stagger(parent, childSel) {
      if (!parent) return;
      if (parent.closest('[data-panel="assistant"]')) return;
      parent.classList.add("sr-stagger");
      var kids = parent.querySelectorAll(childSel);
      kids.forEach(function (child, i) {
        child.classList.add("sr-child");
        child.style.setProperty("--sr-i", String(i));
      });
    }

    if (landing) {
      mark(landing.querySelector(".landing-footer"), 40);

      var featSec = landing.querySelector(".landing-features");
      if (featSec) {
        mark(featSec.querySelector(".sectors-title"), 0);
        stagger(featSec.querySelector(".landing-feature-grid"), ".landing-feat-card");
      }

      var newsSec = landing.querySelector(".news-portfolio-section");
      if (newsSec) {
        mark(newsSec.querySelector(".news-portfolio-head"), 0);
        stagger(newsSec.querySelector(".news-portfolio-scroll"), ".news-portfolio-card");
      }

      var secSec = landing.querySelector(".sectors-section");
      if (secSec) {
        mark(secSec.querySelector(".sectors-title"), 0);
        stagger(secSec.querySelector(".sectors-grid"), ".sector-card");
      }

      stagger(landing.querySelector(".landing-stats"), ".stat-card");
      stagger(landing.querySelector(".feature-grid"), ".feature-card");
    }

    if (dashboard) {
      dashboard.querySelectorAll(".dashboard-action").forEach(function (el, i) {
        mark(el, (i % 6) * 70);
      });
      dashboard.querySelectorAll("[data-panel]:not(.hidden) .card").forEach(function (el, i) {
        if (el.closest('[data-panel="assistant"]')) return;
        mark(el, (i % 4) * 60);
      });
      var dirPanel = dashboard.querySelector('[data-panel="directory"]');
      if (dirPanel) {
        mark(dirPanel.querySelector(".dir-top-bar"), 0);
        mark(dirPanel.querySelector(".dir-view-tabs"), 50);
        mark(dirPanel.querySelector("#dirInstitutionsPanel .dir-toolbar"), 80);
        mark(dirPanel.querySelector("#dirProgrammesPanel .dir-toolbar"), 60);
      }
      var loanPanel = dashboard.querySelector('[data-panel="loan"]');
      if (loanPanel) {
        mark(loanPanel.querySelector(".loan-topbar"), 0);
        loanPanel.querySelectorAll(".card").forEach(function (el, i) {
          mark(el, (i % 5) * 55);
        });
      }
    }
  }

  var scrollMotionObserver = null;

  function revealScrollNode(node) {
    if (!node) return;
    node.classList.add("is-visible", "is-revealed");
  }

  function hideScrollNode(node) {
    if (!node) return;
    node.classList.remove("is-visible", "is-revealed");
  }

  function initScrollMotion() {
    tagScrollMotionTargets();

    var nodes = document.querySelectorAll(".sr, .sr-stagger");
    if (!nodes.length) return;

    if (!("IntersectionObserver" in window)) {
      nodes.forEach(revealScrollNode);
      return;
    }

    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) {
      nodes.forEach(revealScrollNode);
      return;
    }

    if (scrollMotionObserver) {
      scrollMotionObserver.disconnect();
    }

    scrollMotionObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            revealScrollNode(entry.target);
          } else {
            hideScrollNode(entry.target);
          }
        });
      },
      {
        threshold: [0, 0.08, 0.15],
        rootMargin: "0px 0px -6% 0px",
      }
    );

    nodes.forEach(function (node) {
      scrollMotionObserver.observe(node);
    });
  }

  function refreshScrollMotionSoon() {
    window.requestAnimationFrame(function () {
      initScrollMotion();
    });
  }

  function initScrollReveal() {
    initScrollMotion();
  }

  var newsPortfolioAutoTimer = null;

  function initNewsPortfolio() {
    var scroll = document.getElementById("newsPortfolioScroll");
    var prevBtn = document.getElementById("newsScrollPrev");
    var nextBtn = document.getElementById("newsScrollNext");
    var items = window.MWONGOZO_NEWS;
    if (!scroll || !items || !items.length) return;

    var lang = getUiLang();
    var readMore = lang === "en" ? "Read more" : "Soma zaidi";

    scroll.innerHTML = items
      .map(function (item, i) {
        var title = lang === "en" ? item.title_en : item.title_sw;
        var desc = lang === "en" ? item.desc_en : item.desc_sw;
        var href = item.link || "#";
        var external = href.indexOf("http") === 0;
        var tagCls =
          item.tag === "loan"
            ? "loan"
            : item.tag === "results"
              ? "results"
              : item.tag === "guide"
                ? "guide"
                : "tcu";
        return (
          '<a class="news-portfolio-card sr-child" role="listitem" href="' +
          escapeHtmlAttr(href) +
          '"' +
          (external ? ' target="_blank" rel="noopener noreferrer"' : "") +
          '">' +
          '<div class="news-portfolio-card__media">' +
          '<img src="' +
          escapeHtmlAttr(item.image) +
          '" data-remote="' +
          escapeHtmlAttr(item.imageRemote || "") +
          '" alt="' +
          escapeHtml(item.category) +
          '" width="400" height="168" loading="lazy" decoding="async" />' +
          '<span class="news-portfolio-card__tag news-portfolio-card__tag--' +
          escapeHtmlAttr(tagCls) +
          '">' +
          escapeHtml(item.category) +
          "</span></div>" +
          '<div class="news-portfolio-card__body">' +
          '<div class="news-portfolio-card__meta"><time datetime="' +
          escapeHtmlAttr(String(item.date)) +
          '">' +
          escapeHtml(String(item.date)) +
          "</time></div>" +
          "<h3>" +
          escapeHtml(title) +
          "</h3>" +
          "<p>" +
          escapeHtml(desc) +
          "</p>" +
          '<span class="news-portfolio-card__link">' +
          readMore +
          ' <i class="fa-solid fa-arrow-right" aria-hidden="true"></i></span>' +
          "</div></a>"
        );
      })
      .join("");

    scroll.querySelectorAll("img[data-remote]").forEach(function (img) {
      img.addEventListener("error", function () {
        var remote = img.getAttribute("data-remote");
        if (!remote || img.dataset.fellback === "1") return;
        img.dataset.fellback = "1";
        img.src = remote;
      });
    });

    function scrollStep(dir) {
      var card = scroll.querySelector(".news-portfolio-card");
      var gap = 18;
      var amount = card ? card.offsetWidth + gap : 318;
      scroll.scrollBy({ left: dir * amount, behavior: "smooth" });
    }

    if (prevBtn && !prevBtn.dataset.bound) {
      prevBtn.dataset.bound = "1";
      prevBtn.addEventListener("click", function () { scrollStep(-1); });
    }
    if (nextBtn && !nextBtn.dataset.bound) {
      nextBtn.dataset.bound = "1";
      nextBtn.addEventListener("click", function () { scrollStep(1); });
    }

    scroll.classList.add("sr-stagger");
    scroll.querySelectorAll(".news-portfolio-card").forEach(function (card, i) {
      card.classList.add("sr-child");
      card.style.setProperty("--sr-i", String(i));
    });

    if (newsPortfolioAutoTimer) clearInterval(newsPortfolioAutoTimer);
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!reduce) {
      newsPortfolioAutoTimer = setInterval(function () {
        if (scroll.matches(":hover")) return;
        var max = scroll.scrollWidth - scroll.clientWidth - 2;
        if (max <= 0) return;
        if (scroll.scrollLeft >= max) scroll.scrollTo({ left: 0, behavior: "smooth" });
        else scrollStep(1);
      }, 4200);
    }
  }

  function initPartnerMarquee() {
    var inner = document.getElementById("partnerMarqueeInner");
    var partners = window.MWONGOZO_PARTNERS;
    if (!inner || !partners || !partners.length) return;
    function buildSet(eager) {
      return partners
        .map(function (p, i) {
          var src = "/static/partners/" + p.file;
          var fb = p.fallbackFile ? "/static/partners/" + p.fallbackFile : "";
          var alt = escapeHtml(p.name);
          var load = eager && i < 6 ? "eager" : "lazy";
          var fetchp = eager && i < 6 ? ' fetchpriority="high"' : "";
          var label = escapeHtml(p.label || p.name || "");
          return (
            '<a class="partner-marquee__item" href="' +
            escapeHtmlAttr(p.url) +
            '" target="_blank" rel="noopener noreferrer" title="' +
            alt +
            '"><span class="partner-marquee__unit">' +
            '<span class="partner-marquee__ring">' +
            '<img src="' +
            escapeHtmlAttr(src) +
            '"' +
            (fb ? ' data-fallback="' + escapeHtmlAttr(fb) + '"' : "") +
            ' alt="' +
            alt +
            '" width="40" height="40" loading="' +
            load +
            '"' +
            fetchp +
            ' decoding="async" /></span>' +
            '<span class="partner-marquee__name">' +
            label +
            "</span></span></a>"
          );
        })
        .join("");
    }
    inner.innerHTML = buildSet(true) + buildSet(false);
    inner.querySelectorAll("img[data-fallback]").forEach(function (img) {
      img.addEventListener("error", function onErr() {
        var fb = img.getAttribute("data-fallback");
        if (!fb || img.dataset.fellback === "1") return;
        img.dataset.fellback = "1";
        img.src = fb;
      });
    });
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!reduce) {
      inner.classList.add("is-running");
    } else {
      inner.style.flexWrap = "wrap";
      inner.style.justifyContent = "center";
      inner.style.width = "100%";
    }
  }

  var fabLabelAnimSeq = 0;

  function initFabChatLabelAnimation() {
    var label = document.getElementById("fabChatLabel");
    var fab = document.getElementById("fabChat");
    if (!label || !fab) return;
    if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    var phrasesSw = ["Tupige story", "Uliza SAM...", "Msaada wa haraka", "NECTA · TCU · HESLB"];
    var phrasesEn = ["Let's chat", "Ask SAM...", "Quick help", "NECTA · TCU · HESLB"];
    var mySeq = ++fabLabelAnimSeq;
    var idx = 0;

    function phrases() {
      return getUiLang() === "en" ? phrasesEn : phrasesSw;
    }

    function typeIn(text, done) {
      var i = 0;
      var tid = setInterval(function () {
        if (mySeq !== fabLabelAnimSeq) {
          clearInterval(tid);
          return;
        }
        i += 1;
        label.textContent = text.slice(0, i);
        if (fab) fab.setAttribute("aria-label", label.textContent);
        if (i >= text.length) {
          clearInterval(tid);
          if (typeof done === "function") setTimeout(done, 1700);
        }
      }, 42);
    }

    function erase(done) {
      var tid = setInterval(function () {
        if (mySeq !== fabLabelAnimSeq) {
          clearInterval(tid);
          return;
        }
        var t = label.textContent || "";
        if (!t.length) {
          clearInterval(tid);
          if (typeof done === "function") done();
          return;
        }
        label.textContent = t.slice(0, -1);
        if (fab) fab.setAttribute("aria-label", label.textContent || "Chat");
      }, 28);
    }

    function loop() {
      if (mySeq !== fabLabelAnimSeq) return;
      var list = phrases();
      var phrase = list[idx % list.length];
      idx += 1;
      typeIn(phrase, function () {
        erase(loop);
      });
    }

    label.textContent = "";
    loop();
  }

  function initFabChatDock() {
    if (typeof window.SamChat !== "undefined" && window.SamChat.initDock) {
      window.__samDock = window.SamChat.initDock();
      return;
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
      refreshScrollMotionSoon();
    });
  }

  function goToLanding() {
    runStageTransition(function () {
      if (mainWrapInner) mainWrapInner.classList.remove("wrap-inner--reco-focus");
      if (dashboardShell) dashboardShell.classList.remove("dashboard--results-mode");
      if (dashboardShell) dashboardShell.classList.add("hidden");
      if (landingView) landingView.classList.remove("hidden");
      scrollToTopAnimated();
      initLandingMetaAnimation();
      refreshScrollMotionSoon();
    });
  }

  function clearPanelScrollMotion(panelId) {
    var panel = document.querySelector('[data-panel="' + panelId + '"]');
    if (!panel) return;
    panel.querySelectorAll(".sr, .sr-stagger, .sr-child, .scroll-reveal").forEach(function (el) {
      el.classList.remove("sr", "sr-stagger", "sr-child", "scroll-reveal", "is-visible", "is-revealed");
      el.style.removeProperty("--sr-delay");
      el.style.removeProperty("--sr-i");
      el.style.opacity = "";
      el.style.transform = "";
    });
  }

  function revealPanelMotion(panelId) {
    var panel = document.querySelector('[data-panel="' + panelId + '"]');
    if (!panel) return;
    panel.querySelectorAll(".sr, .sr-stagger, .sr-child, .scroll-reveal").forEach(revealScrollNode);
  }

  function scrollActivePanelToTop(panelId) {
    var panel = document.querySelector('[data-panel="' + panelId + '"]');
    if (!panel || panel.classList.contains("hidden")) return;
    if (panelId === "assistant") {
      scrollHelpPanelIntoView();
      return;
    }
    if (panelId === "loan") {
      scrollLoanPanelIntoView();
      return;
    }
    window.scrollTo({ top: 0, left: 0, behavior: "auto" });
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
    var appMain = document.querySelector(".app-main");
    if (appMain) appMain.scrollTop = 0;
    requestAnimationFrame(function () {
      window.scrollTo({ top: 0, left: 0, behavior: "auto" });
      if (appMain) appMain.scrollTop = 0;
    });
  }

  function scrollHelpPanelIntoView() {
    var panel = document.querySelector('[data-panel="assistant"]');
    if (!panel || panel.classList.contains("hidden")) return;
    var anchor = panel.querySelector(".help-hero") || panel;
    var topInset =
      (parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--topbar-h")) || 52) +
      (parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--topbar-offset")) || 10) +
      12;

    function resetScrollers() {
      window.scrollTo({ top: 0, left: 0, behavior: "auto" });
      document.documentElement.scrollTop = 0;
      document.body.scrollTop = 0;
      if (dashboardShell) dashboardShell.scrollTop = 0;
      var appShell = document.querySelector(".app-shell");
      if (appShell) appShell.scrollTop = 0;
      var appMain = document.querySelector(".app-main");
      if (appMain) appMain.scrollTop = 0;
      var chatLog = document.getElementById("chatMessages");
      if (chatLog) chatLog.scrollTop = 0;
    }

    function alignToTop() {
      var rect = anchor.getBoundingClientRect();
      var targetY = window.scrollY + rect.top - topInset;
      if (Math.abs(rect.top - topInset) > 2) {
        window.scrollTo({ top: Math.max(0, targetY), left: 0, behavior: "auto" });
      }
    }

    resetScrollers();
    requestAnimationFrame(function () {
      alignToTop();
      requestAnimationFrame(function () {
        resetScrollers();
        alignToTop();
      });
    });
    setTimeout(function () {
      alignToTop();
    }, 80);
    setTimeout(function () {
      alignToTop();
    }, 220);
  }

  function scrollLoanPanelIntoView() {
    var panel = document.querySelector('[data-panel="loan"]');
    if (!panel || panel.classList.contains("hidden")) return;
    var anchor = panel.querySelector(".loan-topbar") || panel;
    var topInset =
      (parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--topbar-h")) || 52) +
      (parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--topbar-offset")) || 10) +
      12;

    function resetScrollers() {
      window.scrollTo({ top: 0, left: 0, behavior: "auto" });
      document.documentElement.scrollTop = 0;
      document.body.scrollTop = 0;
      if (dashboardShell) dashboardShell.scrollTop = 0;
      var appMain = document.querySelector(".app-main");
      if (appMain) appMain.scrollTop = 0;
    }

    function alignToTop() {
      var rect = anchor.getBoundingClientRect();
      var targetY = window.scrollY + rect.top - topInset;
      if (Math.abs(rect.top - topInset) > 2) {
        window.scrollTo({ top: Math.max(0, targetY), left: 0, behavior: "auto" });
      }
    }

    resetScrollers();
    requestAnimationFrame(function () {
      alignToTop();
      requestAnimationFrame(alignToTop);
    });
    setTimeout(alignToTop, 80);
  }

  function measureHelpPanelLayout() {
    scrollHelpPanelIntoView();
  }

  function formatInstitutionCellHTML(rec) {
    var name = String((rec.programme && rec.programme.institution_name) || "").trim();
    var code = String((rec.programme && rec.programme.institution_code) || "").trim();
    if (!name && code) {
      return '<span class="rec-inst-line">' + escapeHtml(code) + "</span>";
    }
    if (!name) {
      return '<span class="rec-inst-line">—</span>';
    }
    if (!code || name.toUpperCase().indexOf(code.toUpperCase()) !== -1) {
      return '<span class="rec-inst-line rec-inst-line--full">' + escapeHtml(name) + "</span>";
    }
    return (
      '<span class="rec-inst-line rec-inst-line--full">' +
      '<span class="rec-inst-name">' +
      escapeHtml(name) +
      '</span> <span class="rec-inst-code">(' +
      escapeHtml(code) +
      ")</span></span>"
    );
  }

  function buildRecColumnHeadersHTML(L) {
    return (
      '<div class="rec-column-headers" role="row">' +
      '<span class="rec-column-headers__cell reco-col-num">' +
      escapeHtml(L.results_col_rank) +
      '</span><span class="rec-column-headers__cell reco-col-inst">' +
      escapeHtml(L.results_col_inst) +
      '</span><span class="rec-column-headers__cell reco-col-prog">' +
      escapeHtml(L.results_col_prog) +
      '</span><span class="rec-column-headers__cell reco-col-region">' +
      escapeHtml(L.results_col_region) +
      '</span><span class="rec-column-headers__cell reco-col-pts">' +
      escapeHtml(L.results_col_pts) +
      '</span><span class="rec-column-headers__cell reco-col-conf">' +
      escapeHtml(L.results_col_conf) +
      '</span><span class="rec-column-headers__cell reco-col-type">' +
      escapeHtml(L.results_col_type) +
      '</span><span class="rec-column-headers__cell reco-col-actions">' +
      escapeHtml(L.results_col_actions) +
      "</span></div>"
    );
  }

  function navigateDash(panel) {
    var showPanel = "main";
    if (panel === "home") showPanel = "home";
    else if (panel === "saved") showPanel = "saved";
    else if (panel === "directory") showPanel = "directory";
    else if (panel === "loan") showPanel = "loan";
    else if (panel === "assistant") showPanel = "assistant";
    else showPanel = "main";
    window.scrollTo(0, 0);
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
    document.querySelectorAll("[data-panel]").forEach(function (p) {
      var active = p.getAttribute("data-panel") === showPanel;
      p.classList.toggle("hidden", !active);
      p.style.display = active ? "" : "none";
    });
    document.body.classList.toggle("dash-panel-assistant", showPanel === "assistant");
    document.body.classList.toggle("dash-panel-results", panel === "results");
    document.querySelectorAll("[data-dash-nav]").forEach(function (btn) {
      btn.classList.toggle("is-active", btn.getAttribute("data-dash-nav") === panel);
    });
    if (panel === "input") showInputView();
    if (panel === "results") showResultsView();
    if (panel === "directory" && directoryBody && !directoryBody.dataset.loaded) loadDirectoryData();
    if (panel === "home") loadMetaSummary();
    if (panel === "saved") {
      renderSavedPage();
      if (isLoggedIn()) syncAllSavedFromServer();
    }
    if (showPanel === "assistant") clearPanelScrollMotion("assistant");
    if (showPanel !== "main") scrollActivePanelToTop(showPanel);
    revealPanelMotion(showPanel);
    refreshScrollMotionSoon();
    requestAnimationFrame(function () {
      if (showPanel === "assistant") clearPanelScrollMotion("assistant");
      if (showPanel !== "main") scrollActivePanelToTop(showPanel);
    });
    if (panel === "loan") {
      if (typeof window.initLoanTracker === "function") window.initLoanTracker();
      scrollLoanPanelIntoView();
      setTimeout(scrollLoanPanelIntoView, 100);
    }
    if (panel === "assistant" && typeof window.initHelpPanel === "function") window.initHelpPanel();
    if (showPanel === "assistant") {
      scrollHelpPanelIntoView();
      requestAnimationFrame(function () {
        scrollHelpPanelIntoView();
      });
      setTimeout(scrollHelpPanelIntoView, 120);
    }
  }

  window.scrollHelpPanelIntoView = scrollHelpPanelIntoView;

  var landMetaAnimSeq = 0;

  function loadMetaSummary() {
    if (typeof MwongozoApi === "undefined") return;
    MwongozoApi.fetchJson("/meta", { method: "GET" })
      .then(function (m) {
        homeMeta = m || homeMeta;
        if (metaStatsEl) {
          metaStatsEl.innerHTML =
            '<div class="stat-card glass"><span class="stat-value">' +
            (m.programmes_loaded || "—") +
            '</span><span class="stat-label">Programme zilizopakiwa</span></div>' +
            '<div class="stat-card glass"><span class="stat-value">' +
            (m.institutions_covered && m.institutions_covered.length) +
            '</span><span class="stat-label">Taasisi</span></div>';
        }
        renderHomeDashboard();
      })
      .catch(function () {
        if (metaStatsEl) metaStatsEl.innerHTML = '<p class="muted small">' + escapeHtml(t("meta_load_fail")) + "</p>";
        renderHomeDashboard();
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

  function parseHeroStatDisplay(text) {
    var raw = String(text || "").trim();
    var m = raw.match(/^(\d+)\s*(\+|%)?$/);
    if (!m) return { value: 0, suffix: raw };
    return { value: parseInt(m[1], 10), suffix: m[2] || "" };
  }

  function animateHeroStatEl(el, target, suffix, ms) {
    if (!el) return;
    target = Math.max(0, Math.floor(Number(target) || 0));
    suffix = suffix || "";
    var start = performance.now();
    function frame(t) {
      var u = Math.min(1, (t - start) / ms);
      var eased = 1 - (1 - u) * (1 - u);
      el.textContent = String(Math.round(target * eased)) + suffix;
      if (u < 1) requestAnimationFrame(frame);
      else el.textContent = String(target) + suffix;
    }
    requestAnimationFrame(frame);
  }

  var heroStatsCycleTimer = null;

  function initHeroStatsCycle() {
    var nums = document.querySelectorAll("[data-hero-stat]");
    if (!nums.length) return;
    if (heroStatsCycleTimer) clearInterval(heroStatsCycleTimer);

    function applyFromMeta(meta) {
      meta = meta || {};
      var instN = Array.isArray(meta.institutions_covered) ? meta.institutions_covered.length : 60;
      var progN = Number(meta.programmes_loaded) || 400;
      var map = {
        institutions: { value: instN, suffix: "+" },
        programmes: { value: progN, suffix: "+" },
        tcu: { value: 100, suffix: "%" },
        free: null,
      };
      nums.forEach(function (el) {
        var key = el.getAttribute("data-stat-key") || "";
        if (key === "free") return;
        var spec = map[key];
        if (!spec) {
          var parsed = parseHeroStatDisplay(el.textContent);
          animateHeroStatEl(el, parsed.value, parsed.suffix, 1100);
          return;
        }
        animateHeroStatEl(el, spec.value, spec.suffix, 1200);
      });
    }

    function pulse() {
      var fetchMeta =
        typeof MwongozoApi !== "undefined"
          ? MwongozoApi.fetchJson("/meta", { method: "GET" })
          : fetch("/meta").then(function (r) {
              return r.json();
            });
      fetchMeta.then(applyFromMeta).catch(function () {
        nums.forEach(function (el) {
          var p = parseHeroStatDisplay(el.textContent);
          animateHeroStatEl(el, p.value, p.suffix, 900);
        });
      });
    }

    pulse();
    heroStatsCycleTimer = setInterval(pulse, 14000);
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
        homeMeta = m || homeMeta;
        var p = Number(m.programmes_loaded) || 0;
        var ins = Array.isArray(m.institutions_covered) ? m.institutions_covered.length : 0;
        animateCountTo(nPro, p, 900);
        animateCountTo(nInst, ins, 900);
        renderHomeDashboard();
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

  function instOwnership(code) {
    var inst = institutionsByCode[code];
    return (inst && inst.ownership) || "public";
  }

  function setDirectoryView(view) {
    directoryView = view === "programmes" ? "programmes" : "institutions";
    document.querySelectorAll("[data-dir-view]").forEach(function (btn) {
      var on = btn.getAttribute("data-dir-view") === directoryView;
      btn.classList.toggle("is-active", on);
      btn.setAttribute("aria-selected", on ? "true" : "false");
    });
    if (dirInstitutionsPanel) dirInstitutionsPanel.classList.toggle("hidden", directoryView !== "institutions");
    if (dirProgrammesPanel) dirProgrammesPanel.classList.toggle("hidden", directoryView !== "programmes");
    if (directoryView === "institutions") {
      renderUniversitiesGrid();
      revealUniversityCards();
    } else {
      renderDirectoryTable();
    }
  }

  function mergeLiveSummaries(summaries) {
    if (!summaries || !institutionList.length) return 0;
    var updated = 0;
    institutionList = institutionList.map(function (inst) {
      var live = summaries[inst.code];
      if (!live || live.status !== "ok" || !(live.programme_count > 0)) return inst;
      updated += 1;
      var merged = Object.assign({}, inst, {
        programme_count: live.programme_count,
        programme_preview: (live.programmes || []).slice(0, 5),
        programme_source: "official",
        source_label: live.source_label || "Tovuti rasmi",
        programmes_url: live.source_url || inst.programmes_url,
        live_fetched_at: live.fetched_at,
      });
      institutionsByCode[inst.code] = merged;
      return merged;
    });
    return updated;
  }

  function enrichInstitutionsFromOfficialSites() {
    if (typeof MwongozoApi === "undefined") return Promise.resolve(0);
    return MwongozoApi.fetchJson("/institutions/live-summaries?refresh=15", { method: "GET" })
      .then(function (payload) {
        var n = mergeLiveSummaries((payload && payload.summaries) || {});
        if (directoryView === "institutions") {
          renderUniversitiesGrid();
          pulseUnivGridRefresh();
        }
        var Lm = I18N[getUiLang()] || I18N.sw;
        if (n > 0) toast((Lm.dir_live_partial || "Updated from official sites") + " (" + n + ")", "success");
        return n;
      })
      .catch(function () {
        return 0;
      });
  }

  function loadDirectoryData() {
    if (!directoryBody || typeof MwongozoApi === "undefined") return;
    directoryBody.innerHTML =
      '<tr><td colspan="5" class="muted">Inapakia orodha ya programme…</td></tr>';
    if (univGrid)
      univGrid.innerHTML = '<p class="muted small">' + escapeHtml(t("dir_loading")) + "</p>";
    Promise.all([
      MwongozoApi.fetchJson("/programmes", { method: "GET" }).catch(function () {
        return [];
      }),
      MwongozoApi.fetchJson("/institutions?source=catalogue", { method: "GET" }).catch(function () {
        return MwongozoApi.fetchJson("/institutions", { method: "GET" }).catch(function () {
          return [];
        });
      }),
    ]).then(function (pair) {
      var programmes = pair[0] || [];
      var insts = pair[1] || [];
      institutionsByCode = {};
      institutionList = Array.isArray(insts) ? insts.slice() : [];
      insts.forEach(function (i) {
        institutionsByCode[i.code] = i;
      });
      directoryRows = Array.isArray(programmes) ? programmes : [];
      directoryBody.dataset.loaded = "1";
      if (!institutionList.length && !directoryRows.length) {
        if (directoryBody)
          directoryBody.innerHTML =
            '<tr><td colspan="5" class="muted">Hakuna data — angalia muunganisho wa server.</td></tr>';
        if (univGrid)
          univGrid.innerHTML = '<p class="muted small">' + escapeHtml(t("dir_no_data")) + "</p>";
        toast("Orodha haipatikani kwa sasa", "warn");
        return;
      }
      populateDirectoryFilters();
      populateUnivFilters();
      setDirectoryView(directoryView);
      toast("Orodha ya vyuo imepakuliwa", "success");
      var cachedLive = MwongozoApi.fetchJson("/institutions/live-summaries", { method: "GET" }).catch(function () {
        return { summaries: {} };
      });
      cachedLive.then(function (payload) {
        mergeLiveSummaries((payload && payload.summaries) || {});
        if (directoryView === "institutions") renderUniversitiesGrid();
      });
      enrichInstitutionsFromOfficialSites();
    });
  }

  function populateUnivFilters() {
    if (!univRegion) return;
    var regions = [
      ...new Set(institutionList.map(function (i) {
        return i.region;
      }).filter(Boolean)),
    ].sort();
    var regHtml =
      '<option value="all">' +
      escapeHtml((I18N[getUiLang()] || I18N.sw).dir_all_regions) +
      "</option>" +
      regions
        .map(function (r) {
          return '<option value="' + escapeHtmlAttr(r) + '">' + escapeHtml(r) + "</option>";
        })
        .join("");
    univRegion.innerHTML = regHtml;
  }

  function filteredInstitutions() {
    var q = (univSearch && univSearch.value.trim().toLowerCase()) || "";
    var reg = (univRegion && univRegion.value) || "all";
    var own = (univOwnership && univOwnership.value) || "all";
    var kind = (univKind && univKind.value) || "all";
    return institutionList.filter(function (i) {
      var hay = [i.name, i.code, i.city, i.region, i.ownership, i.kind].join(" ").toLowerCase();
      var okQ = !q || hay.indexOf(q) !== -1;
      var okR = reg === "all" || String(i.region) === reg;
      var okO = own === "all" || String(i.ownership) === own;
      var okK = kind === "all" || String(i.kind) === kind;
      return okQ && okR && okO && okK;
    });
  }

  function ownershipLabel(own) {
    var Lm = I18N[getUiLang()] || I18N.sw;
    if (own === "private") return Lm.dir_private;
    return Lm.dir_public;
  }

  function kindLabel(kind) {
    var Lm = I18N[getUiLang()] || I18N.sw;
    if (kind === "university") return Lm.dir_kind_univ;
    if (kind === "college") return Lm.dir_kind_college;
    return Lm.dir_kind_other;
  }

  function institutionSummary(inst) {
    var lang = getUiLang();
    if (lang === "en" && inst.summary_en) return inst.summary_en;
    return inst.summary || "";
  }

  function truncateSummary(text, maxLen) {
    if (!text) return "";
    maxLen = maxLen || 118;
    if (text.length <= maxLen) return text;
    return text.slice(0, maxLen).replace(/\s+\S*$/, "") + "…";
  }

  function ensureInstitutionOption(code) {
    if (!directoryInstitution || !code || code === "all") return;
    var exists = false;
    for (var i = 0; i < directoryInstitution.options.length; i++) {
      if (directoryInstitution.options[i].value === code) {
        exists = true;
        break;
      }
    }
    if (!exists && institutionsByCode[code]) {
      var opt = document.createElement("option");
      opt.value = code;
      opt.textContent = institutionsByCode[code].name || code;
      directoryInstitution.appendChild(opt);
    }
  }

  function openInstitutionProgrammes(code) {
    if (!code) return;
    ensureInstitutionOption(code);
    if (directoryInstitution) directoryInstitution.value = code;
    setDirectoryView("programmes");
    window.requestAnimationFrame(function () {
      var panel = dirProgrammesPanel || document.getElementById("dirProgrammesPanel");
      if (panel && panel.scrollIntoView) panel.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  function programmeCountLabel(inst, Lm) {
    if (inst && inst.programme_source === "official")
      return Lm.dir_prog_official || "programme (tovuti rasmi)";
    return Lm.dir_prog_verified || "programme (TCU)";
  }

  function openUnivModal(inst) {
    if (!univModal || !inst) return;
    var Lm = I18N[getUiLang()] || I18N.sw;
    var lang = getUiLang();
    var full = institutionSummary(inst);
    var progN = inst.programme_count != null ? inst.programme_count : 0;
    univModalInstCode = inst.code || "";
    if (univModalTitle) univModalTitle.textContent = inst.name || "";
    if (univModalMeta)
      univModalMeta.textContent =
        (inst.city || "") +
        " · " +
        (inst.region || "") +
        " · " +
        progN +
        " " +
        programmeCountLabel(inst, Lm);
    if (univModalBody) univModalBody.textContent = full;
    if (univModalSource)
      univModalSource.textContent = inst.source_label
        ? (lang === "en" ? "Source: " : "Chanzo: ") + inst.source_label
        : "";
    if (univModalPreview) {
      var preview = Array.isArray(inst.programme_preview) ? inst.programme_preview : [];
      var extra = progN > preview.length ? " +" + (progN - preview.length) + " " + (Lm.dir_preview_more || "") : "";
      univModalPreview.innerHTML = preview
        .map(function (name) {
          return "<li>" + escapeHtml(name) + "</li>";
        })
        .join("");
      if (extra && preview.length)
        univModalPreview.innerHTML += '<li class="muted small">' + escapeHtml(extra.trim()) + "</li>";
    }
    var web = inst.programmes_url || inst.website || "";
    if (univModalWebLink) {
      if (web) {
        univModalWebLink.href = web;
        univModalWebLink.classList.remove("hidden");
      } else univModalWebLink.classList.add("hidden");
    }
    if (univModalProgBtn) univModalProgBtn.textContent = Lm.dir_view_programmes || "Angalia programme";
    if (inst.programme_source !== "official" && typeof MwongozoApi !== "undefined") {
      MwongozoApi.fetchJson(
        "/institutions/" + encodeURIComponent(inst.code) + "/programmes/live",
        { method: "GET" }
      )
        .then(function (live) {
          if (!live || live.status !== "ok" || !(live.programme_count > 0)) return;
          mergeLiveSummaries({ [inst.code]: live });
          institutionsByCode[inst.code] = institutionList.find(function (x) {
            return x.code === inst.code;
          }) || inst;
          var refreshed = institutionsByCode[inst.code];
          if (univModalBody && refreshed.summary) univModalBody.textContent = institutionSummary(refreshed);
          if (univModalPreview && live.programmes) {
            univModalPreview.innerHTML = live.programmes
              .map(function (name) {
                return "<li>" + escapeHtml(name) + "</li>";
              })
              .join("");
          }
          if (univModalMeta)
            univModalMeta.textContent =
              (refreshed.city || "") +
              " · " +
              (refreshed.region || "") +
              " · " +
              live.programme_count +
              " " +
              programmeCountLabel(refreshed, Lm);
          if (univModalSource) univModalSource.textContent = live.source_label || "";
        })
        .catch(function () {});
    }
    univModal.classList.add("is-open");
    univModal.setAttribute("aria-hidden", "false");
    document.body.classList.add("univ-modal-open");
  }

  function closeUnivModal() {
    if (!univModal) return;
    univModal.classList.remove("is-open");
    univModal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("univ-modal-open");
    univModalInstCode = "";
  }

  function initUnivModal() {
    if (!univModal) return;
    if (univModal.parentElement !== document.body) document.body.appendChild(univModal);
    univModal.querySelectorAll("[data-univ-modal-close]").forEach(function (el) {
      el.addEventListener("click", closeUnivModal);
    });
    if (univModalProgBtn) {
      univModalProgBtn.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        var code = univModalInstCode;
        closeUnivModal();
        openInstitutionProgrammes(code);
      });
    }
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && univModal && univModal.classList.contains("is-open")) closeUnivModal();
    });
  }

  function pulseUnivGridRefresh() {
    if (!univGrid) return;
    univGrid.classList.remove("univ-grid--refresh");
    void univGrid.offsetWidth;
    univGrid.classList.add("univ-grid--refresh");
    window.setTimeout(function () {
      univGrid.classList.remove("univ-grid--refresh");
    }, 400);
  }

  function revealUniversityCards() {
    if (!univGrid) return;
    univGrid.querySelectorAll(".univ-card").forEach(function (card) {
      card.classList.add("is-visible", "is-revealed", "univ-card--ready");
    });
  }

  function revealRecommendationRows() {
    if (!resultsEl) return;
    resultsEl.querySelectorAll(".rec-table tbody tr").forEach(function (row) {
      row.classList.remove("sr");
      row.classList.add("is-visible", "is-revealed", "rec-row--ready");
    });
    var bundle = resultsEl.querySelector(".results-bundle");
    if (bundle) {
      bundle.classList.remove("sr");
    }
  }

  function bindUnivGridEvents() {
    if (!univGrid || univGridDelegated) return;
    univGridDelegated = true;
    univGrid.addEventListener("click", function (e) {
      var moreBtn = e.target.closest("[data-univ-read-more]");
      if (moreBtn) {
        e.preventDefault();
        e.stopPropagation();
        var codeMore = moreBtn.getAttribute("data-univ-read-more") || "";
        var instMore = institutionsByCode[codeMore];
        if (instMore) openUnivModal(instMore);
        return;
      }
      if (e.target.closest("a, button")) return;
      var card = e.target.closest(".univ-card");
      if (!card) return;
      openInstitutionProgrammes(card.getAttribute("data-inst-code") || "");
    });
    univGrid.addEventListener("mousedown", function (e) {
      var card = e.target.closest(".univ-card");
      if (card) card.classList.add("is-active");
    });
    univGrid.addEventListener("mouseup", function () {
      univGrid.querySelectorAll(".univ-card.is-active").forEach(function (c) {
        c.classList.remove("is-active");
      });
    });
    univGrid.addEventListener("mouseleave", function () {
      univGrid.querySelectorAll(".univ-card.is-active").forEach(function (c) {
        c.classList.remove("is-active");
      });
    });
  }

  function scheduleRenderUniversitiesGrid() {
    if (univGridRenderTimer) window.clearTimeout(univGridRenderTimer);
    univGridRenderTimer = window.setTimeout(function () {
      univGridRenderTimer = null;
      renderUniversitiesGrid();
    }, 100);
  }

  function renderUniversitiesGrid() {
    if (!univGrid) return;
    var rows = filteredInstitutions().sort(function (a, b) {
      return (b.programme_count || 0) - (a.programme_count || 0) || String(a.name).localeCompare(String(b.name));
    });
    var Lm = I18N[getUiLang()] || I18N.sw;
    if (univResultCount)
      univResultCount.textContent = rows.length + " " + Lm.dir_univ_count;
    if (!rows.length) {
      univGrid.innerHTML = '<p class="muted small">' + escapeHtml(t("dir_no_match")) + "</p>";
      return;
    }
    univGrid.innerHTML = rows
      .map(function (i, idx) {
        var progN = i.programme_count != null ? i.programme_count : 0;
        var excerpt = truncateSummary(institutionSummary(i), 108);
        var preview = Array.isArray(i.programme_preview) ? i.programme_preview.slice(0, 3) : [];
        var previewHtml = preview
          .map(function (name) {
            return '<span class="univ-card__chip">' + escapeHtml(name) + "</span>";
          })
          .join("");
        if (progN > preview.length && preview.length)
          previewHtml +=
            '<span class="univ-card__chip univ-card__chip--more">+' +
            (progN - preview.length) +
            "</span>";
        var web = i.programmes_url || i.website || "";
        var link = web
          ? '<a class="univ-card__link" href="' +
            escapeHtmlAttr(web) +
            '" target="_blank" rel="noopener" onclick="event.stopPropagation()">' +
            escapeHtml(Lm.dir_official_site || "Tovuti") +
            "</a>"
          : "";
        var officialCls = i.programme_source === "official" ? " univ-card--official" : "";
        return (
          '<article class="univ-card glass' +
          officialCls +
          '" role="listitem" tabindex="0" data-inst-code="' +
          escapeHtmlAttr(i.code) +
          '">' +
          '<div class="univ-card__head">' +
          '<h3 class="univ-card__title">' +
          escapeHtml(i.name) +
          "</h3>" +
          '<span class="univ-card__badge univ-card__badge--' +
          escapeHtmlAttr(i.ownership || "public") +
          '">' +
          escapeHtml(ownershipLabel(i.ownership)) +
          "</span>" +
          "</div>" +
          '<p class="univ-card__meta muted small">' +
          escapeHtml(i.city || "") +
          " · " +
          escapeHtml(i.region || "") +
          "</p>" +
          '<p class="univ-card__excerpt">' +
          escapeHtml(excerpt) +
          "</p>" +
          (previewHtml ? '<div class="univ-card__chips">' + previewHtml + "</div>" : "") +
          '<div class="univ-card__stats">' +
          '<span class="univ-card__stat"><strong>' +
          escapeHtml(String(progN)) +
          "</strong> " +
          escapeHtml(programmeCountLabel(i, Lm)) +
          "</span>" +
          '<span class="univ-card__stat">' +
          escapeHtml(kindLabel(i.kind)) +
          "</span>" +
          "</div>" +
          '<div class="univ-card__foot">' +
          '<button type="button" class="univ-card__more" data-univ-read-more="' +
          escapeHtmlAttr(i.code) +
          '">' +
          escapeHtml(Lm.dir_read_more || "Soma zaidi") +
          "</button>" +
          link +
          "</div>" +
          "</article>"
        );
      })
      .join("");
    bindUnivGridEvents();
    revealUniversityCards();
    refreshScrollMotionSoon();
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
    var categories = [
      ...new Set(directoryRows.map(function (r) {
        return r.category;
      }).filter(Boolean)),
    ].sort();
    var Lm = I18N[getUiLang()] || I18N.sw;
    var regHtml =
      '<option value="all">' +
      escapeHtml(Lm.dir_all_regions) +
      "</option>" +
      regions
        .map(function (r) {
          return '<option value="' + escapeHtmlAttr(r) + '">' + escapeHtml(r) + "</option>";
        })
        .join("");
    var instHtml =
      '<option value="all">' +
      escapeHtml(Lm.dir_all_inst) +
      "</option>" +
      instCodes
        .map(function (c) {
          var name = (institutionsByCode[c] && institutionsByCode[c].name) || c;
          return '<option value="' + escapeHtmlAttr(c) + '">' + escapeHtml(name) + "</option>";
        })
        .join("");
    var catHtml =
      '<option value="all">' +
      escapeHtml(Lm.results_quick_all) +
      "</option>" +
      categories
        .map(function (c) {
          return '<option value="' + escapeHtmlAttr(c) + '">' + escapeHtml(c) + "</option>";
        })
        .join("");
    directoryRegion.innerHTML = regHtml;
    directoryInstitution.innerHTML = instHtml;
    if (directoryCategory) directoryCategory.innerHTML = catHtml;
  }

  function filteredDirectoryRows() {
    var q = (directorySearch && directorySearch.value.trim().toLowerCase()) || "";
    var reg = (directoryRegion && directoryRegion.value) || "all";
    var inst = (directoryInstitution && directoryInstitution.value) || "all";
    var own = (directoryOwnership && directoryOwnership.value) || "all";
    var cat = (directoryCategory && directoryCategory.value) || "all";
    var award = (directoryAward && directoryAward.value) || "all";
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
      var okO = own === "all" || instOwnership(r.institution_code) === own;
      var okC = cat === "all" || String(r.category) === cat;
      var okA = award === "all" || String(r.award_level) === award;
      return okQ && okR && okI && okO && okC && okA;
    });
  }

  function renderDirectoryTable() {
    if (!directoryBody) return;
    var rows = filteredDirectoryRows();
    var Lm = I18N[getUiLang()] || I18N.sw;
    if (progResultCount) progResultCount.textContent = rows.length + " " + Lm.dir_prog_count;
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
      nectaLookupMsg.innerHTML = '<div class="warning">' + escapeHtml(t("necta_pick_level")) + "</div>";
      toast("Chagua level kwanza", "warn");
      return;
    }
    var year = parseInt(nectaExamYear.value, 10);
    var candidate = nectaIndexNo.value.trim();
    if (!candidate) {
      nectaLookupMsg.innerHTML = '<div class="warning">' + escapeHtml(t("necta_enter_cno")) + "</div>";
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
        var allowed = ["I", "II", "III", "IV", "0"];
        if (allowed.indexOf(div) !== -1) document.getElementById("division").value = div;
      }
      var school = rec.school_name || "";
      var cno = rec.candidate_number || candidate.toUpperCase();
      setExamContext({
        exam_number: cno,
        exam_year: Number(year) || null,
        source: isCsee ? "necta_csee_lookup" : "necta_acsee_lookup",
        exam_level: isCsee ? "o_level" : "a_level",
      });
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
      addRecentActivity("lookup", "NECTA lookup", (school || cno) + " · " + year);
      renderHomeDashboard();
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
    document.body.classList.add("is-theme-animating");
    document.body.dataset.theme = nextTheme;
    localStorage.setItem("mwongozo-theme", nextTheme);
    refreshThemeLabels();
    if (themeAnimTimer) clearTimeout(themeAnimTimer);
    themeAnimTimer = setTimeout(function () {
      document.body.classList.remove("is-theme-animating");
    }, 200);
  }

  function showInputView() {
    if (inputView) inputView.classList.remove("hidden");
    if (resultsView) resultsView.classList.add("hidden");
    if (mainWrapInner) mainWrapInner.classList.remove("wrap-inner--reco-focus");
    if (dashboardShell) dashboardShell.classList.remove("dashboard--results-mode");
    scrollToTopAnimated();
  }

  function showResultsView() {
    if (inputView) inputView.classList.add("hidden");
    if (resultsView) resultsView.classList.remove("hidden");
    if (mainWrapInner) mainWrapInner.classList.add("wrap-inner--reco-focus");
    if (dashboardShell) dashboardShell.classList.add("dashboard--results-mode");
    scrollToTopAnimated();
    window.requestAnimationFrame(function () {
      revealRecommendationRows();
      syncRecoTableLayout();
    });
  }

  function syncRecoTableLayout() {
    var stack = document.querySelector(".reco-sticky-stack");
    if (!stack) return;
    var topbar = document.querySelector(".app-topbar");
    var topbarBottom = topbar ? Math.ceil(topbar.getBoundingClientRect().bottom + 4) : 68;
    document.documentElement.style.setProperty("--reco-filter-top", topbarBottom + "px");
    var viewport = document.querySelector(".results-viewport--table");
    if (viewport) viewport.scrollTop = 0;
  }

  if (!window.__mwRecoLayoutResize) {
    window.__mwRecoLayoutResize = true;
    window.addEventListener("resize", syncRecoTableLayout);
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

  function scrollToTopAnimated() {
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" });
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
    var examCtx = getExamContext() || {};
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
      csee_division:
        pathway === "o_level" ? document.getElementById("division").value || null : null,
      exam_number: examCtx.exam_number || null,
      exam_year: examCtx.exam_year || null,
      source: examCtx.source || "recommend_form",
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
      "</p>" +
      '<div class="reco-skeleton-grid" aria-hidden="true">' +
      '<div class="reco-skeleton-card"><span class="skeleton-chip"></span><span class="skeleton-line" style="width:78%"></span><span class="skeleton-line" style="width:62%"></span><div style="display:flex;gap:8px;flex-wrap:wrap"><span class="skeleton-pill"></span><span class="skeleton-pill"></span><span class="skeleton-pill"></span></div></div>' +
      '<div class="reco-skeleton-card"><span class="skeleton-chip"></span><span class="skeleton-line" style="width:84%"></span><span class="skeleton-line" style="width:54%"></span><div style="display:flex;gap:8px;flex-wrap:wrap"><span class="skeleton-pill"></span><span class="skeleton-pill"></span></div></div>' +
      '<div class="reco-skeleton-card"><span class="skeleton-chip"></span><span class="skeleton-line" style="width:72%"></span><span class="skeleton-line" style="width:68%"></span><div style="display:flex;gap:8px;flex-wrap:wrap"><span class="skeleton-pill"></span><span class="skeleton-pill"></span></div></div>' +
      "</div></div>"
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
    var bandClass = confidenceBandClass(rec.assessment && rec.assessment.confidence_band);
    var typeLabel = isReview ? L.results_borderline : L.results_direct;
    var matchClass = isReview ? "rec-row--review" : "rec-row--direct";
    var saved = isProgrammeSaved(rec);
    var instName = (rec.programme && rec.programme.institution_name) || "";
    var instCode = (rec.programme && rec.programme.institution_code) || "";
    var instTitle =
      instName +
      (instCode && instName && instName.toUpperCase().indexOf(instCode.toUpperCase()) === -1
        ? " (" + instCode + ")"
        : instCode && !instName
          ? instCode
          : "");
    var progName = (rec.programme && rec.programme.name) || "";
    var regionName = (rec.programme && rec.programme.region) || "—";
    var applyBtn = applyUrl
      ? '<a class="btn btn-secondary btn-sm rec-apply-link" href="' +
        escapeHtmlAttr(applyUrl) +
        '" target="_blank" rel="noopener noreferrer" title="' +
        escapeHtmlAttr(applyUrl) +
        '"><i class="fa-solid fa-arrow-up-right-from-square" aria-hidden="true"></i></a> '
      : "";
    var saveBtn =
      '<button type="button" class="btn btn-secondary btn-sm rec-save-btn ' +
      (saved ? "is-saved" : "") +
      '" data-rec-save="' +
      fidx +
      '" title="' +
      escapeHtmlAttr(saved ? "Unsave programme" : "Save programme") +
      '">' +
      '<i class="fa-' +
      (saved ? "solid" : "regular") +
      ' fa-bookmark" aria-hidden="true"></i></button> ';
    return (
      '<tr class="rec-row ' +
      matchClass +
      '" data-match="' +
      (isReview ? "review" : "direct") +
      '">' +
      '<td class="rec-td-num" data-label="' +
      escapeHtmlAttr(L.results_col_rank) +
      '">' +
      escapeHtml(String(rec.rank != null ? rec.rank : "—")) +
      '</td><td class="rec-td-inst" data-label="' +
      escapeHtmlAttr(L.results_col_inst) +
      '" title="' +
      escapeHtmlAttr(instTitle || instName) +
      '">' +
      formatInstitutionCellHTML(rec) +
      '</td><td class="rec-td-prog" data-label="' +
      escapeHtmlAttr(L.results_col_prog) +
      '" title="' +
      escapeHtmlAttr(progName) +
      '"><strong>' +
      escapeHtml(progName) +
      '</strong></td><td class="rec-td-region" data-label="' +
      escapeHtmlAttr(L.results_col_region) +
      '" title="' +
      escapeHtmlAttr(regionName) +
      '">' +
      escapeHtml(regionName) +
      '</td><td class="rec-td-pts" data-label="' +
      escapeHtmlAttr(L.results_col_pts) +
      '" title="' +
      escapeHtmlAttr(String(rec.student_points) + " / " + String(rec.minimum_required_points)) +
      '">' +
      escapeHtml(String(rec.student_points)) +
      " / " +
      escapeHtml(String(rec.minimum_required_points)) +
      '</td><td class="rec-td-conf" data-label="' +
      escapeHtmlAttr(L.results_col_conf) +
      '"><div class="rec-mini-bar ' +
      bandClass +
      '" title="' +
      escapeHtmlAttr(L.results_conf + " " + conf + "%") +
      '"><span style="width:' +
      barW +
      '"></span></div><span class="rec-conf-meta ' +
      bandClass +
      '">' +
      escapeHtml(String(rec.assessment.confidence) + "% · " + String(rec.assessment.confidence_band)) +
      '</span></td><td class="rec-td-type" data-label="' +
      escapeHtmlAttr(L.results_col_type) +
      '"><span class="rec-pill">' +
      escapeHtml(typeLabel) +
      '</span></td><td class="rec-td-actions" data-label="' +
      escapeHtmlAttr(L.results_col_actions) +
      '"><div class="rec-td-actions__inner">' +
      saveBtn +
      applyBtn +
      '<button type="button" class="btn btn-secondary btn-sm rec-detail-btn" data-rec-detail="' +
      fidx +
      '" title="' +
      escapeHtmlAttr(L.results_detail_btn) +
      '"><i class="fa-solid fa-circle-info" aria-hidden="true"></i><span class="u-visually-hidden">' +
      escapeHtml(L.results_detail_btn) +
      "</span></button></div></td></tr>"
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
      '<option value="all">' + escapeHtml(t("results_all_regions")) + "</option>" +
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
      '<option value="all">' + escapeHtml(t("results_all_categories")) + "</option>" +
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
    var recoColgroup =
      "<colgroup>" +
      '<col class="reco-col-num" />' +
      '<col class="reco-col-inst" />' +
      '<col class="reco-col-prog" />' +
      '<col class="reco-col-region" />' +
      '<col class="reco-col-pts" />' +
      '<col class="reco-col-conf" />' +
      '<col class="reco-col-type" />' +
      '<col class="reco-col-actions" />' +
      "</colgroup>";
    var thead =
      "<thead><tr>" +
      "<th scope=\"col\">" +
      escapeHtml(L.results_col_rank) +
      '</th><th scope="col">' +
      escapeHtml(L.results_col_inst) +
      '</th><th scope="col">' +
      escapeHtml(L.results_col_prog) +
      '</th><th scope="col">' +
      escapeHtml(L.results_col_region) +
      '</th><th scope="col">' +
      escapeHtml(L.results_col_pts) +
      '</th><th scope="col">' +
      escapeHtml(L.results_col_conf) +
      '</th><th scope="col">' +
      escapeHtml(L.results_col_type) +
      '</th><th scope="col">' +
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
      '<div class="results-bundle results-bundle--table">' +
      '<div class="reco-sticky-stack">' +
      '<div class="results-filters-sticky">' +
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
      escapeHtml(t("results_sort_high")) +
      '</option><option value="confidence_asc" ' +
      ((f.sort || "confidence_desc") === "confidence_asc" ? "selected" : "") +
      ">" +
      escapeHtml(t("results_sort_low")) +
      "</option></select></div></div>" +
      '<div class="results-toolbar-row2">' +
      '<button type="button" class="btn btn-primary rec-save-analysis-btn" id="saveRecoAnalysisBtn" title="' +
      escapeHtmlAttr(L.saved_save_run) +
      '"><i class="fa-solid fa-floppy-disk" aria-hidden="true"></i> ' +
      escapeHtml(L.saved_save_run) +
      '</button>' +
      '<input id="resultsSearch" type="search" placeholder="' +
      escapeHtmlAttr(L.results_search_ph) +
      '" value="' +
      escapeHtmlAttr(f.query || "") +
      '" class="results-search-input" />' +
      '<button type="button" class="btn btn-secondary" data-quick-category="all">' +
      escapeHtml(L.results_quick_all) +
      '</button><button type="button" class="btn btn-secondary" data-quick-category="health">' +
      escapeHtml(L.results_quick_health) +
      '</button><button type="button" class="btn btn-secondary" data-quick-category="economics">' +
      escapeHtml(L.results_quick_econ) +
      '</button><button type="button" class="btn btn-secondary" data-quick-category="law">' +
      escapeHtml(L.results_quick_law) +
      "</button></div></div>" +
      '<div class="reco-table-head-wrap" aria-hidden="false">' +
      '<table class="rec-table rec-table--head">' +
      recoColgroup +
      thead +
      "</table></div></div>" +
      '<div class="results-viewport results-viewport--table"><table class="rec-table rec-table--body">' +
      recoColgroup +
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
    var saveButtons = document.querySelectorAll("[data-rec-save]");
    var prevButton = document.getElementById("prevResultsPage");
    var nextButton = document.getElementById("nextResultsPage");
    var saveAnalysisBtn = document.getElementById("saveRecoAnalysisBtn");
    if (saveAnalysisBtn) {
      saveAnalysisBtn.addEventListener("click", saveCurrentRecommendations);
    }
    updateSaveAnalysisButtonState();
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
    saveButtons.forEach(function (button) {
      button.addEventListener("click", function () {
        var idx = Number(button.getAttribute("data-rec-save"));
        var rec = resultsPagination._filteredSorted && resultsPagination._filteredSorted[idx];
        if (!rec) return;
        toggleSavedProgramme(rec);
        renderHomeDashboard();
        renderResultsPageTable();
      });
    });

    revealRecommendationRows();
    window.requestAnimationFrame(function () {
      syncRecoTableLayout();
      window.requestAnimationFrame(function () {
        syncRecoTableLayout();
        var vp = document.querySelector(".results-viewport--table");
        if (vp) vp.scrollTop = 0;
      });
    });
    refreshScrollMotionSoon();
  }

  function renderRecommendations(data, inputSnapshot) {
    var recommendations = (data.recommendations || []).map(function (rec) {
      return Object.assign({}, rec, { __isReview: false });
    });
    var reviewCandidates = (data.review_candidates || []).map(function (rec) {
      return Object.assign({}, rec, { __isReview: true });
    });
    var allRows = recommendations.concat(reviewCandidates).sort(renderResultsCompareRows);
    lastRecommendBundle = buildRecommendBundlePayload(data, inputSnapshot || lastRecommendInputSnapshot || {});
    updateAuthOnlyNav();
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
      var blockedMsg = data.csee_entry_message || "";
      var emptyLead = data.csee_entry_blocked
        ? blockedMsg || "CSEE Division 0 — hakuna njia ya cheti/diploma kwa sasa."
        : "Hakuna programme iliyo eligible kwa input hii.";
      resultsEl.innerHTML =
        '<div class="results-bundle glass results-bundle--table"><div class="error layout-block">' +
        escapeHtml(emptyLead) +
        "</div>" +
        comboHtml +
        '<p class="footer-note muted small">' +
        (data.csee_entry_blocked
          ? "Rudia mtihani wa CSEE au wasiliana na taasisi kwa maelekezo ya upya."
          : "Jaribu combination nyingine au angalia strict requirements.") +
        "</p></div>";
      addRecentActivity("recommend", "Recommendations checked", "0 eligible programmes");
      lastRecommendBundle = null;
      updateAuthOnlyNav();
      renderHomeDashboard();
      toast(data.csee_entry_blocked ? "Division haihitimu" : "Hakuna programme zilizo eligible", "warn");
      return;
    }
    delete resultSummaryEl.dataset.idle;
    resultSummaryEl.innerHTML = "";
    renderResultsPageTable();
    updateSaveAnalysisButtonState();
    addRecentActivity("recommend", "Recommendations ready", String(allRows.length) + " programmes returned");
    renderHomeDashboard();
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
    if (typeof window.helpPanelHandleSend === "function") {
      window.helpPanelHandleSend();
      return;
    }
    if (!chatInput) return;
    var t = chatInput.value.trim();
    if (!t) return;
    pushChat("user", t);
    chatInput.value = "";
    var Lchat = I18N[getUiLang()] || I18N.sw;
    setTimeout(function () {
      pushChat(
        "bot",
        Lchat.help_fallback ||
          "Tumia kichupo Msaada kwa mada zilizopangwa."
      );
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
      lastRecommendInputSnapshot = payload;
      var response = await (MwongozoApi
        ? MwongozoApi.fetchWithTimeout("/recommend?limit=150", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          })
        : apiFetch("/recommend?limit=150", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          }));
      var data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Request failed");
      renderRecommendations(data, payload);
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
    addRecentActivity("form", "Loaded example", "Sample data applied to form");
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
    resultSummaryEl.dataset.idle = "1";
    resultSummaryEl.innerHTML = '<div class="muted">' + t("input_cleared") + "</div>";
    resultsEl.innerHTML = "";
    showInputView();
    navigateDash("input");
    addRecentActivity("form", "Form cleared", "Inputs reset to defaults");
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
    saved: 1,
    input: 1,
    results: 1,
    directory: 1,
    loan: 1,
    assistant: 1,
  };
  if (skipLanding) enterApp();

  document.querySelectorAll("[data-dir-view]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      setDirectoryView(btn.getAttribute("data-dir-view"));
    });
  });
  if (univSearch)
    univSearch.addEventListener("input", scheduleRenderUniversitiesGrid);
  if (univRegion)
    univRegion.addEventListener("change", scheduleRenderUniversitiesGrid);
  if (univOwnership)
    univOwnership.addEventListener("change", scheduleRenderUniversitiesGrid);
  if (univKind)
    univKind.addEventListener("change", scheduleRenderUniversitiesGrid);
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
  if (directoryOwnership)
    directoryOwnership.addEventListener("change", function () {
      renderDirectoryTable();
    });
  if (directoryCategory)
    directoryCategory.addEventListener("change", function () {
      renderDirectoryTable();
    });
  if (directoryAward)
    directoryAward.addEventListener("change", function () {
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

  document.querySelectorAll("[data-set-lang]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      setUiLang(btn.getAttribute("data-set-lang") || "sw");
      if (landingView && !landingView.classList.contains("hidden")) {
        try {
          initNewsPortfolio();
        } catch (_e) {}
        try {
          initLandingMetaAnimation();
        } catch (_e) {}
        try {
          initFabChatLabelAnimation();
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
  initLazyMedia();
  if (!skipLanding) {
    initPageEntrance();
    initHeroStatsCycle();
    try {
      initLandingMetaAnimation();
    } catch (_e) {}
  }
  var savedLang = localStorage.getItem("mwongozo-ui-lang");
  if (savedLang === "en" || savedLang === "sw") setUiLang(savedLang);
  else {
    applyI18n();
  }
  initNewsPortfolio();
  initScrollMotion();
  initUnivModal();
  bindUnivGridEvents();
  renderHomeDashboard();
  updateAuthOnlyNav();
  renderSavedPage();
  if (saveRecoRunBtn) saveRecoRunBtn.addEventListener("click", saveCurrentRecommendations);
  document.addEventListener("mwongozo:auth", function () {
    updateAuthOnlyNav();
    syncAllSavedFromServer();
  });
  whenAuthReady(function () {
    updateAuthOnlyNav();
    return syncAllSavedFromServer();
  });
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

  initPartnerMarquee();
  initFabChatDock();
  initFabChatLabelAnimation();

  window.toast = toast;
  window.addRecentActivity = addRecentActivity;
  window.navigateDash = navigateDash;
  window.clearPanelScrollMotion = clearPanelScrollMotion;
  if (typeof window.initLoanTracker === "function") window.initLoanTracker();
})();
