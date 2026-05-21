/**
 * News & deadlines — portfolio cards on landing (images: Unsplash, education Tanzania context).
 */
(function (global) {
  "use strict";

  global.MWONGOZO_NEWS = [
    {
      id: "tcu",
      category: "TCU",
      tag: "deadline",
      date: "2026",
      title_sw: "Mwongozo wa kujiunga",
      title_en: "Admission guide",
      desc_sw:
        "Angalia dirisha la maombi la taasisi husika na Guidebook la mwaka wa masomo unaofuata.",
      desc_en:
        "Check each institution's application window and the Guidebook for the upcoming academic year.",
      image: "/static/news/tcu.jpg",
      imageRemote:
        "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?auto=format&fit=crop&w=900&q=80",
      link: "https://www.tcu.go.tz/",
    },
    {
      id: "heslb",
      category: "HESLB",
      tag: "loan",
      date: "2026",
      title_sw: "Dirisha la maombi ya mkopo",
      title_en: "Higher education loan window",
      desc_sw:
        "Fuata tangazo la OLAS; hakikisha majina yanalingana na NIDA kabla ya deadline.",
      desc_en:
        "Follow OLAS announcements; ensure your names match NIDA before the deadline.",
      image: "/static/news/heslb.jpg",
      imageRemote:
        "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=900&q=80",
      link: "https://www.heslb.go.tz/",
    },
    {
      id: "necta",
      category: "NECTA",
      tag: "results",
      date: "2026",
      title_sw: "Matokeo ya CSEE / ACSEE",
      title_en: "CSEE / ACSEE results",
      desc_sw:
        "Pakua matokeo kwa mwaka na nambari ya mtihani (CNO) moja kwa moja kwenye dashboard.",
      desc_en:
        "Fetch results by exam year and candidate number directly from the dashboard.",
      image: "/static/news/necta.jpg",
      imageRemote:
        "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?auto=format&fit=crop&w=900&q=80",
      link: "https://www.necta.go.tz/",
    },
    {
      id: "institutions",
      category: "Taasisi",
      tag: "deadline",
      date: "2026",
      title_sw: "Maombi ya chuo",
      title_en: "University applications",
      desc_sw:
        "Kila chuo kinaweza kuwa na tarehe tofauti — thibitisha tovuti rasmi ya chuo unachotaka.",
      desc_en:
        "Each university may set different dates — always confirm on the official website.",
      image: "/static/news/institutions.jpg",
      imageRemote:
        "https://images.unsplash.com/photo-1562774053-701939374585?auto=format&fit=crop&w=900&q=80",
      link: "https://www.tcu.go.tz/",
    },
    {
      id: "mwongozo",
      category: "MWONGOZO",
      tag: "guide",
      date: "Sasa",
      title_sw: "Anza na matokeo yako",
      title_en: "Start with your results",
      desc_sw:
        "Ingiza CSEE / ACSEE, pata mapendekezo ya programme, na chunguza vyuo Tanzania — bure.",
      desc_en:
        "Enter CSEE / ACSEE, get programme recommendations, and browse Tanzanian institutions — free.",
      image: "/static/news/mwongozo.jpg",
      imageRemote:
        "https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=900&q=80",
      link: "?app=1",
    },
  ];
})(typeof window !== "undefined" ? window : globalThis);
