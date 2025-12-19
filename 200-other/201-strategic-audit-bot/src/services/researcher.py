"""Enhanced research service for deep strategic intelligence."""

from tavily import TavilyClient

from src.config import settings


class Researcher:
    """Gathers deep company intelligence using Tavily search API."""

    def __init__(self) -> None:
        """Initialize the Tavily client."""
        self.client = TavilyClient(api_key=settings.tavily_api_key)

    def _search(self, query: str, max_results: int = 10) -> dict:
        """Execute a search and return structured results."""
        response = self.client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
            include_answer=True,
        )
        return {
            "articles": response.get("results", []),
            "answer": response.get("answer", ""),
            "query": query,
        }

    # === LAYER 1: CURRENT STATE ===

    def get_strategic_moves(self, company: str, max_results: int = 10) -> dict:
        """Fetch strategic moves, pivots, and major announcements."""
        query = f"{company} strategic moves announcements product launches pivots 2024"
        return self._search(query, max_results)

    def get_leadership_changes(self, company: str, max_results: int = 10) -> dict:
        """Fetch leadership changes, executive hires, departures."""
        query = f"{company} CEO CTO CPO executive leadership changes hires departures"
        return self._search(query, max_results)

    def get_customer_economics(self, company: str, max_results: int = 10) -> dict:
        """Analyze customer churn, LTV, acquisition costs, retention."""
        query = f"{company} customer churn retention rate LTV CAC acquisition cost"
        return self._search(query, max_results)

    def get_competitive_moat(self, company: str, max_results: int = 10) -> dict:
        """Analyze competitive advantages, moats, and emerging threats."""
        query = f"{company} competitive advantage moat differentiation vs competitors threats"
        return self._search(query, max_results)

    # === LAYER 2: STRUCTURAL FORCES ===

    def get_business_model(self, company: str, max_results: int = 10) -> dict:
        """Analyze business model, unit economics, revenue streams."""
        query = f"{company} business model revenue streams unit economics pricing margins"
        return self._search(query, max_results)

    def get_regulatory_landscape(self, company: str, max_results: int = 10) -> dict:
        """Analyze regulatory risks, compliance issues, legal challenges."""
        query = f"{company} regulatory compliance legal challenges lawsuits government antitrust"
        return self._search(query, max_results)

    def get_technology_platform(self, company: str, max_results: int = 10) -> dict:
        """Analyze technology stack, technical debt, infrastructure."""
        query = f"{company} technology stack platform infrastructure API technical architecture"
        return self._search(query, max_results)

    # === LAYER 3: ECOSYSTEM & OPPORTUNITIES ===

    def get_partnerships_ma(self, company: str, max_results: int = 10) -> dict:
        """Analyze M&A activity, partnerships, strategic alliances."""
        query = f"{company} acquisitions mergers partnerships strategic alliances investments"
        return self._search(query, max_results)

    def get_pricing_strategy(self, company: str, max_results: int = 10) -> dict:
        """Analyze pricing changes, monetization strategy evolution."""
        query = f"{company} pricing strategy price changes monetization fees costs customers"
        return self._search(query, max_results)

    def get_market_position(self, company: str, max_results: int = 10) -> dict:
        """Analyze market share, positioning, and growth trajectory."""
        query = f"{company} market share position growth rate revenue valuation funding"
        return self._search(query, max_results)

    def gather_deep_research(self, company: str) -> dict:
        """
        Gather comprehensive deep research across all dimensions.
        
        Returns structured data for multi-layer strategic analysis.
        """
        return {
            "company_name": company,
            # Layer 1: Current State
            "strategic_moves": self.get_strategic_moves(company),
            "leadership": self.get_leadership_changes(company),
            "customer_economics": self.get_customer_economics(company),
            "competitive_moat": self.get_competitive_moat(company),
            # Layer 2: Structural Forces
            "business_model": self.get_business_model(company),
            "regulatory": self.get_regulatory_landscape(company),
            "technology": self.get_technology_platform(company),
            # Layer 3: Ecosystem
            "partnerships_ma": self.get_partnerships_ma(company),
            "pricing": self.get_pricing_strategy(company),
            "market_position": self.get_market_position(company),
        }


if __name__ == "__main__":
    researcher = Researcher()
    company = "Stripe"

    print(f"Deep Research: {company}\n{'='*50}\n")

    # Test a few key methods
    print("[1] Strategic Moves...")
    moves = researcher.get_strategic_moves(company, max_results=3)
    print(f"    {moves['answer'][:200]}...\n")

    print("[2] Business Model...")
    model = researcher.get_business_model(company, max_results=3)
    print(f"    {model['answer'][:200]}...\n")

    print("[3] Regulatory Landscape...")
    reg = researcher.get_regulatory_landscape(company, max_results=3)
    print(f"    {reg['answer'][:200]}...\n")

    print("[4] Partnerships & M&A...")
    ma = researcher.get_partnerships_ma(company, max_results=3)
    print(f"    {ma['answer'][:200]}...\n")

    print("[5] Competitive Moat...")
    moat = researcher.get_competitive_moat(company, max_results=3)
    print(f"    {moat['answer'][:200]}...")
