"""HESLB loan guidance content — official links and educational steps only.

Does not invent HESLB policy. Students must confirm deadlines and requirements on:
- https://www.heslb.go.tz/
- https://olas.heslb.go.tz/
"""

from __future__ import annotations

from typing import Any

from mwongozo_smart.loan_tracking import OFFICIAL_LINKS

_VALID_LEVELS = frozenset({"a_level", "o_level"})
_VALID_LANGS = frozenset({"sw", "en"})


def _pick(lang: str, sw: str, en: str) -> str:
    return sw if lang == "sw" else en


def build_loan_guidance(exam_level: str = "o_level", language: str = "sw") -> dict[str, Any]:
    level = exam_level if exam_level in _VALID_LEVELS else "o_level"
    lang = language if language in _VALID_LANGS else "sw"

    if level == "o_level":
        sections = _o_level_sections(lang)
        checklist = _o_level_checklist(lang)
        faq = _o_level_faq(lang)
        pathway = _o_level_pathway(lang)
        olas_steps: list[dict[str, Any]] = []
    else:
        sections = _a_level_sections(lang)
        checklist = _a_level_checklist(lang)
        faq = _a_level_faq(lang)
        pathway = _a_level_pathway(lang)
        olas_steps = _olas_steps(lang)

    return {
        "exam_level": level,
        "language": lang,
        "title": _pick(
            lang,
            "Mwongozo wa mkopo wa HESLB — O-Level",
            "HESLB loan guidance — O-Level",
        )
        if level == "o_level"
        else _pick(
            lang,
            "Mwongozo wa mkopo wa HESLB — A-Level / Chuo",
            "HESLB loan guidance — A-Level / University",
        ),
        "subtitle": _pick(
            lang,
            "Maandalizi ya nyaraka na hatua za baadaye — thibitisha kila mwaka kwenye tovuti rasmi.",
            "Document preparation and next steps — confirm annually on official sites.",
        ),
        "transparency_banner": _pick(
            lang,
            "Mwongozo huu hau badili OLAS wala HESLB. Hakuna upakiaji wa vyeti hapa — tumia tovuti rasmi kwa maombi halisi.",
            "This guidance does not replace OLAS or HESLB. No certificate uploads here — use official sites for real applications.",
        ),
        "official_links": OFFICIAL_LINKS,
        "sections": sections,
        "document_checklist": checklist,
        "faq": faq,
        "pathway_steps": pathway,
        "olas_steps": olas_steps,
        "pathway_intro": _pathway_intro(lang, level),
        "tracker_note": _pick(
            lang,
            "Ukiwa tayari kufuatilia mfano wa maombi (demo), tumia kichupo «Fuatilia (demo)» na nambari HSL-2026-xxxxx.",
            "When ready to try a sample application tracker (demo), use the «Track (demo)» tab with an HSL-2026-xxxxx reference.",
        ),
    }


