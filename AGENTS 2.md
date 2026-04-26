# Workspace Rules (uv + research)

## Environment
- Python env is managed by uv under: envs/
- Never use conda/poetry/pipenv.
- Never run `pip install` directly.
- If you need a dependency, ask to add it only under envs/<name>/ using `uv add`.
- Prefer explicit python path:
  - envs/base/.venv/bin/python
  - envs/qc/.venv/bin/python
  - envs/rl/.venv/bin/python

## Safety
- Do not modify system settings.
- Do not delete or overwrite files without making a backup copy.
- Keep changes incremental; avoid broad refactors.

## Output / Language
- Explanations in Japanese.