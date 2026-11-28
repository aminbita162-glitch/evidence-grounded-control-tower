# K14 synthetic extraction quality

The labelled subset of `data/scenarios/k14/cases.json` contains six single-document normalized values and six fields that must stay empty or flagged. It uses recorded candidates with the same deterministic grounding path as runtime.

| Measure | SYNTHETIC result |
| --- | ---: |
| Exact normalized values | 6 of 6 |
| Exact-match precision among released values | 6 of 6 |
| False fills among empty or flagged fields | 0 of 6 |

The cross-language goldens separately verify equal Arabic and English quantities and units, plus the expected flag when values differ. The fixture corpus does not measure live provider accuracy.