def _o_level_sections(lang: str) -> list[dict[str, Any]]:
    return [
        {
            "id": "when",
            "title": _pick(lang, "Mkopo wa HESLB unahusiana lini?", "When does HESLB funding apply?"),
            "body": _pick(
                lang,
                "Bodi ya Mikopo ya Elimu ya Juu (HESLB) inafadhili wanafunzi wa vyuo vya elimu ya juu (chuo kikuu, kolleji, nk.) "
                "baada ya kukamilisha A-Level au njia nyingine za kuingia chuo. Kama mwanafunzi wa O-Level, lengo lako sasa ni "
                "kujiandaa: NIDA (NIN), cheti cha kuzaliwa (RITA), matokeo ya NECTA, na kuelewa mchakato wa baadaye.",
                "The Higher Education Students' Loans Board (HESLB) funds students in higher-education institutions "
                "after A-Level or other entry routes. As an O-Level student, focus on preparation: NIDA (NIN), "
                "birth certificate (RITA), NECTA results, and understanding the later process.",
            ),
        },
        {
            "id": "nida",
            "title": _pick(lang, "NIDA — Nambari ya Utambulisho (NIN)", "NIDA — National Identification Number (NIN)"),
            "body": _pick(
                lang,
                "HESLB inahitaji NIN kwenye mchakato wa maombi. Pata au thibitisha NIN yako mapema — hii inapunguza kuchelewa "
                "wakati wa OLAS baada ya kupata nafasi chuo.",
                "HESLB requires NIN during applications. Obtain or verify your NIN early — this reduces delays on OLAS after university admission.",
            ),
            "links": [{"label": "NIDA", "url": "https://www.nida.go.tz/", "logo": "/static/partners/nida.png"}],
        },
        {
            "id": "rita",
            "title": _pick(lang, "RITA — Cheti cha kuzaliwa", "RITA — Birth certificate"),
            "body": _pick(
                lang,
                "Miongozo ya HESLB mara nyingi yanahitaji cheti cha kuzaliwa kilichothibitishwa kupitia RITA. Hakikisha majina "
                "yanalingana na NIDA na vyeti vya NECTA.",
                "HESLB guidelines often require a RITA-certified birth certificate. Ensure names match NIDA and NECTA certificates.",
            ),
            "links": [{"label": "RITA", "url": "https://www.rita.go.tz/", "logo": "/static/partners/rita.png"}],
        },
        {
            "id": "family",
            "title": _pick(lang, "Mzazi / mlezi na kipato", "Parent / guardian and income"),
            "body": _pick(
                lang,
                "Maombi ya mkopo yanahusisha taarifa za mzazi au mlezi na uthibitisho wa kipato inapohitajika. Andaa nambari ya simu "
                "inayopatikana na nyaraka za msaada za familia mapema.",
                "Loan applications involve parent or guardian details and income verification when required. Prepare a reachable "
                "phone number and family supporting documents early.",
            ),
        },
        {
            "id": "special",
            "title": _pick(lang, "Makundi maalum", "Special categories"),
            "body": _pick(
                lang,
                "HESLB inataja makundi kama yatima, ulemavu, kipato cha chini, na familia ya mzazi mmoja. Soma miongozo ya mwaka "
                "husika kwenye heslb.go.tz — vigezo hubadilika.",
                "HESLB lists categories such as orphan, disability, low income, and single-parent households. Read the current "
                "year's guidelines on heslb.go.tz — criteria change.",
            ),
            "links": [{"label": "HESLB guidelines", "url": "https://www.heslb.go.tz/application_guideline"}],
        },
    ]


def _a_level_sections(lang: str) -> list[dict[str, Any]]:
    return [
        {
            "id": "olas",
            "title": _pick(lang, "OLAS — mfumo wa maombi", "OLAS — application system"),
            "body": _pick(
                lang,
                "Maombi ya mkopo hufanywa kupitia OLAS (Online Loan Application & Management System). Fungua akaunti, "
                "kamilisha wasifu, pakia nyaraka kama inavyoelekezwa, na wasilisha kabla ya deadline rasmi.",
                "Loan applications are submitted through OLAS. Create an account, complete your profile, upload documents "
                "as directed, and submit before the official deadline.",
            ),
            "links": [
                {"label": "OLAS", "url": "https://olas.heslb.go.tz/"},
                {"label": "HESLB application link", "url": "https://www.heslb.go.tz/loanapplication/application-link"},
            ],
        },
        {
            "id": "documents",
            "title": _pick(lang, "Nyaraka za kawaida", "Common documents"),
            "body": _pick(
                lang,
                "Kwa kawaida utahitaji: NIN (NIDA), cheti cha kuzaliwa (RITA), matokeo ya NECTA, taarifa za chuo/programu, "
                "na nyaraka za mzazi/mlezi. Orodha kamili iko kwenye miongozo ya mwaka husika.",
                "You typically need: NIN (NIDA), birth certificate (RITA), NECTA results, institution/programme details, "
                "and parent/guardian documents. See the current year's official guideline for the full list.",
            ),
        },
        {
            "id": "names",
            "title": _pick(lang, "Majina yanapaswa kulingana", "Names must match"),
            "body": _pick(
                lang,
                "Makosa ya kawaida: tofauti kati ya majina kwenye NIDA, RITA, na NECTA. Rekebisha kabla ya kuwasilisha OLAS.",
                "Common error: mismatched names across NIDA, RITA, and NECTA. Fix before submitting on OLAS.",
            ),
        },
        {
            "id": "batch",
            "title": _pick(lang, "Batch One / Batch Two", "Batch One / Batch Two"),
            "body": _pick(
                lang,
                "HESLB inachakata maombi kwa makundi (batch). Fuatilia tangazo rasmi — usitegemee utabiri wa mfumo huu (demo).",
                "HESLB processes applications in batches. Follow official announcements — do not rely on this system's demo predictions.",
            ),
        },
        {
            "id": "appeal",
            "title": _pick(lang, "Rufaa", "Appeal"),
            "body": _pick(
                lang,
                "Ikiwa maombi yamekataliwa, soma sababu kwenye OLAS na angalia dirisha la rufaa kwenye miongozo ya HESLB.",
                "If rejected, read reasons on OLAS and check the appeal window in HESLB guidelines.",
            ),
        },
    ]


