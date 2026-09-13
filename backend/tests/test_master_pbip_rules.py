"""
Unit tests for generating EvaluationRuleSet directly from a Master/Solution PBIP Project.
"""
import pytest
from app.services.sample_fixtures import create_sample_dataset_archive
from app.parsers.pbip_parser import PBIPParser
from app.parsers.answer_key_parser import AnswerKeyParser
from app.models.schemas import TargetComponent


def test_generate_rules_from_master_pbip():
    # 1. Generate sample master PBIP project
    archive_bytes = create_sample_dataset_archive()
    import zipfile
    import tempfile
    import io
    from pathlib import Path

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        with zipfile.ZipFile(io.BytesIO(archive_bytes), "r") as z:
            z.extractall(temp_path)

            # Subfolder 23001 is a full 100% solution
            master_dir = temp_path / "23001"
            parser = PBIPParser(str(master_dir), register_no="MASTER_SOLUTION")
            pbip_project = parser.parse()

            assert pbip_project.is_valid is True
            assert pbip_project.semantic_model is not None
            assert len(pbip_project.semantic_model.all_measures()) > 0

            # 2. Synthesize Rule Set
            rule_set = AnswerKeyParser.generate_rules_from_pbip(pbip_project, total_marks=100.0)

            assert rule_set is not None
            assert len(rule_set.questions) >= 3
            assert round(rule_set.total_marks) == 100

            # Verify DAX measures rule presence
            dax_questions = [q for q in rule_set.questions if any(c.component == TargetComponent.DAX for c in q.criteria)]
            assert len(dax_questions) > 0

            # Verify Visuals rule presence
            visual_questions = [q for q in rule_set.questions if any(c.component == TargetComponent.VISUAL for c in q.criteria)]
            assert len(visual_questions) > 0

            # Verify Model Relationships / Schema presence
            model_questions = [q for q in rule_set.questions if any(c.component in [TargetComponent.SEMANTIC_MODEL, TargetComponent.RELATIONSHIP] for c in q.criteria)]
            assert len(model_questions) > 0
