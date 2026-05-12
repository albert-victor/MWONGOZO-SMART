from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator

from mwongozo_smart.core.models import ALevelScheme


class ExamType(str, Enum):
    """Exam types supported by the discovery engine (expandable)."""

    CSEE = "csee"
    ACSEE = "acsee"
    PSLE = "psle"
    FTNA = "ftna"


class NectaSubjectGrade(BaseModel):
    code: str
    name: str
    grade: str


class NectaSchoolLink(BaseModel):
    center_number: str
    school_name: str
    result_href: str


class NectaCseeResult(BaseModel):
    exam_year: int
    candidate_number: str
    student_name: str = ""
    school_name: str = ""
    center_number: str = ""
    region: str = ""
    division: str = ""
    sex: str | None = None
    aggregate: int | None = None
    subjects: list[NectaSubjectGrade] = Field(default_factory=list)
    source_url: str = ""
    data_source: str = Field(
        default="necta_onlinesys",
        description="Origin label, e.g. necta_onlinesys or tetea_maktaba.",
    )

    @field_validator("candidate_number", "center_number")
    @classmethod
    def uppercase_tokens(cls, value: str) -> str:
        return value.strip().upper()


class NectaAcseeResult(BaseModel):
    """Structured row parsed from an official ACSEE centre results page (NECTA or TETEA mirror)."""

    exam_year: int
    candidate_number: str
    student_name: str = ""
    school_name: str = ""
    center_number: str = ""
    region: str = ""
    inferred_combination: str | None = None
    subjects: list[NectaSubjectGrade] = Field(default_factory=list)
    division: str = ""
    aggregate_points: int | None = None
    gpa: float | None = Field(default=None, description="Candidate GPA when the source table uses a GPA column.")
    sex: str | None = None
    centre_gpa: float | None = Field(default=None, description="Centre-wide GPA from NECTA footer when present.")
    source_url: str = ""
    data_source: str = Field(
        default="necta_onlinesys",
        description="necta_onlinesys or tetea_maktaba",
    )

    @field_validator("candidate_number", "center_number")
    @classmethod
    def uppercase_tokens(cls, value: str) -> str:
        return value.strip().upper()


class StudentLookupRequest(BaseModel):
    year: int = Field(ge=1990, le=2100)
    candidate_number: str = Field(min_length=4, max_length=32)
    include_recommendations: bool = False
    recommend_limit: int = Field(default=80, ge=1, le=200)

    @field_validator("candidate_number")
    @classmethod
    def strip_candidate(cls, value: str) -> str:
        return value.strip()


class AcseeLookupRequest(StudentLookupRequest):
    """Lookup a single candidate on official ACSEE pages (optional full centre index refresh)."""

    refresh_centre_index: bool = False


class AcseeRecommendRequest(AcseeLookupRequest):
    preferred_regions: list[str] = Field(default_factory=list)
    preferred_institutions: list[str] = Field(default_factory=list)
    language: str = "english"
    a_level_scheme: ALevelScheme = ALevelScheme.POST_2016


class StudentResultsLookupRequest(BaseModel):
    exam_type: ExamType
    year: int = Field(ge=1980, le=2100)
    candidate_number: str = Field(min_length=4, max_length=32)
    skip_cache: bool = False

    @field_validator("candidate_number")
    @classmethod
    def strip_candidate(cls, value: str) -> str:
        return value.strip()

    @field_validator("exam_type")
    @classmethod
    def only_csee_or_acsee(cls, value: ExamType) -> ExamType:
        if value not in (ExamType.CSEE, ExamType.ACSEE):
            raise ValueError(
                f"exam_type must be '{ExamType.CSEE.value}' or '{ExamType.ACSEE.value}' for this endpoint "
                f"(got '{value.value}')."
            )
        return value


class StudentResultsRecommendRequest(StudentResultsLookupRequest):
    recommend_limit: int = Field(default=80, ge=1, le=200)
    preferred_regions: list[str] = Field(default_factory=list)
    preferred_institutions: list[str] = Field(default_factory=list)
    language: str = "english"
    a_level_scheme: ALevelScheme = ALevelScheme.POST_2016
