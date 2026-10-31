# Local Environment Setup

## What this environment is for

The local environment gives this project an isolated Python installation and a declared set of dependencies. Isolation prevents packages required by one project from silently changing another project.

## Files involved

- `.venv/` — the local Python environment; generated and not committed.
- `pyproject.toml` — declares supported Python versions and dependencies.
- `.env.example` — documents required secret/configuration names safely.
- `.env` — your real local values; never committed.
- `.gitignore` — prevents secrets and generated files from entering Git.
- `src/eia_pipeline/` — importable project code.
- `tests/` — automated checks of project behavior.

## Activate the environment

From the project folder:

```bash
source .venv/bin/activate
```

Your shell prompt should normally show `(.venv)`. Activation changes which `python` and `pip` commands the shell finds first.

Verify it:

```bash
which python
python --version
```

`which python` should point inside this project's `.venv` folder.

## Deactivate the environment

```bash
deactivate
```

This returns the shell to its previous Python configuration.

## Install or refresh project dependencies

With the environment active:

```bash
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

Why use `python -m pip`? It makes the relationship explicit: use `pip` belonging to this exact Python interpreter.

Why use `-e`? Editable installation means changes under `src/` are reflected without reinstalling the project after every edit.

Why `.[dev]`? The dot means “this project,” while the `dev` extra installs development tools such as pytest and Ruff in addition to runtime packages.

## Run the first checks

```bash
python -m pytest
python -m ruff check .
```

- `pytest` runs behavioral tests.
- `ruff` finds common code-quality problems and keeps imports consistent.

## Configure the EIA API key

First obtain a personal key from the EIA Open Data registration page. Then create your private local configuration:

```bash
cp .env.example .env
```

Open `.env` and replace the empty value:

```text
EIA_API_KEY=your_real_key_here
```

Do not add quotation marks unless the value itself requires them, and do not share or commit the key.

## What is intentionally not installed yet

- PostgreSQL and its Python driver.
- dbt.
- Airflow.
- Jupyter and analysis packages.
- Tableau integration packages.

They will be introduced when their architectural phase begins. This keeps the first lesson focused on Python, HTTP requests, JSON, and EIA metadata.