def _o_level_checklist(lang: str) -> list[dict[str, str]]:
    items = [
        ("nin", "Pata au thibitisha NIN (NIDA)", "Obtain or verify NIN (NIDA)", "https://www.nida.go.tz/"),
        ("rita", "Cheti cha kuzaliwa — thibitisha kwa RITA", "Birth certificate — certify via RITA", "https://www.rita.go.tz/"),
        ("necta", "Hifadhi nakala za matokeo ya CSEE (NECTA)", "Keep copies of CSEE results (NECTA)", "https://www.necta.go.tz/"),
        ("names", "Hakikisha majina yanalingana kwenye vyeti vyote", "Ensure names match on all certificates", ""),
        ("parent", "Andaa taarifa za mzazi/mlezi na simu inayopatikana", "Prepare guardian details and reachable phone", ""),
        ("heslb", "Soma miongozo ya HESLB ya mwaka wa maombi", "Read HESLB guidelines for your application year", "https://www.heslb.go.tz/application_guideline"),
        ("path", "Panga njia: ACSEE, diploma, au college — kisha chuo", "Plan route: ACSEE, diploma, or college — then university", ""),
    ]
    return [
        {
            "id": item[0],
            "text": _pick(lang, item[1], item[2]),
            **({"link": item[3]} if item[3] else {}),
        }
        for item in items
    ]


def _a_level_checklist(lang: str) -> list[dict[str, str]]:
    items = [
        ("olas_account", "Fungua akaunti OLAS", "Create OLAS account", "https://olas.heslb.go.tz/"),
        ("nin", "Weka NIN sahihi (tarakimu 20)", "Enter valid NIN (20 digits)", "https://www.nida.go.tz/"),
        ("rita", "Cheti cha kuzaliwa (RITA) kama inavyohitajika", "Birth certificate (RITA) if required", "https://www.rita.go.tz/"),
        ("necta", "Matokeo ya ACSEE / diploma", "ACSEE or diploma results", "https://www.necta.go.tz/"),
        ("admission", "Taarifa za kujiunga chuo (programu, chuo)", "University admission details (programme, institution)", ""),
        ("guardian", "Taarifa na nyaraka za mzazi/mlezi", "Parent/guardian details and documents", ""),
        ("submit", "Wasilisha OLAS kabla ya deadline", "Submit OLAS before deadline", "https://www.heslb.go.tz/loanapplication/application-link"),
        ("track", "Fuatilia hali kwenye OLAS kila siku", "Monitor status on OLAS daily", "https://olas.heslb.go.tz/"),
    ]
    return [
        {
            "id": item[0],
            "text": _pick(lang, item[1], item[2]),
            **({"link": item[3]} if item[3] else {}),
        }
        for item in items
    ]


def _faq(lang: str, cat_sw: str, cat_en: str, q_sw: str, q_en: str, a_sw: str, a_en: str) -> dict[str, str]:
    return {
        "category": _pick(lang, cat_sw, cat_en),
        "question": _pick(lang, q_sw, q_en),
        "answer": _pick(lang, a_sw, a_en),
    }


