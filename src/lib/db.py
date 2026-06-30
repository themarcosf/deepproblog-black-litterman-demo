################################################################################
# Date: 2026-06-30
################################################################################
COMPANIES = {
    "acme": {
        "description": "A mid-cap technology company specializing in cloud infrastructure.",
        "valuation_score": 72,
        "valuation_reasoning":
            "Trading below peers on EV/EBITDA; recent pullback creates entry opportunity.",

        "earnings_score": 65,
        "earnings_reasoning":
            "Solid but decelerating growth; margins under pressure from R&D spend.",

        "earnings_details": {
            "stability_score": 70,
            "growth_score": 55,
        },

        "financial_score": 80,
        "financial_reasoning":
            "Strong balance sheet, low debt, consistent free cash flow.",

        "financial_details": {
            "liquidity_score": 85,
            "debt_score": 82,
            "dividend_score": 60,
        },
    },
    "globex": {
        "description": "A large-cap consumer staples company with diversified retail and distribution operations.",
        "valuation_score": 45,
        "valuation_reasoning":
            "Trading at a premium to sector peers; limited margin of safety at current multiples.",

        "earnings_score": 38,
        "earnings_reasoning":
            "Revenue flat year-over-year; rising input costs squeezing operating margins.",

        "earnings_details": {
            "stability_score": 55,
            "growth_score": 22,
        },

        "financial_score": 50,
        "financial_reasoning":
            "Moderate leverage with adequate liquidity; dividend coverage thinning.",

        "financial_details": {
            "liquidity_score": 58,
            "debt_score": 44,
            "dividend_score": 48,
        },
    },
}
