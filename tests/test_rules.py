from mwongozo_smart.core.models import AdmissionPathway, StudentResult, SubjectGrade
from mwongozo_smart.core.rules import TCURuleEngine
from mwongozo_smart.data.guidebook_data import programme_index


def test_muhas_md_requires_strict_pcb():
    programme = programme_index()["MH011"]
    student = StudentResult(
        pathway=AdmissionPathway.A_LEVEL,
        a_level_subjects=[
            SubjectGrade(subject="Physics", grade="D"),
            SubjectGrade(subject="Chemistry", grade="D"),
            SubjectGrade(subject="Biology", grade="D"),
        ],
    )
    result = TCURuleEngine().evaluate(student, programme)
    assert result.eligible is True


def test_aku_nursing_rejects_wrong_subject_mix():
    programme = programme_index()["AKU01"]
    student = StudentResult(
        pathway=AdmissionPathway.A_LEVEL,
        a_level_subjects=[
            SubjectGrade(subject="Economics", grade="A"),
            SubjectGrade(subject="Geography", grade="B"),
            SubjectGrade(subject="History", grade="C"),
        ],
    )
    result = TCURuleEngine().evaluate(student, programme)
    assert result.eligible is False


def test_architecture_requires_math_fallback():
    programme = programme_index()["AR001"]
    student = StudentResult(
        pathway=AdmissionPathway.A_LEVEL,
        a_level_subjects=[
            SubjectGrade(subject="Physics", grade="B"),
            SubjectGrade(subject="Fine Arts", grade="B"),
        ],
        o_level_subjects=[
            SubjectGrade(subject="Basic Mathematics", grade="D", level="o_level"),
        ],
    )
    result = TCURuleEngine().evaluate(student, programme)
    assert result.eligible is False


def test_business_requires_math_when_not_principal():
    programme = programme_index()["AM003"]
    student = StudentResult(
        pathway=AdmissionPathway.A_LEVEL,
        a_level_subjects=[
            SubjectGrade(subject="Economics", grade="B"),
            SubjectGrade(subject="Commerce", grade="B"),
        ],
        o_level_subjects=[
            SubjectGrade(subject="Basic Mathematics", grade="E", level="o_level"),
        ],
    )
    result = TCURuleEngine().evaluate(student, programme)
    assert result.eligible is True


def test_o_level_cannot_apply_directly_to_bachelor():
    programme = programme_index()["MH011"]
    student = StudentResult(
        pathway=AdmissionPathway.O_LEVEL,
        o_level_subjects=[
            SubjectGrade(subject="Biology", grade="B", level="o_level"),
            SubjectGrade(subject="Chemistry", grade="B", level="o_level"),
            SubjectGrade(subject="Physics", grade="B", level="o_level"),
        ],
    )
    result = TCURuleEngine().evaluate(student, programme)
    assert result.eligible is False


def test_o_level_can_match_certificate_route():
    programme = programme_index()["HIHS04"]
    student = StudentResult(
        pathway=AdmissionPathway.O_LEVEL,
        o_level_subjects=[
            SubjectGrade(subject="Biology", grade="B", level="o_level"),
            SubjectGrade(subject="Chemistry", grade="B", level="o_level"),
            SubjectGrade(subject="Physics", grade="C", level="o_level"),
            SubjectGrade(subject="English Language", grade="D", level="o_level"),
        ],
    )
    result = TCURuleEngine().evaluate(student, programme)
    assert result.eligible is True


def test_o_level_mathematics_alias_supports_college_routes():
    programme = programme_index()["A3IPS04"]
    student = StudentResult(
        pathway=AdmissionPathway.O_LEVEL,
        o_level_subjects=[
            SubjectGrade(subject="Mathematics", grade="B", level="o_level"),
            SubjectGrade(subject="English Language", grade="B", level="o_level"),
            SubjectGrade(subject="Biology", grade="C", level="o_level"),
            SubjectGrade(subject="Chemistry", grade="C", level="o_level"),
        ],
    )
    result = TCURuleEngine().evaluate(student, programme)
    assert result.eligible is True
