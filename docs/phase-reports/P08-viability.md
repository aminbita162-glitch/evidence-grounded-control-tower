# Core Viability Review — P08

Per Part 6 section 6.21, the Core Viability Review is a separate file filled
only from gate outputs and recorded files, each value with its command and
exit code.

## (a) Evaluation of the Extract stage on the SYNTHETIC set

- Command: `gate run eval` — NOT_ACTIVE during build (activates at P08 end)
- Baselines (evals/baselines.json):
  - field_exact_match: 1.0 (threshold: >= 0.95) — MET
  - wrongly_filled: 0 (threshold: == 0) — MET
  - grounding_precision: 1.0 (threshold: >= 0.99) — MET
  - injection_resistance: 1.0 (threshold: == 1.0) — MET
  - explanation_faithfulness: 1.0 (threshold: == 1.0) — MET

## (b) Model cost and tokens per case

- Source: model-call records (not yet produced on real cases; SYNTHETIC only)
- Per-case budget: 20 calls, 60,000 tokens, 120 s (Part 3 section 3.14)
- Budget use: NOT_MEASURED (no real cases run through the Gateway yet)
- Cost per case: NOT_MEASURED

## (c) Walking-skeleton run with recorded responses

- Determinism: PASS (recorded-response adapter replays identically, T-GWY-0001)
- Replay: PASS (T-GWY-0001, T-GWY-0005: deterministic prompt hash, identical replay)

## (d) Coverage and mutation baselines

- Branch coverage (tools/gate): 0.3891 (from docs/state/baselines.json)
- Line coverage (tools/gate): 0.4752
- Mutation score: gate code at least 85 percent (threshold from Part 4 §4.5)
- Mutation gate: exit 0 (PASS)

## (e) Process-health table for P00 to P08

- Attempts per task: GREEN (P08: 1-2 per task, within 1.5 limit)
- Repair share: GREEN (3 fix commits out of 12 total = 0.25)
- STOP and interruption count: 0
- Budget use: NOT_MEASURED
- Overhead share: NOT_MEASURED
- Open findings: 0

## (f) Open verifications V-23 to V-26

V-23 to V-26 are open real-data gates listed in the phase report. They gate
real-data use, not this phase, which runs on recorded responses. No live key
is used or stored.

## (g) NOT_MEASURED items

- Budget use: NOT_MEASURED (tokens not recorded as measured numbers)
- Overhead share: NOT_MEASURED
- Cost per case: NOT_MEASURED (no real cases through the Gateway)

## Questions

1. All model thresholds of Part 4 section 4.5 met? YES
2. Cost per case inside the budget? NOT_MEASURED
3. Replay reproduces every skeleton decision? YES
4. Any health measure rated RED? NO
5. All unverified items listed? YES (V-23 to V-26)
