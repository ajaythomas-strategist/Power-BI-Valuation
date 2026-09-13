"""
REST API Routes for Power BI Answer Evaluator.
"""
import os
import io
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse

from app.models.schemas import (
    EvaluationRuleSet,
    ScanResult,
    BatchEvaluationSummary,
    StudentEvaluationResult,
    EvaluationException,
    EvaluationStatus,
    ExceptionType,
)
from app.parsers.answer_key_parser import AnswerKeyParser
from app.services.cleanup_service import CleanupService
from app.services.batch_scanner import BatchScanner
from app.evaluator.engine import EvaluationEngine
from app.exporters.excel_exporter import ExcelExporter

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory session store for current active browser session evaluations
_SESSION_SUMMARIES: Dict[str, BatchEvaluationSummary] = {}
_SESSION_EXCEL_BYTES: Dict[str, bytes] = {}


@router.post("/extract-text")
async def extract_document_text(file: UploadFile = File(...)):
    """Extracts human-readable plain text from uploaded DOCX, TXT, MD, JSON files."""
    import zipfile
    import xml.etree.ElementTree as ET

    filename = file.filename or ""
    bytes_data = await file.read()

    # 1. DOCX (Word) format extraction
    if filename.lower().endswith(".docx") or bytes_data.startswith(b"PK"):
        try:
            with zipfile.ZipFile(io.BytesIO(bytes_data)) as z:
                if "word/document.xml" in z.namelist():
                    xml_content = z.read("word/document.xml")
                    tree = ET.fromstring(xml_content)
                    ns_w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
                    paragraphs = []
                    for p in tree.iter(f"{{{ns_w}}}p"):
                        texts = [node.text for node in p.iter(f"{{{ns_w}}}t") if node.text]
                        if texts:
                            p_str = "".join(texts).strip()
                            if p_str:
                                paragraphs.append(p_str)
                    extracted = "\n\n".join(paragraphs).strip()
                    if extracted:
                        return {"text": extracted, "filename": filename}
        except Exception as e:
            logger.warning(f"DOCX XML extraction failed: {e}")

    # 2. Text / Markdown / UTF-8 fallback
    try:
        text = bytes_data.decode("utf-8-sig", errors="ignore")
        return {"text": text, "filename": filename}
    except Exception:
        return {"text": "", "filename": filename}



@router.post("/rules/parse-answer-key", response_model=EvaluationRuleSet)
async def parse_answer_key(
    file: Optional[UploadFile] = File(None),
    raw_content: Optional[str] = Form(None),
):
    """Parses an uploaded Answer Key file or text into a structured EvaluationRuleSet."""
    content = ""
    filename = ""

    if file:
        filename = file.filename or "answer_key.json"
        bytes_data = await file.read()
        content = bytes_data.decode("utf-8", errors="ignore")
    elif raw_content:
        content = raw_content
        filename = "answer_key.txt"
    else:
        raise HTTPException(status_code=400, detail="No file or content provided.")

    try:
        rule_set = AnswerKeyParser.parse_content(content, filename)
        return rule_set
    except Exception as e:
        logger.error(f"Error parsing answer key: {e}")
        raise HTTPException(status_code=422, detail=f"Failed to parse answer key: {str(e)}")


