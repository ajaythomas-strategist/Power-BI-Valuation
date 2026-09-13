"""
Sample Test Fixtures and Generator for Power BI Answer Evaluator.
Contains realistic Question Paper, Answer Key, and 5 student PBIP submissions.
"""
import io
import json
import zipfile
from typing import Dict, Any


def get_sample_question_paper() -> str:
    return """# Power BI Practical Assessment: Sales & Performance Analytics
**Duration:** 90 Minutes | **Total Marks:** 100 Marks

## Instructions:
1. Save your Power BI project in PBIP format.
2. Build the semantic model, relationships, DAX measures, and visual report pages as specified below.
3. Name your project submission folder using your Register Number (e.g., `23001`).

---

### Question 1: Sales Trend Analysis (25 Marks)
Create a **Line Chart** on Page 1 showing **Total Sales** over **Date** (Date Hierarchy or Date column is accepted).
- Visual Type: Line Chart
- X-Axis: Date (or Date Hierarchy)
- Y-Axis: Total Sales

### Question 2: Total Sales DAX Measure (25 Marks)
Create a DAX Measure named `Total Sales` calculating the sum of sales amount from the `Sales` table.
- Formula: `Total Sales = SUM(Sales[Amount])`

### Question 3: Profit Margin Calculation (25 Marks)
Create a DAX Measure named `Profit Margin` calculating the ratio of Total Profit over Total Sales using the `DIVIDE` function.
- Formula: `Profit Margin = DIVIDE([Total Profit], [Total Sales], 0)`

### Question 4: Category Performance Breakdown (25 Marks)
Create a **Clustered Bar Chart** comparing **Total Sales** by **Product Category**.
- Visual Type: Clustered Bar Chart
- Y-Axis / Category: Product Category
- X-Axis / Values: Total Sales
"""


def get_sample_answer_key() -> Dict[str, Any]:
    return {
        "title": "Sales & Performance Analytics - Official Answer Key",
        "total_marks": 100.0,
        "questions": [
            {
                "question_id": "Q1",
                "question_text": "Create a Line chart showing Total Sales by Date (Date Hierarchy / Date is accepted).",
                "marks": 25.0,
                "accepted_variations": ["Date", "Date Hierarchy", "OrderDate", "Order Date", "Date.Year"],
                "criteria": [
                    {
                        "id": "Q1_C1",
                        "title": "Visual Type is Line Chart",
                        "component": "Visual",
                        "target_property": "visual_type",
                        "expected_value": "Line Chart",
                        "accepted_variations": ["LineChart", "Line"],
                        "marks": 10.0,
                    },
                    {
                        "id": "Q1_C2",
                        "title": "X-Axis uses Date or Date Hierarchy",
                        "component": "Visual",
                        "target_property": "x_axis",
                        "expected_value": "Date",
                        "accepted_variations": ["Date Hierarchy", "OrderDate", "Order Date", "Date.Year", "Date Hierarchy (Year)"],
                        "marks": 8.0,
                    },
                    {
                        "id": "Q1_C3",
                        "title": "Y-Axis uses Total Sales",
                        "component": "Visual",
                        "target_property": "y_axis",
                        "expected_value": "Total Sales",
                        "accepted_variations": ["Sales Amount", "Sales.Amount"],
                        "marks": 7.0,
                    },
                ],
            },
            {
                "question_id": "Q2",
                "question_text": "Create a DAX Measure named Total Sales = SUM(Sales[Amount]).",
                "marks": 25.0,
                "criteria": [
                    {
                        "id": "Q2_C1",
                        "title": "DAX Measure: Total Sales",
                        "component": "DAX Measure",
                        "target_property": "dax_formula",
                        "expected_value": "SUM(Sales[Amount])",
                        "accepted_variations": [
                            "SUM('Sales'[Amount])",
                            "SUM([Amount])",
                            "SUMX(Sales, Sales[Amount])",
                            "SUMX('Sales', 'Sales'[Amount])",
                        ],
                        "marks": 25.0,
                    }
                ],
            },
            {
                "question_id": "Q3",
                "question_text": "Create a DAX Measure named Profit Margin = DIVIDE([Total Profit], [Total Sales], 0).",
                "marks": 25.0,
                "criteria": [
                    {
                        "id": "Q3_C1",
                        "title": "DAX Measure: Profit Margin",
                        "component": "DAX Measure",
                        "target_property": "dax_formula",
                        "expected_value": "DIVIDE([Total Profit], [Total Sales], 0)",
                        "accepted_variations": [
                            "DIVIDE([Total Profit], [Total Sales])",
                            "DIVIDE(SUM(Sales[Profit]), SUM(Sales[Amount]), 0)",
                            "DIVIDE(SUM(Sales[Profit]), SUM(Sales[Amount]))",
                            "DIVIDE('Sales'[Total Profit], 'Sales'[Total Sales])",
                        ],
                        "marks": 25.0,
                    }
                ],
            },
            {
                "question_id": "Q4",
                "question_text": "Create a Clustered Bar Chart comparing Total Sales by Product Category.",
                "marks": 25.0,
                "criteria": [
                    {
                        "id": "Q4_C1",
                        "title": "Visual Type is Clustered Bar Chart",
                        "component": "Visual",
                        "target_property": "visual_type",
                        "expected_value": "Clustered Bar Chart",
                        "accepted_variations": ["Bar Chart", "ClusteredBarChart", "BarChart"],
                        "marks": 10.0,
                    },
                    {
                        "id": "Q4_C2",
                        "title": "Category / Axis is Product Category",
                        "component": "Visual",
                        "target_property": "x_axis",
                        "expected_value": "Product Category",
                        "accepted_variations": ["Category", "Product[Category]", "Products.Category"],
                        "marks": 8.0,
                    },
                    {
                        "id": "Q4_C3",
                        "title": "Values is Total Sales",
                        "component": "Visual",
                        "target_property": "y_axis",
                        "expected_value": "Total Sales",
                        "accepted_variations": ["Sales Amount"],
                        "marks": 7.0,
                    },
                ],
            },
        ],
    }


