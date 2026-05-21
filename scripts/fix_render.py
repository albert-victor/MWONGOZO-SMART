from pathlib import Path

p = Path("scripts/loan_render_guidance.js")
t = p.read_text(encoding="utf-8")
t = t.replace("</motion></motion>", "</div></motion>")
t = t.replace("</motion></motion>", "</motion></motion>")
t = t.replace("</motion></motion>", "</motion></motion>")
t = t.replace("</motion>", "</motion>")
t = t.replace("</motion>", "")
t = t.replace("</div></motion>", "</motion></div>")
t = t.replace("</motion></motion>", "</motion></motion>")
# simpler
t = p.read_text(encoding="utf-8")
t = t.replace('"</span></p></div></motion>"', '"</span></p></motion></motion>"')
t = t.replace('"</span></p></motion></motion>"', '"</span></p></motion></motion>"')
t = t.replace('"</span></p></div></motion>"', '"</span></p></motion></motion>"')
lines = t.splitlines()
out = []
for line in lines:
    if "docsHtml = docsHtml.replace" in line:
        continue
    line = line.replace("</motion>", "")
    line = line.replace('"</span></p></div></motion>"', '"</span></p></motion></motion>"')
    line = line.replace('"</span></p></motion></motion>"', '"</span></p></div></div>"')
    out.append(line)
p.write_text("\n".join(out) + "\n", encoding="utf-8")
print("fixed")
