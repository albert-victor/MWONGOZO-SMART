from pathlib import Path

p = Path("backend/templates/home.html")
text = p.read_text(encoding="utf-8")

start = text.index('          <div id="loanDashboard"')
end_marker = "            </div>\n          </div>\n          </div>\n        </section>\n        <!-- Assistant -->"
end = text.index(end_marker, start)

new_block = Path("scripts/_loan_dashboard_snippet.html").read_text(encoding="utf-8")
text = text[:start] + new_block + text[end:]
p.write_text(text, encoding="utf-8")
print("patched ok", len(new_block), "chars")
