"""
DAX Analyzer and Normalizer for Power BI Evaluation.
Performs semantic normalization, tokenization, component extraction, and equivalent formula matching.
"""
import re
from typing import Dict, Any, List, Set, Optional, Tuple


class DAXAnalyzer:
    """Analyzes and compares DAX expressions deterministically."""

    @staticmethod
    def strip_comments(dax: str) -> str:
        if not dax:
            return ""
        # Remove /* multi-line comments */
        dax = re.sub(r"/\*.*?\*/", " ", dax, flags=re.DOTALL)
        # Remove // single-line comments
        dax = re.sub(r"//.*$", "", dax, flags=re.MULTILINE)
        # Remove -- single-line comments
        dax = re.sub(r"--.*$", "", dax, flags=re.MULTILINE)
        return dax

    @staticmethod
    def normalize_dax(dax: str) -> str:
        """Normalizes formatting, whitespace, brackets, and case."""
        if not dax:
            return ""
        cleaned = DAXAnalyzer.strip_comments(dax)
        
        # Remove leading measure definition if present e.g. "Total Sales = ..." or "Total Sales:="
        cleaned = re.sub(r"^[^=:]+[:=]+\s*", "", cleaned.strip())

        # Replace multiple whitespaces/newlines with single space
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        return cleaned

    @staticmethod
    def canonicalize_expression(dax: str) -> str:
        """
        Transforms DAX into a canonical format:
        - Removes table prefixes from column references: 'Sales'[Amount] -> [amount]
        - Standardizes function names to uppercase
        - Normalizes quotes
        """
        if not dax:
            return ""
        cleaned = DAXAnalyzer.normalize_dax(dax)

        # Normalize 'Table'[Column] or Table[Column] -> [column]
        cleaned = re.sub(r"'?[A-Za-z0-9_ ]+'?\[([A-Za-z0-9_ ]+)\]", r"[\1]", cleaned)

        # Remove spaces around operators & delimiters
        cleaned = re.sub(r"\s*([(),+\-*/=<>])\s*", r"\1", cleaned)

        # Convert to lowercase for comparison
        return cleaned.lower().strip()

    @staticmethod
    def extract_referenced_columns_and_measures(dax: str) -> Tuple[Set[str], Set[str]]:
        """Extracts column references [Col] and measure/function calls."""
        if not dax:
            return set(), set()
        
        cleaned = DAXAnalyzer.strip_comments(dax)
        
        # Matches [ColumnOrMeasureName]
        bracket_refs = set(re.findall(r"\[([A-Za-z0-9_ ]+)\]", cleaned))
        
        # Matches FunctionName(
        function_calls = set(re.findall(r"([A-Za-z_][A-Za-z0-9_.]*)\s*\(", cleaned, re.IGNORECASE))
        function_calls = {f.upper() for f in function_calls}

        return bracket_refs, function_calls

    @staticmethod
    def is_equivalent(
        student_dax: str,
        expected_dax: str,
        accepted_variations: Optional[List[str]] = None,
    ) -> Tuple[bool, str]:
        """
        Determines if student DAX meets expected requirements or accepted variations.
        Returns (is_match, reason).
        """
        if not student_dax:
            return False, "No DAX expression found in student submission."
        if not expected_dax:
            return True, "No specific expected DAX defined."

        std_student = DAXAnalyzer.canonicalize_expression(student_dax)
        std_expected = DAXAnalyzer.canonicalize_expression(expected_dax)

        # 1. Exact canonical match
        if std_student == std_expected:
            return True, "DAX expression exactly matches expected logic."

        # 2. Check accepted variations
        if accepted_variations:
            for variation in accepted_variations:
                std_var = DAXAnalyzer.canonicalize_expression(variation)
                if std_student == std_var:
                    return True, f"DAX matches accepted variation: '{variation}'."

        # 3. Check semantic equivalences
        student_cols, student_funcs = DAXAnalyzer.extract_referenced_columns_and_measures(student_dax)
        expected_cols, expected_funcs = DAXAnalyzer.extract_referenced_columns_and_measures(expected_dax)

        # Example: DIVIDE with optional 0 alternate result e.g. DIVIDE([A], [B]) vs DIVIDE([A], [B], 0)
        if "DIVIDE" in expected_funcs and "DIVIDE" in student_funcs:
            # Check if columns match
            if expected_cols.issubset(student_cols):
                return True, "DAX uses DIVIDE with matching terms."

        # Example: CALCULATE with filter variations
        if "CALCULATE" in expected_funcs and "CALCULATE" in student_funcs:
            if expected_cols.issubset(student_cols):
                return True, "DAX correctly applies CALCULATE on required fields."

        # Example: SUM / SUMX equivalent
        if any(f in expected_funcs for f in ["SUM", "SUMX"]) and any(f in student_funcs for f in ["SUM", "SUMX"]):
            if expected_cols.issubset(student_cols) and len(expected_cols) > 0:
                return True, "DAX correctly aggregates the required column."

        return False, f"Expected logic equivalent to '{expected_dax}', but found '{student_dax}'."