def _path_step(
    lang: str,
    step: int,
    title_sw: str,
    title_en: str,
    summary_sw: str,
    summary_en: str,
    detail_sw: str,
    detail_en: str,
    read_more_sw: str = "",
    read_more_en: str = "",
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "step": step,
        "title": _pick(lang, title_sw, title_en),
        "summary": _pick(lang, summary_sw, summary_en),
        "detail": _pick(lang, detail_sw, detail_en),
    }
    if read_more_sw or read_more_en:
        item["read_more"] = _pick(lang, read_more_sw, read_more_en)
    return item


def _pathway_intro(lang: str, level: str) -> str:
    if level == "o_level":
        return _pick(
            lang,
            "Njia hii inaelezea maandalizi kutoka CSEE hadi unapofika hatua ya chuo na OLAS. Bofya «Soma zaidi» kwa maelezo ya kina kila hatua.",
            "This pathway explains preparation from CSEE until university and OLAS. Use Read more on each step for detail.",
        )
    return _pick(
        lang,
        "Njia hii inafuatana na mchakato wa OLAS kama unavyoonekana kwenye miongozo ya HESLB — soma kila hatua na thibitisha kwenye tovuti rasmi.",
        "This pathway follows the OLAS process as described in HESLB guidelines — read each step and confirm on official sites.",
    )


def _o_level_faq(lang: str) -> list[dict[str, str]]:
    c_gen, c_prep, c_doc = "Jumla", "Maandalizi", "Nyaraka"
    c_gen_e, c_prep_e, c_doc_e = "General", "Preparation", "Documents"
    return [
        _faq(
            lang, c_gen, c_gen_e,
            "Je, naweza kuomba mkopo nikiwa O-Level tu?",
            "Can I apply for a loan while only at O-Level?",
            "HESLB inafadhili elimu ya juu (chuo, kolleji) baada ya kupata nafasi. Kama O-Level, lengo ni maandalizi: NIDA, RITA, NECTA, na kuelewa mchakato.",
            "HESLB funds higher education after placement. At O-Level, focus on preparation: NIDA, RITA, NECTA, and understanding the process.",
        ),
        _faq(
            lang, c_gen, c_gen_e,
            "Mkopo na ufadhili wa serikali ni kitu kimoja?",
            "Is a loan the same as a government scholarship?",
            "HESLB hutoa mkopo unaolipwa baadaye; ufadhili mwingine unaweza kuwa hiba au programu nyingine. Soma miongozo ya mwaka husika.",
            "HESLB provides repayable loans; other funding may be grants or other programmes. Read the current year's guidelines.",
        ),
        _faq(
            lang, c_prep, c_prep_e,
            "NIN inahitajika lini?",
            "When is NIN required?",
            "Pata NIN mapema kwenye NIDA — itatumika kwenye OLAS na uthibitisho wa uraia baada ya kujiunga chuo.",
            "Obtain NIN early via NIDA — it is used on OLAS and for verification after university admission.",
        ),
        _faq(
            lang, c_prep, c_prep_e,
            "Nahitaji cheti cha kuzaliwa lini?",
            "When do I need a birth certificate?",
            "Mara nyingi unahitaji cheti kilichothibitishwa na RITA kabla ya OLAS. Usisubiri wiki ya mwisho ya maombi.",
            "You often need a RITA-certified certificate before OLAS. Do not wait until the final application week.",
        ),
        _faq(
            lang, c_doc, c_doc_e,
            "Nini kama majina yangu hayalingani?",
            "What if my names do not match?",
            "Hii ni kosa la kawaida. Rekebisha kupitia NIDA, RITA, au NECTA kabla ya maombi — OLAS inalinganisha vyeti.",
            "This is a common issue. Correct via NIDA, RITA, or NECTA before applying — OLAS cross-checks documents.",
        ),
        _faq(
            lang, c_doc, c_doc_e,
            "Nyaraka za mzazi/mlezi ni zipi?",
            "Which parent or guardian documents are needed?",
            "Kwa kawaida: taarifa za mzazi/mlezi, simu inayopatikana, na uthibitisho wa kipato inapohitajika. Orodha kamili iko kwenye miongozo ya mwaka.",
            "Typically: guardian details, reachable phone, and income proof when required. See the full list in the year's guideline.",
        ),
        _faq(
            lang, c_prep, c_prep_e,
            "ACSEE, diploma, au college — nijue vipi?",
            "How do I choose ACSEE, diploma, or college?",
            "Chagua kulingana na malengo ya kazi na programu unayotaka baadaye. Mwongozo huu unasaidia maandalizi ya nyaraka kwa njia yoyote.",
            "Choose based on career goals and future programme. This guidance helps document preparation for any route.",
        ),
        _faq(
            lang, c_gen, c_gen_e,
            "Je, mfumo huu unaomba mkopo kwa niaba yangu?",
            "Does this system apply for a loan on my behalf?",
            "Hapana. Hakuna upakiaji wa vyeti wala uwasilishaji wa OLAS hapa — tumia OLAS na heslb.go.tz kwa maombi halisi.",
            "No. There is no certificate upload or OLAS submission here — use OLAS and heslb.go.tz for real applications.",
        ),
        _faq(
            lang, c_gen, c_gen_e,
            "Nini maana ya «Fuatilia (demo)»?",
            "What does «Track (demo)» mean?",
            "Ni mfano wa dashibodi ya maendeleo (nambari HSL-2026-xxxxx) ili ujifunze hatua — si data halisi ya HESLB.",
            "A sample progress dashboard (HSL-2026-xxxxx reference) to learn the steps — not real HESLB data.",
        ),
        _faq(
            lang, c_doc, c_doc_e,
            "Naweza kuhifadhi maendeleo ya checklist?",
            "Can I save checklist progress?",
            "Ndiyo — kifaa chako kinahifadhi alama za checklist (local). Ingia tena ukurasa huu kuendelea.",
            "Yes — your device saves checklist ticks locally. Return to this page to continue.",
        ),
    ]


