from pathlib import Path

tracker_path = Path("backend/static/loan-tracker.js")
text = tracker_path.read_text(encoding="utf-8")

helpers = Path("scripts/loan_ui_insert.js").read_text(encoding="utf-8")
# take only up to fetchGuidance (exclude broken render in insert file)
helpers_end = helpers.index("  function fetchGuidance")
helpers = helpers[:helpers_end]

render_load = Path("scripts/loan_render_guidance.js").read_text(encoding="utf-8")

start = text.index("  function fetchGuidance(level)")
end = text.index("  function renderDemoHint(refs)")
text = text[:start] + helpers + render_load + text[end:]

if "buildTrackerSubnav();" not in text:
    text = text.replace(
        'dash.classList.remove("hidden");',
        'dash.classList.remove("hidden");\n    buildTrackerSubnav();\n    setTrackerView("summary");',
        1,
    )

# today card icon
text = text.replace(
    '<span class="loan-today-card__icon">',
    '<span class="loan-today-card__icon"><i class="fa-solid fa-thumbtack" aria-hidden="true"></i>',
    1,
)

tracker_path.write_text(text, encoding="utf-8")
print("patched loan-tracker.js")
