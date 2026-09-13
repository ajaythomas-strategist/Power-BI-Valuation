export enum EvaluationStatus {
  CORRECT = "Correct",
  PARTIAL = "Partially Correct",
  INCORRECT = "Incorrect",
  EXCEPTION = "Exception",
}

export enum ExceptionType {
  MISSING_PROJECT = "Missing Student Project",
  INVALID_FOLDER = "Invalid Student Folder",
  PBIP_NOT_FOUND = "PBIP Project Not Detected",
  CORRUPTED_PROJECT = "Corrupted Project Files",
  UNSUPPORTED_STRUCTURE = "Unsupported Project Structure",
  PARSING_ERROR = "Parsing Error",
  ENGINE_ERROR = "Evaluation Engine Error",
}

export enum TargetComponent {
  VISUAL = "Visual",
  SEMANTIC_MODEL = "Semantic Model",
  DAX = "DAX Measure",
  CALCULATED_COLUMN = "Calculated Column",
  RELATIONSHIP = "Relationship",
  PAGE = "Page",
  FILTER_SLICER = "Filter/Slicer",
}

export interface CriterionRule {
  id: string;
  title: string;
  component: TargetComponent;
  target_property: string;
  expected_value: string | number | boolean;
  accepted_variations: string[];
  marks: number;
  is_optional?: boolean;
  case_sensitive?: boolean;
}

export interface EvaluationRule {
  question_id: string;
  question_text: string;
  marks: number;
  criteria: CriterionRule[];
  accepted_variations: string[];
  notes?: string;
}

export interface EvaluationRuleSet {
  title: string;
  description?: string;
  total_marks: number;
  questions: EvaluationRule[];
}

export interface ScanItem {
  register_no: string;
  folder_path: string;
  pbip_file_found: boolean;
  report_folder_found: boolean;
  model_folder_found: boolean;
  is_valid: boolean;
  issue_type?: ExceptionType;
  issue_message?: string;
}

export interface ScanResult {
  total_folders: number;
  valid_count: number;
  missing_count: number;
  invalid_count: number;
  items: ScanItem[];
  session_id: string;
}

export interface CriterionEvaluationResult {
  criterion_id: string;
  title: string;
  marks_awarded: number;
  maximum_marks: number;
  is_met: boolean;
  student_value?: string;
  expected_value?: string;
  remarks: string;
}

export interface QuestionEvaluationDetail {
  question_id: string;
  question_text: string;
  status: EvaluationStatus;
  marks_awarded: number;
  maximum_marks: number;
  requirement_summary: string;
  expected_summary: string;
  student_summary: string;
  criteria_results: CriterionEvaluationResult[];
  remarks: string;
}

export interface EvaluationException {
  register_no: string;
  issue_type: ExceptionType;
  description: string;
  status: string;
  details?: string;
}

export interface StudentEvaluationResult {
  register_no: string;
  total_marks: number;
  maximum_marks: number;
  percentage: number;
  questions_evaluated: number;
  questions_correct: number;
  questions_partially_correct: number;
  questions_incorrect: number;
  status: EvaluationStatus;
  question_details: QuestionEvaluationDetail[];
  exception?: EvaluationException;
}

export interface BatchEvaluationSummary {
  session_id: string;
  total_students: number;
  evaluated_count: number;
  exception_count: number;
  average_score: number;
  highest_score: number;
  lowest_score: number;
  results: StudentEvaluationResult[];
  exceptions: EvaluationException[];
  rule_set: EvaluationRuleSet;
  excel_download_url?: string;
}
