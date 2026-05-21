from pathlib import Path

d = "div"
snippet = f"""        <!-- Help centre -->
        <section data-panel="assistant" class="hidden" aria-label="Msaada">
          <{d} class="top-bar help-topbar">
            <{d}>
              <h2 data-i18n="help_title">Kituo cha Msaada</h2>
              <p class="muted small" data-i18n="help_sub">SAM — mwongozo wa NECTA, mapendekezo, vyuo, na HESLB.</p>
            </{d}>
          </{d}>
          <{d} class="help-hero card glass">
            <span class="help-hero__badge"><i class="fa-solid fa-sparkles" aria-hidden="true"></i> <span data-i18n="help_badge">Msaada hai</span></span>
            <h3 data-i18n="help_hero_title">Uliza, chagua mada, au enda moja kwa moja</h3>
            <p class="muted small" data-i18n="help_hero_p">Majibu ya haraka yaliyopangwa — mwongozo wa vitendo kutoka MWONGOZO SMART.</p>
          </{d}>
          <ul class="help-quick-grid" id="helpQuickGrid" aria-label="Vitendo vya haraka">
            <li><button type="button" class="help-quick-card" data-help-go="input"><span class="help-quick-card__icon"><i class="fa-solid fa-pen-to-square" aria-hidden="true"></i></span><strong data-i18n="nav_input">Matokeo</strong><span data-i18n="help_quick_input">Jaza / pakua NECTA</span></button></li>
            <li><button type="button" class="help-quick-card" data-help-go="results"><span class="help-quick-card__icon"><i class="fa-solid fa-list-check" aria-hidden="true"></i></span><strong data-i18n="nav_results">Mapendekezo</strong><span data-i18n="help_quick_results">Angalia orodha</span></button></li>
            <li><button type="button" class="help-quick-card" data-help-go="directory"><span class="help-quick-card__icon"><i class="fa-solid fa-building-columns" aria-hidden="true"></i></span><strong data-i18n="nav_directory">Vyuo</strong><span data-i18n="help_quick_dir">Chunguza programme</span></button></li>
            <li><button type="button" class="help-quick-card" data-help-go="loan"><span class="help-quick-card__icon"><i class="fa-solid fa-hand-holding-dollar" aria-hidden="true"></i></span><strong data-i18n="nav_loan">Mkopo</strong><span data-i18n="help_quick_loan">Mwongozo HESLB</span></button></li>
          </ul>
          <{d} class="help-layout">
            <aside class="help-topics-panel card glass">
              <label class="help-search-wrap">
                <i class="fa-solid fa-magnifying-glass" aria-hidden="true"></i>
                <input type="search" id="helpTopicSearch" class="help-search" data-i18n-placeholder="help_search_ph" placeholder="Tafuta mada…" autocomplete="off" />
              </label>
              <{d} id="helpTopicList" class="help-topic-list" role="list"></{d}>
            </aside>
            <{d} class="help-chat-panel card glass">
              <{d} class="help-chat-head">
                <{d} class="help-chat-head__brand">
                  <span class="help-sam-avatar" aria-hidden="true">SAM</span>
                  <{d}>
                    <strong data-i18n="chat_head">SAM — msaada wa haraka</strong>
                    <p class="muted small help-chat-head__sub" data-i18n="chat_intro">Uliza kuhusu NECTA, TCU, vyuo, au HESLB.</p>
                  </{d}>
                </{d}>
              </{d}>
              <{d} class="help-chat-shell">
                <{d} id="chatMessages" class="help-chat-log chat-log" role="log" aria-live="polite"></{d}>
                <{d} class="help-chat-foot">
                  <{d} id="helpChatChips" class="help-chips" aria-label="Maswali ya haraka"></{d}>
                  <{d} class="chat-input-row">
                    <input type="text" id="chatInput" data-i18n-placeholder="chat_ph" placeholder="Andika swali…" autocomplete="off" />
                    <button type="button" class="btn btn-primary btn-icon-send" id="chatSend" aria-label="Tuma"><i class="fa-solid fa-paper-plane" aria-hidden="true"></i></button>
                  </{d}>
                </{d}>
              </{d}>
            </{d}>
          </{d}>
        </section>
"""

home = Path(__file__).resolve().parents[1] / "backend" / "templates" / "home.html"
text = home.read_text(encoding="utf-8")
start = text.index("        <!-- Assistant -->")
end = text.index("        </section>", start) + len("        </section>")
home.write_text(text[:start] + snippet + text[end:], encoding="utf-8")
print("patched home.html")
