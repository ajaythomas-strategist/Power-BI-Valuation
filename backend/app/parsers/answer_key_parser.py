"""
Parser for Question Papers and Answer Keys into structured EvaluationRuleSet.
Supports JSON, YAML, CSV, and structured Text.
"""
import json
import re
import csv
import io
from typing import Dict, Any, List, Optional
import yaml

from app.models.schemas import (
    EvaluationRuleSet,
    EvaluationRule,
    CriterionRule,
    TargetComponent,
)


class AnswerKeyParser:
    """Parses Answer Key files and formats them into an EvaluationRuleSet."""

    @staticmethod
    def parse_content(content: str, filename: str = "") -> EvaluationRuleSet:
        """Determines format by filename or content and parses into EvaluationRuleSet."""
        ext = filename.lower().split(".")[-1] if "." in filename else ""
        content_stripped = content.strip()

        # 1. JSON
        if ext == "json" or content_stripped.startswith("{") or content_stripped.startswith("["):
            try:
                data = json.loads(content_stripped)
                return AnswerKeyParser._from_dict_or_list(data)
            except Exception:
                pass

        # 2. YAML
        if ext in ["yaml", "yml"] or ("questions:" in content_stripped or "total_marks:" in content_stripped):
            try:
                data = yaml.safe_load(content_stripped)
                if isinstance(data, (dict, list)):
                    return AnswerKeyParser._from_dict_or_list(data)
            except Exception:
                pass

        # 3. CSV
        if ext == "csv" or ("," in content_stripped and "\n" in content_stripped):
            try:
                return AnswerKeyParser._from_csv(content_stripped)
            except Exception:
                pass

        # 4. Fallback: Parse structured text / markdown
        return AnswerKeyParser._from_text(content_stripped)

    @staticmethod
    def _from_dict_or_list(data: Any) -> EvaluationRuleSet:
        if isinstance(data, list):
            questions = [AnswerKeyParser._parse_question_dict(q, idx + 1) for idx, q in enumerate(data)]
            total_marks = sum(q.marks for q in questions)
            return EvaluationRuleSet(title="Answer Key Rules", total_marks=total_marks, questions=questions)
        elif isinstance(data, dict):
            raw_questions = data.get("questions", [])
            title = data.get("title", "Answer Key Rules")
            description = data.get("description", "")
            questions = [AnswerKeyParser._parse_question_dict(q, idx + 1) for idx, q in enumerate(raw_questions)]
            total_marks = data.get("total_marks", sum(q.marks for q in questions))
            return EvaluationRuleSet(
                title=title,
                description=description,
                total_marks=float(total_marks),
                questions=questions,
            )
        return EvaluationRuleSet()

    @staticmethod
    def _parse_question_dict(q_data: Dict[str, Any], default_idx: int) -> EvaluationRule:
        q_id = str(q_data.get("question_id") or q_data.get("id") or f"Q{default_idx}")
        q_text = q_data.get("question_text") or q_data.get("question") or q_data.get("title", f"Question {default_idx}")
        marks = float(q_data.get("marks", 10.0))
        accepted_variations = q_data.get("accepted_variations", [])
        if isinstance(accepted_variations, str):
            accepted_variations = [accepted_variations]

        criteria: List[CriterionRule] = []

        # If explicit criteria provided in JSON
        if "criteria" in q_data and isinstance(q_data["criteria"], list):
            for c_idx, c in enumerate(q_data["criteria"]):
                comp = TargetComponent.VISUAL
                comp_str = c.get("component", "Visual").upper().replace(" ", "_")
                if "DAX" in comp_str or "MEASURE" in comp_str:
                    comp = TargetComponent.DAX
                elif "MODEL" in comp_str or "TABLE" in comp_str:
                    comp = TargetComponent.SEMANTIC_MODEL
                elif "RELATIONSHIP" in comp_str:
                    comp = TargetComponent.RELATIONSHIP
                elif "FILTER" in comp_str or "SLICER" in comp_str:
                    comp = TargetComponent.FILTER_SLICER

                crit_variations = c.get("accepted_variations", [])
                if isinstance(crit_variations, str):
                    crit_variations = [crit_variations]

                criteria.append(CriterionRule(
                    id=c.get("id", f"C{c_idx+1}"),
                    title=c.get("title", f"Criterion {c_idx+1}"),
                    component=comp,
                    target_property=c.get("target_property", "visual_type"),
                    expected_value=c.get("expected_value", ""),
                    accepted_variations=crit_variations,
                    marks=float(c.get("marks", 0.0)),
                    is_optional=c.get("is_optional", False),
                ))
        else:
            # Auto-build criteria from high-level fields if provided
            criteria = AnswerKeyParser._build_auto_criteria(q_data, marks, accepted_variations)

        # If criteria marks don't sum to question marks, adjust last or scale
        crit_sum = sum(c.marks for c in criteria)
        if crit_sum == 0 and criteria:
            even_mark = round(marks / len(criteria), 2)
            for c in criteria:
                c.marks = even_mark

        return EvaluationRule(
            question_id=q_id,
            question_text=q_text,
            marks=marks,
            criteria=criteria,
            accepted_variations=accepted_variations,
            notes=q_data.get("notes"),
        )

    @staticmethod
    def _build_auto_criteria(q_data: Dict[str, Any], total_marks: float, q_variations: List[str]) -> List[CriterionRule]:
        criteria = []
        c_counter = 1

        # 1. Visual Type
        if "visual_type" in q_data:
            criteria.append(CriterionRule(
                id=f"C{c_counter}",
                title="Visual Type",
                component=TargetComponent.VISUAL,
                target_property="visual_type",
                expected_value=q_data["visual_type"],
                accepted_variations=q_data.get("visual_type_variations", []),
                marks=round(total_marks * 0.3, 1),
            ))
            c_counter += 1

        # 2. X Axis / Category
        if "x_axis" in q_data or "category" in q_data:
            expected_x = q_data.get("x_axis") or q_data.get("category")
            # Collect variations for x axis
            x_vars = [v for v in q_variations if "date" in v.lower() or "hierarchy" in v.lower()]
            criteria.append(CriterionRule(
                id=f"C{c_counter}",
                title="X-Axis Field",
                component=TargetComponent.VISUAL,
                target_property="x_axis",
                expected_value=expected_x,
                accepted_variations=x_vars,
                marks=round(total_marks * 0.3, 1),
            ))
            c_counter += 1

        # 3. Y Axis / Values
        if "y_axis" in q_data or "values" in q_data or "value" in q_data:
            expected_y = q_data.get("y_axis") or q_data.get("values") or q_data.get("value")
            criteria.append(CriterionRule(
                id=f"C{c_counter}",
                title="Y-Axis / Value Field",
                component=TargetComponent.VISUAL,
                target_property="y_axis",
                expected_value=expected_y,
                accepted_variations=q_data.get("value_variations", []),
                marks=round(total_marks * 0.3, 1),
            ))
            c_counter += 1

        # 4. DAX Measure
        if "measure_name" in q_data or "dax" in q_data or "dax_formula" in q_data:
            m_name = q_data.get("measure_name", "Calculated Measure")
            dax_expr = q_data.get("dax") or q_data.get("dax_formula", "")
            criteria.append(CriterionRule(
                id=f"C{c_counter}",
                title=f"DAX Measure: {m_name}",
                component=TargetComponent.DAX,
                target_property="dax_formula",
                expected_value=dax_expr,
                accepted_variations=q_data.get("dax_variations", q_variations),
                marks=round(total_marks * 0.5, 1) if criteria else round(total_marks * 0.7, 1),
            ))
            c_counter += 1

        # 5. Relationship
        if "relationship" in q_data:
            rel = q_data["relationship"]
            criteria.append(CriterionRule(
                id=f"C{c_counter}",
                title="Model Relationship",
                component=TargetComponent.RELATIONSHIP,
                target_property="relationship",
                expected_value=rel,
                marks=total_marks if not criteria else round(total_marks * 0.5, 1),
            ))
            c_counter += 1

        # If nothing specific was found, add generic question fulfillment criterion
        if not criteria:
            criteria.append(CriterionRule(
                id=f"C{c_counter}",
                title="Requirement Fulfilled",
                component=TargetComponent.VISUAL,
                target_property="visual_type",
                expected_value="Any",
                marks=total_marks,
            ))

        return criteria

    @staticmethod
    def _from_csv(csv_text: str) -> EvaluationRuleSet:
        reader = csv.DictReader(io.StringIO(csv_text))
        questions = []
        for idx, row in enumerate(reader):
            q_id = row.get("Question ID") or row.get("question_id") or f"Q{idx+1}"
            q_text = row.get("Question") or row.get("question_text") or f"Question {idx+1}"
            marks = float(row.get("Marks") or row.get("marks") or 10.0)
            vis_type = row.get("Visual Type") or row.get("visual_type")
            x_axis = row.get("X Axis") or row.get("x_axis")
            y_axis = row.get("Y Axis") or row.get("Value") or row.get("values")
            dax = row.get("DAX") or row.get("dax")
            variations = [v.strip() for v in (row.get("Accepted Variations") or "").split(";") if v.strip()]

            q_data = {
                "question_id": q_id,
                "question_text": q_text,
                "marks": marks,
                "accepted_variations": variations,
            }
            if vis_type:
                q_data["visual_type"] = vis_type
            if x_axis:
                q_data["x_axis"] = x_axis
            if y_axis:
                q_data["y_axis"] = y_axis
            if dax:
                q_data["dax"] = dax

            questions.append(AnswerKeyParser._parse_question_dict(q_data, idx + 1))

        return EvaluationRuleSet(
            title="CSV Imported Answer Key",
            total_marks=sum(q.marks for q in questions),
            questions=questions,
        )

    @staticmethod
    def _from_text(text: str) -> EvaluationRuleSet:
        """Parses numbered questions or bullet points from Markdown/Text."""
        blocks = re.split(r"(?:^|\n)(?:Q(?:uestion)?\s*(\d+)[:.]?|(\d+)[\.\)])\s*", text, flags=re.MULTILINE)
        questions = []
        
        # If no numbered pattern found, split by double newlines
        if len(blocks) <= 1:
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            for idx, p in enumerate(paragraphs):
                questions.append(EvaluationRule(
                    question_id=f"Q{idx+1}",
                    question_text=p[:120] + ("..." if len(p) > 120 else ""),
                    marks=10.0,
                    criteria=[
                        CriterionRule(
                            id="C1",
                            title="Requirement Verification",
                            component=TargetComponent.VISUAL,
                            target_property="visual_type",
                            expected_value="Line Chart" if "line" in p.lower() else "Table",
                            marks=10.0,
                        )
                    ],
                ))
            return EvaluationRuleSet(title="Text Parsed Rules", total_marks=sum(q.marks for q in questions), questions=questions)

        # Iterate over regex matches
        idx = 1
        for i in range(1, len(blocks), 3):
            q_num = blocks[i] or blocks[i+1] or str(idx)
            q_body = blocks[i+2].strip() if i+2 < len(blocks) else ""
            if not q_body:
                continue

            marks = 10.0
            marks_match = re.search(r"\(?(\d+(?:\.\d+)?)\s*(?:marks?|pts?|points?)\)?", q_body, re.IGNORECASE)
            if marks_match:
                marks = float(marks_match.group(1))

            variations = []
            if "variation" in q_body.lower() or "ok" in q_body.lower() or "accepted" in q_body.lower():
                var_match = re.search(r"\(([^)]*(?:ok|accepted|variation)[^)]*)\)", q_body, re.IGNORECASE)
                if var_match:
                    variations.append(var_match.group(1))

            # Detect visual type
            vis_type = None
            if "line chart" in q_body.lower():
                vis_type = "Line Chart"
            elif "bar chart" in q_body.lower():
                vis_type = "Bar Chart"
            elif "column chart" in q_body.lower():
                vis_type = "Column Chart"
            elif "pie chart" in q_body.lower():
                vis_type = "Pie Chart"
            elif "matrix" in q_body.lower():
                vis_type = "Matrix"
            elif "card" in q_body.lower():
                vis_type = "Card"

            q_data = {
                "question_id": f"Q{q_num}",
                "question_text": q_body.split("\n")[0].strip(),
                "marks": marks,
                "accepted_variations": variations,
            }
            if vis_type:
                q_data["visual_type"] = vis_type

            questions.append(AnswerKeyParser._parse_question_dict(q_data, idx))
            idx += 1

        return EvaluationRuleSet(
            title="Imported Answer Key",
            total_marks=sum(q.marks for q in questions),
            questions=questions,
        )
