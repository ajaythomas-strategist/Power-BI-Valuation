"""
Unit tests for Answer Key Parser.
"""
import pytest
from app.parsers.answer_key_parser import AnswerKeyParser


def test_parse_json_answer_key():
    json_content = """
    {
        "title": "Exam 1",
        "total_marks": 20,
        "questions": [
            {
                "question_id": "Q1",
                "question_text": "Create a Line Chart of Sales by Date",
                "marks": 10,
                "visual_type": "Line Chart",
                "x_axis": "Date",
                "y_axis": "Sales",
                "accepted_variations": ["Date Hierarchy"]
            },
            {
                "question_id": "Q2",
                "question_text": "Create Measure Total Sales",
                "marks": 10,
                "measure_name": "Total Sales",
                "dax": "SUM(Sales[Amount])"
            }
        ]
    }
    """
    rule_set = AnswerKeyParser.parse_content(json_content, "answer_key.json")
    assert rule_set.total_marks == 20
    assert len(rule_set.questions) == 2
    assert rule_set.questions[0].question_id == "Q1"
    assert len(rule_set.questions[0].criteria) >= 3


def test_parse_yaml_answer_key():
    yaml_content = """
    title: YAML Exam
    total_marks: 10
    questions:
      - question_id: Q1
        question_text: Create Line Chart
        marks: 10
        visual_type: Line Chart
    """
    rule_set = AnswerKeyParser.parse_content(yaml_content, "answer_key.yaml")
    assert len(rule_set.questions) == 1
    assert rule_set.questions[0].question_id == "Q1"


def test_parse_csv_answer_key():
    csv_content = "Question ID,Question,Marks,Visual Type,X Axis,Y Axis\nQ1,Sales Trend,10,Line Chart,Date,Sales\n"
    rule_set = AnswerKeyParser.parse_content(csv_content, "answer_key.csv")
    assert len(rule_set.questions) == 1
    assert rule_set.questions[0].question_id == "Q1"
