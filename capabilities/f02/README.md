# Classification Judge

F02 evaluates a declared tariff code against a verified shipment description from F01. It resolves codes at the level of the active tariff index, validates the declared code at the evaluation instant and reports the most severe line outcome. The scorer uses deterministic BM25 overlap normalized against each candidate's own score. Verified applicability facts may trigger exclusions, which appear in the report.

The active synthetic pack uses English calibration. Arabic requires a closed glossary and a separate calibration bound to the same pack. The view records the language, each applied exclusion, calibration provenance and held-out and shifted diagnostics.

On the SYNTHETIC calibration distribution, and assuming exchangeability, the true code lies in the candidate set with probability at least 90 percent (marginal). This statement does not apply to real goods descriptions or to any single chapter.

Invoke F02 through the case evaluation API or the CLI evaluate capability filter. Only authorized tariff packs can participate in a case decision. The project has no verified tariff source for production activation.
