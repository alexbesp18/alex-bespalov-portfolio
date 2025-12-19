"""Enhanced report generator for deep strategic audit reports."""

import os
from datetime import datetime
from pathlib import Path

from fpdf import FPDF
from jinja2 import Environment, FileSystemLoader

from src.models.strategy import StrategicBrief


def sanitize_text(text: str) -> str:
    """Replace special Unicode characters with ASCII equivalents."""
    replacements = {
        '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
        '\u2013': '-', '\u2014': '-', '\u2026': '...', '\u2022': '-',
        '\u00a0': ' ', '\u00b7': '-',
    }
    for unicode_char, ascii_char in replacements.items():
        text = text.replace(unicode_char, ascii_char)
    return text.encode('ascii', 'replace').decode('ascii')


class AuditPDF(FPDF):
    """Custom PDF class for strategic audit reports."""

    def __init__(self, company_name: str) -> None:
        super().__init__()
        self.company_name = company_name
        self.set_auto_page_break(auto=True, margin=20)
        self.left_margin = 10
        self.set_left_margin(self.left_margin)

    def header(self) -> None:
        """Add header to each page."""
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(100, 100, 100)
        self.set_xy(self.left_margin, 10)
        self.cell(0, 8, f"STRATEGIC AUDIT: {self.company_name}", ln=True)
        self.set_draw_color(200, 200, 200)
        self.line(self.left_margin, 18, 200, 18)
        self.ln(8)

    def footer(self) -> None:
        """Add footer to each page."""
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def write_text(self, text: str, font_style: str = "", size: int = 10,
                   color: tuple = (51, 51, 51), spacing: int = 5):
        """Write text with proper margin reset."""
        self.set_x(self.left_margin)
        self.set_font("Helvetica", font_style, size)
        self.set_text_color(*color)
        self.multi_cell(0, spacing, sanitize_text(text))

    def write_list_item(self, text: str, prefix: str = "-"):
        """Write a list item."""
        self.set_x(self.left_margin)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(51, 51, 51)
        self.multi_cell(0, 5, f"  {prefix} {sanitize_text(text)}")


