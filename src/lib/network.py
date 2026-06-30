################################################################################
# Date: 2026-03-23
################################################################################
import logging
import time
import torch as t
import torch.nn as nn

from typing import cast

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from problog.logic import Term
from pydantic import BaseModel, Field, model_validator

from lib.db import COMPANIES

logger = logging.getLogger(__name__)


################################################################################
# Data structures
################################################################################
class MarketStanceOutput(BaseModel):
    bullish_confidence: int = Field(
        ge=0, le=100,
        description="Confidence that the company is in a bullish stance (0-100)."
    )
    bearish_confidence: int = Field(
        ge=0, le=100,
        description="Confidence that the company is in a bearish stance (0-100)."
    )
    neutral_confidence: int = Field(
        ge=0, le=100,
        description="Confidence that the company is in a neutral stance (0-100)."
    )
    reasoning: str = Field(
        description="Brief explanation of how the scores drove this classification."
    )

    @model_validator(mode="after")
    def confidences_must_sum_to_100(self) -> "MarketStanceOutput":
        total = self.bullish_confidence + self.bearish_confidence + self.neutral_confidence
        if total != 100:
            raise ValueError(
                f"Confidences must sum to 100, got {total}. "
                f"Redistribute: bullish={self.bullish_confidence}, "
                f"bearish={self.bearish_confidence}, "
                f"neutral={self.neutral_confidence}."
            )
        return self


################################################################################
# Prompt templates
################################################################################
SYSTEM_PROMPT = """\
You are a financial analysis engine acting as a neural predicate in a \
neuro-symbolic reasoning system. Your sole responsibility is to evaluate \
a company's financial profile and output a probability distribution over \
three market stances: bullish, bearish, and neutral.

All input scores are integers between 0 and 100, where higher is better.

Scoring guide:
  - valuation_score   : how attractively priced the company is (high = undervalued)
  - earnings_score    : overall earnings quality
    - stability_score : consistency of earnings over time
    - growth_score    : earnings growth trajectory
  - financial_score   : overall financial health
    - liquidity_score : ability to meet short-term obligations
    - debt_score      : leverage health (high = low problematic debt)
    - dividend_score  : dividend reliability and sustainability

Rules you must follow:
  1. bullish_confidence + bearish_confidence + neutral_confidence = 100 (exactly).
  2. Do not invent information beyond what is provided.
  3. Weight sub-scores (stability, growth, liquidity, debt, dividend) more \
granularly than their parent scores when they conflict.
  4. A company can be bullish on valuation but bearish on financials — \
reflect this tension in a lower bullish confidence, not a forced neutral.
"""

USER_PROMPT = """\
Company profile:
  Description     : {description}

  Valuation
    score         : {valuation_score}
    reasoning     : {valuation_reasoning}

  Earnings
    score         : {earnings_score}
    reasoning     : {earnings_reasoning}
    stability     : {stability_score}
    growth        : {growth_score}

  Financials
    score         : {financial_score}
    reasoning     : {financial_reasoning}
    liquidity     : {liquidity_score}
    debt          : {debt_score}
    dividend      : {dividend_score}

Classify this company's market stance and return your confidence distribution.
"""


################################################################################
# Public interface
################################################################################
class CompanyClassifier(nn.Module):
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.0):
        super().__init__()

        self.last_reasoning = None
        self._cache: dict[str, t.Tensor] = {}

        llm = ChatOpenAI(model=model, temperature=temperature)

        structured_llm = llm.with_structured_output(
            MarketStanceOutput,
            method="json_schema",
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human",  USER_PROMPT),
        ])

        self.chain = prompt | structured_llm

        logger.info("CompanyClassifier initialized (model=%s, temperature=%s).", model, temperature)

    def forward(self, company_name: Term) -> t.Tensor:
        name = company_name.functor

        if name in self._cache:
            logger.debug(
                "Cache hit for %s; skipping LLM call (cache holds %d entries).",
                name, len(self._cache),
            )
            return self._cache[name]

        data = COMPANIES.get(name)

        if not data:
            logger.error("No data available for company %s.", company_name)
            raise ValueError(f"No data available for company {company_name}.")

        logger.info("Invoking LLM classifier for %s.", name)
        logger.debug("Input scores for %s: %s", name, {
            k: v for k, v in data.items() if k.endswith("_score")
        })

        start = time.perf_counter()
        try:
            result = cast(MarketStanceOutput, self.chain.invoke({
                "description":        data.get("description", "N/A"),
                "valuation_score":    data["valuation_score"],
                "valuation_reasoning": data["valuation_reasoning"],
                "earnings_score":     data["earnings_score"],
                "earnings_reasoning": data["earnings_reasoning"],
                "stability_score":    data["earnings_details"]["stability_score"],
                "growth_score":       data["earnings_details"]["growth_score"],
                "financial_score":    data["financial_score"],
                "financial_reasoning": data["financial_reasoning"],
                "liquidity_score":    data["financial_details"]["liquidity_score"],
                "debt_score":         data["financial_details"]["debt_score"],
                "dividend_score":     data["financial_details"]["dividend_score"],
            }))
        except Exception:
            elapsed = time.perf_counter() - start
            logger.exception(
                "LLM classifier call for %s failed after %.2fs.", name, elapsed
            )
            raise
        elapsed = time.perf_counter() - start
        logger.info("LLM classifier call for %s completed in %.2fs.", name, elapsed)

        self.last_reasoning = result.reasoning

        logger.info(
            "LLM classification for %s: bullish=%d bearish=%d neutral=%d",
            name, result.bullish_confidence, result.bearish_confidence, result.neutral_confidence,
        )
        logger.debug("Reasoning for %s: %s", name, result.reasoning)

        self._cache[name] = t.tensor([
            result.bullish_confidence / 100.0,
            result.bearish_confidence / 100.0,
            result.neutral_confidence / 100.0,
        ])

        return self._cache[name]