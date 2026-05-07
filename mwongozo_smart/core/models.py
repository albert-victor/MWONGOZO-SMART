from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class AdmissionPathway(str, Enum):
    # Student entry route.
    O_LEVEL = "o_level"
    A_LEVEL = "a_level"
    EQUIVALENT = "equivalent"


class ALevelScheme(str, Enum):
    # Grade-to-points schemes used in Tanzanian A-Level systems.
    PRE_2014 = "pre_2014"
    YEAR_2014_2015 = "2014_2015"
    POST_2016 = "2016_plus"


class ProgrammeCategory(str, Enum):
    # Simple grouping used for rules and UI sections.
    HEALTH = "health"
    ENGINEERING = "engineering"
    EDUCATION = "education"
    BUSINESS = "business"
    ACCOUNTING_FINANCE = "accounting_finance"
    AGRICULTURE = "agriculture"
    LAW = "law"
    ARTS = "arts"
    SCIENCE = "science"
    TECH = "tech"
    COMPUTING = "computing"
    OTHER = "other"


class ProgrammeAwardLevel(str, Enum):
    # Broad award type used to separate certificate, diploma, and degree pathways.
    CERTIFICATE = "certificate"
    DIPLOMA = "diploma"
    BACHELOR = "bachelor"
    POSTGRADUATE = "postgraduate"


class ConfidenceBand(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    VERY_LOW = "Very Low"


class SubjectGrade(BaseModel):
    # One subject + one grade from the user.
    subject: str
    grade: str
    principal: bool = True
    level: str = "a_level"

    @field_validator("subject")
    @classmethod
    def normalize_subject(cls, value: str) -> str:
        return " ".join(value.strip().split())

    @field_validator("grade")
    @classmethod
    def normalize_grade(cls, value: str) -> str:
        return value.strip().upper()


class Institution(BaseModel):
    # Basic institution metadata used when building programme records.
    code: str
    name: str
    city: str
    region: str
    website: str | None = None
    apply_url: str | None = None
    cta_label: str = "Apply Now"

    @field_validator("code", "name", "city", "region")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class ConditionalRequirement(BaseModel):
    # Extra rule that applies only in special cases.
    unless_any_principal: list[str] = Field(default_factory=list)
    unless_any_subjects: list[str] = Field(default_factory=list)
    require_a_level_subject_grades: dict[str, str] = Field(default_factory=dict)
    require_o_level_subject_grades: dict[str, str] = Field(default_factory=dict)
    message: str = ""

    @field_validator("unless_any_principal", mode="before")
    @classmethod
    def normalize_subject_list(cls, value: Any) -> list[str]:
        if not value:
            return []
        return [" ".join(str(item).strip().split()) for item in value]

    @field_validator("unless_any_subjects", mode="before")
    @classmethod
    def normalize_subject_list_any(cls, value: Any) -> list[str]:
        if not value:
            return []
        return [" ".join(str(item).strip().split()) for item in value]

    @field_validator("require_a_level_subject_grades", "require_o_level_subject_grades", mode="before")
    @classmethod
    def normalize_grade_map(cls, value: Any) -> dict[str, str]:
        if not value:
            return {}
        return {" ".join(str(k).strip().split()): str(v).strip().upper() for k, v in dict(value).items()}


class AdmissionRequirement(BaseModel):
    # The main TCU-style entry requirements for a programme.
    minimum_principal_passes: int = 2
    minimum_total_points: float = 4.0
    minimum_o_level_passes: int = 0
    principal_subject_pool: list[str] = Field(default_factory=list)
    principal_pool_min_count: int = 0
    required_principal_subjects: list[str] = Field(default_factory=list)
    minimum_a_level_subject_grades: dict[str, str] = Field(default_factory=dict)
    minimum_o_level_subject_grades: dict[str, str] = Field(default_factory=dict)
    conditional_requirements: list[ConditionalRequirement] = Field(default_factory=list)
    preferred_o_level_subjects: dict[str, str] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)
    strict: bool = False

    @field_validator(
        "principal_subject_pool",
        "required_principal_subjects",
        "notes",
        mode="before",
    )
    @classmethod
    def normalize_list(cls, value: Any) -> list[str]:
        if not value:
            return []
        return [" ".join(str(item).strip().split()) for item in value]

    @field_validator(
        "minimum_a_level_subject_grades",
        "minimum_o_level_subject_grades",
        "preferred_o_level_subjects",
        mode="before",
    )
    @classmethod
    def normalize_map(cls, value: Any) -> dict[str, str]:
        if not value:
            return {}
        return {" ".join(str(k).strip().split()): str(v).strip().upper() for k, v in dict(value).items()}

    @model_validator(mode="after")
    def normalize_counts(self) -> "AdmissionRequirement":
        self.minimum_principal_passes = max(0, self.minimum_principal_passes)
        self.minimum_o_level_passes = max(0, self.minimum_o_level_passes)
        self.principal_pool_min_count = max(0, self.principal_pool_min_count)
        return self


