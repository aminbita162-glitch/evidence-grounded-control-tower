"""Model Gateway adapters (Part 3 §3.11, D-06, P08).

The Gateway is the single door to language models.  No component outside
this package may call a provider directly — all calls go through the
:class:`~adapters.model.gateway.GatewayPort` interface.
"""
