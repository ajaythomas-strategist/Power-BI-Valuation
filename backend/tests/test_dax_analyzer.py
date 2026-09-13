"""
Unit tests for DAX Analyzer.
"""
import pytest
from app.parsers.dax_analyzer import DAXAnalyzer


def test_dax_comment_stripping():
    dax = """
    // Calculate total sales
    Total Sales = 
    /* Multi-line comment */
    SUM(Sales[Amount]) -- trailing comment
    """
    cleaned = DAXAnalyzer.strip_comments(dax)
    assert "//" not in cleaned
    assert "/*" not in cleaned
    assert "--" not in cleaned
    assert "SUM(Sales[Amount])" in cleaned


def test_dax_normalization():
    dax = "  Total Sales   =   SUM(   Sales[Amount]   )  "
    norm = DAXAnalyzer.normalize_dax(dax)
    assert norm == "SUM( Sales[Amount] )"


def test_dax_canonicalization():
    expr1 = "SUM('Sales'[Amount])"
    expr2 = "sum(Sales[Amount])"
    expr3 = "SUM([Amount])"
    assert DAXAnalyzer.canonicalize_expression(expr1) == "sum([amount])"
    assert DAXAnalyzer.canonicalize_expression(expr2) == "sum([amount])"
    assert DAXAnalyzer.canonicalize_expression(expr3) == "sum([amount])"


def test_dax_equivalence_exact():
    student = "SUM('Sales'[Amount])"
    expected = "SUM(Sales[Amount])"
    is_eq, reason = DAXAnalyzer.is_equivalent(student, expected)
    assert is_eq is True


def test_dax_equivalence_accepted_variations():
    student = "SUMX('Sales', 'Sales'[Amount])"
    expected = "SUM(Sales[Amount])"
    variations = ["SUMX(Sales, Sales[Amount])", "SUMX('Sales', 'Sales'[Amount])"]
    is_eq, reason = DAXAnalyzer.is_equivalent(student, expected, accepted_variations=variations)
    assert is_eq is True
    assert "variation" in reason.lower() or "matches" in reason.lower()


def test_dax_divide_equivalence():
    student = "DIVIDE([Total Profit], [Total Sales])"
    expected = "DIVIDE([Total Profit], [Total Sales], 0)"
    is_eq, reason = DAXAnalyzer.is_equivalent(student, expected)
    assert is_eq is True


def test_dax_incorrect_mismatch():
    student = "[Total Profit] - [Total Sales]"
    expected = "DIVIDE([Total Profit], [Total Sales], 0)"
    is_eq, reason = DAXAnalyzer.is_equivalent(student, expected)
    assert is_eq is False
