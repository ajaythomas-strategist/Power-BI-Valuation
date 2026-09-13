"""
Modular deterministic evaluation engine for Power BI student projects.
Evaluates PBIPProject data against EvaluationRuleSet criteria.
"""
import re
from typing import Dict, Any, List, Optional, Tuple

from app.models.schemas import (
    PBIPProject,
    PBIPVisual,
    PBIPMeasure,
    PBIPTable,
    PBIPRelationship,
    EvaluationRuleSet,
    EvaluationRule,
    CriterionRule,
    TargetComponent,
    StudentEvaluationResult,
    QuestionEvaluationDetail,
    CriterionEvaluationResult,
    EvaluationStatus,
    EvaluationException,
    ExceptionType,
)
from app.parsers.dax_analyzer import DAXAnalyzer


class EvaluationEngine:
    """Evaluates a student's parsed PBIP project against an EvaluationRuleSet."""

    def __init__(self, rule_set: EvaluationRuleSet):
        self.rule_set = rule_set

    def evaluate_student(self, project: PBIPProject) -> StudentEvaluationResult:
        """Evaluates a single student project."""
        # Check if project itself is invalid or has fatal parsing errors
        if not project.is_valid:
            exc = EvaluationException(
                register_no=project.register_no,
                issue_type=ExceptionType.CORRUPTED_PROJECT,
                description=project.error_message or "Unable to parse student PBIP project.",
                details="No valid Report or Semantic Model definitions found.",
            )
            return StudentEvaluationResult(
                register_no=project.register_no,
                total_marks=0.0,
                maximum_marks=self.rule_set.total_marks,
                percentage=0.0,
                questions_evaluated=0,
                questions_correct=0,
                questions_partially_correct=0,
                questions_incorrect=len(self.rule_set.questions),
                status=EvaluationStatus.EXCEPTION,
                question_details=[],
                exception=exc,
            )

        question_results: List[QuestionEvaluationDetail] = []
        total_awarded = 0.0
        q_correct = 0
        q_partial = 0
        q_incorrect = 0

        for rule in self.rule_set.questions:
            q_detail = self._evaluate_question(rule, project)
            question_results.append(q_detail)
            total_awarded += q_detail.marks_awarded

            if q_detail.status == EvaluationStatus.CORRECT:
                q_correct += 1
            elif q_detail.status == EvaluationStatus.PARTIAL:
                q_partial += 1
            else:
                q_incorrect += 1

        total_awarded = round(total_awarded, 2)
        max_marks = self.rule_set.total_marks if self.rule_set.total_marks > 0 else 100.0
        percentage = round((total_awarded / max_marks) * 100, 2) if max_marks > 0 else 0.0

        if q_correct == len(self.rule_set.questions):
            overall_status = EvaluationStatus.CORRECT
        elif total_awarded > 0:
            overall_status = EvaluationStatus.PARTIAL
        else:
            overall_status = EvaluationStatus.INCORRECT

        return StudentEvaluationResult(
            register_no=project.register_no,
            total_marks=total_awarded,
            maximum_marks=max_marks,
            percentage=percentage,
            questions_evaluated=len(self.rule_set.questions),
            questions_correct=q_correct,
            questions_partially_correct=q_partial,
            questions_incorrect=q_incorrect,
            status=overall_status,
            question_details=question_results,
            exception=None,
        )

    def _evaluate_question(self, rule: EvaluationRule, project: PBIPProject) -> QuestionEvaluationDetail:
        """Evaluates all criteria for a specific question."""
        criterion_results: List[CriterionEvaluationResult] = []
        awarded_marks = 0.0

        # Check if question primarily targets a Visual or DAX/Model
        has_visual_criteria = any(c.component in (TargetComponent.VISUAL, TargetComponent.FILTER_SLICER) for c in rule.criteria)
        
        # Best candidate visual if visual criteria are involved
        candidate_visual = None
        if has_visual_criteria and project.report:
            candidate_visual = self._find_best_matching_visual(rule, project.report.pages)

        for c in rule.criteria:
            c_res = self._evaluate_criterion(c, rule, project, candidate_visual)
            criterion_results.append(c_res)
            awarded_marks += c_res.marks_awarded

        awarded_marks = round(min(awarded_marks, rule.marks), 2)

        # Determine Question Status
        all_met = all(cr.is_met for cr in criterion_results)
        any_met = any(cr.is_met or cr.marks_awarded > 0 for cr in criterion_results)

        if all_met and awarded_marks == rule.marks:
            status = EvaluationStatus.CORRECT
        elif any_met and awarded_marks > 0:
            status = EvaluationStatus.PARTIAL
        else:
            status = EvaluationStatus.INCORRECT

        # Build summaries and remarks
        req_summary = "; ".join([f"{c.title} ({c.expected_value})" for c in rule.criteria])
        exp_summary = "; ".join([f"{c.title}: {c.expected_value}" for c in rule.criteria])
        std_summary = "; ".join([f"{cr.title}: {cr.student_value or 'Not Found'}" for cr in criterion_results])
        
        # Combine remarks
        remarks_list = [cr.remarks for cr in criterion_results if cr.remarks]
        remarks = " | ".join(remarks_list) if remarks_list else ("All criteria met." if status == EvaluationStatus.CORRECT else "Requirements not satisfied.")

        return QuestionEvaluationDetail(
            question_id=rule.question_id,
            question_text=rule.question_text,
            status=status,
            marks_awarded=awarded_marks,
            maximum_marks=rule.marks,
            requirement_summary=req_summary,
            expected_summary=exp_summary,
            student_summary=std_summary,
            criteria_results=criterion_results,
            remarks=remarks,
        )

    def _evaluate_criterion(
        self,
        c: CriterionRule,
        rule: EvaluationRule,
        project: PBIPProject,
        candidate_visual: Optional[PBIPVisual],
    ) -> CriterionEvaluationResult:
        """Evaluates a single criterion rule."""
        target_prop = c.target_property.lower()
        expected = str(c.expected_value).strip()
        variations = list(c.accepted_variations) + list(rule.accepted_variations)

        # -------------------------------------------------------------
        # 1. VISUAL EVALUATION
        # -------------------------------------------------------------
        if c.component in (TargetComponent.VISUAL, TargetComponent.FILTER_SLICER):
            if not project.report or not project.report.pages:
                return CriterionEvaluationResult(
                    criterion_id=c.id,
                    title=c.title,
                    marks_awarded=0.0,
                    maximum_marks=c.marks,
                    is_met=False,
                    student_value="No Report Pages Found",
                    expected_value=expected,
                    remarks="Student report has no visual pages.",
                )

            if not candidate_visual:
                return CriterionEvaluationResult(
                    criterion_id=c.id,
                    title=c.title,
                    marks_awarded=0.0,
                    maximum_marks=c.marks,
                    is_met=False,
                    student_value="Visual Not Found",
                    expected_value=expected,
                    remarks=f"No matching visual found for requirement: {c.title}.",
                )

            # Check Visual Type
            if "visual_type" in target_prop or "type" in target_prop:
                std_val = candidate_visual.visual_type
                is_match, reason = self._match_text_or_variations(std_val, expected, variations)
                return CriterionEvaluationResult(
                    criterion_id=c.id,
                    title=c.title,
                    marks_awarded=c.marks if is_match else 0.0,
                    maximum_marks=c.marks,
                    is_met=is_match,
                    student_value=std_val,
                    expected_value=expected,
                    remarks=f"Visual type '{std_val}' matches expected '{expected}'." if is_match else f"Visual type '{std_val}' does not match '{expected}'. {reason}",
                )

            # Check Y-Axis / Values / Measure first
            if any(k in target_prop for k in ["y_axis", "yaxis", "y-axis", "value", "values", "measure"]):
                std_fields = candidate_visual.y_axis_fields or candidate_visual.values_fields or candidate_visual.all_referenced_fields
                is_match, matched_field, reason = self._match_fields_list(std_fields, expected, variations)
                return CriterionEvaluationResult(
                    criterion_id=c.id,
                    title=c.title,
                    marks_awarded=c.marks if is_match else 0.0,
                    maximum_marks=c.marks,
                    is_met=is_match,
                    student_value=", ".join(std_fields) if std_fields else "None",
                    expected_value=expected,
                    remarks=f"Found Y-axis/value field '{matched_field}'." if is_match else f"Missing expected Y-axis/value '{expected}'. Found: {', '.join(std_fields) or 'None'}.",
                )

            # Check X-Axis / Category
            if any(k in target_prop for k in ["x_axis", "xaxis", "x-axis", "category", "axis", "group"]):
                std_fields = candidate_visual.x_axis_fields or candidate_visual.all_referenced_fields
                is_match, matched_field, reason = self._match_fields_list(std_fields, expected, variations)
                return CriterionEvaluationResult(
                    criterion_id=c.id,
                    title=c.title,
                    marks_awarded=c.marks if is_match else 0.0,
                    maximum_marks=c.marks,
                    is_met=is_match,
                    student_value=", ".join(std_fields) if std_fields else "None",
                    expected_value=expected,
                    remarks=f"Found X-axis field '{matched_field}'." if is_match else f"Missing expected X-axis field '{expected}'. Found: {', '.join(std_fields) or 'None'}.",
                )

            # Check Legend / Series
            if any(k in target_prop for k in ["legend", "series"]):
                std_fields = candidate_visual.legend_fields
                is_match, matched_field, reason = self._match_fields_list(std_fields, expected, variations)
                return CriterionEvaluationResult(
                    criterion_id=c.id,
                    title=c.title,
                    marks_awarded=c.marks if is_match else 0.0,
                    maximum_marks=c.marks,
                    is_met=is_match,
                    student_value=", ".join(std_fields) if std_fields else "None",
                    expected_value=expected,
                    remarks=f"Found legend field '{matched_field}'." if is_match else f"Missing expected legend '{expected}'.",
                )

            # Check Slicer field
            if "slicer" in target_prop:
                std_fields = candidate_visual.slicer_fields or candidate_visual.all_referenced_fields
                is_match, matched_field, reason = self._match_fields_list(std_fields, expected, variations)
                return CriterionEvaluationResult(
                    criterion_id=c.id,
                    title=c.title,
                    marks_awarded=c.marks if is_match else 0.0,
                    maximum_marks=c.marks,
                    is_met=is_match,
                    student_value=", ".join(std_fields) if std_fields else "None",
                    expected_value=expected,
                    remarks=f"Found slicer field '{matched_field}'." if is_match else f"Missing expected slicer '{expected}'.",
                )

        # -------------------------------------------------------------
        # 2. DAX MEASURE EVALUATION
        # -------------------------------------------------------------
        elif c.component == TargetComponent.DAX:
            if not project.semantic_model or not project.semantic_model.measures:
                return CriterionEvaluationResult(
                    criterion_id=c.id,
                    title=c.title,
                    marks_awarded=0.0,
                    maximum_marks=c.marks,
                    is_met=False,
                    student_value="No Measures Found",
                    expected_value=expected,
                    remarks="Student semantic model contains no DAX measures.",
                )

            # Find measure by name
            measure_target_name = c.title.replace("DAX Measure:", "").replace("DAX:", "").strip()
            student_measure = self._find_measure(project.semantic_model.measures, measure_target_name, variations)

            if not student_measure:
                # Also try checking if any measure has matching DAX
                for m in project.semantic_model.measures:
                    is_eq, _ = DAXAnalyzer.is_equivalent(m.expression, expected, variations)
                    if is_eq:
                        student_measure = m
                        break

            if not student_measure:
                all_meas = [m.name for m in project.semantic_model.measures]
                return CriterionEvaluationResult(
                    criterion_id=c.id,
                    title=c.title,
                    marks_awarded=0.0,
                    maximum_marks=c.marks,
                    is_met=False,
                    student_value=f"Available measures: {', '.join(all_meas) if all_meas else 'None'}",
                    expected_value=f"{measure_target_name} = {expected}",
                    remarks=f"Measure '{measure_target_name}' was not found in the model.",
                )

            # Check DAX expression equivalence
            is_eq, eq_remarks = DAXAnalyzer.is_equivalent(student_measure.expression, expected, variations)
            return CriterionEvaluationResult(
                criterion_id=c.id,
                title=c.title,
                marks_awarded=c.marks if is_eq else 0.0,
                maximum_marks=c.marks,
                is_met=is_eq,
                student_value=f"{student_measure.name} = {student_measure.expression}",
                expected_value=expected,
                remarks=f"DAX measure '{student_measure.name}' verified: {eq_remarks}",
            )

        # -------------------------------------------------------------
        # 3. SEMANTIC MODEL & CALCULATED COLUMNS EVALUATION
        # -------------------------------------------------------------
        elif c.component in (TargetComponent.SEMANTIC_MODEL, TargetComponent.CALCULATED_COLUMN):
            if not project.semantic_model:
                return CriterionEvaluationResult(
                    criterion_id=c.id,
                    title=c.title,
                    marks_awarded=0.0,
                    maximum_marks=c.marks,
                    is_met=False,
                    student_value="No Semantic Model",
                    expected_value=expected,
                    remarks="Student project is missing semantic model.",
                )

            # Table existence check
            if "table" in target_prop:
                found_table = any(t.name.lower() == expected.lower() for t in project.semantic_model.tables)
                std_tables = [t.name for t in project.semantic_model.tables]
                return CriterionEvaluationResult(
                    criterion_id=c.id,
                    title=c.title,
                    marks_awarded=c.marks if found_table else 0.0,
                    maximum_marks=c.marks,
                    is_met=found_table,
                    student_value=", ".join(std_tables),
                    expected_value=expected,
                    remarks=f"Table '{expected}' found." if found_table else f"Table '{expected}' not found in model.",
                )

            # Calculated Column check
            if "column" in target_prop or c.component == TargetComponent.CALCULATED_COLUMN:
                found_col = None
                for t in project.semantic_model.tables:
                    for col in t.columns:
                        if col.name.lower() == expected.lower() or expected.lower() in col.name.lower():
                            found_col = col
                            break
                    if found_col:
                        break

                if found_col:
                    return CriterionEvaluationResult(
                        criterion_id=c.id,
                        title=c.title,
                        marks_awarded=c.marks,
                        maximum_marks=c.marks,
                        is_met=True,
                        student_value=f"{found_col.name} ({found_col.expression or 'Standard Column'})",
                        expected_value=expected,
                        remarks=f"Column '{found_col.name}' found in model.",
                    )
                else:
                    return CriterionEvaluationResult(
                        criterion_id=c.id,
                        title=c.title,
                        marks_awarded=0.0,
                        maximum_marks=c.marks,
                        is_met=False,
                        student_value="Column Not Found",
                        expected_value=expected,
                        remarks=f"Column '{expected}' was not found in any table.",
                    )

        # -------------------------------------------------------------
        # 4. RELATIONSHIP EVALUATION
        # -------------------------------------------------------------
        elif c.component == TargetComponent.RELATIONSHIP:
            if not project.semantic_model or not project.semantic_model.relationships:
                return CriterionEvaluationResult(
                    criterion_id=c.id,
                    title=c.title,
                    marks_awarded=0.0,
                    maximum_marks=c.marks,
                    is_met=False,
                    student_value="No Relationships Found",
                    expected_value=expected,
                    remarks="Student model has no relationships defined.",
                )

            found_rel = False
            rel_details = ""
            for r in project.semantic_model.relationships:
                rel_str = f"{r.from_table}[{r.from_column}] -> {r.to_table}[{r.to_column}]".lower()
                rev_str = f"{r.to_table}[{r.to_column}] -> {r.from_table}[{r.from_column}]".lower()
                exp_clean = expected.lower().replace("'", "").replace(" ", "")

                if (exp_clean in rel_str.replace(" ", "") or exp_clean in rev_str.replace(" ", "")) or (
                    r.from_table.lower() in exp_clean and r.to_table.lower() in exp_clean
                ):
                    found_rel = True
                    rel_details = f"{r.from_table}[{r.from_column}] -> {r.to_table}[{r.to_column}] ({r.cardinality})"
                    break

            all_rels = [f"{r.from_table}->{r.to_table}" for r in project.semantic_model.relationships]
            return CriterionEvaluationResult(
                criterion_id=c.id,
                title=c.title,
                marks_awarded=c.marks if found_rel else 0.0,
                maximum_marks=c.marks,
                is_met=found_rel,
                student_value=rel_details if found_rel else f"Found: {', '.join(all_rels)}",
                expected_value=expected,
                remarks=f"Relationship verified: {rel_details}" if found_rel else f"Expected relationship '{expected}' not found.",
            )

        # Fallback
        return CriterionEvaluationResult(
            criterion_id=c.id,
            title=c.title,
            marks_awarded=c.marks,
            maximum_marks=c.marks,
            is_met=True,
            student_value="Verified",
            expected_value=expected,
            remarks="Criterion verified.",
        )

    # -------------------------------------------------------------
    # MATCHING HELPERS
    # -------------------------------------------------------------

    def _find_best_matching_visual(self, rule: EvaluationRule, pages: List[Any]) -> Optional[PBIPVisual]:
        """Finds the visual across all pages that scores highest against the question's criteria."""
        all_visuals: List[PBIPVisual] = []
        for p in pages:
            all_visuals.extend(p.visuals)

        if not all_visuals:
            return None

        best_vis = None
        best_score = -1

        for vis in all_visuals:
            score = 0
            # Check visual type
            for c in rule.criteria:
                prop = c.target_property.lower()
                expected = str(c.expected_value)
                variations = list(c.accepted_variations) + list(rule.accepted_variations)

                if "visual_type" in prop:
                    match, _ = self._match_text_or_variations(vis.visual_type, expected, variations)
                    if match:
                        score += 5
                elif any(k in prop for k in ["x_axis", "category"]):
                    match, _, _ = self._match_fields_list(vis.x_axis_fields or vis.all_referenced_fields, expected, variations)
                    if match:
                        score += 3
                elif any(k in prop for k in ["y_axis", "values", "value"]):
                    match, _, _ = self._match_fields_list(vis.y_axis_fields or vis.values_fields or vis.all_referenced_fields, expected, variations)
                    if match:
                        score += 3
                elif "legend" in prop:
                    match, _, _ = self._match_fields_list(vis.legend_fields, expected, variations)
                    if match:
                        score += 2
                elif "slicer" in prop:
                    match, _, _ = self._match_fields_list(vis.slicer_fields, expected, variations)
                    if match:
                        score += 3

            if score > best_score:
                best_score = score
                best_vis = vis

        return best_vis if best_score > 0 else (all_visuals[0] if all_visuals else None)

    def _match_text_or_variations(self, student_text: str, expected: str, variations: List[str]) -> Tuple[bool, str]:
        if not student_text:
            return False, "Empty student value."
        s_clean = self._clean_str(student_text)
        e_clean = self._clean_str(expected)

        if s_clean == e_clean or e_clean in s_clean or s_clean in e_clean:
            return True, "Match found."

        for v in variations:
            v_clean = self._clean_str(v)
            if v_clean and (v_clean == s_clean or v_clean in s_clean or s_clean in v_clean):
                return True, f"Accepted variation '{v}' matched."

        return False, f"Expected '{expected}'"

    def _match_fields_list(self, student_fields: List[str], expected: str, variations: List[str]) -> Tuple[bool, str, str]:
        if not student_fields:
            return False, "", "No fields found in student visual."

        e_clean = self._clean_str(expected)
        # Check direct fields
        for f in student_fields:
            f_clean = self._clean_str(f)
            if f_clean == e_clean or e_clean in f_clean or f_clean in e_clean:
                return True, f, "Direct match."

        # Check variations (e.g. 'Date Hierarchy', 'OrderDate', 'Date', etc.)
        for v in variations:
            v_clean = self._clean_str(v)
            for f in student_fields:
                f_clean = self._clean_str(f)
                if v_clean and (v_clean == f_clean or v_clean in f_clean or f_clean in v_clean):
                    return True, f, f"Accepted variation '{v}' matched."

        # Special semantic aliases
        # If expected is 'Date' or 'Date Hierarchy'
        if "date" in e_clean:
            for f in student_fields:
                if any(d in f.lower() for d in ["date", "year", "month", "quarter", "day", "orderdate"]):
                    return True, f, f"Date dimension field '{f}' accepted."

        return False, "", f"Expected field '{expected}' not present."

    def _find_measure(self, measures: List[PBIPMeasure], target_name: str, variations: List[str]) -> Optional[PBIPMeasure]:
        t_clean = self._clean_str(target_name)
        for m in measures:
            m_clean = self._clean_str(m.name)
            if m_clean == t_clean or t_clean in m_clean or m_clean in t_clean:
                return m

        for v in variations:
            v_clean = self._clean_str(v)
            for m in measures:
                m_clean = self._clean_str(m.name)
                if v_clean and (v_clean == m_clean or v_clean in m_clean):
                    return m
        return None

    def _clean_str(self, s: str) -> str:
        if not s:
            return ""
        return re.sub(r"[^a-zA-Z0-9]", "", s).lower()
