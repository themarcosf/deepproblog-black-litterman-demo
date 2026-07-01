[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# DeepProbLog for Market Stance Classification

A toy example accompanying a scientific paper on neuro-symbolic reasoning for portfolio allocation. The system integrates **DeepProbLog** with a large language model (LLM) neural predicate to classify companies into market stances — *bullish*, *bearish*, or *neutral* — and feeds the resulting probability distributions into a **Black-Litterman** portfolio optimizer.

---

## Overview

Classical deep learning approaches to financial classification operate as black boxes: they learn from data alone, can memorize spurious correlations, and offer no mechanism to enforce domain constraints. DeepProbLog addresses these limitations by combining symbolic reasoning with learned or predicted probabilities.

This example demonstrates the following pipeline:

```
Financial profile (structured scores)
        │
        ▼
  LLM neural predicate (GPT-4o via LangChain)
  → P(bullish | company), P(bearish | company), P(neutral | company)
        │
        ▼
  DeepProbLog inference (ExactEngine)
  → market_stance probability per (company, stance) pair
        │
        ▼
  Black-Litterman model (PyPortfolioOpt)
  → optimal portfolio weights
```

The neural predicate is declared in Prolog as:

```prolog
nn(classifier, [Company], Stance, [bullish, bearish, neutral]) ::
    market_stance(Company, Stance).

bullish_company(Company) :-
    market_stance(Company, bullish).

bearish_company(Company) :-
    market_stance(Company, bearish).

neutral_company(Company) :-
    market_stance(Company, neutral).
```

DeepProbLog calls the LLM classifier whenever the logic engine needs to evaluate `market_stance`, binding the output probabilities to the symbolic proof tree. This allows logical rules (e.g., `bullish_company`) to compose over uncertain, LLM-derived facts in a principled probabilistic framework.

---

## Prerequisites

This project is intended to be run inside the provided Development Container (Dev Container). The container automatically installs and configures all required dependencies, including Python, SWI-Prolog, and the Python packages used by the example.

| Requirement | Notes |
|---|---|
| Dev Containers support | Available in VS Code, GitHub Codespaces, and compatible environments |
| `OPENAI_API_KEY` | **Must be set in the environment before running** |

No manual installation steps are required once the Dev Container has been created.

### Setting the API key

```bash
export OPENAI_API_KEY="sk-..."
```

The application will refuse to start if the key is absent.

---

## Installation

Opening the repository in the Dev Container automatically provisions:

- `deepproblog` — neuro-symbolic inference engine
- `langchain-core` / `langchain-openai` — LLM integration
- `pydantic` — structured output validation
- `pyportfolioopt` — Black-Litterman portfolio construction
- `pyswip` — Python bindings for SWI-Prolog
- Python 3.13 and SWI-Prolog runtime dependencies

No additional pip install commands are necessary.

---

## Usage

```bash
bash run.sh --run
```

The `--help` flag prints available options:

```bash
bash run.sh --help
```

### Expected output

```
INFO  Entering main execution.
INFO  Execution completed successfully.
INFO  Black-Litterman allocation:
INFO    acme:   XX.XX%
INFO    globex: XX.XX%
```

Weights reflect the posterior portfolio allocation after combining market-implied priors with LLM-derived views and their associated confidence (measured as normalized inverse entropy of the stance distribution).

---

## Project structure

```
src/
├── main.py              # Entry point: wires neural predicate, DeepProbLog, and optimizer
└── lib/
    ├── classifier.pl    # Prolog program: neural predicate declaration and stance rules
    ├── network.py       # CompanyClassifier — PyTorch nn.Module wrapping the LLM chain
    ├── allocation.py    # Black-Litterman model and portfolio optimization
    └── db.py            # Hard-coded company profiles (toy data)
```

---

## Reproducing the experiment

The company profiles in `src/lib/db.py` are hard-coded synthetic profiles for two fictional companies (`acme`, `globex`). To extend the experiment:

1. Add entries to the `COMPANIES` dictionary following the existing schema.
2. Register the corresponding Prolog terms in `src/main.py` (`companies` list).
3. Re-run with `bash run.sh --run`.

Model and temperature are configurable in `main.py` (`CompanyClassifier(model=..., temperature=...)`).

---

## Citation

If you use this code in your research, please cite the accompanying paper (reference to be added upon publication).
