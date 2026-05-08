from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel, Field

from mwongozo_smart.core.engine import RecommendationEngine
from mwongozo_smart.core.models import AdmissionPathway, ALevelScheme, StudentResult, SubjectGrade
from mwongozo_smart.data.guidebook_data import PROGRAMMES
from mwongozo_smart.data.institutions import INSTITUTIONS
from mwongozo_smart.utils.combination_helper import COMBINATION_MAP


engine = RecommendationEngine()
app = FastAPI(title="Mwongozo Smart", version="0.1.0")


def get_engine() -> RecommendationEngine:
    # Single shared engine instance used by all API routes.
    return engine


class SubjectInput(BaseModel):
    # One subject row from the frontend form.
    subject: str
    grade: str
    principal: bool = True
    level: str = Field(default="a_level", pattern="^(a_level|o_level)$")


class StudentInput(BaseModel):
    # Full student payload sent from the browser to /recommend.
    pathway: AdmissionPathway = AdmissionPathway.A_LEVEL
    a_level_scheme: ALevelScheme = ALevelScheme.POST_2016
    a_level_subjects: list[SubjectInput] = Field(default_factory=list)
    o_level_subjects: list[SubjectInput] = Field(default_factory=list)
    combination: str | None = None
    preferred_regions: list[str] = Field(default_factory=list)
    preferred_institutions: list[str] = Field(default_factory=list)
    language: str = "english"
    equivalent_qualification: str | None = None
    notes: list[str] = Field(default_factory=list)

    def to_student_result(self) -> StudentResult:
        # Convert request JSON into the internal model used by the engine.
        return StudentResult(
            pathway=self.pathway,
            a_level_scheme=self.a_level_scheme,
            a_level_subjects=[SubjectGrade(**item.model_dump()) for item in self.a_level_subjects],
            o_level_subjects=[SubjectGrade(**item.model_dump()) for item in self.o_level_subjects],
            combination=self.combination,
            preferred_regions=self.preferred_regions,
            preferred_institutions=self.preferred_institutions,
            language=self.language,
            equivalent_qualification=self.equivalent_qualification,
            notes=self.notes,
        )


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    # Prefer the external template so the frontend stays out of the backend file.
    template_path = Path(__file__).resolve().parent / "templates" / "home.html"
    # The homepage serves the entire frontend UI.
    sample_payload = {
        "pathway": "a_level",
        "combination": "PCB",
        "a_level_subjects": [
            {"subject": "Physics", "grade": "A", "principal": True, "level": "a_level"},
            {"subject": "Chemistry", "grade": "B", "principal": True, "level": "a_level"},
            {"subject": "Biology", "grade": "B", "principal": True, "level": "a_level"},
        ],
        "o_level_subjects": [
            {"subject": "Mathematics", "grade": "C", "principal": True, "level": "o_level"},
            {"subject": "English Language", "grade": "C", "principal": True, "level": "o_level"},
        ],
        "language": "english",
    }

    a_level_subjects_catalog = [
        "Physics",
        "Chemistry",
        "Biology",
        "Advanced Mathematics",
        "Basic Applied Mathematics",
        "Basic Mathematics",
        "English Language",
        "Kiswahili",
        "Geography",
        "History",
        "Economics",
        "Commerce",
        "Accountancy",
        "Book Keeping",
        "Nutrition",
        "Computer Studies",
    ]

    o_level_subjects_catalog = [
        "Mathematics",
        "English Language",
        "Kiswahili",
        "Biology",
        "Chemistry",
        "Physics",
        "History",
        "Geography",
        "Civics",
        "Commerce",
        "Book Keeping",
        "Economics",
        "Agriculture",
        "Computer Studies",
        "Information and Computer Studies",
        "Food and Nutrition",
        "Home Economics",
        "Fine Arts",
        "French",
        "Arabic",
        "Islamic Knowledge",
        "Bible Knowledge",
        "Civics and Moral Education",
        "Computer Applications",
        "Design and Technology",
        "Nutrition",
        "Physical Education",
        "Music",
        "Theatre Arts",
    ]

    default_o_level_subjects = [
        "Mathematics",
        "English Language",
        "Kiswahili",
        "Biology",
        "Chemistry",
        "Physics",
        "History",
        "Geography",
        "Civics",
        "Commerce",
        "Book Keeping",
        "Economics",
        "Agriculture",
        "Computer Studies",
        "Information and Computer Studies",
        "Food and Nutrition",
        "Bible Knowledge",
        "Islamic Knowledge",
        "Civics and Moral Education",
        "Nutrition",
        "Physical Education",
    ]

    grades = ["", "A", "B", "C", "D", "E", "S"]
    combo_options = "".join(f'<option value="{code}">{code}</option>' for code in sorted(COMBINATION_MAP.keys()))

    return (
        template_path.read_text(encoding="utf-8")
        .replace("__ASUBJECTS_JSON__", json.dumps(a_level_subjects_catalog))
        .replace("__OSUBJECTS_JSON__", json.dumps(o_level_subjects_catalog))
        .replace("__ODEFAULTS_JSON__", json.dumps(default_o_level_subjects))
        .replace("__GRADES_JSON__", json.dumps(grades))
        .replace("__SAMPLE_JSON__", json.dumps(sample_payload))
        .replace("__COMBO_OPTIONS__", combo_options)
    )

    template = """
    <!doctype html>
    <html lang="sw">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>Mwongozo Smart</title>
      <style>
        html { scroll-behavior:smooth; }
        :root {
          --bg:#07111f;
          --panel:rgba(10,16,29,.92);
          --line:rgba(148,163,184,.22);
          --text:#e5eefc;
          --muted:#95a7bf;
          --accent:#6ee7f9;
          --accent2:#34d399;
          --warn:#fbbf24;
          --danger:#fb7185;
          --shadow:0 8px 18px rgba(0,0,0,.18);
          --shadow-soft:0 4px 10px rgba(0,0,0,.12);
        }
        body[data-theme="light"] {
          --bg:#eef5fb;
          --panel:rgba(255,255,255,.90);
          --line:rgba(100,116,139,.18);
          --text:#0f172a;
          --muted:#475569;
          --accent:#0284c7;
          --accent2:#059669;
          --warn:#b45309;
          --danger:#be123c;
          --shadow:0 8px 18px rgba(15,23,42,.10);
          --shadow-soft:0 4px 10px rgba(15,23,42,.08);
        }
        * { box-sizing:border-box; }
        body {
          margin:0;
          font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          color:var(--text);
          background:
            radial-gradient(circle at top left, rgba(52,211,153,.08), transparent 28%),
            radial-gradient(circle at top right, rgba(110,231,249,.08), transparent 24%),
            linear-gradient(180deg, var(--bg) 0%, #091525 100%);
          transition:background .25s ease, color .25s ease;
        }
        body[data-theme="light"] .hero {
          background: linear-gradient(135deg, rgba(255,255,255,.94), rgba(239,246,255,.90));
        }
        body[data-theme="light"] .hero p,
        body[data-theme="light"] .footer-note,
        body[data-theme="light"] .small,
        body[data-theme="light"] .result-card,
        body[data-theme="light"] .meta-grid,
        body[data-theme="light"] .pill {
          color: var(--text);
        }
        .wrap { max-width:1120px; margin:0 auto; padding:22px; }
        .hero {
          background: linear-gradient(135deg, rgba(15,23,42,.96), rgba(8,47,73,.92));
          border:1px solid var(--line);
          box-shadow:var(--shadow);
          padding:24px;
          border-radius:22px;
          position:relative;
        }
        .hero h1 { margin:0 0 10px; font-size:2.2rem; line-height:1.05; }
        .hero p { margin:0; color:var(--muted); line-height:1.75; max-width:860px; }
        .pill-row { display:flex; flex-wrap:wrap; gap:10px; margin-top:14px; }
        .pill {
          border:1px solid rgba(110,231,249,.18);
          background:rgba(15,23,42,.60);
          padding:8px 12px;
          border-radius:999px;
          color:#c7f9ff;
          font-size:.92rem;
        }
        body[data-theme="light"] .pill { background:rgba(255,255,255,.95); color:#0369a1; }
        .theme-toggle {
          position:absolute;
          top:18px;
          right:18px;
        }
        .card {
          background:var(--panel);
          border:1px solid var(--line);
          border-radius:20px;
          padding:18px;
          box-shadow:var(--shadow);
        }
        .page-view { margin-top:18px; }
        .page-view.hidden { display:none; }
        .fade-in { animation:fadeUp .35s ease both; }
        @keyframes fadeUp {
          from { opacity:0; transform:translateY(10px); }
          to { opacity:1; transform:translateY(0); }
        }
        .section-title { display:flex; align-items:baseline; justify-content:space-between; gap:10px; margin-bottom:12px; }
        .section-title h2, .section-title h3 { margin:0; }
        .muted { color:var(--muted); }
        .small { font-size:.9rem; }
        .step-bar { display:grid; gap:10px; grid-template-columns:repeat(2, minmax(0,1fr)); margin-bottom:16px; }
        .btn {
          border:none;
          border-radius:14px;
          padding:12px 14px;
          font-weight:800;
          cursor:pointer;
          transition:transform .18s ease, box-shadow .18s ease, opacity .18s ease;
          box-shadow:var(--shadow-soft);
        }
        .btn:hover { transform:translateY(-1px); opacity:.98; }
        .btn-primary { background:linear-gradient(135deg, #06b6d4, #10b981); color:#04111b; }
        .btn-secondary { background:rgba(15,23,42,.92); color:var(--text); border:1px solid rgba(148,163,184,.22); }
        body[data-theme="light"] .btn-secondary { background:rgba(255,255,255,.96); }
        .btn-danger { background:rgba(127,29,29,.85); color:#fee2e2; }
        .btn.active { outline:2px solid rgba(110,231,249,.45); }
        .grid-2 { display:grid; gap:14px; grid-template-columns:repeat(2, minmax(0,1fr)); }
        .grid-3 { display:grid; gap:14px; grid-template-columns:repeat(3, minmax(0,1fr)); }
        .field { display:grid; gap:8px; }
        label { color:var(--text); font-size:.95rem; }
        input, select {
          font:inherit;
          color:var(--text);
          background:rgba(2,6,23,.82);
          border:1px solid rgba(148,163,184,.24);
          border-radius:12px;
          padding:11px 13px;
          outline:none;
        }
        body[data-theme="light"] input, body[data-theme="light"] select { background:rgba(255,255,255,.96); }
        input:focus, select:focus { border-color:rgba(110,231,249,.68); box-shadow:0 0 0 2px rgba(34,211,238,.10); }
        .hidden { display:none !important; }
        .subject-list { display:grid; gap:10px; margin-top:12px; }
        .subject-row {
          display:grid;
          gap:10px;
          grid-template-columns:minmax(0,2fr) 92px 120px auto;
          align-items:center;
          background:rgba(15,23,42,.68);
          border:1px solid rgba(148,163,184,.14);
          border-radius:14px;
          padding:10px;
        }
        body[data-theme="light"] .subject-row { background:rgba(255,255,255,.92); }
        .action-row { display:flex; flex-wrap:wrap; gap:10px; margin-top:14px; }
        .results { display:grid; gap:14px; margin-top:14px; }
        .result-card {
          background:linear-gradient(180deg, rgba(15,23,42,.92), rgba(2,6,23,.96));
          border:1px solid rgba(148,163,184,.14);
          border-radius:16px;
          padding:16px;
          color:var(--text);
        }
        body[data-theme="light"] .result-card {
          background:linear-gradient(180deg, rgba(255,255,255,.98), rgba(240,248,255,.96));
        }
        .result-head { display:flex; justify-content:space-between; gap:12px; align-items:center; }
        .rank {
          min-width:40px;
          height:40px;
          display:inline-grid;
          place-items:center;
          border-radius:12px;
          background:rgba(34,197,94,.10);
          color:var(--accent2);
          font-weight:800;
        }
        .confidence {
          padding:6px 10px;
          border-radius:999px;
          font-weight:700;
          background:rgba(110,231,249,.10);
          color:var(--text);
          border:1px solid rgba(110,231,249,.18);
        }
        .meta-grid {
          display:grid;
          gap:8px;
          grid-template-columns:repeat(auto-fit, minmax(170px, 1fr));
          margin-top:12px;
          font-size:.92rem;
          color:var(--text);
        }
        .warning, .error, .success {
          margin-top:12px;
          padding:10px 12px;
          border-radius:12px;
          color:var(--text);
        }
        .warning { border-left:3px solid var(--warn); background:rgba(251,191,36,.08); }
        .error { border-left:3px solid var(--danger); background:rgba(251,113,133,.08); }
        .success { border-left:3px solid var(--accent2); background:rgba(52,211,153,.08); }
        body[data-theme="light"] .warning { background:rgba(180,83,9,.08); }
        body[data-theme="light"] .error { background:rgba(190,18,60,.08); }
        body[data-theme="light"] .success { background:rgba(5,150,105,.08); }
        .footer-note { margin-top:12px; color:var(--muted); font-size:.92rem; }
        .results-nav { display:flex; justify-content:space-between; gap:12px; align-items:center; flex-wrap:wrap; }
        .toggle-icon {
          display:inline-grid;
          place-items:center;
          width:1.1em;
          height:1.1em;
          margin-right:6px;
          vertical-align:-0.12em;
        }
        @media (max-width: 980px) {
          .grid-2, .grid-3, .step-bar { grid-template-columns:1fr; }
          .subject-row { grid-template-columns:1fr 1fr; }
          .theme-toggle { position:static; margin-top:14px; }
        }
      </style>
    </head>
    <body>
      <div class="wrap">
        <section class="hero fade-in">
          <button type="button" class="btn btn-secondary theme-toggle" id="themeToggle"><span class="toggle-icon" id="themeIcon">â˜€</span><span id="themeLabel">Light mode</span></button>
          <h1>Mwongozo Smart</h1>
          <p>Chagua level, jaza matokeo yako, kisha bonyeza <strong>Pata Recommendations</strong>. Mfumo utatoa programme zinazokaribia eligibility yako kwa kutumia TCU Guidebook 2025/2026.</p>
          <div class="pill-row">
            <span class="pill">Step 1: select level</span>
            <span class="pill">Step 2: enter results</span>
            <span class="pill">Rules first</span>
            <span class="pill">English output</span>
          </div>
        </section>

        <section id="inputView" class="page-view fade-in">
          <div class="card">
            <div class="section-title">
              <h2>Chagua level ya mtumiaji</h2>
              <span class="muted small">Form 4 au Form 6</span>
            </div>
            <div class="step-bar">
              <button type="button" class="btn btn-primary" data-pathway-button="o_level">Form 4 / O-Level</button>
              <button type="button" class="btn btn-primary" data-pathway-button="a_level">Form 6 / A-Level</button>
            </div>
            <p class="footer-note">Chagua level kwanza. Kisha form husika itaonekana tu.</p>

            <form id="recommendForm">
              <input type="hidden" id="pathway" name="pathway" value="" />

              <div id="levelPrompt" class="success">
                Bonyeza <strong>Form 4</strong> au <strong>Form 6</strong> ili uanze.
              </div>

              <div id="aLevelSection" class="hidden">
                <div class="section-title" style="margin-top:16px;">
                  <h3>Form 6 / A-Level</h3>
                  <span class="muted small">Chagua combination kisha masomo yajaze automatically</span>
                </div>
                <div class="grid-3">
                  <div class="field">
                    <input type="hidden" id="a_level_scheme" name="a_level_scheme" value="2016_plus" />
                  </div>
                  <div class="field">
                    <label for="combination">Combination</label>
                    <select id="combination" name="combination">
                      <option value="">Select combination</option>
                      __COMBO_OPTIONS__
                    </select>
                  </div>
                  <div class="field">
                    <input type="hidden" id="language" name="language" value="english" />
                  </div>
                </div>
                <div class="field" style="margin-top:14px;">
                  <label>Principal subjects</label>
                  <div id="aLevelSubjects" class="subject-list"></div>
                  <div class="action-row">
                    <button type="button" class="btn btn-secondary" data-add-subject="a">+ Add A-Level subject</button>
                  </div>
                </div>
              </div>

              <div id="oLevelSection" class="hidden">
                <div class="section-title" style="margin-top:16px;">
                  <h3>Form 4 / O-Level</h3>
                  <span class="muted small">NECTA CSEE subjects, grades, and result model</span>
                </div>
                <div class="grid-3">
                  <div class="field">
                    <label for="division">Calculated division</label>
                    <select id="division" name="division">
                      <option value="">Select division</option>
                      <option value="I">Division I</option>
                      <option value="II">Division II</option>
                      <option value="III">Division III</option>
                      <option value="IV">Division IV</option>
                    </select>
                  </div>
                  <div class="field">
                    <label for="result_model">Result model</label>
                    <select id="result_model" name="result_model">
                      <option value="standard">NECTA standard</option>
                      <option value="borderline">Borderline / review</option>
                    </select>
                  </div>
                  <div class="field">
                    <input type="hidden" id="o_language" name="o_language" value="english" />
                  </div>
                </div>
                <div class="field" style="margin-top:14px;">
                  <label>NECTA O-Level subjects</label>
                  <div id="oLevelSubjects" class="subject-list"></div>
                  <div class="action-row">
                    <button type="button" class="btn btn-secondary" data-add-subject="o">+ Add O-Level subject</button>
                  </div>
                </div>
              </div>

              <div class="action-row" style="margin-top:18px;">
                <button type="submit" class="btn btn-primary">Pata Recommendations</button>
                <button type="button" class="btn btn-secondary" id="loadExample">Load example</button>
                <button type="button" class="btn btn-secondary" id="clearForm">Clear</button>
              </div>
            </form>
          </div>
        </section>

        <section id="resultsView" class="page-view hidden fade-in">
          <div class="card">
            <div class="results-nav">
              <div class="section-title" style="margin:0;">
                <h2>Matokeo</h2>
                <span class="muted small">Top eligible programmes</span>
              </div>
              <button type="button" class="btn btn-secondary" id="backToInput">Badilisha inputs</button>
            </div>
            <div id="resultSummary" class="muted">Chagua level, jaza matokeo, kisha bonyeza <strong>Pata Recommendations</strong>.</div>
            <div id="results" class="results"></div>
          </div>
        </section>
      </div>

      <script>
        const subjectCatalog = __ASUBJECTS_JSON__;
        const gradeOptions = __GRADES_JSON__;
        const samplePayload = __SAMPLE_JSON__;
        const oLevelSubjectsCatalog = __OSUBJECTS_JSON__;
        const defaultOLevelSubjects = __ODEFAULTS_JSON__;

        const aLevelContainer = document.getElementById("aLevelSubjects");
        const oLevelContainer = document.getElementById("oLevelSubjects");
        const resultsEl = document.getElementById("results");
        const resultSummaryEl = document.getElementById("resultSummary");
        const pathwayInput = document.getElementById("pathway");
        const levelPrompt = document.getElementById("levelPrompt");
        const aLevelSection = document.getElementById("aLevelSection");
        const oLevelSection = document.getElementById("oLevelSection");
        const pathwayButtons = document.querySelectorAll("[data-pathway-button]");
        const combinationInput = document.getElementById("combination");
        const inputView = document.getElementById("inputView");
        const resultsView = document.getElementById("resultsView");
        const themeToggle = document.getElementById("themeToggle");
        const themeIcon = document.getElementById("themeIcon");
        const themeLabel = document.getElementById("themeLabel");

        function setTheme(theme) {
          const nextTheme = theme === "light" ? "light" : "dark";
          document.body.dataset.theme = nextTheme;
          localStorage.setItem("mwongozo-theme", nextTheme);
          themeLabel.textContent = nextTheme === "light" ? "Dark mode" : "Light mode";
          themeIcon.textContent = nextTheme === "light" ? "â˜¾" : "â˜€";
        }

        function showInputView() {
          inputView.classList.remove("hidden");
          resultsView.classList.add("hidden");
          window.scrollTo({ top: 0, behavior: "smooth" });
        }

        function showResultsView() {
          resultsView.classList.remove("hidden");
          inputView.classList.add("hidden");
          window.scrollTo({ top: 0, behavior: "smooth" });
        }

        function subjectRow(preset = {}, level = "a") {
          const catalog = level === "o" ? oLevelSubjectsCatalog : subjectCatalog;
          const gradeOptionsHtml = gradeOptions.map(g => {
            const label = g === "" ? "--" : g;
            return `<option value="${g}" ${preset.grade === g ? "selected" : ""}>${label}</option>`;
          }).join("");
          const wrapper = document.createElement("div");
          wrapper.className = "subject-row";
          wrapper.innerHTML = `
            <select class="subject-name">
              ${catalog.map(s => `<option value="${s}" ${preset.subject === s ? "selected" : ""}>${s}</option>`).join("")}
            </select>
            <select class="subject-grade">
              ${gradeOptionsHtml}
            </select>
            <select class="subject-model">
              <option value="core" ${preset.model !== "elective" ? "selected" : ""}>Core</option>
              <option value="elective" ${preset.model === "elective" ? "selected" : ""}>Elective</option>
            </select>
            <button type="button" class="btn btn-danger remove-btn">Remove</button>
          `;
          wrapper.querySelector(".remove-btn").addEventListener("click", () => wrapper.remove());
          return wrapper;
        }

        const combinationMap = {
          PCB: ["Physics", "Chemistry", "Biology"],
          PCM: ["Physics", "Chemistry", "Advanced Mathematics"],
          PGM: ["Physics", "Geography", "Advanced Mathematics"],
          CBG: ["Chemistry", "Biology", "Geography"],
          EGM: ["Economics", "Geography", "Advanced Mathematics"],
          HGL: ["History", "Geography", "English Language"],
          HKL: ["History", "Kiswahili", "English Language"],
          HGK: ["History", "Geography", "Kiswahili"],
        };

        function setAlevelByCombination(code) {
          // Auto-fill the common A-Level subject set for the selected combination.
          const selected = combinationMap[code] || [];
          aLevelContainer.innerHTML = "";
          (selected.length ? selected : ["Physics", "Chemistry", "Biology"]).forEach((subject, index) => {
            aLevelContainer.appendChild(subjectRow({ subject, grade: index === 0 ? "A" : "B", model: "core" }, "a"));
          });
        }

        function ensureDefaultRows() {
          // Create starter rows so the form is never empty when a level is opened.
          if (!aLevelContainer.children.length) {
            setAlevelByCombination(combinationInput.value || "PCB");
          }
          if (!oLevelContainer.children.length) {
            defaultOLevelSubjects.forEach(subject => {
              oLevelContainer.appendChild(subjectRow({ subject, grade: "", model: "core" }, "o"));
            });
          }
        }

        function setPathway(pathway) {
          // Switch between A-Level and O-Level input panels.
          pathwayInput.value = pathway;
          levelPrompt.classList.add("hidden");
          aLevelSection.classList.add("hidden");
          oLevelSection.classList.add("hidden");
          pathwayButtons.forEach(btn => btn.classList.remove("active"));
          const active = [...pathwayButtons].find(btn => btn.dataset.pathwayButton === pathway);
          if (active) active.classList.add("active");
          if (pathway === "a_level") aLevelSection.classList.remove("hidden");
          if (pathway === "o_level") {
            oLevelSection.classList.remove("hidden");
            if (!oLevelContainer.children.length) {
              ensureDefaultRows();
            }
          }
        }

        function populateFromPayload(payload) {
          // Load a demo student profile so the user can test the flow quickly.
          setPathway(payload.pathway || "a_level");
          document.getElementById("a_level_scheme").value = payload.a_level_scheme || "2016_plus";
          document.getElementById("combination").value = payload.combination || "";
          document.getElementById("language").value = payload.language || "both";
          document.getElementById("o_language").value = payload.language || "both";
          document.getElementById("division").value = "";
          document.getElementById("result_model").value = "standard";
          aLevelContainer.innerHTML = "";
          oLevelContainer.innerHTML = "";
          (payload.a_level_subjects || []).forEach(item => aLevelContainer.appendChild(subjectRow(item, "a")));
          (payload.o_level_subjects || []).forEach(item => oLevelContainer.appendChild(subjectRow(item, "o")));
          ensureDefaultRows();
          if (payload.combination) {
            setAlevelByCombination(payload.combination);
          }
        }

        function buildPayload() {
          // Translate form inputs into the exact JSON shape expected by FastAPI.
          const pathway = pathwayInput.value || "a_level";
          const readSubjects = (container, level) => Array.from(container.querySelectorAll(".subject-row")).map(row => ({
            subject: row.querySelector(".subject-name").value,
            grade: row.querySelector(".subject-grade").value,
            principal: true,
            level,
          }));
          return {
            pathway,
            a_level_scheme: document.getElementById("a_level_scheme").value,
            a_level_subjects: pathway === "a_level" ? readSubjects(aLevelContainer, "a_level") : [],
            o_level_subjects: pathway === "o_level" ? readSubjects(oLevelContainer, "o_level") : [],
            combination: document.getElementById("combination").value || null,
            preferred_regions: [],
            preferred_institutions: [],
            language: pathway === "a_level" ? document.getElementById("language").value : document.getElementById("o_language").value,
            equivalent_qualification: null,
            notes: pathway === "o_level"
              ? [
                  `Division: ${document.getElementById("division").value || ""}`,
                  `Result model: ${document.getElementById("result_model").value || ""}`,
                ]
              : [],
          };
        }

        function renderRecommendations(data) {
          // Turn API response JSON into readable recommendation cards.
          const recommendations = data.recommendations || [];
          const reviewCandidates = data.review_candidates || [];
          showResultsView();
          if (!recommendations.length) {
            resultSummaryEl.innerHTML = `<div class="error">Hakuna programme iliyo eligible kwa input hii.</div>`;
            resultsEl.innerHTML = reviewCandidates.length
              ? `<div class="warning">Borderline / parallel options:</div><div class="footer-note">${reviewCandidates.length} near-matches available for review.</div>`
              : `<div class="footer-note">Hii inaonyesha current inputs bado hazijafikia direct match. Jaribu combination nyingine au angalia strict requirements.</div>`;
            return;
          }
          resultSummaryEl.innerHTML = `<div class="success">${recommendations.length} programme(s) zimepata direct eligibility.</div>${reviewCandidates.length ? `<div class="warning" style="margin-top:10px;">${reviewCandidates.length} borderline/parallel options ziko chini kwa review.</div>` : ""}`;
          resultsEl.innerHTML = [...recommendations, ...reviewCandidates].map((rec) => {
            const warnings = (rec.assessment?.warnings || []).map(w => `<div class="warning">${w}</div>`).join("");
            const issues = (rec.assessment?.missing_rules || []).length ? `<div class="error">${rec.assessment.missing_rules.join("<br>")}</div>` : "";
            const matched = (rec.assessment?.matched_rules || []).slice(0, 5).join(", ") || "No matched rules listed";
            const isReview = reviewCandidates.includes(rec);
            const applyUrl = rec.institution_apply_url || rec.institution_website || "";
            const explanation = [...(rec.assessment?.why_recommended || []), ...(rec.assessment?.why_borderline || []), ...(rec.assessment?.why_not_matched || [])];
            const parallel = (rec.assessment?.parallel_courses || []).map(item => `<li>${item}</li>`).join("");
            const ruleTraces = (rec.assessment?.rule_traces || []).map(trace => `<li>${trace.passed ? "Passed" : "Failed"}: ${trace.label} (${trace.points} pts)${trace.details ? ` - ${trace.details}` : ""}</li>`).join("");
            return `
              <article class="result-card ${isReview ? "review-card" : ""}">
                <div class="result-head">
                  <div style="display:flex; gap:12px; align-items:center;">
                    <div class="rank">${rec.rank}</div>
                    <div>
                      <div class="small muted">${rec.programme.code}</div>
                      <h3 style="margin:0;">${rec.programme.name}</h3>
                      ${isReview ? `<div class="small muted">Borderline / parallel option</div>` : ""}
                      <div class="small muted">${rec.programme.institution_name} Â· ${rec.programme.region}</div>
                    </div>
                  </div>
                  <div class="confidence">${rec.assessment.confidence}% Â· ${rec.assessment.confidence_band}</div>
                </div>
                <div class="meta-grid">
                  <div><strong>User points:</strong> ${rec.student_points}</div>
                  <div><strong>Min points:</strong> ${rec.minimum_required_points}</div>
                  <div><strong>Duration:</strong> ${rec.programme.duration_years ?? "-"} years</div>
                  <div><strong>Section:</strong> ${rec.assessment.section}</div>
                  <div><strong>Tier:</strong> ${rec.programme.competition_tier}</div>
                  <div><strong>Margin:</strong> ${rec.assessment.points_margin}</div>
                </div>
                <div class="footer-note"><strong>Matched rules:</strong> ${matched}</div>
                <div class="footer-note"><strong>Rule points:</strong> ${rec.assessment.rule_points ?? 0}</div>
                ${warnings}
                ${issues}
                ${applyUrl ? `<div class="action-row"><a class="btn btn-primary" href="${applyUrl}" target="_blank" rel="noopener noreferrer">${rec.cta_label || "Apply Now"}</a></div>` : ""}
                <details class="readmore"><summary>Read more: Show why this programme was recommended</summary>
                  <div class="footer-note">
                    <ul>${explanation.map(item => `<li>${item}</li>`).join("") || "<li>No explanation available yet.</li>"}</ul>
                    <p><strong>Parallel courses:</strong></p>
                    <ul>${parallel || "<li>No similar course found yet.</li>"}</ul>
                    <p><strong>Rule trace:</strong></p>
                    <ul>${ruleTraces || "<li>No rule trace available.</li>"}</ul>
                  </div>
                </details>
              </article>
            `;
          }).join("");
        }

        document.getElementById("recommendForm").addEventListener("submit", async (event) => {
          event.preventDefault();
          resultSummaryEl.innerHTML = `<div class="muted">Ina-load recommendations...</div>`;
          resultsEl.innerHTML = "";
          showResultsView();
          try {
            const response = await fetch("/recommend", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(buildPayload()),
            });
            const data = await response.json();
            if (!response.ok) {
              throw new Error(data.detail || "Request failed");
            }
            renderRecommendations(data);
          } catch (error) {
            resultSummaryEl.innerHTML = `<div class="error">${error.message}</div>`;
          }
        });

        pathwayButtons.forEach(button => button.addEventListener("click", () => setPathway(button.dataset.pathwayButton)));
        document.querySelector('[data-add-subject="a"]').addEventListener("click", () => aLevelContainer.appendChild(subjectRow({}, "a")));
        document.querySelector('[data-add-subject="o"]').addEventListener("click", () => oLevelContainer.appendChild(subjectRow({}, "o")));
        document.getElementById("combination").addEventListener("change", () => {
          if (pathwayInput.value === "a_level" && combinationInput.value) {
            setAlevelByCombination(combinationInput.value);
          }
        });
        document.getElementById("loadExample").addEventListener("click", () => populateFromPayload(samplePayload));
        document.getElementById("clearForm").addEventListener("click", () => {
          aLevelContainer.innerHTML = "";
          oLevelContainer.innerHTML = "";
          document.getElementById("a_level_scheme").value = "2016_plus";
          document.getElementById("combination").value = "";
          document.getElementById("language").value = "both";
          document.getElementById("o_language").value = "both";
          document.getElementById("division").value = "";
          document.getElementById("result_model").value = "standard";
          pathwayInput.value = "";
          levelPrompt.classList.remove("hidden");
          aLevelSection.classList.add("hidden");
          oLevelSection.classList.add("hidden");
          resultSummaryEl.innerHTML = '<div class="muted">Form imeclear. Chagua level kisha ujaze matokeo.</div>';
          resultsEl.innerHTML = "";
          showInputView();
        });

        themeToggle.addEventListener("click", () => {
          setTheme(document.body.dataset.theme === "light" ? "dark" : "light");
        });
        document.getElementById("backToInput").addEventListener("click", showInputView);

        document.getElementById("recommendForm").reset();
        aLevelContainer.innerHTML = "";
        oLevelContainer.innerHTML = "";
        levelPrompt.classList.remove("hidden");
        setTheme(localStorage.getItem("mwongozo-theme") || "dark");
        showInputView();
      </script>
    </body>
    </html>
    """

    return (
        template.replace("__ASUBJECTS_JSON__", json.dumps(a_level_subjects_catalog))
        .replace("__OSUBJECTS_JSON__", json.dumps(o_level_subjects_catalog))
        .replace("__ODEFAULTS_JSON__", json.dumps(default_o_level_subjects))
        .replace("__GRADES_JSON__", json.dumps(grades))
        .replace("__SAMPLE_JSON__", json.dumps(sample_payload))
        .replace("__COMBO_OPTIONS__", combo_options)
    )


