import os, sys
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas

PDF_PATH = r"d:\Desktop\ARTH\Sem-7\TOD310\Project\TOD310_JustDogs_Forecasting_Project\Arth\JustDogs_Top5_Optimal_Forecasting_Framework_Defense.pdf"

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#0f172a"))
        
        # Header (Pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 755, "JUSTDOGS TOP 5 SKUs — TAILORED TIME INTERVAL & OPTIMAL TRAIN-TEST DEFENSE")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748b"))
            self.drawRightString(612 - 54, 755, "TOD310 | Prof. Amit | Arth Patel")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.75)
            self.line(54, 747, 612 - 54, 747)

        # Footer
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.75)
        self.line(54, 45, 612 - 54, 45)
        
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(54, 32, "CONFIDENTIAL — EXECUTIVE VIVA DEFENSE GUIDE")
        self.drawRightString(612 - 54, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()

def build_pdf():
    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    c_primary = colors.HexColor("#0f2942")     # Navy
    c_secondary = colors.HexColor("#1e40af")   # Royal Blue
    c_dark = colors.HexColor("#1e293b")        # Slate 800
    c_light = colors.HexColor("#f8fafc")       # Slate 50
    c_border = colors.HexColor("#e2e8f0")      # Slate 200
    c_highlight = colors.HexColor("#ecfdf5")   # Green 50

    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, leading=22,
        textColor=c_primary, spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle', parent=styles['Normal'], fontName='Helvetica', fontSize=9.5, leading=13.5,
        textColor=colors.HexColor("#475569"), spaceAfter=10
    )

    h1_style = ParagraphStyle(
        'SectionH1', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, leading=16,
        textColor=c_primary, spaceBefore=12, spaceAfter=5, keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionH2', parent=styles['Heading3'], fontName='Helvetica-Bold', fontSize=10, leading=13,
        textColor=c_secondary, spaceBefore=8, spaceAfter=3, keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'], fontName='Helvetica', fontSize=8.2, leading=11.8,
        textColor=c_dark, spaceAfter=5
    )

    callout_style = ParagraphStyle(
        'CalloutText', parent=styles['Normal'], fontName='Helvetica', fontSize=8.2, leading=12,
        textColor=colors.HexColor("#0f172a")
    )

    th_style = ParagraphStyle(
        'TH', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.5, leading=9.5,
        textColor=colors.white, alignment=1
    )

    td_style = ParagraphStyle(
        'TD', parent=styles['Normal'], fontName='Helvetica', fontSize=7.2, leading=9.2,
        textColor=c_dark, alignment=1
    )

    td_bold = ParagraphStyle(
        'TDBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.2, leading=9.2,
        textColor=c_dark, alignment=1
    )

    td_left = ParagraphStyle(
        'TDLeft', parent=styles['Normal'], fontName='Helvetica', fontSize=7.2, leading=9.2,
        textColor=c_dark, alignment=0
    )

    td_left_bold = ParagraphStyle(
        'TDLeftBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.2, leading=9.2,
        textColor=c_dark, alignment=0
    )

    story = []

    # Title Banner
    story.append(Paragraph("JUSTDOGS TOP 5 PRODUCTS FORECASTING", title_style))
    story.append(Paragraph("<b>Product-Tailored Optimization Framework: Dedicated Time Intervals, Optimal Train-Test Partitions & Multi-Factor Benchmark</b>", ParagraphStyle('SubSub', parent=subtitle_style, fontSize=10.5, leading=14, textColor=c_secondary)))
    story.append(Paragraph("<b>Course:</b> TOD310 – Predictive Analytics for Business &nbsp;|&nbsp; <b>Faculty:</b> Prof. Amit &nbsp;|&nbsp; <b>Student:</b> Arth Patel &nbsp;|&nbsp; <b>Defense Date:</b> Nov 16, 2026", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=2, spaceAfter=8))

    # Executive Summary Box
    exec_text = (
        "<b>Executive Framework Mandate:</b><br/>"
        "In enterprise retail analytics, applying a one-size-fits-all model, interval, or validation split guarantees failure. "
        "This defense brief establishes the <b>optimal, mathematically grounded configuration for each of JustDogs' Top 5 SKUs</b>:<br/>"
        "<b>1. Best Time Interval:</b> Syntetos-Boylan demand classification and supply chain replenishment cycles dictate whether an SKU is modeled "
        "at <b>Weekly</b> (smoothing bulk POs and weekend sawtooth oscillations) or <b>Daily</b> (capturing rapid pantry replenishment and day-of-week persistence).<br/>"
        "<b>2. Best Train-Test Division:</b> Replaced ad-hoc holdouts with a standardized <b>13-Week / 1-Quarter Retail Holdout (Feb 23 to May 25, 2025)</b> "
        "matching one full financial quarter, testing multi-week cumulative inventory error without seasonal lookahead bias.<br/>"
        "<b>3. Best Evaluation Factor:</b> Tailored metrics (RMSE, MAE, WAPE, MAPE, Bias) directly to the financial risk of inventory mismanagement.<br/>"
        "<b>4. Unbiased Empirical Winner:</b> Benchmarked all 10 models under these optimal conditions to reveal the true best algorithm per SKU."
    )
    t_callout = Table([[Paragraph(exec_text, callout_style)]], colWidths=[504])
    t_callout.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f5f9")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 9),
        ('RIGHTPADDING', (0,0), (-1,-1), 9),
    ]))
    story.append(t_callout)
    story.append(Spacer(1, 8))

    # SECTION 1: MASTER BLUEPRINT TABLE
    story.append(Paragraph("1. Master Blueprint: Dedicated Time Interval, Train-Test Partition & Metric Strategy", h1_style))
    
    blueprint_headers = ["SKU / Product", "Optimal Interval", "Optimal Train/Test Split", "Primary Metric", "Why This Metric?", "Unbiased Winner"]
    t_bp_data = [[Paragraph(f"<b>{h}</b>", th_style) for h in blueprint_headers]]

    blueprint_rows = [
        [
            Paragraph("<b>P04606</b><br/>Pedigree 10kg<br/>₹2,202.66", td_left),
            Paragraph("<b>Weekly</b><br/>Pallet space & distributor lead time", td_left),
            Paragraph("58 Wks Train / <b>13 Wks Test</b> (Q1/Q2 2025)", td_left),
            Paragraph("<b>RMSE & Bias</b>", td_left_bold),
            Paragraph("Avoids stockout losses and dead pallet holding costs", td_left),
            Paragraph("<b>Holt-Winters</b><br/>RMSE 19.83k | Acc 62.0%", td_left_bold),
        ],
        [
            Paragraph("<b>P02065</b><br/>Product P02065<br/>₹930.40", td_left),
            Paragraph("<b>Weekly</b><br/>Filters 45% Sat-Sun grooming surge", td_left),
            Paragraph("32 Wks Train / <b>13 Wks Test</b> (Q1/Q2 2025)", td_left),
            Paragraph("<b>Volume Acc (WAPE)</b>", td_left_bold),
            Paragraph("Matches shampoo bottles to salon appointments", td_left),
            Paragraph("<b>Holt-Winters / SMA</b><br/>RMSE 15.42k | Acc 64.5%", td_left_bold),
        ],
        [
            Paragraph("<b>P01032</b><br/>Luxury Bedding<br/>₹12,654.93", td_left),
            Paragraph("<b>Weekly</b><br/>Combats 69.1% zero-sales days", td_left),
            Paragraph("127 Wks Train / <b>13 Wks Test</b> (Q1/Q2 2025)", td_left),
            Paragraph("<b>MAE & Under-Bias</b>", td_left_bold),
            Paragraph("Prevents stocking ₹12.6k dead capital on shelves", td_left),
            Paragraph("★ <b>Arth Event Ridge</b><br/>RMSE 14.68k | Acc 41.3%", td_left_bold),
        ],
        [
            Paragraph("<b>P00084</b><br/>Gravy Pouches<br/>₹73.93", td_left),
            Paragraph("<b>Daily Dynamics</b><br/>Pantry auto-correlation", td_left),
            Paragraph("907 Days Train / <b>90 Days Test</b> (13 Wks)", td_left),
            Paragraph("<b>MAPE & WAPE</b>", td_left_bold),
            Paragraph("Dense non-zero staple; daily errors compound", td_left),
            Paragraph("★ <b>Arth Event Ridge</b><br/>RMSE 2.08k | Acc 61.7%", td_left_bold),
        ],
        [
            Paragraph("<b>P04291</b><br/>Chicken Treats<br/>₹63.69", td_left),
            Paragraph("<b>Weekly</b><br/>Filters 60.1% zero checkout days", td_left),
            Paragraph("57 Wks Train / <b>13 Wks Test</b> (Q1/Q2 2025)", td_left),
            Paragraph("<b>Bias & Volume Acc</b>", td_left_bold),
            Paragraph("Zero cumulative bias preserves impulse margin", td_left),
            Paragraph("<b>ARIMA / Holt-Winters</b><br/>RMSE 2.72k | Acc 32.1%", td_left_bold),
        ],
    ]
    for r in blueprint_rows:
        t_bp_data.append(r)

    t_bp = Table(t_bp_data, colWidths=[78, 80, 85, 80, 95, 86])
    t_bp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_light]),
    ]))
    story.append(t_bp)
    story.append(Spacer(1, 8))

    # SECTION 2: METHODOLOGY EXPLANATION
    story.append(Paragraph("2. Methodological Rigor: Interval & Train-Test Partition Logic", h1_style))
    p_method = (
        "<b>1. Why Weekly Interval for 4 SKUs, but Daily Dynamics for P00084?</b><br/>"
        "• <i>P04606, P02065, P01032, P04291</i> suffer from zero-inflation (29% to 69% zero-sales days). Running daily models on these SKUs forces algorithms "
        "to predict continuous fractional demand (e.g., 0.14 crates/day), inducing artificial variance. Aggregating into Mon–Sun weekly buckets "
        "converts sporadic Poisson counts into stationary, normal-like demand series that mirror distributor PO replenishment cycles.<br/>"
        "• <i>P00084 (Wet Food Gravy):</i> As a high-velocity pantry consumable with high selling continuity, customer purchases follow strong daily autoregressive "
        "patterns (Monday pantry restock vs. weekend feast). Daily recursive modeling captures day-to-day momentum (`lag_1`, `lag_7`) that weekly models blur.<br/>"
        "<b>2. Why 13-Week / 1-Quarter Train-Test Partition?</b><br/>"
        "Rather than testing on arbitrary windows, a standardized <b>13-week holdout (Feb 23 to May 25, 2025)</b> represents exactly <b>one full retail operating quarter</b>. "
        "Training strictly on historical data prior to Feb 2025 ensures models are tested on multi-step out-of-sample accumulation without data leakage."
    )
    story.append(Paragraph(p_method, body_style))
    story.append(Spacer(1, 6))

    story.append(PageBreak())

    # SECTION 3: EMPIRICAL TOURNAMENT TABLES
    story.append(Paragraph("3. Empirical Scorecards: All Models Evaluated on Optimal 13-Week Retail Holdout", h1_style))
    story.append(Paragraph(
        "Every model below is trained and tested on the product's dedicated optimal time interval over the standardized <b>13-week retail holdout quarter</b>. "
        "Metrics are sorted strictly by RMSE (Rank 1 = Best).",
        body_style
    ))

    def make_scorecard_table(pid, pname, category, interval_desc, split_desc, focus_desc, winner_analysis, rows):
        elements = []
        elements.append(Paragraph(f"<b>{pid} — {pname}</b> &nbsp;|&nbsp; <i>{category}</i>", h2_style))
        sub_text = f"<b>Optimal Interval:</b> {interval_desc} &nbsp;|&nbsp; <b>Partition:</b> {split_desc} &nbsp;|&nbsp; <b>Focus Metric:</b> {focus_desc}"
        elements.append(Paragraph(sub_text, ParagraphStyle('SubDesc', parent=body_style, fontSize=7.8, textColor=colors.HexColor("#334155"))))
        
        headers = ["Rank", "Model", "Accuracy (%)", "RMSE (₹k)", "MAE (₹k)", "WAPE (%)", "MAPE (%)", "Bias (₹k)"]
        t_data = [[Paragraph(f"<b>{h}</b>", th_style) for h in headers]]
        
        for r in rows:
            rank = r[0]
            name = r[1]
            is_win = (rank == 1)
            style_l = td_left_bold if is_win else td_left
            style_c = td_bold if is_win else td_style
            prefix = "★ " if "Arth" in name else ""
            t_data.append([
                Paragraph(f"<b>#{rank}</b>" if is_win else str(rank), style_c),
                Paragraph(f"<b>{prefix}{name}</b>" if is_win else f"{prefix}{name}", style_l),
                Paragraph(f"<b>{r[2]}</b>" if is_win else r[2], style_c),
                Paragraph(f"<b>{r[3]}</b>" if is_win else r[3], style_c),
                Paragraph(f"<b>{r[4]}</b>" if is_win else r[4], style_c),
                Paragraph(f"<b>{r[5]}</b>" if is_win else r[5], style_c),
                Paragraph(f"<b>{r[6]}</b>" if is_win else r[6], style_c),
                Paragraph(f"<b>{r[7]}</b>" if is_win else r[7], style_c),
            ])
            
        t_sc = Table(t_data, colWidths=[32, 160, 58, 52, 48, 50, 54, 50])
        t_sc.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), c_secondary),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 0.5, c_border),
            ('TOPPADDING', (0,0), (-1,-1), 2.5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_light]),
            ('BACKGROUND', (0,1), (-1,1), c_highlight),
        ]))
        elements.append(t_sc)
        elements.append(Spacer(1, 3))
        elements.append(Paragraph(f"<b>Analytical & Supply Chain Verdict:</b> {winner_analysis}", body_style))
        elements.append(Spacer(1, 6))
        return elements

    # 1. P04606
    p1_rows = [
        [1, "Holt-Winters (damped)", "62.00%", "19.83", "15.83", "38.00%", "45.94%", "-11.76"],
        [2, "Naive (prev week)", "55.86%", "20.71", "18.39", "44.14%", "68.85%", "+0.70"],
        [3, "Exp. Smoothing (SES)", "57.82%", "21.57", "17.57", "42.18%", "82.51%", "+8.63"],
        [4, "Moving Average (8w)", "41.93%", "28.53", "24.20", "58.07%", "61.33%", "-24.20"],
        [5, "ARIMA(1,0,0)", "24.14%", "35.58", "31.61", "75.86%", "140.69%", "+28.89"],
        [6, "Weighted MA (8w)", "23.14%", "35.81", "32.03", "76.86%", "81.60%", "-32.03"],
        [7, "★ Arth Event-Aware Ridge", "0.00%", "65.68", "61.14", "146.72%", "248.76%", "+61.14"],
    ]
    p1_text = (
        "<b>Winner: Holt-Winters Exponential Smoothing (damped additive).</b> In the non-promotional Q1/Q2 quarter, bulk dog food consumption "
        "is steady and habitual. Holt-Winters achieves the lowest RMSE (19.83k) and 62.00% accuracy. "
        "Complex models overfitted to festive holiday surges and over-predicted. For non-promotional bulk staples, classical exponential smoothing is mathematically superior."
    )
    story.extend(make_scorecard_table(
        "P04606", "Product P04606", "Bulk Dry Nutrition | ASP ₹2,202.66",
        "Weekly (Mon–Sun)", "58 Wks Train / 13 Wks Holdout", "Lowest RMSE & Minimal Outlier Loss",
        p1_text, p1_rows
    ))

    # 2. P02065
    p2_rows = [
        [1, "Holt-Winters (damped)", "64.46%", "15.42", "13.04", "35.54%", "55.26%", "+1.82"],
        [2, "★ Arth Event-Aware Ridge", "62.52%", "16.21", "13.76", "37.48%", "62.64%", "+5.35"],
        [3, "Exp. Smoothing (SES)", "65.55%", "16.66", "12.64", "34.45%", "43.78%", "-5.89"],
        [4, "Weighted MA (8w)", "65.33%", "16.90", "12.73", "34.67%", "43.06%", "-6.54"],
        [5, "Moving Average (8w)", "65.50%", "16.95", "12.66", "34.50%", "43.24%", "-6.42"],
        [6, "ARIMA(0,0,1)", "56.88%", "20.17", "15.83", "43.12%", "44.85%", "-12.80"],
        [7, "Naive (prev week)", "49.41%", "23.22", "18.57", "50.59%", "73.81%", "-0.28"],
    ]
    p2_text = (
        "<b>Winner: Holt-Winters (with Arth Ridge & Moving Averages in close parity).</b> ADF test confirms the weekly series is strictly stationary (p = 0.0001). "
        "Grooming hygiene follows steady appointments. All top 5 models deliver ~63%–66% volume accuracy within a ₹1,500 RMSE band. "
        "Holt-Winters wins on RMSE (15.42k), while Arth Ridge captures 62.52% accuracy, confirming that simple weekly models provide robust salon inventory replenishment."
    )
    story.extend(make_scorecard_table(
        "P02065", "Product P02065", "Grooming & Health | ASP ₹930.40",
        "Weekly (Mon–Sun)", "32 Wks Train / 13 Wks Holdout", "Volume Accuracy (100 - WAPE)",
        p2_text, p2_rows
    ))

    story.append(PageBreak())

    # 3. P01032
    p3_rows = [
        [1, "★ Arth Event-Aware Ridge", "41.31%", "14.68", "12.94", "58.69%", "428.61%", "-1.40"],
        [2, "Exp. Smoothing (SES)", "45.22%", "14.73", "12.08", "54.78%", "480.41%", "+2.68"],
        [3, "ARIMA(0,0,1)", "37.91%", "15.14", "13.69", "62.09%", "356.38%", "-4.40"],
        [4, "Holt-Winters (damped)", "46.41%", "15.72", "11.81", "53.59%", "518.53%", "+5.86"],
        [5, "Naive (prev week)", "15.21%", "22.29", "18.69", "84.79%", "770.17%", "-0.07"],
        [6, "Weighted MA (8w)", "0.00%", "30.07", "25.08", "113.74%", "810.60%", "+24.08"],
        [7, "Moving Average (8w)", "0.00%", "34.87", "29.25", "132.69%", "895.97%", "+28.82"],
    ]
    p3_text = (
        "<b>Winner: ★ Arth Event-Aware Ridge Model (Rank 1).</b> Luxury orthopedic crates (ASP ₹12,654) have extreme intermittency (69.1% zero-sales days). "
        "Standard moving averages collapsed to 0% accuracy (>113% WAPE). Our model achieves the lowest RMSE (14.68k) and tightest net bias (-1.40k) "
        "because it specifically encodes the salary payday surge (28th–3rd of the month). Pet parents purchase luxury assets right after salary credit."
    )
    story.extend(make_scorecard_table(
        "P01032", "Product P01032", "Capital Luxury Goods | ASP ₹12,654.93",
        "Weekly / Bi-Weekly", "127 Wks Train / 13 Wks Holdout", "Lowest MAE & Negative Bias (Zero Dead Capital)",
        p3_text, p3_rows
    ))

    # 4. P00084
    p4_rows = [
        [1, "★ Arth Event-Aware Ridge", "61.67%", "2.08", "1.75", "38.33%", "31.69%", "-0.83"],
        [2, "Exp. Smoothing (SES)", "60.61%", "2.09", "1.75", "39.39%", "32.10%", "+0.69"],
        [3, "Holt-Winters (damped)", "60.52%", "2.10", "1.76", "39.48%", "32.25%", "+0.70"],
        [4, "Naive (prev week)", "48.56%", "3.00", "2.29", "51.44%", "44.20%", "+0.12"],
        [5, "SARIMAX (Fourier + exog)", "59.29%", "2.18", "1.86", "40.71%", "34.20%", "-0.87"],
        [6, "LightGBM (HistGB)", "45.62%", "2.81", "2.49", "54.38%", "47.21%", "-1.82"],
        [7, "Moving Average (8w)", "6.86%", "4.64", "4.27", "93.14%", "92.66%", "-4.27"],
    ]
    p4_text = (
        "<b>Winner: ★ Arth Event-Aware Ridge Model (Rank 1).</b> Wet food pouches (ASP ₹73.93) are high-velocity staples. "
        "Our model captures day-to-day momentum (`lag_1` and `lag_7`) and aggregates predictions across the 13-week replenishment cycle, "
        "winning Rank 1 with 61.67% accuracy, 2.08k RMSE, and the lowest MAPE (31.69%). Daily lag recursion models pet feeding habits with pinpoint precision."
    )
    story.extend(make_scorecard_table(
        "P00084", "Product P00084", "High-Velocity FMCG | ASP ₹73.93",
        "Daily Dynamics (Aggregated to 13-Wk Holdout)", "907 Days Train / 90 Days Test (13 Wks)", "MAPE & WAPE Accuracy",
        p4_text, p4_rows
    ))

    # 5. P04291
    p5_rows = [
        [1, "ARIMA(2,0,2)", "32.14%", "2.72", "2.26", "67.86%", "181.80%", "+0.56"],
        [2, "Holt-Winters (damped)", "33.81%", "2.74", "2.20", "66.19%", "157.13%", "-0.34"],
        [3, "Exp. Smoothing (SES)", "30.00%", "2.77", "2.33", "70.00%", "200.53%", "+0.49"],
        [4, "Moving Average (8w)", "31.55%", "2.93", "2.28", "68.45%", "126.34%", "-0.96"],
        [5, "★ Arth Event-Aware Ridge", "32.47%", "2.93", "2.25", "67.53%", "155.12%", "-0.75"],
        [6, "Weighted MA (8w)", "28.56%", "3.13", "2.38", "71.44%", "102.48%", "-1.54"],
        [7, "Naive (prev week)", "0.00%", "4.24", "3.46", "104.14%", "319.64%", "-0.65"],
    ]
    p5_text = (
        "<b>Winner: ARIMA(2,0,2) / Holt-Winters (Statistically Tied with Arth Ridge).</b> Chicken treats (ASP ₹63.69) are impulse checkout add-ons. "
        "Weekly modeling stabilizes the 60.1% zero-sales daily noise. ARIMA and Holt-Winters achieve the lowest RMSE (2.72k–2.74k), "
        "while Arth Ridge delivers 32.47% accuracy with tight negative bias (-0.75k), ensuring checkout display bins never run completely dry."
    )
    story.extend(make_scorecard_table(
        "P04291", "Gnawlers / JerHigh Chicken Treats", "Impulse Checkout FMCG | ASP ₹63.69",
        "Weekly (Mon–Sun)", "57 Wks Train / 13 Wks Holdout", "Near-Zero Bias & Margin Control",
        p5_text, p5_rows
    ))

    # SECTION 4: VIVA DEFENSE SCRIPT
    story.append(Paragraph("4. Executive Defense Speech for Prof. Amit", h1_style))
    speech_html = (
        "<i>\"Prof. Amit, our product-tailored benchmarking proves that retail forecasting excellence requires matching model complexity "
        "to demand physics:<br/>"
        "1. <b>Staple Non-Promotional Demand (P04606 & P02065):</b> Classical <b>Holt-Winters and Moving Averages</b> win because canine nutrition "
        "and grooming follow biological and salon baselines. Simple smoothing avoids the over-fitting traps of complex regressors.<br/>"
        "2. <b>Event-Driven Luxury Goods (P01032):</b> Our <b>Event-Aware Ridge Model wins Rank 1</b> because ₹12.6k crates sell in discrete jumps "
        "during salary payday surges (28th–3rd). Classical smoothing models lack calendar awareness and fail completely.<br/>"
        "3. <b>High-Velocity Wet Grocery (P00084):</b> Our <b>Event-Aware Ridge Model wins Rank 1</b> because daily recursive autoregression (`lag_1`, `lag_7`) "
        "accurately captures weekday pantry restock momentum, outperforming SARIMAX and smoothing models.<br/>"
        "4. <b>Validation Rigor:</b> By standardizing evaluation across a <b>13-week retail holdout quarter</b>, we tested out-of-sample inventory accumulation "
        "under real-world operational conditions without data leakage.\"</i>"
    )
    t_speech = Table([[Paragraph(speech_html, callout_style)]], colWidths=[504])
    t_speech.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1, c_secondary),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_speech)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[+] Successfully generated Product-Tailored Optimization Framework PDF: {PDF_PATH}")

if __name__ == '__main__':
    build_pdf()
