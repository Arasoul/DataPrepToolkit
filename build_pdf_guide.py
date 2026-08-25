"""Script to generate DataPrepToolkit_User_Guide.pdf using ReportLab."""

from __future__ import annotations

import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and render 'Page X of Y' headers and footers."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states: list[dict] = []

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count: int) -> None:
        self.saveState()
        
        # Suppress headers/footers on page 1 (Title page)
        if self._pageNumber > 1:
            # Header
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#475569"))
            self.drawString(54, 11 * 72 - 36, "DataPrepToolkit v1.1.0 — User & Technical Guide")
            
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawRightString(8.5 * 72 - 54, 11 * 72 - 36, "Production Documentation")
            
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 11 * 72 - 42, 8.5 * 72 - 54, 11 * 72 - 42)

            # Footer
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawRightString(8.5 * 72 - 54, 36, page_text)
            self.drawString(54, 36, "DataPrepToolkit — Independent Data Quality & Hygiene Layer")
            
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(54, 48, 8.5 * 72 - 54, 48)
            
        self.restoreState()


def build_pdf(filename: str = "DataPrepToolkit_User_Guide.pdf") -> None:
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    PRIMARY = colors.HexColor("#0F172A")       # Deep Slate Blue / Black
    SECONDARY = colors.HexColor("#1E3A8A")     # Royal Navy Blue
    ACCENT = colors.HexColor("#2563EB")        # Electric Blue
    SUCCESS = colors.HexColor("#059669")       # Emerald Green
    WARNING_BG = colors.HexColor("#FFFBEB")    # Amber Light Tint
    WARNING_BORDER = colors.HexColor("#F59E0B")# Amber Border
    CODE_BG = colors.HexColor("#0F172A")       # Dark Editor Background
    TEXT_DARK = colors.HexColor("#1E293B")     # Main Body Text
    TEXT_MUTED = colors.HexColor("#64748B")    # Secondary Text
    LIGHT_BG = colors.HexColor("#F8FAFC")      # Table Alt Light BG
    CARD_BG = colors.HexColor("#F1F5F9")       # Soft Card Gray

    # Typography Styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=26,
        leading=32,
        textColor=PRIMARY,
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=ACCENT,
        spaceAfter=15,
    )

    meta_style = ParagraphStyle(
        "DocMeta",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=12,
        textColor=TEXT_MUTED,
        spaceAfter=20,
    )

    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        textColor=SECONDARY,
        spaceBefore=18,
        spaceAfter=8,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=ACCENT,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=TEXT_DARK,
        spaceAfter=8,
    )

    bullet_style = ParagraphStyle(
        "BulletDark",
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4,
    )

    code_style = ParagraphStyle(
        "CodeText",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#F8FAFC"),
    )

    callout_style = ParagraphStyle(
        "CalloutText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#78350F"),
    )

    tbl_header_style = ParagraphStyle(
        "TblHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
    )

    tbl_body_style = ParagraphStyle(
        "TblBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=TEXT_DARK,
    )

    story = []

    # -------------------------------------------------------------------------
    # COVER / HEADER BANNER
    # -------------------------------------------------------------------------
    story.append(Paragraph("DataPrepToolkit", title_style))
    story.append(Paragraph("Official User Guide & Technical Reference Manual", subtitle_style))
    story.append(Paragraph("Version 1.1.0 | Python &ge; 3.11 | Pure Local & Offline Execution | 100% Deterministic", meta_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceAfter=15))

    # Executive Summary Card
    exec_summary_text = (
        "<b>Executive Overview:</b> DataPrepToolkit is a production-grade Python library designed for "
        "automated dataset profiling, data quality assessment, safe cleaning, rule validation, outlier detection, "
        "memory optimization, and quality reporting. It acts as the trustworthy foundation layer for downstream "
        "Exploratory Data Analysis (AutoEDA), analytics (AutoAnalytics), and dashboards (AutoBI)."
    )
    
    summary_table = Table(
        [[Paragraph(exec_summary_text, body_style)]],
        colWidths=[504],
    )
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('PADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 15))

    # -------------------------------------------------------------------------
    # SECTION 1: CORE PHILOSOPHY & ECOSYSTEM
    # -------------------------------------------------------------------------
    story.append(Paragraph("1. Core Philosophy & Ecosystem Architecture", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceAfter=8))
    
    p1 = (
        "DataPrepToolkit strictly operates as an independent, deterministic data preparation layer. "
        "Input DataFrames are <b>never mutated in-place</b>; every function returns a new DataFrame alongside "
        "a structured audit result object (e.g., <code>CleaningResult</code>, <code>OptimizationResult</code>, "
        "<code>ValidationResult</code>)."
    )
    story.append(Paragraph(p1, body_style))

    # Ecosystem ASCII / Flow Box Table
    eco_data = [
        [Paragraph("<b>Layer</b>", tbl_header_style), Paragraph("<b>Ecosystem Module</b>", tbl_header_style), Paragraph("<b>Primary Responsibility</b>", tbl_header_style)],
        [Paragraph("Layer 1", tbl_body_style), Paragraph("<b>DataPrepToolkit</b>", tbl_body_style), Paragraph("Data Hygiene, Quality Assessment, Cleaning, Validation, Optimization", tbl_body_style)],
        [Paragraph("Layer 2", tbl_body_style), Paragraph("<b>AutoEDA</b>", tbl_body_style), Paragraph("Exploratory Analysis, Statistical Distributions, Visual Correlations", tbl_body_style)],
        [Paragraph("Layer 3", tbl_body_style), Paragraph("<b>AutoAnalytics</b>", tbl_body_style), Paragraph("Advanced Diagnostics, Hypothesis Testing, Analytical Conclusions", tbl_body_style)],
        [Paragraph("Layer 4", tbl_body_style), Paragraph("<b>AutoBI</b>", tbl_body_style), Paragraph("Interactive Decision Dashboards & Business Communication", tbl_body_style)],
    ]
    eco_table = Table(eco_data, colWidths=[60, 110, 334])
    eco_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SECONDARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(eco_table)
    story.append(Spacer(1, 15))

    # -------------------------------------------------------------------------
    # SECTION 2: QUICK START WORKFLOW
    # -------------------------------------------------------------------------
    story.append(Paragraph("2. Installation & Quick Start", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceAfter=8))
    
    story.append(Paragraph("Install DataPrepToolkit via standard pip:", body_style))
    
    code_install = "pip install datapreptoolkit"
    t_code1 = Table([[Preformatted(code_install, code_style)]], colWidths=[504])
    t_code1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CODE_BG),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_code1)
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>30-Second Executable Workflow:</b>", h2_style))
    quick_code = (
        "import pandas as pd\n"
        "import datapreptoolkit as dpt\n\n"
        "# 1. Load CSV data safely\n"
        "df = dpt.load_csv('sales.csv')\n\n"
        "# 2. Profile dataset & generate quality score\n"
        "profile = dpt.profile_dataset(df)\n"
        "report = dpt.generate_quality_report(df)\n"
        "print(f'Quality Score: {report.overall_quality_score}/100')\n\n"
        "# 3. Run full cleaning pipeline (imputation + deduplication + datetimes)\n"
        "cleaned_df, clean_res = dpt.clean_dataset(df)\n\n"
        "# 4. Validate business constraints\n"
        "rules = [dpt.ValidationRule(column='price', rule_type='range', min_value=0.01)]\n"
        "val_res = dpt.validate_dataset(cleaned_df, rules)\n\n"
        "# 5. Export professional HTML report\n"
        "dpt.export_html_report(report, 'quality_report.html')"
    )
    t_code2 = Table([[Preformatted(quick_code, code_style)]], colWidths=[504])
    t_code2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CODE_BG),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_code2)
    story.append(Spacer(1, 15))

    # -------------------------------------------------------------------------
    # SECTION 3: REAL-WORLD SCENARIO & BEFORE/AFTER MATRIX
    # -------------------------------------------------------------------------
    story.append(KeepTogether([
        Paragraph("3. Real-World E-Commerce Scenario Walkthrough", h1_style),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceAfter=8),
        Paragraph(
            "Below is a demonstration of processing an unrefined retail order table containing duplicate transactions, "
            "missing prices, invalid negative quantities, and unoptimized memory types.",
            body_style,
        )
    ]))

    matrix_data = [
        [Paragraph("<b>Metric / Indicator</b>", tbl_header_style), Paragraph("<b>Raw Initial State</b>", tbl_header_style), Paragraph("<b>Prepared Final State</b>", tbl_header_style), Paragraph("<b>Action Taken / Impact</b>", tbl_header_style)],
        [Paragraph("Row Count", tbl_body_style), Paragraph("8 rows", tbl_body_style), Paragraph("6 rows", tbl_body_style), Paragraph("Removed 1 duplicate row & 1 invalid negative row", tbl_body_style)],
        [Paragraph("Column Count", tbl_body_style), Paragraph("6 columns", tbl_body_style), Paragraph("6 columns", tbl_body_style), Paragraph("All required schema columns preserved", tbl_body_style)],
        [Paragraph("Missing Cells", tbl_body_style), Paragraph("3 missing cells", tbl_body_style), Paragraph("0 missing cells", tbl_body_style), Paragraph("Median imputed for price, mode for region", tbl_body_style)],
        [Paragraph("Duplicate Rows", tbl_body_style), Paragraph("1 duplicate row", tbl_body_style), Paragraph("0 duplicate rows", tbl_body_style), Paragraph("Deduplicated on primary order key", tbl_body_style)],
        [Paragraph("Datetime Types", tbl_body_style), Paragraph("0 (object string)", tbl_body_style), Paragraph("1 (datetime64[ns])", tbl_body_style), Paragraph("Parsed order_date to timestamp cleanly", tbl_body_style)],
        [Paragraph("Memory Footprint", tbl_body_style), Paragraph("900 Bytes", tbl_body_style), Paragraph("420 Bytes", tbl_body_style), Paragraph("Down-casted int/float and string to category (53.3% savings)", tbl_body_style)],
        [Paragraph("Quality Score", tbl_body_style), Paragraph("78.20 / 100", tbl_body_style), Paragraph("98.50 / 100", tbl_body_style), Paragraph("+20.30 Quality Score Improvement", tbl_body_style)],
    ]
    matrix_table = Table(matrix_data, colWidths=[90, 80, 85, 249])
    matrix_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SECONDARY),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(matrix_table)
    story.append(Spacer(1, 15))

    # -------------------------------------------------------------------------
    # SECTION 4: FEATURE GUIDES & STRATEGIES
    # -------------------------------------------------------------------------
    story.append(Paragraph("4. Feature Guides & Strategy Reference", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceAfter=8))

    # 4.1 Missing Values
    story.append(Paragraph("A. Missing Value Imputation Strategies", h2_style))
    mv_text = (
        "<code>handle_missing_values()</code> supports 10 distinct imputation strategies. "
        "When using <code>strategy='drop_column'</code>, columns are dropped <b>only</b> if their null ratio "
        "exceeds <code>drop_threshold</code> (default 0.6 = 60%). Columns below the threshold safely fall back to mode imputation."
    )
    story.append(Paragraph(mv_text, body_style))

    mv_table_data = [
        [Paragraph("<b>Strategy</b>", tbl_header_style), Paragraph("<b>Target Type</b>", tbl_header_style), Paragraph("<b>Behavior Description</b>", tbl_header_style)],
        [Paragraph("<code>median</code> (default)", tbl_body_style), Paragraph("Numeric", tbl_body_style), Paragraph("Fills numeric nulls with median. Non-numeric columns fall back to <code>mode</code>.", tbl_body_style)],
        [Paragraph("<code>mean</code>", tbl_body_style), Paragraph("Symmetric Numeric", tbl_body_style), Paragraph("Fills numeric nulls with mean. Non-numeric columns fall back to <code>mode</code>.", tbl_body_style)],
        [Paragraph("<code>mode</code>", tbl_body_style), Paragraph("Categorical / String", tbl_body_style), Paragraph("Fills nulls with the single most frequent value.", tbl_body_style)],
        [Paragraph("<code>ffill</code> / <code>bfill</code>", tbl_body_style), Paragraph("Time-Series", tbl_body_style), Paragraph("Forward-fills or backward-fills missing values sequentially.", tbl_body_style)],
        [Paragraph("<code>interpolate</code>", tbl_body_style), Paragraph("Ordered Numeric", tbl_body_style), Paragraph("Linear interpolation for numeric; forward-fill for categoricals.", tbl_body_style)],
        [Paragraph("<code>drop_rows</code>", tbl_body_style), Paragraph("Critical Target", tbl_body_style), Paragraph("Drops any row containing a null value in specified columns.", tbl_body_style)],
        [Paragraph("<code>drop_column</code>", tbl_body_style), Paragraph("Heavy Missing (>60%)", tbl_body_style), Paragraph("Drops column if null ratio > threshold. Otherwise imputes with mode.", tbl_body_style)],
        [Paragraph("<code>zero</code> / <code>empty</code>", tbl_body_style), Paragraph("Sparse / Text", tbl_body_style), Paragraph("Fills numeric nulls with 0 and categorical nulls with 'Unknown'.", tbl_body_style)],
    ]
    mv_table = Table(mv_table_data, colWidths=[90, 85, 329])
    mv_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SECONDARY),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(mv_table)
    story.append(Spacer(1, 12))

    # 4.2 Outliers
    story.append(Paragraph("B. Outlier Detection Mechanics", h2_style))
    outlier_text = (
        "DataPrepToolkit provides read-only outlier detection via IQR and Z-Score (Standard and Modified MAD-based). "
        "Infinities (<code>inf</code> / <code>-inf</code>) are isolated so they do not corrupt finite bounds."
    )
    story.append(Paragraph(outlier_text, body_style))

    # Outlier Warning Callout Table
    callout_data = [[
        Paragraph(
            "<b>IMPORTANT RULE: Outlier Detection &ne; Outlier Deletion.</b><br/>"
            "DataPrepToolkit flags outlier row indices programmatically without deleting rows. "
            "An outlier may represent a high-value transaction or fraud signal that must be analyzed rather than deleted.",
            callout_style,
        )
    ]]
    callout_table = Table(callout_data, colWidths=[504])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), WARNING_BG),
        ('BOX', (0, 0), (-1, -1), 1, WARNING_BORDER),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(callout_table)
    story.append(Spacer(1, 12))

    # 4.3 Validation Rules
    story.append(Paragraph("C. Rule-Based Validation System", h2_style))
    val_text = (
        "Declarative validation via <code>ValidationRule</code> checks DataFrames against business constraints "
        "and returns a <code>ValidationResult</code> detailing any <code>ValidationViolation</code>s."
    )
    story.append(Paragraph(val_text, body_style))

    val_code = (
        "from datapreptoolkit import validate_dataset, ValidationRule\n\n"
        "rules = [\n"
        "    ValidationRule(column='order_id', rule_type='required'),\n"
        "    ValidationRule(column='order_id', rule_type='no_duplicates'),\n"
        "    ValidationRule(column='age', rule_type='range', min_value=18, max_value=65),\n"
        "    ValidationRule(column='email', rule_type='regex', pattern=r'^[\\w.-]+@[\\w.-]+\\.\\w+$'),\n"
        "    ValidationRule(column='status', rule_type='in_set', allowed_values={'active', 'pending'}),\n"
        "]\n"
        "result = validate_dataset(df, rules)"
    )
    t_val_code = Table([[Preformatted(val_code, code_style)]], colWidths=[504])
    t_val_code.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CODE_BG),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_val_code)
    story.append(Spacer(1, 15))

    # -------------------------------------------------------------------------
    # SECTION 5: CONFIGURATION & SCORING
    # -------------------------------------------------------------------------
    story.append(KeepTogether([
        Paragraph("5. Configuration & Quality Scoring Mechanics", h1_style),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceAfter=8),
        Paragraph(
            "The composite Quality Score (0–100) starts at 100.0 and deducts weighted penalties defined in "
            "<code>ToolkitConfig.quality_weights</code>:",
            body_style,
        )
    ]))

    formula_text = (
        "<b>Quality Score Formula:</b><br/>"
        "Score = 100.0 - [(missing / total_cells) &times; W_missing] - [(duplicates / rows) &times; W_dup] "
        "- [N_const &times; W_const] - [N_high_card &times; W_card] - [N_outlier &times; W_outlier]"
    )
    t_formula = Table([[Paragraph(formula_text, body_style)]], colWidths=[504])
    t_formula.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_formula)
    story.append(Spacer(1, 12))

    cfg_code = (
        "from datapreptoolkit import ToolkitConfig, EncodingStrategy, ZScoreMethod\n\n"
        "config = ToolkitConfig(\n"
        "    remove_duplicates=True,\n"
        "    parse_datetimes=True,\n"
        "    optimise_memory=True,\n"
        "    detect_outliers=True,\n"
        "    outlier_method='zscore',\n"
        "    zscore_method=ZScoreMethod.MODIFIED,\n"
        "    encoding_strategy=EncodingStrategy.LABEL,\n"
        "    high_cardinality_threshold=0.95,\n"
        "    constant_threshold=0.99,\n"
        "    quality_weights={\n"
        "        'missing': 40.0, 'duplicate': 20.0, 'constant': 2.0,\n"
        "        'high_cardinality': 1.0, 'outlier': 3.0,\n"
        "    },\n"
        ")"
    )
    t_cfg_code = Table([[Preformatted(cfg_code, code_style)]], colWidths=[504])
    t_cfg_code.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CODE_BG),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_cfg_code)
    story.append(Spacer(1, 15))

    # -------------------------------------------------------------------------
    # SECTION 6: DECISION MATRIX & API CATALOG
    # -------------------------------------------------------------------------
    story.append(KeepTogether([
        Paragraph("6. Feature Decision Matrix & API Catalog", h1_style),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceAfter=8),
    ]))

    dec_data = [
        [Paragraph("<b>Goal / Task</b>", tbl_header_style), Paragraph("<b>Function to Call</b>", tbl_header_style), Paragraph("<b>Returned Object Type</b>", tbl_header_style)],
        [Paragraph("Load CSV safely", tbl_body_style), Paragraph("<code>load_csv(filepath)</code>", tbl_body_style), Paragraph("<code>pd.DataFrame</code>", tbl_body_style)],
        [Paragraph("Profile shape & metadata", tbl_body_style), Paragraph("<code>profile_dataset(df)</code>", tbl_body_style), Paragraph("<code>DatasetProfile</code>", tbl_body_style)],
        [Paragraph("Analyze missing cells", tbl_body_style), Paragraph("<code>analyze_missing_values(df)</code>", tbl_body_style), Paragraph("<code>MissingValueAnalysis</code>", tbl_body_style)],
        [Paragraph("Impute missing cells", tbl_body_style), Paragraph("<code>handle_missing_values(df)</code>", tbl_body_style), Paragraph("<code>(pd.DataFrame, CleaningResult)</code>", tbl_body_style)],
        [Paragraph("Deduplicate rows", tbl_body_style), Paragraph("<code>remove_duplicates(df)</code>", tbl_body_style), Paragraph("<code>(pd.DataFrame, CleaningResult)</code>", tbl_body_style)],
        [Paragraph("Detect invalid values", tbl_body_style), Paragraph("<code>detect_invalid_values(df)</code>", tbl_body_style), Paragraph("<code>(dict, CleaningResult)</code>", tbl_body_style)],
        [Paragraph("Detect outliers", tbl_body_style), Paragraph("<code>detect_outliers(df)</code>", tbl_body_style), Paragraph("<code>OutlierDetection</code>", tbl_body_style)],
        [Paragraph("Downcast memory", tbl_body_style), Paragraph("<code>optimise_memory(df)</code>", tbl_body_style), Paragraph("<code>(pd.DataFrame, OptimizationResult)</code>", tbl_body_style)],
        [Paragraph("Validate data rules", tbl_body_style), Paragraph("<code>validate_dataset(df, rules)</code>", tbl_body_style), Paragraph("<code>ValidationResult</code>", tbl_body_style)],
        [Paragraph("Generate quality score", tbl_body_style), Paragraph("<code>generate_quality_report(df)</code>", tbl_body_style), Paragraph("<code>QualityReport</code>", tbl_body_style)],
        [Paragraph("Export HTML report", tbl_body_style), Paragraph("<code>export_html_report(report)</code>", tbl_body_style), Paragraph("<code>str</code> (File Path)", tbl_body_style)],
    ]
    dec_table = Table(dec_data, colWidths=[130, 174, 200])
    dec_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SECONDARY),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(dec_table)
    story.append(Spacer(1, 15))

    # -------------------------------------------------------------------------
    # SECTION 7: EXCEPTION HIERARCHY & ROBUSTNESS
    # -------------------------------------------------------------------------
    story.append(Paragraph("7. Exception Hierarchy & Hardened Robustness", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceAfter=8))

    exc_tree = (
        "DataPrepError (Base)\n"
        "├── LoadError (FileFormatError, EmptyDatasetError)\n"
        "├── CleaningError (InvalidColumnError, IncompatibleDataError)\n"
        "├── ValidationError (QualityThresholdError)\n"
        "├── ReportError\n"
        "└── ConfigError"
    )
    t_exc = Table([[Preformatted(exc_tree, code_style)]], colWidths=[504])
    t_exc.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CODE_BG),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_exc)
    story.append(Spacer(1, 10))

    rob_text = (
        "<b>Verified Edge Case Handling:</b> DataPrepToolkit has been systematically tested across 20 distinct dataset "
        "archetypes (Datasets A–T). It cleanly handles empty DataFrames (0 rows), single-row DataFrames, single-column DataFrames, "
        "all-null columns, constant columns, extreme outliers, infinite values (<code>inf</code>/<code>-inf</code>), mixed `np.nan`/`None` representations, "
        "and non-English UTF-8 headers (Arabic, Spanish, Japanese) without unhandled crashes."
    )
    story.append(Paragraph(rob_text, body_style))

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated professional PDF guide: {filename}")


if __name__ == "__main__":
    build_pdf()
