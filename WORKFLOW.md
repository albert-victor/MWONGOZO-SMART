# Mwongozo Smart Workflow

This project helps a student check which university programmes they may be eligible for.

## File Structure

- `backend/app.py`: FastAPI app, homepage UI, and API routes.
- `mwongozo_smart/core/models.py`: all main data models.
- `mwongozo_smart/core/calculator.py`: counts principal subjects and points.
- `mwongozo_smart/core/rules.py`: strict eligibility rules.
- `mwongozo_smart/core/engine.py`: final recommendation workflow.
- `mwongozo_smart/data/guidebook_data.py`: programme knowledge base.
- `mwongozo_smart/data/guidebook_export_parser.py`: parser for guidebook JSON exports.
- `mwongozo_smart/data/institutions.py`: institution directory.
- `mwongozo_smart/ml/ranking_model.py`: lightweight scoring model.
- `mwongozo_smart/utils/*.py`: helpers for grades and subject combinations.
- `tests/`: automated tests for the calculator, rules, and engine.

## Step-by-Step Execution

1. The student opens the homepage at `/`.
2. The frontend asks the student to choose `A-Level` or `O-Level`.
3. The student fills subjects, grades, combination, region preference, and other notes.
4. The browser converts the form into JSON and sends it to `POST /recommend`.
5. FastAPI validates the JSON using Pydantic models.
6. `StudentInput.to_student_result()` converts request data into the internal `StudentResult` model.
7. `RecommendationEngine.recommend()` starts the recommendation process.
8. `calculator.get_principal_summary()` normalizes subject names and counts the best principal subjects.
9. `TCURuleEngine.evaluate()` checks strict programme requirements one by one.
10. Programmes that fail rules are rejected immediately.
11. Eligible programmes are scored by `RecommendationEngine._score()`.
12. The lightweight ranking model adds an estimated probability boost.
13. Recommendations are sorted by confidence, score, competition tier, and capacity.
14. The API returns ranked results to the frontend.
15. The frontend renders each recommendation card with points, confidence, warnings, and missing-rule details.

## Who Does What

- Student: enters subjects and grades.
- Frontend: collects inputs and displays results.
- API layer: receives JSON and returns recommendations.
- Calculator: prepares point totals and principal counts.
- Rules engine: decides if a programme is eligible.
- Ranking engine: orders eligible programmes from strongest to weakest.
- Data layer: stores programmes and institution metadata.

## Where Programmes Come From

- Some programmes are written manually in `guidebook_data.py`.
- More programmes can be loaded from a guidebook JSON export through `guidebook_export_parser.py`.
- The final list is created by merging both sources.

## Important Note

This system is rule-based first. The ML part is only a light scoring helper, not a fully trained admissions model yet.
