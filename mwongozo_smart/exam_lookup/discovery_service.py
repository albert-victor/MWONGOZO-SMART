"""Unified exam discovery: CSEE and ACSEE with automatic NECTA vs TETEA routing, then TCU recommendations."""

from __future__ import annotations

from mwongozo_smart.core.calculator import get_o_level_summary, get_principal_summary
from mwongozo_smart.core.engine import RecommendationEngine
from mwongozo_smart.core.models import StudentResult
from mwongozo_smart.data.guidebook_data import PROGRAMMES
from mwongozo_smart.exam_lookup.acsee_service import (
    AcseeResultService,
    necta_acsee_to_student_result,
    student_result_to_api_input,
)
from mwongozo_smart.exam_lookup.models import ExamType, StudentResultsLookupRequest, StudentResultsRecommendRequest
from mwongozo_smart.exam_lookup.result_service import (
    CseeResultService,
    necta_csee_result_to_student_result,
    necta_result_to_student_payload,
)
from mwongozo_smart.exam_lookup.sources.source_router import assert_supported_exam


def _student_result_to_input_dict(student: StudentResult) -> dict[str, object]:
    return {
        "pathway": student.pathway.value,
        "a_level_scheme": student.a_level_scheme.value,
        "a_level_subjects": [s.model_dump(mode="json") for s in student.a_level_subjects],
        "o_level_subjects": [s.model_dump(mode="json") for s in student.o_level_subjects],
        "combination": student.combination,
        "preferred_regions": list(student.preferred_regions),
        "preferred_institutions": list(student.preferred_institutions),
        "language": student.language,
        "equivalent_qualification": student.equivalent_qualification,
        "notes": list(student.notes),
    }


def _recommendations_bundle(student: StudentResult, engine: RecommendationEngine, limit: int) -> dict[str, object]:
    ranked = engine.recommend(student, limit=limit)
    review_limit = min(120, max(60, limit + 20))
    review = engine.review_candidates(student, limit=review_limit)
    combinations = engine.suggest_combinations(student)
    return {
        "input": _student_result_to_input_dict(student),
        "loaded_programmes": len(PROGRAMMES),
        "count": len(ranked),
        "recommendations": [item.model_dump(mode="json") for item in ranked],
        "review_candidates": [item.model_dump(mode="json") for item in review],
        "combination_suggestions": [item.model_dump(mode="json") for item in combinations],
    }


class ExamDiscoveryService:
    """Hybrid lookup: NECTA onlinesys for >=2023 (CSEE & ACSEE), TETEA Maktaba archive for older years."""

    def __init__(
        self,
        *,
        csee: CseeResultService | None = None,
        acsee: AcseeResultService | None = None,
    ) -> None:
        self._csee = csee or CseeResultService()
        self._acsee = acsee or AcseeResultService()

    async def lookup(self, body: StudentResultsLookupRequest) -> dict[str, object]:
        exam = assert_supported_exam(body.exam_type)
        if exam is ExamType.CSEE:
            record = await self._csee.lookup(body.year, body.candidate_number, skip_cache=body.skip_cache)
            student_sr = necta_csee_result_to_student_result(record)
            o_summary = get_o_level_summary(student_sr)
            return {
                "exam_type": exam.value,
                "data_source": record.data_source,
                "record": record.model_dump(mode="json"),
                "student_input": necta_result_to_student_payload(record),
                "calculated_points": {
                    "pathway": "o_level",
                    "total_grade_points": o_summary.total_grade_points,
                    "pass_count": o_summary.pass_count,
                },
            }
        record = await self._acsee.lookup(
            body.year,
            body.candidate_number,
            refresh_centre_index=False,
            skip_cache=body.skip_cache,
        )
        student = necta_acsee_to_student_result(record)
        principal = get_principal_summary(student)
        return {
            "exam_type": exam.value,
            "data_source": record.data_source,
            "record": record.model_dump(mode="json"),
            "student_input": student_result_to_api_input(student),
            "calculated_points": {
                "pathway": "a_level",
                "principal_points": principal.total_points,
                "principal_count": principal.principal_count,
            },
        }

    async def recommend(self, body: StudentResultsRecommendRequest, engine: RecommendationEngine) -> dict[str, object]:
        exam = assert_supported_exam(body.exam_type)
        if exam is ExamType.CSEE:
            record = await self._csee.lookup(body.year, body.candidate_number, skip_cache=body.skip_cache)
            student = necta_csee_result_to_student_result(
                record,
                preferred_regions=body.preferred_regions,
                preferred_institutions=body.preferred_institutions,
                language=body.language,
                a_level_scheme=body.a_level_scheme,
            )
            o_summary = get_o_level_summary(student)
            bundle = _recommendations_bundle(student, engine, body.recommend_limit)
            return {
                "exam_type": exam.value,
                "data_source": record.data_source,
                "record": record.model_dump(mode="json"),
                "student_input": necta_result_to_student_payload(record),
                "calculated_points": {
                    "pathway": "o_level",
                    "total_grade_points": o_summary.total_grade_points,
                    "pass_count": o_summary.pass_count,
                },
                "recommendations_bundle": bundle,
            }
        record = await self._acsee.lookup(
            body.year,
            body.candidate_number,
            refresh_centre_index=False,
            skip_cache=body.skip_cache,
        )
        acsee_bundle = self._acsee.recommend_from_acsee(
            record,
            engine,
            limit=body.recommend_limit,
            preferred_regions=body.preferred_regions,
            preferred_institutions=body.preferred_institutions,
            language=body.language,
            a_level_scheme=body.a_level_scheme,
        )
        recommendations_bundle: dict[str, object] = {
            "input": acsee_bundle["input"],
            "loaded_programmes": acsee_bundle["loaded_programmes"],
            "count": acsee_bundle["count"],
            "recommendations": acsee_bundle["recommendations"],
            "review_candidates": acsee_bundle["review_candidates"],
            "combination_suggestions": acsee_bundle["combination_suggestions"],
        }
        return {
            "exam_type": exam.value,
            "data_source": record.data_source,
            "record": acsee_bundle["necta"],
            "student_input": acsee_bundle["input"],
            "calculated_points": {
                "pathway": "a_level",
                "principal_points": acsee_bundle["tcu_points"],
                "principal_count": acsee_bundle["principal_count"],
            },
            "recommendations_bundle": recommendations_bundle,
        }
