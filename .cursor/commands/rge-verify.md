# RGE Verify

Run the strongest available verification for the current phase.

## Minimum

```bash
pytest
```

## If golden tests exist

```bash
pytest tests/golden
```

## If CLI exists

```bash
research --help
```

## If fixture run exists

```bash
research run --topic "Does AI improve creative output while reducing diversity?" --domain creativity --fixture-mode
```

## If public export exists

```bash
research export-public --limit 100
```

## If safety auditor exists

```bash
python -m rge.modules.safety_auditor --audit full
```

## If public site exists

```bash
cd apps/public-site && npm run build
```

## Reporting

Write results to an agent report in `agent_reports/`.

Do not hide failing tests. Do not modify code unless explicitly asked.
