################################################################################
# Date: 2026-06-30
################################################################################
import logging
import math

import numpy as np
import pandas as pd

from pypfopt import black_litterman, EfficientFrontier
from pypfopt.black_litterman import BlackLittermanModel

logger = logging.getLogger(__name__)


################################################################################
# Constants
################################################################################
STANCE_RETURNS = {"bullish": 0.20, "neutral": 0.00, "bearish": -0.15}


COMPANY_PARAMS = {
    "acme": {"vol": 0.28, "market_cap": 5e9},
    "globex": {"vol": 0.18, "market_cap": 12e9},
}

INTER_ASSET_CORR = 0.25
RISK_AVERSION = 2.5


################################################################################
# Private interface
################################################################################
def parse_stances(result) -> dict[str, dict[str, float]]:
    probs: dict[str, dict[str, float]] = {}
    for entry in result:
        for term, tensor in entry.result.items():
            company = term.args[0].functor
            stance = term.args[1].functor
            probs.setdefault(company, {})[stance] = tensor.item()
    return probs


def entropy(dist: dict[str, float]) -> float:
    return -sum(p * math.log(p + 1e-12) for p in dist.values())


def round_floats(value, ndigits: int = 3):
    if isinstance(value, (pd.Series, pd.DataFrame)):
        return value.round(ndigits)
    if isinstance(value, dict):
        return {k: round_floats(v, ndigits) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(round_floats(v, ndigits) for v in value)
    if isinstance(value, float):
        return round(value, ndigits)
    return value


def market_data(companies: list[str]) -> tuple[pd.DataFrame, pd.Series]:
    logger.debug("Computing market data for companies: %s", companies)
    n = len(companies)
    vols = np.array([COMPANY_PARAMS[c]["vol"] for c in companies])
    corr = (1 - INTER_ASSET_CORR) * np.eye(n) + INTER_ASSET_CORR * np.ones((n, n))
    cov  = pd.DataFrame(np.outer(vols, vols) * corr, index=companies, columns=companies)
    logger.debug("Covariance matrix:\n%s", round_floats(cov))

    market_caps = pd.Series({c: COMPANY_PARAMS[c]["market_cap"] for c in companies})
    pi = black_litterman.market_implied_prior_returns(market_caps, RISK_AVERSION, cov)
    logger.debug("Market-implied prior returns: %s", round_floats(pi.to_dict()))

    return cov, pi


################################################################################
# Public interface
################################################################################
def build_base_allocation(companies: list[str]) -> dict[int, float]:
    logger.info("Building base allocation (no classifier views) for companies: %s", companies)
    cov, pi = market_data(companies)

    ef = EfficientFrontier(pi, cov)
    ef.max_sharpe()
    weights = dict(ef.clean_weights())
    logger.info("Base portfolio weights: %s", round_floats(weights))
    return weights


def build_allocation(result) -> dict[int, float]:
    probs = parse_stances(result)
    companies = list(probs.keys())
    logger.info("Building neural-predicate views allocation for companies: %s", companies)
    logger.debug("Stance probabilities: %s", round_floats(probs))

    views = pd.Series({
        c: sum(probs[c][s] * STANCE_RETURNS[s] for s in STANCE_RETURNS)
        for c in companies
    })
    logger.debug("Implied views (expected returns): %s", round_floats(views.to_dict()))

    max_entropy = math.log(len(STANCE_RETURNS))
    view_confidences = [1.0 - entropy(probs[c]) / max_entropy for c in companies]
    logger.info("View confidences: %s", round_floats(dict(zip(companies, view_confidences))))
    logger.info(
        "Each view's confidence is 1 minus the normalized Shannon entropy of its "
        "stance distribution (entropy divided by log(%d), the max possible entropy "
        "across %d stances): a classifier that is certain (probability mass on one "
        "stance) yields confidence near 1, while a uniform distribution yields confidence near 0.",
        len(STANCE_RETURNS), len(STANCE_RETURNS),
    )

    cov, pi = market_data(companies)

    bl = BlackLittermanModel(
        cov,
        pi=pi,
        absolute_views=views,
        omega="idzorek",
        view_confidences=view_confidences,
    )
    logger.info("Black-Litterman posterior returns: %s", round_floats(bl.bl_returns().to_dict()))
    logger.info(
        "Black-Litterman posterior returns blend the market-implied prior returns "
        "(derived from market-cap weights and the covariance matrix) with the "
        "classifier-implied views, weighted by the view confidences via Idzorek's "
        "method for the uncertainty matrix omega: higher-confidence views pull the "
        "posterior further from the prior and closer to the view."
    )

    ef = EfficientFrontier(bl.bl_returns(), bl.bl_cov())
    ef.max_sharpe()
    logger.info(
        "Max-Sharpe optimization solves for the tangency portfolio: the asset "
        "weights, constrained to sum to 1 with no shorting, that maximize the "
        "Sharpe ratio (expected portfolio return over portfolio volatility) using "
        "the Black-Litterman posterior returns and covariance computed above."
    )
    weights = dict(ef.clean_weights())
    logger.info("Max-Sharpe optimization complete: %s", round_floats(weights))
    return weights
