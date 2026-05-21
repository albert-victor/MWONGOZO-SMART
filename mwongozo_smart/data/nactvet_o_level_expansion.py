"""NACTVET / NACTE O-Level catalogue — certificates, diplomas, private TVET & health colleges.

Curated cluster data (2024–2026) aligned with NACTVET NTA routes and NACTE registered colleges.
Does not change A-Level / bachelor TCU rules.
"""

from __future__ import annotations

from mwongozo_smart.core.models import (
    AdmissionRequirement,
    Institution,
    Programme,
    ProgrammeAwardLevel,
    ProgrammeCategory,
)
from mwongozo_smart.data.college_catalog_expansion import _o_level_req, _prog
from mwongozo_smart.data.institutions import institution_index

_INST = institution_index()

# Institutions referenced here must exist in institutions.py (or programme rows supply names).
_EXTRA_INSTITUTIONS: list[Institution] = []


def _req_health_cert() -> AdmissionRequirement:
    return _o_level_req(passes=3, subjects={"Biology": "D", "Chemistry": "D", "English Language": "D"})


def _req_health_dip() -> AdmissionRequirement:
    return _o_level_req(passes=4, subjects={"Biology": "D", "Chemistry": "D"})


def _req_general() -> AdmissionRequirement:
    return _o_level_req(passes=3, subjects={"English Language": "D"})


def _req_stem_dip() -> AdmissionRequirement:
    return _o_level_req(
        passes=4,
        subjects={"Basic Mathematics": "D"},
        pool=["Basic Mathematics", "Physics", "Chemistry", "Biology"],
        pool_min=1,
    )


