/**
 * Help centre — topics, search, SAM chat (uses sam-chat.js).
 */
(function (global) {
  "use strict";

  var HELP_TOPICS = global.SamChat ? global.SamChat.TOPICS : [];

  var initialized = false;
  var activeTopicId = "";
  var messenger = null;

  function lang() {
    return document.body.getAttribute("data-ui-lang") === "en" ? "en" : "sw";
  }

  function t(sw, en) {
    return lang() === "en" ? en : sw;
  }

  function $(id) {
    return document.getElementById(id);
  }

  function escapeHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function formatAnswer(text) {
    return global.SamChat
      ? global.SamChat.formatAnswer(text)
      : escapeHtml(text).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/\n/g, "<br />");
  }

  function getTopic(topic) {
    if (global.SamChat) {
      var p = global.SamChat.packTopic(topic);
      return {
        title: p.title,
        desc: lang() === "en" ? topic.desc_en || "" : topic.desc_sw || "",
        cat: lang() === "en" ? topic.cat_en || "" : topic.cat_sw || "",
        answer: p.answer,
        chip: p.chip,
      };
    }
    return {
      title: lang() === "en" ? topic.title_en : topic.title_sw,
      desc: lang() === "en" ? topic.desc_en : topic.desc_sw,
      cat: lang() === "en" ? topic.cat_en : topic.cat_sw,
      answer: lang() === "en" ? topic.answer_en : topic.answer_sw,
      chip: "",
    };
  }

  function getMessenger() {
    if (!global.SamChat) return null;
    if (!messenger) {
      messenger = global.SamChat.createMessenger($("chatMessages"), $("helpChatTyping"));
    }
    return messenger;
  }

  function pushChat(role, text) {
    var m = getMessenger();
    if (m) {
      if (role === "user") m.pushUser(text);
      else m.pushBotHtml(formatAnswer(text));
      return;
    }
    var log = $("chatMessages");
    if (!log) return;
    var wrap = document.createElement("div");
    wrap.className = "chat-bubble chat-bubble--" + role;
    wrap.textContent = text;
    log.appendChild(wrap);
    log.scrollTop = log.scrollHeight;
  }

  function pushChatHtml(html) {
    var m = getMessenger();
    if (m) {
      m.pushBotHtml(html);
      return;
    }
    var log = $("chatMessages");
    if (!log) return;
    var wrap = document.createElement("div");
    wrap.className = "chat-bubble chat-bubble--bot";
    wrap.innerHTML = html;
    log.appendChild(wrap);
    log.scrollTop = log.scrollHeight;
  }

  function showTopicAnswer(topic) {
    if (!topic) return;
    var pack = getTopic(topic);
    activeTopicId = topic.id;
    document.querySelectorAll(".help-topic-btn").forEach(function (btn) {
      btn.classList.toggle("is-active", btn.getAttribute("data-help-topic") === topic.id);
    });
    var m = getMessenger();
    if (m) {
      m.replyFromTopicId(topic.id);
      return;
    }
    pushChat("user", pack.title);
    setTimeout(function () {
      pushChatHtml(formatAnswer(pack.answer));
    }, 320);
  }

  function replyToMessage(text) {
    if (global.SamChat) {
      var m = getMessenger();
      if (m) {
        m.reply(text);
        return;
      }
    }
    var matched = global.SamChat ? global.SamChat.matchTopic(text) : null;
    if (!matched) {
      HELP_TOPICS.forEach(function (topic) {
        var lower = text.toLowerCase();
        (topic.keywords || []).forEach(function (kw) {
          if (lower.indexOf(kw) !== -1) matched = topic;
        });
      });
    }
    if (matched) {
      showTopicAnswer(matched);
      return;
    }
    var composed = global.SamChat ? global.SamChat.composeReply(text) : null;
    if (composed) {
      pushChatHtml(composed.html);
      return;
    }
    pushChatHtml(
      formatAnswer(
        t(
          "Samahani, sijaelewa vizuri. Chagua mada au swali hapa chini.",
          "Sorry, I did not quite get that. Pick a topic or quick question below."
        )
      )
    );
  }

  function renderTopics(filter) {
    var list = $("helpTopicList");
    if (!list) return;
    var q = String(filter || "").toLowerCase().trim();
    var html = "";
    HELP_TOPICS.forEach(function (topic) {
      var pack = getTopic(topic);
      var desc = pack.desc || pack.chip || "";
      var cat = pack.cat || (lang() === "en" ? "Help" : "Msaada");
      var hay = (pack.title + " " + desc + " " + (topic.keywords || []).join(" ")).toLowerCase();
      if (q && hay.indexOf(q) === -1) return;
      var icon = topic.icon || "fa-circle-question";
      html +=
        '<button type="button" class="help-topic-btn' +
        (activeTopicId === topic.id ? " is-active" : "") +
        '" data-help-topic="' +
        escapeHtml(topic.id) +
        '"><span class="help-topic-btn__icon"><i class="fa-solid ' +
        escapeHtml(icon) +
        '" aria-hidden="true"></i></span><span class="help-topic-btn__text"><strong>' +
        escapeHtml(pack.title) +
        "</strong><em>" +
        escapeHtml(cat) +
        (desc ? " · " + escapeHtml(desc) : "") +
        "</em></span></button>";
    });
    list.innerHTML =
      html ||
      '<p class="help-empty-topics">' + escapeHtml(t("Hakuna mada iliyopatikana.", "No topics found.")) + "</p>";
    list.querySelectorAll("[data-help-topic]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var id = btn.getAttribute("data-help-topic");
        var topic = HELP_TOPICS.filter(function (x) {
          return x.id === id;
        })[0];
        showTopicAnswer(topic);
      });
    });
  }

  function renderChips() {
    var wrap = $("helpChatChips");
    if (!wrap) return;
    if (global.SamChat) {
      global.SamChat.renderChips(wrap, function (topicId) {
        var topic = HELP_TOPICS.filter(function (x) {
          return x.id === topicId;
        })[0];
        if (topic) showTopicAnswer(topic);
      });
      return;
    }
    wrap.innerHTML = HELP_TOPICS.slice(0, 8)
      .map(function (topic) {
        var pack = getTopic(topic);
        return (
          '<button type="button" class="help-chip" data-help-chip="' +
          escapeHtml(topic.id) +
          '">' +
          escapeHtml(pack.chip || pack.title) +
          "</button>"
        );
      })
      .join("");
    wrap.querySelectorAll("[data-help-chip]").forEach(function (chip) {
      chip.addEventListener("click", function () {
        var id = chip.getAttribute("data-help-chip");
        var topic = HELP_TOPICS.filter(function (x) {
          return x.id === id;
        })[0];
        if (topic) showTopicAnswer(topic);
      });
    });
  }

  function wireQuickActions() {
    document.querySelectorAll("[data-help-go]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var panel = btn.getAttribute("data-help-go");
        if (typeof global.navigateDash === "function") global.navigateDash(panel);
        else {
          document.querySelectorAll("[data-dash-nav]").forEach(function (nav) {
            if (nav.getAttribute("data-dash-nav") === panel) nav.click();
          });
        }
      });
    });
  }

  function welcomeIfNeeded() {
    var log = $("chatMessages");
    if (!log || log.querySelector(".sam-msg, .chat-bubble")) return;
    var key = "mwongozo-help-welcome-v2-" + lang();
    if (sessionStorage.getItem(key)) return;
    sessionStorage.setItem(key, "1");
    if (global.SamChat) {
      var m = getMessenger();
      if (m) m.pushBotHtml(global.SamChat.welcomeHtml());
      if (log) log.scrollTop = 0;
      if (typeof global.scrollHelpPanelIntoView === "function") global.scrollHelpPanelIntoView();
      return;
    }
    pushChatHtml(
      formatAnswer(
        t(
          "Hujambo! Mimi **SAM** — msaidizi wa MWONGOZO SMART. Chagua mada au swali la haraka.",
          "Hello! I'm **SAM** — your MWONGOZO SMART guide. Pick a topic or quick question."
        )
      )
    );
    if (log) log.scrollTop = 0;
    if (typeof global.scrollHelpPanelIntoView === "function") global.scrollHelpPanelIntoView();
  }

  function handleSend() {
    var input = $("chatInput");
    if (!input) return;
    var text = input.value.trim();
    if (!text) return;
    var m = getMessenger();
    if (m) {
      m.pushUser(text);
      input.value = "";
      m.reply(text);
      return;
    }
    pushChat("user", text);
    input.value = "";
    setTimeout(function () {
      replyToMessage(text);
    }, 320);
  }

  function initHelpPanel() {
    if (typeof global.clearPanelScrollMotion === "function") {
      global.clearPanelScrollMotion("assistant");
    }
    messenger = null;
    renderTopics("");
    renderChips();
    wireQuickActions();
    welcomeIfNeeded();
    if (typeof global.scrollHelpPanelIntoView === "function") {
      global.scrollHelpPanelIntoView();
      requestAnimationFrame(function () {
        global.scrollHelpPanelIntoView();
      });
    }

    if (!initialized) {
      initialized = true;
      var search = $("helpTopicSearch");
      if (search) {
        search.addEventListener("input", function () {
          renderTopics(search.value);
        });
      }
      var send = $("chatSend");
      var input = $("chatInput");
      if (send) send.addEventListener("click", handleSend);
      if (input) {
        input.addEventListener("keydown", function (e) {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
          }
        });
      }
    }
  }

  function refreshHelpLang() {
    messenger = null;
    renderTopics($("helpTopicSearch") ? $("helpTopicSearch").value : "");
    renderChips();
  }

  global.initHelpPanel = initHelpPanel;
  global.refreshHelpLang = refreshHelpLang;
  global.helpPanelHandleSend = handleSend;
})(typeof window !== "undefined" ? window : globalThis);
