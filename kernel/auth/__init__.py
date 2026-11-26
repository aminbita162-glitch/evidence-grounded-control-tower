"""Kernel authentication and roles (Part 3 §3.15, §3.24, P11-T01).

Opaque high-entropy API tokens stored only as SHA-256 hashes with tenant,
role and expiry.  Signed, HTTP-only, same-site session cookies for later
views.  Roles: viewer, operator, reviewer, administrator (tenant-bound)
and platform operator (no tenant, deployment routes only).

Spec: Part 3 §3.15, §3.24; Part 4 §4.4; P11-T01.
"""
