"""Payload store tables — encrypted payload persistence (P11-T02).

Tables for encrypted payloads under the P04 migration lint (tenant policy
on every table).  The in-memory implementation is used for unit tests;
the PostgreSQL implementation uses the same schema with RLS enforced.

Spec: Part 3 §3.5, §3.24; Part 4 §4.4; P11-T02.
"""
