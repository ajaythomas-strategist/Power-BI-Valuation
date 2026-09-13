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
    PBIPProject,
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

    @staticmethod
    def generate_rules_from_pbip(
        pbip_project: PBIPProject,
        total_marks: float = 100.0,
        title: Optional[str] = None,
    ) -> EvaluationRuleSet:
        """
        Synthesizes a complete machine-evaluable EvaluationRuleSet from a Master/Solution PBIP project.
        Extracts:
        - Data Model tables and calculated columns
        - Relationships and foreign key linkages
        - DAX measures and exact formulas
        - Visuals across pages with types, axes, legends, values, and filters
        """
        questions: List[EvaluationRule] = []
        all_criteria: List[CriterionRule] = []
        crit_counter = 1

        # 1. Model Schema & Tables
        if pbip_project.semantic_model and pbip_project.semantic_model.tables:
            schema_criteria: List[CriterionRule] = []
            for tbl in pbip_project.semantic_model.tables:
                # Table existence check
                schema_criteria.append(CriterionRule(
                    id=f"C{crit_counter}",
                    title=f"Table '{tbl.name}' exists in Semantic Model",
                    component=TargetComponent.SEMANTIC_MODEL,
                    target_property="table",
                    expected_value=tbl.name,
                    marks=5.0,
                ))
                crit_counter += 1

                # Calculated columns
                for col in tbl.columns:
                    if col.is_calculated:
                        schema_criteria.append(CriterionRule(
                            id=f"C{crit_counter}",
                            title=f"Calculated Column '{tbl.name}[{col.name}]'",
                            component=TargetComponent.CALCULATED_COLUMN,
                            target_property="column",
                            expected_value=col.name,
                            marks=5.0,
                        ))
                        crit_counter += 1

            if schema_criteria:
                questions.append(EvaluationRule(
                    question_id=f"Q{len(questions)+1}",
                    question_text="Data Model Structure & Schema",
                    marks=sum(c.marks for c in schema_criteria),
                    criteria=schema_criteria,
                    notes="Tables and calculated columns imported from Master Solution Model.",
                ))
                all_criteria.extend(schema_criteria)

        # 2. Model Relationships
        if pbip_project.semantic_model and pbip_project.semantic_model.relationships:
            rel_criteria: List[CriterionRule] = []
            for rel in pbip_project.semantic_model.relationships:
                rel_str = f"{rel.from_table}[{rel.from_column}] -> {rel.to_table}[{rel.to_column}]"
                rel_criteria.append(CriterionRule(
                    id=f"C{crit_counter}",
                    title=f"Relationship: {rel_str}",
                    component=TargetComponent.RELATIONSHIP,
                    target_property="relationship",
                    expected_value=rel_str,
                    marks=5.0,
                ))
                crit_counter += 1

            if rel_criteria:
                questions.append(EvaluationRule(
                    question_id=f"Q{len(questions)+1}",
                    question_text="Data Model Relationships",
                    marks=sum(c.marks for c in rel_criteria),
                    criteria=rel_criteria,
                    notes="Entity relationships and cardinality from Master Solution Model.",
                ))
                all_criteria.extend(rel_criteria)

        # 3. DAX Measures
        if pbip_project.semantic_model:
            dax_measures = pbip_project.semantic_model.all_measures()
            if dax_measures:
                dax_criteria: List[CriterionRule] = []
                for m in dax_measures:
                    dax_criteria.append(CriterionRule(
                        id=f"C{crit_counter}",
                        title=f"DAX Measure: [{m.name}]",
                        component=TargetComponent.DAX,
                        target_property="dax_formula",
                        expected_value=m.expression,
                        accepted_variations=[f"Alternative formulation for {m.name}"],
                        marks=10.0,
                    ))
                    crit_counter += 1

                questions.append(EvaluationRule(
                    question_id=f"Q{len(questions)+1}",
                    question_text="DAX Measures & Calculations",
                    marks=sum(c.marks for c in dax_criteria),
                    criteria=dax_criteria,
                    notes="Measures and business formulas from Master Solution Model.",
                ))
                all_criteria.extend(dax_criteria)

        # 4. Report Visuals by Page
        if pbip_project.report and pbip_project.report.pages:
            vis_index = 1
            for page in pbip_project.report.pages:
                page_name = page.display_name or page.name
                for vis in page.visuals:
                    # Ignore pure textbox/shape decorators with no visual type or fields
                    if not vis.visual_type or (not vis.x_axis_fields and not vis.y_axis_fields and not vis.values_fields and not vis.legend_fields):
                        continue

                    vis_criteria: List[CriterionRule] = []
                    
                    # 1. Visual Type
                    vis_title = vis.title or vis.visual_type
                    vis_criteria.append(CriterionRule(
                        id=f"C{crit_counter}",
                        title=f"Visual Type is {vis.visual_type}",
                        component=TargetComponent.VISUAL,
                        target_property="visual_type",
                        expected_value=vis.visual_type,
                        accepted_variations=[],
                        marks=5.0,
                    ))
                    crit_counter += 1

                    # 2. X-Axis
                    if vis.x_axis_fields:
                        x_field = vis.x_axis_fields[0]
                        vis_criteria.append(CriterionRule(
                            id=f"C{crit_counter}",
                            title=f"X-Axis field ({x_field})",
                            component=TargetComponent.VISUAL,
                            target_property="x_axis",
                            expected_value=x_field,
                            marks=3.0,
                        ))
                        crit_counter += 1

                    # 3. Y-Axis
                    if vis.y_axis_fields:
                        y_field = vis.y_axis_fields[0]
                        vis_criteria.append(CriterionRule(
                            id=f"C{crit_counter}",
                            title=f"Y-Axis field ({y_field})",
                            component=TargetComponent.VISUAL,
                            target_property="y_axis",
                            expected_value=y_field,
                            marks=3.0,
                        ))
                        crit_counter += 1

                    # 4. Legend
                    if vis.legend_fields:
                        leg_field = vis.legend_fields[0]
                        vis_criteria.append(CriterionRule(
                            id=f"C{crit_counter}",
                            title=f"Legend field ({leg_field})",
                            component=TargetComponent.VISUAL,
                            target_property="legend",
                            expected_value=leg_field,
                            marks=2.0,
                        ))
                        crit_counter += 1

                    # 5. Values
                    if vis.values_fields and not vis.y_axis_fields:
                        val_field = vis.values_fields[0]
                        vis_criteria.append(CriterionRule(
                            id=f"C{crit_counter}",
                            title=f"Values field ({val_field})",
                            component=TargetComponent.VISUAL,
                            target_property="values",
                            expected_value=val_field,
                            marks=3.0,
                        ))
                        crit_counter += 1

                    # 6. Slicers / Filters
                    if vis.slicer_fields:
                        vis_criteria.append(CriterionRule(
                            id=f"C{crit_counter}",
                            title=f"Slicer configured on {', '.join(vis.slicer_fields)}",
                            component=TargetComponent.FILTER_SLICER,
                            target_property="slicer",
                            expected_value=vis.slicer_fields[0],
                            marks=2.0,
                        ))
                        crit_counter += 1

                    if vis_criteria:
                        q_id = f"Q{len(questions)+1}"
                        questions.append(EvaluationRule(
                            question_id=q_id,
                            question_text=f"Visual: {vis_title} on page '{page_name}'",
                            marks=sum(c.marks for c in vis_criteria),
                            criteria=vis_criteria,
                            notes=f"Visual #{vis_index} extracted from {page_name}.",
                        ))
                        all_criteria.extend(vis_criteria)
                        vis_index += 1

        # Fallback if no questions were extracted
        if not questions:
            questions.append(EvaluationRule(
                question_id="Q1",
                question_text="Power BI Project Evaluation",
                marks=total_marks,
                criteria=[CriterionRule(
                    id="C1",
                    title="Power BI Project Valid Structure",
                    component=TargetComponent.VISUAL,
                    target_property="visual_type",
                    expected_value="Report",
                    marks=total_marks,
                )],
            ))
            all_criteria = questions[0].criteria

        # Distribute / scale total marks to match requested total_marks (e.g. 100.0)
        current_sum = sum(c.marks for c in all_criteria)
        if current_sum > 0 and abs(current_sum - total_marks) > 0.01:
            ratio = total_marks / current_sum
            for c in all_criteria:
                c.marks = round(c.marks * ratio, 1)
            # Rebalance questions marks
            for q in questions:
                q.marks = round(sum(c.marks for c in q.criteria), 1)

        set_title = title or f"Master Key: {pbip_project.project_name or 'Power BI Project'}"
        return EvaluationRuleSet(
            title=set_title,
            description="Auto-synthesized evaluation rules from Master Solution PBIP project.",
            total_marks=round(sum(q.marks for q in questions), 1),
            questions=questions,
        )

