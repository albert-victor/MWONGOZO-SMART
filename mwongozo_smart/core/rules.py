from __future__ import annotations

from collections.abc import Iterable

from mwongozo_smart.core.calculator import (
    a_level_sensitive_readiness,
    a_level_subject_grade_map,
    csee_health_award_allowed,
    csee_o_level_entry_gate,
    get_o_level_summary,
    get_principal_summary,
    o_level_health_science_eligible,
    o_level_stem_engineering_eligible,
    o_level_subject_grade_map,
    student_has_subject,
)
from mwongozo_smart.utils.combination_helper import (
    combination_blocks_stem_programme,
    normalize_subject_name,
    resolve_student_combination,
)
from mwongozo_smart.core.health_classification import (
    is_clinical_health_programme,
    is_general_health_programme,
)
from mwongozo_smart.core.pool_normalize import (
    health_principal_pool_satisfied,
    normalize_principal_subject_pool,
)
from mwongozo_smart.core.models import (
    AdmissionRequirement,
    ConfidenceBand,
    EligibilityIssue,
    Programme,
    ProgrammeAwardLevel,
    ProgrammeAssessment,
    ProgrammeCategory,
    RuleTrace,
    StudentResult,
)
from mwongozo_smart.utils.grade_converter import confidence_band_from_score, grade_at_least


