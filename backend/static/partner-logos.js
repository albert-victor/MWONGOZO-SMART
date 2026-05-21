/**
 * Partner logos — PNGs in /static/partners/ (fallback: fallbackFile).
 * `label` = short name shown under the logo in the marquee.
 */
(function (global) {
  "use strict";

  global.MWONGOZO_PARTNERS = [
    { id: "gov", name: "Serikali ya Tanzania", label: "Serikali", file: "gov.png", fallbackFile: "gov.svg", url: "https://www.tanzania.go.tz/" },
    { id: "tamisemi", name: "TAMISEMI", label: "TAMISEMI", file: "tamisemi.png", url: "https://www.tamisemi.go.tz/" },
    { id: "tcu", name: "TCU", label: "TCU", file: "tcu.png", fallbackFile: "tcu.svg", url: "https://www.tcu.go.tz/" },
    { id: "necta", name: "NECTA", label: "NECTA", file: "necta.png", fallbackFile: "necta.svg", url: "https://www.necta.go.tz/" },
    { id: "heslb", name: "HESLB", label: "HESLB", file: "heslb.png", fallbackFile: "heslb.svg", url: "https://www.heslb.go.tz/" },
    { id: "nacte", name: "NACTE", label: "NACTE", file: "nacte.png", fallbackFile: "nacte.svg", url: "https://www.nacte.go.tz/" },
    { id: "nactvet", name: "NACTVET", label: "NACTVET", file: "nactvet.png", fallbackFile: "nactvet.svg", url: "https://www.nactvet.go.tz/" },
    { id: "tveta", name: "TVETA", label: "TVETA", file: "tveta.png", fallbackFile: "tveta.svg", url: "https://www.tveta.go.tz/" },
    { id: "nida", name: "NIDA", label: "NIDA", file: "nida.png", url: "https://www.nida.go.tz/" },
    { id: "rita", name: "RITA", label: "RITA", file: "rita.png", fallbackFile: "rita.svg", url: "https://www.rita.go.tz/" },
    { id: "moe", name: "Wizara ya Elimu", label: "Wizara", file: "moe.png", fallbackFile: "moe.svg", url: "https://www.moe.go.tz/" },
    { id: "costech", name: "COSTECH", label: "COSTECH", file: "costech.png", url: "https://www.costech.or.tz/" },
  ];
})(typeof window !== "undefined" ? window : globalThis);