@router.post("/rules/from-master-pbip", response_model=EvaluationRuleSet)
async def generate_rules_from_master_pbip(
    file: UploadFile = File(...),
    total_marks: float = Form(100.0),
):
    """
    Accepts a Master/Solution Power BI Project (.zip archive),
    extracts and parses the model, DAX measures, and visual pages,
    and automatically synthesizes a complete machine-evaluable EvaluationRuleSet.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    temp_dir = CleanupService.create_temp_workspace()
    try:
        content_bytes = await file.read()
        zip_path = temp_dir / "master_pbip.zip"
        with open(zip_path, "wb") as f:
            f.write(content_bytes)

        import zipfile
        if zipfile.is_zipfile(zip_path):
            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(temp_dir / "extracted")
            scan_dir = temp_dir / "extracted"
        else:
            scan_dir = temp_dir

        from app.parsers.pbip_parser import PBIPParser
        parser = PBIPParser(str(scan_dir), register_no="MASTER_SOLUTION")
        parsed_project = parser.parse()

        # If direct root didn't find report/model, check first level child directories
        if not parsed_project.is_valid:
            for child in scan_dir.iterdir():
                if child.is_dir():
                    sub_parser = PBIPParser(str(child), register_no="MASTER_SOLUTION")
                    sub_project = sub_parser.parse()
                    if sub_project.is_valid:
                        parsed_project = sub_project
                        break

        if not parsed_project.is_valid:
            raise HTTPException(
                status_code=422,
                detail="Could not detect a valid Power BI Project (.Report / .SemanticModel or model.bim/TMDL) inside the uploaded archive. Ensure your solution is saved as a Power BI Project (*.pbip) and zipped."
            )

        rule_set = AnswerKeyParser.generate_rules_from_pbip(
            parsed_project,
            total_marks=total_marks,
            title=f"Master Solution: {parsed_project.project_name}",
        )
        return rule_set
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error generating rules from master PBIP: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract rules from Master PBIP: {str(e)}")
    finally:
        CleanupService.purge_directory(temp_dir)


@router.post("/evaluate/scan-submissions", response_model=ScanResult)
async def scan_submissions(
    file: Optional[UploadFile] = File(None),
    session_id: Optional[str] = Form(None),
):
    """
    Accepts student folder ZIP submission.
    Unpacks into temporary session workspace, detects Register Numbers from subfolders,
    checks for PBIP projects, and isolates exceptions.
    """
    sid, session_path = CleanupService.create_session_workspace(session_id)

    if not file:
        raise HTTPException(status_code=400, detail="No submission file provided.")

    filename = file.filename or ""
    if not (filename.endswith(".zip") or filename.endswith(".tar.gz")):
        raise HTTPException(status_code=400, detail="Please upload a .zip archive of the Main Student Folder.")

    try:
        content_bytes = await file.read()
        submissions_dir = session_path / "submissions"
        main_folder = BatchScanner.process_zip_upload(content_bytes, submissions_dir)
        scan_result = BatchScanner.scan_directory(main_folder, session_id=sid)
        return scan_result
    except Exception as e:
        logger.error(f"Error scanning submissions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to scan student submissions: {str(e)}")


@router.post("/evaluate/run", response_model=BatchEvaluationSummary)
async def run_evaluation(
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks,
):
    """
    Runs the rule-based evaluation engine against the scanned student submissions.
    """
    session_id = payload.get("session_id")
    raw_rule_set = payload.get("rule_set")

    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required.")

    if not raw_rule_set:
        raise HTTPException(status_code=400, detail="rule_set is required.")

    try:
        rule_set = EvaluationRuleSet(**raw_rule_set)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid rule_set model: {str(e)}")

    session_path = CleanupService.get_session_workspace(session_id)
    if not session_path:
        raise HTTPException(status_code=404, detail="Session workspace not found or expired.")

    submissions_dir = session_path / "submissions"
    scan_result = BatchScanner.scan_directory(submissions_dir, session_id=session_id)

    # If top folder was single wrapper
    if scan_result.total_folders == 0:
        for sub in submissions_dir.iterdir():
            if sub.is_dir() and not sub.name.startswith("."):
                scan_result = BatchScanner.scan_directory(sub, session_id=session_id)
                if scan_result.total_folders > 0:
                    break

    projects, exceptions = BatchScanner.load_and_parse_all_students(scan_result)

    engine = EvaluationEngine(rule_set)
    results: List[StudentEvaluationResult] = []

    for proj in projects:
        try:
            res = engine.evaluate_student(proj)
            results.append(res)
        except Exception as e:
            logger.error(f"Error evaluating student {proj.register_no}: {e}")
            exc = EvaluationException(
                register_no=proj.register_no,
                issue_type=ExceptionType.ENGINE_ERROR,
                description=f"Evaluation failed: {str(e)}",
                details=f"Project: {proj.project_name}",
            )
            exceptions.append(exc)
            results.append(StudentEvaluationResult(
                register_no=proj.register_no,
                total_marks=0.0,
                maximum_marks=rule_set.total_marks,
                percentage=0.0,
                questions_evaluated=0,
                questions_correct=0,
                questions_partially_correct=0,
                questions_incorrect=len(rule_set.questions),
                status=EvaluationStatus.EXCEPTION,
                question_details=[],
                exception=exc,
            ))

    # Add invalid/missing folders as evaluated exception rows for visibility
    for exc in exceptions:
        if not any(r.register_no == exc.register_no for r in results):
            results.append(StudentEvaluationResult(
                register_no=exc.register_no,
                total_marks=0.0,
                maximum_marks=rule_set.total_marks,
                percentage=0.0,
                questions_evaluated=0,
                questions_correct=0,
                questions_partially_correct=0,
                questions_incorrect=len(rule_set.questions),
                status=EvaluationStatus.EXCEPTION,
                question_details=[],
                exception=exc,
            ))

    # Sort results by Register Number
    results.sort(key=lambda r: r.register_no)

    valid_results = [r for r in results if r.status != EvaluationStatus.EXCEPTION]
    total_students = len(results)
    evaluated_count = len(valid_results)
    exception_count = len(exceptions)

    avg_score = round(sum(r.total_marks for r in valid_results) / evaluated_count, 2) if evaluated_count > 0 else 0.0
    highest_score = max((r.total_marks for r in valid_results), default=0.0)
    lowest_score = min((r.total_marks for r in valid_results), default=0.0)

    summary = BatchEvaluationSummary(
        session_id=session_id,
        total_students=total_students,
        evaluated_count=evaluated_count,
        exception_count=exception_count,
        average_score=avg_score,
        highest_score=highest_score,
        lowest_score=lowest_score,
        results=results,
        exceptions=exceptions,
        rule_set=rule_set,
        excel_download_url=f"/api/evaluate/export-excel/{session_id}",
    )

    # Generate Excel in memory
    try:
        excel_stream = ExcelExporter.generate_workbook(summary)
        _SESSION_EXCEL_BYTES[session_id] = excel_stream.getvalue()
        _SESSION_SUMMARIES[session_id] = summary
    except Exception as e:
        logger.error(f"Failed to generate Excel: {e}")

    return summary


@router.get("/evaluate/export-excel/{session_id}")
async def export_excel(session_id: str):
    """Downloads the generated 4-sheet formatted .xlsx evaluation report."""
    excel_bytes = _SESSION_EXCEL_BYTES.get(session_id)
    if not excel_bytes:
        # Check if we have summary in store to regenerate
        summary = _SESSION_SUMMARIES.get(session_id)
        if summary:
            stream = ExcelExporter.generate_workbook(summary)
            excel_bytes = stream.getvalue()
            _SESSION_EXCEL_BYTES[session_id] = excel_bytes
        else:
            raise HTTPException(status_code=404, detail="Evaluation results not found for this session.")

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=PowerBI_Evaluation_{session_id[:8]}.xlsx"
        },
    )


@router.post("/evaluate/cleanup/{session_id}")
async def cleanup_session(session_id: str):
    """Cleans up temporary disk workspace after evaluation is downloaded."""
    CleanupService.cleanup_session(session_id)
    _SESSION_EXCEL_BYTES.pop(session_id, None)
    _SESSION_SUMMARIES.pop(session_id, None)
    return {"status": "success", "message": f"Session {session_id} cleaned up."}


@router.get("/samples/load")
async def load_sample_data():
    """
    Returns pre-configured sample question paper, answer key, and creates
    sample student submission structures for 1-click end-to-end testing.
    """
    from app.services.sample_fixtures import (
        create_sample_dataset_archive,
        get_sample_question_paper,
        get_sample_answer_key,
    )
    
    question_paper = get_sample_question_paper()
    answer_key = get_sample_answer_key()
    
    # Create sample zip in memory / session
    sid, session_path = CleanupService.create_session_workspace()
    zip_bytes = create_sample_dataset_archive()
    
    submissions_dir = session_path / "submissions"
    main_folder = BatchScanner.process_zip_upload(zip_bytes, submissions_dir)
    scan_result = BatchScanner.scan_directory(main_folder, session_id=sid)

    return {
        "session_id": sid,
        "question_paper": question_paper,
        "answer_key": answer_key,
        "scan_result": scan_result,
    }