class Reporter:
    """Generates enhanced strategic audit reports in PDF format."""

    def __init__(self) -> None:
        """Initialize the reporter."""
        template_dir = Path(__file__).parent.parent / "templates"
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def generate_pdf(
        self, strategy: StrategicBrief, company_name: str, output_path: str
    ) -> None:
        """Generate enhanced PDF report from strategic brief."""
        pdf = AuditPDF(company_name)
        pdf.add_page()

        # === TITLE PAGE ===
        pdf.set_xy(pdf.left_margin, 30)
        pdf.set_font("Helvetica", "B", 28)
        pdf.set_text_color(26, 26, 46)
        pdf.cell(0, 20, "STRATEGIC AUDIT", ln=True, align="C")
        
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_text_color(74, 78, 105)
        pdf.cell(0, 12, sanitize_text(company_name), ln=True, align="C")
        
        pdf.ln(5)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(100, 100, 100)
        date_str = datetime.now().strftime("%B %d, %Y")
        pdf.cell(0, 6, f"Generated: {date_str}", ln=True, align="C")
        pdf.cell(0, 6, "Deep Analysis with Multi-Layer Strategic Framework", ln=True, align="C")
        pdf.ln(15)

        # === SECTION 1: SITUATION ASSESSMENT ===
        self._section_header(pdf, "1. SITUATION ASSESSMENT")
        pdf.write_text(strategy.situation_assessment)
        pdf.ln(8)

        # === SECTION 2: DRIVING FORCES ===
        self._section_header(pdf, "2. DRIVING FORCES")
        pdf.write_text(strategy.driving_forces)
        pdf.ln(8)

        # === SECTION 3: STRATEGIC WINDOWS ===
        self._section_header(pdf, "3. STRATEGIC WINDOWS (Time-Sensitive)")
        for i, window in enumerate(strategy.strategic_windows, 1):
            pdf.write_text(f"{i}. {window}")
        pdf.ln(5)

        # === SECTION 4: ASYMMETRIC OPPORTUNITIES ===
        pdf.add_page()
        self._section_header(pdf, "4. ASYMMETRIC OPPORTUNITIES")
        pdf.write_text("High upside, limited downside opportunities with cascade analysis",
                       font_style="I", size=9, color=(100, 100, 100))
        pdf.ln(5)

        for i, opp in enumerate(strategy.asymmetric_opportunities, 1):
            self._add_opportunity(pdf, i, opp)

        # === SECTION 5: VULNERABILITY ANALYSIS ===
        pdf.add_page()
        self._section_header(pdf, "5. VULNERABILITY ANALYSIS")
        
        # Kill Scenario
        pdf.write_text("KILL SCENARIO", font_style="B", size=11, color=(180, 50, 50))
        pdf.write_text(strategy.vulnerability_analysis.kill_scenario)
        pdf.ln(5)

        # Hidden Dependencies
        pdf.write_text("Hidden Dependencies", font_style="B", size=11, color=(74, 78, 105))
        for dep in strategy.vulnerability_analysis.hidden_dependencies:
            pdf.write_list_item(dep)
        pdf.ln(3)

        # Competitive Blind Spots
        pdf.write_text("Competitive Blind Spots", font_style="B", size=11, color=(74, 78, 105))
        for spot in strategy.vulnerability_analysis.competitive_blind_spots:
            pdf.write_list_item(spot)
        pdf.ln(3)

        # Misaligned Incentives
        if strategy.vulnerability_analysis.misaligned_incentives:
            pdf.write_text("Misaligned Incentives", font_style="B", size=11, color=(74, 78, 105))
            for inc in strategy.vulnerability_analysis.misaligned_incentives:
                pdf.write_list_item(inc)
        pdf.ln(8)

        # === SECTION 6: RESOURCE REALLOCATION ===
        self._section_header(pdf, "6. RESOURCE REALLOCATION (Stop Doing)")
        for i, item in enumerate(strategy.resource_reallocation, 1):
            pdf.write_text(f"{i}. {item}")
        pdf.ln(5)

        # === SECTION 7: QUANTIFIED RECOMMENDATIONS ===
        self._section_header(pdf, "7. QUANTIFIED RECOMMENDATIONS")
        for i, rec in enumerate(strategy.quantified_recommendations, 1):
            pdf.write_text(f"{i}. {rec}")
        pdf.ln(5)

        # === SECTION 8: 90-DAY PRIORITIES ===
        self._section_header(pdf, "8. 90-DAY PRIORITIES")
        for i, priority in enumerate(strategy.ninety_day_priorities, 1):
            pdf.write_text(f"{i}. {priority}", font_style="B", color=(26, 100, 26))
        pdf.ln(10)

        # Footer
        pdf.write_text("Generated by Strategic Audit Bot - Deep Analysis Framework",
                       font_style="I", size=8, color=(128, 128, 128))

        pdf.output(output_path)

    def _section_header(self, pdf: AuditPDF, title: str) -> None:
        """Add a styled section header."""
        pdf.set_x(pdf.left_margin)
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(26, 26, 46)
        pdf.cell(0, 10, sanitize_text(title), ln=True)
        pdf.set_draw_color(74, 78, 105)
        pdf.line(pdf.left_margin, pdf.get_y(), 120, pdf.get_y())
        pdf.ln(6)

    def _add_opportunity(self, pdf: AuditPDF, num: int, opp) -> None:
        """Add a deep opportunity entry with cascade analysis."""
        # Title
        pdf.write_text(f"{num}. {opp.title}", font_style="B", size=12, color=(34, 34, 59))

        # Thesis
        pdf.write_text(f"Thesis: {opp.thesis}", font_style="I", size=10, color=(74, 78, 105))
        pdf.ln(2)

        # Cascade Analysis
        pdf.write_text("CASCADE ANALYSIS:", font_style="B", size=9, color=(100, 100, 100))
        pdf.write_text(f"1st Order: {opp.first_order_effect}", size=9)
        pdf.write_text(f"2nd Order: {opp.second_order_effect}", size=9)
        pdf.write_text(f"3rd Order: {opp.third_order_effect}", size=9)
        pdf.ln(2)

        # Quantified Upside
        pdf.write_text("UPSIDE:", font_style="B", size=9, color=(26, 100, 26))
        pdf.write_text(opp.quantified_upside, size=9)

        # Downside Risk
        pdf.write_text("RISK:", font_style="B", size=9, color=(180, 50, 50))
        pdf.write_text(opp.downside_risk, size=9)

        # Time Sensitivity
        pdf.write_text("WINDOW:", font_style="B", size=9, color=(180, 120, 0))
        pdf.write_text(opp.time_sensitivity, size=9)

        # Contrarian Angle
        pdf.write_text("CONTRARIAN:", font_style="B", size=9, color=(74, 78, 105))
        pdf.write_text(opp.contrarian_angle, font_style="I", size=9)

        pdf.ln(8)

    def generate_report(
        self,
        strategy: StrategicBrief,
        company_name: str,
        output_dir: str = "output",
    ) -> str:
        """Generate complete PDF report."""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{company_name}_deep_audit_{timestamp}.pdf"
        output_path = os.path.join(output_dir, filename)
        self.generate_pdf(strategy, company_name, output_path)
        return output_path


