#!/usr/bin/env python3
"""Strategic Audit Bot - Deep Analysis CLI."""

import argparse
import sys
from typing import NoReturn

from src.services.researcher import Researcher
from src.services.strategist import Strategist
from src.services.reporter import Reporter


def run_deep_audit(company_name: str, output_dir: str = "output") -> str:
    """
    Run the deep strategic audit pipeline.

    Args:
        company_name: Name of the company to analyze
        output_dir: Directory to save the report

    Returns:
        Path to the generated PDF report
    """
    print(f"\n{'='*70}")
    print(f"  DEEP STRATEGIC AUDIT: {company_name}")
    print(f"  Multi-Layer Analysis with Rigorous Frameworks")
    print(f"{'='*70}\n")

    # Phase 1: Deep Research
    print("[PHASE 1] Gathering Deep Intelligence...")
    researcher = Researcher()

    print("  Layer 1: Current State")
    print("    - Strategic moves & announcements...")
    strategic = researcher.get_strategic_moves(company_name)
    print(f"      Found {len(strategic['articles'])} sources")

    print("    - Leadership changes...")
    leadership = researcher.get_leadership_changes(company_name)
    print(f"      Found {len(leadership['articles'])} sources")

    print("    - Customer economics (churn, LTV, CAC)...")
    customer = researcher.get_customer_economics(company_name)
    print(f"      Found {len(customer['articles'])} sources")

    print("    - Competitive moat analysis...")
    moat = researcher.get_competitive_moat(company_name)
    print(f"      Found {len(moat['articles'])} sources")

    print("\n  Layer 2: Structural Forces")
    print("    - Business model & unit economics...")
    business = researcher.get_business_model(company_name)
    print(f"      Found {len(business['articles'])} sources")

    print("    - Regulatory & legal landscape...")
    regulatory = researcher.get_regulatory_landscape(company_name)
    print(f"      Found {len(regulatory['articles'])} sources")

    print("    - Technology platform...")
    tech = researcher.get_technology_platform(company_name)
    print(f"      Found {len(tech['articles'])} sources")

    print("\n  Layer 3: Ecosystem")
    print("    - Partnerships & M&A...")
    partnerships = researcher.get_partnerships_ma(company_name)
    print(f"      Found {len(partnerships['articles'])} sources")

    print("    - Pricing strategy...")
    pricing = researcher.get_pricing_strategy(company_name)
    print(f"      Found {len(pricing['articles'])} sources")

    print("    - Market position...")
    market = researcher.get_market_position(company_name)
    print(f"      Found {len(market['articles'])} sources")

    research_data = {
        "company_name": company_name,
        "strategic_moves": strategic,
        "leadership": leadership,
        "customer_economics": customer,
        "competitive_moat": moat,
        "business_model": business,
        "regulatory": regulatory,
        "technology": tech,
        "partnerships_ma": partnerships,
        "pricing": pricing,
        "market_position": market,
    }
    print("\n  Research complete!\n")

    # Phase 2: Deep Strategic Analysis
    print("[PHASE 2] Generating Deep Strategic Analysis...")
    print("  Applying analytical frameworks:")
    print("    - Inversion analysis (kill scenarios)")
    print("    - Cascade thinking (1st/2nd/3rd order effects)")
    print("    - Incentive mapping")
    print("    - Contrarian analysis")
    
    strategist = Strategist()
    strategy = strategist.generate_strategy(research_data)
    
    print(f"\n  Analysis Results:")
    print(f"    - Strategic windows: {len(strategy.strategic_windows)}")
    print(f"    - Asymmetric opportunities: {len(strategy.asymmetric_opportunities)}")
    print(f"    - Hidden dependencies: {len(strategy.vulnerability_analysis.hidden_dependencies)}")
    print(f"    - 90-day priorities: {len(strategy.ninety_day_priorities)}")
    print("  Analysis complete!\n")

    # Phase 3: Report Generation
    print("[PHASE 3] Generating Deep Audit Report...")
    reporter = Reporter()
    output_path = reporter.generate_report(strategy, company_name, output_dir)
    print(f"  Report saved: {output_path}\n")

    # Summary
    print(f"{'='*70}")
    print("  AUDIT COMPLETE")
    print(f"{'='*70}")
    print(f"\n  Key Findings Preview:")
    print(f"  - Kill Scenario: {strategy.vulnerability_analysis.kill_scenario[:80]}...")
    if strategy.asymmetric_opportunities:
        opp = strategy.asymmetric_opportunities[0]
        print(f"  - Top Opportunity: {opp.title}")
        print(f"    Upside: {opp.quantified_upside[:60]}...")
    if strategy.ninety_day_priorities:
        print(f"  - Priority #1: {strategy.ninety_day_priorities[0][:60]}...")
    print()

    return output_path


def main() -> NoReturn:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Deep Strategic Audit - Multi-Layer Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py Stripe
  python main.py "OpenAI" --output-dir reports
  python main.py Microsoft --output-dir ./audits

The audit analyzes:
  - Strategic moves, leadership, customer economics
  - Business model, regulatory landscape, technology
  - Partnerships, pricing, market position
  
And generates insights on:
  - Kill scenarios (what could destroy the company)
  - Asymmetric opportunities (high upside, limited downside)
  - Cascade effects (1st, 2nd, 3rd order consequences)
  - 90-day priorities for immediate action
        """,
    )
    parser.add_argument(
        "company",
        help="Name of the company to analyze",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default="output",
        help="Directory to save the report (default: output)",
    )

    args = parser.parse_args()

    try:
        output_path = run_deep_audit(args.company, args.output_dir)
        print(f"Success! Deep audit available at: {output_path}")
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