def _build_rows() -> list[tuple]:
    """(code, name, inst, category, award, req, years, tier, source_suffix)."""
    rows: list[tuple] = []

    def add(
        code: str,
        name: str,
        inst: str,
        cat: ProgrammeCategory,
        award: ProgrammeAwardLevel,
        req: AdmissionRequirement,
        years: int = 3,
        tier: int = 2,
    ) -> None:
        rows.append((code, name, inst, cat, award, req, years, tier, "NACTVET"))

    # —— NACTVET health (certificates & diplomas) ——
    health_certs = [
        ("NVHTC01", "Technician Certificate in Nursing", "HIHS"),
        ("NVHTC02", "Technician Certificate in Midwifery", "HIHS"),
        ("NVHTC03", "Technician Certificate in Clinical Medicine", "A3IPS"),
        ("NVHTC04", "Technician Certificate in Pharmaceutical Sciences", "A3IPS"),
        ("NVHTC05", "Technician Certificate in Medical Laboratory Sciences", "ATC"),
        ("NVHTC06", "Technician Certificate in Community Health", "TICD"),
        ("NVHTC07", "Technician Certificate in Nursing", "A3IPS"),
        ("NVHTC08", "Certificate in Clinical Medicine", "PRIMUS"),
        ("NVHTC09", "Certificate in Nursing", "PRIMUS"),
        ("NVHTC10", "Technician Certificate in Nursing", "STJCH"),
        ("NVHTC11", "Technician Certificate in Midwifery", "STJCH"),
        ("NVHTC12", "Certificate in Clinical Medicine", "OCEANIC"),
        ("NVHTC13", "Technician Certificate in Nursing", "BMC"),
        ("NVHTC14", "Technician Certificate in Laboratory Technology", "KCMC_TVET"),
        ("NVHTC15", "Certificate in Pharmaceutical Sciences", "MARIST_HT"),
    ]
    for code, name, inst in health_certs:
        add(code, name, inst, ProgrammeCategory.HEALTH, ProgrammeAwardLevel.CERTIFICATE, _req_health_cert(), 1, 1)

    health_dips = [
        ("NVHTD01", "Ordinary Diploma in Nursing", "PRIMUS"),
        ("NVHTD02", "Ordinary Diploma in Clinical Medicine", "PRIMUS"),
        ("NVHTD03", "Ordinary Diploma in Pharmaceutical Sciences", "A3IPS"),
        ("NVHTD04", "Ordinary Diploma in Medical Laboratory Sciences", "ATC"),
        ("NVHTD05", "Ordinary Diploma in Community Health", "TICD"),
        ("NVHTD06", "Ordinary Diploma in Nursing", "STJCH"),
        ("NVHTD07", "Ordinary Diploma in Midwifery", "STJCH"),
        ("NVHTD08", "Ordinary Diploma in Clinical Medicine", "OCEANIC"),
        ("NVHTD09", "Ordinary Diploma in Nursing", "BMC"),
        ("NVHTD10", "Ordinary Diploma in Pharmaceutical Sciences", "MARIST_HT"),
        ("NVHTD11", "Ordinary Diploma in Medical Laboratory Sciences", "KCMC_TVET"),
        ("NVHTD12", "Ordinary Diploma in Environmental Health Sciences", "MUHIMBILI_CT"),
    ]
    for code, name, inst in health_dips:
        add(code, name, inst, ProgrammeCategory.HEALTH, ProgrammeAwardLevel.DIPLOMA, _req_health_dip())

    # —— Private & faith-based TVET (business / ICT / accountancy) ——
    private_specs = [
        ("Ordinary Diploma in Business Administration", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.DIPLOMA, _req_general()),
        ("Ordinary Diploma in Accountancy", ProgrammeCategory.ACCOUNTING_FINANCE, ProgrammeAwardLevel.DIPLOMA, _o_level_req(passes=3, subjects={"Basic Mathematics": "D"})),
        ("Ordinary Diploma in Information Technology", ProgrammeCategory.COMPUTING, ProgrammeAwardLevel.DIPLOMA, _req_stem_dip()),
        ("Ordinary Diploma in Procurement and Supply", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.DIPLOMA, _req_general()),
        ("Technician Certificate in Business Administration", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.CERTIFICATE, _req_general(), 1, 1),
        ("Technician Certificate in Accountancy", ProgrammeCategory.ACCOUNTING_FINANCE, ProgrammeAwardLevel.CERTIFICATE, _req_general(), 1, 1),
        ("Technician Certificate in Information Technology", ProgrammeCategory.COMPUTING, ProgrammeAwardLevel.CERTIFICATE, _o_level_req(passes=3, subjects={"Basic Mathematics": "D"}), 1, 1),
    ]
    private_insts = [
        "OUT", "KIUT", "TEKU", "UAUT", "ZU", "HKMU", "MWECAU", "SFUCHAS", "MUMCCO", "MUDCCO",
        "CUOM", "AMUCTA", "SUMAIT", "SAUT", "UOI",
    ]
    def unpack_spec(spec: tuple) -> tuple:
        if len(spec) == 6:
            return spec
        name, cat, award, req = spec
        if award == ProgrammeAwardLevel.CERTIFICATE:
            return name, cat, award, req, 1, 1
        return name, cat, award, req, 3, 2

    seq = 1
    for inst in private_insts:
        for spec in private_specs:
            name, cat, award, req, years, tier = unpack_spec(spec)
            code = f"PV{inst[:4]}{seq:03d}"
            seq += 1
            add(code, name, inst, cat, award, req, years, tier)

    # —— Public technical colleges (extra NACTE clusters) ——
    public_specs = [
        ("Ordinary Diploma in Education", ProgrammeCategory.EDUCATION, ProgrammeAwardLevel.DIPLOMA, _req_general()),
        ("Ordinary Diploma in Records and Archives Management", ProgrammeCategory.ARTS, ProgrammeAwardLevel.DIPLOMA, _req_general()),
        ("Ordinary Diploma in Tourism and Hospitality", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.DIPLOMA, _req_general()),
        ("Ordinary Diploma in Agriculture", ProgrammeCategory.AGRICULTURE, ProgrammeAwardLevel.DIPLOMA, _o_level_req(passes=3, subjects={"Biology": "D"})),
        ("Technician Certificate in Agriculture", ProgrammeCategory.AGRICULTURE, ProgrammeAwardLevel.CERTIFICATE, _o_level_req(passes=3), 1, 1),
        ("Technician Certificate in Catering and Accommodation", ProgrammeCategory.BUSINESS, ProgrammeAwardLevel.CERTIFICATE, _req_general(), 1, 1),
    ]
    public_insts = ["DIT", "NIT", "ATC", "CBE", "DMI", "ITA", "CFR", "CAWM", "WI", "MNMA_PEMBA"]
    for inst in public_insts:
        for spec in public_specs:
            name, cat, award, req, years, tier = unpack_spec(spec)
            code = f"PB{inst[:3]}{seq:03d}"
            seq += 1
            add(code, name, inst, cat, award, req, years, tier)

    return rows


def _build_programmes() -> list[Programme]:
    output: list[Programme] = []
    for row in _build_rows():
        code, name, inst, category, award, req, years, tier, src_tag = row
        if inst not in _INST:
            continue
        source = f"NACTVET / NACTE O-Level cluster ({src_tag}) 2024–2026"
        output.append(_prog(code, name, inst, category, award, req, years=years, tier=tier, source=source))
    return output


NACTVET_OLEVEL_PROGRAMMES: list[Programme] = _build_programmes()