if __name__ == "__main__":
    from src.models.strategy import DeepOpportunity, VulnerabilityAnalysis

    # Test with sample data
    test_strategy = StrategicBrief(
        situation_assessment="Stripe is the dominant payment processor for internet businesses, processing over $1T annually. Strong developer moat but facing margin pressure.",
        driving_forces="API-first approach created network effects. Developer loyalty drives adoption. Transaction-based model creates alignment with customer success.",
        strategic_windows=[
            "AI-powered fraud prevention (12-month window before commoditization)",
            "Embedded finance for SaaS (18-month first-mover window)",
        ],
        asymmetric_opportunities=[
            DeepOpportunity(
                title="Embedded Finance Platform",
                thesis="SaaS companies want to offer financial services but lack infrastructure",
                first_order_effect="New revenue from embedded finance APIs",
                second_order_effect="Deep integration creates 10x switching costs",
                third_order_effect="Becomes financial infrastructure layer for all SaaS",
                quantified_upside="$500M ARR within 3 years (5% of $10B TAM)",
                downside_risk="$50M development cost if adoption 50% slower",
                time_sensitivity="Banks building competing APIs in 18-24 months",
                contrarian_angle="Market sees payments commoditizing; embedded finance is defensible",
            ),
        ],
        vulnerability_analysis=VulnerabilityAnalysis(
            kill_scenario="Regulatory change requiring banking licenses kills margin structure",
            hidden_dependencies=["AWS concentration", "Banking partner relationships"],
            competitive_blind_spots=["Apple/Google B2B entry", "Blockchain settlement"],
            misaligned_incentives=["Sales comp favors volume over margin"],
        ),
        resource_reallocation=[
            "Stop custom enterprise features for single clients",
            "Reduce investment in mature payment rail optimization",
        ],
        quantified_recommendations=[
            "Launch embedded finance to 1000 SaaS partners, targeting $100M Y1 revenue",
            "Increase developer relations budget 40% to defend moat",
        ],
        ninety_day_priorities=[
            "Ship embedded finance MVP to 10 beta partners",
            "Hire Head of AI/ML for intelligent routing",
            "Renegotiate AWS for 20% cost reduction",
        ],
    )

    print("Generating enhanced test report...")
    reporter = Reporter()
    output_path = reporter.generate_report(test_strategy, "Stripe")
    print(f"Report generated: {output_path}")
