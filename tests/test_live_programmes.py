from __future__ import annotations

from mwongozo_smart.services.live_programmes import extract_programme_names


def test_extract_programme_names_from_html() -> None:
    html = """
    <html><body>
    <select>
      <option value="1">Bachelor of Laws</option>
      <option value="2">Bachelor of Science in Computer Science</option>
    </select>
    <h2>Bachelor of Business Administration</h2>
    <p>Contact us today</p>
    </body></html>
    """
    names = extract_programme_names(html)
    assert "Bachelor of Laws" in names
    assert any("Computer Science" in n for n in names)
    assert any("Business Administration" in n for n in names)
    assert not any("contact" in n.lower() for n in names)