@app.get("/health")
def health() -> dict[str, str]:
    # Simple liveness check for deployment and debugging.
    return {"status": "ok", "engine": "mwongozo-smart"}


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


@app.get("/meta")
def meta() -> dict[str, object]:
    # Basic catalog statistics for debugging and quick inspection.
    return {
        "programmes_loaded": len(PROGRAMMES),
        "institutions_covered": sorted({programme.institution_code for programme in PROGRAMMES}),
        "pathways_supported": [item.value for item in AdmissionPathway],
        "a_level_schemes": [item.value for item in ALevelScheme],
    }


@app.get("/programmes")
def programmes() -> list[dict[str, object]]:
    # Public list of all loaded programmes with the most important fields.
    institution_map = {item.code: item for item in INSTITUTIONS}
    return [
        {
            "code": programme.code,
            "name": programme.name,
            "institution_code": programme.institution_code,
            "institution_name": programme.institution_name,
            "award_level": programme.award_level.value,
            "website": institution_map.get(programme.institution_code).website if institution_map.get(programme.institution_code) else None,
            "apply_url": institution_map.get(programme.institution_code).website if institution_map.get(programme.institution_code) else None,
            "cta_label": institution_map.get(programme.institution_code).cta_label if institution_map.get(programme.institution_code) else "Apply Now",
            "region": programme.region,
            "category": programme.category.value,
            "duration_years": programme.duration_years,
            "competition_tier": programme.competition_tier,
            "minimum_points": programme.admission_requirement.minimum_total_points,
        }
        for programme in PROGRAMMES
    ]


