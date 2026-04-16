# Contributing to QuICR

Thank you for your interest in QuICR. This document explains how to contribute effectively.

## Reporting Issues

File bugs and feature requests via [GitHub Issues](https://github.com/MorrisGlr/Automate-QuICR/issues). For bugs, include:
- Your operating system and Python version
- The command you ran and the full error output
- Whether the issue is reproducible with the synthetic test data in `data/`

## Submitting Pull Requests

1. Fork the repository and create a branch from `master`.
2. Set up the environment: `conda env create -f myenv.yml && conda activate quicr`
3. Make your changes and run the test suite: `pytest tests/ -v`
4. Open a pull request with a clear description of what changed and why.

## Clinical Domain Changes

Changes to system prompts (`prompt/system/`), JSON schemas (`prompt/json_schema/`), or severity/evidence logic (`src/severity/`, `src/evidence/`) require a clinical justification in the PR description — not just a technical rationale. These components encode attending-level review criteria; changes should be grounded in published guidelines or established QI standards.

## Code Conventions

- Follow the existing style in each module (no linter is enforced, but match the surrounding code).
- Do not add new Python dependencies without first checking whether SciSpaCy or spaCy already provides the capability.
- All inference calls must log token usage to `generated_output/<model>/usage/` — do not remove this instrumentation.
- Do not introduce PHI. All test data must be synthetic.

## License

By contributing, you agree that your contributions will be licensed under the [Apache License 2.0](LICENSE).
