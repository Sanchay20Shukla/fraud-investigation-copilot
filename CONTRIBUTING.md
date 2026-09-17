# Contributing

## Local development

1. Follow the [quick start](README.md#quick-start--windows) and generate demo data.
2. Create a focused branch for your change.
3. Make the change and run `python -m pytest -q`.
4. Update documentation and tests when behavior changes.
5. Open a pull request describing the problem, behavior change and validation.

Tests create their own temporary synthetic database and model. They do not require PaySim, a live OpenAI account or PostgreSQL. The GitHub Actions workflow runs the core test suite.

## Evidence and evaluation standards

- Keep labels and future transactions out of analyst-facing evidence.
- Preserve source IDs, policy sections, hashes and model versions.
- Explain SHAP contributions in log-odds, not percentage points or causal terms.
- Label synthetic policies, fixture data and uncalibrated probabilities clearly.
- Report metrics that were actually measured and describe the evaluation sample.
- Change review-band code and its policy documentation together.
- Add integration evidence before claiming Docker, PostgreSQL or a live provider has been verified.

## Repository hygiene

Do not commit `.env`, credentials, raw datasets, local databases, virtual environments or generated model binaries. Use `.env.example` for placeholder configuration. The bundled Docker passwords are explicitly local demo values, not deployment credentials.

Use issues for reproducible bugs and feature requests. Include the command, dependency versions and a minimal synthetic example; remove credentials and personal data from logs before sharing them.