class TCURuleEngine:
    """Strict rule evaluator based on the 2025/2026 TCU guidebook."""

    def evaluate(self, student: StudentResult, programme: Programme) -> ProgrammeAssessment:
        # Rules are checked before any ranking happens. If a programme fails here,
        # it will not appear in the final recommendation list.
        summary = get_principal_summary(student)
        requirement = programme.admission_requirement
        issues: list[EligibilityIssue] = []
        matched_rules: list[str] = []
        missing_rules: list[str] = []
        warnings: list[str] = []
        rule_traces: list[RuleTrace] = []
        rule_points = 0.0

        def add_trace(rule_id: str, label: str, passed: bool, message: str, points: float = 0.0, details: str | None = None) -> None:
            nonlocal rule_points
            rule_traces.append(
                RuleTrace(
                    rule_id=rule_id,
                    label=label,
                    passed=passed,
                    points=round(points if passed else 0.0, 2),
                    message=message,
                    details=details,
                )
            )
            if passed:
                rule_points += points

        combo = resolve_student_combination(student.combination, student.a_level_subjects)

        if student.pathway.value == "o_level":
            entry_ok, entry_msg, _division = csee_o_level_entry_gate(student)
            if not entry_ok:
                add_trace("csee_division", "CSEE overall division", False, entry_msg)
                return ProgrammeAssessment(
                    eligible=False,
                    score=0.0,
                    confidence=0.0,
                    confidence_band=ConfidenceBand.VERY_LOW,
                    rule_points=rule_points,
                    missing_rules=[entry_msg],
                    issues=[EligibilityIssue(rule_id="csee_division", message=entry_msg)],
                    rule_traces=rule_traces,
                    why_not_matched=[entry_msg],
                    section=self._section_for(programme),
                )

        o_level_only = student.pathway.value == "o_level" and programme.award_level == ProgrammeAwardLevel.BACHELOR
        if o_level_only:
            # O-Level students should not be routed into bachelor programmes directly.
            add_trace(
                "pathway",
                "Admission pathway",
                False,
                "O-Level applicants are restricted to certificate and diploma routes in this engine.",
            )
            return ProgrammeAssessment(
                eligible=False,
                score=0.0,
                confidence=0.0,
                confidence_band=ConfidenceBand.VERY_LOW,
                rule_points=rule_points,
                missing_rules=["O-Level applicants cannot apply directly to bachelor programmes here."],
                issues=[EligibilityIssue(rule_id="pathway", message="O-Level applicants cannot apply directly to bachelor programmes here.")],
                rule_traces=rule_traces,
                why_not_matched=["This profile is treated as O-Level only and does not qualify for direct bachelor entry."],
                section=self._section_for(programme),
            )

        if student.pathway.value == "a_level" and combination_blocks_stem_programme(combo, programme.category.value):
            add_trace(
                "combination_stem",
                "Combination vs programme",
                False,
                (
                    f"Combination {combo or 'unknown'} cannot qualify for "
                    f"{programme.category.value.replace('_', ' ')} programmes."
                ),
                0.0,
            )
            issues.append(
                EligibilityIssue(
                    rule_id="combination_stem",
                    message=(
                        f"Arts/business combinations such as {combo} do not qualify for "
                        f"{programme.category.value.replace('_', ' ')} programmes. "
                        "Health and STEM routes require science combinations (e.g. PCB, PCM, CBG)."
                    ),
                )
            )

        college_route = student.pathway.value == "o_level" and programme.award_level != ProgrammeAwardLevel.BACHELOR

        if programme.category == ProgrammeCategory.LAW:
            if college_route:
                law_ok = student_has_subject(student, "English Language", "D")
            else:
                law_ok = student_has_subject(student, "English Language", "D") or student_has_subject(
                    student, "History", "D"
                ) or student_has_subject(student, "Kiswahili", "D")
            add_trace(
                "law_anchor",
                "Law / legal anchor",
                law_ok,
                "Law routes require strong English (and humanities for bachelor programmes).",
                4.0,
            )
            if not law_ok:
                issues.append(
                    EligibilityIssue(
                        rule_id="law_anchor",
                        message="Law programmes require English Language at grade D or better (CSEE / A-Level).",
                    )
                )

        if programme.category in {ProgrammeCategory.ENGINEERING, ProgrammeCategory.TECH, ProgrammeCategory.COMPUTING}:
            # Engineering and tech programmes need strong math/science anchors.
            if college_route:
                stem_ok, stem_msg = o_level_stem_engineering_eligible(student)
                math_ok = any(
                    student_has_subject(student, name, "D") for name in ("Basic Mathematics", "Mathematics")
                )
                if not math_ok:
                    add_trace(
                        "college_stem_math",
                        "CSEE mathematics for STEM/TVET",
                        False,
                        "Certificate/diploma tech routes require CSEE Mathematics or Basic Mathematics at grade D or better.",
                    )
                    issues.append(
                        EligibilityIssue(
                            rule_id="college_stem_math",
                            message="Tech and engineering college routes require CSEE Mathematics or Basic Mathematics (grade D+).",
                        )
                    )
                anchor_ok = stem_ok
                if not stem_ok:
                    add_trace(
                        "o_level_stem_engineering_gate",
                        "CSEE STEM for engineering/tech",
                        False,
                        stem_msg,
                        6.0,
                    )
                    issues.append(
                        EligibilityIssue(
                            rule_id="o_level_stem_engineering_gate",
                            message=stem_msg,
                        )
                    )
            else:
                math_ok = student_has_subject(student, "Advanced Mathematics", "D") or student_has_subject(
                    student, "Basic Applied Mathematics", "D"
                )
                phys_chem_ok = student_has_subject(student, "Physics", "D") and student_has_subject(
                    student, "Chemistry", "D"
                )
                anchor_ok = math_ok or phys_chem_ok
            add_trace(
                "engineering_anchor",
                "STEM anchor",
                anchor_ok,
                (
                    "Engineering/Tech bachelor routes require Advanced/Basic Applied Mathematics (D+) "
                    "or both Physics and Chemistry at D+."
                ),
                5.0,
            )
            if not anchor_ok:
                issues.append(
                    EligibilityIssue(
                        rule_id="engineering_anchor",
                        message="Engineering/Tech programmes require at least one science or mathematics principal subject.",
                    )
                )

            if any(tag in {"civil", "architecture"} for tag in programme.tags):
                if college_route:
                    math_ok = self._has_any_subjects(student, ["Basic Mathematics", "Mathematics", "Physics"])
                    if not math_ok:
                        issues.append(
                            EligibilityIssue(
                                rule_id="engineering_math_anchor",
                                message="Civil/Architecture college routes require CSEE Mathematics or a science subject.",
                            )
                        )
                elif not self._has_any_principal_subjects(student, ["Advanced Mathematics", "Basic Applied Mathematics"]):
                    issues.append(
                        EligibilityIssue(
                            rule_id="engineering_math_anchor",
                            message="Civil/Architecture pathways require Advanced Mathematics or Basic Applied Mathematics as a principal subject.",
                        )
                    )

            if any(tag in {"electrical", "chemical"} for tag in programme.tags):
                if college_route:
                    sci_ok = self._has_any_subjects(student, ["Physics", "Chemistry", "Basic Mathematics", "Mathematics"])
                    if not sci_ok:
                        issues.append(
                            EligibilityIssue(
                                rule_id="engineering_science_anchor",
                                message="Electrical/Chemical college routes require CSEE Physics, Chemistry, or Mathematics.",
                            )
                        )
                elif not self._has_any_principal_subjects(student, ["Physics", "Chemistry"]):
                    issues.append(
                        EligibilityIssue(
                            rule_id="engineering_science_anchor",
                            message="Electrical/Chemical pathways require Physics or Chemistry as a principal subject.",
                        )
                    )

            if any(tag in {"computer", "it"} for tag in programme.tags):
                if college_route:
                    computer_ok = self._has_any_subjects(student, ["Basic Mathematics", "Mathematics", "Computer Studies", "Computer Science"])
                else:
                    computer_ok = self._has_any_principal_subjects(student, ["Advanced Mathematics", "Computer Science"])
                add_trace(
                    "engineering_computer_anchor",
                    "Computing anchor",
                    computer_ok,
                    "Computer/IT pathways require Advanced Mathematics or Computer Science as a principal subject.",
                    5.0,
                )
                if not computer_ok:
                    issues.append(
                        EligibilityIssue(
                            rule_id="engineering_computer_anchor",
                            message="Computer/IT pathways require Advanced Mathematics or Computer Science as a principal subject.",
                        )
                    )

        if programme.category == ProgrammeCategory.HEALTH:
            health_allowed, _health_cap, health_div_msg = csee_health_award_allowed(
                student, programme.award_level.value
            )
            add_trace(
                "csee_health_division",
                "CSEE division vs health award",
                health_allowed,
                health_div_msg or "CSEE division supports this health award level.",
                10.0,
            )
            if not health_allowed:
                issues.append(
                    EligibilityIssue(
                        rule_id="csee_health_division",
                        message=health_div_msg,
                    )
                )

            # Health programmes are strict because they need the right science base.
            anchor_msg = "Health programmes require appropriate science foundation."
            if college_route:
                health_ok, anchor_msg = o_level_health_science_eligible(student)
            elif student.pathway.value == "a_level":
                if is_clinical_health_programme(programme):
                    health_ok = student_has_subject(student, "Biology", "D") and student_has_subject(
                        student, "Chemistry", "D"
                    )
                    anchor_msg = "Clinical health (medicine/nursing) needs Biology and Chemistry at grade D+."
                elif is_general_health_programme(programme):
                    health_ok = student_has_subject(student, "Biology", "D") or student_has_subject(
                        student, "Chemistry", "D"
                    )
                    anchor_msg = "General health sciences need Biology or Chemistry at grade D+ (TCU college routes)."
                else:
                    health_ok = student_has_subject(student, "Biology", "D") or student_has_subject(
                        student, "Chemistry", "D"
                    )
                    anchor_msg = "Health programmes need Biology or Chemistry at grade D+ (see programme minimums)."
            else:
                health_ok = self._has_all_principal_subjects(student, ["Biology", "Chemistry"])
                anchor_msg = "Health programmes require Biology and Chemistry foundation at principal level."
            add_trace(
                "health_anchor",
                "Health anchor",
                health_ok,
                anchor_msg,
                5.0,
            )
            if not health_ok:
                issues.append(
                    EligibilityIssue(
                        rule_id="health_anchor",
                        message=anchor_msg,
                    )
                )

            if (
                student.pathway.value == "a_level"
                and not college_route
                and programme.award_level == ProgrammeAwardLevel.BACHELOR
                and is_clinical_health_programme(programme)
            ):
                readiness = a_level_sensitive_readiness(student)
                min_health_points = 7.0
                points_ok_health = float(readiness["total_points"]) >= min_health_points
                add_trace(
                    "health_points_floor",
                    "Clinical health points (TCU)",
                    points_ok_health,
                    f"Clinical routes need about {min_health_points} A-Level points; found {readiness['total_points']}.",
                    8.0,
                )
                if not points_ok_health:
                    issues.append(
                        EligibilityIssue(
                            rule_id="health_points_floor",
                            message=(
                                f"Clinical health programmes need about {min_health_points}+ A-Level points; "
                                f"this profile has {readiness['total_points']}."
                            ),
                        )
                    )
                clinical_ok = bool(readiness["biology_c_plus"] and readiness["chemistry_c_plus"])
                add_trace(
                    "health_clinical_grades",
                    "Clinical health grades",
                    clinical_ok,
                    "Medicine/nursing/pharmacy routes need Biology and Chemistry at grade C or better.",
                    8.0,
                )
                if not clinical_ok:
                    issues.append(
                        EligibilityIssue(
                            rule_id="health_clinical_grades",
                            message="Clinical health routes need Biology and Chemistry at grade C or better.",
                        )
                    )

        if college_route:
            add_trace(
                "principal_passes",
                "Principal passes",
                True,
                "O-Level college routes use pass-count checks instead of A-Level principal passes.",
                0.0,
            )
            principal_pass_ok = True
        else:
            principal_pass_ok = summary.principal_count >= requirement.minimum_principal_passes
            add_trace(
                "principal_passes",
                "Principal passes",
                principal_pass_ok,
                f"Needs at least {requirement.minimum_principal_passes} principal passes, found {summary.principal_count}.",
                10.0,
            )
            if not principal_pass_ok:
                # Count only principal passes, not all subjects.
                issues.append(
                    EligibilityIssue(
                        rule_id="principal_passes",
                        message=f"Needs at least {requirement.minimum_principal_passes} principal passes, found {summary.principal_count}.",
                    )
                )

        if college_route:
            add_trace(
                "minimum_points",
                "Minimum points",
                True,
                "O-Level college routes rely on O-Level passes and subject grades.",
                0.0,
            )
            points_ok = True
            matched_rules.append("minimum_points")
        else:
            points_ok = summary.total_points >= requirement.minimum_total_points
            add_trace(
                "minimum_points",
                "Minimum points",
                points_ok,
                f"Needs at least {requirement.minimum_total_points} points, found {summary.total_points}.",
                20.0,
            )
            if not points_ok:
                # Total points are the main pass/fail gate.
                issues.append(
                    EligibilityIssue(
                        rule_id="minimum_points",
                        message=f"Needs at least {requirement.minimum_total_points} points, found {summary.total_points}.",
                    )
                )
            else:
                matched_rules.append("minimum_points")

            if student.pathway.value == "a_level" and programme.category in {
                ProgrammeCategory.ENGINEERING,
                ProgrammeCategory.TECH,
                ProgrammeCategory.COMPUTING,
            }:
                readiness = a_level_sensitive_readiness(student)
                stem_floor = 5.0
                stem_points_ok = float(readiness["total_points"]) >= stem_floor and bool(readiness["stem_ready"])
                add_trace(
                    "stem_points_floor",
                    "STEM points floor (TCU)",
                    stem_points_ok,
                    f"STEM bachelor routes need about {stem_floor}+ points with mathematics or Physics+Chemistry (D+).",
                    6.0,
                )
                if not stem_points_ok:
                    issues.append(
                        EligibilityIssue(
                            rule_id="stem_points_floor",
                            message=(
                                "Engineering/Tech routes need stronger STEM preparation "
                                "(mathematics D+ or Physics and Chemistry both D+)."
                            ),
                        )
                    )

        if requirement.minimum_o_level_passes and student.pathway.value == "o_level":
            o_level_passes = sum(1 for subject in student.o_level_subjects if grade_at_least(subject.grade, "D"))
            o_level_pass_ok = o_level_passes >= requirement.minimum_o_level_passes
            add_trace(
                "o_level_passes",
                "O-Level passes",
                o_level_pass_ok,
                f"Needs at least {requirement.minimum_o_level_passes} O-Level passes, found {o_level_passes}.",
                10.0,
            )
            if not o_level_pass_ok:
                issues.append(
                    EligibilityIssue(
                        rule_id="o_level_passes",
                        message=f"Needs at least {requirement.minimum_o_level_passes} O-Level passes, found {o_level_passes}.",
                    )
                )
            else:
                matched_rules.append("o_level_passes")

        if requirement.principal_subject_pool and requirement.principal_pool_min_count:
            # Many programmes need a specific subject mix, not just a point total.
            normalized_pool = normalize_principal_subject_pool(requirement.principal_subject_pool)
            pool_for_match = normalized_pool or list(requirement.principal_subject_pool)
            count = self._count_pool_matches(student, pool_for_match, college_route)
            pool_ok, count, effective_min = health_principal_pool_satisfied(
                student,
                programme,
                requirement.principal_subject_pool,
                requirement.principal_pool_min_count,
                matched_count=count,
                college_route=college_route,
            )
            if not pool_ok:
                pool_ok = count >= requirement.principal_pool_min_count
                effective_min = requirement.principal_pool_min_count
            pool_label = "O-Level subjects in the approved pool" if college_route else "Principal subjects from the approved pool"
            add_trace(
                "principal_pool",
                "Approved subject pool",
                pool_ok,
                f"Needs at least {effective_min} {pool_label.lower()}, found {count}.",
                15.0,
            )
            if not pool_ok:
                issues.append(
                    EligibilityIssue(
                        rule_id="principal_pool",
                        message=f"Needs at least {effective_min} principal subjects from the approved pool, found {count}.",
                    )
                )
            else:
                matched_rules.append("principal_pool")

        for subject in requirement.required_principal_subjects:
            # Some programmes demand specific subjects by name.
            subject_ok = student_has_subject(student, subject)
            add_trace(
                f"req_subject:{subject}",
                f"Required subject: {subject}",
                subject_ok,
                f"Missing required subject: {subject}.",
                8.0,
            )
            if not subject_ok:
                issues.append(EligibilityIssue(rule_id=f"req_subject:{subject}", message=f"Missing required subject: {subject}."))
            else:
                matched_rules.append(f"subject:{subject}")

        a_level_map = a_level_subject_grade_map(student)
        o_level_map = o_level_subject_grade_map(student)
        for subject, minimum_grade in requirement.minimum_a_level_subject_grades.items():
            # Grade floor checks for individual A-Level subjects.
            actual = a_level_map.get(subject)
            grade_ok = actual is not None and grade_at_least(actual, minimum_grade, student.a_level_scheme)
            add_trace(
                f"a_level:{subject}",
                f"A-Level grade: {subject}",
                grade_ok,
                f"{subject} needs at least {minimum_grade}.",
                8.0,
                details=f"Actual grade: {actual or 'missing'}",
            )
            if not grade_ok:
                issues.append(
                    EligibilityIssue(
                        rule_id=f"a_level:{subject}",
                        message=f"{subject} needs at least {minimum_grade}.",
                    )
                )
            else:
                matched_rules.append(f"a_level:{subject}")

        for subject, minimum_grade in requirement.minimum_o_level_subject_grades.items():
            # Grade floor checks for O-Level fallback requirements.
            actual = o_level_map.get(subject)
            grade_scheme = student.a_level_scheme
            if actual is None and student.pathway.value == "a_level":
                actual = a_level_map.get(subject)
                grade_scheme = student.a_level_scheme
            grade_ok = actual is not None and grade_at_least(actual, minimum_grade, grade_scheme)
            add_trace(
                f"o_level:{subject}",
                f"O-Level grade: {subject}",
                grade_ok,
                f"O-Level {subject} needs at least {minimum_grade}.",
                8.0,
                details=f"Actual grade: {actual or 'missing'}",
            )
            if not grade_ok:
                issues.append(
                    EligibilityIssue(
                        rule_id=f"o_level:{subject}",
                        message=f"O-Level {subject} needs at least {minimum_grade}.",
                    )
                )
            else:
                matched_rules.append(f"o_level:{subject}")

        for condition in requirement.conditional_requirements:
            # Conditional rules only apply when the exception conditions are not met.
            condition_applies = not self._any_principal_subjects(student, condition.unless_any_principal) and not self._any_subjects(student, condition.unless_any_subjects)
            if condition_applies:
                for subject, minimum_grade in condition.require_a_level_subject_grades.items():
                    actual = a_level_map.get(subject)
                    grade_ok = actual is not None and grade_at_least(actual, minimum_grade, student.a_level_scheme)
                    add_trace(
                        f"conditional_a_level:{subject}",
                        f"Conditional A-Level: {subject}",
                        grade_ok,
                        condition.message or f"Requires {subject} at least {minimum_grade}.",
                        6.0,
                        details=f"Actual grade: {actual or 'missing'}",
                    )
                    if not grade_ok:
                        issues.append(
                            EligibilityIssue(
                                rule_id=f"conditional_a_level:{subject}",
                                message=condition.message or f"Requires {subject} at least {minimum_grade}.",
                            )
                        )
                    else:
                        matched_rules.append(f"conditional_a_level:{subject}")

                for subject, minimum_grade in condition.require_o_level_subject_grades.items():
                    actual = o_level_map.get(subject)
                    grade_ok = actual is not None and grade_at_least(actual, minimum_grade)
                    add_trace(
                        f"conditional_o_level:{subject}",
                        f"Conditional O-Level: {subject}",
                        grade_ok,
                        condition.message or f"Requires O-Level {subject} at least {minimum_grade}.",
                        6.0,
                        details=f"Actual grade: {actual or 'missing'}",
                    )
                    if not grade_ok:
                        issues.append(
                            EligibilityIssue(
                                rule_id=f"conditional_o_level:{subject}",
                                message=condition.message or f"Requires O-Level {subject} at least {minimum_grade}.",
                            )
                        )
                    else:
                        matched_rules.append(f"conditional_o_level:{subject}")

        if programme.capacity is not None and programme.capacity <= 50:
            warnings.append("Programme has limited capacity and may be highly competitive.")

        if programme.competition_tier >= 4:
            warnings.append("This is a highly competitive programme.")

        eligible = not issues
        section = self._section_for(programme)
        if college_route:
            o_summary = get_o_level_summary(student)
            min_o = requirement.minimum_o_level_passes or 0
            if min_o:
                points_margin = float(o_summary.pass_count - min_o)
            else:
                points_margin = max(0.0, float(o_summary.pass_count - 4))
            why_recommended = [
                f"CSEE route: {o_summary.pass_count} O-Level pass(es); margin versus this programme's minimum is about {round(points_margin, 2)}.",
                f"Matched {len(matched_rules)} rule(s) successfully.",
            ]
        else:
            points_margin = summary.total_points - requirement.minimum_total_points
            why_recommended = [
                f"Meets minimum admission points with a margin of {round(points_margin, 2)}.",
                f"Matched {len(matched_rules)} rule(s) successfully.",
            ]
        if warnings:
            why_recommended.extend(warnings)
        why_borderline = []
        if eligible and (points_margin <= 1.0 or programme.competition_tier >= 4):
            why_borderline.append("This is a borderline match because the programme is competitive or the points margin is small.")
        if not eligible and issues:
            why_borderline.append("This profile is close, but one or more blocking rules failed.")
        why_not_matched = [issue.message for issue in issues[:5]] if issues else []
        # The assessment object keeps both the pass/fail result and the explanations.
        return ProgrammeAssessment(
            eligible=eligible,
            score=0.0,
            confidence=0.0,
            confidence_band=ConfidenceBand.VERY_LOW,
            rule_points=round(rule_points, 2),
            matched_rules=matched_rules,
            missing_rules=[issue.message for issue in issues],
            warnings=warnings,
            issues=issues,
            rule_traces=rule_traces,
            why_recommended=why_recommended,
            why_borderline=why_borderline,
            why_not_matched=why_not_matched,
            section=section,
            points_margin=points_margin,
        )

    def _count_pool_matches(self, student: StudentResult, pool: Iterable[str], college_route: bool) -> int:
        # Count A-Level principals or (for college routes) O-Level passes inside the approved pool.
        pool_set = {normalize_subject_name(item).lower() for item in pool}
        if college_route:
            count = 0
            for subject in student.o_level_subjects:
                if not grade_at_least(subject.grade, "D"):
                    continue
                if normalize_subject_name(subject.subject).lower() in pool_set:
                    count += 1
            return count
        count = 0
        for subject in student.a_level_subjects:
            if normalize_subject_name(subject.subject).lower() in pool_set and subject.principal:
                count += 1
        return count

    def _any_principal_subjects(self, student: StudentResult, subjects: Iterable[str]) -> bool:
        # True if any principal subject matches the provided list.
        subject_set = {normalize_subject_name(item).lower() for item in subjects}
        for subject in student.a_level_subjects:
            if subject.principal and normalize_subject_name(subject.subject).lower() in subject_set:
                return True
        return False

    def _any_subjects(self, student: StudentResult, subjects: Iterable[str]) -> bool:
        # True if the student has the subject anywhere, A-Level or O-Level.
        subject_set = {normalize_subject_name(item).lower() for item in subjects}
        for subject in student.a_level_subjects + student.o_level_subjects:
            if normalize_subject_name(subject.subject).lower() in subject_set:
                return True
        return False

    def _has_any_subjects(self, student: StudentResult, subjects: Iterable[str]) -> bool:
        # Backwards-compatible alias for the mixed-level subject check.
        return self._any_subjects(student, subjects)

    def _has_any_principal_subjects(self, student: StudentResult, subjects: Iterable[str]) -> bool:
        # Same as _any_principal_subjects, but kept as a clearer named helper.
        subject_set = {normalize_subject_name(item).lower() for item in subjects}
        for subject in student.a_level_subjects:
            if subject.principal and normalize_subject_name(subject.subject).lower() in subject_set:
                return True
        return False

    def _has_all_principal_subjects(self, student: StudentResult, subjects: Iterable[str]) -> bool:
        required = {normalize_subject_name(item).lower() for item in subjects}
        found = {
            normalize_subject_name(subject.subject).lower()
            for subject in student.a_level_subjects
            if subject.principal
        }
        return required.issubset(found)

    def _section_for(self, programme: Programme) -> str:
        name = programme.name.lower()
        tags = {tag.lower() for tag in programme.tags}
        if programme.category in {ProgrammeCategory.BUSINESS, ProgrammeCategory.ACCOUNTING_FINANCE} and (
            "economics" in name
            or "finance" in name
            or "banking" in name
            or {"economics", "finance", "banking"} & tags
        ):
            return "Economics & Finance"
        return {
            "health": "Health Sciences",
            "engineering": "Engineering & Tech",
            "education": "Education",
            "business": "Business",
            "accounting_finance": "Business",
            "agriculture": "Agriculture",
            "law": "Law",
            "science": "Science",
            "tech": "Engineering & Tech",
            "computing": "Engineering & Tech",
            "arts": "Arts & Humanities",
        }.get(programme.category.value, "General")


def evaluate_programme(student: StudentResult, programme: Programme) -> ProgrammeAssessment:
    return TCURuleEngine().evaluate(student, programme)
