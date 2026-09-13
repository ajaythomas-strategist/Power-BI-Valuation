"""
Integration tests for Evaluation Engine, Batch Scanner, and Excel Exporter.
"""
import pytest
from pathlib import Path
from app.services.sample_fixtures import (
    create_sample_dataset_archive,
    get_sample_answer_key,
)
from app.models.schemas import EvaluationRuleSet, EvaluationStatus
from app.services.cleanup_service import CleanupService
from app.services.batch_scanner import BatchScanner
from app.evaluator.engine import EvaluationEngine
from app.exporters.excel_exporter import ExcelExporter
import openpyxl


def test_end_to_end_evaluation_pipeline():
    # 1. Load RuleSet
    raw_key = get_sample_answer_key()
    rule_set = EvaluationRuleSet(**raw_key)
    assert len(rule_set.questions) == 4

    # 2. Extract sample student archive
    sid, session_path = CleanupService.create_session_workspace()
    try:
        zip_bytes = create_sample_dataset_archive()
        submissions_dir = session_path / "submissions"
        main_folder = BatchScanner.process_zip_upload(zip_bytes, submissions_dir)

        # 3. Scan directory
        scan_res = BatchScanner.scan_directory(main_folder, session_id=sid)
        assert scan_res.total_folders == 5
        assert scan_res.valid_count == 3
        assert scan_res.missing_count + scan_res.invalid_count == 2

        # 4. Load projects
        projects, exceptions = BatchScanner.load_and_parse_all_students(scan_res)
        assert len(projects) == 3
        assert len(exceptions) == 2

        # 5. Evaluate students
        engine = EvaluationEngine(rule_set)
        results = [engine.evaluate_student(p) for p in projects]

        # Student 23001 should have full marks (100) due to accepted Date Hierarchy variation
        res_23001 = next(r for r in results if r.register_no == "23001")
        assert res_23001.total_marks == 100.0
        assert res_23001.status == EvaluationStatus.CORRECT

        # Student 23002 should have 82 marks (Q1, Q2, Q3 full marks; Q4 partial 7 marks for values field)
        res_23002 = next(r for r in results if r.register_no == "23002")
        assert res_23002.total_marks == 82.0
        assert res_23002.status == EvaluationStatus.PARTIAL

        # Student 23003 should have 39 marks (Q2 correct: 25, Q1 partial: 7 for Total Sales value, Q3 wrong: 0, Q4 partial: 7 for Total Sales value)
        res_23003 = next(r for r in results if r.register_no == "23003")
        assert res_23003.total_marks == 39.0
        assert res_23003.status == EvaluationStatus.PARTIAL

        # 6. Generate Excel workbook
        from app.models.schemas import BatchEvaluationSummary
        all_results = list(results)
        for exc in exceptions:
            all_results.append(engine.evaluate_student(
                type("Obj", (), {"register_no": exc.register_no, "is_valid": False, "error_message": exc.description, "project_name": "Exception"})()
            ))

        summary = BatchEvaluationSummary(
            session_id=sid,
            total_students=5,
            evaluated_count=3,
            exception_count=2,
            average_score=66.67,
            highest_score=100.0,
            lowest_score=25.0,
            results=all_results,
            exceptions=exceptions,
            rule_set=rule_set,
        )

        excel_bytes = ExcelExporter.generate_workbook(summary)
        wb = openpyxl.load_workbook(excel_bytes)

        # Verify sheets
        sheet_names = wb.sheetnames
        assert "Summary" in sheet_names
        assert "Question-wise Evaluation" in sheet_names
        assert "Exceptions" in sheet_names
        assert "Evaluation Rules" in sheet_names

        # Verify Summary sheet content
        ws_sum = wb["Summary"]
        assert ws_sum["A1"].value == "Register No."
        assert ws_sum["B1"].value == "Total Marks"

    finally:
        # 7. Cleanup
        CleanupService.cleanup_session(sid)
        assert not session_path.exists()
