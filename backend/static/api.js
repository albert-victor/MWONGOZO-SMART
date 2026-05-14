/**
 * Thin fetch helpers for Mwongozo Smart — same paths and methods as FastAPI routes.
 * No backend contract changes; timeouts + JSON parse errors surface as thrown Error.
 */
(function (global) {
  "use strict";

  var DEFAULT_TIMEOUT_MS = 28000;

  function withTimeout(ms, controller) {
    var id = setTimeout(function () {
      try {
        controller.abort();
      } catch (_e) {}
    }, ms);
    return function () {
      clearTimeout(id);
    };
  }

  /**
   * @param {string} url
   * @param {RequestInit} [init]
   * @param {number} [timeoutMs]
   * @returns {Promise<Response>}
   */
  function fetchWithTimeout(url, init, timeoutMs) {
    var ms = timeoutMs != null ? timeoutMs : DEFAULT_TIMEOUT_MS;
    var controller = new AbortController();
    var clear = withTimeout(ms, controller);
    var merged = Object.assign({}, init || {}, { signal: controller.signal });
    return fetch(url, merged).finally(clear);
  }

  /**
   * @param {string} url
   * @param {RequestInit} [init]
   */
  function fetchJson(url, init, timeoutMs) {
    return fetchWithTimeout(url, init, timeoutMs).then(function (res) {
      return res.json().then(function (data) {
        if (!res.ok) {
          var msg = formatApiError(data);
          var err = new Error(msg);
          err.status = res.status;
          err.data = data;
          throw err;
        }
        return data;
      });
    });
  }

  function formatApiError(data) {
    if (!data) return "Hitilafu isiyojulikana";
    var d = data.detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d))
      return d
        .map(function (x) {
          return x.msg ? x.msg : JSON.stringify(x);
        })
        .join("; ");
    try {
      return JSON.stringify(data);
    } catch (_e) {
      return "Request failed";
    }
  }

  global.MwongozoApi = {
    fetchWithTimeout: fetchWithTimeout,
    fetchJson: fetchJson,
    formatApiError: formatApiError,
    DEFAULT_TIMEOUT_MS: DEFAULT_TIMEOUT_MS,
  };
})(typeof window !== "undefined" ? window : globalThis);
