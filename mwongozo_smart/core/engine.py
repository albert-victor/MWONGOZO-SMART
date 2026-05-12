from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Iterable

from mwongozo_smart.core.calculator import OLevelSummary, get_o_level_summary, get_principal_summary
from mwongozo_smart.core.models import CombinationSuggestion, ConfidenceBand, Programme, ProgrammeAwardLevel, ProgrammeCategory, Recommendation, StudentResult
from mwongozo_smart.core.rules import TCURuleEngine
from mwongozo_smart.data.guidebook_data import PROGRAMMES
from mwongozo_smart.data.institutions import INSTITUTIONS
from mwongozo_smart.ml.ranking_model import FeatureVector, RuleBoostedRankingModel
from mwongozo_smart.utils.combination_helper import infer_combination, normalize_subject_name
from mwongozo_smart.utils.grade_converter import confidence_band_from_score

logger = logging.getLogger(__name__)


class RecommendationEngine:
    # This class is the top-level workflow:
    # 1. normalize the student's results
    # 2. check rules against every programme
    # 3. score the eligible ones
    # 4. rank the final list
    def __init__(
        self,
        programmes: Iterable[Programme] | None = None,
        rule_engine: TCURuleEngine | None = None,
        ranking_model: RuleBoostedRankingModel | None = None,
    ) -> None:
        self.programmes = list(programmes or PROGRAMMES)
        self.rule_engine = rule_engine or TCURuleEngine()
        self.ranking_model = ranking_model or RuleBoostedRankingModel()
        self.institutions = {institution.code: institution for institution in INSTITUTIONS}

    def recommend(self, student: StudentResult, limit: int = 80) -> list[Recommendation]:
        # The principal subjects are summarized once, then reused for all programmes.
        summary = get_principal_summary(student)
        o_summary = get_o_level_summary(student) if student.pathway.value == "o_level" else None
        ranked: list[Recommendation] = []

        for programme in self.programmes:
            if not self._programme_allowed_for_pathway(student, programme):
                continue
            # First pass: strict TCU-style eligibility check.
            assessment = self.rule_engine.evaluate(student, programme)
            if not assessment.eligible:
                logger.debug("Rejected %s due to rules: %s", programme.code, assessment.missing_rules)
                continue

            # Second pass: heuristic ranking for the programmes that passed rules.
            score = self._score(student, programme, summary.total_points, o_summary=o_summary)
            assessment.score = score
            assessment.confidence = round(self._confidence(score, programme, student, o_summary=o_summary), 2)
            assessment.confidence_band = ConfidenceBand(confidence_band_from_score(assessment.confidence))
            assessment.parallel_courses = self._parallel_courses(programme)
            display_student_points = o_summary.total_grade_points if o_summary else summary.total_points
            display_minimum = (
                float(programme.admission_requirement.minimum_o_level_passes or 0)
                if o_summary
                else programme.admission_requirement.minimum_total_points
            )
            recommendation = Recommendation(
                programme=programme,
                assessment=assessment,
                student_points=display_student_points,
                minimum_required_points=display_minimum,
                institution_website=self.institutions.get(programme.institution_code).website if self.institutions.get(programme.institution_code) else None,
                institution_apply_url=self._stable_apply_url(programme.institution_code),
                cta_label=self._stable_cta_label(programme.institution_code),
            )
            ranked.append(recommendation)

        ranked.sort(key=lambda item: self._rank_key(student, item), reverse=True)

        for index, recommendation in enumerate(ranked[:limit], start=1):
            recommendation.rank = index

        return ranked[:limit]

    def review_candidates(self, student: StudentResult, limit: int = 10) -> list[Recommendation]:
        # Near-miss programmes are useful when there are no direct matches.
        summary = get_principal_summary(student)
        o_summary = get_o_level_summary(student) if student.pathway.value == "o_level" else None
        reviewed: list[Recommendation] = []

        for programme in self.programmes:
            if not self._programme_allowed_for_pathway(student, programme):
                continue
            assessment = self.rule_engine.evaluate(student, programme)
            if assessment.eligible:
                continue

            score = self._score(student, programme, summary.total_points, o_summary=o_summary)
            assessment.score = score
            assessment.confidence = round(self._confidence(score, programme, student, o_summary=o_summary), 2)
            assessment.confidence_band = ConfidenceBand(confidence_band_from_score(assessment.confidence))
            assessment.parallel_courses = self._parallel_courses(programme)

            if score < 22.0 and assessment.points_margin < -2.0:
                continue

            display_student_points = o_summary.total_grade_points if o_summary else summary.total_points
            display_minimum = (
                float(programme.admission_requirement.minimum_o_level_passes or 0)
                if o_summary
                else programme.admission_requirement.minimum_total_points
            )
            reviewed.append(
                Recommendation(
                    programme=programme,
                    assessment=assessment,
                    student_points=display_student_points,
                    minimum_required_points=display_minimum,
                    institution_website=self.institutions.get(programme.institution_code).website if self.institutions.get(programme.institution_code) else None,
                    institution_apply_url=self._stable_apply_url(programme.institution_code),
                    cta_label=self._stable_cta_label(programme.institution_code),
                )
            )

        reviewed.sort(key=lambda item: self._rank_key(student, item), reverse=True)

        for index, recommendation in enumerate(reviewed[:limit], start=1):
            recommendation.rank = index

        return reviewed[:limit]

    def recommend_grouped(self, student: StudentResult, limit: int = 80) -> dict[str, list[Recommendation]]:
        # Same recommendations, grouped by faculty/category section.
        grouped: dict[str, list[Recommendation]] = defaultdict(list)
        for recommendation in self.recommend(student, limit=limit):
            grouped[recommendation.assessment.section].append(recommendation)
        return dict(grouped)

    def suggest_combinations(self, student: StudentResult, limit: int = 4) -> list[CombinationSuggestion]:
        # Offer guidebook-style A-Level combination guidance based on the student's subjects.
        if student.pathway.value != "a_level":
            return []

        subjects = {normalize_subject_name(subject.subject).lower() for subject in student.a_level_subjects}
        suggestions: list[CombinationSuggestion] = []
        profiles: list[tuple[str, list[str], list[str], list[str]]] = [
            ("PCB", ["Physics", "Chemistry", "Biology"], ["Health Sciences", "Science"], ["Strong fit for medicine, nursing, and biology-based programmes."]),
            ("PCM", ["Physics", "Chemistry", "Advanced Mathematics"], ["Engineering & Tech", "Science"], ["Best for engineering, IT, and mathematics-heavy routes."]),
            ("PGM", ["Physics", "Geography", "Advanced Mathematics"], ["Engineering & Tech", "Science"], ["Good for planning, surveying, transport, and geo-science tracks."]),
            ("CBG", ["Chemistry", "Biology", "Geography"], ["Health Sciences", "Agriculture", "Science"], ["Useful for health and agriculture-focused programmes."]),
            ("CBN", ["Chemistry", "Biology", "Nutrition"], ["Health Sciences", "Agriculture", "Science"], ["Useful for nutrition, health, and agriculture-focused programmes."]),
            ("HGE", ["History", "Geography", "Economics"], ["Economics & Finance", "Business"], ["Strong fit for economics, policy, and development-focused programmes."]),
            ("ECA", ["Economics", "Commerce", "Accountancy"], ["Economics & Finance", "Business"], ["Strong fit for accounting, finance, and economics degree routes."]),
            ("CBE", ["Commerce", "Book Keeping", "Economics"], ["Economics & Finance", "Business"], ["Useful for business economics, finance, and accounting pathways."]),
            ("HGL", ["History", "Geography", "English Language"], ["Education", "Arts & Humanities"], ["Broad humanities track with education and law options."]),
            ("HKL", ["History", "Kiswahili", "English Language"], ["Education", "Arts & Humanities"], ["Strong for teaching, communication, and language-based routes."]),
            ("HGK", ["History", "Geography", "Kiswahili"], ["Education", "Arts & Humanities"], ["Useful for public service and social sciences."]),
        ]

        for code, cluster, sections, rationale in profiles:
            matched = len(subjects & {item.lower() for item in cluster})
            if matched < 2:
                continue
            confidence = round(min(1.0, (matched / len(cluster)) * 0.75 + 0.15), 2)
            suggestions.append(
                CombinationSuggestion(
                    code=code,
                    subjects=cluster,
                    confidence=confidence,
                    likely_sections=sections,
                    rationale=rationale,
                )
            )

        suggestions.sort(key=lambda item: item.confidence, reverse=True)
        return suggestions[:limit]

    def _score(
        self,
        student: StudentResult,
        programme: Programme,
        student_points: float,
        *,
        o_summary: OLevelSummary | None = None,
    ) -> float:
        # Combine points margin, subject fit, competition, region preference, and capacity.
        combo = self._student_combination(student)
        req = programme.admission_requirement
        if o_summary is not None:
            min_o = req.minimum_o_level_passes or 4
            pass_margin = max(0, o_summary.pass_count - min_o)
            avg_strength = o_summary.total_grade_points / max(1, o_summary.pass_count)
            points_margin = float(pass_margin) + max(0.0, avg_strength - 2.0) * 0.85
            subject_pool = req.principal_subject_pool
            pool_fit = 0.0
            if subject_pool and req.principal_pool_min_count:
                pool_lower = {normalize_subject_name(item).lower() for item in subject_pool}
                matched = sum(1 for name in o_summary.subjects_passing if name.lower() in pool_lower)
                pool_fit = min(1.0, matched / max(1, req.principal_pool_min_count))
            else:
                pool_fit = min(1.0, 0.28 + 0.62 * min(1.0, o_summary.pass_count / 7.0))
        else:
            points_margin = max(0.0, student_points - req.minimum_total_points)
            subject_pool = req.principal_subject_pool
            pool_fit = 0.0
            if subject_pool and req.principal_pool_min_count:
                pool_lower = {normalize_subject_name(item).lower() for item in subject_pool}
                matched = sum(
                    1
                    for subject in student.a_level_subjects
                    if subject.principal and normalize_subject_name(subject.subject).lower() in pool_lower
                )
                pool_fit = min(1.0, matched / max(1, req.principal_pool_min_count))
            else:
                pool_fit = 0.35

        region_match = 1.0 if programme.region.lower() in set(student.preferred_regions) else 0.0
        preferred_institutions = set(student.preferred_institutions)
        institution_match = 1.0 if (
            programme.institution_code.lower() in preferred_institutions
            or programme.institution_name.lower() in preferred_institutions
        ) else 0.0
        capacity_factor = 0.0 if programme.capacity is None else min(1.0, programme.capacity / 500.0)

        probability = self.ranking_model.predict_probability(
            # Lightweight probability estimate used to boost the rule-based score.
            FeatureVector(
                points_margin=points_margin,
                subject_fit=pool_fit,
                competition_tier=float(programme.competition_tier),
                region_match=max(region_match, institution_match),
                capacity_factor=capacity_factor,
            )
        )

        capped_margin = min(points_margin, 6.0)
        rule_score = min(100.0, 28.0 + capped_margin * 8.0 + pool_fit * 30.0 + (6.0 if region_match or institution_match else 0.0))
        combined = (0.7 * rule_score) + (0.3 * (probability * 100.0))

        if programme.competition_tier >= 5:
            combined -= 10.0
        elif programme.competition_tier == 4:
            combined -= 6.0

        if combo == "PCB" and programme.category == ProgrammeCategory.HEALTH:
            combined += 18.0 if self._is_major_health_programme(programme) else 6.0
        elif combo in {"CBG", "CBN"} and programme.category == ProgrammeCategory.HEALTH:
            combined += 14.0 if self._is_major_health_programme(programme) else 4.0
        elif combo == "PCM" and programme.category == ProgrammeCategory.HEALTH:
            combined += 8.0 if self._is_major_health_programme(programme) else 3.0

        if region_match or institution_match:
            combined += 4.0

        return round(max(0.0, min(100.0, combined)), 2)

    def _confidence(
        self,
        score: float,
        programme: Programme,
        student: StudentResult,
        *,
        o_summary: OLevelSummary | None = None,
    ) -> float:
        # Confidence is a user-facing version of how strong the match looks.
        confidence = 22.0 + (score * 0.72)
        confidence += min(max(score - 40.0, 0.0), 30.0) * 0.48
        confidence += min(max(programme.admission_requirement.minimum_principal_passes, 0), 4) * 0.55
        confidence += min(max(programme.admission_requirement.minimum_total_points, 0.0), 12.0) * 0.16
        confidence += min(max(programme.admission_requirement.minimum_o_level_passes, 0), 6) * 0.85
        confidence -= max(0, programme.competition_tier - 1) * 1.05
        if programme.admission_requirement.strict:
            confidence -= 0.85
        if programme.category.name in {"HEALTH", "ENGINEERING"}:
            confidence -= 0.30
        if score >= 75.0:
            confidence += 2.5
        elif score < 35.0:
            confidence -= 1.0
        if o_summary is not None:
            confidence += min(8.0, max(0, o_summary.pass_count - 4) * 1.1)
            confidence += min(5.0, max(0.0, o_summary.total_grade_points / max(1, o_summary.pass_count) - 2.5) * 2.0)
        elif student.pathway.value == "a_level":
            confidence += 1.2
        return max(24.0, min(97.0, confidence))

    def _rank_key(self, student: StudentResult, recommendation: Recommendation) -> tuple[float, float, float, float, float]:
        # Show the strongest confidence first, then use score and pathway bias as tie-breakers.
        return (
            recommendation.assessment.confidence,
            recommendation.assessment.score,
            self._priority_bias(student, recommendation.programme),
            recommendation.programme.competition_tier * -1.0,
            recommendation.programme.capacity if recommendation.programme.capacity is not None else 0.0,
        )

    def _priority_bias(self, student: StudentResult, programme: Programme) -> float:
        # Preference bias nudges the list toward the most relevant academic pathway.
        combo = self._student_combination(student)
        name = programme.name.lower()
        tags = {tag.lower() for tag in programme.tags}
        bias = 0.0

        if student.pathway.value == "o_level":
            bias += self._o_level_subject_bias(student, programme)
            if programme.award_level == ProgrammeAwardLevel.CERTIFICATE:
                bias += 12.0
            elif programme.award_level == ProgrammeAwardLevel.DIPLOMA:
                bias += 9.0
        elif student.pathway.value == "a_level":
            if programme.award_level == ProgrammeAwardLevel.BACHELOR:
                bias += 8.0

        business_first_codes = {"PGM"}
        science_first_codes = {"PCB", "PCM", "CBG", "PGM", "CBN"}
        economics_first_codes = {"HGE", "ECA", "CBE", "EGM"}

        if combo in science_first_codes and (programme.category == ProgrammeCategory.ARTS or "arts" in tags):
            bias -= 10.0

        if combo in business_first_codes:
            if programme.category in {ProgrammeCategory.ACCOUNTING_FINANCE, ProgrammeCategory.BUSINESS}:
                bias += 14.0
            if any(keyword in name for keyword in ("economics", "account", "banking", "finance")):
                bias += 12.0
            if programme.category == ProgrammeCategory.ARTS:
                bias -= 4.0

        if combo in science_first_codes:
            if programme.category == ProgrammeCategory.HEALTH:
                bias += 20.0 if self._is_major_health_programme(programme) else 6.0
            elif "education" in name and "science" in name:
                bias += 16.0
            elif programme.category in {ProgrammeCategory.SCIENCE, ProgrammeCategory.ENGINEERING, ProgrammeCategory.TECH, ProgrammeCategory.COMPUTING}:
                bias += 10.0
            elif programme.category in {ProgrammeCategory.ACCOUNTING_FINANCE, ProgrammeCategory.BUSINESS} and any(
                keyword in name for keyword in ("economics", "account", "finance", "banking")
            ):
                bias += 4.0

        if combo == "PCB" and programme.category == ProgrammeCategory.HEALTH:
            bias += 22.0 if self._is_major_health_programme(programme) else 8.0
        elif combo in {"CBG", "CBN"} and programme.category == ProgrammeCategory.HEALTH:
            bias += 14.0 if self._is_major_health_programme(programme) else 4.0
        elif combo == "PCM" and programme.category == ProgrammeCategory.HEALTH:
            bias += 8.0 if self._is_major_health_programme(programme) else 3.0

        if combo in economics_first_codes:
            if self._is_economics_programme(programme):
                # Keep economics-first combinations focused on economics-family programmes.
                bias += 22.0
            elif programme.category in {ProgrammeCategory.BUSINESS, ProgrammeCategory.ACCOUNTING_FINANCE}:
                bias += 8.0
            else:
                bias -= 3.0

        if combo in {"HKL", "HGL", "HGK"}:
            if programme.category == ProgrammeCategory.ARTS:
                bias += 2.0
            else:
                bias -= 2.0

        return bias

    def _o_level_subject_bias(self, student: StudentResult, programme: Programme) -> float:
        # Nudge certificate/diploma ranking toward programmes that match the student's CSEE subject mix.
        oset = {normalize_subject_name(s.subject).lower() for s in student.o_level_subjects if s.grade and s.grade.strip()}
        if not oset:
            return 0.0
        bias = 0.0
        science_core = {"physics", "chemistry", "biology"} & oset
        if programme.category == ProgrammeCategory.HEALTH and len(science_core) >= 2:
            bias += 16.0 if self._is_major_health_programme(programme) else 8.0
        elif programme.category == ProgrammeCategory.ENGINEERING and (
            "basic mathematics" in oset or "physics" in oset or "chemistry" in oset
        ):
            bias += 11.0
        elif programme.category in {ProgrammeCategory.COMPUTING, ProgrammeCategory.TECH} and (
            "computer science" in oset or "basic mathematics" in oset
        ):
            bias += 9.0
        elif programme.category in {ProgrammeCategory.BUSINESS, ProgrammeCategory.ACCOUNTING_FINANCE} and (
            {"commerce", "book keeping", "economics", "accountancy"} & oset
        ):
            bias += 11.0
        elif programme.category == ProgrammeCategory.EDUCATION and ({"kiswahili", "english language", "history", "geography"} & oset):
            bias += 7.0
        elif programme.category == ProgrammeCategory.LAW and "english language" in oset:
            bias += 9.0
        elif programme.category == ProgrammeCategory.AGRICULTURE and ("agriculture" in oset or len(science_core) >= 1):
            bias += 8.0
        elif programme.category == ProgrammeCategory.ARTS and ({"history", "geography", "english language", "kiswahili", "fine arts"} & oset):
            bias += 6.0
        return bias

    def _student_combination(self, student: StudentResult) -> str:
        combo = student.combination or infer_combination(subject.subject for subject in student.a_level_subjects)
        return "".join(ch for ch in (combo or "").upper() if ch.isalpha())

    def _parallel_courses(self, programme: Programme) -> list[str]:
        # Offer a short list of similar programmes to show parallel pathways.
        similar: list[str] = []
        for candidate in self.programmes:
            if candidate.code == programme.code:
                continue
            same_category = candidate.category == programme.category
            same_institution = candidate.institution_code == programme.institution_code
            shared_tag = bool(set(candidate.tags) & set(programme.tags))
            if same_category or same_institution or shared_tag:
                similar.append(f"{candidate.institution_code}: {candidate.name}")
            if len(similar) >= 4:
                break
        return similar

    def _programme_allowed_for_pathway(self, student: StudentResult, programme: Programme) -> bool:
        # O-Level applicants should only see certificate and diploma routes.
        if student.pathway.value == "o_level" and programme.award_level == ProgrammeAwardLevel.BACHELOR:
            return False
        # A-Level applicants should be prioritized to bachelor routes only.
        if student.pathway.value == "a_level" and programme.award_level != ProgrammeAwardLevel.BACHELOR:
            return False
        return True

    def _stable_apply_url(self, institution_code: str) -> str | None:
        institution = self.institutions.get(institution_code)
        if not institution:
            return None
        # Prefer institution homepage for stable navigation when apply portals change.
        if institution.website and institution.website.startswith("http"):
            return institution.website
        if institution.apply_url and institution.apply_url.startswith("http"):
            return institution.apply_url
        return institution.website or institution.apply_url

    def _stable_cta_label(self, institution_code: str) -> str:
        institution = self.institutions.get(institution_code)
        if not institution:
            return "Visit Website"
        return institution.cta_label or "Visit Website"

    def _is_economics_programme(self, programme: Programme) -> bool:
        name = programme.name.lower()
        tags = {tag.lower() for tag in programme.tags}
        return (
            programme.category == ProgrammeCategory.ACCOUNTING_FINANCE
            or "economics" in name
            or "finance" in name
            or "banking" in name
            or bool({"economics", "finance", "banking"} & tags)
        )

    def _is_medicine_programme(self, programme: Programme) -> bool:
        name = programme.name.lower()
        tags = {tag.lower() for tag in programme.tags}
        return bool(
            {
                "medicine",
                "dental",
                "dentistry",
                "nursing",
                "pharmacy",
                "physiotherapy",
                "laboratory",
                "midwifery",
                "public health",
                "health information",
                "clinical medicine",
                "biomedical",
                "radiography",
                "optometry",
            }
            & ({name} | tags | set(name.split()))
        ) or any(
            keyword in name
            for keyword in (
                "doctor of medicine",
                "doctor of dental surgery",
                "medical laboratory",
                "health sciences",
                "health systems",
                "community health",
            )
        )

    def _is_major_health_programme(self, programme: Programme) -> bool:
        name = programme.name.lower()
        tags = {tag.lower() for tag in programme.tags}
        keywords = {
            "medicine",
            "medical",
            "nursing",
            "midwifery",
            "pharmacy",
            "dentistry",
            "dental",
            "physiotherapy",
            "laboratory",
            "clinical medicine",
            "radiography",
            "optometry",
            "public health",
            "biomedical",
            "surgery",
        }
        return bool(keywords & ({name} | tags | set(name.split()))) or any(
            keyword in name
            for keyword in (
                "doctor of medicine",
                "doctor of dental surgery",
                "medical laboratory",
                "clinical medicine",
                "health sciences",
                "nursing and midwifery",
                "public health",
                "pharmacy",
                "physiotherapy",
                "biomedical",
                "surgery",
            )
        )
