"""
Pydantic data models for Power BI Answer Evaluator.
"""
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class EvaluationStatus(str, Enum):
    CORRECT = "Correct"
    PARTIAL = "Partially Correct"
    INCORRECT = "Incorrect"
    EXCEPTION = "Exception"


class ExceptionType(str, Enum):
    MISSING_PROJECT = "Missing Student Project"
    INVALID_FOLDER = "Invalid Student Folder"
    PBIP_NOT_FOUND = "PBIP Project Not Detected"
    CORRUPTED_PROJECT = "Corrupted Project Files"
    UNSUPPORTED_STRUCTURE = "Unsupported Project Structure"
    PARSING_ERROR = "Parsing Error"
    ENGINE_ERROR = "Evaluation Engine Error"


class TargetComponent(str, Enum):
    VISUAL = "Visual"
    SEMANTIC_MODEL = "Semantic Model"
    DAX = "DAX Measure"
    CALCULATED_COLUMN = "Calculated Column"
    RELATIONSHIP = "Relationship"
    PAGE = "Page"
    FILTER_SLICER = "Filter/Slicer"


class CriterionRule(BaseModel):
    id: str = Field(default="", description="Unique criterion ID e.g. C1")
    title: str = Field(description="Criterion description e.g. Visual Type is Line Chart")
    component: TargetComponent = Field(default=TargetComponent.VISUAL)
    target_property: str = Field(description="Property being checked: visual_type, x_axis, y_axis, legend, measure_name, dax_formula, table, column, relationship")
    expected_value: Any = Field(description="Expected value or regex or name")
    accepted_variations: List[str] = Field(default_factory=list, description="Explicitly permitted variations")
    marks: float = Field(default=0.0, description="Marks allocated for this criterion")
    is_optional: bool = Field(default=False)
    case_sensitive: bool = Field(default=False)


class EvaluationRule(BaseModel):
    question_id: str = Field(description="e.g. Q1, Q2")
    question_text: str = Field(description="Full text of the question")
    marks: float = Field(description="Total marks for this question")
    criteria: List[CriterionRule] = Field(default_factory=list, description="Granular criteria for scoring")
    accepted_variations: List[str] = Field(default_factory=list, description="General accepted variations note")
    notes: Optional[str] = None


class EvaluationRuleSet(BaseModel):
    title: str = Field(default="Power BI Evaluation Rule Set")
    description: Optional[str] = None
    total_marks: float = Field(default=100.0)
    questions: List[EvaluationRule] = Field(default_factory=list)


# --- PBIP Extracted Representation Models ---

class PBIPColumn(BaseModel):
    name: str
    data_type: Optional[str] = None
    is_calculated: bool = False
    expression: Optional[str] = None
    is_hidden: bool = False


class PBIPMeasure(BaseModel):
    name: str
    expression: str
    table_name: Optional[str] = None
    format_string: Optional[str] = None
    is_hidden: bool = False


class PBIPRelationship(BaseModel):
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    cardinality: Optional[str] = "manyToOne"  # oneToOne, oneToMany, manyToOne, manyToMany
    cross_filter_direction: Optional[str] = "single"  # single, both
    is_active: bool = True


class PBIPTable(BaseModel):
    name: str
    columns: List[PBIPColumn] = Field(default_factory=list)
    measures: List[PBIPMeasure] = Field(default_factory=list)
    is_hidden: bool = False


class PBIPVisual(BaseModel):
    id: str
    title: Optional[str] = None
    visual_type: str  # e.g. lineChart, clusteredBarChart, pieChart, tableEx, card
    x_axis_fields: List[str] = Field(default_factory=list)
    y_axis_fields: List[str] = Field(default_factory=list)
    legend_fields: List[str] = Field(default_factory=list)
    values_fields: List[str] = Field(default_factory=list)
    tooltip_fields: List[str] = Field(default_factory=list)
    filters: List[Dict[str, Any]] = Field(default_factory=list)
    slicer_fields: List[str] = Field(default_factory=list)
    all_referenced_fields: List[str] = Field(default_factory=list)
    raw_config: Optional[Dict[str, Any]] = None


class PBIPPage(BaseModel):
    id: str
    name: str
    display_name: Optional[str] = None
    visuals: List[PBIPVisual] = Field(default_factory=list)


class PBIPReport(BaseModel):
    pages: List[PBIPPage] = Field(default_factory=list)
    visuals_count: int = 0


class PBIPSemanticModel(BaseModel):
    tables: List[PBIPTable] = Field(default_factory=list)
    measures: List[PBIPMeasure] = Field(default_factory=list)
    relationships: List[PBIPRelationship] = Field(default_factory=list)

    def all_measures(self) -> List[PBIPMeasure]:
        result = list(self.measures)
        seen_names = {m.name.lower() for m in result}
        for t in self.tables:
            for m in t.measures:
                if m.name.lower() not in seen_names:
                    result.append(m)
                    seen_names.add(m.name.lower())
        return result


class PBIPProject(BaseModel):
    project_name: str
    register_no: str
    report: Optional[PBIPReport] = None
    semantic_model: Optional[PBIPSemanticModel] = None
    is_valid: bool = True
    error_message: Optional[str] = None


# --- Evaluation Output Models ---

class CriterionEvaluationResult(BaseModel):
    criterion_id: str
    title: str
    marks_awarded: float
    maximum_marks: float
    is_met: bool
    student_value: Optional[str] = None
    expected_value: Optional[str] = None
    remarks: str = ""


class QuestionEvaluationDetail(BaseModel):
    question_id: str
    question_text: str
    status: EvaluationStatus
    marks_awarded: float
    maximum_marks: float
    requirement_summary: str
    expected_summary: str
    student_summary: str
    criteria_results: List[CriterionEvaluationResult] = Field(default_factory=list)
    remarks: str


class EvaluationException(BaseModel):
    register_no: str
    issue_type: ExceptionType
    description: str
    status: str = "Exception"
    details: Optional[str] = None


class StudentEvaluationResult(BaseModel):
    register_no: str
    total_marks: float
    maximum_marks: float
    percentage: float
    questions_evaluated: int
    questions_correct: int
    questions_partially_correct: int
    questions_incorrect: int
    status: EvaluationStatus
    question_details: List[QuestionEvaluationDetail] = Field(default_factory=list)
    exception: Optional[EvaluationException] = None


class ScanItem(BaseModel):
    register_no: str
    folder_path: str
    pbip_file_found: bool
    report_folder_found: bool
    model_folder_found: bool
    is_valid: bool
    issue_type: Optional[ExceptionType] = None
    issue_message: Optional[str] = None


class ScanResult(BaseModel):
    total_folders: int
    valid_count: int
    missing_count: int
    invalid_count: int
    items: List[ScanItem] = Field(default_factory=list)
    session_id: str


class BatchEvaluationSummary(BaseModel):
    session_id: str
    total_students: int
    evaluated_count: int
    exception_count: int
    average_score: float
    highest_score: float
    lowest_score: float
    results: List[StudentEvaluationResult] = Field(default_factory=list)
    exceptions: List[EvaluationException] = Field(default_factory=list)
    rule_set: EvaluationRuleSet
    excel_download_url: Optional[str] = None
