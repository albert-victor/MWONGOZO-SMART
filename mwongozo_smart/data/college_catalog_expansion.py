"""Extra diploma, certificate, and college routes (NACTE-style / TCU college clusters).

Curated for O-Level and mixed entry — does not relax A-Level rule engine checks.
"""

from __future__ import annotations

from mwongozo_smart.core.models import (
    AdmissionRequirement,
    Programme,
    ProgrammeAwardLevel,
    ProgrammeCategory,
)
from mwongozo_smart.data.institutions import institution_index

_INST = institution_index()


def _o_level_req(
    *,
    passes: int = 3,
    subjects: dict[str, str] | None = None,
    pool: list[str] | None = None,
    pool_min: int = 0,
    notes: list[str] | None = None,
) -> AdmissionRequirement:
    grades = dict(subjects or {})
    grades.setdefault("English Language", "D")
    return AdmissionRequirement(
        minimum_principal_passes=1,
        minimum_total_points=0.0,
        minimum_o_level_passes=passes,
        minimum_o_level_subject_grades=grades,
        principal_subject_pool=pool or [],
        principal_pool_min_count=pool_min,
        notes=notes or [],
    )


def _prog(
    code: str,
    name: str,
    inst: str,
    category: ProgrammeCategory,
    award: ProgrammeAwardLevel,
    requirement: AdmissionRequirement,
    *,
    tier: int = 2,
    years: int = 3,
    tags: list[str] | None = None,
    source: str = "TCU / NACTE college cluster 2024–2026",
) -> Programme:
    base = _INST[inst]
    return Programme(
        code=code,
        name=name,
        institution_code=inst,
        institution_name=base.name,
        city=base.city,
        region=base.region,
        category=category,
        award_level=award,
        duration_years=years,
        competition_tier=tier,
        admission_requirement=requirement,
        tags=tags or [category.value, award.value],
        source_reference=source,
    )


