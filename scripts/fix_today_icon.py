import re
from pathlib import Path

p = Path("backend/static/loan-tracker.js")
t = p.read_text(encoding="utf-8")
t = re.sub(
    r'(<i class="fa-solid fa-thumbtack" aria-hidden="true"></i>)[^<]*</span>',
    r"\1</span>",
    t,
)
p.write_text(t, encoding="utf-8")
print("fixed today icon")