class Programme(BaseModel):
    # One programme offered by one institution.
    code: str
    name: str
    institution_code: str
    institution_name: str
    city: str
    region: str
    category: ProgrammeCategory = ProgrammeCategory.OTHER
    award_level: ProgrammeAwardLevel = ProgrammeAwardLevel.BACHELOR
    duration_years: int | None = None
    capacity: int | None = None
    competition_tier: int = 3
    admission_requirement: AdmissionRequirement = Field(default_factory=AdmissionRequirement)
    tags: list[str] = Field(default_factory=list)
    source_reference: str = "TCU Bachelor's Degree Admission Guidebook 2025/2026"

    @field_validator("code", "name", "institution_code", "institution_name", "city", "region")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_tags(cls, value: Any) -> list[str]:
        if not value:
            return []
        return [str(item).strip().lower() for item in value]

    @field_validator("competition_tier")
    @classmethod
    def clamp_competition_tier(cls, value: int) -> int:
        return min(5, max(1, int(value)))


class StudentResult(BaseModel):
    # Full student profile before the engine starts scoring.
    pathway: AdmissionPathway = AdmissionPathway.A_LEVEL
    a_level_scheme: ALevelScheme = ALevelScheme.POST_2016
    a_level_subjects: list[SubjectGrade] = Field(default_factory=list)
    o_level_subjects: list[SubjectGrade] = Field(default_factory=list)
    combination: str | None = None
    preferred_regions: list[str] = Field(default_factory=list)
    preferred_institutions: list[str] = Field(default_factory=list)
    language: str = "both"
    equivalent_qualification: str | None = None
    notes: list[str] = Field(default_factory=list)

    @field_validator("combination")
    @classmethod
    def normalize_combination(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return "".join(ch for ch in value.strip().upper() if ch.isalpha())

    @field_validator("preferred_regions", "preferred_institutions", "notes", mode="before")
    @classmethod
    def normalize_list(cls, value: Any) -> list[str]:
        if not value:
            return []
        return [" ".join(str(item).strip().split()).lower() for item in value]

    @field_validator("language")
    @classmethod
    def normalize_language(cls, value: str) -> str:
        return value.strip().lower()

    @model_validator(mode="after")
    def normalize_subject_models(self) -> "StudentResult":
        self.a_level_subjects = [item.model_copy(update={"subject": item.subject.strip()}) for item in self.a_level_subjects]
        self.o_level_subjects = [item.model_copy(update={"subject": item.subject.strip()}) for item in self.o_level_subjects]
        return self


class EligibilityIssue(BaseModel):
    # One rule that failed during eligibility evaluation.
    rule_id: str
    message: str
    severity: str = "blocking"


class RuleTrace(BaseModel):
    # Explains one rule outcome in a compact, UI-friendly form.
    rule_id: str
    label: str
    passed: bool
    points: float = 0.0
    message: str = ""
    details: str | None = None


class ProgrammeAssessment(BaseModel):
    # Result of running a student against one programme.
    eligible: bool
    score: float = 0.0
    confidence: float = 0.0
    confidence_band: ConfidenceBand = ConfidenceBand.VERY_LOW
    rule_points: float = 0.0
    matched_rules: list[str] = Field(default_factory=list)
    missing_rules: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    issues: list[EligibilityIssue] = Field(default_factory=list)
    rule_traces: list[RuleTrace] = Field(default_factory=list)
    why_recommended: list[str] = Field(default_factory=list)
    why_borderline: list[str] = Field(default_factory=list)
    why_not_matched: list[str] = Field(default_factory=list)
    parallel_courses: list[str] = Field(default_factory=list)
    section: str = "General"
    points_margin: float = 0.0


class Recommendation(BaseModel):
    # Final ranked recommendation shown to the user.
    rank: int = 0
    programme: Programme
    assessment: ProgrammeAssessment
    student_points: float
    minimum_required_points: float
    institution_website: str | None = None
    institution_apply_url: str | None = None
    cta_label: str = "Apply Now"

    @property
    def confidence(self) -> float:
        return self.assessment.confidence


class CombinationSuggestion(BaseModel):
    # A lightweight guidebook-based suggestion for A-Level combinations.
    code: str
    subjects: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    likely_sections: list[str] = Field(default_factory=list)
    rationale: list[str] = Field(default_factory=list)


class RecommendedSection(str, Enum):
    HIGHLY_RECOMMENDED = "Highly Recommended"
    BORDERLINE = "Possible with borderline"
    HEALTH = "Health Sciences"
    ENGINEERING = "Engineering & Tech"
    EDUCATION = "Education"
    BUSINESS = "Business"
    ACCOUNTING_FINANCE = "Accounting & Finance"
    AGRICULTURE = "Agriculture"
    LAW = "Law"
    OTHER = "Other"
