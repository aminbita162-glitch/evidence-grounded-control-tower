"""Kernel cryptography — envelope encryption and key lifecycle (P11-T02).

One data key per tenant wrapped by a master key held by the secret store.
Payloads with personal or sensitive data are stored by reference and
encrypted.  Crypto-erasure destroys a tenant data key, after which
``verify --structural`` passes and ``verify --full`` reports ERASED.

Spec: Part 3 §3.5, §3.24; Part 4 §4.4; P11-T02.
"""