@app.post("/recommend")
def recommend(student: StudentInput) -> dict[str, object]:
    # Main API: evaluate the student and return ranked eligible programmes.
    try:
        student_result = student.to_student_result()
        result = engine.recommend(student_result)
        # Keep a wider borderline pool so category filters (for example Health)
        # still have visible options when strict direct matches are few.
        review = engine.review_candidates(student_result, limit=50)
        combinations = engine.suggest_combinations(student_result)
        return {
            "input": student.model_dump(),
            "loaded_programmes": len(PROGRAMMES),
            "count": len(result),
            "recommendations": [item.model_dump(mode="json") for item in result],
            "review_candidates": [item.model_dump(mode="json") for item in review],
            "combination_suggestions": [item.model_dump(mode="json") for item in combinations],
        }
    except Exception as exc:  # pragma: no cover - defensive API guard
        return JSONResponse(status_code=500, content={"detail": f"Recommendation engine failed: {exc}"})


@app.post("/recommend/grouped")
def recommend_grouped(student: StudentInput) -> dict[str, object]:
    # Same recommendations, but grouped by programme section.
    grouped = engine.recommend_grouped(student.to_student_result())
    return {
        "input": student.model_dump(),
        "loaded_programmes": len(PROGRAMMES),
        "sections": {
            section: [item.model_dump(mode="json") for item in items]
            for section, items in grouped.items()
        },
    }


@app.get("/institutions")
def institutions() -> list[dict[str, object]]:
    # Public list of institutions with official links and application CTAs.
    return [
        {
            "code": institution.code,
            "name": institution.name,
            "city": institution.city,
            "region": institution.region,
            "website": institution.website,
            "apply_url": institution.website or institution.apply_url,
            "cta_label": institution.cta_label,
        }
        for institution in INSTITUTIONS
    ]


@app.exception_handler(ValueError)
def value_error_handler(_: Request, exc: ValueError) -> JSONResponse:
    # Convert validation/runtime value errors into a clean JSON response.
    return JSONResponse(status_code=400, content={"detail": str(exc)})

