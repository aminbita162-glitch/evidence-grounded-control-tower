# K14 scan coverage

| Script | Corpus | Character error rate | Digit error rate |
| --- | --- | --- | --- |
| Latin | SYNTHETIC seeded scan | UNPROVEN | UNPROVEN |
| Arabic | Owner-provided V-31 fixtures pending | UNPROVEN | UNPROVEN |

The English scan and its reference are recorded under `data/scenarios/k14/scan/`. The run parameters contain no V-31 engine or training-data pins. Scan reading therefore returns `TEXT_UNAVAILABLE`. The fixture-based tests cover digest mismatch, an oversized scan, and the confidence and verification boundaries for recorded OCR lines.