def _a_level_faq(lang: str) -> list[dict[str, str]]:
    c_gen, c_olas, c_doc, c_batch = "Jumla", "OLAS", "Nyaraka", "Batch & malipo"
    c_gen_e, c_olas_e, c_doc_e, c_batch_e = "General", "OLAS", "Documents", "Batch & payment"
    return [
        _faq(
            lang, c_olas, c_olas_e,
            "Wapi ninaomba mkopo?",
            "Where do I apply for a loan?",
            "Kupitia OLAS (olas.heslb.go.tz). Fungua akaunti, kamilisha wasifu, pakia nyaraka, na wasilisha kabla ya deadline iliyotangazwa.",
            "Through OLAS (olas.heslb.go.tz). Create an account, complete your profile, upload documents, and submit before the announced deadline.",
        ),
        _faq(
            lang, c_olas, c_olas_e,
            "Nimesahau nenosiri la OLAS — nifanye nini?",
            "I forgot my OLAS password — what should I do?",
            "Tumia kiungo cha «Forgot password» kwenye ukurasa wa kuingia OLAS. Usitumie akaunti ya mtu mwingine.",
            "Use Forgot password on the OLAS login page. Do not use someone else's account.",
        ),
        _faq(
            lang, c_olas, c_olas_e,
            "Nyaraka zinakataliwa kwenye OLAS — kwa nini?",
            "Why are documents rejected on OLAS?",
            "Mara nyingi: PDF si wazi, imekata pembe, au majina hayalingani. Pakia upya nakala iliyoskanwa vizuri baada ya kurekebisha.",
            "Often: unclear PDF, cropped scan, or name mismatch. Re-upload a clear scan after corrections.",
        ),
        _faq(
            lang, c_doc, c_doc_e,
            "NIN yangu inakataliwa — sababu?",
            "Why is my NIN rejected?",
            "Hakikisha tarakimu 20, haijaandikwa na nafasi, na inalingana na NIDA. Nambari isiyo sahihi husitisha maombi.",
            "Ensure 20 digits, no spaces, and match with NIDA. Invalid NIN blocks the application.",
        ),
        _faq(
            lang, c_batch, c_batch_e,
            "Nini maana ya Batch One na Batch Two?",
            "What are Batch One and Batch Two?",
            "Ni makundi ya uchakataji wa maombi. Tarehe na orodha hutangazwa na HESLB — angalia OLAS na tovuti rasmi, si uvumi.",
            "Processing groups for applications. Dates and lists are announced by HESLB — check OLAS and official notices, not rumours.",
        ),
        _faq(
            lang, c_batch, c_batch_e,
            "Malipo ya mkopo yataanza lini?",
            "When does loan disbursement start?",
            "Baada ya uthibitisho na makundi ya uchakataji. Fuatilia OLAS na tangazo la chuo — tarehe hubadilika kila mwaka.",
            "After verification and processing batches. Monitor OLAS and your institution — dates change each year.",
        ),
        _faq(
            lang, c_gen, c_gen_e,
            "Je, chuo binafsi kinastahili?",
            "Do private universities qualify?",
            "Soma miongozo ya mwaka husika kwenye heslb.go.tz — orodha ya vyuo na programu zinastahili hubadilika.",
            "Read the current guideline on heslb.go.tz — eligible institutions and programmes change.",
        ),
        _faq(
            lang, c_gen, c_gen_e,
            "Naweza kubadilisha programu baada ya kuwasilisha?",
            "Can I change programme after submitting?",
            "Fuata maelekezo ya OLAS na HESLB kwa mwaka husika — mabadiliko yanategemea dirisha la marekebisho.",
            "Follow OLAS and HESLB instructions for that year — changes depend on the correction window.",
        ),
        _faq(
            lang, c_gen, c_gen_e,
            "Naweza kurufaa ikiwa nimekataliwa?",
            "Can I appeal if rejected?",
            "Ndio, ikiwa dirisha la rufaa limefunguliwa. Soma sababu kwenye OLAS na andaa nyaraka zilizorekebishwa.",
            "Yes, when the appeal window is open. Read reasons on OLAS and prepare corrected documents.",
        ),
        _faq(
            lang, c_doc, c_doc_e,
            "Taarifa za mzazi/mlezi — nani awekwe?",
            "Whose details should I enter for parent/guardian?",
            "Mlezi anayekusaidia kifedha au mzazi kama inavyoelekezwa kwenye fomu. Simu lazima ipatikane wakati wa uthibitisho.",
            "The guardian who supports you financially or parent as directed on the form. Phone must be reachable for verification.",
        ),
        _faq(
            lang, c_olas, c_olas_e,
            "Je, naweza kutumia simu ya mkononi kwa OLAS?",
            "Can I use a mobile phone for OLAS?",
            "Ndiyo, lakini pakia PDF wazi; tumia mtandao thabiti na hifadhi nakala za nyaraka kabla ya kupakia.",
            "Yes, but upload clear PDFs; use a stable connection and keep document copies before uploading.",
        ),
        _faq(
            lang, c_gen, c_gen_e,
            "Tofauti ya mwongozo huu na kuuliza tu ofisini?",
            "How is this guidance different from only asking at an office?",
            "Hapa una hatua, FAQ, checklist, na viungo rasmi kwa mpangilio. Ofisini bado thibitisha tarehe za mwaka husika.",
            "Here you get steps, FAQs, checklist, and official links in order. Still confirm current-year dates at the office or online.",
        ),
    ]


