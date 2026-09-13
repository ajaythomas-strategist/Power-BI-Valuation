"""
Batch Submissions Scanner for Power BI Evaluation.
Scans student folders, captures Register Numbers from immediate subfolder names,
identifies PBIP projects, and isolates exceptions without blocking the batch.
"""
import os
import zipfile
import shutil
from pathlib import Path
from typing import List, Tuple, Optional

from app.models.schemas import (
    ScanResult,
    ScanItem,
    ExceptionType,
    PBIPProject,
    EvaluationException,
)
from app.parsers.pbip_parser import PBIPParser


class BatchScanner:
    """Scans and validates batch student folder submissions."""

    @classmethod
    def process_zip_upload(cls, zip_file_bytes: bytes, target_dir: Path) -> Path:
        """Extracts a ZIP archive containing student subfolders."""
        import io
        target_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(zip_file_bytes), "r") as z:
            z.extractall(target_dir)

        # Detect if there is a single top-level directory wrapper (e.g. MainFolder/)
        top_items = [p for p in target_dir.iterdir() if p.is_dir() and not p.name.startswith((".", "__MACOSX"))]
        if len(top_items) == 1 and not any(p.suffix == ".pbip" for p in top_items[0].iterdir() if p.is_file()):
            # If the single top folder contains subdirectories, use it as the main folder
            sub_dirs = [p for p in top_items[0].iterdir() if p.is_dir() and not p.name.startswith((".", "__MACOSX"))]
            if len(sub_dirs) > 1:
                return top_items[0]

        return target_dir

    @classmethod
    def scan_directory(cls, main_folder_path: Path, session_id: str) -> ScanResult:
        """
        Scans all immediate subfolders in the main folder.
        Each immediate subfolder name is captured as the student Register Number.
        """
        if not main_folder_path.exists():
            return ScanResult(
                total_folders=0,
                valid_count=0,
                missing_count=0,
                invalid_count=0,
                items=[],
                session_id=session_id,
            )

        items: List[ScanItem] = []
        valid_count = 0
        missing_count = 0
        invalid_count = 0

        # Filter out hidden or macOS resource directories
        subfolders = [
            p for p in sorted(main_folder_path.iterdir())
            if p.is_dir() and not p.name.startswith((".", "__MACOSX", "_"))
        ]

        # If no subfolders exist directly, but root has pbip files, treat root as single student submission
        if not subfolders:
            root_pbips = list(main_folder_path.glob("*.pbip"))
            if root_pbips:
                subfolders = [main_folder_path]

        for subfolder in subfolders:
            reg_no = subfolder.name if subfolder != main_folder_path else "Student_Submission"
            
            # Check contents of the subfolder
            all_files = list(subfolder.rglob("*"))
            non_hidden_files = [f for f in all_files if not f.name.startswith(".") and "__MACOSX" not in str(f)]

            # 1. Empty folder check
            if not non_hidden_files:
                items.append(ScanItem(
                    register_no=reg_no,
                    folder_path=str(subfolder),
                    pbip_file_found=False,
                    report_folder_found=False,
                    model_folder_found=False,
                    is_valid=False,
                    issue_type=ExceptionType.MISSING_PROJECT,
                    issue_message=f"Subfolder '{reg_no}' is empty. No student files found.",
                ))
                missing_count += 1
                continue

            pbip_files = [f for f in non_hidden_files if f.is_file() and f.name.endswith(".pbip")]
            pbix_files = [f for f in non_hidden_files if f.is_file() and f.name.endswith(".pbix")]
            report_dirs = [f for f in non_hidden_files if f.is_dir() and f.name.endswith(".Report")]
            model_dirs = [f for f in non_hidden_files if f.is_dir() and (f.name.endswith(".Dataset") or f.name.endswith(".SemanticModel"))]
            bim_files = [f for f in non_hidden_files if f.is_file() and f.name == "model.bim"]
            report_json_files = [f for f in non_hidden_files if f.is_file() and f.name == "report.json"]
            tmdl_files = [f for f in non_hidden_files if f.is_file() and f.name.endswith(".tmdl")]

            has_pbip = len(pbip_files) > 0 or len(pbix_files) > 0
            has_report = len(report_dirs) > 0 or len(report_json_files) > 0 or len(pbix_files) > 0
            has_model = len(model_dirs) > 0 or len(bim_files) > 0 or len(tmdl_files) > 0 or len(pbix_files) > 0

            # If none of the Power BI project indicators are found
            if not has_pbip and not has_report and not has_model:
                items.append(ScanItem(
                    register_no=reg_no,
                    folder_path=str(subfolder),
                    pbip_file_found=False,
                    report_folder_found=False,
                    model_folder_found=False,
                    is_valid=False,
                    issue_type=ExceptionType.PBIP_NOT_FOUND,
                    issue_message=f"No Power BI (.pbip / .Report / .Dataset / TMDL) project detected in folder '{reg_no}'.",
                ))
                invalid_count += 1
                continue

            # Quick parse validation test
            parser = PBIPParser(str(subfolder), register_no=reg_no)
            parsed_proj = parser.parse()

            if not parsed_proj.is_valid:
                items.append(ScanItem(
                    register_no=reg_no,
                    folder_path=str(subfolder),
                    pbip_file_found=has_pbip,
                    report_folder_found=has_report,
                    model_folder_found=has_model,
                    is_valid=False,
                    issue_type=ExceptionType.CORRUPTED_PROJECT,
                    issue_message=parsed_proj.error_message or "Project files could not be parsed.",
                ))
                invalid_count += 1
                continue

            # Submission is Valid!
            items.append(ScanItem(
                register_no=reg_no,
                folder_path=str(subfolder),
                pbip_file_found=has_pbip,
                report_folder_found=has_report,
                model_folder_found=has_model,
                is_valid=True,
                issue_type=None,
                issue_message=None,
            ))
            valid_count += 1

        return ScanResult(
            total_folders=len(items),
            valid_count=valid_count,
            missing_count=missing_count,
            invalid_count=invalid_count,
            items=items,
            session_id=session_id,
        )

    @classmethod
    def load_and_parse_all_students(cls, scan_result: ScanResult) -> Tuple[List[PBIPProject], List[EvaluationException]]:
        """Parses all valid student folders into PBIPProject objects and compiles exceptions for invalid ones."""
        projects: List[PBIPProject] = []
        exceptions: List[EvaluationException] = []

        for item in scan_result.items:
            if not item.is_valid:
                exceptions.append(EvaluationException(
                    register_no=item.register_no,
                    issue_type=item.issue_type or ExceptionType.INVALID_FOLDER,
                    description=item.issue_message or "Invalid student submission folder.",
                    details=f"Folder Path: {item.folder_path}",
                ))
                continue

            try:
                parser = PBIPParser(item.folder_path, register_no=item.register_no)
                project = parser.parse()
                projects.append(project)
            except Exception as e:
                exceptions.append(EvaluationException(
                    register_no=item.register_no,
                    issue_type=ExceptionType.ENGINE_ERROR,
                    description=f"Error reading project: {str(e)}",
                    details=f"Path: {item.folder_path}",
                ))

        return projects, exceptions
