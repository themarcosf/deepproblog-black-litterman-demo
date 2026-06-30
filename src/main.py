################################################################################
# Date: 2026-03-23
################################################################################
import logging
import os
import sys
import time

from pathlib import Path

from deepproblog.engines import ExactEngine
from deepproblog.model import Model
from deepproblog.query import Query
from deepproblog.network import Network
from problog.logic import Term

from lib.allocation import (
    build_allocation,
    build_base_allocation,
    COMPANY_PARAMS,
    INTER_ASSET_CORR,
    RISK_AVERSION,
    STANCE_RETURNS,
)
from lib.network import CompanyClassifier

################################################################################
# Setup
################################################################################
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


################################################################################
# Main execution
################################################################################
if __name__ == "__main__":
    run_start = time.perf_counter()
    logger.debug("Log level set to %s.", LOG_LEVEL)

    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY is not set. Aborting.")
        sys.exit(1)

    logger.info("Entering main execution.")

    try:
        prolog = Path(__file__).parent / "lib" / "classifier.pl"
        logger.debug("Loading Prolog program from %s", prolog)

        nn = CompanyClassifier(model="gpt-4o", temperature=0.0)
        dpl_nn = Network(nn, "classifier")
        model = Model(str(prolog), [dpl_nn])
        model.set_engine(ExactEngine(model))
        logger.info("DeepProbLog model loaded with ExactEngine.")

        companies = [Term("acme"), Term("globex")]
        stances = ("bullish", "bearish", "neutral")

        queries = [
            Query(Term("market_stance", company, Term(s)))
            for company in companies
            for s in stances
        ]
        logger.info("Solving %d queries for companies: %s", len(queries), [c.functor for c in companies])

        solve_start = time.perf_counter()
        result = model.solve(queries)
        logger.info("DeepProbLog inference completed in %.2fs.", time.perf_counter() - solve_start)

        for entry in result:
            for term, tensor in entry.result.items():
                logger.debug("Query result: %s = %.4f", term, tensor)

        logger.info(
            "Black-Litterman hyperparameters: risk_aversion=%s, inter_asset_corr=%s, "
            "stance_returns=%s",
            RISK_AVERSION, INTER_ASSET_CORR, STANCE_RETURNS,
        )
        logger.info("Black-Litterman company params: %s", COMPANY_PARAMS)

        base_weights = build_base_allocation([c.functor for c in companies])
        weights = build_allocation(result)
    except Exception:
        logger.exception("Unhandled error after %.2fs; aborting.", time.perf_counter() - run_start)
        sys.exit(1)

    logger.info("Execution completed successfully in %.2fs.", time.perf_counter() - run_start)
    logger.info("Base portfolio (no classifier views) vs. classifier-informed allocation:")
    for company in weights:
        base = base_weights.get(company, 0.0)
        adjusted = weights[company]
        logger.info(
            f"  {company}: base={base:.2%}  adjusted={adjusted:.2%}  delta={adjusted - base:+.2%}"
        )