def _o_level_pathway(lang: str) -> list[dict[str, Any]]:
    return [
        _path_step(
            lang, 1, "CSEE (O-Level)", "CSEE (O-Level)",
            "Maliza mitihani na hifadhi matokeo ya NECTA.",
            "Finish exams and keep NECTA results.",
            "Matokeo ya CSEE yatahitajika baadaye kama uthibitisho wa masomo ya sekondari.",
            "CSEE results will be required later as proof of secondary education.",
            "Pakua/hifadhi nakala za PDF kutoka NECTA, na hakikisha majina yako yanaonekana wazi. "
            "Ikiwa kuna makosa, fuata mchakato wa marekebisho wa NECTA kabla ya kuingia chuo.",
            "Download/keep PDF copies from NECTA and ensure names are clear. If there are errors, follow NECTA correction before higher education.",
        ),
        _path_step(
            lang, 2, "Chagua njia ya baadaye", "Choose your next pathway",
            "ACSEE, diploma, au college — chagua kulingana na malengo.",
            "ACSEE, diploma, or college — choose based on goals.",
            "Kila njia inaongoza kwenye elimu ya juu; maandalizi ya nyaraka yanafanana.",
            "Each route leads to higher education; document preparation is similar.",
            "Zungumza na mwalimu wa ushauri wa masomo, angalia mahitaji ya programu unayotaka, "
            "na anza kuandaa NIDA na RITA mapema — usisubiri mwaka wa maombi ya mkopo.",
            "Talk to a guidance teacher, check programme requirements, and start NIDA and RITA early — do not wait until the loan application year.",
        ),
        _path_step(
            lang, 3, "NIDA (NIN)", "NIDA (NIN)",
            "Pata au thibitisha Nambari ya Utambulisho.",
            "Obtain or verify your National Identification Number.",
            "NIN inahitajika kwenye OLAS baada ya kupata nafasi chuo.",
            "NIN is required on OLAS after university placement.",
            "Tembelea kituo cha NIDA kilicho karibu, hakikisha majina yanalingana na cheti cha kuzaliwa, "
            "na hifadhi nambari yako kwa usalama — usimtumie mtu usiomjuwa.",
            "Visit a nearby NIDA centre, ensure names match your birth certificate, and store your number safely — do not share with strangers.",
        ),
        _path_step(
            lang, 4, "RITA — cheti cha kuzaliwa", "RITA — birth certificate",
            "Thibitisha cheti cha kuzaliwa kupitia RITA.",
            "Certify your birth certificate through RITA.",
            "Miongozo ya HESLB mara nyingi yanahitaji cheti kilichothibitishwa.",
            "HESLB guidelines often require a certified certificate.",
            "Tengeneza nakala iliyoidhinishwa kabla ya msongamano wa maombi. Majina lazima yalingane na NIDA na NECTA.",
            "Obtain certified copies before application rush periods. Names must match NIDA and NECTA.",
        ),
        _path_step(
            lang, 5, "Baada ya nafasi chuo", "After university placement",
            "Fungua OLAS na fuata miongozo ya mwaka.",
            "Open OLAS and follow that year's guideline.",
            "Maombi ya mkopo hufanywa baada ya kujiunga chuo — si wakati wa O-Level peke yake.",
            "Loan applications happen after admission — not at O-Level alone.",
            "Wakati umepata nafasi, tembelea olas.heslb.go.tz, soma Application Guideline ya mwaka husika, "
            "na tumia kichupo «Fuatilia (demo)» hapa kujifunza hatua kabla ya kuingia OLAS halisi.",
            "Once placed, visit olas.heslb.go.tz, read that year's Application Guideline, and use the Track (demo) tab here to learn steps before real OLAS.",
        ),
    ]


