"""
Robust PBIP (Power BI Project) parser.
Supports:
- .pbip project manifests
- Semantic Models (.Dataset / .SemanticModel) in both model.bim and TMDL format
- Reports (.Report) in both legacy report.json and modern PBIR definition formats
"""
import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from app.models.schemas import (
    PBIPProject,
    PBIPReport,
    PBIPPage,
    PBIPVisual,
    PBIPSemanticModel,
    PBIPTable,
    PBIPColumn,
    PBIPMeasure,
    PBIPRelationship,
)


class PBIPParser:
    """Parses extracted Power BI Project (PBIP) folder structures."""

    def __init__(self, project_root_path: str, register_no: str = ""):
        self.root_path = Path(project_root_path)
        self.register_no = register_no

    def parse(self) -> PBIPProject:
        """Finds and parses all components of the PBIP project."""
        project_name = self._find_project_name()

        report = self._parse_report()
        semantic_model = self._parse_semantic_model()

        is_valid = True
        error_message = None

        if not report and not semantic_model:
            is_valid = False
            error_message = "Neither Report nor Semantic Model could be found in the student project directory."

        return PBIPProject(
            project_name=project_name or self.root_path.name,
            register_no=self.register_no,
            report=report,
            semantic_model=semantic_model,
            is_valid=is_valid,
            error_message=error_message,
        )

    def _find_project_name(self) -> str:
        """Looks for .pbip file to extract project name."""
        try:
            for p in self.root_path.glob("*.pbip"):
                return p.stem
            # Check one level deeper if nested
            for p in self.root_path.glob("*/*.pbip"):
                return p.stem
        except Exception:
            pass
        return self.root_path.name

    # -------------------------------------------------------------
    # SEMANTIC MODEL PARSER
    # -------------------------------------------------------------

    def _parse_semantic_model(self) -> Optional[PBIPSemanticModel]:
        """Finds and parses the dataset/semantic model folder or files."""
        model_dirs = []
        for d in self.root_path.rglob("*"):
            if d.is_dir() and (d.name.endswith(".Dataset") or d.name.endswith(".SemanticModel")):
                model_dirs.append(d)

        # Also search for model.bim directly in root or subfolders
        bim_files = list(self.root_path.rglob("model.bim"))
        tmdl_dirs = list(self.root_path.rglob("definition"))

        tables: List[PBIPTable] = []
        measures: List[PBIPMeasure] = []
        relationships: List[PBIPRelationship] = []

        # 1. Try parsing model.bim (Tabular JSON)
        if bim_files:
            try:
                with open(bim_files[0], "r", encoding="utf-8-sig", errors="ignore") as f:
                    bim_data = json.load(f)
                    b_tables, b_measures, b_rels = self._parse_bim_data(bim_data)
                    tables.extend(b_tables)
                    measures.extend(b_measures)
                    relationships.extend(b_rels)
            except Exception as e:
                pass

        # 2. Try parsing TMDL definition files if tables are empty
        if not tables and not measures:
            tmdl_tables, tmdl_measures, tmdl_rels = self._parse_tmdl_definitions()
            tables.extend(tmdl_tables)
            measures.extend(tmdl_measures)
            relationships.extend(tmdl_rels)

        # 3. Check for standalone item.metadata.json or schema files
        if not tables and not measures and not relationships:
            # Check model directory if found
            for mdir in model_dirs:
                m_bim = mdir / "model.bim"
                if m_bim.exists():
                    try:
                        with open(m_bim, "r", encoding="utf-8-sig", errors="ignore") as f:
                            b_tables, b_measures, b_rels = self._parse_bim_data(json.load(f))
                            tables.extend(b_tables)
                            measures.extend(b_measures)
                            relationships.extend(b_rels)
                    except Exception:
                        pass

        if not tables and not measures and not relationships:
            return None

        # Consolidate all measures across tables
        all_measures = list(measures)
        for t in tables:
            for m in t.measures:
                if not any(x.name.lower() == m.name.lower() for x in all_measures):
                    all_measures.append(m)

        return PBIPSemanticModel(
            tables=tables,
            measures=all_measures,
            relationships=relationships,
        )

    def _parse_bim_data(self, bim_data: Dict[str, Any]) -> Tuple[List[PBIPTable], List[PBIPMeasure], List[PBIPRelationship]]:
        tables: List[PBIPTable] = []
        measures: List[PBIPMeasure] = []
        relationships: List[PBIPRelationship] = []

        model = bim_data.get("model", bim_data)

        # Tables & Columns & Measures
        for t_data in model.get("tables", []):
            t_name = t_data.get("name", "UnnamedTable")
            t_columns: List[PBIPColumn] = []
            t_measures: List[PBIPMeasure] = []

            for c in t_data.get("columns", []):
                col = PBIPColumn(
                    name=c.get("name", ""),
                    data_type=c.get("dataType"),
                    is_calculated=(c.get("type") == "calculated"),
                    expression=self._extract_expression(c.get("expression")),
                    is_hidden=c.get("isHidden", False),
                )
                t_columns.append(col)

            for m in t_data.get("measures", []):
                meas = PBIPMeasure(
                    name=m.get("name", ""),
                    expression=self._extract_expression(m.get("expression")),
                    table_name=t_name,
                    format_string=m.get("formatString"),
                    is_hidden=m.get("isHidden", False),
                )
                t_measures.append(meas)
                measures.append(meas)

            tables.append(PBIPTable(
                name=t_name,
                columns=t_columns,
                measures=t_measures,
                is_hidden=t_data.get("isHidden", False),
            ))

        # Relationships
        for r in model.get("relationships", []):
            relationships.append(PBIPRelationship(
                from_table=r.get("fromTable", ""),
                from_column=r.get("fromColumn", ""),
                to_table=r.get("toTable", ""),
                to_column=r.get("toColumn", ""),
                cardinality=r.get("fromCardinality") or r.get("cardinality", "manyToOne"),
                cross_filter_direction=r.get("crossFilteringBehavior", "single"),
                is_active=r.get("isActive", True),
            ))

        return tables, measures, relationships

    def _parse_tmdl_definitions(self) -> Tuple[List[PBIPTable], List[PBIPMeasure], List[PBIPRelationship]]:
        tables: List[PBIPTable] = []
        measures: List[PBIPMeasure] = []
        relationships: List[PBIPRelationship] = []

        # Find all .tmdl files
        tmdl_files = list(self.root_path.rglob("*.tmdl"))
        for tf in tmdl_files:
            try:
                content = tf.read_text(encoding="utf-8-sig", errors="ignore")
                
                # Check if it's a relationship file
                if "relationships.tmdl" in tf.name.lower() or "relationship " in content:
                    rels = self._parse_tmdl_relationships(content)
                    relationships.extend(rels)
                
                # Check if it's a table file
                if tf.parent.name == "tables" or content.strip().startswith("table "):
                    table, t_measures = self._parse_tmdl_table(content, tf.stem)
                    if table:
                        tables.append(table)
                        measures.extend(t_measures)
            except Exception:
                pass

        return tables, measures, relationships

    def _parse_tmdl_table(self, content: str, default_name: str) -> Tuple[Optional[PBIPTable], List[PBIPMeasure]]:
        lines = content.splitlines()
        table_name = default_name
        columns: List[PBIPColumn] = []
        measures: List[PBIPMeasure] = []

        current_column: Optional[Dict[str, Any]] = None
        current_measure: Optional[Dict[str, Any]] = None
        in_expression = False
        expr_lines = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Table declaration
            if line.startswith("table ") or line.startswith("table '"):
                m = re.match(r"table\s+'?([^'\n]+)'?", line)
                if m:
                    table_name = m.group(1).strip("'")
                continue

            # Measure declaration
            measure_match = re.match(r"^\s+measure\s+'?([^'=]+)'?\s*=\s*(.*)", line)
            if measure_match:
                # Flush previous
                if current_column:
                    columns.append(PBIPColumn(**current_column))
                    current_column = None
                if current_measure:
                    if expr_lines:
                        current_measure["expression"] = "\n".join(expr_lines).strip()
                    measures.append(PBIPMeasure(**current_measure))
                    current_measure = None
                    expr_lines = []

                m_name = measure_match.group(1).strip().strip("'")
                first_line_expr = measure_match.group(2).strip()
                current_measure = {
                    "name": m_name,
                    "expression": first_line_expr,
                    "table_name": table_name,
                }
                expr_lines = [first_line_expr] if first_line_expr else []
                in_expression = True
                continue

            # Column declaration
            col_match = re.match(r"^\s+column\s+'?([^'\n=]+)'?(?:\s*=\s*(.*))?", line)
            if col_match:
                if current_column:
                    columns.append(PBIPColumn(**current_column))
                    current_column = None
                if current_measure:
                    if expr_lines:
                        current_measure["expression"] = "\n".join(expr_lines).strip()
                    measures.append(PBIPMeasure(**current_measure))
                    current_measure = None
                    expr_lines = []

                c_name = col_match.group(1).strip().strip("'")
                c_expr = col_match.group(2)
                current_column = {
                    "name": c_name,
                    "is_calculated": bool(c_expr),
                    "expression": c_expr.strip() if c_expr else None,
                }
                in_expression = bool(c_expr)
                expr_lines = [c_expr.strip()] if c_expr else []
                continue

            # Property under measure or column
            if current_measure:
                if line.startswith("\t\t") or line.startswith("        ") or (line.startswith(" ") and not line.strip().startswith(("formatString:", "lineageTag:", "annotation"))):
                    expr_lines.append(stripped)
                elif "formatString:" in line:
                    current_measure["format_string"] = line.split("formatString:")[1].strip()
            elif current_column:
                if "dataType:" in line:
                    current_column["data_type"] = line.split("dataType:")[1].strip()
                elif in_expression:
                    expr_lines.append(stripped)

        if current_column:
            if expr_lines and current_column.get("is_calculated"):
                current_column["expression"] = "\n".join(expr_lines).strip()
            columns.append(PBIPColumn(**current_column))

        if current_measure:
            if expr_lines:
                current_measure["expression"] = "\n".join(expr_lines).strip()
            measures.append(PBIPMeasure(**current_measure))

        table = PBIPTable(
            name=table_name,
            columns=columns,
            measures=measures,
        )
        return table, measures

    def _parse_tmdl_relationships(self, content: str) -> List[PBIPRelationship]:
        rels: List[PBIPRelationship] = []
        blocks = content.split("relationship ")
        for block in blocks[1:]:
            lines = block.splitlines()
            from_table, from_col = "", ""
            to_table, to_col = "", ""
            cardinality = "manyToOne"
            cross_filter = "single"
            is_active = True

            for line in lines:
                s = line.strip()
                if s.startswith("fromColumn:"):
                    parts = s.split("fromColumn:")[1].strip().split(".")
                    if len(parts) >= 2:
                        from_table, from_col = parts[0].strip("' "), parts[1].strip("' []")
                elif s.startswith("toColumn:"):
                    parts = s.split("toColumn:")[1].strip().split(".")
                    if len(parts) >= 2:
                        to_table, to_col = parts[0].strip("' "), parts[1].strip("' []")
                elif s.startswith("cardinality:"):
                    cardinality = s.split("cardinality:")[1].strip()
                elif s.startswith("crossFilteringBehavior:"):
                    cross_filter = s.split("crossFilteringBehavior:")[1].strip()
                elif s.startswith("isActive:"):
                    is_active = (s.split("isActive:")[1].strip().lower() == "true")

            if from_table and to_table:
                rels.append(PBIPRelationship(
                    from_table=from_table,
                    from_column=from_col,
                    to_table=to_table,
                    to_column=to_col,
                    cardinality=cardinality,
                    cross_filter_direction=cross_filter,
                    is_active=is_active,
                ))
        return rels

    # -------------------------------------------------------------
    # REPORT PARSER
    # -------------------------------------------------------------

    def _parse_report(self) -> Optional[PBIPReport]:
        """Finds and parses the report definitions."""
        pages: List[PBIPPage] = []

        # Check for report.json
        report_json_files = list(self.root_path.rglob("report.json"))
        if report_json_files:
            try:
                with open(report_json_files[0], "r", encoding="utf-8-sig", errors="ignore") as f:
                    data = json.load(f)
                    pages = self._parse_classic_report_json(data)
            except Exception:
                pass

        # If not found or empty, check for modern PBIR structure: definition/pages/*/page.json
        if not pages:
            pages = self._parse_pbir_pages()

        if not pages:
            return None

        total_visuals = sum(len(p.visuals) for p in pages)
        return PBIPReport(pages=pages, visuals_count=total_visuals)

    def _parse_classic_report_json(self, data: Dict[str, Any]) -> List[PBIPPage]:
        pages: List[PBIPPage] = []
        sections = data.get("sections", [])

        for idx, sec in enumerate(sections):
            page_id = sec.get("name", f"Page_{idx+1}")
            display_name = sec.get("displayName", page_id)
            visuals: List[PBIPVisual] = []

            for v_cont in sec.get("visualContainers", []):
                vis = self._parse_visual_container(v_cont)
                if vis:
                    visuals.append(vis)

            pages.append(PBIPPage(
                id=page_id,
                name=page_id,
                display_name=display_name,
                visuals=visuals,
            ))

        return pages

    def _parse_visual_container(self, v_cont: Dict[str, Any]) -> Optional[PBIPVisual]:
        config_raw = v_cont.get("config", "{}")
        if isinstance(config_raw, str):
            try:
                config = json.loads(config_raw)
            except Exception:
                config = {}
        else:
            config = config_raw

        single_vis = config.get("singleVisual", {})
        if not single_vis:
            # Check if it's a group or custom
            return None

        vis_type = single_vis.get("visualType", "unknown")
        vis_id = config.get("name", v_cont.get("name", "v_unknown"))

        # Extract title if present
        title = self._extract_visual_title(single_vis)

        # Extract projections / data roles
        projections = single_vis.get("projections", {})
        prototype_query = single_vis.get("prototypeQuery", {})

        x_axis, y_axis, legend, values, tooltips, slicers, all_fields = self._extract_projections(
            projections, prototype_query, single_vis
        )

        filters_raw = v_cont.get("filters", "[]")
        filters = []
        if isinstance(filters_raw, str):
            try:
                filters = json.loads(filters_raw)
            except Exception:
                pass
        elif isinstance(filters_raw, list):
            filters = filters_raw

        return PBIPVisual(
            id=vis_id,
            title=title,
            visual_type=self._normalize_visual_type(vis_type),
            x_axis_fields=x_axis,
            y_axis_fields=y_axis,
            legend_fields=legend,
            values_fields=values,
            tooltip_fields=tooltips,
            slicer_fields=slicers,
            all_referenced_fields=all_fields,
            filters=filters,
            raw_config=config,
        )

    def _parse_pbir_pages(self) -> List[PBIPPage]:
        pages: List[PBIPPage] = []
        
        # Find all page.json in definition/pages/
        page_files = list(self.root_path.rglob("definition/pages/*/page.json")) + list(self.root_path.rglob("pages/*/page.json"))
        
        for pf in page_files:
            try:
                with open(pf, "r", encoding="utf-8-sig", errors="ignore") as f:
                    page_data = json.load(f)
                    page_id = page_data.get("name", pf.parent.name)
                    display_name = page_data.get("displayName", page_id)
                    
                    visuals = []
                    # Find visuals in sibling visuals/ dir
                    vis_dir = pf.parent / "visuals"
                    if vis_dir.exists():
                        for vf in vis_dir.rglob("visual.json"):
                            try:
                                with open(vf, "r", encoding="utf-8-sig", errors="ignore") as vf_file:
                                    v_data = json.load(vf_file)
                                    vis = self._parse_pbir_visual(v_data, vf.parent.name)
                                    if vis:
                                        visuals.append(vis)
                            except Exception:
                                pass
                    
                    pages.append(PBIPPage(
                        id=page_id,
                        name=page_id,
                        display_name=display_name,
                        visuals=visuals,
                    ))
            except Exception:
                pass

        return pages

    def _parse_pbir_visual(self, v_data: Dict[str, Any], default_id: str) -> Optional[PBIPVisual]:
        vis = v_data.get("visual", v_data)
        vis_type = vis.get("visualType", "unknown")
        vis_id = v_data.get("name", default_id)
        
        title = None
        if "visualContainerObjects" in vis:
            title_objs = vis.get("visualContainerObjects", {}).get("title", [])
            for tobj in title_objs:
                text_expr = tobj.get("properties", {}).get("text", {}).get("expr", {})
                if "Literal" in text_expr:
                    title = text_expr["Literal"].get("Value", "").strip("'")

        x_axis, y_axis, legend, values, tooltips, slicers, all_fields = [], [], [], [], [], [], []
        
        query_state = vis.get("query", {}).get("queryState", {})
        for role, role_def in query_state.items():
            proj_list = role_def.get("projections", [])
            for proj in proj_list:
                field_name = self._extract_field_from_proj(proj)
                if field_name:
                    all_fields.append(field_name)
                    role_lower = role.lower()
                    if "category" in role_lower or "axis" in role_lower or "x" in role_lower:
                        x_axis.append(field_name)
                    elif "y" in role_lower or "value" in role_lower or "measure" in role_lower:
                        y_axis.append(field_name)
                        values.append(field_name)
                    elif "series" in role_lower or "legend" in role_lower:
                        legend.append(field_name)
                    elif "tooltip" in role_lower:
                        tooltips.append(field_name)
                    elif "slicer" in role_lower or vis_type.lower() == "slicer":
                        slicers.append(field_name)

        return PBIPVisual(
            id=vis_id,
            title=title,
            visual_type=self._normalize_visual_type(vis_type),
            x_axis_fields=x_axis,
            y_axis_fields=y_axis,
            legend_fields=legend,
            values_fields=values,
            tooltip_fields=tooltips,
            slicer_fields=slicers,
            all_referenced_fields=list(set(all_fields)),
            raw_config=v_data,
        )

    # -------------------------------------------------------------
    # HELPER EXTRACTION FUNCTIONS
    # -------------------------------------------------------------

    def _extract_projections(
        self, projections: Dict[str, Any], proto_query: Dict[str, Any], single_vis: Dict[str, Any]
    ) -> Tuple[List[str], List[str], List[str], List[str], List[str], List[str], List[str]]:
        x_axis: List[str] = []
        y_axis: List[str] = []
        legend: List[str] = []
        values: List[str] = []
        tooltips: List[str] = []
        slicers: List[str] = []
        all_fields: List[str] = []

        # 1. Inspect projections dictionary
        for role, items in projections.items():
            role_l = role.lower()
            if isinstance(items, list):
                for item in items:
                    q_ref = item.get("queryRef", "")
                    clean_name = self._clean_query_ref(q_ref)
                    if clean_name:
                        all_fields.append(clean_name)
                        if any(k in role_l for k in ["category", "axis", "group"]):
                            x_axis.append(clean_name)
                        elif any(k in role_l for k in ["y", "value", "values"]):
                            y_axis.append(clean_name)
                            values.append(clean_name)
                        elif any(k in role_l for k in ["series", "legend"]):
                            legend.append(clean_name)
                        elif "tooltip" in role_l:
                            tooltips.append(clean_name)
                        elif "values" in role_l and single_vis.get("visualType") == "slicer":
                            slicers.append(clean_name)

        # 2. Inspect prototypeQuery select columns
        for sel in proto_query.get("Select", []):
            name = sel.get("Name", "")
            clean_name = self._clean_query_ref(name)
            if clean_name and clean_name not in all_fields:
                all_fields.append(clean_name)

        return x_axis, y_axis, legend, values, tooltips, slicers, list(dict.fromkeys(all_fields))

    def _extract_field_from_proj(self, proj: Dict[str, Any]) -> str:
        field = proj.get("field", {})
        if "Column" in field:
            prop = field["Column"].get("Property", "")
            entity = field["Column"].get("Expression", {}).get("SourceRef", {}).get("Entity", "")
            return f"{entity}.{prop}" if entity else prop
        elif "HierarchyLevel" in field:
            level = field["HierarchyLevel"].get("Level", "")
            hier = field["HierarchyLevel"].get("Expression", {}).get("Hierarchy", {}).get("Hierarchy", "")
            return f"Date Hierarchy ({level})" if "date" in hier.lower() or "date" in level.lower() else f"{hier}.{level}"
        elif "Measure" in field:
            prop = field["Measure"].get("Property", "")
            return prop
        return proj.get("queryRef", "")

    def _extract_visual_title(self, single_vis: Dict[str, Any]) -> Optional[str]:
        objects = single_vis.get("objects", {})
        title_obj = objects.get("title", [])
        if isinstance(title_obj, list) and title_obj:
            props = title_obj[0].get("properties", {})
            text_prop = props.get("text", {})
            if isinstance(text_prop, dict):
                expr = text_prop.get("expr", {})
                if "Literal" in expr:
                    return str(expr["Literal"].get("Value", "")).strip("'")
            elif isinstance(text_prop, str):
                return text_prop
        return None

    def _clean_query_ref(self, ref: str) -> str:
        if not ref:
            return ""
        # e.g. "Sum(Sales.Total Sales)" -> "Sales.Total Sales" or "Total Sales"
        # e.g. "Min(Sales.Date.(DateHierarchy).(Year))" -> "Date Hierarchy"
        if "datehierarchy" in ref.lower():
            return "Date Hierarchy"
        # Strip aggregation wrapper e.g. Sum(x) -> x
        match = re.match(r"^[A-Za-z]+\((.+)\)$", ref)
        if match:
            ref = match.group(1)
        # Strip table prefix if desired or retain
        return ref.strip()

    def _extract_expression(self, expr_data: Any) -> str:
        if isinstance(expr_data, str):
            return expr_data
        elif isinstance(expr_data, list):
            return "\n".join([str(x) for x in expr_data])
        return ""

    def _normalize_visual_type(self, vtype: str) -> str:
        v_lower = vtype.lower().replace(" ", "").replace("_", "").replace("-", "")
        mapping = {
            "linechart": "Line Chart",
            "columnchart": "Column Chart",
            "barchart": "Bar Chart",
            "clusteredcolumnchart": "Clustered Column Chart",
            "clusteredbarchart": "Clustered Bar Chart",
            "stackedcolumnchart": "Stacked Column Chart",
            "stackedbarchart": "Stacked Bar Chart",
            "100stackedcolumnchart": "100% Stacked Column Chart",
            "100stackedbarchart": "100% Stacked Bar Chart",
            "piechart": "Pie Chart",
            "donutchart": "Donut Chart",
            "tableex": "Table",
            "table": "Table",
            "pivottable": "Matrix",
            "matrix": "Matrix",
            "card": "Card",
            "multirawcard": "Multi-row Card",
            "slicer": "Slicer",
            "treemap": "Treemap",
            "gauge": "Gauge",
            "kpi": "KPI",
            "areachart": "Area Chart",
            "stackedareachart": "Stacked Area Chart",
            "scatterchart": "Scatter Chart",
            "waterfallchart": "Waterfall Chart",
            "funnel": "Funnel Chart",
            "map": "Map",
            "filledmap": "Filled Map",
        }
        return mapping.get(v_lower, vtype)