# (code, name, institution_code, category, award, requirement factory kwargs)
_COLLEGE_ROWS: list[tuple] = [
    ("ATCD01", "Ordinary Diploma in Civil Engineering", "ATC", ProgrammeCategory.ENGINEERING, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"Basic Mathematics": "D", "Physics": "D"}, "pool": ["Basic Mathematics", "Physics", "Chemistry"]}),
    ("ATCD02", "Ordinary Diploma in Electrical Engineering", "ATC", ProgrammeCategory.ENGINEERING, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"Basic Mathematics": "D", "Physics": "D"}}),
    ("ATCD03", "Ordinary Diploma in Architecture", "ATC", ProgrammeCategory.ENGINEERING, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"Basic Mathematics": "D"}, "pool": ["Basic Mathematics", "Physics"]}),
    ("ATCD04", "Ordinary Diploma in Information Technology", "ATC", ProgrammeCategory.COMPUTING, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"Basic Mathematics": "D"}, "pool": ["Basic Mathematics", "Computer Studies", "Computer Science"]}),
    ("ATCD05", "Ordinary Diploma in Laboratory Technology", "ATC", ProgrammeCategory.HEALTH, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"Biology": "D", "Chemistry": "D"}, "pool": ["Biology", "Chemistry", "Physics"]}),
    ("ATCC01", "Technician Certificate in Civil Engineering", "ATC", ProgrammeCategory.ENGINEERING, ProgrammeAwardLevel.CERTIFICATE, {"passes": 4, "subjects": {"Basic Mathematics": "D"}}, 1, 2),
    ("DITD01", "Ordinary Diploma in Computer Engineering", "DIT", ProgrammeCategory.COMPUTING, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"Basic Mathematics": "D", "Physics": "D"}}),
    ("DITD02", "Ordinary Diploma in Civil Engineering", "DIT", ProgrammeCategory.ENGINEERING, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"Basic Mathematics": "D", "Physics": "D"}}),
    ("DITD03", "Ordinary Diploma in Electrical Engineering", "DIT", ProgrammeCategory.ENGINEERING, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"Basic Mathematics": "D", "Physics": "D"}}),
    ("DITD04", "Ordinary Diploma in Science in Laboratory Technology", "DIT", ProgrammeCategory.HEALTH, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"Biology": "D", "Chemistry": "D"}}),
    ("DITD05", "Ordinary Diploma in Business Administration", "DIT", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"English Language": "D"}}),
    ("NITD01", "Ordinary Diploma in Information Technology", "NIT", ProgrammeCategory.COMPUTING, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"Basic Mathematics": "D"}}),
    ("NITD02", "Ordinary Diploma in Computer Science", "NIT", ProgrammeCategory.COMPUTING, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"Basic Mathematics": "D"}}),
    ("NITD03", "Ordinary Diploma in Business Administration", "NIT", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.DIPLOMA, {}),
    ("TIAD01", "Ordinary Diploma in Accountancy", "TIA", ProgrammeCategory.ACCOUNTING_FINANCE, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"Basic Mathematics": "D", "Book Keeping": "D"}}),
    ("TIAD02", "Ordinary Diploma in Business Administration", "TIA", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.DIPLOMA, {}),
    ("TIAD03", "Ordinary Diploma in Procurement and Supply", "TIA", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.DIPLOMA, {}),
    ("WID01", "Ordinary Diploma in Water Operations and Maintenance", "WI", ProgrammeCategory.ENGINEERING, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"Basic Mathematics": "D", "Physics": "D"}}),
    ("WID02", "Ordinary Diploma in Water Engineering", "WI", ProgrammeCategory.ENGINEERING, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"Basic Mathematics": "D"}}),
    ("A3D01", "Ordinary Diploma in Clinical Medicine", "A3IPS", ProgrammeCategory.HEALTH, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"Biology": "D", "Chemistry": "D", "English Language": "D"}}),
    ("A3D02", "Ordinary Diploma in Pharmaceutical Sciences", "A3IPS", ProgrammeCategory.HEALTH, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"Biology": "D", "Chemistry": "D"}}),
    ("A3D03", "Ordinary Diploma in Nursing", "A3IPS", ProgrammeCategory.HEALTH, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"Biology": "D", "Chemistry": "D"}}),
    ("HIHD01", "Ordinary Diploma in Clinical Medicine", "HIHS", ProgrammeCategory.HEALTH, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"Biology": "D", "Chemistry": "D"}}),
    ("HIHD02", "Ordinary Diploma in Nursing", "HIHS", ProgrammeCategory.HEALTH, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"Biology": "D", "Chemistry": "D"}}),
    ("HIHD03", "Ordinary Diploma in Midwifery", "HIHS", ProgrammeCategory.HEALTH, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"Biology": "D", "Chemistry": "D"}}),
    ("TICDD01", "Ordinary Diploma in Community Development", "TICD", ProgrammeCategory.EDUCATION, ProgrammeAwardLevel.DIPLOMA, {}),
    ("TICDD02", "Ordinary Diploma in Social Work", "TICD", ProgrammeCategory.EDUCATION, ProgrammeAwardLevel.DIPLOMA, {}),
    ("TIPMD01", "Ordinary Diploma in Project Planning and Management", "TIPM", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.DIPLOMA, {}),
    ("ESAMID01", "Ordinary Diploma in Management of Social Protection", "ESAMI", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.DIPLOMA, {}),
    ("ESAMID02", "Ordinary Diploma in Public Administration", "ESAMI", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.DIPLOMA, {}),
    ("CBED01", "Ordinary Diploma in Business Administration", "CBE", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.DIPLOMA, {}),
    ("CBED02", "Ordinary Diploma in Accountancy", "CBE", ProgrammeCategory.ACCOUNTING_FINANCE, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"Basic Mathematics": "D"}}),
    ("DMID01", "Ordinary Diploma in Information Technology", "DMI", ProgrammeCategory.COMPUTING, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"Basic Mathematics": "D"}}),
    ("DMID02", "Ordinary Diploma in Business Administration", "DMI", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.DIPLOMA, {}),
    ("ITAD01", "Ordinary Diploma in Accountancy", "ITA", ProgrammeCategory.ACCOUNTING_FINANCE, ProgrammeAwardLevel.DIPLOMA, {}),
    ("ITAD02", "Ordinary Diploma in Business Administration", "ITA", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.DIPLOMA, {}),
    ("IAED01", "Ordinary Diploma in Accountancy", "IAE", ProgrammeCategory.ACCOUNTING_FINANCE, ProgrammeAwardLevel.DIPLOMA, {}),
    ("IAAD01", "Ordinary Diploma in Business Administration", "IAA", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.DIPLOMA, {}),
    ("IPAD01", "Ordinary Diploma in Public Administration", "IPA", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.DIPLOMA, {}),
    ("ISWD01", "Ordinary Diploma in Social Work", "ISW", ProgrammeCategory.EDUCATION, ProgrammeAwardLevel.DIPLOMA, {}),
    ("CAWMD01", "Ordinary Diploma in Wildlife Management", "CAWM", ProgrammeCategory.AGRICULTURE, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"Biology": "D"}}),
    ("CAWMD02", "Ordinary Diploma in Tourism and Hospitality Management", "CAWM", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.DIPLOMA, {}),
    ("CFRD01", "Ordinary Diploma in Records and Archives Management", "CFR", ProgrammeCategory.ARTS, ProgrammeAwardLevel.DIPLOMA, {}),
    ("CFRD02", "Ordinary Diploma in Library and Information Studies", "CFR", ProgrammeCategory.ARTS, ProgrammeAwardLevel.DIPLOMA, {}),
    ("EASTCD01", "Ordinary Diploma in Business Administration", "EASTC", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.DIPLOMA, {}),
    ("EASTCD02", "Ordinary Diploma in Accountancy", "EASTC", ProgrammeCategory.ACCOUNTING_FINANCE, ProgrammeAwardLevel.DIPLOMA, {}),
    ("KIUTD01", "Ordinary Diploma in Business Administration", "KIUT", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.DIPLOMA, {}),
    ("KIUTD02", "Ordinary Diploma in Accountancy", "KIUT", ProgrammeCategory.ACCOUNTING_FINANCE, ProgrammeAwardLevel.DIPLOMA, {}),
    ("TEKUD01", "Ordinary Diploma in Business Administration", "TEKU", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.DIPLOMA, {}),
    ("TEKUD02", "Ordinary Diploma in Accountancy", "TEKU", ProgrammeCategory.ACCOUNTING_FINANCE, ProgrammeAwardLevel.DIPLOMA, {}),
    ("MUCCD01", "Ordinary Diploma in Business Administration", "MUCE", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.DIPLOMA, {}),
    ("MNUATD01", "Ordinary Diploma in Business Administration", "MNUAT", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.DIPLOMA, {}),
    ("SJCETD01", "Ordinary Diploma in Civil Engineering", "SJCET", ProgrammeCategory.ENGINEERING, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"Basic Mathematics": "D", "Physics": "D"}}),
    ("SJCETD02", "Ordinary Diploma in Electrical Engineering", "SJCET", ProgrammeCategory.ENGINEERING, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"Basic Mathematics": "D"}}),
    ("HKMUD01", "Ordinary Diploma in Business Administration", "HKMU", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.DIPLOMA, {}),
    ("MWECAUD01", "Ordinary Diploma in Business Administration", "MWECAU", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.DIPLOMA, {}),
    ("UAUTD01", "Ordinary Diploma in Business Administration", "UAUT", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.DIPLOMA, {}),
    ("ZUD01", "Ordinary Diploma in Business Administration", "ZU", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.DIPLOMA, {}),
    ("ZUD02", "Ordinary Diploma in Education", "ZU", ProgrammeCategory.EDUCATION, ProgrammeAwardLevel.DIPLOMA, {}),
    ("OUTD01", "Ordinary Diploma in Business Administration", "OUT", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.DIPLOMA, {}),
    ("OUTD02", "Ordinary Diploma in Accountancy", "OUT", ProgrammeCategory.ACCOUNTING_FINANCE, ProgrammeAwardLevel.DIPLOMA, {}),
    ("MUDCCD01", "Ordinary Diploma in Business Administration", "MUDCCO", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.DIPLOMA, {}),
    ("MUMCCD01", "Ordinary Diploma in Business Administration", "MUMCCO", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.DIPLOMA, {}),
    ("SFUCHASD01", "Ordinary Diploma in Business Administration", "SFUCHAS", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.DIPLOMA, {}),
    ("MNMAPD01", "Ordinary Diploma in Public Administration", "MNMA_PEMBA", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.DIPLOMA, {}),
    ("SUAKAD01", "Ordinary Diploma in Agriculture", "SUA_KATAVI", ProgrammeCategory.AGRICULTURE, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"Biology": "D"}}),
    ("ATCC02", "Technician Certificate in Information Technology", "ATC", ProgrammeCategory.COMPUTING, ProgrammeAwardLevel.CERTIFICATE, {"passes": 4}, 1, 2),
    ("A3C01", "Technician Certificate in Clinical Medicine", "A3IPS", ProgrammeCategory.HEALTH, ProgrammeAwardLevel.CERTIFICATE, {"subjects": {"Biology": "D", "Chemistry": "D"}}, 1, 2),
    ("HIHC01", "Technician Certificate in Nursing", "HIHS", ProgrammeCategory.HEALTH, ProgrammeAwardLevel.CERTIFICATE, {"subjects": {"Biology": "D"}}, 1, 2),
    ("TICC01", "Certificate in Community Development", "TICD", ProgrammeCategory.EDUCATION, ProgrammeAwardLevel.CERTIFICATE, {"passes": 4}, 1, 1),
    ("WIC01", "Technician Certificate in Water Supply", "WI", ProgrammeCategory.ENGINEERING, ProgrammeAwardLevel.CERTIFICATE, {"passes": 4}, 1, 2),
    # Law — NACTE / college clusters (O-Level entry)
    ("LAWD01", "Ordinary Diploma in Law", "OUT", ProgrammeCategory.LAW, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"English Language": "D"}, "pool": ["History", "Geography", "Kiswahili", "English Language"]}),
    ("LAWD02", "Ordinary Diploma in Legal Practice", "UDSM", ProgrammeCategory.LAW, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"English Language": "D"}, "pool": ["History", "Geography", "English Language", "Kiswahili"]}),
    ("LAWD03", "Ordinary Diploma in Law", "UOI", ProgrammeCategory.LAW, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"English Language": "D"}}),
    ("LAWD04", "Ordinary Diploma in Paralegal Studies", "ZU", ProgrammeCategory.LAW, ProgrammeAwardLevel.DIPLOMA, {"subjects": {"English Language": "D"}}),
    ("LAWC01", "Technician Certificate in Legal Studies", "OUT", ProgrammeCategory.LAW, ProgrammeAwardLevel.CERTIFICATE, {"passes": 4, "subjects": {"English Language": "D"}}, 1, 2),
    ("LAWC02", "Technician Certificate in Court Reporting", "UDSM", ProgrammeCategory.LAW, ProgrammeAwardLevel.CERTIFICATE, {"passes": 4, "subjects": {"English Language": "D"}}, 1, 2),
    ("LAWC03", "Certificate in Legal Metrology", "DIT", ProgrammeCategory.LAW, ProgrammeAwardLevel.CERTIFICATE, {"passes": 4}, 1, 2),
]


def _build_college_catalog() -> list[Programme]:
    output: list[Programme] = []
    for row in _COLLEGE_ROWS:
        code, name, inst, category, award = row[:5]
        req_kwargs = row[5] if len(row) > 5 else {}
        years = row[6] if len(row) > 6 else (1 if award == ProgrammeAwardLevel.CERTIFICATE else 3)
        tier = row[7] if len(row) > 7 else 2
        if isinstance(req_kwargs, dict):
            pool = req_kwargs.pop("pool", None)
            pool_min = len(pool) if pool else 0
            req = _o_level_req(pool=pool, pool_min=pool_min, **req_kwargs)
        else:
            req = _o_level_req()
        output.append(
            _prog(code, name, inst, category, award, req, years=years, tier=tier, source="NACTE/TCU college routes 2024–2026")
        )
    return output


COLLEGE_CATALOG_PROGRAMMES: list[Programme] = _build_college_catalog()