def _a_level_pathway(lang: str) -> list[dict[str, Any]]:
    return [
        _path_step(
            lang, 1, "Matokeo na nafasi chuo", "Results and placement",
            "Thibitisha chuo na programu uliyopewa.",
            "Confirm your institution and programme.",
            "Hakikisha taarifa za kujiunga zinalingana na OLAS.",
            "Ensure admission details match what you will enter on OLAS.",
            "Hifadhi barua ya kujiunga, nambari ya usajili wa chuo, na programu — zitatumika kwenye sehemu ya chuo/programu kwenye OLAS.",
            "Keep your admission letter, university registration number, and programme — needed for the institution section on OLAS.",
        ),
        _path_step(
            lang, 2, "Soma miongozo ya mwaka", "Read the year's guideline",
            "Pakua Application Guideline kutoka heslb.go.tz.",
            "Download the Application Guideline from heslb.go.tz.",
            "Vigezo, tarehe, na orodha ya nyaraka hubadilika kila mwaka.",
            "Criteria, dates, and document lists change every year.",
            "Usitumie PDF ya mwaka uliopita. Angalia makundi maalum (yatima, ulemavu, kipato cha chini) ikiwa unastahili.",
            "Do not use last year's PDF. Check special categories (orphan, disability, low income) if you qualify.",
        ),
    ]