def create_sample_dataset_archive() -> bytes:
    """Creates an in-memory ZIP archive containing 5 sample student folders."""
    buf = io.BytesIO()

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        # 1. Student 23001 (100% - Perfect score, uses Date Hierarchy)
        z.writestr("23001/Sales_Project.pbip", json.dumps({"version": "1.0", "artifacts": [{"report": {"path": "Sales.Report"}}] }))
        
        report_23001 = {
            "sections": [
                {
                    "name": "Page1",
                    "displayName": "Overview",
                    "visualContainers": [
                        {
                            "config": json.dumps({
                                "name": "vis_line_q1",
                                "singleVisual": {
                                    "visualType": "lineChart",
                                    "projections": {
                                        "Category": [{"queryRef": "Min(Sales.Date.(DateHierarchy).(Year))"}],
                                        "Y": [{"queryRef": "Sales.Total Sales"}],
                                    },
                                    "objects": {"title": [{"properties": {"text": {"expr": {"Literal": {"Value": "'Sales Trend'"}}}}}]},
                                }
                            })
                        },
                        {
                            "config": json.dumps({
                                "name": "vis_bar_q4",
                                "singleVisual": {
                                    "visualType": "clusteredBarChart",
                                    "projections": {
                                        "Category": [{"queryRef": "Products.Product Category"}],
                                        "Values": [{"queryRef": "Sales.Total Sales"}],
                                    },
                                }
                            })
                        }
                    ]
                }
            ]
        }
        z.writestr("23001/Sales.Report/report.json", json.dumps(report_23001))

        model_23001 = {
            "model": {
                "tables": [
                    {
                        "name": "Sales",
                        "columns": [{"name": "Amount", "dataType": "decimal"}, {"name": "Profit", "dataType": "decimal"}, {"name": "Date", "dataType": "dateTime"}],
                        "measures": [
                            {"name": "Total Sales", "expression": "SUM(Sales[Amount])"},
                            {"name": "Total Profit", "expression": "SUM(Sales[Profit])"},
                            {"name": "Profit Margin", "expression": "DIVIDE([Total Profit], [Total Sales], 0)"},
                        ],
                    },
                    {
                        "name": "Products",
                        "columns": [{"name": "ProductID", "dataType": "int64"}, {"name": "Product Category", "dataType": "string"}],
                        "measures": [],
                    }
                ],
                "relationships": [
                    {"fromTable": "Sales", "fromColumn": "ProductID", "toTable": "Products", "toColumn": "ProductID", "cardinality": "manyToOne"}
                ]
            }
        }
        z.writestr("23001/Sales.Dataset/model.bim", json.dumps(model_23001))

        # 2. Student 23002 (82% - Q1, Q2, Q3 full marks, Q4 partial 7 marks)
        z.writestr("23002/MySubmission.pbip", json.dumps({"version": "1.0"}))
        report_23002 = {
            "sections": [
                {
                    "name": "Page1",
                    "displayName": "Report",
                    "visualContainers": [
                        {
                            "config": json.dumps({
                                "name": "vis_1",
                                "singleVisual": {
                                    "visualType": "lineChart",
                                    "projections": {
                                        "Category": [{"queryRef": "Sales.Date"}],
                                        "Y": [{"queryRef": "Sales.Total Sales"}],
                                    }
                                }
                            })
                        }
                    ]
                }
            ]
        }
        z.writestr("23002/MySubmission.Report/report.json", json.dumps(report_23002))
        model_23002 = {
            "model": {
                "tables": [
                    {
                        "name": "Sales",
                        "columns": [{"name": "Amount", "dataType": "decimal"}, {"name": "Date", "dataType": "dateTime"}],
                        "measures": [
                            {"name": "Total Sales", "expression": "SUM('Sales'[Amount])"},
                            {"name": "Total Profit", "expression": "SUM('Sales'[Profit])"},
                            {"name": "Profit Margin", "expression": "DIVIDE([Total Profit], [Total Sales])"},
                        ],
                    }
                ]
            }
        }
        z.writestr("23002/MySubmission.Dataset/model.bim", json.dumps(model_23002))

        # 3. Student 23003 (39% - Q1 partial 7 marks, Q2 25 marks, Q3 wrong DAX 0 marks, Q4 partial 7 marks)
        z.writestr("23003/StudentAnswer.pbip", json.dumps({"version": "1.0"}))
        report_23003 = {
            "sections": [
                {
                    "name": "Page1",
                    "displayName": "Page 1",
                    "visualContainers": [
                        {
                            "config": json.dumps({
                                "name": "pie_vis",
                                "singleVisual": {
                                    "visualType": "pieChart",
                                    "projections": {
                                        "Category": [{"queryRef": "Sales.Region"}],
                                        "Y": [{"queryRef": "Sales.Total Sales"}],
                                    }
                                }
                            })
                        }
                    ]
                }
            ]
        }
        z.writestr("23003/StudentAnswer.Report/report.json", json.dumps(report_23003))
        model_23003 = {
            "model": {
                "tables": [
                    {
                        "name": "Sales",
                        "columns": [{"name": "Amount", "dataType": "decimal"}],
                        "measures": [
                            {"name": "Total Sales", "expression": "SUM(Sales[Amount])"},
                            {"name": "Profit Margin", "expression": "[Total Profit] - [Total Sales]"},
                        ],
                    }
                ]
            }
        }
        z.writestr("23003/StudentAnswer.Dataset/model.bim", json.dumps(model_23003))

        # 4. Student 23004 (Exception: Missing PBIP / empty submission)
        z.writestr("23004/notes.txt", "Forgot to save PBIP before submitting.")

        # 5. Student 23005 (Exception: Corrupted folder)
        z.writestr("23005/damaged.pbip", "{invalid_json: true,,}")

    buf.seek(0)
    return buf.getvalue()
