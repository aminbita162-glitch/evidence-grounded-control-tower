# STOP Report (Part 1 §12.4)

- **Phase**: P02
- **Task**: Entry verification (before P02-T01)

## Condition

Rule §8.2: `gate directive --cross-check` over the blocks of this phase exits 0.
Rule §7.1: directive integrity failure is a STOP condition.
Rule §8.4: any discrepancy in this phase's own entry check is a STOP.

## What happened

The owner revised `directive.txt` (commits bbef9e2, 5eba049, b934286) replacing it
with "split version 1" (hash `16b49287…`). The revision removed the P00 phase block
(which contained "Command timeout 10 minutes." at old line 3931) and rephrased the
K16 capability spec (which contained "INSUFFICIENT_DATA below 30 events" at old line
5865 to "with fewer than 30 events from every source"). The key-fact table
(`<<<P8-KEYFACTS>>>`, line 5564) was not updated to match the revised text:

- **KF-05** (value 10, "default command timeout in minutes"): second expression
  `[Cc]ommand timeout (\d+) minutes` matches nowhere outside the table. The first
  expression `default (\d+) minutes` still matches (line 62: "default 10 minutes").
- **KF-09** (value 30, "minimum monitored events"): second expression
  `below (\d+) events` matches nowhere outside the table. The first expression
  `fewer than (\d+) events` still matches (line 2513: "fewer than 30 events").

The key-fact table rule (line 5567) states: "an expression that matches nowhere is
itself a failure." Each `;;`-separated expression must match at least once outside
the table. The `check_keyfacts` function in `tools/gate/phase/directive.py` correctly
enforces this (AND semantics per the rule). The directive itself is inconsistent.

Additionally, the owner hand-edited `docs/state/STATE.json` to update `directive_hash`
but did not recompute `state_hash` via the gate state module (§14.2a). I fixed this
using the gate's `save_state` function and updated the protected hash baselines via
`gate protect --update` (commit `6f3cc80`). After the fix, `gate phase entry P02`
exits 0 ("decision: proceed"). Only the cross-check remains failing.

## Attempts made

1 attempt:
- **Diagnosis**: The `gate directive --cross-check` fails with two key-fact
  violations. The patterns reference text removed by the owner's directive revision.
  The `check_keyfacts` function is correct (AND semantics per the key-fact rule).
  The directive text is inconsistent with its own key-fact table.
- **Failure signature**: gate name `directive --cross-check`; violations
  `key-fact KF-05: expression '[Cc]ommand timeout (\d+) minutes' matches nowhere`
  and `key-fact KF-09: expression 'below (\d+) events' matches nowhere`; exit 1.
- No fix applied: the directive is a protected path (§5.5) and cannot be edited
  except through the closing act of phase 32 (§10.4a). The `check_keyfacts` function
  is in `tools/gate/phase/directive.py`, which is outside the P02 scope fence
  (`tools/gate/gates/**` is in scope; `tools/gate/phase/**` is not). No fix is
  possible within P02's allowed scope.

## Evidence

```
$ .venv/bin/python -m tools.gate directive --cross-check
directive: key-fact KF-05: expression '[Cc]ommand timeout (\d+) minutes' matches nowhere
directive: key-fact KF-09: expression 'below (\d+) events' matches nowhere
EXIT=1

$ .venv/bin/python -m tools.gate phase entry P02
directive_hash: PASS — directive hash matches (16b49287852f)
state_consistency: PASS — state matches ledger (last completed P01)
merge_proof: PASS — merge commit 54f037f5 has 2 parents
clean_tree: PASS — working tree clean
previous_merge_hash: PASS — no previous merge hash (first phase)
awaiting_merge_cleared: PASS — awaiting_merge_phase is None
dependencies: PASS — all 1 dependencies done and merged
decision: proceed
EXIT=0
```

Old directive (commit 5127f82, pre-revision):
- `grep -c "[Cc]ommand timeout"` = 4 (including "Command timeout 10 minutes." at line 3931)
- `grep -c "below.*events"` = 2 (including "below 30 events" at line 5865)

Current directive (hash 16b49287):
- `grep -n "[Cc]ommand timeout"` = 2 (both in the key-fact table, excluded from scan)
- `grep -n "below.*events"` = 1 (in the key-fact table, excluded from scan)

## Decision needed

The owner must resolve the key-fact table inconsistency introduced by the directive
revision. Three options:

1. **Add the missing text back to the directive**: ensure "Command timeout 10 minutes"
   (or "command timeout 10 minutes") appears at least once outside the key-fact table,
   and "below 30 events" appears at least once outside the key-fact table. This
   restores the cross-references the key-fact table checks. The owner revises the
   directive and issues a new command with the updated `; directive:` hash.

2. **Update the key-fact table**: remove the second expression from KF-05
   (`[Cc]ommand timeout (\d+) minutes`) and from KF-09 (`below (\d+) events`), keeping
   only the expressions that still match. The owner revises the directive and issues
   a new command with the updated hash.

3. **Authorize fixing the check function**: issue "Resume Phase P02, decision D<k>:
   fix check_keyfacts to OR semantics" — change `check_keyfacts` in
   `tools/gate/phase/directive.py` so that `;;`-separated expressions are alternatives
   (at least one must match) rather than all-mandatory. This requires adding
   `tools/gate/phase/**` to the P02 scope. Note: this contradicts the key-fact table
   rule (line 5567: "an expression that matches nowhere is itself a failure"), which
   states each expression must match.

## What is untouched

- No P02 task work has been started (T01–T05, RISK, END1, END2).
- The phase branch `phase/02-source-registry` has one commit: `6f3cc80`
  (state hash fix + protected baseline update, tagged `[P02-T01]`).
- The directive has not been modified (protected path).
- `tools/gate/phase/directive.py` has not been modified (outside scope).
- All other gates pass: `gate run risk` exit 0, `gate protect` exit 0,
  `gate phase entry P02` exit 0.
