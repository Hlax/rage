"""Repository layer: the only place allowed to write accepted graph tables.

Phase 0 stub. Later tickets add typed repositories for sources, chunks,
claims (staged/accepted/rejected with reasons), concepts, relationships,
score events, reports, cards, tickets, and safety audits per
``docs/agents/05_DATA_MODEL.md``.

Invariants for every future repository:
- Model output never reaches these writers without deterministic validation.
- Rejected claims are stored with rejection reasons, never discarded.
- Scores change only through append-only score events.
"""
