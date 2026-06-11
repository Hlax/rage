"""Durable memory layer (SQLite first).

The database is the system's memory; prompts are not memory. Only Python code
in this layer may write to accepted graph tables. Model clients never touch
this package. See ``docs/agents/05_DATA_MODEL.md``.
"""
