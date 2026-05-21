from pathlib import Path
p = Path("scripts/loan_render_guidance.js")
t = p.read_text(encoding="utf-8")
t = t.replace('"</motion>";', '"</div>";', 1)
t = t.replace('root.innerHTML = root.innerHTML.replace("</motion>", "</div>");\n\n', "")
p.write_text(t, encoding="utf-8")
print("ok")
