from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Iterable

from mwongozo_smart.core.health_classification import (
    health_bachelor_confidence_cap,
    is_clinical_health_programme,
    is_general_health_programme,
)
from mwongozo_smart.core.pool_normalize import normalize_principal_subject_pool
from mwongozo_smart.data.institution_catalog import is_programme_allowed_for_institution
from mwongozo_smart.core.calculator import (
    OLevelSummary,
    a_level_sensitive_readiness,
    csee_division_band,
    csee_health_award_allowed,
    csee_o_level_entry_gate,
    extract_csee_division,
    get_o_level_summary,
    get_principal_summary,
    normalize_student_subjects,
    o_level_health_science_eligible,
    o_level_stem_engineering_eligible,
)
from mwongozo_smart.core.models import CombinationSuggestion, ConfidenceBand, Programme, ProgrammeAwardLevel, ProgrammeCategory, Recommendation, StudentResult
from mwongozo_smart.core.rules import TCURuleEngine
from mwongozo_smart.data.guidebook_data import PROGRAMMES
from mwongozo_smart.data.institutions import INSTITUTIONS
from mwongozo_smart.ml.ranking_model import FeatureVector, RuleBoostedRankingModel
from mwongozo_smart.utils.combination_helper import (
    combination_blocks_stem_programme,
    infer_combination,
    normalize_subject_name,
    resolve_student_combination,
)
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

    def recommend(self, student: StudentResult, limit: int = 120) -> list[Recommendation]:
        # The principal subjects are summarized once, then reused for all programmes.
        normalize_student_subjects(student)
        if student.pathway.value == "o_level":
            entry_ok, entry_msg, _ = csee_o_level_entry_gate(student)
            if not entry_ok:
                logger.info("O-Level recommendations blocked: %s", entry_msg)
                return []
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
            assessment.confidence = self._apply_health_division_confidence_cap(
                assessment.confidence, student, programme
            )
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
        ranked = self._promote_college_health_for_weak_csee(student, ranked)
        ranked = self._diversify_a_level_health(student, ranked)
        ranked = self._interleave_o_level_by_category(student, ranked)

        for index, recommendation in enumerate(ranked[:limit], start=1):
            recommendation.rank = index

        return ranked[:limit]

    def review_candidates(self, student: StudentResult, limit: int = 10) -> list[Recommendation]:
        # Near-miss programmes are useful when there are no direct matches.
        normalize_student_subjects(student)
        if student.pathway.value == "o_level":
            entry_ok, _entry_msg, _ = csee_o_level_entry_gate(student)
            if not entry_ok:
                return []
        summary = get_principal_summary(student)
        o_summary = get_o_level_summary(student) if student.pathway.value == "o_level" else None
        reviewed: list[Recommendation] = []
        is_o_level = student.pathway.value == "o_level"

        combo = resolve_student_combination(student.combination, student.a_level_subjects)

        for programme in self.programmes:
            if not self._programme_allowed_for_pathway(student, programme):
                continue
            if not is_o_level and combination_blocks_stem_programme(combo, programme.category.value):
                continue
            if is_o_level and programme.category == ProgrammeCategory.HEALTH:
                health_sci_ok, _health_sci_msg = o_level_health_science_eligible(student)
                if not health_sci_ok:
                    continue
            if is_o_level and programme.category in {
                ProgrammeCategory.ENGINEERING,
                ProgrammeCategory.TECH,
                ProgrammeCategory.COMPUTING,
            }:
                stem_ok, _stem_msg = o_level_stem_engineering_eligible(student)
                if not stem_ok:
                    continue
            assessment = self.rule_engine.evaluate(student, programme)
            if assessment.eligible:
                continue

            score = self._score(student, programme, summary.total_points, o_summary=o_summary)
            assessment.score = score
            assessment.confidence = round(self._confidence(score, programme, student, o_summary=o_summary), 2)
            assessment.confidence = self._apply_health_division_confidence_cap(
                assessment.confidence, student, programme
            )
            assessment.confidence_band = ConfidenceBand(confidence_band_from_score(assessment.confidence))
            assessment.parallel_courses = self._parallel_courses(programme)

            if is_o_level:
                if score < 12.0 and assessment.points_margin < -5.0:
                    continue
            elif score < 22.0 and assessment.points_margin < -2.0:
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

    def recommend_grouped(self, student: StudentResult, limit: int = 120) -> dict[str, list[Recommendation]]:
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
                pool_tokens = normalize_principal_subject_pool(subject_pool) or list(subject_pool)
                pool_lower = {normalize_subject_name(item).lower() for item in pool_tokens}
                matched = sum(
                    1
                    for subject in student.a_level_subjects
                    if subject.principal and normalize_subject_name(subject.subject).lower() in pool_lower
                )
                effective_min = req.principal_pool_min_count
                if programme.category == ProgrammeCategory.HEALTH and matched >= 2 and effective_min >= 3:
                    effective_min = 2
                pool_fit = min(1.0, matched / max(1, effective_min))
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

        readiness = a_level_sensitive_readiness(student) if student.pathway.value == "a_level" else None
        health_boost_ok = readiness is None or (
            bool(readiness["health_science_ready"]) and float(readiness["total_points"]) >= 6.0
        )
        if is_general_health_programme(programme):
            health_boost_ok = readiness is None or float(readiness["total_points"]) >= 4.5
        if health_boost_ok and combo == "PCB" and programme.category == ProgrammeCategory.HEALTH:
            combined += 18.0 if self._is_major_health_programme(programme) else 6.0
        elif health_boost_ok and combo in {"CBG", "CBN"} and programme.category == ProgrammeCategory.HEALTH:
            combined += 8.0 if self._is_major_health_programme(programme) else 2.0
        elif health_boost_ok and combo == "PCM" and programme.category == ProgrammeCategory.HEALTH:
            combined += 6.0 if self._is_major_health_programme(programme) else 2.0

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
            confidence = self._cap_a_level_confidence(confidence, student, programme, score)
        health_cap = health_bachelor_confidence_cap(student, programme)
        if health_cap is not None:
            confidence = min(confidence, health_cap)
        return max(24.0, min(97.0, confidence))

    def _promote_college_health_for_weak_csee(
        self,
        student: StudentResult,
        ranked: list[Recommendation],
    ) -> list[Recommendation]:
        """Surface NACTVET/NACTE health diplomas/certificates for CSEE Division III–IV."""
        if student.pathway.value != "o_level":
            return ranked
        band = csee_division_band(extract_csee_division(student))
        if band not in {"weak", "borderline"}:
            return ranked
        college_health = [
            item
            for item in ranked
            if item.programme.category == ProgrammeCategory.HEALTH
            and item.programme.award_level in {ProgrammeAwardLevel.CERTIFICATE, ProgrammeAwardLevel.DIPLOMA}
        ]
        if not college_health:
            return ranked
        college_health.sort(
            key=lambda item: (
                0 if item.programme.award_level == ProgrammeAwardLevel.DIPLOMA else 1,
                -item.assessment.confidence,
            )
        )
        promote = college_health[:6]
        promote_codes = {item.programme.code for item in promote}
        remainder = [item for item in ranked if item.programme.code not in promote_codes]
        return promote + remainder

    def _apply_health_division_confidence_cap(
        self,
        confidence: float,
        student: StudentResult,
        programme: Programme,
    ) -> float:
        if programme.category != ProgrammeCategory.HEALTH:
            return confidence
        allowed, max_conf, _ = csee_health_award_allowed(student, programme.award_level.value)
        if not allowed:
            return confidence
        if max_conf is not None:
            confidence = min(confidence, max_conf)
        tier_cap = health_bachelor_confidence_cap(student, programme)
        if tier_cap is not None:
            confidence = min(confidence, tier_cap)
        return confidence

    def _health_programme_family(self, programme: Programme) -> str:
        name = programme.name.lower()
        if is_clinical_health_programme(programme):
            return "clinical"
        if "environmental" in name:
            return "environmental"
        if "community" in name or "public health" in name:
            return "public"
        if "laboratory" in name or "lab " in name:
            return "laboratory"
        if "food" in name or "nutrition" in name:
            return "nutrition"
        if "management" in name or "information" in name:
            return "management"
        return "other"

    def _diversify_a_level_health(
        self,
        student: StudentResult,
        ranked: list[Recommendation],
    ) -> list[Recommendation]:
        if student.pathway.value != "a_level":
            return ranked
        health_items = [item for item in ranked if item.programme.category == ProgrammeCategory.HEALTH]
        if len(health_items) < 6:
            return ranked
        non_health = [item for item in ranked if item.programme.category != ProgrammeCategory.HEALTH]
        by_family: dict[str, list[Recommendation]] = {}
        for item in health_items:
            family = self._health_programme_family(item.programme)
            by_family.setdefault(family, []).append(item)
        for bucket in by_family.values():
            bucket.sort(key=lambda item: self._rank_key(student, item), reverse=True)

        institution_seen: dict[str, int] = {}
        spread: list[Recommendation] = []
        families = sorted(by_family.keys(), key=lambda key: len(by_family[key]), reverse=True)
        exhausted = False
        while not exhausted and len(spread) < len(health_items):
            exhausted = True
            for family in families:
                bucket = by_family.get(family) or []
                if not bucket:
                    continue
                pick_index = 0
                while pick_index < len(bucket):
                    candidate = bucket[pick_index]
                    code = candidate.programme.institution_code.lower()
                    if institution_seen.get(code, 0) >= 2:
                        pick_index += 1
                        continue
                    spread.append(bucket.pop(pick_index))
                    institution_seen[code] = institution_seen.get(code, 0) + 1
                    exhausted = False
                    break
                else:
                    if bucket:
                        spread.append(bucket.pop(0))
                        exhausted = False
        spread_codes = {item.programme.code for item in spread}
        tail = [item for item in health_items if item.programme.code not in spread_codes]
        merged_health = spread + tail
        return merged_health + non_health

    def _interleave_o_level_by_category(
        self,
        student: StudentResult,
        ranked: list[Recommendation],
    ) -> list[Recommendation]:
        """Spread O-Level results across categories so ICT does not dominate every list."""
        if student.pathway.value != "o_level" or len(ranked) < 8:
            return ranked
        import hashlib
        import random
        from collections import defaultdict

        buckets: dict[str, list[Recommendation]] = defaultdict(list)
        for item in ranked:
            buckets[item.programme.category.value].append(item)
        categories = list(buckets.keys())
        fingerprint = "|".join(
            [
                extract_csee_division(student) or "",
                str(sorted((s.subject, s.grade) for s in student.o_level_subjects[:8])),
            ]
        )
        seed = int(hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:16], 16)
        rng = random.Random(seed)
        rng.shuffle(categories)
        merged: list[Recommendation] = []
        while True:
            moved = False
            for cat in categories:
                if buckets[cat]:
                    merged.append(buckets[cat].pop(0))
                    moved = True
            if not moved:
                break
        return merged

    def _cap_a_level_confidence(
        self,
        confidence: float,
        student: StudentResult,
        programme: Programme,
        score: float,
    ) -> float:
        summary = get_principal_summary(student)
        margin = summary.total_points - programme.admission_requirement.minimum_total_points
        sensitive = programme.category in {
            ProgrammeCategory.HEALTH,
            ProgrammeCategory.ENGINEERING,
            ProgrammeCategory.TECH,
            ProgrammeCategory.COMPUTING,
        }
        if summary.total_points < 4.5:
            return min(confidence, 30.0)
        if sensitive:
            readiness = a_level_sensitive_readiness(student)
            if summary.total_points < 6.0:
                confidence = min(confidence, 36.0)
            elif margin <= 1.0:
                confidence = min(confidence, 42.0)
            elif margin <= 2.0:
                confidence = min(confidence, 50.0)
            if programme.category == ProgrammeCategory.HEALTH and not readiness["health_science_ready"]:
                confidence = min(confidence, 38.0)
            if programme.category in {
                ProgrammeCategory.ENGINEERING,
                ProgrammeCategory.TECH,
                ProgrammeCategory.COMPUTING,
            } and not readiness["stem_ready"]:
                confidence = min(confidence, 38.0)
        elif margin <= 1.0:
            confidence = min(confidence, 55.0)
        elif score < 45.0:
            confidence = min(confidence, 58.0)
        return confidence

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
        readiness = a_level_sensitive_readiness(student) if student.pathway.value == "a_level" else None
        health_bias_ok = readiness is None or (
            bool(readiness["health_science_ready"]) and float(readiness["total_points"]) >= 6.0
        )

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
            if programme.category == ProgrammeCategory.HEALTH and health_bias_ok:
                bias += 12.0 if self._is_major_health_programme(programme) else 4.0
            elif "education" in name and "science" in name:
                bias += 16.0
            elif programme.category in {ProgrammeCategory.SCIENCE, ProgrammeCategory.ENGINEERING, ProgrammeCategory.TECH, ProgrammeCategory.COMPUTING}:
                bias += 10.0
            elif programme.category in {ProgrammeCategory.ACCOUNTING_FINANCE, ProgrammeCategory.BUSINESS} and any(
                keyword in name for keyword in ("economics", "account", "finance", "banking")
            ):
                bias += 4.0

        if health_bias_ok and combo == "PCB" and programme.category == ProgrammeCategory.HEALTH:
            bias += 22.0 if self._is_major_health_programme(programme) else 8.0
        elif health_bias_ok and combo in {"CBG", "CBN"} and programme.category == ProgrammeCategory.HEALTH:
            if is_general_health_programme(programme):
                bias += 14.0
            else:
                bias += 8.0 if self._is_major_health_programme(programme) else 4.0
        elif health_bias_ok and combo == "PCM" and programme.category == ProgrammeCategory.HEALTH:
            bias += 4.0 if self._is_major_health_programme(programme) else 1.0

        if combo in economics_first_codes:
            if self._is_economics_programme(programme):
                # Keep economics-first combinations focused on economics-family programmes.
                bias += 22.0
            elif programme.category in {ProgrammeCategory.BUSINESS, ProgrammeCategory.ACCOUNTING_FINANCE}:
                bias += 8.0
            else:
                bias -= 3.0

        if combo in {"HKL", "HGL", "HGK", "HGE"}:
            if programme.category == ProgrammeCategory.ARTS:
                bias += 6.0
            elif programme.category in {
                ProgrammeCategory.HEALTH,
                ProgrammeCategory.SCIENCE,
                ProgrammeCategory.ENGINEERING,
                ProgrammeCategory.COMPUTING,
                ProgrammeCategory.TECH,
            }:
                bias -= 40.0
            elif programme.category in {ProgrammeCategory.BUSINESS, ProgrammeCategory.ACCOUNTING_FINANCE, ProgrammeCategory.LAW, ProgrammeCategory.EDUCATION}:
                bias += 4.0

        return bias

    def _o_level_subject_bias(self, student: StudentResult, programme: Programme) -> float:
        # Nudge certificate/diploma ranking toward programmes that match the student's CSEE subject mix.
        oset = {normalize_subject_name(s.subject).lower() for s in student.o_level_subjects if s.grade and s.grade.strip()}
        if not oset:
            return 0.0
        bias = 0.0
        science_core = {"physics", "chemistry", "biology"} & oset
        if programme.category == ProgrammeCategory.HEALTH and len(science_core) >= 2:
            band = csee_division_band(extract_csee_division(student))
            if programme.award_level == ProgrammeAwardLevel.DIPLOMA and band in {"weak", "borderline"}:
                bias += 38.0 if self._is_major_health_programme(programme) else 26.0
            elif programme.award_level == ProgrammeAwardLevel.CERTIFICATE and band in {"weak", "borderline"}:
                bias += 24.0
            else:
                bias += 16.0 if self._is_major_health_programme(programme) else 8.0
        elif programme.category == ProgrammeCategory.ENGINEERING and (
            "basic mathematics" in oset or "physics" in oset or "chemistry" in oset
        ):
            bias += 11.0
        elif programme.category in {ProgrammeCategory.COMPUTING, ProgrammeCategory.TECH} and (
            "computer science" in oset or "basic mathematics" in oset
        ):
            bias += 3.0
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
        return resolve_student_combination(student.combination, student.a_level_subjects)

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
        if not is_programme_allowed_for_institution(programme):
            return False
        # O-Level applicants should only see certificate and diploma routes.
        if student.pathway.value == "o_level" and programme.award_level == ProgrammeAwardLevel.BACHELOR:
            return False
        if student.pathway.value == "a_level":
            if programme.award_level == ProgrammeAwardLevel.BACHELOR:
                return True
            band = csee_division_band(extract_csee_division(student))
            if band in {"weak", "borderline"} and programme.award_level in {
                ProgrammeAwardLevel.CERTIFICATE,
                ProgrammeAwardLevel.DIPLOMA,
            }:
                if programme.category == ProgrammeCategory.HEALTH:
                    allowed, _, _ = csee_health_award_allowed(student, programme.award_level.value)
                    return allowed
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