def _olas_steps(lang: str) -> list[dict[str, Any]]:
    return [
        _path_step(
            lang, 1, "Akaunti OLAS", "OLAS account",
            "Jisajili kwa barua pepe na simu inayopatikana.",
            "Register with email and a reachable phone number.",
            "Utapokea ujumbe wa uthibitisho — usitumie barua pepe ya mtu mwingine.",
            "You will receive verification messages — do not use someone else's email.",
            "Weka nenosiri imara na usihifadhi kwenye simu isiyolindwa. Ikiwa umesahau, tumia Forgot password.",
            "Use a strong password. If forgotten, use Forgot password on the login page.",
        ),
        _path_step(
            lang, 2, "Wasifu binafsi", "Personal profile",
            "Jaza taarifa zote — lazima zilingane na NIDA.",
            "Complete all fields — they must match NIDA.",
            "Makosa ya majina hapa husababisha kukataliwa baadaye.",
            "Name errors here cause later rejection.",
            "Linganisha kila jina na kadi ya NIDA na cheti cha RITA kabla ya kubofya endelea.",
            "Compare every name with your NIDA card and RITA certificate before continuing.",
        ),
        _path_step(
            lang, 3, "Chuo na programu", "Institution and programme",
            "Chagua chuo na programu uliyopewa nafasi.",
            "Select the institution and programme you were placed in.",
            "Ikiwa taarifa si sahihi, rekebisha na chuo kwanza.",
            "If details are wrong, correct with your institution first.",
            "Usichague programu «ya ndoto» isiyolingana na nafasi — hii inachelewesha uthibitisho.",
            "Do not select a dream programme that does not match placement — this delays verification.",
        ),
        _path_step(
            lang, 4, "Pakia nyaraka", "Upload documents",
            "PDF wazi, kamili, na zenye ukubwa unaokubalika.",
            "Clear, complete PDFs within allowed size.",
            "Kila faili iwe inayosomeka — skana mpya ikiwa ya zamani imeharibika.",
            "Each file must be readable — rescan if old copies are faded.",
            "Wanafunzi wengi wanakataliwa kwa picha za simu zenye vivuli. Tumia skana au programu ya skana ya simu.",
            "Many rejections are phone photos with shadows. Use a scanner or proper scanning app.",
        ),
        _path_step(
            lang, 5, "Kagua na wasilisha", "Review and submit",
            "Kagua mara mbili kisha wasilisha kabla ya deadline.",
            "Review twice then submit before the deadline.",
            "Baada ya kuwasilisha, hifadhi nambari ya kumbukumbu ya OLAS.",
            "After submitting, save your OLAS reference number.",
            "Usisubiri siku ya mwisho — mfumo unaweza kuwa na msongamano. Wasilisha mapema ukiwa na nyaraka kamili.",
            "Do not wait for the last day — the system may be busy. Submit early when documents are complete.",
        ),
        _path_step(
            lang, 6, "Fuatilia hali", "Monitor status",
            "Angalia OLAS mara kwa mara kwa uthibitisho na batch.",
            "Check OLAS regularly for verification and batch status.",
            "HESLB inatangaza batch kwenye tovuti — demo hapa haibadili OLAS.",
            "HESLB announces batches on its website — the demo here does not change OLAS.",
            "Wakati hali inasema «pending verification», hakikisha simu ya mzazi inapatikana — watakapigiwa wakati mwingine.",
            "When status shows pending verification, ensure your guardian's phone is reachable — they may be called.",
        ),
    ]
