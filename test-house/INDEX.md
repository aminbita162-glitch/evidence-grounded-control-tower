# Test Index

| id | title | level | file | function |
|---|---|---|---|---|
| T-API-0001 | MISSING_FACT error code maps to problem response | fast | api/test_T_API_0001_to_0014.py | test_T_API_0001_missing_fact_problem |
| T-API-0002 | UNVERIFIED_FACT error code maps to problem response | fast | api/test_T_API_0001_to_0014.py | test_T_API_0002_unverified_fact_problem |
| T-API-0003 | WEAK_LABEL error code maps to problem response | fast | api/test_T_API_0001_to_0014.py | test_T_API_0003_weak_label_problem |
| T-API-0004 | RULE_FAILURE error code maps to problem response | fast | api/test_T_API_0001_to_0014.py | test_T_API_0004_rule_failure_problem |
| T-API-0005 | VERSION_CONFLICT error code maps to problem response | fast | api/test_T_API_0001_to_0014.py | test_T_API_0005_version_conflict_problem |
| T-API-0006 | IDEMPOTENCY_CONFLICT error code maps to problem response | fast | api/test_T_API_0001_to_0014.py | test_T_API_0006_idempotency_conflict_problem |
| T-API-0007 | UNKNOWN_TAG error code maps to problem response | fast | api/test_T_API_0001_to_0014.py | test_T_API_0007_unknown_tag_problem |
| T-API-0008 | INVALID_CONFIG error code maps to problem response | fast | api/test_T_API_0001_to_0014.py | test_T_API_0008_invalid_config_problem |
| T-API-0009 | REGION_POLICY error code maps to problem response | fast | api/test_T_API_0001_to_0014.py | test_T_API_0009_region_policy_problem |
| T-API-0010 | BUDGET_EXCEEDED error code maps to problem response | fast | api/test_T_API_0001_to_0014.py | test_T_API_0010_budget_exceeded_problem |
| T-API-0011 | QUARANTINED error code maps to problem response | fast | api/test_T_API_0001_to_0014.py | test_T_API_0011_quarantined_problem |
| T-API-0012 | Foreign id and missing id indistinguishable by status and body | fast | api/test_T_API_0001_to_0014.py | test_T_API_0012_foreign_and_missing_indistinguishable |
| T-API-0013 | Foreign id and missing id indistinguishable by timing class | fast | api/test_T_API_0001_to_0014.py | test_T_API_0013_foreign_and_missing_timing_class |
| T-API-0014 | Size limits are enforced | fast | api/test_T_API_0001_to_0014.py | test_T_API_0014_size_limits_enforced |
| T-API-0015 | OpenAPI document exists and is valid | fast | api/test_T_API_0015_to_0030.py | test_T_API_0015_openapi_exists |
| T-API-0016 | invoke route appears in the contract | fast | api/test_T_API_0015_to_0030.py | test_T_API_0016_invoke_route_in_contract |
| T-API-0017 | status route appears in the contract | fast | api/test_T_API_0015_to_0030.py | test_T_API_0017_status_route_in_contract |
| T-API-0018 | result route appears in the contract | fast | api/test_T_API_0015_to_0030.py | test_T_API_0018_result_route_in_contract |
| T-API-0019 | evidence route appears in the contract | fast | api/test_T_API_0015_to_0030.py | test_T_API_0019_evidence_route_in_contract |
| T-API-0020 | invoke returns a valid response | fast | api/test_T_API_0015_to_0030.py | test_T_API_0020_invoke_returns_valid_response |
| T-API-0021 | status returns a valid response | fast | api/test_T_API_0015_to_0030.py | test_T_API_0021_status_returns_valid_response |
| T-API-0022 | result returns a valid response | fast | api/test_T_API_0015_to_0030.py | test_T_API_0022_result_returns_valid_response |
| T-API-0023 | evidence returns a valid response | fast | api/test_T_API_0015_to_0030.py | test_T_API_0023_evidence_returns_valid_response |
| T-API-0024 | schema-driven test finds no server error on generated inputs | slow | api/test_T_API_0015_to_0030.py | test_T_API_0024_schema_driven_no_server_error |
| T-API-0025 | a seeded breaking change is reported | fast | api/test_T_API_0015_to_0030.py | test_T_API_0025_seeded_breaking_change_reported |
| T-API-0026 | documentation is served | fast | api/test_T_API_0015_to_0030.py | test_T_API_0026_documentation_served |
| T-API-0027 | OpenAPI version is 3.x | fast | api/test_T_API_0015_to_0030.py | test_T_API_0027_openapi_version_3x |
| T-API-0028 | every operation has an operation_id | fast | api/test_T_API_0015_to_0030.py | test_T_API_0028_every_operation_has_operation_id |
| T-API-0029 | every operation has a summary | fast | api/test_T_API_0015_to_0030.py | test_T_API_0029_every_operation_has_summary |
| T-API-0030 | contract gate verifies operations | fast | api/test_T_API_0015_to_0030.py | test_T_API_0030_contract_gate_verifies_operations |
| T-API-0031 | a repeated call returns the original result | fast | api/test_T_API_0031_to_0042.py | test_T_API_0031_repeated_call_returns_original |
| T-API-0032 | different key produces different result | fast | api/test_T_API_0031_to_0042.py | test_T_API_0032_different_key_different_result |
| T-API-0033 | concurrent identical calls produce one effect | fast | api/test_T_API_0031_to_0042.py | test_T_API_0033_concurrent_identical_one_effect |
| T-API-0034 | stale-version writes return the conflict code | fast | api/test_T_API_0031_to_0042.py | test_T_API_0034_stale_version_conflict_code |
| T-API-0035 | case creation is idempotent | fast | api/test_T_API_0031_to_0042.py | test_T_API_0035_case_creation_idempotent |
| T-API-0036 | document ingest is idempotent | fast | api/test_T_API_0031_to_0042.py | test_T_API_0036_document_ingest_idempotent |
| T-API-0037 | first approval wins | fast | api/test_T_API_0031_to_0042.py | test_T_API_0037_first_approval_wins |
| T-API-0038 | second approval with same key gets conflict | fast | api/test_T_API_0031_to_0042.py | test_T_API_0038_second_approval_conflict |
| T-API-0039 | idempotency record is stored | fast | api/test_T_API_0031_to_0042.py | test_T_API_0039_idempotency_record_stored |
| T-API-0040 | missing idempotency key on mutating call is rejected | fast | api/test_T_API_0031_to_0042.py | test_T_API_0040_missing_key_rejected |
| T-API-0041 | idempotency middleware preserves response body | fast | api/test_T_API_0031_to_0042.py | test_T_API_0041_preserves_response_body |
| T-API-0042 | version conflict on stale version | fast | api/test_T_API_0031_to_0042.py | test_T_API_0042_version_conflict_stale |
| T-API-0043 | ingest command exits 0 | fast | api/test_T_API_0043_to_0052.py | test_T_API_0043_ingest_exits_ok |
| T-API-0044 | evaluate command exits 0 | fast | api/test_T_API_0043_to_0052.py | test_T_API_0044_evaluate_exits_ok |
| T-API-0045 | replay command exits 0 | fast | api/test_T_API_0043_to_0052.py | test_T_API_0045_replay_exits_ok |
| T-API-0046 | verify-ledger works with no server | fast | api/test_T_API_0043_to_0052.py | test_T_API_0046_verify_ledger_no_server |
| T-API-0047 | prove works with no server | fast | api/test_T_API_0043_to_0052.py | test_T_API_0047_prove_no_server |
| T-API-0048 | export command exits 0 | fast | api/test_T_API_0043_to_0052.py | test_T_API_0048_export_exits_ok |
| T-API-0049 | skeleton runs through the command line | fast | api/test_T_API_0043_to_0052.py | test_T_API_0049_skeleton_cli |
| T-API-0050 | autonomy pause is role-gated and ledgered | fast | api/test_T_API_0043_to_0052.py | test_T_API_0050_autonomy_pause |
| T-API-0051 | autonomy freeze requires --confirm flag | fast | api/test_T_API_0043_to_0052.py | test_T_API_0051_freeze_requires_confirm |
| T-API-0052 | autonomy lift exits 0 | fast | api/test_T_API_0043_to_0052.py | test_T_API_0052_autonomy_lift |
| T-API-0053 | readiness fails when the database is down | fast | api/test_T_API_0053_to_0060.py | test_T_API_0053_readiness_fails_db_down |
| T-API-0054 | readiness passes when all dependencies are up | fast | api/test_T_API_0053_to_0060.py | test_T_API_0054_readiness_passes_all_up |
| T-API-0055 | shutdown mid-request loses no committed work | fast | api/test_T_API_0053_to_0060.py | test_T_API_0055_shutdown_no_lost_work |
| T-API-0056 | build-info shows the configuration hash | fast | api/test_T_API_0053_to_0060.py | test_T_API_0056_build_info_config_hash |
| T-API-0057 | health endpoint returns 200 | fast | api/test_T_API_0053_to_0060.py | test_T_API_0057_health_returns_200 |
| T-API-0058 | readiness checks storage | fast | api/test_T_API_0053_to_0060.py | test_T_API_0058_readiness_checks_storage |
| T-API-0059 | readiness checks policy engine | fast | api/test_T_API_0053_to_0060.py | test_T_API_0059_readiness_checks_policy_engine |
| T-API-0060 | readiness checks ledger signer | fast | api/test_T_API_0053_to_0060.py | test_T_API_0060_readiness_checks_ledger_signer |
| T-API-0061 | storage unavailable fault ends in ABSTAIN | fast | api/chaos/test_T_API_0061_to_0072.py | test_T_API_0061_storage_unavailable_abstain |
| T-API-0062 | model unavailable fault ends in ABSTAIN | fast | api/chaos/test_T_API_0061_to_0072.py | test_T_API_0062_model_unavailable_abstain |
| T-API-0063 | policy engine unavailable fault ends in ABSTAIN | fast | api/chaos/test_T_API_0061_to_0072.py | test_T_API_0063_policy_engine_unavailable_abstain |
| T-API-0064 | slow dependencies fault ends in ABSTAIN | fast | api/chaos/test_T_API_0061_to_0072.py | test_T_API_0064_slow_dependencies_abstain |
| T-API-0065 | storage fault produces no partial write | fast | api/chaos/test_T_API_0061_to_0072.py | test_T_API_0065_storage_no_partial_write |
| T-API-0066 | model fault produces no partial write | fast | api/chaos/test_T_API_0061_to_0072.py | test_T_API_0066_model_no_partial_write |
| T-API-0067 | policy engine fault produces no partial write | fast | api/chaos/test_T_API_0061_to_0072.py | test_T_API_0067_policy_no_partial_write |
| T-API-0068 | existence oracle mapped to test | fast | api/chaos/test_T_API_0061_to_0072.py | test_T_API_0068_existence_oracle_mapped |
| T-API-0069 | forged tenant identifier mapped to test | fast | api/chaos/test_T_API_0061_to_0072.py | test_T_API_0069_forged_tenant_mapped |
| T-API-0070 | search or aggregate endpoint mapped to test | fast | api/chaos/test_T_API_0061_to_0072.py | test_T_API_0070_search_aggregate_mapped |
| T-API-0071 | gate run chaos exits 0 | fast | api/chaos/test_T_API_0061_to_0072.py | test_T_API_0071_gate_run_chaos_exits_0 |
| T-API-0072 | gate run contract exits 0 | fast | api/chaos/test_T_API_0061_to_0072.py | test_T_API_0072_gate_run_contract_exits_0 |
| T-BASELINE-0001 | Empty baselines are seeded with the measured floor | fast | gate/test_baseline.py | test_update_baselines_seeds_empty |
| T-BASELINE-0002 | A higher measured value ratchets the floor up | fast | gate/test_baseline.py | test_update_baselines_ratchets_up |
| T-BASELINE-0003 | A lowered measured value is rejected and the floor is kept | fast | gate/test_baseline.py | test_update_baselines_rejects_decrease |
| T-BASELINE-0004 | Mixed measured values keep the improved key and reject the decreased one | fast | gate/test_baseline.py | test_update_baselines_mixed_up_and_down |
| T-BASELINE-0005 | check_baseline_decrease flags a lowered value | fast | gate/test_baseline.py | test_check_baseline_decrease_flags_and_clears |
| T-BASELINE-0006 | baselines.json validates against its schema | fast | gate/test_baseline.py | test_baselines_schema_valid_and_invalid |
| T-BASELINE-0007 | A missing measured component reports a decrease | fast | gate/test_baseline.py | test_check_baseline_decrease_missing_component |
| T-BCH-0001 | Same seed gives byte-identical output | fast | synthetic/test_T_BCH_0001_to_0012.py | test_T_BCH_0001_same_seed_byte_identical |
| T-BCH-0002 | Different seed gives different output | fast | synthetic/test_T_BCH_0001_to_0012.py | test_T_BCH_0002_different_seed_different_output |
| T-BCH-0003 | Every record carries the SYNTHETIC label | fast | synthetic/test_T_BCH_0001_to_0012.py | test_T_BCH_0003_every_record_labelled |
| T-BCH-0004 | Every record carries the seed | fast | synthetic/test_T_BCH_0001_to_0012.py | test_T_BCH_0004_every_record_carries_seed |
| T-BCH-0005 | Every record carries the factory version | fast | synthetic/test_T_BCH_0001_to_0012.py | test_T_BCH_0005_every_record_carries_factory_version |
| T-BCH-0006 | No deny-list name appears in output | fast | synthetic/test_T_BCH_0001_to_0012.py | test_T_BCH_0006_no_denylist_in_output |
| T-BCH-0007 | Arabic-Indic digits present in Arabic documents | fast | synthetic/test_T_BCH_0001_to_0012.py | test_T_BCH_0007_arabic_indic_digits |
| T-BCH-0008 | Persian digits present in Persian documents | fast | synthetic/test_T_BCH_0001_to_0012.py | test_T_BCH_0008_persian_digits |
| T-BCH-0009 | Factory is deterministic on regenerate | fast | synthetic/test_T_BCH_0001_to_0012.py | test_T_BCH_0009_deterministic_regenerate |
| T-BCH-0010 | Tariff rows have HS codes | fast | synthetic/test_T_BCH_0001_to_0012.py | test_T_BCH_0010_tariff_rows_have_hs_codes |
| T-BCH-0011 | Tenant feeds have entries | fast | synthetic/test_T_BCH_0001_to_0012.py | test_T_BCH_0011_tenant_feeds_have_entries |
| T-BCH-0012 | Labels gate passes on factory output | fast | synthetic/test_T_BCH_0001_to_0012.py | test_T_BCH_0012_labels_gate_factory_output |
| T-BCH-0013 | Bench runner is deterministic | fast | synthetic/test_T_BCH_0013_to_0022.py | test_T_BCH_0013_bench_deterministic |
| T-BCH-0014 | Unmet expectation fails with the scenario id | fast | synthetic/test_T_BCH_0013_to_0022.py | test_T_BCH_0014_unmet_expectation_fails |
| T-BCH-0015 | Met expectation passes | fast | synthetic/test_T_BCH_0013_to_0022.py | test_T_BCH_0015_met_expectation_passes |
| T-BCH-0016 | Scenario loading from JSON | fast | synthetic/test_T_BCH_0013_to_0022.py | test_T_BCH_0016_scenario_loading |
| T-BCH-0017 | Invalid scenario kind is rejected | fast | synthetic/test_T_BCH_0013_to_0022.py | test_T_BCH_0017_invalid_kind_rejected |
| T-BCH-0018 | Missing required fields are rejected | fast | synthetic/test_T_BCH_0013_to_0022.py | test_T_BCH_0018_missing_fields_rejected |
| T-BCH-0019 | Bench report counts are correct | fast | synthetic/test_T_BCH_0013_to_0022.py | test_T_BCH_0019_report_counts |
| T-BCH-0020 | Runner exception produces a failed entry | fast | synthetic/test_T_BCH_0013_to_0022.py | test_T_BCH_0020_runner_exception |
| T-BCH-0021 | All scenarios from the scenario directory pass | fast | synthetic/test_T_BCH_0013_to_0022.py | test_T_BCH_0021_all_scenarios_pass |
| T-BCH-0022 | Scenario without test_id has empty test_id | fast | synthetic/test_T_BCH_0013_to_0022.py | test_T_BCH_0022_no_test_id |
| T-BCH-0023 | Skeleton runs end-to-end without raising | fast | e2e/test_T_BCH_0023_to_0034.py | test_T_BCH_0023_skeleton_runs_e2e |
| T-BCH-0024 | Passport hash is a valid SHA-256 | fast | e2e/test_T_BCH_0023_to_0034.py | test_T_BCH_0024_passport_hash_valid |
| T-BCH-0025 | Same seed gives identical decision | fast | e2e/test_T_BCH_0023_to_0034.py | test_T_BCH_0025_same_seed_identical_decision |
| T-BCH-0026 | Passport replays to an equal hash | fast | e2e/test_T_BCH_0023_to_0034.py | test_T_BCH_0026_passport_replays_equal |
| T-BCH-0027 | Bundle verifies with the independent verifier | fast | e2e/test_T_BCH_0023_to_0034.py | test_T_BCH_0027_bundle_verifies |
| T-BCH-0028 | Structural verification passes | fast | e2e/test_T_BCH_0023_to_0034.py | test_T_BCH_0028_structural_verification |
| T-BCH-0029 | Decision is a valid DecisionValue | fast | e2e/test_T_BCH_0023_to_0034.py | test_T_BCH_0029_decision_valid |
| T-BCH-0030 | Stage failure produces a non-ALLOW decision | fast | e2e/test_T_BCH_0023_to_0034.py | test_T_BCH_0030_stage_failure_non_allow |
| T-BCH-0031 | Records cover all expected pipeline stages | fast | e2e/test_T_BCH_0023_to_0034.py | test_T_BCH_0031_records_cover_stages |
| T-BCH-0032 | Bundle hash is a valid SHA-256 | fast | e2e/test_T_BCH_0023_to_0034.py | test_T_BCH_0032_bundle_hash_valid |
| T-BCH-0033 | Reason codes are non-empty for non-ALLOW decisions | fast | e2e/test_T_BCH_0023_to_0034.py | test_T_BCH_0033_reason_codes_nonempty |
| T-BCH-0034 | Skeleton imports no capability internals | fast | e2e/test_T_BCH_0023_to_0034.py | test_T_BCH_0034_no_capability_internals |
| T-BCH-0035 | Harness starts cleanly | fast | e2e/test_T_BCH_0035_to_0042.py | test_T_BCH_0035_harness_starts |
| T-BCH-0036 | Harness stops cleanly | fast | e2e/test_T_BCH_0035_to_0042.py | test_T_BCH_0036_harness_stops |
| T-BCH-0037 | Harness raises when not started | fast | e2e/test_T_BCH_0035_to_0042.py | test_T_BCH_0037_harness_not_started_raises |
| T-BCH-0038 | Two-tenant scenario runs | fast | e2e/test_T_BCH_0035_to_0042.py | test_T_BCH_0038_two_tenant_runs |
| T-BCH-0039 | Two-tenant scenario finds zero cross-tenant reads | fast | e2e/test_T_BCH_0035_to_0042.py | test_T_BCH_0039_zero_cross_tenant_reads |
| T-BCH-0040 | Two-tenant scenario has two tenants | fast | e2e/test_T_BCH_0035_to_0042.py | test_T_BCH_0040_two_tenants_present |
| T-BCH-0041 | Output identical across two runs with same seed | fast | e2e/test_T_BCH_0035_to_0042.py | test_T_BCH_0041_identical_output_same_seed |
| T-BCH-0042 | Tenant decisions are non-ALLOW | fast | e2e/test_T_BCH_0035_to_0042.py | test_T_BCH_0042_tenant_decisions_non_allow |
| T-BCH-0043 | Matrix builds without error | fast | e2e/test_T_BCH_0043_to_0054.py | test_T_BCH_0043_matrix_builds |
| T-BCH-0044 | Matrix includes test IDs | fast | e2e/test_T_BCH_0043_to_0054.py | test_T_BCH_0044_matrix_has_tests |
| T-BCH-0045 | Matrix includes scenario IDs | fast | e2e/test_T_BCH_0043_to_0054.py | test_T_BCH_0045_matrix_has_scenarios |
| T-BCH-0046 | A scenario without a test fails when seeded | fast | e2e/test_T_BCH_0043_to_0054.py | test_T_BCH_0046_scenario_without_test_broken |
| T-BCH-0047 | A scenario referencing an unknown test fails when seeded | fast | e2e/test_T_BCH_0043_to_0054.py | test_T_BCH_0047_test_without_scenario_broken |
| T-BCH-0048 | A risk without a control fails when seeded | fast | e2e/test_T_BCH_0043_to_0054.py | test_T_BCH_0048_risk_without_control_broken |
| T-BCH-0049 | A control without a test is advisory | fast | e2e/test_T_BCH_0043_to_0054.py | test_T_BCH_0049_control_without_test_advisory |
| T-BCH-0050 | Matrix is reproducible | fast | e2e/test_T_BCH_0043_to_0054.py | test_T_BCH_0050_matrix_reproducible |
| T-BCH-0051 | gate run trace exits 0 | fast | e2e/test_T_BCH_0043_to_0054.py | test_T_BCH_0051_gate_trace_exits_0 |
| T-BCH-0052 | Report is valid JSON | fast | e2e/test_T_BCH_0043_to_0054.py | test_T_BCH_0052_report_valid_json |
| T-BCH-0053 | Matrix includes risks and controls | fast | e2e/test_T_BCH_0043_to_0054.py | test_T_BCH_0053_matrix_has_risks_controls |
| T-BCH-0054 | No broken links in the real repo | fast | e2e/test_T_BCH_0043_to_0054.py | test_T_BCH_0054_no_broken_links_real |
| T-BCH-0055 | Sets reproduce for a fixed seed | fast | synthetic/test_T_BCH_0055_to_0060.py | test_T_BCH_0055_sets_reproduce |
| T-BCH-0056 | Calibration set has known score distribution | fast | synthetic/test_T_BCH_0055_to_0060.py | test_T_BCH_0056_calibration_score_distribution |
| T-BCH-0057 | Test set has known score distribution | fast | synthetic/test_T_BCH_0055_to_0060.py | test_T_BCH_0057_test_score_distribution |
| T-BCH-0058 | Exchangeability holds by construction | fast | synthetic/test_T_BCH_0055_to_0060.py | test_T_BCH_0058_exchangeability |
| T-BCH-0059 | Artifact IDs are stable | fast | synthetic/test_T_BCH_0055_to_0060.py | test_T_BCH_0059_artifact_ids_stable |
| T-BCH-0060 | Coverage statements carry the SYNTHETIC label | fast | synthetic/test_T_BCH_0055_to_0060.py | test_T_BCH_0060_synthetic_label |
| T-BCH-0061 | Eval thresholds hold on the larger set | fast | e2e/test_T_BCH_0061_to_0066.py | test_T_BCH_0061_thresholds_hold_larger_set |
| T-BCH-0062 | Refreshed recording is a recorded event | fast | e2e/test_T_BCH_0061_to_0066.py | test_T_BCH_0062_recording_is_recorded_event |
| T-BCH-0063 | Factory output replaces small fixtures | fast | e2e/test_T_BCH_0061_to_0066.py | test_T_BCH_0063_factory_output_replaces_fixtures |
| T-BCH-0064 | Baselines carry over and may only improve | fast | e2e/test_T_BCH_0061_to_0066.py | test_T_BCH_0064_baselines_carry_over |
| T-BCH-0065 | Eval set is SYNTHETIC-labeled | fast | e2e/test_T_BCH_0061_to_0066.py | test_T_BCH_0065_synthetic_label |
| T-BCH-0066 | Recorded set is deterministic for the same seed | fast | e2e/test_T_BCH_0061_to_0066.py | test_T_BCH_0066_recorded_deterministic |
| T-BCH-0067 | Packet is reproducible | fast | review/test_T_BCH_0067_to_0074.py | test_T_BCH_0067_packet_reproducible |
| T-BCH-0068 | Packet contains no code | fast | review/test_T_BCH_0067_to_0074.py | test_T_BCH_0068_packet_no_code |
| T-BCH-0069 | Changed scenario changes hash → CHANGED_SINCE_REVIEW | fast | review/test_T_BCH_0067_to_0074.py | test_T_BCH_0069_changed_scenario_changes_status |
| T-BCH-0070 | A capability without a line is UNREVIEWED | fast | review/test_T_BCH_0067_to_0074.py | test_T_BCH_0070_unreviewed |
| T-BCH-0071 | A line with the current hash gives REVIEWED | fast | review/test_T_BCH_0067_to_0074.py | test_T_BCH_0071_reviewed |
| T-BCH-0072 | A malformed line or unknown kind fails | fast | review/test_T_BCH_0067_to_0074.py | test_T_BCH_0072_malformed_line_fails |
| T-BCH-0073 | A malformed hash fails | fast | review/test_T_BCH_0067_to_0074.py | test_T_BCH_0073_malformed_hash_fails |
| T-BCH-0074 | Status file equals the generated one | fast | review/test_T_BCH_0067_to_0074.py | test_T_BCH_0074_status_file_roundtrip |
| T-CI-0001 | CI workflows use only gate and build steps with actions pinned by hash | fast | gate/test_ci.py | test_ci_workflows_structure |
| T-DATA-0001 | Label strength order is a total preorder with stated tie | fast | data/test_T_DATA_0001_to_0006.py | test_T_DATA_0001_label_order |
| T-DATA-0002 | SIMULATED_RULE and SYNTHETIC are tied in strength | fast | data/test_T_DATA_0001_to_0006.py | test_T_DATA_0002_simulated_rule_synthetic_tied |
| T-DATA-0003 | weakest_of is commutative | fast | data/test_T_DATA_0001_to_0006.py | test_T_DATA_0003_weakest_of_commutative |
| T-DATA-0004 | weakest_of is associative | fast | data/test_T_DATA_0001_to_0006.py | test_T_DATA_0004_weakest_of_associative |
| T-DATA-0005 | weakest_of is idempotent | fast | data/test_T_DATA_0001_to_0006.py | test_T_DATA_0005_weakest_of_idempotent_pair |
| T-DATA-0006 | Only OFFICIAL and DERIVED are ALLOW-eligible; unknown label rejected | fast | data/test_T_DATA_0001_to_0006.py | test_T_DATA_0006_allow_eligible |
| T-DATA-0007 | Missing required field fails validation | fast | data/test_T_DATA_0007_to_0014.py | test_T_DATA_0007_missing_field_fails |
| T-DATA-0008 | Duplicate source_id fails validation | fast | data/test_T_DATA_0007_to_0014.py | test_T_DATA_0008_duplicate_id_fails |
| T-DATA-0009 | Day-level retrieved_month date fails validation | fast | data/test_T_DATA_0007_to_0014.py | test_T_DATA_0009_day_level_date_fails |
| T-DATA-0010 | Valid entry passes validation | fast | data/test_T_DATA_0007_to_0014.py | test_T_DATA_0010_valid_entry_passes |
| T-DATA-0011 | Changed entry without baseline update fails | fast | data/test_T_DATA_0007_to_0014.py | test_T_DATA_0011_changed_entry_without_baseline_fails |
| T-DATA-0012 | New entry not in baseline fails | fast | data/test_T_DATA_0007_to_0014.py | test_T_DATA_0012_new_entry_without_baseline_fails |
| T-DATA-0013 | update_baseline writes correct entry hashes | fast | data/test_T_DATA_0007_to_0014.py | test_T_DATA_0013_update_baseline_writes_correct_hashes |
| T-DATA-0014 | Invalid source_id format fails validation | fast | data/test_T_DATA_0007_to_0014.py | test_T_DATA_0014_invalid_source_id_format_fails |
| T-DATA-0015 | Uncovered data file fails the data gate | fast | data/test_T_DATA_0015_to_0022.py | test_T_DATA_0015_uncovered_file_fails |
| T-DATA-0016 | UNVERIFIED license on a used dataset fails the data gate | fast | data/test_T_DATA_0015_to_0022.py | test_T_DATA_0016_unverified_license_fails |
| T-DATA-0017 | Third-party copyright table detection | fast | data/test_T_DATA_0015_to_0022.py | test_T_DATA_0017_third_party_table_detected |
| T-DATA-0018 | Gap entry without verification id fails | fast | data/test_T_DATA_0015_to_0022.py | test_T_DATA_0018_gap_without_verification_id_fails |
| T-DATA-0019 | Manifest missing required field fails | fast | data/test_T_DATA_0015_to_0022.py | test_T_DATA_0019_manifest_missing_field_fails |
| T-DATA-0020 | Gap entry missing required field fails | fast | data/test_T_DATA_0015_to_0022.py | test_T_DATA_0020_gap_missing_field_fails |
| T-DATA-0021 | Invalid redistribution_permission fails | fast | data/test_T_DATA_0015_to_0022.py | test_T_DATA_0021_invalid_redistribution_permission_fails |
| T-DATA-0022 | Gap entry invalid next_check date fails | fast | data/test_T_DATA_0015_to_0022.py | test_T_DATA_0022_gap_invalid_date_fails |
| T-DATA-0023 | Seed entry count equals 20 | fast | data/test_T_DATA_0023_to_0024.py | test_T_DATA_0023_seed_entry_count_equals_20 |
| T-DATA-0024 | All fields valid and data V-items covered | fast | data/test_T_DATA_0023_to_0024.py | test_T_DATA_0024_all_fields_valid_and_v_items_covered |
| T-DATA-0025 | docs/dependencies.json regenerates byte-identically | fast | data/test_T_DATA_0025_to_0030.py | test_T_DATA_0025_dependencies_json_regenerates_identically |
| T-DATA-0026 | Source without manifest fails data gate | fast | data/test_T_DATA_0025_to_0030.py | test_T_DATA_0026_dependency_missing_from_registry_fails_data_gate |
| T-DATA-0027 | Registry entry without label fails labels gate | fast | data/test_T_DATA_0025_to_0030.py | test_T_DATA_0027_record_without_label_fails_labels_gate |
| T-DATA-0028 | Registry entry with unknown label fails labels gate | fast | data/test_T_DATA_0025_to_0030.py | test_T_DATA_0028_record_with_unknown_label_fails_labels_gate |
| T-DATA-0029 | Manifest source_id absent from registry fails labels gate | fast | data/test_T_DATA_0025_to_0030.py | test_T_DATA_0029_source_id_absent_from_registry_fails_labels_gate |
| T-DATA-0030 | Data and labels gates pass on the live repository | fast | data/test_T_DATA_0025_to_0030.py | test_T_DATA_0030_live_data_and_labels_gates_pass |
| T-DB-0001 | Roles have exactly the stated privileges | slow | persistence/test_T_DB_0001_to_0008.py | test_T_DB_0001_role_privileges |
| T-DB-0002 | Application role cannot create tables | slow | persistence/test_T_DB_0001_to_0008.py | test_T_DB_0002_application_cannot_create |
| T-DB-0003 | Application role cannot alter tables | slow | persistence/test_T_DB_0001_to_0008.py | test_T_DB_0003_application_cannot_alter |
| T-DB-0004 | Application role cannot drop tables | slow | persistence/test_T_DB_0001_to_0008.py | test_T_DB_0004_application_cannot_drop |
| T-DB-0005 | Ephemeral database starts from the lock file only | slow | persistence/test_T_DB_0001_to_0008.py | test_T_DB_0005_ephemeral_starts_from_lock_file |
| T-DB-0006 | Migration owner can create tables | slow | persistence/test_T_DB_0001_to_0008.py | test_T_DB_0006_migration_owner_can_create |
| T-DB-0007 | Audit role is read-only | slow | persistence/test_T_DB_0001_to_0008.py | test_T_DB_0007_audit_readonly |
| T-DB-0008 | Gate run integration exits 0 | slow | persistence/test_T_DB_0001_to_0008.py | test_T_DB_0008_gate_run_integration |
| T-DB-0009 | Every persisted entity has a table | slow | persistence/test_T_DB_0009_to_0018.py | test_T_DB_0009_every_entity_has_table |
| T-DB-0010 | Table without tenant_id fails the migration lint | fast | persistence/test_T_DB_0009_to_0018.py | test_T_DB_0010_table_without_tenant_id_fails_lint |
| T-DB-0011 | Generated schema regenerates byte-identical | fast | persistence/test_T_DB_0009_to_0018.py | test_T_DB_0011_generated_schema_byte_identical |
| T-DB-0012 | Foreign-tenant row cannot satisfy a foreign key | slow | persistence/test_T_DB_0009_to_0018.py | test_T_DB_0012_foreign_tenant_fk_rejected |
| T-DB-0013 | No SERIAL columns or shared sequences | fast | persistence/test_T_DB_0009_to_0018.py | test_T_DB_0013_no_serial_columns |
| T-DB-0014 | Every table has schema_version | fast | persistence/test_T_DB_0009_to_0018.py | test_T_DB_0014_every_table_has_schema_version |
| T-DB-0015 | Every table has a time-sortable primary key (id TEXT) | fast | persistence/test_T_DB_0009_to_0018.py | test_T_DB_0015_every_table_has_id_primary_key |
| T-DB-0016 | Tenant-scoped uniqueness | fast | persistence/test_T_DB_0009_to_0018.py | test_T_DB_0016_tenant_scoped_uniqueness |
| T-DB-0017 | Expand-then-contract convention recorded in migration header | fast | persistence/test_T_DB_0009_to_0018.py | test_T_DB_0017_expand_then_contract_header |
| T-DB-0018 | Generator output is deterministic | fast | persistence/test_T_DB_0009_to_0018.py | test_T_DB_0018_generator_deterministic |
| T-DB-0019 | No read without a tenant setting | slow | persistence/test_T_DB_0019_to_0034.py | test_T_DB_0019_no_read_without_tenant |
| T-DB-0020 | No write without a tenant setting | slow | persistence/test_T_DB_0019_to_0034.py | test_T_DB_0020_no_write_without_tenant |
| T-DB-0021 | Foreign tenant sees zero rows | slow | persistence/test_T_DB_0019_to_0034.py | test_T_DB_0021_foreign_tenant_sees_zero |
| T-DB-0022 | Forced RLS applies to table owner | slow | persistence/test_T_DB_0019_to_0034.py | test_T_DB_0022_forced_policy_on_owner |
| T-DB-0023 | Pooled connection setting does not leak | slow | persistence/test_T_DB_0019_to_0034.py | test_T_DB_0023_pooled_connection_no_leak |
| T-DB-0024 | Lint rejects table without RLS policy | fast | persistence/test_T_DB_0019_to_0034.py | test_T_DB_0024_lint_rejects_table_without_policy |
| T-DB-0025 | Tenant context requires a principal | fast | persistence/test_T_DB_0019_to_0034.py | test_T_DB_0025_tenant_context_requires_principal |
| T-DB-0026 | RLS enabled on every table | slow | persistence/test_T_DB_0019_to_0034.py | test_T_DB_0026_rls_enabled_every_table |
| T-DB-0027 | RLS forced on every table | slow | persistence/test_T_DB_0019_to_0034.py | test_T_DB_0027_rls_forced_every_table |
| T-DB-0028 | Write with tenant setting succeeds | slow | persistence/test_T_DB_0019_to_0034.py | test_T_DB_0028_write_with_tenant_succeeds |
| T-DB-0029 | Write with mismatched tenant fails | slow | persistence/test_T_DB_0019_to_0034.py | test_T_DB_0029_mismatched_tenant_write_fails |
| T-DB-0030 | Every table has an RLS policy | slow | persistence/test_T_DB_0019_to_0034.py | test_T_DB_0030_every_table_has_policy |
| T-DB-0031 | Tenant context set_sql produces valid SQL | fast | persistence/test_T_DB_0019_to_0034.py | test_T_DB_0031_tenant_context_set_sql |
| T-DB-0032 | Security definer lint catches unlisted functions | fast | persistence/test_T_DB_0019_to_0034.py | test_T_DB_0032_security_definer_lint |
| T-DB-0033 | RLS lint passes on the actual migration files | fast | persistence/test_T_DB_0019_to_0034.py | test_T_DB_0033_rls_lint_on_migrations |
| T-DB-0034 | Read with matching tenant succeeds | slow | persistence/test_T_DB_0019_to_0034.py | test_T_DB_0034_read_with_matching_tenant |
| T-DB-0035 | In-memory repository get returns None for missing entity | fast | persistence/test_T_DB_0035_to_0048.py | test_T_DB_0035_inmem_get_missing |
| T-DB-0036 | In-memory repository insert and get | fast | persistence/test_T_DB_0035_to_0048.py | test_T_DB_0036_inmem_insert_get |
| T-DB-0037 | In-memory repository stale version rejected | fast | persistence/test_T_DB_0035_to_0048.py | test_T_DB_0037_inmem_stale_version |
| T-DB-0038 | In-memory repository delete | fast | persistence/test_T_DB_0035_to_0048.py | test_T_DB_0038_inmem_delete |
| T-DB-0039 | In-memory repository list is tenant-scoped | fast | persistence/test_T_DB_0035_to_0048.py | test_T_DB_0039_inmem_tenant_scoped_list |
| T-DB-0040 | PostgreSQL repository get returns None for missing entity | slow | persistence/test_T_DB_0035_to_0048.py | test_T_DB_0040_pg_get_missing |
| T-DB-0041 | PostgreSQL repository insert and get | slow | persistence/test_T_DB_0035_to_0048.py | test_T_DB_0041_pg_insert_get |
| T-DB-0042 | PostgreSQL repository stale version rejected | slow | persistence/test_T_DB_0035_to_0048.py | test_T_DB_0042_pg_stale_version |
| T-DB-0043 | PostgreSQL repository delete | slow | persistence/test_T_DB_0035_to_0048.py | test_T_DB_0043_pg_delete |
| T-DB-0044 | PostgreSQL repository list is tenant-scoped | slow | persistence/test_T_DB_0035_to_0048.py | test_T_DB_0044_pg_tenant_scoped_list |
| T-DB-0045 | Contract test suite runs against both implementations | fast | persistence/test_T_DB_0035_to_0048.py | test_T_DB_0045_contract_suite_both |
| T-DB-0046 | Stale version write rejected with ConflictError | fast | persistence/test_T_DB_0035_to_0048.py | test_T_DB_0046_stale_version_conflict_error |
| T-DB-0047 | Repository protocol requires a TenantContext parameter | fast | persistence/test_T_DB_0035_to_0048.py | test_T_DB_0047_protocol_requires_tenant_context |
| T-DB-0048 | Query without tenant context fails at run time | slow | persistence/test_T_DB_0035_to_0048.py | test_T_DB_0048_no_tenant_context_fails |
| T-DB-0049 | Unit of work rolls back on outbox failure | fast | persistence/test_T_DB_0049_to_0060.py | test_T_DB_0049_uow_rollback_on_failure |
| T-DB-0050 | Idempotency store returns original result for repeated command | fast | persistence/test_T_DB_0049_to_0060.py | test_T_DB_0050_idempotency_returns_original |
| T-DB-0051 | Concurrent identical commands produce one effect | fast | persistence/test_T_DB_0049_to_0060.py | test_T_DB_0051_concurrent_one_effect |
| T-DB-0052 | Dead-lettered event is visible and not lost | fast | persistence/test_T_DB_0049_to_0060.py | test_T_DB_0052_dead_letter_visible |
| T-DB-0053 | Unit of work atomic commit | fast | persistence/test_T_DB_0049_to_0060.py | test_T_DB_0053_uow_atomic_commit |
| T-DB-0054 | Outbox relay delivers each event exactly once | fast | persistence/test_T_DB_0049_to_0060.py | test_T_DB_0054_outbox_deliver_once |
| T-DB-0055 | Outbox does not re-deliver | fast | persistence/test_T_DB_0049_to_0060.py | test_T_DB_0055_outbox_no_redelivery |
| T-DB-0056 | Idempotency store is tenant-keyed | fast | persistence/test_T_DB_0049_to_0060.py | test_T_DB_0056_idempotency_tenant_keyed |
| T-DB-0057 | Idempotency store clear | fast | persistence/test_T_DB_0049_to_0060.py | test_T_DB_0057_idempotency_clear |
| T-DB-0058 | Dead letter entry fields | fast | persistence/test_T_DB_0049_to_0060.py | test_T_DB_0058_dead_letter_fields |
| T-DB-0059 | Outbox entry fields | fast | persistence/test_T_DB_0049_to_0060.py | test_T_DB_0059_outbox_entry_fields |
| T-DB-0060 | Outbox pending entries | fast | persistence/test_T_DB_0049_to_0060.py | test_T_DB_0060_outbox_pending |
| T-DB-0061 | UPDATE on append-only table fails | slow | persistence/test_T_DB_0061_to_0068.py | test_T_DB_0061_update_append_only_fails |
| T-DB-0062 | DELETE on append-only table fails | slow | persistence/test_T_DB_0061_to_0068.py | test_T_DB_0062_delete_append_only_fails |
| T-DB-0063 | Grant UPDATE on append-only table fails lint | fast | persistence/test_T_DB_0061_to_0068.py | test_T_DB_0063_grant_update_fails_lint |
| T-DB-0064 | Forward migration on seeded data passes | slow | persistence/test_T_DB_0061_to_0068.py | test_T_DB_0064_forward_migration_passes |
| T-DB-0065 | Gate run migration exits 0 | slow | persistence/test_T_DB_0061_to_0068.py | test_T_DB_0065_gate_run_migration |
| T-DB-0066 | Append-only lint catches GRANT UPDATE | fast | persistence/test_T_DB_0061_to_0068.py | test_T_DB_0066_lint_catches_grant_update |
| T-DB-0067 | Append-only lint catches GRANT DELETE | fast | persistence/test_T_DB_0061_to_0068.py | test_T_DB_0067_lint_catches_grant_delete |
| T-DB-0068 | Append-only tables identified correctly | fast | persistence/test_T_DB_0061_to_0068.py | test_T_DB_0068_append_only_tables_identified |
| T-DB-0069 | Kill point before_commit recovers | fast | persistence/test_T_DB_0069_to_0078.py | test_T_DB_0069_kill_before_commit |
| T-DB-0070 | Kill point after_commit_before_outbox recovers | fast | persistence/test_T_DB_0069_to_0078.py | test_T_DB_0070_kill_after_commit_before_outbox |
| T-DB-0071 | Kill point during_delivery recovers | fast | persistence/test_T_DB_0069_to_0078.py | test_T_DB_0071_kill_during_delivery |
| T-DB-0072 | Kill point during_migration recovers | fast | persistence/test_T_DB_0069_to_0078.py | test_T_DB_0072_kill_during_migration |
| T-DB-0073 | No partial write visible after recovery | fast | persistence/test_T_DB_0069_to_0078.py | test_T_DB_0073_no_partial_write |
| T-DB-0074 | Lab reports registered kill points | fast | persistence/test_T_DB_0069_to_0078.py | test_T_DB_0074_lab_reports_kill_points |
| T-DB-0075 | Lab fails if registered point has no scenario | fast | persistence/test_T_DB_0069_to_0078.py | test_T_DB_0075_missing_scenario_fails |
| T-DB-0076 | Scenario compares by hash | fast | persistence/test_T_DB_0069_to_0078.py | test_T_DB_0076_scenario_compares_by_hash |
| T-DB-0077 | Lab is a shared tool | fast | persistence/test_T_DB_0069_to_0078.py | test_T_DB_0077_lab_shared_tool |
| T-DB-0078 | All kill points recover to equal state | fast | persistence/test_T_DB_0069_to_0078.py | test_T_DB_0078_all_points_recover |
| T-DB-0079 | Catalog parses to the full item list | fast | tenancy/test_T_DB_0079_to_0084.py | test_T_DB_0079_catalog_full_list |
| T-DB-0080 | Item without test is listed | fast | tenancy/test_T_DB_0079_to_0084.py | test_T_DB_0080_item_without_test_listed |
| T-DB-0081 | Mapping covers identifier-reference items | fast | tenancy/test_T_DB_0079_to_0084.py | test_T_DB_0081_identifier_coverage |
| T-DB-0082 | Mapping covers RLS bypass items | fast | tenancy/test_T_DB_0079_to_0084.py | test_T_DB_0082_rls_bypass_coverage |
| T-DB-0083 | Mapping covers pooled-connection items | fast | tenancy/test_T_DB_0079_to_0084.py | test_T_DB_0083_pooled_connection_coverage |
| T-DB-0084 | Mapping covers shared-sequence items | fast | tenancy/test_T_DB_0079_to_0084.py | test_T_DB_0084_shared_sequence_coverage |
| T-DOCS-0001 | A missing honesty line makes the docs gate fail | fast | gate/test_docs.py | test_missing_honesty_line_fails |
| T-DOCS-0002 | A fenced code block makes the docs gate fail | fast | gate/test_docs.py | test_code_block_fails |
| T-DOCS-0003 | A Build Progress row count mismatch makes the docs gate fail | fast | gate/test_docs.py | test_row_mismatch_fails |
| T-DOCS-0004 | A broken local link makes the docs gate fail | fast | gate/test_docs.py | test_broken_link_fails |
| T-DOCS-0005 | A hand-edited tick in Build Progress makes the docs gate fail | fast | gate/test_docs.py | test_hand_edited_tick_fails |
| T-DOCS-0006 | A forbidden pattern in the README makes the docs gate fail | fast | gate/test_docs.py | test_forbidden_pattern_fails |
| T-DOCS-LINKS | check_links skips http, https and anchor links | fast | gate/test_docs.py | test_check_links_skips_external_and_anchor |
| T-F01-0001 | F01-S01 golden scenario | fast | f01/test_consistency.py | test_T_F01_0001_golden_scenario |
| T-F01-0002 | F01-S02 golden scenario | fast | f01/test_consistency.py | test_T_F01_0002_golden_scenario |
| T-F01-0003 | F01-S03 golden scenario | fast | f01/test_consistency.py | test_T_F01_0003_golden_scenario |
| T-F01-0004 | F01-S04 golden scenario | fast | f01/test_consistency.py | test_T_F01_0004_golden_scenario |
| T-F01-0005 | F01-S05 golden scenario | fast | f01/test_consistency.py | test_T_F01_0005_golden_scenario |
| T-F01-0006 | F01-S06 golden scenario | fast | f01/test_consistency.py | test_T_F01_0006_golden_scenario |
| T-F01-0007 | F01-S07 golden scenario | fast | f01/test_consistency.py | test_T_F01_0007_golden_scenario |
| T-F01-0008 | F01-S08 golden scenario | fast | f01/test_consistency.py | test_T_F01_0008_golden_scenario |
| T-F01-0009 | F01-S09 golden scenario | fast | f01/test_consistency.py | test_T_F01_0009_golden_scenario |
| T-F01-0010 | F01-S10 golden scenario | fast | f01/test_consistency.py | test_T_F01_0010_golden_scenario |
| T-F01-0011 | F01-S11 golden scenario | fast | f01/test_consistency.py | test_T_F01_0011_golden_scenario |
| T-F01-0012 | F01-S12 golden scenario | fast | f01/test_consistency.py | test_T_F01_0012_golden_scenario |
| T-F01-0102 | Missing and proposed never publish | fast | f01/test_consistency.py | test_T_F01_0102_missing_and_proposed_never_publish |
| T-F01-0103 | Registry gates the container rule | fast | f01/test_consistency.py | test_T_F01_0103_registry_gates_the_container_rule |
| T-F01-0104 | Mismatch taxonomy | fast | f01/test_consistency.py | test_T_F01_0104_mismatch_taxonomy |
| T-F01-0113 | Arithmetic taxonomy | fast | f01/test_consistency.py | test_T_F01_0113_arithmetic_taxonomy |
| T-F01-0126 | Abstention and solver disagreement | fast | f01/test_consistency.py | test_T_F01_0126_abstention_and_solver_disagreement |
| T-F01-0201 | Common intersection | fast | f01/test_consistency.py | test_T_F01_0201_common_intersection |
| T-F01-0202 | Kilograms and grams preserve agreement | fast | f01/test_consistency.py | test_T_F01_0202_kilograms_and_grams_preserve_agreement |
| T-F01-0203 | Integer model matches interval sum | fast | f01/test_consistency.py | test_T_F01_0203_integer_model_matches_interval_sum |
| T-F01-0204 | Order independent consensus and conflict | fast | f01/test_consistency.py | test_T_F01_0204_order_independent_consensus_and_conflict |
| T-F01-0205 | Agreement comparators preserve precision and evidence boundaries | fast | f01/test_consistency.py | test_T_F01_0205_evidence_and_comparators |
| T-F01-0206 | Invalid arithmetic operands fail closed | fast | f01/test_consistency.py | test_T_F01_0206_invalid_and_valid_arithmetic_operands |
| T-F02-0001 | Classification scenarios | fast | f02/test_classification.py | test_classification_scenarios |
| T-F02-0003 | Shared headings escalate | fast | f02/test_classification.py | test_T_F02_0003_shared_headings_escalate |
| T-F02-0005 | Code valid through last instant | fast | f02/test_classification.py | test_T_F02_0005_code_valid_through_last_instant |
| T-F02-0008 | Secondary pack forces abstention | fast | f02/test_classification.py | test_T_F02_0008_secondary_pack_forces_abstention |
| T-F02-0009 | Older calibration is stale | fast | f02/test_classification.py | test_T_F02_0009_older_calibration_is_stale |
| T-F02-0010 | Claimed code in description is ignored | fast | f02/test_classification.py | test_T_F02_0010_claimed_code_in_description_is_ignored |
| T-F02-0011 | Statistical report carries the required label | fast | f02/test_classification.py | test_T_F02_0011_statistical_report_carries_the_required_label |
| T-F02-0012 | Shifted coverage is diagnostic | fast | f02/test_classification.py | test_T_F02_0012_shifted_coverage_is_diagnostic |
| T-F02-0101 | Closed outcome reasons | fast | f02/test_classification.py | test_closed_outcome_reasons |
| T-F02-0201 | Similarity matches reference | fast | f02/test_scoring.py | test_T_F02_0201_similarity_matches_reference |
| T-F02-0202 | Scorer optimized and differential | fast | f02/test_scoring.py | test_scorer_optimized_and_differential |
| T-F02-0212 | Smaller alpha never shrinks candidates | fast | f02/test_scoring.py | test_smaller_alpha_never_shrinks_candidates |
| T-F02-0215 | Quantile matches definition | fast | f02/test_scoring.py | test_T_F02_0215_quantile_matches_definition |
| T-F02-0216 | Seeded conformal coverage implementation correctness | slow | f02/test_scoring.py | test_T_F02_0216_seeded_conformal_coverage_implementation_correctness |
| T-F02-0217 | English only without glossary | fast | f02/test_scoring.py | test_T_F02_0217_english_only_without_glossary |
| T-F02-0218 | Glossary expansion is stable and recorded | fast | f02/test_scoring.py | test_T_F02_0218_glossary_expansion_is_stable_and_recorded |
| T-F02-0219 | Refuse a mismatched calibration language | fast | f02/test_scoring.py | test_T_F02_0219_refuse_a_mismatched_calibration_language |
| T-F02-0220 | Pack derived minimum | fast | f02/test_scoring.py | test_pack_derived_minimum |
| T-F02-0227 | Tariff filter requires verified applicability | fast | f02/test_scoring.py | test_tariff_filter_requires_verified_applicability |
| T-F02-0231 | Shift increases abstain or escalate by margin | fast | f02/test_classification.py | test_T_F02_0231_shift_increases_abstain_or_escalate_by_margin |
| T-F02-0232 | Shift cannot increase allow share | fast | f02/test_classification.py | test_T_F02_0232_shift_cannot_increase_allow_share |
| T-F02-0233 | Shift on old pack abstains | fast | f02/test_classification.py | test_T_F02_0233_shift_on_old_pack_abstains |
| T-F02-0234 | Statistical claim label is enforced | fast | f02/test_classification.py | test_T_F02_0234_statistical_claim_label_is_enforced |
| T-F02-0235 | Digit only tokens are removed before scoring | fast | f02/test_scoring.py | test_T_F02_0235_digit_only_tokens_are_removed_before_scoring |
| T-F02-0236 | Active calibration must support the published claim | fast | f02/test_classification.py | test_T_F02_0236_active_calibration_must_support_the_published_claim |
| T-F02-0301 | Adversarial description never creates allow | fast | f02/test_classification.py | test_adversarial_description_never_creates_allow |
| T-F02-0317 | Copied headings and embedded codes are scorer inputs only | fast | f02/test_classification.py | test_copied_headings_and_embedded_codes_are_scorer_inputs_only |
| T-F02-0321 | Repeated single keyword cannot pass with the active pack | fast | f02/test_classification.py | test_T_F02_0321_repeated_single_keyword_cannot_pass_with_the_active_pack |
| T-F02-0401 | Replay commits to same output | fast | f02/test_classification.py | test_T_F02_0401_replay_commits_to_same_output |
| T-F02-0402 | Changed description changes commitments | fast | f02/test_classification.py | test_T_F02_0402_changed_description_changes_commitments |
| T-F02-0403 | Line order does not affect case outcome | fast | f02/test_classification.py | test_T_F02_0403_line_order_does_not_affect_case_outcome |
| T-F02-0404 | Report keeps each line decision | fast | f02/test_classification.py | test_T_F02_0404_report_keeps_each_line_decision |
| T-F02-0405 | Deep code reports the comparison level | fast | f02/test_classification.py | test_T_F02_0405_deep_code_reports_the_comparison_level |
| T-F02-0406 | Exclusions are recorded on verified facts | fast | f02/test_classification.py | test_T_F02_0406_exclusions_are_recorded_on_verified_facts |
| T-F02-0407 | Unverified attribute cannot exclude | fast | f02/test_classification.py | test_unverified_attribute_cannot_exclude |
| T-F02-0501 | Http invocation returns decision | fast | f02/test_classification.py | test_T_F02_0501_http_invocation_returns_decision |
| T-F02-0502 | Case result has verbatim banner | fast | f02/test_classification.py | test_T_F02_0502_case_result_has_verbatim_banner |
| T-F02-0503 | Other tenant cannot invoke | fast | f02/test_classification.py | test_T_F02_0503_other_tenant_cannot_invoke |
| T-F02-0504 | Unknown evaluation is not found | fast | f02/test_classification.py | test_T_F02_0504_unknown_evaluation_is_not_found |
| T-F02-0505 | View anchor is stable | fast | f02/test_classification.py | test_T_F02_0505_view_anchor_is_stable |
| T-F02-0506 | Coverage claim and language are recorded | fast | f02/test_classification.py | test_T_F02_0506_coverage_claim_and_language_are_recorded |
| T-F02-0507 | No duty or rewording advice | fast | f02/test_classification.py | test_no_duty_or_rewording_advice |
| T-F02-0511 | Calibration hash appears in evidence | fast | f02/test_classification.py | test_T_F02_0511_calibration_hash_appears_in_evidence |
| T-F02-0512 | Case reports supported languages | fast | f02/test_classification.py | test_T_F02_0512_case_reports_supported_languages |
| T-F03-0001 | Scenario 01 | fast | f03/test_outcomes.py | test_T_F03_0001_scenario_01 |
| T-F03-0002 | Scenario 02 | fast | f03/test_outcomes.py | test_T_F03_0002_scenario_02 |
| T-F03-0003 | Scenario 03 | fast | f03/test_outcomes.py | test_T_F03_0003_scenario_03 |
| T-F03-0004 | Scenario 04 | fast | f03/test_outcomes.py | test_T_F03_0004_scenario_04 |
| T-F03-0005 | Scenario 05 | fast | f03/test_outcomes.py | test_T_F03_0005_scenario_05 |
| T-F03-0006 | Scenario 06 | fast | f03/test_outcomes.py | test_T_F03_0006_scenario_06 |
| T-F03-0007 | Scenario 07 | fast | f03/test_outcomes.py | test_T_F03_0007_scenario_07 |
| T-F03-0008 | Scenario 08 | fast | f03/test_outcomes.py | test_T_F03_0008_scenario_08 |
| T-F03-0009 | Scenario 09 | fast | f03/test_outcomes.py | test_T_F03_0009_scenario_09 |
| T-F03-0010 | Scenario 10 | fast | f03/test_outcomes.py | test_T_F03_0010_scenario_10 |
| T-F03-0011 | Scenario 11 | fast | f03/test_outcomes.py | test_T_F03_0011_scenario_11 |
| T-F03-0012 | Scenario 12 | fast | f03/test_outcomes.py | test_T_F03_0012_scenario_12 |
| T-F03-0101 | Within free | fast | f03/test_outcomes.py | test_T_F03_0101_within_free |
| T-F03-0102 | Stopped | fast | f03/test_outcomes.py | test_T_F03_0102_stopped |
| T-F03-0103 | Ending | fast | f03/test_outcomes.py | test_T_F03_0103_ending |
| T-F03-0104 | Accruing | fast | f03/test_outcomes.py | test_T_F03_0104_accruing |
| T-F03-0105 | Order invalid | fast | f03/test_outcomes.py | test_T_F03_0105_order_invalid |
| T-F03-0106 | Missing event | fast | f03/test_outcomes.py | test_T_F03_0106_missing_event |
| T-F03-0107 | Missing tariff | fast | f03/test_outcomes.py | test_T_F03_0107_missing_tariff |
| T-F03-0108 | Unspecified day rule | fast | f03/test_outcomes.py | test_T_F03_0108_unspecified_day_rule |
| T-F03-0109 | Missing calendar | fast | f03/test_outcomes.py | test_T_F03_0109_missing_calendar |
| T-F03-0110 | Unmatched container | fast | f03/test_outcomes.py | test_T_F03_0110_unmatched_container |
| T-F03-0111 | Insufficient label | fast | f03/test_outcomes.py | test_T_F03_0111_insufficient_label |
| T-F03-0201 | Optimized clock matches day simulation | fast | f03/test_clock.py | test_T_F03_0201_optimized_matches_day_simulation |
| T-F03-0202 | Later clock end is monotonic | fast | f03/test_clock.py | test_T_F03_0202_later_end_is_monotonic |
| T-F03-0203 | A verified suspension cannot increase charge | fast | f03/test_clock.py | test_T_F03_0203_verified_suspension_is_monotonic |
| T-F03-0204 | Adjacent periods preserve the accrued amount | fast | f03/test_clock.py | test_T_F03_0204_period_partition_is_additive |
| T-F03-0205 | Zero before expiry | fast | f03/test_clock.py | test_T_F03_0205_zero_before_expiry |
| T-F03-0206 | Zero at expiry | fast | f03/test_clock.py | test_T_F03_0206_zero_at_expiry |
| T-F03-0207 | First tier amount | fast | f03/test_clock.py | test_T_F03_0207_first_tier_amount |
| T-F03-0208 | Tier edge amount | fast | f03/test_clock.py | test_T_F03_0208_tier_edge_amount |
| T-F03-0209 | Second tier amount | fast | f03/test_clock.py | test_T_F03_0209_second_tier_amount |
| T-F03-0210 | Last tier amount | fast | f03/test_clock.py | test_T_F03_0210_last_tier_amount |
| T-F03-0211 | Leap day | fast | f03/test_clock.py | test_T_F03_0211_leap_day |
| T-F03-0212 | Working holiday | fast | f03/test_clock.py | test_T_F03_0212_working_holiday |
| T-F03-0213 | Working weekend | fast | f03/test_clock.py | test_T_F03_0213_working_weekend |
| T-F03-0214 | Working restart | fast | f03/test_clock.py | test_T_F03_0214_working_restart |
| T-F03-0215 | Exclude first day | fast | f03/test_clock.py | test_T_F03_0215_exclude_first_day |
| T-F03-0216 | Cutoff boundary | fast | f03/test_clock.py | test_T_F03_0216_cutoff_boundary |
| T-F03-0217 | Complete partial | fast | f03/test_clock.py | test_T_F03_0217_complete_partial |
| T-F03-0218 | Prorated partial | fast | f03/test_clock.py | test_T_F03_0218_prorated_partial |
| T-F03-0219 | Spring forward | fast | f03/test_clock.py | test_T_F03_0219_spring_forward |
| T-F03-0220 | Fall back | fast | f03/test_clock.py | test_T_F03_0220_fall_back |
| T-F03-0221 | Exact boundary | fast | f03/test_clock.py | test_T_F03_0221_exact_boundary |
| T-F03-0222 | Before boundary | fast | f03/test_clock.py | test_T_F03_0222_before_boundary |
| T-F03-0223 | Zero free days | fast | f03/test_clock.py | test_T_F03_0223_zero_free_days |
| T-F03-0224 | Unverified window | fast | f03/test_clock.py | test_T_F03_0224_unverified_window |
| T-F03-0225 | Overlapping windows | fast | f03/test_clock.py | test_T_F03_0225_overlapping_windows |
| T-F03-0226 | After free window | fast | f03/test_clock.py | test_T_F03_0226_after_free_window |
| T-F03-0227 | Full free suspension | fast | f03/test_clock.py | test_T_F03_0227_full_free_suspension |
| T-F03-0228 | Fixed offset shift | fast | f03/test_clock.py | test_T_F03_0228_fixed_offset_shift |
| T-F03-0229 | Validity start | fast | f03/test_clock.py | test_T_F03_0229_validity_start |
| T-F03-0230 | Validity end | fast | f03/test_clock.py | test_T_F03_0230_validity_end |
| T-F03-0231 | Early stop | fast | f03/test_clock.py | test_T_F03_0231_early_stop |
| T-F03-0232 | Period before expiry | fast | f03/test_clock.py | test_T_F03_0232_period_before_expiry |
| T-F03-0233 | Period after end | fast | f03/test_clock.py | test_T_F03_0233_period_after_end |
| T-F03-0234 | Apportioned tiers | fast | f03/test_clock.py | test_T_F03_0234_apportioned_tiers |
| T-F03-0235 | Tariff day continuity | fast | f03/test_clock.py | test_T_F03_0235_tariff_day_continuity |
| T-F03-0301 | Ignore extension claim | fast | f03/test_outcomes.py | test_T_F03_0301_ignore_extension_claim |
| T-F03-0302 | Ignore instruction in note | fast | f03/test_outcomes.py | test_T_F03_0302_ignore_instruction_in_note |
| T-F03-0303 | Impossible leap day | fast | f03/test_outcomes.py | test_T_F03_0303_impossible_leap_day |
| T-F03-0304 | Impossible day | fast | f03/test_outcomes.py | test_T_F03_0304_impossible_day |
| T-F03-0305 | Impossible month | fast | f03/test_outcomes.py | test_T_F03_0305_impossible_month |
| T-F03-0306 | Impossible time | fast | f03/test_outcomes.py | test_T_F03_0306_impossible_time |
| T-F03-0307 | Time without zone | fast | f03/test_outcomes.py | test_T_F03_0307_time_without_zone |
| T-F03-0308 | Wrong year syntax | fast | f03/test_outcomes.py | test_T_F03_0308_wrong_year_syntax |
| T-F03-0309 | Empty time | fast | f03/test_outcomes.py | test_T_F03_0309_empty_time |
| T-F03-0310 | Text as timestamp | fast | f03/test_outcomes.py | test_T_F03_0310_text_as_timestamp |
| T-F03-0311 | Reversed movements | fast | f03/test_outcomes.py | test_T_F03_0311_reversed_movements |
| T-F03-0312 | Duplicate movements | fast | f03/test_outcomes.py | test_T_F03_0312_duplicate_movements |
| T-F03-0313 | Unverified tariff | fast | f03/test_outcomes.py | test_T_F03_0313_unverified_tariff |
| T-F03-0314 | Expired tariff | fast | f03/test_outcomes.py | test_T_F03_0314_expired_tariff |
| T-F03-0315 | Wrong currency | fast | f03/test_outcomes.py | test_T_F03_0315_wrong_currency |
| T-F03-0316 | Required cutoff | fast | f03/test_outcomes.py | test_T_F03_0316_required_cutoff |
| T-F03-0317 | Required day one | fast | f03/test_outcomes.py | test_T_F03_0317_required_day_one |
| T-F03-0318 | Confusable container | fast | f03/test_outcomes.py | test_T_F03_0318_confusable_container |
| T-F03-0319 | Overlapping suspensions | fast | f03/test_outcomes.py | test_T_F03_0319_overlapping_suspensions |
| T-F03-0320 | Huge period fails closed | fast | f03/test_outcomes.py | test_T_F03_0320_huge_period_fails_closed |
| T-F03-0401 | Replay scenario 01 | fast | f03/test_outcomes.py | test_T_F03_0401_replay_scenario_01 |
| T-F03-0402 | Replay scenario 02 | fast | f03/test_outcomes.py | test_T_F03_0402_replay_scenario_02 |
| T-F03-0403 | Replay scenario 03 | fast | f03/test_outcomes.py | test_T_F03_0403_replay_scenario_03 |
| T-F03-0404 | Replay scenario 04 | fast | f03/test_outcomes.py | test_T_F03_0404_replay_scenario_04 |
| T-F03-0405 | Replay scenario 05 | fast | f03/test_outcomes.py | test_T_F03_0405_replay_scenario_05 |
| T-F03-0406 | Replay scenario 06 | fast | f03/test_outcomes.py | test_T_F03_0406_replay_scenario_06 |
| T-F03-0407 | Replay scenario 07 | fast | f03/test_outcomes.py | test_T_F03_0407_replay_scenario_07 |
| T-F03-0408 | Replay scenario 08 | fast | f03/test_outcomes.py | test_T_F03_0408_replay_scenario_08 |
| T-F03-0409 | Replay scenario 09 | fast | f03/test_outcomes.py | test_T_F03_0409_replay_scenario_09 |
| T-F03-0410 | Replay scenario 10 | fast | f03/test_outcomes.py | test_T_F03_0410_replay_scenario_10 |
| T-F03-0501 | Stable anchor | fast | f03/test_outcomes.py | test_T_F03_0501_stable_anchor |
| T-F03-0502 | Event citations | fast | f03/test_outcomes.py | test_T_F03_0502_event_citations |
| T-F03-0503 | Free expiry text | fast | f03/test_outcomes.py | test_T_F03_0503_free_expiry_text |
| T-F03-0504 | Free bar has text | fast | f03/test_outcomes.py | test_T_F03_0504_free_bar_has_text |
| T-F03-0505 | Accrual bar has text | fast | f03/test_outcomes.py | test_T_F03_0505_accrual_bar_has_text |
| T-F03-0506 | Suspension text | fast | f03/test_outcomes.py | test_T_F03_0506_suspension_text |
| T-F03-0507 | Projection horizons | fast | f03/test_outcomes.py | test_T_F03_0507_projection_horizons |
| T-F03-0508 | Operational action text | fast | f03/test_outcomes.py | test_T_F03_0508_operational_action_text |
| T-F03-0509 | Unknown without charge | fast | f03/test_outcomes.py | test_T_F03_0509_unknown_without_charge |
| T-F03-0510 | Contradiction requests review | fast | f03/test_outcomes.py | test_T_F03_0510_contradiction_requests_review |
| T-F03-0511 | Extensions absent from view | fast | f03/test_outcomes.py | test_T_F03_0511_extensions_absent_from_view |
| T-F03-0512 | No suggested record edits | fast | f03/test_outcomes.py | test_T_F03_0512_no_suggested_record_edits |
| T-F07-0001 | Scenario 01 | fast | f07/test_reports.py | test_T_F07_0001_scenario_01 |
| T-F07-0002 | Scenario 02 | fast | f07/test_reports.py | test_T_F07_0002_scenario_02 |
| T-F07-0003 | Scenario 03 | fast | f07/test_reports.py | test_T_F07_0003_scenario_03 |
| T-F07-0004 | Scenario 04 | fast | f07/test_reports.py | test_T_F07_0004_scenario_04 |
| T-F07-0005 | Scenario 05 | fast | f07/test_reports.py | test_T_F07_0005_scenario_05 |
| T-F07-0006 | Scenario 06 | fast | f07/test_reports.py | test_T_F07_0006_scenario_06 |
| T-F07-0007 | Scenario 07 | fast | f07/test_reports.py | test_T_F07_0007_scenario_07 |
| T-F07-0008 | Scenario 08 | fast | f07/test_reports.py | test_T_F07_0008_scenario_08 |
| T-F07-0009 | Scenario 09 | fast | f07/test_reports.py | test_T_F07_0009_scenario_09 |
| T-F07-0010 | Scenario 10 | fast | f07/test_reports.py | test_T_F07_0010_scenario_10 |
| T-F07-0011 | Scenario 11 | fast | f07/test_reports.py | test_T_F07_0011_scenario_11 |
| T-F07-0101 | Matched | fast | f07/test_reports.py | test_T_F07_0101_matched |
| T-F07-0102 | Undercharge | fast | f07/test_reports.py | test_T_F07_0102_undercharge |
| T-F07-0103 | Flat charge | fast | f07/test_reports.py | test_T_F07_0103_flat_charge |
| T-F07-0104 | Duplicate | fast | f07/test_reports.py | test_T_F07_0104_duplicate |
| T-F07-0105 | Not billable | fast | f07/test_reports.py | test_T_F07_0105_not_billable |
| T-F07-0106 | Different effective rate | fast | f07/test_reports.py | test_T_F07_0106_different_effective_rate |
| T-F07-0107 | Day count | fast | f07/test_reports.py | test_T_F07_0107_day_count |
| T-F07-0108 | Arithmetic | fast | f07/test_reports.py | test_T_F07_0108_arithmetic |
| T-F07-0109 | Unsupported tariff | fast | f07/test_reports.py | test_T_F07_0109_unsupported_tariff |
| T-F07-0110 | Ambiguous tariff | fast | f07/test_reports.py | test_T_F07_0110_ambiguous_tariff |
| T-F07-0111 | Clock missing | fast | f07/test_reports.py | test_T_F07_0111_clock_missing |
| T-F07-0112 | Matching missing | fast | f07/test_reports.py | test_T_F07_0112_matching_missing |
| T-F07-0113 | Label insufficient | fast | f07/test_reports.py | test_T_F07_0113_label_insufficient |
| T-F07-0201 | Recomputed amounts match F03 | fast | f07/test_audit.py | test_T_F07_0201_exact_clock_equivalence |
| T-F07-0202 | A corrected supported invoice allows | fast | f07/test_audit.py | test_T_F07_0202_corrected_invoice_allows |
| T-F07-0203 | More verified free time lowers expected charge | fast | f07/test_audit.py | test_T_F07_0203_verified_extension_changes_difference |
| T-F07-0204 | Line order independent | fast | f07/test_audit.py | test_T_F07_0204_line_order_independent |
| T-F07-0205 | Dossier hash deterministic | fast | f07/test_audit.py | test_T_F07_0205_dossier_hash_deterministic |
| T-F07-0206 | Dossier hash covers artifacts | fast | f07/test_audit.py | test_T_F07_0206_dossier_hash_covers_artifacts |
| T-F07-0207 | Duplicate precedes period | fast | f07/test_audit.py | test_T_F07_0207_duplicate_precedes_period |
| T-F07-0208 | Period precedes rate | fast | f07/test_audit.py | test_T_F07_0208_period_precedes_rate |
| T-F07-0209 | Rate precedes days | fast | f07/test_audit.py | test_T_F07_0209_rate_precedes_days |
| T-F07-0210 | Days precede arithmetic | fast | f07/test_audit.py | test_T_F07_0210_days_precede_arithmetic |
| T-F07-0211 | Arithmetic precedes outcome | fast | f07/test_audit.py | test_T_F07_0211_arithmetic_precedes_outcome |
| T-F07-0212 | Unsupported basis | fast | f07/test_audit.py | test_T_F07_0212_unsupported_basis |
| T-F07-0213 | Ambiguous basis | fast | f07/test_audit.py | test_T_F07_0213_ambiguous_basis |
| T-F07-0214 | Missing clock | fast | f07/test_audit.py | test_T_F07_0214_missing_clock |
| T-F07-0215 | Missing match | fast | f07/test_audit.py | test_T_F07_0215_missing_match |
| T-F07-0216 | Undercharge observed | fast | f07/test_audit.py | test_T_F07_0216_undercharge_observed |
| T-F07-0217 | Below minor unit matches | fast | f07/test_audit.py | test_T_F07_0217_below_minor_unit_matches |
| T-F07-0218 | Tax not evaluated | fast | f07/test_audit.py | test_T_F07_0218_tax_not_evaluated |
| T-F07-0219 | Flat charge passes to l01 | fast | f07/test_audit.py | test_T_F07_0219_flat_charge_passes_to_l01 |
| T-F07-0220 | Currency mismatch | fast | f07/test_audit.py | test_T_F07_0220_currency_mismatch |
| T-F07-0221 | Missing period | fast | f07/test_audit.py | test_T_F07_0221_missing_period |
| T-F07-0222 | Step carries exact days | fast | f07/test_audit.py | test_T_F07_0222_step_carries_exact_days |
| T-F07-0223 | Weak label indicative | fast | f07/test_audit.py | test_T_F07_0223_weak_label_indicative |
| T-F07-0224 | After stop not billable | fast | f07/test_audit.py | test_T_F07_0224_after_stop_not_billable |
| T-F07-0225 | Adjacent periods are distinct | fast | f07/test_audit.py | test_T_F07_0225_adjacent_periods_are_distinct |
| T-F07-0301 | Overlapping periods | fast | f07/test_reports.py | test_T_F07_0301_overlapping_periods |
| T-F07-0302 | Negative amount | fast | f07/test_reports.py | test_T_F07_0302_negative_amount |
| T-F07-0303 | Negative rate | fast | f07/test_reports.py | test_T_F07_0303_negative_rate |
| T-F07-0304 | Negative days | fast | f07/test_reports.py | test_T_F07_0304_negative_days |
| T-F07-0305 | Tiny duplicate difference | fast | f07/test_reports.py | test_T_F07_0305_tiny_duplicate_difference |
| T-F07-0306 | Currency mismatch | fast | f07/test_reports.py | test_T_F07_0306_currency_mismatch |
| T-F07-0307 | Unknown currency | fast | f07/test_reports.py | test_T_F07_0307_unknown_currency |
| T-F07-0308 | Invalid amount | fast | f07/test_reports.py | test_T_F07_0308_invalid_amount |
| T-F07-0309 | Invalid period start | fast | f07/test_reports.py | test_T_F07_0309_invalid_period_start |
| T-F07-0310 | Invalid period end | fast | f07/test_reports.py | test_T_F07_0310_invalid_period_end |
| T-F07-0311 | Period without zone | fast | f07/test_reports.py | test_T_F07_0311_period_without_zone |
| T-F07-0312 | Period reversed | fast | f07/test_reports.py | test_T_F07_0312_period_reversed |
| T-F07-0313 | Missing start | fast | f07/test_reports.py | test_T_F07_0313_missing_start |
| T-F07-0314 | Missing end | fast | f07/test_reports.py | test_T_F07_0314_missing_end |
| T-F07-0315 | Unmatched container | fast | f07/test_reports.py | test_T_F07_0315_unmatched_container |
| T-F07-0316 | Future period | fast | f07/test_reports.py | test_T_F07_0316_future_period |
| T-F07-0317 | Confusable container | fast | f07/test_reports.py | test_T_F07_0317_confusable_container |
| T-F07-0318 | Recorded scope empty | fast | f07/test_reports.py | test_T_F07_0318_recorded_scope_empty |
| T-F07-0319 | Text cannot direct outcome | fast | f07/test_reports.py | test_T_F07_0319_text_cannot_direct_outcome |
| T-F07-0320 | Nonfinite amount | fast | f07/test_reports.py | test_T_F07_0320_nonfinite_amount |
| T-F07-0401 | Replay scenario 01 | fast | f07/test_reports.py | test_T_F07_0401_replay_scenario_01 |
| T-F07-0402 | Replay scenario 02 | fast | f07/test_reports.py | test_T_F07_0402_replay_scenario_02 |
| T-F07-0403 | Replay scenario 03 | fast | f07/test_reports.py | test_T_F07_0403_replay_scenario_03 |
| T-F07-0404 | Replay scenario 04 | fast | f07/test_reports.py | test_T_F07_0404_replay_scenario_04 |
| T-F07-0405 | Replay scenario 05 | fast | f07/test_reports.py | test_T_F07_0405_replay_scenario_05 |
| T-F07-0406 | Replay scenario 06 | fast | f07/test_reports.py | test_T_F07_0406_replay_scenario_06 |
| T-F07-0407 | Replay scenario 07 | fast | f07/test_reports.py | test_T_F07_0407_replay_scenario_07 |
| T-F07-0408 | Replay scenario 08 | fast | f07/test_reports.py | test_T_F07_0408_replay_scenario_08 |
| T-F07-0409 | Replay scenario 09 | fast | f07/test_reports.py | test_T_F07_0409_replay_scenario_09 |
| T-F07-0410 | Replay scenario 10 | fast | f07/test_reports.py | test_T_F07_0410_replay_scenario_10 |
| T-F07-0501 | Anchor | fast | f07/test_reports.py | test_T_F07_0501_anchor |
| T-F07-0502 | Root cause column | fast | f07/test_reports.py | test_T_F07_0502_root_cause_column |
| T-F07-0503 | Proportional difference | fast | f07/test_reports.py | test_T_F07_0503_proportional_difference |
| T-F07-0504 | Changed rate two steps | fast | f07/test_reports.py | test_T_F07_0504_changed_rate_two_steps |
| T-F07-0505 | Dossier preview | fast | f07/test_reports.py | test_T_F07_0505_dossier_preview |
| T-F07-0506 | Json export | fast | f07/test_reports.py | test_T_F07_0506_json_export |
| T-F07-0507 | Html export | fast | f07/test_reports.py | test_T_F07_0507_html_export |
| T-F07-0508 | Indicative export | fast | f07/test_reports.py | test_T_F07_0508_indicative_export |
| T-F07-0509 | Unsupported export citation | fast | f07/test_reports.py | test_T_F07_0509_unsupported_export_citation |
| T-F07-0510 | Tax exclusion | fast | f07/test_reports.py | test_T_F07_0510_tax_exclusion |
| T-F07-0511 | No payment instructions | fast | f07/test_reports.py | test_T_F07_0511_no_payment_instructions |
| T-F07-0512 | No owed statement | fast | f07/test_reports.py | test_T_F07_0512_no_owed_statement |
| T-GATE-0001 | Exit-code semantics (pass / fail / misconfiguration) | fast | gate/test_runner.py | test_exit_code_pass |
| T-GATE-0002 | Gate timeout records reason TIMEOUT | slow | gate/test_runner.py | test_timeout_reason |
| T-GATE-0003 | JSON result has the required schema | fast | gate/test_runner.py | test_json_result_schema |
| T-GATE-0004 | NOT_ACTIVE gates are listed but never counted as passed | fast | gate/test_runner.py | test_not_active_never_counted |
| T-GATE-0005 | A required gate missing from the catalogue returns exit 2 | fast | gate/test_runner.py | test_overdue_activation_returns_2 |
| T-GATE-0006 | Generated gate table matches persisted JSON results | fast | gate/test_runner.py | test_report_matches_json |
| T-GATE-0007 | gate affected returns the complete slow set without a coverage map | fast | gate/test_runner.py | test_affected_fallback |
| T-GATE-0008 | Running an unknown gate name returns exit 2 | fast | gate/test_runner.py | test_unknown_gate_returns_2 |
| T-GATE-0009 | Missing header field fails | fast | gate/test_index.py | test_missing_header_field |
| T-GATE-0010 | Duplicate id fails | fast | gate/test_index.py | test_duplicate_id |
| T-GATE-0011 | Stale index fails | fast | gate/test_index.py | test_stale_index |
| T-GATE-0012 | Unmarked test fails | fast | gate/test_index.py | test_unmarked_test |
| T-GATE-0013 | Order-dependent fixture detected by repeat check | fast | gate/test_index.py | test_order_dependent_detected |
| T-GATE-0014 | Index is byte-identical on regeneration | fast | gate/test_index.py | test_index_byte_identical |
| T-GATE-0015 | hygiene gate fails on a file with a forbidden pattern | fast | gate/test_gates.py | test_hygiene_violation |
| T-GATE-0016 | hygiene gate passes on a clean file | fast | gate/test_gates.py | test_hygiene_clean |
| T-GATE-0017 | secrets gate fails on a pre-computed result with findings | fast | gate/test_gates.py | test_secrets_violation |
| T-GATE-0018 | secrets gate passes on a clean result | fast | gate/test_gates.py | test_secrets_clean |
| T-GATE-0019 | security gate fails on yaml.unsafe_load | slow | gate/test_gates.py | test_security_violation |
| T-GATE-0020 | security gate passes on a clean file | slow | gate/test_gates.py | test_security_clean |
| T-GATE-0021 | deps gate fails on a vulnerable package | fast | gate/test_gates.py | test_deps_violation |
| T-GATE-0022 | deps gate passes on a clean audit | fast | gate/test_gates.py | test_deps_clean |
| T-GATE-0023 | license gate fails on a GPL-family licence | fast | gate/test_gates.py | test_license_violation_gpl |
| T-GATE-0024 | license gate passes on allowlisted licences | fast | gate/test_gates.py | test_license_clean |
| T-GATE-0025 | a modified protected file fails the protect gate | fast | gate/test_protect.py | test_modified_protected_file_fails |
| T-GATE-0026 | a modified hashes file (wrong hash) fails the protect gate | fast | gate/test_protect.py | test_modified_hashes_file_fails |
| T-GATE-0027 | --update without a task that changes a protected path fails | fast | gate/test_protect.py | test_update_without_task_fails |
| T-GATE-0028 | a clean tree with matching hashes passes the protect gate | fast | gate/test_protect.py | test_clean_tree_passes |
| T-GATE-0029 | a new protected file not in the hashes file fails the protect gate | fast | gate/test_protect.py | test_new_protected_file_missing_from_hashes_fails |
| T-GATE-0030 | vendor pattern passes in a declared adapter path and fails elsewhere | fast | gate/test_gates.py | test_vendor_pattern_scope |
| T-GATE-0031 | always-forbidden pattern fails everywhere including a declared path | fast | gate/test_gates.py | test_always_forbidden_in_scope |
| T-GATE-0032 | scope entry outside the permitted path families fails | fast | gate/test_gates.py | test_scope_outside_permitted_families |
| T-GATE-0033 | a present but empty list fails the hygiene gate | fast | gate/test_gates.py | test_empty_list_fails |
| T-GATE-0034 | an expired exception fails the deps gate | fast | gate/test_gates.py | test_expired_exception_fails |
| T-GATE-0035 | Order-dependent test caught under at least one pinned seed | fast | gate/test_seeds.py | test_order_dependent_pinned |
| T-GATE-0036 | Same seed, worker count and selection reproduce same result | fast | gate/test_seeds.py | test_same_seed_reproducible |
| T-GATE-0037 | gate seeds add appends a failing seed with its test id and refuses a hand edit | fast | gate/test_seeds.py | test_seeds_add_appends_and_refuses_hand_edit |
| T-GATE-0038 | Regression seeds run in every later gate run; fresh seed printed; hand edit fails | fast | gate/test_seeds.py | test_regression_and_fresh_seed |
| T-GATE-0039 | without lists a local run reports NOT_RUN_LOCAL | fast | gate/test_gates.py | test_not_run_local |
| T-GATE-0040 | in CI a missing list fails closed | fast | gate/test_gates.py | test_ci_missing_list_fails |
| T-GATE-0041 | commit-check rejects violations and accepts a clean message | fast | gate/test_gates.py | test_commit_check_bad_format |
| T-GATE-0042 | hygiene gate runs in CI (not NOT_RUN_LOCAL) when lists are present | fast | gate/test_gates.py | test_hygiene_pending_in_ci |
| T-GATE-0043 | a transitive package with a licence outside the allowlist fails | fast | gate/test_gates.py | test_license_transitive_bad_license |
| T-GATE-0044 | a stale THIRD_PARTY_NOTICES.txt fails the license gate | fast | gate/test_gates.py | test_license_stale_notices |
| T-GATE-0045 | merge commit messages are dropped before the commit checks | fast | gate/test_gates.py | test_drop_merge_messages |
| T-GATE-0046 | the installer accepts only data with the pinned SHA-256 | fast | gate/test_install_gitleaks.py | test_verify_digest |
| T-GATE-0047 | the installer writes the gitleaks member as an executable file | fast | gate/test_install_gitleaks.py | test_extract_binary |
| T-GATE-0048 | the installer fails when the archive has no gitleaks member | fast | gate/test_install_gitleaks.py | test_extract_binary_missing_member |
| T-GATE-0049 | the secrets gate reads findings from the report file | fast | gate/test_secrets_report.py | test_report_file_with_finding |
| T-GATE-0050 | the secrets gate fails closed when the scanner leaves no report | fast | gate/test_secrets_report.py | test_no_report_is_an_error |
| T-GATE-0051 | the secrets gate passes a run the scanner reports as clean | fast | gate/test_secrets_report.py | test_clean_run_without_report |
| T-GATE-0052 | merge commits and consistent state updates pass the structural checks | fast | gate/test_gates.py | test_structural_checks_accept_merge_commits |
| T-GATE-GOLDEN-001 | Golden regenerate refuses a path outside the golden list | fast | gate/test_index.py | test_golden_refuses_outside |
| T-GATE-GOLDEN-002 | Golden regenerate refuses a dirty tree | fast | gate/test_index.py | test_golden_refuses_dirty |
| T-GATE-GOLDEN-003 | Golden regenerate commits golden files alone | fast | gate/test_index.py | test_golden_commits_alone |
| T-GATE-HASH | gate hash matches the system sha256 on fixture and empty files | fast | gate/test_runner.py | test_hash_matches_shasum |
| T-GATE-KILL | Timeout kill leaves no process from the group alive | slow | gate/test_runner.py | test_kill_process_group_leaves_no_child |
| T-GATE-PHASE | Phase parsing and default current phase | fast | gate/test_runner.py | test_parse_phase_number |
| T-GATE-SELFTEST | selftest fails on bad fixtures and passes on good ones | slow | gate/test_runner.py | test_selftest_passes_violation_returns_1 |
| T-GATE-SELFTEST-REAL | selftest passes against the real P00 fixtures with real tools | slow | gate/test_runner.py | test_selftest_real_round_trip |
| T-GATE-SELFTEST-T06 | selftest passes against the hygiene, secrets, security, deps, license | slow | gate/test_gates.py | test_selftest_t06_gates |
| T-GATE-SETS | Set selection resolves quick / phase / nightly correctly | fast | gate/test_runner.py | test_select_sets |
| T-GATE-STUB | stub.txt equals the two lines of <<<P7-STUB>>> and is protected | fast | gate/test_protect.py | test_stub_txt_matches_directive_bytes |
| T-GWY-0001 | A recorded call replays identically | fast | gateway/test_T_GWY_0001_to_0012.py | test_T_GWY_0001_recorded_call_replays_identically |
| T-GWY-0002 | An unknown prompt in recorded mode fails closed | fast | gateway/test_T_GWY_0001_to_0012.py | test_T_GWY_0002_unknown_prompt_fails_closed |
| T-GWY-0003 | Every call writes a record | fast | gateway/test_T_GWY_0001_to_0012.py | test_T_GWY_0003_every_call_writes_record |
| T-GWY-0004 | No module outside adapters/model/ imports a provider client | fast | gateway/test_T_GWY_0001_to_0012.py | test_T_GWY_0004_no_provider_import_outside_adapters |
| T-GWY-0005 | compute_prompt_hash is deterministic | fast | gateway/test_T_GWY_0001_to_0012.py | test_T_GWY_0005_prompt_hash_deterministic |
| T-GWY-0006 | compute_prompt_hash differs for different prompts | fast | gateway/test_T_GWY_0001_to_0012.py | test_T_GWY_0006_prompt_hash_differs |
| T-GWY-0007 | ModelCallRequest is frozen | fast | gateway/test_T_GWY_0001_to_0012.py | test_T_GWY_0007_request_is_frozen |
| T-GWY-0008 | ModelCallResponse is frozen | fast | gateway/test_T_GWY_0001_to_0012.py | test_T_GWY_0008_response_is_frozen |
| T-GWY-0009 | Schema validation passes for valid output | fast | gateway/test_T_GWY_0001_to_0012.py | test_T_GWY_0009_schema_validation_passes |
| T-GWY-0010 | Schema validation fails for invalid output | fast | gateway/test_T_GWY_0001_to_0012.py | test_T_GWY_0010_schema_validation_fails |
| T-GWY-0011 | Gateway validates output and raises SchemaValidationError on invalid | fast | gateway/test_T_GWY_0001_to_0012.py | test_T_GWY_0011_gateway_validates_output |
| T-GWY-0012 | to_record produces a ModelCallRecord with all fields | fast | gateway/test_T_GWY_0001_to_0012.py | test_T_GWY_0012_to_record_all_fields |
| T-GWY-0013 | PrimaryAdapter call returns a ModelCallResponse | fast | gateway/test_T_GWY_0013_to_0024.py | test_T_GWY_0013_primary_adapter_call |
| T-GWY-0014 | SecondaryAdapter call returns a ModelCallResponse | fast | gateway/test_T_GWY_0013_to_0024.py | test_T_GWY_0014_secondary_adapter_call |
| T-GWY-0015 | LocalAdapter call returns a ModelCallResponse | fast | gateway/test_T_GWY_0013_to_0024.py | test_T_GWY_0015_local_adapter_call |
| T-GWY-0016 | All three adapters share the same contract (GatewayPort) | fast | gateway/test_T_GWY_0013_to_0024.py | test_T_GWY_0016_all_adapters_share_contract |
| T-GWY-0017 | Switching provider is configuration only | fast | gateway/test_T_GWY_0013_to_0024.py | test_T_GWY_0017_switching_provider_config_only |
| T-GWY-0018 | PrimaryAdapter has pinned model_id | fast | gateway/test_T_GWY_0013_to_0024.py | test_T_GWY_0018_primary_pinned_model_id |
| T-GWY-0019 | SecondaryAdapter has pinned model_id | fast | gateway/test_T_GWY_0013_to_0024.py | test_T_GWY_0019_secondary_pinned_model_id |
| T-GWY-0020 | LocalAdapter has pinned model_id | fast | gateway/test_T_GWY_0013_to_0024.py | test_T_GWY_0020_local_pinned_model_id |
| T-GWY-0021 | An identifier change without a recorded evaluation is rejected | fast | gateway/test_T_GWY_0013_to_0024.py | test_T_GWY_0021_identifier_change_rejected |
| T-GWY-0022 | PrimaryAdapter declares processing_region | fast | gateway/test_T_GWY_0013_to_0024.py | test_T_GWY_0022_primary_region |
| T-GWY-0023 | SecondaryAdapter declares processing_region | fast | gateway/test_T_GWY_0013_to_0024.py | test_T_GWY_0023_secondary_region |
| T-GWY-0024 | LocalAdapter declares processing_region | fast | gateway/test_T_GWY_0013_to_0024.py | test_T_GWY_0024_local_region |
| T-GWY-0025 | A timeout ends in fallback or recorded refusal | fast | gateway/test_T_GWY_0025_to_0036.py | test_T_GWY_0025_timeout_fallback |
| T-GWY-0026 | Circuit breaker opens after max_failures | fast | gateway/test_T_GWY_0025_to_0036.py | test_T_GWY_0026_circuit_opens |
| T-GWY-0027 | Circuit breaker blocks calls when open | fast | gateway/test_T_GWY_0025_to_0036.py | test_T_GWY_0027_circuit_blocks |
| T-GWY-0028 | Bounded retry retries up to max_retries | fast | gateway/test_T_GWY_0025_to_0036.py | test_T_GWY_0028_bounded_retry |
| T-GWY-0029 | Fallback to second adapter on failure | fast | gateway/test_T_GWY_0025_to_0036.py | test_T_GWY_0029_fallback_on_failure |
| T-GWY-0030 | Fallback is recorded (response.fallback == True) | fast | gateway/test_T_GWY_0025_to_0036.py | test_T_GWY_0030_fallback_recorded |
| T-GWY-0031 | Budget limits hold for call count | fast | gateway/test_T_GWY_0025_to_0036.py | test_T_GWY_0031_budget_calls_exceeded |
| T-GWY-0032 | Budget limits hold for token count | fast | gateway/test_T_GWY_0025_to_0036.py | test_T_GWY_0032_budget_tokens_exceeded |
| T-GWY-0033 | Cache hit never crosses tenants | fast | gateway/test_T_GWY_0025_to_0036.py | test_T_GWY_0033_cache_tenant_isolation |
| T-GWY-0034 | Cache hit returns same response | fast | gateway/test_T_GWY_0025_to_0036.py | test_T_GWY_0034_cache_hit |
| T-GWY-0035 | A refused call yields ABSTAIN or ESCALATE, never silent truncation | fast | gateway/test_T_GWY_0025_to_0036.py | test_T_GWY_0035_refused_call_explicit |
| T-GWY-0036 | Deterministic path continues when model unavailable | fast | gateway/test_T_GWY_0025_to_0036.py | test_T_GWY_0036_deterministic_path_continues |
| T-GWY-0037 | A field without a locator is rejected | fast | extract/test_T_GWY_0037_to_0050.py | test_T_GWY_0037_field_without_locator_rejected |
| T-GWY-0038 | A guessed field on a document lacking it counts as a defect | fast | extract/test_T_GWY_0037_to_0050.py | test_T_GWY_0038_guessed_field_is_unknown |
| T-GWY-0039 | An instruction inside a document has no effect on tools or flow | fast | extract/test_T_GWY_0037_to_0050.py | test_T_GWY_0039_instruction_in_document_no_effect |
| T-GWY-0040 | Extract produces fields matching the schema | fast | extract/test_T_GWY_0037_to_0050.py | test_T_GWY_0040_extract_all_fields |
| T-GWY-0041 | Every extracted field carries a locator | fast | extract/test_T_GWY_0037_to_0050.py | test_T_GWY_0041_every_field_has_locator |
| T-GWY-0042 | Every extracted field carries a method | fast | extract/test_T_GWY_0037_to_0050.py | test_T_GWY_0042_every_field_has_method |
| T-GWY-0043 | An unextractable field becomes UNKNOWN | fast | extract/test_T_GWY_0037_to_0050.py | test_T_GWY_0043_unextractable_becomes_unknown |
| T-GWY-0044 | ExtractRequest is frozen | fast | extract/test_T_GWY_0037_to_0050.py | test_T_GWY_0044_extract_request_frozen |
| T-GWY-0045 | ExtractedField is frozen | fast | extract/test_T_GWY_0037_to_0050.py | test_T_GWY_0045_extracted_field_frozen |
| T-GWY-0046 | FieldLocator is frozen | fast | extract/test_T_GWY_0037_to_0050.py | test_T_GWY_0046_field_locator_frozen |
| T-GWY-0047 | Extract is tool-less (model receives only text and schema) | fast | extract/test_T_GWY_0037_to_0050.py | test_T_GWY_0047_extract_toolless |
| T-GWY-0048 | Extract is secret-less | fast | extract/test_T_GWY_0037_to_0050.py | test_T_GWY_0048_extract_secretless |
| T-GWY-0049 | UNKNOWN constant is defined | fast | extract/test_T_GWY_0037_to_0050.py | test_T_GWY_0049_unknown_constant |
| T-GWY-0050 | ExtractResult has fields list | fast | extract/test_T_GWY_0037_to_0050.py | test_T_GWY_0050_extract_result_has_fields |
| T-GWY-0051 | A proposal changed after commitment cannot be approved | fast | extract/test_T_GWY_0051_to_0064.py | test_T_GWY_0051_changed_proposal_rejected |
| T-GWY-0052 | Ungrounded claims are rejected | fast | extract/test_T_GWY_0051_to_0064.py | test_T_GWY_0052_ungrounded_claims_rejected |
| T-GWY-0053 | Dual extraction disagreement gives HOLD | fast | extract/test_T_GWY_0051_to_0064.py | test_T_GWY_0053_dual_extraction_disagreement_hold |
| T-GWY-0054 | Verified facts carry their locator | fast | extract/test_T_GWY_0051_to_0064.py | test_T_GWY_0054_verified_facts_carry_locator |
| T-GWY-0055 | Grounding exact match passes | fast | extract/test_T_GWY_0051_to_0064.py | test_T_GWY_0055_grounding_exact_match |
| T-GWY-0056 | Grounding normalized match passes | fast | extract/test_T_GWY_0051_to_0064.py | test_T_GWY_0056_grounding_normalized_match |
| T-GWY-0057 | SchemaChecker rejects missing method | fast | extract/test_T_GWY_0051_to_0064.py | test_T_GWY_0057_schema_verifier_missing_method |
| T-GWY-0058 | RuleConformanceChecker checks required fields | fast | extract/test_T_GWY_0051_to_0064.py | test_T_GWY_0058_rule_conformance_missing |
| T-GWY-0059 | RecomputationChecker rejects UNKNOWN extracted fields | fast | extract/test_T_GWY_0051_to_0064.py | test_T_GWY_0059_recomputation_unknown |
| T-GWY-0060 | Dual extraction agreement yields ALLOW | fast | extract/test_T_GWY_0051_to_0064.py | test_T_GWY_0060_dual_extraction_agreement |
| T-GWY-0061 | ground_fields grounds multiple fields | fast | extract/test_T_GWY_0051_to_0064.py | test_T_GWY_0061_ground_fields |
| T-GWY-0062 | ProposeVerifyGate passes a valid proposal | fast | extract/test_T_GWY_0051_to_0064.py | test_T_GWY_0062_gate_passes_valid |
| T-GWY-0063 | Proposal is frozen | fast | extract/test_T_GWY_0051_to_0064.py | test_T_GWY_0063_proposal_frozen |
| T-GWY-0064 | VerificationResult is frozen | fast | extract/test_T_GWY_0051_to_0064.py | test_T_GWY_0064_verification_result_frozen |
| T-GWY-0065 | Thresholds are met (exact match >= 95%) | fast | gateway/test_T_GWY_0065_to_0076.py | test_T_GWY_0065_exact_match_threshold |
| T-GWY-0066 | Wrongly filled fields == 0 | fast | gateway/test_T_GWY_0065_to_0076.py | test_T_GWY_0066_wrongly_filled_zero |
| T-GWY-0067 | Grounding precision >= 99% | fast | gateway/test_T_GWY_0065_to_0076.py | test_T_GWY_0067_grounding_precision |
| T-GWY-0068 | Adversarial documents with no effect == 100% | fast | gateway/test_T_GWY_0065_to_0076.py | test_T_GWY_0068_injection_resistance |
| T-GWY-0069 | A seeded regression fails the gate | fast | gateway/test_T_GWY_0065_to_0076.py | test_T_GWY_0069_regression_detected |
| T-GWY-0070 | Baselines move only through the gate | fast | gateway/test_T_GWY_0065_to_0076.py | test_T_GWY_0070_baselines_protected |
| T-GWY-0071 | SYNTHETIC evaluation sets exist | fast | gateway/test_T_GWY_0065_to_0076.py | test_T_GWY_0071_synthetic_sets_exist |
| T-GWY-0072 | Arabic digit variants in eval sets | fast | gateway/test_T_GWY_0065_to_0076.py | test_T_GWY_0072_arabic_variants |
| T-GWY-0073 | Persian digit variants in eval sets | fast | gateway/test_T_GWY_0065_to_0076.py | test_T_GWY_0073_persian_variants |
| T-GWY-0074 | Adversarial injection set exists | fast | gateway/test_T_GWY_0065_to_0076.py | test_T_GWY_0074_adversarial_set |
| T-GWY-0075 | Explanation faithfulness threshold met | fast | gateway/test_T_GWY_0065_to_0076.py | test_T_GWY_0075_explanation_faithfulness |
| T-GWY-0076 | Eval sets have expected_fields | fast | gateway/test_T_GWY_0065_to_0076.py | test_T_GWY_0076_eval_sets_have_expected_fields |
| T-GWY-0077 | A recorded trace contains tier, tokens and cost | fast | gateway/test_T_GWY_0077_to_0084.py | test_T_GWY_0077_trace_contains_attributes |
| T-GWY-0078 | Mapped threat items have tests | fast | gateway/test_T_GWY_0077_to_0084.py | test_T_GWY_0078_mapped_items_have_tests |
| T-GWY-0079 | Crash recovery during a call leaves exactly one call record | fast | gateway/test_T_GWY_0077_to_0084.py | test_T_GWY_0079_crash_recovery_one_record |
| T-GWY-0080 | TraceAttributes is frozen | fast | gateway/test_T_GWY_0077_to_0084.py | test_T_GWY_0080_trace_attributes_frozen |
| T-GWY-0081 | ATTACK_CATALOG includes model-gateway threats | fast | gateway/test_T_GWY_0077_to_0084.py | test_T_GWY_0081_attack_catalog_has_model_threats |
| T-GWY-0082 | InMemoryTracer call_count is accurate | fast | gateway/test_T_GWY_0077_to_0084.py | test_T_GWY_0082_tracer_count |
| T-GWY-0083 | Tracer records provider and model_id | fast | gateway/test_T_GWY_0077_to_0084.py | test_T_GWY_0083_trace_provider_model |
| T-GWY-0084 | Tracer clear resets to zero | fast | gateway/test_T_GWY_0077_to_0084.py | test_T_GWY_0084_tracer_clear |
| T-GWY-0085 | A call inside the profile succeeds and records its region | fast | gateway/test_T_GWY_0085_to_0096.py | test_T_GWY_0085_call_inside_profile_succeeds |
| T-GWY-0086 | A call outside the profile is refused with REGION_POLICY and no provider is contacted | fast | gateway/test_T_GWY_0085_to_0096.py | test_T_GWY_0086_call_outside_profile_refused |
| T-GWY-0087 | A missing profile allows only the local adapter | fast | gateway/test_T_GWY_0085_to_0096.py | test_T_GWY_0087_missing_profile_local_only |
| T-GWY-0088 | A missing declared region fails closed | fast | gateway/test_T_GWY_0085_to_0096.py | test_T_GWY_0088_missing_region_fails_closed |
| T-GWY-0089 | The policy decision is identical for the same inputs | fast | gateway/test_T_GWY_0085_to_0096.py | test_T_GWY_0089_policy_deterministic |
| T-GWY-0090 | RegionProfile is frozen | fast | gateway/test_T_GWY_0085_to_0096.py | test_T_GWY_0090_region_profile_frozen |
| T-GWY-0091 | check_region allows allowed regions | fast | gateway/test_T_GWY_0085_to_0096.py | test_T_GWY_0091_check_region_allows |
| T-GWY-0092 | check_region rejects disallowed regions | fast | gateway/test_T_GWY_0085_to_0096.py | test_T_GWY_0092_check_region_rejects |
| T-GWY-0093 | check_region fails closed on empty region | fast | gateway/test_T_GWY_0085_to_0096.py | test_T_GWY_0093_check_region_empty |
| T-GWY-0094 | DEFAULT_PROFILE is local-only | fast | gateway/test_T_GWY_0085_to_0096.py | test_T_GWY_0094_default_profile_local |
| T-GWY-0095 | REGION_POLICY_REASON is defined | fast | gateway/test_T_GWY_0085_to_0096.py | test_T_GWY_0095_region_policy_reason |
| T-GWY-0096 | RegionPolicyChecker with custom profile | fast | gateway/test_T_GWY_0085_to_0096.py | test_T_GWY_0096_custom_profile |
| T-INT-0001 | Document roundtrip and tenant isolation | fast | intake/test_intake.py | test_T_INT_0001_document_roundtrip_and_tenant_isolation |
| T-INT-0010 | Parse supported formats | fast | intake/test_intake.py | test_T_INT_0010_parse_supported_formats |
| T-INT-0011 | Erasure retains shared originals until the last document reference | fast | intake/test_intake.py | test_T_INT_0011_erasure_reference_lifecycle |
| T-INT-0012 | Date normalization handles explicit locale and rejects invalid month names | fast | intake/test_intake.py | test_T_INT_0012_date_format_boundaries |
| T-INT-0021 | Reader refuses unusable payload | fast | intake/test_intake.py | test_T_INT_0021_reader_refuses_unusable_payload |
| T-INT-0022 | Rejects unsafe archive | fast | intake/test_intake.py | test_T_INT_0022_rejects_unsafe_archive |
| T-INT-0023 | Reader crash is contained | fast | intake/test_intake.py | test_T_INT_0023_reader_crash_is_contained |
| T-INT-0024 | Network denied in worker | fast | intake/test_intake.py | test_T_INT_0024_network_denied_in_worker |
| T-INT-0041 | Parallel extraction feeds consistency | fast | pairs/test_intake_pipeline.py | test_T_INT_0041_parallel_extraction_feeds_consistency |
| T-INT-0042 | Flagged value is not canonical | fast | pairs/test_intake_pipeline.py | test_T_INT_0042_flagged_value_is_not_canonical |
| T-INT-0043 | Skeleton reaches replayed passport | fast | pairs/test_intake_pipeline.py | test_T_INT_0043_skeleton_reaches_replayed_passport |
| T-INT-0044 | Api uniform capability path | fast | pairs/test_intake_pipeline.py | test_T_INT_0044_api_uniform_capability_path |
| T-INT-0045 | Cli document workflow | fast | pairs/test_intake_pipeline.py | test_T_INT_0045_cli_document_workflow |
| T-INT-0046 | Reviewer relation and erasure refresh related case evidence | fast | pairs/test_intake_pipeline.py | test_T_INT_0046_relation_and_erasure |
| T-INT-0047 | Access, write-path and name-link boundaries survive repeat ingestion | fast | pairs/test_intake_pipeline.py | test_T_INT_0047_case_ownership_and_repeat_intake |
| T-INT-0061 | Disabled and tampered ocr | fast | intake/test_intake.py | test_T_INT_0061_disabled_and_tampered_ocr |
| T-INT-0062 | Oversized scan is refused before ocr | fast | intake/test_intake.py | test_T_INT_0062_oversized_scan_is_refused_before_ocr |
| T-INT-0063 | Scan fixture has stable bytes | fast | intake/test_intake.py | test_T_INT_0063_scan_fixture_has_stable_bytes |
| T-INT-0064 | OCR derives error counts and accepts only complete owner pins | fast | intake/test_intake.py | test_T_INT_0064_ocr_configuration_and_error_totals |
| T-K05-0001 | Interval scenarios | fast | k05/test_valuation.py | test_interval_scenarios |
| T-K05-0002 | Declared documentary mismatch | fast | k05/test_valuation.py | test_T_K05_0002_declared_documentary_mismatch |
| T-K05-0006 | Falls back to parent | fast | k05/test_valuation.py | test_T_K05_0006_falls_back_to_parent |
| T-K05-0007 | Missing dated rate | fast | k05/test_valuation.py | test_T_K05_0007_missing_dated_rate |
| T-K05-0008 | Tonnes match kilograms | fast | k05/test_valuation.py | test_T_K05_0008_tonnes_match_kilograms |
| T-K05-0009 | Quantity weighted aggregate is below | fast | k05/test_valuation.py | test_T_K05_0009_quantity_weighted_aggregate_is_below |
| T-K05-0010 | Bounds require review privilege | fast | k05/test_valuation.py | test_T_K05_0010_bounds_require_review_privilege |
| T-K05-0011 | Calibration coverage | slow | k05/test_valuation.py | test_T_K05_0011_calibration_coverage |
| T-K05-0012 | Untrusted label is not an instruction | fast | k05/test_valuation.py | test_T_K05_0012_untrusted_label_is_not_an_instruction |
| T-K05-0013 | Expired reference | fast | k05/test_valuation.py | test_T_K05_0013_expired_reference |
| T-K05-0014 | Missing required adjustment | fast | k05/test_valuation.py | test_T_K05_0014_missing_required_adjustment |
| T-K05-0015 | Floor bounds for zero spread | fast | k05/test_valuation.py | test_T_K05_0015_floor_bounds_for_zero_spread |
| T-K05-0101 | Closed reason registry | fast | k05/test_valuation.py | test_closed_reason_registry |
| T-K05-0115 | Real origin requires tenant calibration | fast | k05/test_valuation.py | test_T_K05_0115_real_origin_requires_tenant_calibration |
| T-K05-0201 | Exact unit conversion | fast | k05/test_basis_and_reference.py | test_T_K05_0201_exact_unit_conversion |
| T-K05-0202 | Exact currency conversion | fast | k05/test_basis_and_reference.py | test_T_K05_0202_exact_currency_conversion |
| T-K05-0203 | Documentary basis fraction oracle | fast | k05/test_basis_and_reference.py | test_T_K05_0203_documentary_basis_fraction_oracle |
| T-K05-0204 | Reference median and mad | fast | k05/test_basis_and_reference.py | test_reference_median_and_mad |
| T-K05-0212 | Reference sample boundaries | fast | k05/test_basis_and_reference.py | test_reference_sample_boundaries |
| T-K05-0219 | Split quantile matches rank | fast | k05/test_basis_and_reference.py | test_split_quantile_matches_rank |
| T-K05-0225 | Unavailable inputs abstain | fast | k05/test_basis_and_reference.py | test_unavailable_inputs_abstain |
| T-K05-0229 | Grams scale exactly | fast | k05/test_basis_and_reference.py | test_T_K05_0229_grams_scale_exactly |
| T-K05-0230 | Currency and unit conversion compose | fast | k05/test_basis_and_reference.py | test_T_K05_0230_currency_and_unit_conversion_compose |
| T-K05-0231 | Invalid unit factor is refused | fast | k05/test_interfaces.py | test_T_K05_0231_invalid_unit_factor_is_refused |
| T-K05-0232 | Invalid reference sample abstains | fast | k05/test_interfaces.py | test_T_K05_0232_invalid_reference_sample_abstains |
| T-K05-0233 | Calibration rejects insufficient draws | fast | k05/test_interfaces.py | test_T_K05_0233_calibration_rejects_insufficient_draws |
| T-K05-0234 | Public abstention has no basis or calibration | fast | k05/test_interfaces.py | test_T_K05_0234_public_abstention_has_no_basis_or_calibration |
| T-K05-0235 | Ambiguous canonical quantity abstains | fast | k05/test_interfaces.py | test_T_K05_0235_ambiguous_canonical_quantity_abstains |
| T-K05-0236 | Missing adjustment reference abstains | fast | k05/test_interfaces.py | test_T_K05_0236_missing_adjustment_reference_abstains |
| T-K05-0237 | Duplicate rule adjustment rejected | fast | k05/test_interfaces.py | test_T_K05_0237_duplicate_rule_adjustment_rejected |
| T-K05-0238 | Unbound valuation rules abstain | fast | k05/test_interfaces.py | test_T_K05_0238_unbound_valuation_rules_abstain |
| T-K05-0239 | Exact upper endpoint is inside | fast | k05/test_valuation.py | test_T_K05_0239_exact_upper_endpoint_is_inside |
| T-K05-0301 | Rejects nonpositive and nonfinite values | fast | k05/test_interfaces.py | test_rejects_nonpositive_and_nonfinite_values |
| T-K05-0308 | Rejects invalid quantities | fast | k05/test_interfaces.py | test_rejects_invalid_quantities |
| T-K05-0313 | Rejects unknown or incompatible units | fast | k05/test_interfaces.py | test_rejects_unknown_or_incompatible_units |
| T-K05-0319 | Tiny quantity is detected | fast | k05/test_interfaces.py | test_T_K05_0319_tiny_quantity_is_detected |
| T-K05-0320 | Extreme reference outlier keeps robust position | fast | k05/test_interfaces.py | test_T_K05_0320_extreme_reference_outlier_keeps_robust_position |
| T-K05-0401 | Replay is deterministic | fast | k05/test_interfaces.py | test_T_K05_0401_replay_is_deterministic |
| T-K05-0402 | Evidence commits to input change | fast | k05/test_interfaces.py | test_T_K05_0402_evidence_commits_to_input_change |
| T-K05-0403 | Operator report uses redacted positions | fast | k05/test_interfaces.py | test_T_K05_0403_operator_report_uses_redacted_positions |
| T-K05-0404 | Reviewer can inspect bounds | fast | k05/test_interfaces.py | test_T_K05_0404_reviewer_can_inspect_bounds |
| T-K05-0405 | Other tenant cannot invoke | fast | k05/test_interfaces.py | test_T_K05_0405_other_tenant_cannot_invoke |
| T-K05-0406 | Other tenant cannot retrieve | fast | k05/test_interfaces.py | test_T_K05_0406_other_tenant_cannot_retrieve |
| T-K05-0407 | Fact revocation marks result stale | fast | k05/test_interfaces.py | test_T_K05_0407_fact_revocation_marks_result_stale |
| T-K05-0408 | Same idempotency key returns same evaluation | fast | k05/test_interfaces.py | test_T_K05_0408_same_idempotency_key_returns_same_evaluation |
| T-K05-0409 | Idempotency payload change returns conflict | fast | k05/test_interfaces.py | test_T_K05_0409_idempotency_payload_change_returns_conflict |
| T-K05-0410 | Query cannot select supplied facts | fast | k05/test_interfaces.py | test_T_K05_0410_query_cannot_select_supplied_facts |
| T-K05-0501 | Registration reads verified canonical facts | fast | k05/test_interfaces.py | test_T_K05_0501_registration_reads_verified_canonical_facts |
| T-K05-0502 | Missing idempotency key fails validation | fast | k05/test_interfaces.py | test_T_K05_0502_missing_idempotency_key_fails_validation |
| T-K05-0503 | Naive time fails validation | fast | k05/test_interfaces.py | test_T_K05_0503_naive_time_fails_validation |
| T-K05-0504 | Generated openapi has evaluation operations | fast | k05/test_interfaces.py | test_T_K05_0504_generated_openapi_has_evaluation_operations |
| T-K05-0505 | View banner is verbatim | fast | k05/test_interfaces.py | test_T_K05_0505_view_banner_is_verbatim |
| T-K05-0506 | Coverage claim is verbatim | fast | k05/test_interfaces.py | test_T_K05_0506_coverage_claim_is_verbatim |
| T-K05-0507 | View never recommends a value | fast | k05/test_interfaces.py | test_view_never_recommends_a_value |
| T-K05-0511 | Evidence cites reference and calibration | fast | k05/test_interfaces.py | test_T_K05_0511_evidence_cites_reference_and_calibration |
| T-K05-0512 | Untrusted note cannot change report | fast | k05/test_interfaces.py | test_T_K05_0512_untrusted_note_cannot_change_report |
| T-K09-0001 | K09-S01 golden scenario | fast | k09/test_shield.py | test_T_K09_0001_golden_scenario |
| T-K09-0002 | K09-S02 golden scenario | fast | k09/test_shield.py | test_T_K09_0002_golden_scenario |
| T-K09-0003 | K09-S03 golden scenario | fast | k09/test_shield.py | test_T_K09_0003_golden_scenario |
| T-K09-0004 | K09-S04 golden scenario | fast | k09/test_shield.py | test_T_K09_0004_golden_scenario |
| T-K09-0005 | K09-S05 golden scenario | fast | k09/test_shield.py | test_T_K09_0005_golden_scenario |
| T-K09-0006 | K09-S06 golden scenario | fast | k09/test_shield.py | test_T_K09_0006_golden_scenario |
| T-K09-0007 | K09-S07 golden scenario | fast | k09/test_shield.py | test_T_K09_0007_golden_scenario |
| T-K09-0008 | K09-S08 golden scenario | fast | k09/test_shield.py | test_T_K09_0008_golden_scenario |
| T-K09-0009 | K09-S09 golden scenario | fast | k09/test_shield.py | test_T_K09_0009_golden_scenario |
| T-K09-0010 | K09-S10 golden scenario | fast | k09/test_shield.py | test_T_K09_0010_golden_scenario |
| T-K09-0011 | K09-S11 golden scenario | fast | k09/test_shield.py | test_T_K09_0011_golden_scenario |
| T-K09-0012 | K09-S12 golden scenario | fast | k09/test_shield.py | test_T_K09_0012_golden_scenario |
| T-K09-0013 | K09-S13 golden scenario | fast | k09/test_shield.py | test_T_K09_0013_golden_scenario |
| T-K09-0014 | K09-S14 golden scenario | fast | k09/test_shield.py | test_T_K09_0014_golden_scenario |
| T-K09-0015 | K09-S15 golden scenario | fast | k09/test_shield.py | test_T_K09_0015_golden_scenario |
| T-K09-0016 | K09-S16 golden scenario | fast | k09/test_shield.py | test_T_K09_0016_golden_scenario |
| T-K09-0017 | K09-S17 golden scenario | fast | k09/test_shield.py | test_T_K09_0017_golden_scenario |
| T-K09-0101 | Fail closed modes | fast | k09/test_shield.py | test_T_K09_0101_fail_closed_modes |
| T-K09-0111 | Index and identity completeness | fast | k09/test_shield.py | test_T_K09_0111_index_and_identity_completeness |
| T-K09-0201 | Bucket agrees with brute force | fast | k09/test_shield.py | test_T_K09_0201_bucket_agrees_with_brute_force |
| T-K09-0202 | Similarity bands | fast | k09/test_shield.py | test_T_K09_0202_similarity_bands |
| T-K09-0301 | Unrelated documents do not change findings | fast | k09/test_shield.py | test_T_K09_0301_unrelated_documents_do_not_change_findings |
| T-K09-0302 | Confusables are protective only for identity | fast | k09/test_shield.py | test_T_K09_0302_confusables_are_protective_only_for_identity |
| T-K09-0303 | Producer observations leave candidate caps unchanged | fast | k09/test_shield.py | test_T_K09_0303_candidate_cap_boundary |
| T-K09-0401 | Reuse is symmetric and tenant scoped | fast | k09/test_shield.py | test_T_K09_0401_reuse_is_symmetric_and_tenant_scoped |
| T-K09-0402 | Resave detected and relation applies only to pair | fast | k09/test_shield.py | test_T_K09_0402_resave_detected_and_relation_applies_only_to_pair |
| T-K09-0403 | Coverage and erasure | fast | k09/test_shield.py | test_T_K09_0403_coverage_and_erasure |
| T-K09-0404 | PostgreSQL fingerprint lookup and cascade respect tenancy | slow | k09/test_fingerprint_store.py | test_T_K09_0404_postgres_fingerprint_joins_and_erasure |
| T-K09-0405 | Approved amendments and closed cases retain their boundaries | fast | k09/test_shield.py | test_T_K09_0405_amendment_and_closed_results |
| T-K14-0001 | K14-S01 golden scenario | fast | k14/test_bilingual.py | test_T_K14_0001_golden_scenario |
| T-K14-0002 | K14-S02 golden scenario | fast | k14/test_bilingual.py | test_T_K14_0002_golden_scenario |
| T-K14-0003 | K14-S03 golden scenario | fast | k14/test_bilingual.py | test_T_K14_0003_golden_scenario |
| T-K14-0004 | K14-S04 golden scenario | fast | k14/test_bilingual.py | test_T_K14_0004_golden_scenario |
| T-K14-0005 | K14-S05 golden scenario | fast | k14/test_bilingual.py | test_T_K14_0005_golden_scenario |
| T-K14-0006 | K14-S06 golden scenario | fast | k14/test_bilingual.py | test_T_K14_0006_golden_scenario |
| T-K14-0007 | K14-S07 golden scenario | fast | k14/test_bilingual.py | test_T_K14_0007_golden_scenario |
| T-K14-0008 | K14-S08 golden scenario | fast | k14/test_bilingual.py | test_T_K14_0008_golden_scenario |
| T-K14-0009 | K14-S09 golden scenario | fast | k14/test_bilingual.py | test_T_K14_0009_golden_scenario |
| T-K14-0010 | K14-S10 golden scenario | fast | k14/test_bilingual.py | test_T_K14_0010_golden_scenario |
| T-K14-0011 | K14-S11 golden scenario | fast | k14/test_bilingual.py | test_T_K14_0011_golden_scenario |
| T-K14-0012 | K14-S12 golden scenario | fast | k14/test_bilingual.py | test_T_K14_0012_golden_scenario |
| T-K14-0013 | K14-S13 golden scenario | fast | k14/test_bilingual.py | test_T_K14_0013_golden_scenario |
| T-K14-0014 | K14-S14 golden scenario | fast | k14/test_bilingual.py | test_T_K14_0014_golden_scenario |
| T-K14-0015 | K14-S15 golden scenario | fast | k14/test_bilingual.py | test_T_K14_0015_golden_scenario |
| T-K14-0016 | K14-S16 golden scenario | fast | k14/test_bilingual.py | test_T_K14_0016_golden_scenario |
| T-K14-0017 | K14-S17 golden scenario | fast | k14/test_bilingual.py | test_T_K14_0017_golden_scenario |
| T-K14-0018 | K14-S18 golden scenario | fast | k14/test_bilingual.py | test_T_K14_0018_golden_scenario |
| T-K14-0019 | K14-S19 golden scenario | fast | k14/test_bilingual.py | test_T_K14_0019_golden_scenario |
| T-K14-0020 | K14-S20 golden scenario | fast | k14/test_bilingual.py | test_T_K14_0020_golden_scenario |
| T-K14-0101 | Flagged values stay unknown | fast | k14/test_bilingual.py | test_T_K14_0101_flagged_values_stay_unknown |
| T-K14-0102 | Ocr cannot verify and low confidence abstains | fast | k14/test_bilingual.py | test_T_K14_0102_ocr_cannot_verify_and_low_confidence_abstains |
| T-K14-0103 | Hijri requires explicit calendar pack | fast | k14/test_bilingual.py | test_T_K14_0103_hijri_requires_explicit_calendar_pack |
| T-K14-0110 | Meter exhaustion | fast | k14/test_bilingual.py | test_T_K14_0110_meter_exhaustion |
| T-K14-0201 | Comparison idempotence | fast | k14/test_bilingual.py | test_T_K14_0201_comparison_idempotence |
| T-K14-0202 | Digit mapping keeps originals | fast | k14/test_bilingual.py | test_T_K14_0202_digit_mapping_keeps_originals |
| T-K14-0203 | Bilingual values | fast | k14/test_bilingual.py | test_T_K14_0203_bilingual_values |
| T-K14-0204 | Parallel comparisons retain only verified comparable fields | fast | k14/test_bilingual.py | test_T_K14_0204_parallel_comparator_categories |
| T-K14-0301 | Locator and typed value both checked | fast | k14/test_bilingual.py | test_T_K14_0301_locator_and_typed_value_both_checked |
| T-K14-0302 | Typed proposals reject mixed digits, bad identifiers and bad locators | fast | k14/test_bilingual.py | test_T_K14_0302_typed_value_protections |
| T-K14-0401 | Recorded replay and parallel check | fast | k14/test_bilingual.py | test_T_K14_0401_recorded_replay_and_parallel_check |
| T-K14-0501 | Abstentions | fast | k14/test_bilingual.py | test_T_K14_0501_abstentions |
| T-K14-0502 | At most two model calls and only retry unknown | fast | k14/test_bilingual.py | test_T_K14_0502_at_most_two_model_calls_and_only_retry_unknown |
| T-K14-0503 | The Gateway preflights case page and token ceilings | fast | k14/test_bilingual.py | test_T_K14_0503_gateway_budget_preflight |
| T-KRN-0001 | Regeneration is byte-identical | fast | kernel/test_T_KRN_0001_to_0008.py | test_T_KRN_0001_regeneration_byte_identical |
| T-KRN-0002 | A hand edit of a generated file fails the gate | fast | kernel/test_T_KRN_0001_to_0008.py | test_T_KRN_0002_hand_edit_fails_gate |
| T-KRN-0003 | Every entity has tenant_id and schema_version | fast | kernel/test_T_KRN_0001_to_0008.py | test_T_KRN_0003_every_entity_has_tenant_id_and_schema_version |
| T-KRN-0004 | Models are immutable (mutation returns a new value) | fast | kernel/test_T_KRN_0001_to_0008.py | test_T_KRN_0004_models_are_immutable |
| T-KRN-0005 | No untyped dictionary crosses a module boundary | fast | kernel/test_T_KRN_0001_to_0008.py | test_T_KRN_0005_no_untyped_dict_crosses_boundary |
| T-KRN-0006 | Models validate against strict typing | fast | kernel/test_T_KRN_0001_to_0008.py | test_T_KRN_0006_models_strict_typing |
| T-KRN-0007 | Generated files carry the AUTO-GENERATED header | fast | kernel/test_T_KRN_0001_to_0008.py | test_T_KRN_0007_generated_files_have_header |
| T-KRN-0008 | __init__.py re-exports all entity models | fast | kernel/test_T_KRN_0001_to_0008.py | test_T_KRN_0008_init_reexports_all_models |
| T-KRN-0009 | Known-answer vector for RFC 8785 canonical JSON | fast | kernel/test_T_KRN_0009_to_0018.py | test_T_KRN_0009_rfc8785_known_answer |
| T-KRN-0010 | Known-answer vector for SHA-256 domain hash | fast | kernel/test_T_KRN_0009_to_0018.py | test_T_KRN_0010_sha256_known_answer |
| T-KRN-0011 | Cross-purpose hash separation | fast | kernel/test_T_KRN_0009_to_0018.py | test_T_KRN_0011_cross_purpose_hash_separation |
| T-KRN-0012 | Decimals serialize without exponent or trailing zeros ambiguity | fast | kernel/test_T_KRN_0009_to_0018.py | test_T_KRN_0012_decimal_serialization |
| T-KRN-0013 | Key order stability under random input order | fast | kernel/test_T_KRN_0009_to_0018.py | test_T_KRN_0013_key_order_stability |
| T-KRN-0014 | Number formatting stability under random input | fast | kernel/test_T_KRN_0009_to_0018.py | test_T_KRN_0014_number_formatting_stability |
| T-KRN-0015 | Unknown tag rejected | fast | kernel/test_T_KRN_0009_to_0018.py | test_T_KRN_0015_unknown_tag_rejected |
| T-KRN-0016 | Algorithm identifier present | fast | kernel/test_T_KRN_0009_to_0018.py | test_T_KRN_0016_algorithm_identifier |
| T-KRN-0017 | Tag registry validates and all tags are unique | fast | kernel/test_T_KRN_0009_to_0018.py | test_T_KRN_0017_tag_registry_validates |
| T-KRN-0018 | Differential test: rfc8785 vs jcs produce identical output | fast | kernel/test_T_KRN_0009_to_0018.py | test_T_KRN_0018_differential_rfc8785_vs_jcs |
| T-KRN-0019 | Lattice combine is associative | fast | kernel/test_T_KRN_0019_to_0030.py | test_T_KRN_0019_combine_associative |
| T-KRN-0020 | Lattice combine is commutative | fast | kernel/test_T_KRN_0019_to_0030.py | test_T_KRN_0020_combine_commutative |
| T-KRN-0021 | Lattice combine is idempotent | fast | kernel/test_T_KRN_0019_to_0030.py | test_T_KRN_0021_combine_idempotent |
| T-KRN-0022 | Lattice combine is monotone | fast | kernel/test_T_KRN_0019_to_0030.py | test_T_KRN_0022_combine_monotone |
| T-KRN-0023 | Combined reasons equal the union of inputs | fast | kernel/test_T_KRN_0019_to_0030.py | test_T_KRN_0023_combined_reasons_union |
| T-KRN-0024 | Floats are rejected in Money | fast | kernel/test_T_KRN_0019_to_0030.py | test_T_KRN_0024_floats_rejected_in_money |
| T-KRN-0025 | Floats are rejected in Quantity | fast | kernel/test_T_KRN_0019_to_0030.py | test_T_KRN_0025_floats_rejected_in_quantity |
| T-KRN-0026 | Rounding mode is mandatory in Money | fast | kernel/test_T_KRN_0019_to_0030.py | test_T_KRN_0026_rounding_mode_mandatory |
| T-KRN-0027 | Weakest-of agrees with the P02 helper on all label pairs | fast | kernel/test_T_KRN_0019_to_0030.py | test_T_KRN_0027_weakest_of_agrees_with_p2 |
| T-KRN-0028 | Money add with mismatched currency fails | fast | kernel/test_T_KRN_0019_to_0030.py | test_T_KRN_0028_money_currency_mismatch |
| T-KRN-0029 | Duration rejects negative values | fast | kernel/test_T_KRN_0019_to_0030.py | test_T_KRN_0029_duration_rejects_negative |
| T-KRN-0030 | Identifier is opaque and immutable | fast | kernel/test_T_KRN_0019_to_0030.py | test_T_KRN_0030_identifier_immutable |
| T-KRN-0031 | Every status transition allowed or rejected as tabulated | fast | kernel/test_T_KRN_0031_to_0042.py | test_T_KRN_0031_status_transitions_tabulated |
| T-KRN-0032 | A conflicted fact key yields ESCALATE with both citations | fast | kernel/test_T_KRN_0031_to_0042.py | test_T_KRN_0032_conflicted_fact_escalate |
| T-KRN-0033 | A missing fact yields ABSTAIN | fast | kernel/test_T_KRN_0031_to_0042.py | test_T_KRN_0033_missing_fact_abstain |
| T-KRN-0034 | SECONDARY input never gives ALLOW | fast | kernel/test_T_KRN_0031_to_0042.py | test_T_KRN_0034_secondary_never_allow |
| T-KRN-0035 | SYNTHETIC-origin ALLOW carries the stamp | fast | kernel/test_T_KRN_0031_to_0042.py | test_T_KRN_0035_synthetic_allow_stamped |
| T-KRN-0036 | Real-data ALLOW with CALIBRATED_SYNTHETIC becomes ESCALATE | fast | kernel/test_T_KRN_0031_to_0042.py | test_T_KRN_0036_calibrated_synthetic_escalates |
| T-KRN-0037 | Real-data ALLOW with VALIDATED_TENANT stays ALLOW | fast | kernel/test_T_KRN_0031_to_0042.py | test_T_KRN_0037_validated_tenant_allows |
| T-KRN-0038 | ALLOW without a declared basis is rejected | fast | kernel/test_T_KRN_0031_to_0042.py | test_T_KRN_0038_allow_without_basis_rejected |
| T-KRN-0039 | The reader never returns a non-VERIFIED fact | fast | kernel/test_T_KRN_0031_to_0042.py | test_T_KRN_0039_reader_only_verified |
| T-KRN-0040 | PROPOSED to VERIFIED transition is allowed | fast | kernel/test_T_KRN_0031_to_0042.py | test_T_KRN_0040_proposed_to_verified |
| T-KRN-0041 | VERIFIED to SUPERSEDED transition is allowed | fast | kernel/test_T_KRN_0031_to_0042.py | test_T_KRN_0041_verified_to_superseded |
| T-KRN-0042 | REJECTED is a terminal state | fast | kernel/test_T_KRN_0031_to_0042.py | test_T_KRN_0042_rejected_is_terminal |
| T-KRN-0043 | Every (state, event) pair covered by the table | fast | kernel/test_T_KRN_0043_to_0052.py | test_T_KRN_0043_all_states_in_table |
| T-KRN-0044 | Undefined transitions are rejected | fast | kernel/test_T_KRN_0043_to_0052.py | test_T_KRN_0044_undefined_transition_rejected |
| T-KRN-0045 | Same idempotency key returns an identical result | fast | kernel/test_T_KRN_0043_to_0052.py | test_T_KRN_0045_idempotency_key_identical |
| T-KRN-0046 | A stale version yields the conflict error | fast | kernel/test_T_KRN_0043_to_0052.py | test_T_KRN_0046_stale_version_conflict |
| T-KRN-0047 | Two approvals of one proposal: the first wins | fast | kernel/test_T_KRN_0043_to_0052.py | test_T_KRN_0047_first_approval_wins |
| T-KRN-0048 | Timeouts move to BLOCKED, never approve | fast | kernel/test_T_KRN_0043_to_0052.py | test_T_KRN_0048_timeout_to_blocked |
| T-KRN-0049 | Re-evaluation supersedes by reference | fast | kernel/test_T_KRN_0043_to_0052.py | test_T_KRN_0049_re_evaluation_supersede |
| T-KRN-0050 | QUARANTINED state exists and can transition | fast | kernel/test_T_KRN_0043_to_0052.py | test_T_KRN_0050_quarantined_state |
| T-KRN-0051 | FAILED is a terminal state | fast | kernel/test_T_KRN_0043_to_0052.py | test_T_KRN_0051_failed_is_terminal |
| T-KRN-0052 | Normal lifecycle path is valid | fast | kernel/test_T_KRN_0043_to_0052.py | test_T_KRN_0052_normal_lifecycle |
| T-KRN-0053 | Every code has title, status and documentation text | fast | kernel/test_T_KRN_0053_to_0058.py | test_T_KRN_0053_every_code_has_fields |
| T-KRN-0054 | Codes are unique and never reused | fast | kernel/test_T_KRN_0053_to_0058.py | test_T_KRN_0054_codes_unique |
| T-KRN-0055 | The problem-details object validates | fast | kernel/test_T_KRN_0053_to_0058.py | test_T_KRN_0055_problem_details_validates |
| T-KRN-0056 | A broad exception handler in the core is rejected by lint | fast | kernel/test_T_KRN_0053_to_0058.py | test_T_KRN_0056_no_broad_except_in_core |
| T-KRN-0057 | Typed result types for expected failures | fast | kernel/test_T_KRN_0053_to_0058.py | test_T_KRN_0057_typed_result_types |
| T-KRN-0058 | get_error raises for unknown codes | fast | kernel/test_T_KRN_0053_to_0058.py | test_T_KRN_0058_unknown_code_raises |
| T-KRN-0059 | Invalid configuration is rejected | fast | kernel/test_T_KRN_0059_to_0064.py | test_T_KRN_0059_invalid_config_rejected |
| T-KRN-0060 | Hash is stable and changes with any field | fast | kernel/test_T_KRN_0059_to_0064.py | test_T_KRN_0060_hash_changes_with_field |
| T-KRN-0061 | Defaults equal the registry parameters | fast | kernel/test_T_KRN_0059_to_0064.py | test_T_KRN_0061_defaults_match_spec |
| T-KRN-0062 | Unknown keys are rejected | fast | kernel/test_T_KRN_0059_to_0064.py | test_T_KRN_0062_unknown_keys_rejected |
| T-KRN-0063 | Hash is deterministic across calls | fast | kernel/test_T_KRN_0059_to_0064.py | test_T_KRN_0063_hash_deterministic |
| T-KRN-0064 | Negative values are rejected | fast | kernel/test_T_KRN_0059_to_0064.py | test_T_KRN_0064_negative_values_rejected |
| T-KRN-0065 | A seeded forbidden import fails the arch gate | fast | kernel/test_T_KRN_0065_to_0074.py | test_T_KRN_0065_forbidden_import_fails |
| T-KRN-0066 | A seeded display name in kernel fails the arch gate | fast | kernel/test_T_KRN_0065_to_0074.py | test_T_KRN_0066_display_name_fails |
| T-KRN-0067 | An actor outside the closed kinds is rejected | fast | kernel/test_T_KRN_0065_to_0074.py | test_T_KRN_0067_actor_kinds_closed |
| T-KRN-0068 | A seeded clock call in the core fails | fast | kernel/test_T_KRN_0065_to_0074.py | test_T_KRN_0068_clock_call_fails |
| T-KRN-0069 | A modified schema without a change task fails the contract gate | fast | kernel/test_T_KRN_0065_to_0074.py | test_T_KRN_0069_modified_schema_fails |
| T-KRN-0070 | A consistent contracts.lock passes the contract gate | fast | kernel/test_T_KRN_0065_to_0074.py | test_T_KRN_0070_consistent_lock_passes |
| T-KRN-0071 | contracts.lock regenerates identically | fast | kernel/test_T_KRN_0065_to_0074.py | test_T_KRN_0071_contracts_lock_regen_identical |
| T-KRN-0072 | All hashes in contracts.lock match actual files | fast | kernel/test_T_KRN_0065_to_0074.py | test_T_KRN_0072_contract_gate_real_repo |
| T-KRN-0073 | gate run arch contract property generated-files exits 0 | fast | kernel/test_T_KRN_0065_to_0074.py | test_T_KRN_0073_gate_run_all_four |
| T-KRN-0074 | Display names not in schemas or kernel source | fast | kernel/test_T_KRN_0065_to_0074.py | test_T_KRN_0074_no_display_names_in_schemas |
| T-L01-0001 | Scenario 01 | fast | l01/test_reports.py | test_T_L01_0001_scenario_01 |
| T-L01-0002 | Scenario 02 | fast | l01/test_reports.py | test_T_L01_0002_scenario_02 |
| T-L01-0003 | Scenario 03 | fast | l01/test_reports.py | test_T_L01_0003_scenario_03 |
| T-L01-0004 | Scenario 04 | fast | l01/test_reports.py | test_T_L01_0004_scenario_04 |
| T-L01-0005 | Scenario 05 | fast | l01/test_reports.py | test_T_L01_0005_scenario_05 |
| T-L01-0006 | Scenario 06 | fast | l01/test_reports.py | test_T_L01_0006_scenario_06 |
| T-L01-0007 | Scenario 07 | fast | l01/test_reports.py | test_T_L01_0007_scenario_07 |
| T-L01-0008 | Scenario 08 | fast | l01/test_reports.py | test_T_L01_0008_scenario_08 |
| T-L01-0009 | Scenario 09 | fast | l01/test_reports.py | test_T_L01_0009_scenario_09 |
| T-L01-0010 | Scenario 10 | fast | l01/test_reports.py | test_T_L01_0010_scenario_10 |
| T-L01-0011 | Scenario 11 | fast | l01/test_reports.py | test_T_L01_0011_scenario_11 |
| T-L01-0012 | Scenario 12 | fast | l01/test_reports.py | test_T_L01_0012_scenario_12 |
| T-L01-0013 | Scenario 13 | fast | l01/test_reports.py | test_T_L01_0013_scenario_13 |
| T-L01-0014 | Scenario 14 | fast | l01/test_reports.py | test_T_L01_0014_scenario_14 |
| T-L01-0015 | Scenario 15 | fast | l01/test_reports.py | test_T_L01_0015_scenario_15 |
| T-L01-0016 | Scenario 16 | fast | l01/test_reports.py | test_T_L01_0016_scenario_16 |
| T-L01-0017 | Scenario 17 | fast | l01/test_reports.py | test_T_L01_0017_scenario_17 |
| T-L01-0018 | Scenario 18 | fast | l01/test_reports.py | test_T_L01_0018_scenario_18 |
| T-L01-0101 | Match | fast | l01/test_reports.py | test_T_L01_0101_match |
| T-L01-0102 | Below basis | fast | l01/test_reports.py | test_T_L01_0102_below_basis |
| T-L01-0103 | Tax excluded | fast | l01/test_reports.py | test_T_L01_0103_tax_excluded |
| T-L01-0104 | Matched for f07 | fast | l01/test_reports.py | test_T_L01_0104_matched_for_f07 |
| T-L01-0105 | Duplicate | fast | l01/test_reports.py | test_T_L01_0105_duplicate |
| T-L01-0106 | Rate above basis | fast | l01/test_reports.py | test_T_L01_0106_rate_above_basis |
| T-L01-0107 | Quantity mismatch | fast | l01/test_reports.py | test_T_L01_0107_quantity_mismatch |
| T-L01-0108 | Arithmetic | fast | l01/test_reports.py | test_T_L01_0108_arithmetic |
| T-L01-0109 | Surcharge validity | fast | l01/test_reports.py | test_T_L01_0109_surcharge_validity |
| T-L01-0110 | Header total | fast | l01/test_reports.py | test_T_L01_0110_header_total |
| T-L01-0111 | Currency mismatch | fast | l01/test_reports.py | test_T_L01_0111_currency_mismatch |
| T-L01-0112 | Possible duplicate | fast | l01/test_reports.py | test_T_L01_0112_possible_duplicate |
| T-L01-0113 | Unquoted | fast | l01/test_reports.py | test_T_L01_0113_unquoted |
| T-L01-0114 | Ambiguous basis | fast | l01/test_reports.py | test_T_L01_0114_ambiguous_basis |
| T-L01-0115 | Freight terms | fast | l01/test_reports.py | test_T_L01_0115_freight_terms |
| T-L01-0116 | Invoice unverified | fast | l01/test_reports.py | test_T_L01_0116_invoice_unverified |
| T-L01-0117 | Taxonomy absent | fast | l01/test_reports.py | test_T_L01_0117_taxonomy_absent |
| T-L01-0118 | Basis pack absent | fast | l01/test_reports.py | test_T_L01_0118_basis_pack_absent |
| T-L01-0119 | Currency unsupported | fast | l01/test_reports.py | test_T_L01_0119_currency_unsupported |
| T-L01-0120 | Label insufficient | fast | l01/test_reports.py | test_T_L01_0120_label_insufficient |
| T-L01-0201 | Corrected invoice allows | fast | l01/test_invoice.py | test_T_L01_0201_corrected_invoice_allows |
| T-L01-0202 | Decimal matches fraction | fast | l01/test_invoice.py | test_T_L01_0202_decimal_matches_fraction |
| T-L01-0203 | Widening band preserves flags | fast | l01/test_invoice.py | test_T_L01_0203_widening_band_preserves_flags |
| T-L01-0204 | Adding duplicate preserves severity | fast | l01/test_invoice.py | test_T_L01_0204_adding_duplicate_preserves_severity |
| T-L01-0205 | Line permutation preserves output | fast | l01/test_invoice.py | test_T_L01_0205_line_permutation_preserves_output |
| T-L01-0206 | Unit conversion preserves outcome | fast | l01/test_invoice.py | test_T_L01_0206_unit_conversion_preserves_outcome |
| T-L01-0207 | Arabic synonym preserves outcome | fast | l01/test_invoice.py | test_T_L01_0207_arabic_synonym_preserves_outcome |
| T-L01-0208 | Exact duplicate | fast | l01/test_invoice.py | test_T_L01_0208_exact_duplicate |
| T-L01-0209 | Near duplicate | fast | l01/test_invoice.py | test_T_L01_0209_near_duplicate |
| T-L01-0210 | Zero band | fast | l01/test_invoice.py | test_T_L01_0210_zero_band |
| T-L01-0211 | Unknown charge | fast | l01/test_invoice.py | test_T_L01_0211_unknown_charge |
| T-L01-0212 | Confusable charge | fast | l01/test_invoice.py | test_T_L01_0212_confusable_charge |
| T-L01-0213 | Ambiguous quote | fast | l01/test_invoice.py | test_T_L01_0213_ambiguous_quote |
| T-L01-0214 | Agreeing quotes | fast | l01/test_invoice.py | test_T_L01_0214_agreeing_quotes |
| T-L01-0215 | Accepted quote wins | fast | l01/test_invoice.py | test_T_L01_0215_accepted_quote_wins |
| T-L01-0216 | Contract fallback | fast | l01/test_invoice.py | test_T_L01_0216_contract_fallback |
| T-L01-0217 | Tariff fallback | fast | l01/test_invoice.py | test_T_L01_0217_tariff_fallback |
| T-L01-0218 | Invalid surcharge | fast | l01/test_invoice.py | test_T_L01_0218_invalid_surcharge |
| T-L01-0219 | Validity start | fast | l01/test_invoice.py | test_T_L01_0219_validity_start |
| T-L01-0220 | Validity end | fast | l01/test_invoice.py | test_T_L01_0220_validity_end |
| T-L01-0221 | Currency mismatch | fast | l01/test_invoice.py | test_T_L01_0221_currency_mismatch |
| T-L01-0222 | Anchor quantity | fast | l01/test_invoice.py | test_T_L01_0222_anchor_quantity |
| T-L01-0223 | Above rate | fast | l01/test_invoice.py | test_T_L01_0223_above_rate |
| T-L01-0224 | Arithmetic mismatch | fast | l01/test_invoice.py | test_T_L01_0224_arithmetic_mismatch |
| T-L01-0225 | Freight terms conflict | fast | l01/test_invoice.py | test_T_L01_0225_freight_terms_conflict |
| T-L01-0226 | Under basis | fast | l01/test_invoice.py | test_T_L01_0226_under_basis |
| T-L01-0227 | Exact basis | fast | l01/test_invoice.py | test_T_L01_0227_exact_basis |
| T-L01-0228 | Header sum includes tax | fast | l01/test_invoice.py | test_T_L01_0228_header_sum_includes_tax |
| T-L01-0229 | Header exposes minor unit | fast | l01/test_invoice.py | test_T_L01_0229_header_exposes_minor_unit |
| T-L01-0230 | Subminor difference | fast | l01/test_invoice.py | test_T_L01_0230_subminor_difference |
| T-L01-0231 | Independent issuers | fast | l01/test_invoice.py | test_T_L01_0231_independent_issuers |
| T-L01-0232 | Previous in window | fast | l01/test_invoice.py | test_T_L01_0232_previous_in_window |
| T-L01-0233 | Previous outside window | fast | l01/test_invoice.py | test_T_L01_0233_previous_outside_window |
| T-L01-0234 | Other shipment basis | fast | l01/test_invoice.py | test_T_L01_0234_other_shipment_basis |
| T-L01-0235 | Rounded line trace | fast | l01/test_invoice.py | test_T_L01_0235_rounded_line_trace |
| T-L01-0301 | Cyrillic lookalike | fast | l01/test_reports.py | test_T_L01_0301_cyrillic_lookalike |
| T-L01-0302 | Greek lookalike | fast | l01/test_reports.py | test_T_L01_0302_greek_lookalike |
| T-L01-0303 | Negative amount | fast | l01/test_reports.py | test_T_L01_0303_negative_amount |
| T-L01-0304 | Negative rate | fast | l01/test_reports.py | test_T_L01_0304_negative_rate |
| T-L01-0305 | Negative quantity | fast | l01/test_reports.py | test_T_L01_0305_negative_quantity |
| T-L01-0306 | Invalid decimal | fast | l01/test_reports.py | test_T_L01_0306_invalid_decimal |
| T-L01-0307 | Nan amount | fast | l01/test_reports.py | test_T_L01_0307_nan_amount |
| T-L01-0308 | Infinite rate | fast | l01/test_reports.py | test_T_L01_0308_infinite_rate |
| T-L01-0309 | Oversized quantity | fast | l01/test_reports.py | test_T_L01_0309_oversized_quantity |
| T-L01-0310 | Malformed currency | fast | l01/test_reports.py | test_T_L01_0310_malformed_currency |
| T-L01-0311 | Empty citation | fast | l01/test_reports.py | test_T_L01_0311_empty_citation |
| T-L01-0312 | Empty shipment | fast | l01/test_reports.py | test_T_L01_0312_empty_shipment |
| T-L01-0313 | Required quantity | fast | l01/test_reports.py | test_T_L01_0313_required_quantity |
| T-L01-0314 | Invalid service date | fast | l01/test_reports.py | test_T_L01_0314_invalid_service_date |
| T-L01-0315 | Overlapping validity | fast | l01/test_reports.py | test_T_L01_0315_overlapping_validity |
| T-L01-0316 | Split duplicate | fast | l01/test_reports.py | test_T_L01_0316_split_duplicate |
| T-L01-0317 | Split band disabled | fast | l01/test_reports.py | test_T_L01_0317_split_band_disabled |
| T-L01-0318 | Header minor unit | fast | l01/test_reports.py | test_T_L01_0318_header_minor_unit |
| T-L01-0319 | Stale surcharge | fast | l01/test_reports.py | test_T_L01_0319_stale_surcharge |
| T-L01-0320 | Secondary tariff | fast | l01/test_reports.py | test_T_L01_0320_secondary_tariff |
| T-L01-0321 | Adversarial note | fast | l01/test_reports.py | test_T_L01_0321_adversarial_note |
| T-L01-0322 | Invoice row not object | fast | l01/test_reports.py | test_T_L01_0322_invoice_row_not_object |
| T-L01-0323 | Taxonomy row not object | fast | l01/test_reports.py | test_T_L01_0323_taxonomy_row_not_object |
| T-L01-0324 | Basis row not object | fast | l01/test_reports.py | test_T_L01_0324_basis_row_not_object |
| T-L01-0325 | Tax claim as text | fast | l01/test_reports.py | test_T_L01_0325_tax_claim_as_text |
| T-L01-0401 | Replay scenario 01 | fast | l01/test_reports.py | test_T_L01_0401_replay_scenario_01 |
| T-L01-0402 | Replay scenario 02 | fast | l01/test_reports.py | test_T_L01_0402_replay_scenario_02 |
| T-L01-0403 | Replay scenario 03 | fast | l01/test_reports.py | test_T_L01_0403_replay_scenario_03 |
| T-L01-0404 | Replay scenario 04 | fast | l01/test_reports.py | test_T_L01_0404_replay_scenario_04 |
| T-L01-0405 | Replay scenario 05 | fast | l01/test_reports.py | test_T_L01_0405_replay_scenario_05 |
| T-L01-0406 | Replay scenario 06 | fast | l01/test_reports.py | test_T_L01_0406_replay_scenario_06 |
| T-L01-0407 | Replay scenario 07 | fast | l01/test_reports.py | test_T_L01_0407_replay_scenario_07 |
| T-L01-0408 | Replay scenario 08 | fast | l01/test_reports.py | test_T_L01_0408_replay_scenario_08 |
| T-L01-0409 | Replay scenario 09 | fast | l01/test_reports.py | test_T_L01_0409_replay_scenario_09 |
| T-L01-0410 | Replay scenario 10 | fast | l01/test_reports.py | test_T_L01_0410_replay_scenario_10 |
| T-L01-0501 | Anchor | fast | l01/test_reports.py | test_T_L01_0501_anchor |
| T-L01-0502 | Basis visible | fast | l01/test_reports.py | test_T_L01_0502_basis_visible |
| T-L01-0503 | Billed column | fast | l01/test_reports.py | test_T_L01_0503_billed_column |
| T-L01-0504 | Expected column | fast | l01/test_reports.py | test_T_L01_0504_expected_column |
| T-L01-0505 | Trace expansion | fast | l01/test_reports.py | test_T_L01_0505_trace_expansion |
| T-L01-0506 | Line citation | fast | l01/test_reports.py | test_T_L01_0506_line_citation |
| T-L01-0507 | Header details | fast | l01/test_reports.py | test_T_L01_0507_header_details |
| T-L01-0508 | Time based match | fast | l01/test_reports.py | test_T_L01_0508_time_based_match |
| T-L01-0509 | Currency totals | fast | l01/test_reports.py | test_T_L01_0509_currency_totals |
| T-L01-0510 | Unblock requirements | fast | l01/test_reports.py | test_T_L01_0510_unblock_requirements |
| T-L01-0511 | No dispute draft | fast | l01/test_reports.py | test_T_L01_0511_no_dispute_draft |
| T-L01-0512 | No withhold advice | fast | l01/test_reports.py | test_T_L01_0512_no_withhold_advice |
| T-L02-0001 | Scenario 01 | fast | l02/test_reports.py | test_T_L02_0001_scenario_01 |
| T-L02-0002 | Scenario 02 | fast | l02/test_reports.py | test_T_L02_0002_scenario_02 |
| T-L02-0003 | Scenario 03 | fast | l02/test_reports.py | test_T_L02_0003_scenario_03 |
| T-L02-0004 | Scenario 04 | fast | l02/test_reports.py | test_T_L02_0004_scenario_04 |
| T-L02-0005 | Scenario 05 | fast | l02/test_reports.py | test_T_L02_0005_scenario_05 |
| T-L02-0006 | Scenario 06 | fast | l02/test_reports.py | test_T_L02_0006_scenario_06 |
| T-L02-0007 | Scenario 07 | fast | l02/test_reports.py | test_T_L02_0007_scenario_07 |
| T-L02-0008 | Scenario 08 | fast | l02/test_reports.py | test_T_L02_0008_scenario_08 |
| T-L02-0009 | Scenario 09 | fast | l02/test_reports.py | test_T_L02_0009_scenario_09 |
| T-L02-0010 | Scenario 10 | fast | l02/test_reports.py | test_T_L02_0010_scenario_10 |
| T-L02-0011 | Scenario 11 | fast | l02/test_reports.py | test_T_L02_0011_scenario_11 |
| T-L02-0012 | Scenario 12 | fast | l02/test_reports.py | test_T_L02_0012_scenario_12 |
| T-L02-0013 | Scenario 13 | fast | l02/test_reports.py | test_T_L02_0013_scenario_13 |
| T-L02-0014 | Scenario 14 | fast | l02/test_reports.py | test_T_L02_0014_scenario_14 |
| T-L02-0015 | Scenario 15 | fast | l02/test_reports.py | test_T_L02_0015_scenario_15 |
| T-L02-0016 | Scenario 16 | fast | l02/test_reports.py | test_T_L02_0016_scenario_16 |
| T-L02-0017 | Scenario 17 | fast | l02/test_reports.py | test_T_L02_0017_scenario_17 |
| T-L02-0101 | Provided | fast | l02/test_reports.py | test_T_L02_0101_provided |
| T-L02-0102 | Indicative | fast | l02/test_reports.py | test_T_L02_0102_indicative |
| T-L02-0103 | Incomplete | fast | l02/test_reports.py | test_T_L02_0103_incomplete |
| T-L02-0104 | Variance | fast | l02/test_reports.py | test_T_L02_0104_variance |
| T-L02-0105 | Rate conflict | fast | l02/test_reports.py | test_T_L02_0105_rate_conflict |
| T-L02-0106 | Missing upstream | fast | l02/test_reports.py | test_T_L02_0106_missing_upstream |
| T-L02-0107 | Valuation rule | fast | l02/test_reports.py | test_T_L02_0107_valuation_rule |
| T-L02-0108 | Missing duty pack | fast | l02/test_reports.py | test_T_L02_0108_missing_duty_pack |
| T-L02-0109 | Declared code absent | fast | l02/test_reports.py | test_T_L02_0109_declared_code_absent |
| T-L02-0110 | Missing fx | fast | l02/test_reports.py | test_T_L02_0110_missing_fx |
| T-L02-0111 | Missing currency | fast | l02/test_reports.py | test_T_L02_0111_missing_currency |
| T-L02-0201 | Ad valorem duty scales with goods value | fast | l02/test_cost.py | test_T_L02_0201_ad_valorem_scales |
| T-L02-0202 | Duty and tax match a rational oracle | fast | l02/test_cost.py | test_T_L02_0202_fraction_oracle |
| T-L02-0203 | K05 and L02 produce an identical basis | fast | l02/test_cost.py | test_T_L02_0203_parallel_k05_and_l02_basis |
| T-L02-0204 | Specific weight conversion | fast | l02/test_cost.py | test_T_L02_0204_specific_weight_conversion |
| T-L02-0205 | Ad valorem exact | fast | l02/test_cost.py | test_T_L02_0205_ad_valorem_exact |
| T-L02-0206 | Specific exact | fast | l02/test_cost.py | test_T_L02_0206_specific_exact |
| T-L02-0207 | Compound exact | fast | l02/test_cost.py | test_T_L02_0207_compound_exact |
| T-L02-0208 | Components sum to total | fast | l02/test_cost.py | test_T_L02_0208_components_sum_to_total |
| T-L02-0209 | Range order | fast | l02/test_cost.py | test_T_L02_0209_range_order |
| T-L02-0210 | Range origin weakens total | fast | l02/test_cost.py | test_T_L02_0210_range_origin_weakens_total |
| T-L02-0211 | Required component missing | fast | l02/test_cost.py | test_T_L02_0211_required_component_missing |
| T-L02-0212 | No implicit fx | fast | l02/test_cost.py | test_T_L02_0212_no_implicit_fx |
| T-L02-0213 | Dated fx | fast | l02/test_cost.py | test_T_L02_0213_dated_fx |
| T-L02-0214 | Unverified goods | fast | l02/test_cost.py | test_T_L02_0214_unverified_goods |
| T-L02-0215 | Unknown declared code | fast | l02/test_cost.py | test_T_L02_0215_unknown_declared_code |
| T-L02-0216 | Absent valuation rule | fast | l02/test_cost.py | test_T_L02_0216_absent_valuation_rule |
| T-L02-0217 | Unsupported goods currency | fast | l02/test_cost.py | test_T_L02_0217_unsupported_goods_currency |
| T-L02-0218 | Missing goods fx | fast | l02/test_cost.py | test_T_L02_0218_missing_goods_fx |
| T-L02-0219 | Duty start inclusive | fast | l02/test_cost.py | test_T_L02_0219_duty_start_inclusive |
| T-L02-0220 | Duty end exclusive | fast | l02/test_cost.py | test_T_L02_0220_duty_end_exclusive |
| T-L02-0221 | Tax start inclusive | fast | l02/test_cost.py | test_T_L02_0221_tax_start_inclusive |
| T-L02-0222 | Tax end exclusive | fast | l02/test_cost.py | test_T_L02_0222_tax_end_exclusive |
| T-L02-0223 | Tax base value only | fast | l02/test_cost.py | test_T_L02_0223_tax_base_value_only |
| T-L02-0224 | Tax base dependency | fast | l02/test_cost.py | test_T_L02_0224_tax_base_dependency |
| T-L02-0225 | No units without verification | fast | l02/test_cost.py | test_T_L02_0225_no_units_without_verification |
| T-L02-0226 | No specific without units | fast | l02/test_cost.py | test_T_L02_0226_no_specific_without_units |
| T-L02-0227 | Unit cost per piece | fast | l02/test_cost.py | test_T_L02_0227_unit_cost_per_piece |
| T-L02-0228 | Unit cost per kg | fast | l02/test_cost.py | test_T_L02_0228_unit_cost_per_kg |
| T-L02-0229 | Unit cost per line | fast | l02/test_cost.py | test_T_L02_0229_unit_cost_per_line |
| T-L02-0230 | Verified preference | fast | l02/test_cost.py | test_T_L02_0230_verified_preference |
| T-L02-0231 | Unverified preference | fast | l02/test_cost.py | test_T_L02_0231_unverified_preference |
| T-L02-0232 | Withdrawn preference | fast | l02/test_cost.py | test_T_L02_0232_withdrawn_preference |
| T-L02-0233 | Weak preference | fast | l02/test_cost.py | test_T_L02_0233_weak_preference |
| T-L02-0234 | Adjusted basis | fast | l02/test_cost.py | test_T_L02_0234_adjusted_basis |
| T-L02-0235 | Zero goods value | fast | l02/test_cost.py | test_T_L02_0235_zero_goods_value |
| T-L02-0301 | Zero value | fast | l02/test_reports.py | test_T_L02_0301_zero_value |
| T-L02-0302 | Negative value | fast | l02/test_reports.py | test_T_L02_0302_negative_value |
| T-L02-0303 | Negative quantity | fast | l02/test_reports.py | test_T_L02_0303_negative_quantity |
| T-L02-0304 | Negative weight | fast | l02/test_reports.py | test_T_L02_0304_negative_weight |
| T-L02-0305 | Huge quantity | fast | l02/test_reports.py | test_T_L02_0305_huge_quantity |
| T-L02-0306 | Huge weight | fast | l02/test_reports.py | test_T_L02_0306_huge_weight |
| T-L02-0307 | Nonfinite amount | fast | l02/test_reports.py | test_T_L02_0307_nonfinite_amount |
| T-L02-0308 | Nonfinite quantity | fast | l02/test_reports.py | test_T_L02_0308_nonfinite_quantity |
| T-L02-0309 | Wrong decimal | fast | l02/test_reports.py | test_T_L02_0309_wrong_decimal |
| T-L02-0310 | Bad goods date | fast | l02/test_reports.py | test_T_L02_0310_bad_goods_date |
| T-L02-0311 | Overlapping rates | fast | l02/test_reports.py | test_T_L02_0311_overlapping_rates |
| T-L02-0312 | Missing currency exponent | fast | l02/test_reports.py | test_T_L02_0312_missing_currency_exponent |
| T-L02-0313 | Missing fx not zero | fast | l02/test_reports.py | test_T_L02_0313_missing_fx_not_zero |
| T-L02-0314 | Free text exemption | fast | l02/test_reports.py | test_T_L02_0314_free_text_exemption |
| T-L02-0315 | Alternative code ignored | fast | l02/test_reports.py | test_T_L02_0315_alternative_code_ignored |
| T-L02-0316 | Preference unverified | fast | l02/test_reports.py | test_T_L02_0316_preference_unverified |
| T-L02-0317 | Invalid components | fast | l02/test_reports.py | test_T_L02_0317_invalid_components |
| T-L02-0318 | Invalid rate pack | fast | l02/test_reports.py | test_T_L02_0318_invalid_rate_pack |
| T-L02-0319 | Unsafe plan component | fast | l02/test_reports.py | test_T_L02_0319_unsafe_plan_component |
| T-L02-0320 | No partial total | fast | l02/test_reports.py | test_T_L02_0320_no_partial_total |
| T-L02-0401 | Replay scenario 01 | fast | l02/test_reports.py | test_T_L02_0401_replay_scenario_01 |
| T-L02-0402 | Replay scenario 02 | fast | l02/test_reports.py | test_T_L02_0402_replay_scenario_02 |
| T-L02-0403 | Replay scenario 03 | fast | l02/test_reports.py | test_T_L02_0403_replay_scenario_03 |
| T-L02-0404 | Replay scenario 04 | fast | l02/test_reports.py | test_T_L02_0404_replay_scenario_04 |
| T-L02-0405 | Replay scenario 05 | fast | l02/test_reports.py | test_T_L02_0405_replay_scenario_05 |
| T-L02-0406 | Replay scenario 06 | fast | l02/test_reports.py | test_T_L02_0406_replay_scenario_06 |
| T-L02-0407 | Replay scenario 07 | fast | l02/test_reports.py | test_T_L02_0407_replay_scenario_07 |
| T-L02-0408 | Replay scenario 08 | fast | l02/test_reports.py | test_T_L02_0408_replay_scenario_08 |
| T-L02-0409 | Replay scenario 09 | fast | l02/test_reports.py | test_T_L02_0409_replay_scenario_09 |
| T-L02-0410 | Replay scenario 10 | fast | l02/test_reports.py | test_T_L02_0410_replay_scenario_10 |
| T-L02-0501 | Anchor | fast | l02/test_reports.py | test_T_L02_0501_anchor |
| T-L02-0502 | Component origins | fast | l02/test_reports.py | test_T_L02_0502_component_origins |
| T-L02-0503 | Trace details | fast | l02/test_reports.py | test_T_L02_0503_trace_details |
| T-L02-0504 | Range visible | fast | l02/test_reports.py | test_T_L02_0504_range_visible |
| T-L02-0505 | Missing components visible | fast | l02/test_reports.py | test_T_L02_0505_missing_components_visible |
| T-L02-0506 | No incomplete total | fast | l02/test_reports.py | test_T_L02_0506_no_incomplete_total |
| T-L02-0507 | Simulation record only | fast | l02/test_reports.py | test_T_L02_0507_simulation_record_only |
| T-L02-0508 | Proposal replaces transport | fast | l02/test_reports.py | test_T_L02_0508_proposal_replaces_transport |
| T-L02-0509 | Observed eight percent | fast | l02/test_reports.py | test_T_L02_0509_observed_eight_percent |
| T-L02-0510 | Unestimated visible | fast | l02/test_reports.py | test_T_L02_0510_unestimated_visible |
| T-L02-0511 | No declaration advice | fast | l02/test_reports.py | test_T_L02_0511_no_declaration_advice |
| T-L02-0512 | No variance without audit | fast | l02/test_reports.py | test_T_L02_0512_no_variance_without_audit |
| T-LED-0001 | Sequence starts at 1 and increments by 1 | fast | ledger/test_T_LED_0001_to_0012.py | test_T_LED_0001_sequence_starts_at_1 |
| T-LED-0002 | No gaps under concurrent appends | fast | ledger/test_T_LED_0001_to_0012.py | test_T_LED_0002_no_gaps_concurrent |
| T-LED-0003 | Every field change alters the record hash | fast | ledger/test_T_LED_0001_to_0012.py | test_T_LED_0003_field_change_alters_hash |
| T-LED-0004 | Cross-purpose hash replay fails | fast | ledger/test_T_LED_0001_to_0012.py | test_T_LED_0004_cross_purpose_hash_replay_fails |
| T-LED-0005 | Update is rejected by the database | slow | ledger/test_T_LED_0001_to_0012.py | test_T_LED_0005_update_rejected |
| T-LED-0006 | Delete is rejected by the database | slow | ledger/test_T_LED_0001_to_0012.py | test_T_LED_0006_delete_rejected |
| T-LED-0007 | A record of one tenant is invisible to another | slow | ledger/test_T_LED_0001_to_0012.py | test_T_LED_0007_tenant_isolation |
| T-LED-0008 | Salted payload hash includes salt_id and salt | fast | ledger/test_T_LED_0001_to_0012.py | test_T_LED_0008_salted_payload_hash |
| T-LED-0009 | With salt destroyed, low-entropy payload cannot be confirmed | fast | ledger/test_T_LED_0001_to_0012.py | test_T_LED_0009_salt_destroyed_unconfirmable |
| T-LED-0010 | Algorithm identifier on every stored hash | fast | ledger/test_T_LED_0001_to_0012.py | test_T_LED_0010_algorithm_identifier |
| T-LED-0011 | Payloads stored by reference | fast | ledger/test_T_LED_0001_to_0012.py | test_T_LED_0011_payload_by_reference |
| T-LED-0012 | First record prev_hash is all zeros | fast | ledger/test_T_LED_0001_to_0012.py | test_T_LED_0012_first_record_prev_hash_zero |
| T-LED-0013 | Each deployment event type appends once | fast | ledger/test_T_LED_0013_to_0020.py | test_T_LED_0013_deployment_events_append |
| T-LED-0014 | Each tenant system event type appends once | fast | ledger/test_T_LED_0013_to_0020.py | test_T_LED_0014_tenant_events_append |
| T-LED-0015 | Invalid event type is rejected | fast | ledger/test_T_LED_0013_to_0020.py | test_T_LED_0015_invalid_event_rejected |
| T-LED-0016 | System chain verifies independently of any case chain | fast | ledger/test_T_LED_0013_to_0020.py | test_T_LED_0016_system_chain_independent |
| T-LED-0017 | Deployment chain is separate from tenant system chain | fast | ledger/test_T_LED_0013_to_0020.py | test_T_LED_0017_deployment_separate_from_tenant |
| T-LED-0018 | Tenant system chain position is independent of other tenants | fast | ledger/test_T_LED_0013_to_0020.py | test_T_LED_0018_tenant_isolation |
| T-LED-0019 | Deployment attestation holds digest, not position | fast | ledger/test_T_LED_0013_to_0020.py | test_T_LED_0019_deployment_attestation_content |
| T-LED-0020 | Case record carries tenant system position | fast | ledger/test_T_LED_0013_to_0020.py | test_T_LED_0020_case_record_carries_tenant_position |
| T-LED-0021 | Leaf hash known-answer vector | fast | ledger/test_T_LED_0021_to_0036.py | test_T_LED_0021_leaf_hash_known_answer |
| T-LED-0022 | Node hash known-answer vector | fast | ledger/test_T_LED_0021_to_0036.py | test_T_LED_0022_node_hash_known_answer |
| T-LED-0023 | Root of a single-leaf tree is the leaf itself | fast | ledger/test_T_LED_0021_to_0036.py | test_T_LED_0023_root_single_leaf |
| T-LED-0024 | Root of a two-leaf tree is node_hash of the two leaves | fast | ledger/test_T_LED_0021_to_0036.py | test_T_LED_0024_root_two_leaves |
| T-LED-0025 | Root of an empty tree is all zeros | fast | ledger/test_T_LED_0021_to_0036.py | test_T_LED_0025_root_empty_tree |
| T-LED-0026 | Inclusion proof verifies for a valid leaf | fast | ledger/test_T_LED_0021_to_0036.py | test_T_LED_0026_inclusion_proof_valid |
| T-LED-0027 | Inclusion proof fails for a wrong index | fast | ledger/test_T_LED_0021_to_0036.py | test_T_LED_0027_inclusion_proof_wrong_index |
| T-LED-0028 | Inclusion proof fails for a tampered root | fast | ledger/test_T_LED_0021_to_0036.py | test_T_LED_0028_inclusion_proof_tampered_root |
| T-LED-0029 | Consistency proof verifies for a valid extension | fast | ledger/test_T_LED_0021_to_0036.py | test_T_LED_0029_consistency_proof_valid |
| T-LED-0030 | Consistency proof fails for a tampered previous root | fast | ledger/test_T_LED_0021_to_0036.py | test_T_LED_0030_consistency_proof_tampered_prev_root |
| T-LED-0031 | A changed byte in a record is detected by the tree root | fast | ledger/test_T_LED_0021_to_0036.py | test_T_LED_0031_tampered_record_detected |
| T-LED-0032 | A changed byte in a checkpoint signature is detected | fast | ledger/test_T_LED_0021_to_0036.py | test_T_LED_0032_tampered_checkpoint_signature_detected |
| T-LED-0033 | Cross-purpose hash replay fails | fast | ledger/test_T_LED_0021_to_0036.py | test_T_LED_0033_cross_purpose_replay_fails |
| T-LED-0034 | Inclusion proof verifies for random trees | fast | ledger/test_T_LED_0021_to_0036.py | test_T_LED_0034_inclusion_property_random_trees |
| T-LED-0035 | Consistency proof verifies for random tree extensions | fast | ledger/test_T_LED_0021_to_0036.py | test_T_LED_0035_consistency_property_random_trees |
| T-LED-0036 | A checkpoint without a valid co-signature is SELF-ATTESTED | fast | ledger/test_T_LED_0021_to_0036.py | test_T_LED_0036_checkpoint_without_cosign_self_attested |
| T-LED-0037 | Equal inputs give equal evaluation commitments | fast | ledger/test_T_LED_0037_to_0046.py | test_T_LED_0037_eval_commitment_equal_inputs |
| T-LED-0038 | Any input change gives a different evaluation commitment | fast | ledger/test_T_LED_0037_to_0046.py | test_T_LED_0038_eval_commitment_input_change |
| T-LED-0039 | Proposal commitment is deterministic | fast | ledger/test_T_LED_0037_to_0046.py | test_T_LED_0039_proposal_commitment_deterministic |
| T-LED-0040 | Proposal commitment changes on proposal change | fast | ledger/test_T_LED_0037_to_0046.py | test_T_LED_0040_proposal_commitment_changes |
| T-LED-0041 | Field commitment with revealed value and salt verifies | fast | ledger/test_T_LED_0037_to_0046.py | test_T_LED_0041_field_commitment_verifies |
| T-LED-0042 | Field commitment with wrong value fails | fast | ledger/test_T_LED_0037_to_0046.py | test_T_LED_0042_field_commitment_wrong_value |
| T-LED-0043 | Field commitment with wrong salt fails | fast | ledger/test_T_LED_0037_to_0046.py | test_T_LED_0043_field_commitment_wrong_salt |
| T-LED-0044 | With salt destroyed, value cannot be confirmed | fast | ledger/test_T_LED_0037_to_0046.py | test_T_LED_0044_salt_destroyed_prevents_confirmation |
| T-LED-0045 | Different salts produce different field commitments | fast | ledger/test_T_LED_0037_to_0046.py | test_T_LED_0045_different_salts_different_commitments |
| T-LED-0046 | Cross-purpose hash reuse fails | fast | ledger/test_T_LED_0037_to_0046.py | test_T_LED_0046_cross_purpose_reuse_fails |
| T-LED-0047 | Structural verification passes on a clean chain | fast | ledger/test_T_LED_0047_to_0058.py | test_T_LED_0047_structural_passes |
| T-LED-0048 | Full verification passes with payloads | fast | ledger/test_T_LED_0047_to_0058.py | test_T_LED_0048_full_passes |
| T-LED-0049 | A tampered record is detected by structural verification | fast | ledger/test_T_LED_0047_to_0058.py | test_T_LED_0049_tampered_record_detected |
| T-LED-0050 | A broken prev_hash link is detected | fast | ledger/test_T_LED_0047_to_0058.py | test_T_LED_0050_chain_broken_prev_hash |
| T-LED-0051 | An erased payload is reported as ERASED, not as a failure | fast | ledger/test_T_LED_0047_to_0058.py | test_T_LED_0051_erased_not_failure |
| T-LED-0052 | The verification level is exactly one of the four levels | fast | ledger/test_T_LED_0047_to_0058.py | test_T_LED_0052_verification_level_exactly_one |
| T-LED-0053 | The bare word "verified" is never printed | fast | ledger/test_T_LED_0047_to_0058.py | test_T_LED_0053_no_bare_verified |
| T-LED-0054 | An empty chain verifies structurally | fast | ledger/test_T_LED_0047_to_0058.py | test_T_LED_0054_empty_chain_verifies |
| T-LED-0055 | Replay reproduces results from recorded inputs | fast | ledger/test_T_LED_0047_to_0058.py | test_T_LED_0055_replay_equality |
| T-LED-0056 | Replay detects a payload mismatch | fast | ledger/test_T_LED_0047_to_0058.py | test_T_LED_0056_replay_mismatch |
| T-LED-0057 | Replay needs no network | fast | ledger/test_T_LED_0047_to_0058.py | test_T_LED_0057_replay_no_network |
| T-LED-0058 | Replay with missing evaluation time fails | fast | ledger/test_T_LED_0047_to_0058.py | test_T_LED_0058_replay_missing_eval_time |
| T-LED-0059 | Export and import round-trip gives equal hashes | fast | ledger/test_T_LED_0059_to_0086.py | test_T_LED_0059_bundle_round_trip |
| T-LED-0060 | A bundle with one altered record fails verification | fast | ledger/test_T_LED_0059_to_0086.py | test_T_LED_0060_altered_bundle_fails |
| T-LED-0061 | Two exports of the same case are byte-identical | fast | ledger/test_T_LED_0059_to_0086.py | test_T_LED_0061_byte_identical_exports |
| T-LED-0062 | Bundle manifest contains correct record count | fast | ledger/test_T_LED_0059_to_0086.py | test_T_LED_0062_manifest_record_count |
| T-LED-0063 | Bundle manifest contains correct root hash | fast | ledger/test_T_LED_0059_to_0086.py | test_T_LED_0063_manifest_root_hash |
| T-LED-0064 | Bundle verifies offline with no database or network | fast | ledger/test_T_LED_0059_to_0086.py | test_T_LED_0064_bundle_verifies_offline |
| T-LED-0065 | An empty bundle verifies | fast | ledger/test_T_LED_0059_to_0086.py | test_T_LED_0065_empty_bundle_verifies |
| T-LED-0066 | A bundle with a wrong record count fails verification | fast | ledger/test_T_LED_0059_to_0086.py | test_T_LED_0066_wrong_count_fails |
| T-LED-0067 | Independent verifier agrees with kernel on valid records | fast | ledger/test_T_LED_0059_to_0086.py | test_T_LED_0067_verifier_agrees_valid |
| T-LED-0068 | Independent verifier detects a tampered record | fast | ledger/test_T_LED_0059_to_0086.py | test_T_LED_0068_verifier_detects_tamper |
| T-LED-0069 | Independent verifier computes the same leaf hash | fast | ledger/test_T_LED_0059_to_0086.py | test_T_LED_0069_verifier_leaf_hash |
| T-LED-0070 | Independent verifier computes the same node hash | fast | ledger/test_T_LED_0059_to_0086.py | test_T_LED_0070_verifier_node_hash |
| T-LED-0071 | Independent verifier computes the same Merkle root | fast | ledger/test_T_LED_0059_to_0086.py | test_T_LED_0071_verifier_root |
| T-LED-0072 | The independent verifier imports no kernel module | fast | ledger/test_T_LED_0059_to_0086.py | test_T_LED_0072_verifier_no_kernel_import |
| T-LED-0073 | Verifier agrees with kernel on random bundles including tampers | fast | ledger/test_T_LED_0059_to_0086.py | test_T_LED_0073_verifier_agrees_random_bundles |
| T-LED-0074 | gate run replay exits 0 | fast | ledger/test_T_LED_0059_to_0086.py | test_T_LED_0074_gate_run_replay |
| T-LED-0075 | Recovery after a kill at append leaves a verifiable ledger | fast | ledger/test_T_LED_0059_to_0086.py | test_T_LED_0075_crash_at_append |
| T-LED-0076 | Recovery after a kill at checkpoint write | fast | ledger/test_T_LED_0059_to_0086.py | test_T_LED_0076_crash_at_checkpoint |
| T-LED-0077 | Recovery after a kill at export | fast | ledger/test_T_LED_0059_to_0086.py | test_T_LED_0077_crash_at_export |
| T-LED-0078 | The tree root matches the independent verifier's computation | fast | ledger/test_T_LED_0059_to_0086.py | test_T_LED_0078_tree_root_matches_verifier |
| T-LED-0079 | Kill points are registered in the fault lab | fast | ledger/test_T_LED_0059_to_0086.py | test_T_LED_0079_kill_points_registered |
| T-LED-0080 | Recovery after a kill at append leaves a gap-free ledger | fast | ledger/test_T_LED_0059_to_0086.py | test_T_LED_0080_recovery_no_gap |
| T-LED-0081 | Evidence tampering threat items have tests | fast | ledger/test_T_LED_0059_to_0086.py | test_T_LED_0081_threat_evidence_tampering |
| T-LED-0082 | Ledger and proof endpoint threat items have tests | fast | ledger/test_T_LED_0059_to_0086.py | test_T_LED_0082_threat_ledger_proofs |
| T-LED-0083 | Hash replay threat items have tests | fast | ledger/test_T_LED_0059_to_0086.py | test_T_LED_0083_threat_hash_replay |
| T-LED-0084 | Signature misuse threat items have tests | fast | ledger/test_T_LED_0059_to_0086.py | test_T_LED_0084_threat_signature_misuse |
| T-LED-0085 | Verifier divergence threat items have tests | fast | ledger/test_T_LED_0059_to_0086.py | test_T_LED_0085_threat_verifier_divergence |
| T-LED-0086 | Salt loss threat items have tests | fast | ledger/test_T_LED_0059_to_0086.py | test_T_LED_0086_threat_salt_loss |
| T-LIB-0001 | Regenerate identical bytes | fast | lib/test_capgen.py | test_T_LIB_0001 |
| T-LIB-0002 | Require a conforming layout | fast | lib/test_capgen.py | test_T_LIB_0002 |
| T-LIB-0003 | Reject an incomplete layout | fast | lib/test_capgen.py | test_T_LIB_0003 |
| T-LIB-0004 | Reject unknown definition keys | fast | lib/test_capgen.py | test_T_LIB_0004 |
| T-LIB-0005 | Require declared calibration artifacts | fast | lib/test_capgen.py | test_T_LIB_0005 |
| T-LIB-0006 | Prevent accidental replacement of edited files | fast | lib/test_capgen.py | test_T_LIB_0006 |
| T-LIB-0007 | Dispatch a generated registration through the skeleton | fast | lib/test_capgen.py | test_T_LIB_0007 |
| T-LIB-0008 | Keep unregistered invocation compatible | fast | lib/test_capgen.py | test_T_LIB_0008 |
| T-LIB-0009 | Keep generated registration behind tenant authentication | fast | lib/test_capgen.py | test_T_LIB_0009 |
| T-LIB-0010 | Give generated views a stable anchor | fast | lib/test_capgen.py | test_T_LIB_0010 |
| T-LIB-0011 | Round half even | fast | lib/test_money.py | test_T_LIB_0011 |
| T-LIB-0012 | Round half up | fast | lib/test_money.py | test_T_LIB_0012 |
| T-LIB-0013 | Round half down | fast | lib/test_money.py | test_T_LIB_0013 |
| T-LIB-0014 | Round toward positive infinity | fast | lib/test_money.py | test_T_LIB_0014 |
| T-LIB-0015 | Round toward negative infinity | fast | lib/test_money.py | test_T_LIB_0015 |
| T-LIB-0016 | Round away from zero | fast | lib/test_money.py | test_T_LIB_0016 |
| T-LIB-0017 | Round toward zero | fast | lib/test_money.py | test_T_LIB_0017 |
| T-LIB-0018 | Round away from zero when the retained digit is zero or five | fast | lib/test_money.py | test_T_LIB_0018 |
| T-LIB-0019 | Add exact amounts associatively | fast | lib/test_money.py | test_T_LIB_0019 |
| T-LIB-0020 | Conserve total units across allocations | fast | lib/test_money.py | test_T_LIB_0020 |
| T-LIB-0021 | Reject mixed currencies without conversion | fast | lib/test_money.py | test_T_LIB_0021 |
| T-LIB-0022 | Retain the recorded conversion rate and weakest label | fast | lib/test_money.py | test_T_LIB_0022 |
| T-LIB-0023 | Require the rate direction to match | fast | lib/test_money.py | test_T_LIB_0023 |
| T-LIB-0024 | Reject currencies absent from the pack | fast | lib/test_money.py | test_T_LIB_0024 |
| T-LIB-0025 | Keep exact amounts until the declared rounding point | fast | lib/test_money.py | test_T_LIB_0025 |
| T-LIB-0026 | Label fallback presentation rounding as an assumption | fast | lib/test_money.py | test_T_LIB_0026 |
| T-LIB-0027 | Compare roundings against a rational oracle | fast | lib/test_money.py | test_T_LIB_0027 |
| T-LIB-0028 | Break allocation ties by key | fast | lib/test_money.py | test_T_LIB_0028 |
| T-LIB-0029 | Reject implicit rounding of working amounts | fast | lib/test_money.py | test_T_LIB_0029 |
| T-LIB-0030 | Compare at currency minor units with explicit tolerance | fast | lib/test_money.py | test_T_LIB_0030 |
| T-LIB-0031 | Replay a money sum | fast | lib/test_calctrace.py | test_T_LIB_0031 |
| T-LIB-0032 | Replay a quantity difference | fast | lib/test_calctrace.py | test_T_LIB_0032 |
| T-LIB-0033 | Replay nested arithmetic | fast | lib/test_calctrace.py | test_T_LIB_0033 |
| T-LIB-0034 | Preserve the weaker label through nesting | fast | lib/test_calctrace.py | test_T_LIB_0034 |
| T-LIB-0035 | Use context-specific quantization | fast | lib/test_calctrace.py | test_T_LIB_0035 |
| T-LIB-0036 | Reject a modified recorded output | fast | lib/test_calctrace.py | test_T_LIB_0036 |
| T-LIB-0037 | Produce stable hashes for identical trees | fast | lib/test_calctrace.py | test_T_LIB_0037 |
| T-LIB-0038 | Commit operand and rule provenance to the hash | fast | lib/test_calctrace.py | test_T_LIB_0038 |
| T-LIB-0039 | Use recorded context instead of ambient context | fast | lib/test_calctrace.py | test_T_LIB_0039 |
| T-LIB-0040 | Keep existing Decision data when adding unique trace references | fast | lib/test_calctrace.py | test_T_LIB_0040 |
| T-LIB-0041 | Reject incompatible units on addition | fast | lib/test_calctrace.py | test_T_LIB_0041 |
| T-LIB-0042 | Keep exact division and reject unrecorded rounding | fast | lib/test_calctrace.py | test_T_LIB_0042 |
| T-LIB-0043 | Map a hold code to the missing fact | fast | lib/test_unblock.py | test_T_LIB_0043 |
| T-LIB-0044 | Map abstention to missing pack evidence | fast | lib/test_unblock.py | test_T_LIB_0044 |
| T-LIB-0045 | Map escalation to unresolved verification | fast | lib/test_unblock.py | test_T_LIB_0045 |
| T-LIB-0046 | Choose the smallest shared alternative across reasons | fast | lib/test_unblock.py | test_T_LIB_0046 |
| T-LIB-0047 | Deduplicate repeated reasons and shared requirements | fast | lib/test_unblock.py | test_T_LIB_0047 |
| T-LIB-0048 | Reevaluate to allow after fixture requirements are resolved | fast | lib/test_unblock.py | test_T_LIB_0048 |
| T-LIB-0049 | Return stable output for reason order permutations | fast | lib/test_unblock.py | test_T_LIB_0049 |
| T-LIB-0050 | Serialize items in the Passport contract | fast | lib/test_unblock.py | test_T_LIB_0050 |
| T-LIB-0051 | Require a closed reason mapping | fast | lib/test_unblock.py | test_T_LIB_0051 |
| T-LIB-0052 | Remove already resolved inputs from the smallest list | fast | lib/test_unblock.py | test_T_LIB_0052 |
| T-LIB-0053 | Accept a current feed with registered provenance | fast | lib/test_feeds.py | test_T_LIB_0053 |
| T-LIB-0054 | Allow only the case tenant to see its feed | fast | lib/test_feeds.py | test_T_LIB_0054 |
| T-LIB-0055 | Reject a batch labelled official by assertion | fast | lib/test_feeds.py | test_T_LIB_0055 |
| T-LIB-0056 | Reject a stale or future feed | fast | lib/test_feeds.py | test_T_LIB_0056 |
| T-LIB-0057 | Reject at the exclusive effective period endpoint | fast | lib/test_feeds.py | test_T_LIB_0057 |
| T-LIB-0058 | Reject the whole batch if one record fails schema validation | fast | lib/test_feeds.py | test_T_LIB_0058 |
| T-LIB-0059 | Reject content that fails its recorded hash | fast | lib/test_feeds.py | test_T_LIB_0059 |
| T-LIB-0060 | Replay identical batch keys and reject replacements | fast | lib/test_feeds.py | test_T_LIB_0060 |
| T-LIB-0061 | Reject malformed envelopes and mismatched sources | fast | lib/test_feeds.py | test_T_LIB_0061 |
| T-LIB-0062 | Validate the serialized envelope against the frozen contract | fast | lib/test_feeds.py | test_T_LIB_0062 |
| T-LIB-0063 | Meet the coverage bound over seeded class-conditional trials | fast | lib/test_conformal.py | test_T_LIB_0063 |
| T-LIB-0064 | Replay Phase 09 calibration fixtures deterministically | fast | lib/test_conformal.py | test_T_LIB_0064 |
| T-LIB-0065 | Use distinct class thresholds and include boundary scores | fast | lib/test_conformal.py | test_T_LIB_0065 |
| T-LIB-0066 | State only the marginal exchangeability guarantee | fast | lib/test_conformal.py | test_T_LIB_0066 |
| T-LIB-0067 | Abstain for empty and oversized sets | fast | lib/test_conformal.py | test_T_LIB_0067 |
| T-LIB-0068 | Disable automatic use after a confirmed coverage drop | fast | lib/test_conformal.py | test_T_LIB_0068 |
| T-LIB-0069 | Record synthetic coverage without disabling automatic use | fast | lib/test_conformal.py | test_T_LIB_0069 |
| T-LIB-0070 | Flag extended not-measurable status for revalidation | fast | lib/test_conformal.py | test_T_LIB_0070 |
| T-LIB-0071 | Pass validation on confirmed outcomes meeting the configured bound | fast | lib/test_conformal.py | test_T_LIB_0071 |
| T-LIB-0072 | Fail validation on inadequate confirmed coverage | fast | lib/test_conformal.py | test_T_LIB_0072 |
| T-LIB-0073 | Fail excessive singleton error despite adequate overall coverage | fast | lib/test_conformal.py | test_T_LIB_0073 |
| T-LIB-0074 | Lapse when the pack, artifact or labelled set changes | fast | lib/test_conformal.py | test_T_LIB_0074 |
| T-LIB-0075 | Require recorded independent approval before using tenant validation | fast | lib/test_conformal.py | test_T_LIB_0075 |
| T-LIB-0076 | Lapse after the configured revalidation interval | fast | lib/test_conformal.py | test_T_LIB_0076 |
| T-LIB-0077 | Reject a seeded incorrect solver assignment | fast | lib/test_solve.py | test_T_LIB_0077 |
| T-LIB-0078 | Find and independently verify a CP-SAT optimum | fast | lib/test_solve.py | test_T_LIB_0078 |
| T-LIB-0079 | Check satisfiability with the Z3 encoding | fast | lib/test_solve.py | test_T_LIB_0079 |
| T-LIB-0080 | Attach an unsatisfiable core to CP-SAT infeasibility | fast | lib/test_solve.py | test_T_LIB_0080 |
| T-LIB-0081 | Record Z3 infeasibility independently | fast | lib/test_solve.py | test_T_LIB_0081 |
| T-LIB-0082 | Confirm stability across fixed thread counts | fast | lib/test_solve.py | test_T_LIB_0082 |
| T-LIB-0083 | Reject seeded instability between worker counts | fast | lib/test_solve.py | test_T_LIB_0083 |
| T-LIB-0084 | Record CP-SAT timeout as abstention | fast | lib/test_solve.py | test_T_LIB_0084 |
| T-LIB-0085 | Record exhausted Z3 time budget as abstention | fast | lib/test_solve.py | test_T_LIB_0085 |
| T-LIB-0086 | Reject domain and completeness errors independently | fast | lib/test_solve.py | test_T_LIB_0086 |
| T-LIB-0087 | Match mathematical enumeration for an encoded objective | fast | lib/test_solve.py | test_T_LIB_0087 |
| T-LIB-0088 | Require known variables before encoding | fast | lib/test_solve.py | test_T_LIB_0088 |
| T-LIB-0089 | Preserve the exact numeric model in the result scope | fast | lib/test_solve.py | test_T_LIB_0089 |
| T-LIB-0090 | Avoid infeasibility claims lacking independent evidence | fast | lib/test_solve.py | test_T_LIB_0090 |
| T-LIB-0091 | Choose the same plan across every input permutation | fast | lib/test_stability_crosscheck.py | test_T_LIB_0091 |
| T-LIB-0092 | Prioritize the first objective above later costs or keys | fast | lib/test_stability_crosscheck.py | test_T_LIB_0092 |
| T-LIB-0093 | Compare later objective fields before stable keys | fast | lib/test_stability_crosscheck.py | test_T_LIB_0093 |
| T-LIB-0094 | Reject duplicate explicit plan keys | fast | lib/test_stability_crosscheck.py | test_T_LIB_0094 |
| T-LIB-0095 | Return an empty choice for an empty feasible set | fast | lib/test_stability_crosscheck.py | test_T_LIB_0095 |
| T-LIB-0096 | Hold on grounded disagreement and record both citations | fast | lib/test_stability_crosscheck.py | test_T_LIB_0096 |
| T-LIB-0097 | Record both independent model identifiers on agreement | fast | lib/test_stability_crosscheck.py | test_T_LIB_0097 |
| T-LIB-0098 | Hold if the cited span does not support the value | fast | lib/test_stability_crosscheck.py | test_T_LIB_0098 |
| T-LIB-0099 | Hold if the independent extraction is unavailable | fast | lib/test_stability_crosscheck.py | test_T_LIB_0099 |
| T-LIB-0100 | Prevent one model from counting as two independent calls | fast | lib/test_stability_crosscheck.py | test_T_LIB_0100 |
| T-LIB-0101 | Compare monetary rounding with integer arithmetic | fast | lib/differential/test_shared_modules.py | test_T_LIB_0101 |
| T-LIB-0102 | Replay a nested calculation against a known amount | fast | lib/differential/test_shared_modules.py | test_T_LIB_0102 |
| T-LIB-0103 | Compare unblock requirements with exhaustive subset search | fast | lib/differential/test_shared_modules.py | test_T_LIB_0103 |
| T-LIB-0104 | Validate a feed using canonical bytes from an independent producer | fast | lib/differential/test_shared_modules.py | test_T_LIB_0104 |
| T-LIB-0105 | Verify conformal thresholds using a known order statistic | fast | lib/differential/test_shared_modules.py | test_T_LIB_0105 |
| T-LIB-0106 | Compare the CP-SAT optimum with exhaustive search | fast | lib/differential/test_shared_modules.py | test_T_LIB_0106 |
| T-LIB-0107 | Check plan stability against a known tie-break answer | fast | lib/differential/test_shared_modules.py | test_T_LIB_0107 |
| T-LIB-0108 | Check the known result of independently cited disagreement | fast | lib/differential/test_shared_modules.py | test_T_LIB_0108 |
| T-LIB-0109 | Name both capabilities in a cycle | fast | lib/test_capgen.py | test_T_LIB_0109 |
| T-LIB-0110 | Name all phases in a cycle | fast | lib/test_capgen.py | test_T_LIB_0110 |
| T-LIB-0111 | Check the real dependency registries | fast | lib/test_capgen.py | test_T_LIB_0111 |
| T-LIB-0112 | Reject tenant-scope Passport inputs | fast | lib/test_capgen.py | test_T_LIB_0112 |
| T-OBS-0001 | a metric with a tenant label is rejected | fast | observability/test_T_OBS_0001_to_0012.py | test_T_OBS_0001_tenant_label_rejected |
| T-OBS-0002 | a metric with a tenant_id label is rejected | fast | observability/test_T_OBS_0001_to_0012.py | test_T_OBS_0002_tenant_id_label_rejected |
| T-OBS-0003 | a metric without tenant labels is accepted | fast | observability/test_T_OBS_0001_to_0012.py | test_T_OBS_0003_metric_without_tenant_ok |
| T-OBS-0004 | JSON log includes correlation id | fast | observability/test_T_OBS_0001_to_0012.py | test_T_OBS_0004_log_includes_correlation_id |
| T-OBS-0005 | JSON log includes tenant id | fast | observability/test_T_OBS_0001_to_0012.py | test_T_OBS_0005_log_includes_tenant_id |
| T-OBS-0006 | seeded personal data never reaches logs | fast | observability/test_T_OBS_0001_to_0012.py | test_T_OBS_0006_no_personal_data_in_logs |
| T-OBS-0007 | model call yields a span with stated attributes | fast | observability/test_T_OBS_0001_to_0012.py | test_T_OBS_0007_model_call_span_attributes |
| T-OBS-0008 | model call span has a unique span_id | fast | observability/test_T_OBS_0001_to_0012.py | test_T_OBS_0008_span_id_unique |
| T-OBS-0009 | JSON log format is valid JSON | fast | observability/test_T_OBS_0001_to_0012.py | test_T_OBS_0009_log_valid_json |
| T-OBS-0010 | metric counter accumulates | fast | observability/test_T_OBS_0001_to_0012.py | test_T_OBS_0010_counter_accumulates |
| T-OBS-0011 | gauge sets value | fast | observability/test_T_OBS_0001_to_0012.py | test_T_OBS_0011_gauge_sets_value |
| T-OBS-0012 | correlation id is settable | fast | observability/test_T_OBS_0001_to_0012.py | test_T_OBS_0012_correlation_id_settable |
| T-OBS-0013 | canary passes on a healthy stack | fast | observability/test_T_OBS_0013_to_0022.py | test_T_OBS_0013_canary_passes_healthy |
| T-OBS-0014 | canary fails on a seeded fault | fast | observability/test_T_OBS_0013_to_0022.py | test_T_OBS_0014_canary_fails_fault |
| T-OBS-0015 | a deleted span is reported as a gap | fast | observability/test_T_OBS_0013_to_0022.py | test_T_OBS_0015_deleted_span_gap |
| T-OBS-0016 | no gap when traces match ledger | fast | observability/test_T_OBS_0013_to_0022.py | test_T_OBS_0016_no_gap_when_match |
| T-OBS-0017 | objectives parse correctly | fast | observability/test_T_OBS_0013_to_0022.py | test_T_OBS_0017_objectives_parse |
| T-OBS-0018 | error budgets parse correctly | fast | observability/test_T_OBS_0013_to_0022.py | test_T_OBS_0018_error_budgets_parse |
| T-OBS-0019 | evaluate_objectives with passing results | fast | observability/test_T_OBS_0013_to_0022.py | test_T_OBS_0019_objectives_passing |
| T-OBS-0020 | evaluate_objectives with a failing result | fast | observability/test_T_OBS_0013_to_0022.py | test_T_OBS_0020_objectives_failing |
| T-OBS-0021 | canary interval is 5 minutes (300 seconds) | fast | observability/test_T_OBS_0013_to_0022.py | test_T_OBS_0021_canary_interval_5min |
| T-OBS-0022 | canary result carries SYNTHETIC label | fast | observability/test_T_OBS_0013_to_0022.py | test_T_OBS_0022_canary_label_synthetic |
| T-OBS-0023 | max_model_calls limit enforced at boundary | fast | observability/test_T_OBS_0023_to_0032.py | test_T_OBS_0023_model_calls_limit |
| T-OBS-0024 | max_tokens limit enforced | fast | observability/test_T_OBS_0023_to_0032.py | test_T_OBS_0024_tokens_limit |
| T-OBS-0025 | max_tool_calls limit enforced | fast | observability/test_T_OBS_0023_to_0032.py | test_T_OBS_0025_tool_calls_limit |
| T-OBS-0026 | max_workflow_steps limit enforced | fast | observability/test_T_OBS_0023_to_0032.py | test_T_OBS_0026_workflow_steps_limit |
| T-OBS-0027 | extraction usage does not reduce meter other | fast | observability/test_T_OBS_0023_to_0032.py | test_T_OBS_0027_extraction_does_not_reduce_other |
| T-OBS-0028 | other meter does not reduce extraction | fast | observability/test_T_OBS_0023_to_0032.py | test_T_OBS_0028_other_does_not_reduce_extraction |
| T-OBS-0029 | extraction exhaustion leaves earlier documents intact | fast | observability/test_T_OBS_0023_to_0032.py | test_T_OBS_0029_extraction_exhaustion_intact |
| T-OBS-0030 | per-document call allowance enforced | fast | observability/test_T_OBS_0023_to_0032.py | test_T_OBS_0030_per_document_allowance |
| T-OBS-0031 | usage events reconcile with the ledger | fast | observability/test_T_OBS_0023_to_0032.py | test_T_OBS_0031_usage_events_reconcile |
| T-OBS-0032 | breach event is recorded | fast | observability/test_T_OBS_0023_to_0032.py | test_T_OBS_0032_breach_event_recorded |
| T-OPS-0001 | Declare non-root runtime and a health check | fast | ops/test_T_OPS_0001_to_0010.py | test_runtime_dockerfile_uses_nonroot_and_health_check |
| T-OPS-0002 | Pin each image stage | fast | ops/test_T_OPS_0001_to_0010.py | test_dockerfile_pins_build_bases |
| T-OPS-0003 | Accept a clean scanner result | fast | ops/test_T_OPS_0001_to_0010.py | test_clean_scan_passes |
| T-OPS-0004 | Accept one exact approved finding | fast | ops/test_T_OPS_0001_to_0010.py | test_exact_approved_finding_passes |
| T-OPS-0005 | Reject a finding outside D5 | fast | ops/test_T_OPS_0001_to_0010.py | test_unapproved_vulnerability_fails |
| T-OPS-0006 | Reject an incomplete scan | fast | ops/test_T_OPS_0001_to_0010.py | test_omitted_package_inventory_fails |
| T-OPS-0007 | Bind findings to the pinned vulnerability database | fast | ops/test_T_OPS_0001_to_0010.py | test_different_database_metadata_fails |
| T-OPS-0008 | Select locked dependencies for the target runtime | fast | ops/test_T_OPS_0001_to_0010.py | test_runtime_export_selects_target_and_exact_versions |
| T-OPS-0009 | Check inventory against the frozen export | fast | ops/test_T_OPS_0001_to_0010.py | test_sbom_contains_exact_locked_package_version |
| T-OPS-0010 | Fail when a locked Python distribution is missing | fast | ops/test_T_OPS_0001_to_0010.py | test_sbom_rejects_wrong_versions_and_ecosystems |
| T-OPS-0011 | Validate the deployment contract | fast | ops/test_T_OPS_0011_to_0018.py | test_T_OPS_0011 |
| T-OPS-0012 | Fail startup on a missing secret | fast | ops/test_T_OPS_0011_to_0018.py | test_T_OPS_0012 |
| T-OPS-0013 | Isolate staging from production | fast | ops/test_T_OPS_0011_to_0018.py | test_T_OPS_0013 |
| T-OPS-0014 | Detect drift in either Blueprint | fast | ops/test_T_OPS_0011_to_0018.py | test_T_OPS_0014 |
| T-OPS-0015 | Stamp the Passport with public configuration | fast | ops/test_T_OPS_0011_to_0018.py | test_T_OPS_0015 |
| T-OPS-0016 | Use the configuration hash recorded in the export | fast | ops/test_T_OPS_0011_to_0018.py | test_T_OPS_0016 |
| T-OPS-0017 | Replay a legacy Passport | fast | ops/test_T_OPS_0011_to_0018.py | test_T_OPS_0017 |
| T-OPS-0018 | Isolate checkpoint signing and preserve the last root | fast | ops/test_T_OPS_0011_to_0018.py | test_T_OPS_0018 |
| T-OPS-0019 | Bundle all required services | fast | ops/test_T_OPS_0019_to_0028.py | test_T_OPS_0019 |
| T-OPS-0020 | Pin the confirmed database image | fast | ops/test_T_OPS_0019_to_0028.py | test_T_OPS_0020 |
| T-OPS-0021 | Pin the policy executable | fast | ops/test_T_OPS_0019_to_0028.py | test_T_OPS_0021 |
| T-OPS-0022 | Isolate migration privileges | fast | ops/test_T_OPS_0019_to_0028.py | test_T_OPS_0022 |
| T-OPS-0023 | Limit access to local services | fast | ops/test_T_OPS_0019_to_0028.py | test_T_OPS_0023 |
| T-OPS-0024 | Share an exact application image | fast | ops/test_T_OPS_0019_to_0028.py | test_T_OPS_0024 |
| T-OPS-0025 | Verify a synthetic case export | fast | ops/test_T_OPS_0019_to_0028.py | test_T_OPS_0025 |
| T-OPS-0026 | Reject a corrupt Merkle root | fast | ops/test_T_OPS_0019_to_0028.py | test_T_OPS_0026 |
| T-OPS-0027 | Require application-side verification | fast | ops/test_T_OPS_0019_to_0028.py | test_T_OPS_0027 |
| T-OPS-0028 | Require a nonempty case bundle | fast | ops/test_T_OPS_0019_to_0028.py | test_T_OPS_0028 |
| T-OPS-0029 | Publish a verified regional backup | fast | ops/test_T_OPS_0029_to_0038.py | test_T_OPS_0029 |
| T-OPS-0030 | Detect a corrupted archive | fast | ops/test_T_OPS_0029_to_0038.py | test_T_OPS_0030 |
| T-OPS-0031 | Reject out-of-region inventory | fast | ops/test_T_OPS_0029_to_0038.py | test_T_OPS_0031 |
| T-OPS-0032 | Reject an unapproved restore region | fast | ops/test_T_OPS_0029_to_0038.py | test_T_OPS_0032 |
| T-OPS-0033 | Retain independent backup snapshots | fast | ops/test_T_OPS_0029_to_0038.py | test_T_OPS_0033 |
| T-OPS-0034 | Reject a failed backup before publish | fast | ops/test_T_OPS_0029_to_0038.py | test_T_OPS_0034 |
| T-OPS-0035 | Verify restored ledger chains independently | fast | ops/test_T_OPS_0029_to_0038.py | test_T_OPS_0035 |
| T-OPS-0036 | Reject changed restored ledger records | fast | ops/test_T_OPS_0029_to_0038.py | test_T_OPS_0036 |
| T-OPS-0037 | Record measured recovery objectives | fast | ops/test_T_OPS_0029_to_0038.py | test_T_OPS_0037 |
| T-OPS-0038 | Reject recovery beyond either objective | fast | ops/test_T_OPS_0029_to_0038.py | test_T_OPS_0038 |
| T-OPS-0039 | Promote a healthy candidate | fast | ops/test_T_OPS_0039_to_0046.py | test_T_OPS_0039 |
| T-OPS-0040 | Roll back a failing canary | fast | ops/test_T_OPS_0039_to_0046.py | test_T_OPS_0040 |
| T-OPS-0041 | Roll back an exhausted error budget | fast | ops/test_T_OPS_0039_to_0046.py | test_T_OPS_0041 |
| T-OPS-0042 | Require a healthy rollback candidate | fast | ops/test_T_OPS_0039_to_0046.py | test_T_OPS_0042 |
| T-OPS-0043 | Reject mutable image references | fast | ops/test_T_OPS_0039_to_0046.py | test_T_OPS_0043 |
| T-OPS-0044 | Link promotions and rollbacks | fast | ops/test_T_OPS_0039_to_0046.py | test_T_OPS_0044 |
| T-OPS-0045 | Prevent stale concurrent release decisions | fast | ops/test_T_OPS_0039_to_0046.py | test_T_OPS_0045 |
| T-OPS-0046 | Reject changed deployment payloads | fast | ops/test_T_OPS_0039_to_0046.py | test_T_OPS_0046 |
| T-OPS-0047 | Map operations threats to indexed tests | fast | ops/test_T_OPS_0047_to_0052.py | test_T_OPS_0047 |
| T-OPS-0048 | Register all declared operations kill points | fast | ops/test_T_OPS_0047_to_0052.py | test_T_OPS_0048 |
| T-OPS-0049 | Kill a restore target and recover on retry | slow | ops/test_T_OPS_0047_to_0052.py | test_T_OPS_0049 |
| T-OPS-0050 | Keep the application stopped on migration failure | fast | ops/test_T_OPS_0047_to_0052.py | test_T_OPS_0050 |
| T-OPS-0051 | Confine supply-chain evidence to pinned inputs | fast | ops/test_T_OPS_0047_to_0052.py | test_T_OPS_0051 |
| T-OPS-0052 | Keep invalid settings out of error messages | fast | ops/test_T_OPS_0047_to_0052.py | test_T_OPS_0052 |
| T-ORC-0001 | A valid workflow DAG loads and validates | fast | orchestration/test_T_ORC_0001_to_0014.py | test_T_ORC_0001_valid_dag_loads |
| T-ORC-0002 | A cycle in the DAG is rejected | fast | orchestration/test_T_ORC_0001_to_0014.py | test_T_ORC_0002_cycle_rejected |
| T-ORC-0003 | An unknown role in a step is rejected | fast | orchestration/test_T_ORC_0001_to_0014.py | test_T_ORC_0003_unknown_role_rejected |
| T-ORC-0004 | An edge to a non-existent step is rejected | fast | orchestration/test_T_ORC_0001_to_0014.py | test_T_ORC_0004_edge_to_missing_step_rejected |
| T-ORC-0005 | A transition outside the DAG is rejected | fast | orchestration/test_T_ORC_0001_to_0014.py | test_T_ORC_0005_transition_outside_dag_rejected |
| T-ORC-0006 | A role cannot exceed its budget share | fast | orchestration/test_T_ORC_0001_to_0014.py | test_T_ORC_0006_role_exceeds_budget |
| T-ORC-0007 | A timeout moves a case to BLOCKED and never approves | fast | orchestration/test_T_ORC_0001_to_0014.py | test_T_ORC_0007_timeout_moves_to_blocked |
| T-ORC-0008 | Repeated delivery of one step executes once | fast | orchestration/test_T_ORC_0001_to_0014.py | test_T_ORC_0008_idempotent_execution |
| T-ORC-0009 | The DAG configuration hash is deterministic | fast | orchestration/test_T_ORC_0001_to_0014.py | test_T_ORC_0009_config_hash_deterministic |
| T-ORC-0010 | The Manager records every step | fast | orchestration/test_T_ORC_0001_to_0014.py | test_T_ORC_0010_steps_recorded |
| T-ORC-0011 | The Manager chooses the deterministic path | fast | orchestration/test_T_ORC_0001_to_0014.py | test_T_ORC_0011_deterministic_path |
| T-ORC-0012 | The case budget is split among roles | fast | orchestration/test_T_ORC_0001_to_0014.py | test_T_ORC_0012_budget_split_among_roles |
| T-ORC-0013 | State transitions follow the case state machine | fast | orchestration/test_T_ORC_0001_to_0014.py | test_T_ORC_0013_state_transitions |
| T-ORC-0014 | A budget exhaustion moves the case to BLOCKED via run() | fast | orchestration/test_T_ORC_0001_to_0014.py | test_T_ORC_0014_budget_exhaustion_blocks |
| T-ORC-0015 | A valid input message is accepted | fast | orchestration/test_T_ORC_0015_to_0026.py | test_T_ORC_0015_valid_input_accepted |
| T-ORC-0016 | An invalid message missing a required field is rejected | fast | orchestration/test_T_ORC_0015_to_0026.py | test_T_ORC_0016_missing_required_rejected |
| T-ORC-0017 | An unknown field in a message is rejected | fast | orchestration/test_T_ORC_0015_to_0026.py | test_T_ORC_0017_unknown_field_rejected |
| T-ORC-0018 | A valid output message is accepted and recorded | fast | orchestration/test_T_ORC_0015_to_0026.py | test_T_ORC_0018_valid_output_accepted |
| T-ORC-0019 | An output not matching the port type is refused | fast | orchestration/test_T_ORC_0015_to_0026.py | test_T_ORC_0019_invalid_output_refused |
| T-ORC-0020 | A command in an explanation field has no effect | fast | orchestration/test_T_ORC_0015_to_0026.py | test_T_ORC_0020_command_in_explanation_no_effect |
| T-ORC-0021 | A command in a non-explanation field is rejected | fast | orchestration/test_T_ORC_0015_to_0026.py | test_T_ORC_0021_command_in_value_rejected |
| T-ORC-0022 | A worker failure never yields ALLOW | fast | orchestration/test_T_ORC_0015_to_0026.py | test_T_ORC_0022_failure_never_allow |
| T-ORC-0023 | Compliance failure ends in ABSTAIN | fast | orchestration/test_T_ORC_0015_to_0026.py | test_T_ORC_0023_compliance_failure_abstain |
| T-ORC-0024 | Risk failure ends in ESCALATE | fast | orchestration/test_T_ORC_0015_to_0026.py | test_T_ORC_0024_risk_failure_escalate |
| T-ORC-0025 | An unknown role raises RuntimeError_ | fast | orchestration/test_T_ORC_0015_to_0026.py | test_T_ORC_0025_unknown_role_rejected |
| T-ORC-0026 | Every role in the closed list has a contract | fast | orchestration/test_T_ORC_0015_to_0026.py | test_T_ORC_0026_all_roles_have_contracts |
| T-ORC-0027 | An ungranted tool is denied | fast | orchestration/test_T_ORC_0027_to_0042.py | test_T_ORC_0027_ungranted_tool_denied |
| T-ORC-0028 | A granted tool is allowed | fast | orchestration/test_T_ORC_0027_to_0042.py | test_T_ORC_0028_granted_tool_allowed |
| T-ORC-0029 | A scope mismatch is denied | fast | orchestration/test_T_ORC_0027_to_0042.py | test_T_ORC_0029_scope_mismatch_denied |
| T-ORC-0030 | An over-rate call is denied | fast | orchestration/test_T_ORC_0027_to_0042.py | test_T_ORC_0030_over_rate_denied |
| T-ORC-0031 | An off-list host is denied | fast | orchestration/test_T_ORC_0027_to_0042.py | test_T_ORC_0031_off_list_host_denied |
| T-ORC-0032 | An on-list host is allowed | fast | orchestration/test_T_ORC_0027_to_0042.py | test_T_ORC_0032_on_list_host_allowed |
| T-ORC-0033 | A model naming a URL is denied | fast | orchestration/test_T_ORC_0027_to_0042.py | test_T_ORC_0033_model_url_denied |
| T-ORC-0034 | A model naming a file path is denied | fast | orchestration/test_T_ORC_0027_to_0042.py | test_T_ORC_0034_model_path_denied |
| T-ORC-0035 | A model naming a destructive command is denied | fast | orchestration/test_T_ORC_0027_to_0042.py | test_T_ORC_0035_model_command_denied |
| T-ORC-0036 | Every call is recorded | fast | orchestration/test_T_ORC_0027_to_0042.py | test_T_ORC_0036_every_call_recorded |
| T-ORC-0037 | Each call record has input and output hashes | fast | orchestration/test_T_ORC_0027_to_0042.py | test_T_ORC_0037_hashes_in_record |
| T-ORC-0038 | Every policy has allow and deny cases | fast | orchestration/test_T_ORC_0027_to_0042.py | test_T_ORC_0038_every_policy_has_cases |
| T-ORC-0039 | Policy allow cases evaluate to ALLOW | fast | orchestration/test_T_ORC_0027_to_0042.py | test_T_ORC_0039_allow_cases_pass |
| T-ORC-0040 | Policy deny cases evaluate to DENY | fast | orchestration/test_T_ORC_0027_to_0042.py | test_T_ORC_0040_deny_cases_fail |
| T-ORC-0041 | run_policy_tests reports all cases passing | fast | orchestration/test_T_ORC_0027_to_0042.py | test_T_ORC_0041_policy_tests_all_pass |
| T-ORC-0042 | An unknown policy raises PolicyError | fast | orchestration/test_T_ORC_0027_to_0042.py | test_T_ORC_0042_unknown_policy_raises |
| T-ORC-0043 | E-irrev without a bound approval is blocked at A0 | fast | orchestration/test_T_ORC_0043_to_0050.py | test_T_ORC_0043_eirrev_blocked_at_a0 |
| T-ORC-0044 | E-irrev without a bound approval is blocked at A2 | fast | orchestration/test_T_ORC_0043_to_0050.py | test_T_ORC_0044_eirrev_blocked_without_approval |
| T-ORC-0045 | E-irrev with a bound approval is allowed at A2 | fast | orchestration/test_T_ORC_0043_to_0050.py | test_T_ORC_0045_eirrev_allowed_with_approval |
| T-ORC-0046 | No level above A2 can be configured | fast | orchestration/test_T_ORC_0043_to_0050.py | test_T_ORC_0046_no_level_above_a2 |
| T-ORC-0047 | The default level is A1 | fast | orchestration/test_T_ORC_0043_to_0050.py | test_T_ORC_0047_default_is_a1 |
| T-ORC-0048 | A0 allows only R (observe) | fast | orchestration/test_T_ORC_0043_to_0050.py | test_T_ORC_0048_a0_observe_only |
| T-ORC-0049 | A1 allows R and P but not E-rev or E-irrev | fast | orchestration/test_T_ORC_0043_to_0050.py | test_T_ORC_0049_a1_propose_only |
| T-ORC-0050 | A level change is recorded as a system-chain event | fast | orchestration/test_T_ORC_0043_to_0050.py | test_T_ORC_0050_change_recorded |
| T-ORC-0051 | Step cap monitor fires on exceeding the cap | fast | containment/test_T_ORC_0051_to_0065.py | test_T_ORC_0051_step_cap_fires |
| T-ORC-0052 | Loop monitor fires on repeated tool+args | fast | containment/test_T_ORC_0051_to_0065.py | test_T_ORC_0052_loop_monitor_fires |
| T-ORC-0053 | Transition monitor fires on out-of-DAG transition | fast | containment/test_T_ORC_0051_to_0065.py | test_T_ORC_0053_transition_monitor_fires |
| T-ORC-0054 | Budget burn monitor fires on exceeded burn rate | fast | containment/test_T_ORC_0051_to_0065.py | test_T_ORC_0054_budget_burn_fires |
| T-ORC-0055 | Output size monitor fires on oversized output | fast | containment/test_T_ORC_0051_to_0065.py | test_T_ORC_0055_output_size_fires |
| T-ORC-0056 | Verification failure monitor fires on repeated failures | fast | containment/test_T_ORC_0051_to_0065.py | test_T_ORC_0056_verification_failure_fires |
| T-ORC-0057 | Policy denial monitor fires on repeated denials | fast | containment/test_T_ORC_0051_to_0065.py | test_T_ORC_0057_policy_denial_fires |
| T-ORC-0058 | Pause case kill switch rejects new commands | fast | containment/test_T_ORC_0051_to_0065.py | test_T_ORC_0058_pause_case_rejects |
| T-ORC-0059 | Disable capability kill switch rejects | fast | containment/test_T_ORC_0051_to_0065.py | test_T_ORC_0059_disable_capability_rejects |
| T-ORC-0060 | Tenant freeze rejects new commands | fast | containment/test_T_ORC_0051_to_0065.py | test_T_ORC_0060_tenant_freeze_rejects |
| T-ORC-0061 | Tenant freeze is lifted only by the tenant administrator | fast | containment/test_T_ORC_0051_to_0065.py | test_T_ORC_0061_tenant_freeze_lift_requires_admin |
| T-ORC-0062 | Deployment freeze is lifted only by two platform operators | fast | containment/test_T_ORC_0051_to_0065.py | test_T_ORC_0062_deployment_freeze_requires_two |
| T-ORC-0063 | A kill switch records a system-chain event | fast | containment/test_T_ORC_0051_to_0065.py | test_T_ORC_0063_kill_switch_records_event |
| T-ORC-0064 | Monitor suite runs all monitors and returns first violation | fast | containment/test_T_ORC_0051_to_0065.py | test_T_ORC_0064_suite_returns_first_violation |
| T-ORC-0065 | A clean case does not trigger any monitor | fast | containment/test_T_ORC_0051_to_0065.py | test_T_ORC_0065_clean_case_no_violation |
| T-ORC-0066 | Short fuzz of messages finds no crash | fast | containment/test_T_ORC_0066_fuzz.py | test_T_ORC_0066_fuzz_no_crash |
| T-ORC-0067 | Approval of a changed proposal is invalid | fast | orchestration/test_T_ORC_0067_to_0078.py | test_T_ORC_0067_changed_proposal_invalid |
| T-ORC-0068 | A valid approval is accepted | fast | orchestration/test_T_ORC_0067_to_0078.py | test_T_ORC_0068_valid_approval_accepted |
| T-ORC-0069 | A rejection requires written justification | fast | orchestration/test_T_ORC_0067_to_0078.py | test_T_ORC_0069_rejection_requires_justification |
| T-ORC-0070 | An override is a separate record | fast | orchestration/test_T_ORC_0067_to_0078.py | test_T_ORC_0070_override_is_separate_record |
| T-ORC-0071 | An override by the same reviewer twice is refused | fast | orchestration/test_T_ORC_0067_to_0078.py | test_T_ORC_0071_override_same_reviewer_refused |
| T-ORC-0072 | An override without a second reviewer is refused | fast | orchestration/test_T_ORC_0067_to_0078.py | test_T_ORC_0072_override_no_second_reviewer_refused |
| T-ORC-0073 | The Decision record is unchanged after an override | fast | orchestration/test_T_ORC_0067_to_0078.py | test_T_ORC_0073_decision_unchanged_after_override |
| T-ORC-0074 | The second concurrent approval receives a conflict | fast | orchestration/test_T_ORC_0067_to_0078.py | test_T_ORC_0074_concurrent_approval_conflict |
| T-ORC-0075 | A reviewer role is required | fast | orchestration/test_T_ORC_0067_to_0078.py | test_T_ORC_0075_reviewer_role_required |
| T-ORC-0076 | Approvals expire with the case state | fast | orchestration/test_T_ORC_0067_to_0078.py | test_T_ORC_0076_approval_expires_with_state |
| T-ORC-0077 | A rejection is recorded | fast | orchestration/test_T_ORC_0067_to_0078.py | test_T_ORC_0077_rejection_recorded |
| T-ORC-0078 | An override without justification is refused | fast | orchestration/test_T_ORC_0067_to_0078.py | test_T_ORC_0078_override_without_justification_refused |
| T-ORC-0079 | Hostile instruction to change goals ends without an effect | fast | containment/test_T_ORC_0079_to_0090.py | test_T_ORC_0079_goal_change_rejected |
| T-ORC-0080 | Hostile instruction to call tools ends without an effect | fast | containment/test_T_ORC_0079_to_0090.py | test_T_ORC_0080_tool_call_denied |
| T-ORC-0081 | Hostile instruction to exfiltrate ends without an effect | fast | containment/test_T_ORC_0079_to_0090.py | test_T_ORC_0081_exfiltration_denied |
| T-ORC-0082 | Hostile instruction to loop ends in quarantine | fast | containment/test_T_ORC_0079_to_0090.py | test_T_ORC_0082_loop_detected |
| T-ORC-0083 | Hostile instruction to exceed budget ends in BLOCKED | fast | containment/test_T_ORC_0079_to_0090.py | test_T_ORC_0083_budget_exceeded_blocked |
| T-ORC-0084 | Hostile instruction to skip the Human Gate is rejected | fast | containment/test_T_ORC_0079_to_0090.py | test_T_ORC_0084_skip_human_gate_rejected |
| T-ORC-0085 | Confused deputy: a frozen tenant cannot issue commands | fast | containment/test_T_ORC_0079_to_0090.py | test_T_ORC_0085_confused_deputy_frozen |
| T-ORC-0086 | Confused deputy: a paused case cannot execute steps | fast | containment/test_T_ORC_0079_to_0090.py | test_T_ORC_0086_paused_case_rejects |
| T-ORC-0087 | 100 percent of the adversarial set ends without an effect | fast | containment/test_T_ORC_0079_to_0090.py | test_T_ORC_0087_all_adversarial_no_effect |
| T-ORC-0088 | Crash recovery resumes without duplicate effects | fast | containment/test_T_ORC_0079_to_0090.py | test_T_ORC_0088_crash_recovery_no_duplicate |
| T-ORC-0089 | Mapped threat items have tests | fast | containment/test_T_ORC_0079_to_0090.py | test_T_ORC_0089_mapped_items_have_tests |
| T-ORC-0090 | Orchestrator kill points are registered in the fault lab | fast | containment/test_T_ORC_0079_to_0090.py | test_T_ORC_0090_orchestrator_kill_points_registered |
| T-PHASE-0001 | Missing DONE line fails exit check | fast | gate/test_phase.py | test_missing_done_line_fails |
| T-PHASE-0002 | Task commit without DONE line fails | fast | gate/test_phase.py | test_task_commit_without_done_fails |
| T-PHASE-0003 | Squash merge fails merge proof check | fast | gate/test_phase.py | test_squash_merge_fails |
| T-PHASE-0004 | Rebase merge fails merge proof check | fast | gate/test_phase.py | test_rebase_merge_fails |
| T-PHASE-0005 | Dirty tree fails clean-tree check | fast | gate/test_phase.py | test_dirty_tree_fails |
| T-PHASE-0006 | STATE mismatch fails state consistency check | fast | gate/test_phase.py | test_state_mismatch_fails |
| T-PHASE-0007 | Wrong directive hash fails directive hash check | fast | gate/test_phase.py | test_wrong_directive_hash_fails |
| T-PHASE-0008 | Previous branch not deleted fails check | fast | gate/test_phase.py | test_previous_branch_not_deleted_fails |
| T-PHASE-0009 | Missing report field fails validation | fast | gate/test_phase.py | test_missing_report_field_fails |
| T-PHASE-0010 | Extra report field fails validation | fast | gate/test_phase.py | test_extra_report_field_fails |
| T-PHASE-0011 | Handwritten STATE edit fails (state_hash mismatch) | fast | gate/test_phase.py | test_handwritten_state_edit_fails |
| T-PHASE-0012 | Baseline decrease fails check | fast | gate/test_phase.py | test_baseline_decrease_fails |
| T-PHASE-0013 | Non-existent marker in Context Pack fails directive lint | fast | gate/test_directive.py | test_nonexistent_marker_fails |
| T-PHASE-0014 | Missing phase block field fails directive lint | fast | gate/test_directive.py | test_missing_field_fails |
| T-PHASE-0015 | Non-sequential task ids fail directive lint | fast | gate/test_directive.py | test_non_sequential_tasks_fails |
| T-PHASE-0016 | Missing Pnn-RISK before Pnn-END1 fails directive lint | fast | gate/test_directive.py | test_missing_risk_fails |
| T-PHASE-0017 | Duplicated test id range fails directive lint | fast | gate/test_directive.py | test_dup_test_range_fails |
| T-PHASE-0018 | Look-ahead referencing non-existent phase fails | fast | gate/test_directive.py | test_bad_lookahead_fails |
| T-PHASE-0019 | Missing Scope paths line fails directive lint | fast | gate/test_directive.py | test_missing_scope_paths_fails |
| T-PHASE-0020 | Block count differing from phases.toml fails directive lint | fast | gate/test_directive.py | test_block_count_differs_fails |
| T-PHASE-0021 | Clean directive passes all checks | fast | gate/test_directive.py | test_clean_directive_passes |
| T-PHASE-0022 | Path outside scope globs fails scope check | fast | gate/test_directive.py | test_scope_outside_globs_fails |
| T-PHASE-0023 | Protected path not named by a task fails scope check | fast | gate/test_directive.py | test_scope_protected_path_fails |
| T-PHASE-0024 | Rename out of scope fails scope check | fast | gate/test_directive.py | test_scope_rename_out_of_scope_fails |
| T-PHASE-0025 | No baseline decrease passes check | fast | gate/test_phase.py | test_no_baseline_decrease_passes |
| T-PHASE-0026 | All DONE lines present passes check | fast | gate/test_phase.py | test_all_done_lines_pass |
| T-PHASE-0027 | phases.toml loads with 16 phase entries | fast | gate/test_phase.py | test_phases_table_loads |
| T-PHASE-0028 | STOP report with all required fields passes | fast | gate/test_phase.py | test_stop_report_valid |
| T-PHASE-0029 | State hash is deterministic | fast | gate/test_phase.py | test_state_hash_deterministic |
| T-PHASE-0030 | Self-review with 10 findings and no overflow passes | fast | gate/test_phase.py | test_selfreview_10_findings_passes |
| T-PHASE-0031 | Known-answer vector for the entry hash | fast | gate/test_chain.py | test_entry_hash_known_answer |
| T-PHASE-0032 | Chain verification detects altered, deleted, reordered, re-linked | fast | gate/test_chain.py | test_verify_clean_chain |
| T-PHASE-0033 | STOP at each boundary of a ten-task fixture phase resumes to identical tree hash | slow | gate/test_recovery.py | test_stop_at_each_boundary_resumes |
| T-PHASE-0034 | STOP report with missing field fails the check | fast | gate/test_recovery.py | test_stop_report_missing_field_fails |
| T-PHASE-0035 | Dirty tree without an explaining STOP report fails recovery | fast | gate/test_recovery.py | test_dirty_without_stop_report_fails |
| T-PHASE-0036 | Task re-run on a finished tree changes nothing (idempotency) | slow | gate/test_recovery.py | test_task_rerun_changes_nothing |
| T-PHASE-0037 | STOP report with all required fields passes the check | fast | gate/test_recovery.py | test_stop_report_valid_passes |
| T-PHASE-0038 | Dirty tree with an explaining STOP report passes recovery | fast | gate/test_recovery.py | test_dirty_with_stop_report_passes |
| T-PHASE-0039 | Clean tree passes the recovery check | fast | gate/test_recovery.py | test_clean_tree_passes_recovery |
| T-PHASE-0040 | STOP at boundary 0 (no tasks run) resumes to identical tree hash | slow | gate/test_recovery.py | test_stop_at_boundary_0_resumes |
| T-PHASE-0041 | Valid stub commit passes stub mode check | fast | gate/test_directive.py | test_valid_stub_passes |
| T-PHASE-0042 | Stub commit that changes another path fails | fast | gate/test_directive.py | test_stub_changes_other_path_fails |
| T-PHASE-0043 | Stub text differing from stub.txt fails | fast | gate/test_directive.py | test_stub_text_differs_fails |
| T-PHASE-0044 | Stub not the last commit fails | fast | gate/test_directive.py | test_stub_not_last_commit_fails |
| T-PHASE-0045 | Parent not P32-END2 fails | fast | gate/test_directive.py | test_parent_not_end2_fails |
| T-PHASE-0046 | Parent directive hash differing from STATE.json fails | fast | gate/test_directive.py | test_parent_hash_differs_fails |
| T-PHASE-0047 | Changed directive.txt outside stub mode fails | fast | gate/test_directive.py | test_changed_directive_outside_stub_fails |
| T-PHASE-0048 | On main with stub and STATE P32 DONE prints RELEASED | fast | gate/test_directive.py | test_released_prints |
| T-PHASE-0049 | 11th finding without OVERFLOW line fails | fast | gate/test_phase.py | test_11_findings_without_overflow_fails |
| T-PHASE-0050 | OVERFLOW line with wrong counts fails | fast | gate/test_phase.py | test_overflow_counts_differ_fails |
| T-PHASE-0051 | Overflow file without OVERFLOW line fails | fast | gate/test_phase.py | test_overflow_file_without_line_fails |
| T-PHASE-0052 | Finding over 40 words fails | fast | gate/test_phase.py | test_finding_over_40_words_fails |
| T-PHASE-0053 | Undefined reason code fails cross-check | fast | gate/test_directive.py | test_cross_undefined_reason_code_fails |
| T-PHASE-0054 | Wrong outcome word fails cross-check | fast | gate/test_directive.py | test_cross_wrong_outcome_word_fails |
| T-PHASE-0055 | Unknown matching mode fails cross-check | fast | gate/test_directive.py | test_cross_unknown_matching_mode_fails |
| T-PHASE-0056 | Unknown label fails cross-check | fast | gate/test_directive.py | test_cross_unknown_label_fails |
| T-PHASE-0057 | Unknown status word fails cross-check | fast | gate/test_directive.py | test_cross_unknown_status_word_fails |
| T-PHASE-0058 | Changed key-fact value fails cross-check | fast | gate/test_directive.py | test_cross_changed_keyfact_value_fails |
| T-PHASE-0059 | Key-fact expression matching nowhere fails cross-check | fast | gate/test_directive.py | test_cross_keyfact_nowhere_fails |
| T-PHASE-0060 | Clean cross-check passes and table block excluded | fast | gate/test_directive.py | test_cross_clean_passes |
| T-PHASE-0061 | Interruption inside every task recovers to identical tree hash | slow | gate/test_recovery.py | test_interruption_every_task_recovers |
| T-PHASE-0062 | Bundle reproduces dirty tree on temp copy; tree restored only after verification | slow | gate/test_recovery.py | test_bundle_verification_and_restore |
| T-PHASE-0063 | Changed path outside Files of interrupted task is a STOP | fast | gate/test_recovery.py | test_outside_path_stops |
| T-PHASE-0064 | Interruption between task commit and DONE line resumes without second commit | slow | gate/test_recovery.py | test_interruption_between_commit_and_done |
| T-PHASE-0065 | Interruption in each phase-end step resumes at that step | slow | gate/test_recovery.py | test_interruption_phase_end_steps |
| T-PHASE-0066 | Stale index.lock removed only when no git process runs | slow | gate/test_recovery.py | test_stale_lock_removed |
| T-PHASE-0067 | Interruption record validates with all required fields | fast | gate/test_recovery.py | test_interruption_record_validates |
| T-PHASE-0068 | Dirty tree without the --interruption command is still a STOP | fast | gate/test_recovery.py | test_dirty_without_interruption_stops |
| T-PHASE-0069 | Telemetry without overhead/task split fails | fast | gate/test_chain.py | test_telemetry_missing_overhead_split_fails |
| T-PHASE-0070 | Overhead exceeding its limit triggers a violation naming overhead | fast | gate/test_chain.py | test_overhead_exceeds_limit_stops |
| T-PHASE-0071 | No part limits — only total enforced | fast | gate/test_chain.py | test_no_part_limits_total_within_passes |
| T-PHASE-0072 | Part limit in telemetry but not in decision record fails | fast | gate/test_chain.py | test_part_limit_not_in_decision_record_fails |
| T-PHASE-0073 | Telemetry save/load round trip | fast | gate/test_chain.py | test_telemetry_save_load_round_trip |
| T-PHASE-0101 | Mixed golden and non-golden commit fails | fast | gate/test_phase.py | test_golden_mixed_commit_fails |
| T-PHASE-0102 | Golden commit without proper scope or reason fails | fast | gate/test_phase.py | test_golden_commit_wrong_scope_fails |
| T-PHASE-0103 | Wrong previous_merge_hash fails check | fast | gate/test_phase.py | test_wrong_previous_merge_hash_fails |
| T-PHASE-0104 | awaiting_merge not cleared fails | fast | gate/test_phase.py | test_awaiting_merge_not_cleared_fails |
| T-PHASE-0105 | PARKED predecessor outside depends_on does not block entry | fast | gate/test_phase.py | test_parked_predecessor_enters |
| T-PHASE-0106 | PARKED dependency stops entry naming the phase | fast | gate/test_phase.py | test_parked_dependency_stops |
| T-PHASE-0107 | Proper two-parent merge passes merge proof | fast | gate/test_phase.py | test_proper_merge_passes |
| T-PHASE-0108 | Clean tree passes clean-tree check | fast | gate/test_phase.py | test_clean_tree_passes |
| T-PHASE-0109 | Correct directive hash passes check | fast | gate/test_phase.py | test_correct_directive_hash_passes |
| T-PHASE-0110 | Deleted previous branch passes check | fast | gate/test_phase.py | test_deleted_branch_passes |
| T-PHASE-0111 | Correct previous_merge_hash passes check | fast | gate/test_phase.py | test_correct_previous_merge_hash_passes |
| T-PHASE-0112 | State save/load round trip preserves all fields | fast | gate/test_phase.py | test_state_save_load_round_trip |
| T-PHASE-0113 | Finding within 40 words passes | fast | gate/test_phase.py | test_finding_within_40_words_passes |
| T-PHASE-0114 | Finding missing category fails | fast | gate/test_phase.py | test_finding_missing_category_fails |
| T-PHASE-0115 | Invalid finding category fails | fast | gate/test_phase.py | test_invalid_category_fails |
| T-PHASE-0116 | Overflow with correct counts passes | fast | gate/test_phase.py | test_overflow_correct_passes |
| T-PHASE-0117 | Self-review constants match spec | fast | gate/test_phase.py | test_selfreview_constants |
| T-PHASE-0118 | State consistency with matching ledger passes | fast | gate/test_phase.py | test_state_consistency_passes |
| T-RISK-0001 | risk validate scales exits 0 on valid SCALES.yaml | fast | risk/test_scales.py | test_validate_scales_passes |
| T-RISK-0002 | RISK-POLICY.md contains no compliance-claim phrases | fast | risk/test_policy.py | test_policy_has_no_forbidden_phrases |
| T-RISK-0003 | risk record validates against risk schema | fast | risk/test_validator.py | test_risk_schema_valid |
| T-RISK-0004 | control record validates against control schema | fast | risk/test_validator.py | test_control_schema_valid |
| T-RISK-0005 | hazard record validates against hazard schema | fast | risk/test_validator.py | test_hazard_schema_valid |
| T-RISK-0006 | threat record validates against threat schema | fast | risk/test_validator.py | test_threat_schema_valid |
| T-RISK-0007 | acceptance record validates against acceptance schema | fast | risk/test_validator.py | test_acceptance_schema_valid |
| T-RISK-0008 | review record validates against review schema | fast | risk/test_validator.py | test_review_schema_valid |
| T-RISK-0009 | incident record validates against incident schema | fast | risk/test_validator.py | test_incident_schema_valid |
| T-RISK-0010 | drill record validates against drill schema | fast | risk/test_validator.py | test_drill_schema_valid |
| T-RISK-0011 | unique ids pass validation | fast | risk/test_validator.py | test_unique_ids_pass |
| T-RISK-0012 | valid control references pass | fast | risk/test_validator.py | test_references_pass |
| T-RISK-0013 | PLANNED control with target_phase passes | fast | risk/test_validator.py | test_lifecycle_planned_with_target |
| T-RISK-0014 | PLANNED control with unreached target_phase passes | fast | risk/test_validator.py | test_control_overdue_pass |
| T-RISK-0015 | VERIFIED control with known test id passes | fast | risk/test_validator.py | test_verified_with_known_test_id |
| T-RISK-0016 | risk with area and accountable passes | fast | risk/test_validator.py | test_risk_fields_pass |
| T-RISK-0017 | every invariant and requirement is referenced by a risk or control | fast | risk/test_coverage.py | test_invariant_requirement_coverage |
| T-RISK-0018 | every threat of Part 3 section 3.15 has an entry | fast | risk/test_threat_coverage.py | test_threat_coverage_p3_s15 |
| T-RISK-0019 | every safeguard S1 to S7 of decision-d06 maps to a model risk and a | fast | risk/test_threat_coverage.py | test_safeguard_coverage_d06 |
| T-RISK-0020 | invalid risk record fails schema validation | fast | risk/test_validator.py | test_risk_schema_invalid |
| T-RISK-0021 | invalid control record fails schema validation | fast | risk/test_validator.py | test_control_schema_invalid |
| T-RISK-0022 | invalid hazard record fails schema validation | fast | risk/test_validator.py | test_hazard_schema_invalid |
| T-RISK-0023 | invalid threat record fails schema validation | fast | risk/test_validator.py | test_threat_schema_invalid |
| T-RISK-0024 | invalid acceptance record fails schema validation | fast | risk/test_validator.py | test_acceptance_schema_invalid |
| T-RISK-0025 | invalid review record fails schema validation | fast | risk/test_validator.py | test_review_schema_invalid |
| T-RISK-0026 | invalid incident record fails schema validation | fast | risk/test_validator.py | test_incident_schema_invalid |
| T-RISK-0027 | invalid drill record fails schema validation | fast | risk/test_validator.py | test_drill_schema_invalid |
| T-RISK-0028 | duplicate ids fail validation | fast | risk/test_validator.py | test_unique_ids_fail |
| T-RISK-0029 | broken control references fail | fast | risk/test_validator.py | test_references_fail |
| T-RISK-0030 | PLANNED control without target_phase fails | fast | risk/test_validator.py | test_lifecycle_planned_without_target |
| T-RISK-0031 | PLANNED control with reached target_phase fails as overdue | fast | risk/test_validator.py | test_control_overdue_fail |
| T-RISK-0032 | VERIFIED control with unknown test id fails | fast | risk/test_validator.py | test_verified_with_unknown_test_id |
| T-RISK-0033 | risk without area or accountable fails | fast | risk/test_validator.py | test_risk_fields_fail |
| T-RISK-0034 | risk validate scales fails on invalid scales | fast | risk/test_scales.py | test_validate_scales_fails_on_bad_scales |
| T-RISK-0035 | check-phrases catches a known compliance-claim violation | fast | risk/test_policy.py | test_forbidden_phrase_detection_finds_violation |
| T-RUL-0001 | A boolean literal parses | fast | rules/test_T_RUL_0001_to_0014.py | test_T_RUL_0001_bool_literal_parses |
| T-RUL-0002 | An integer literal parses | fast | rules/test_T_RUL_0001_to_0014.py | test_T_RUL_0002_int_literal_parses |
| T-RUL-0003 | A decimal literal parses | fast | rules/test_T_RUL_0001_to_0014.py | test_T_RUL_0003_decimal_literal_parses |
| T-RUL-0004 | A string literal parses | fast | rules/test_T_RUL_0001_to_0014.py | test_T_RUL_0004_string_literal_parses |
| T-RUL-0005 | A field reference parses | fast | rules/test_T_RUL_0001_to_0014.py | test_T_RUL_0005_field_ref_parses |
| T-RUL-0006 | Boolean operators parse | fast | rules/test_T_RUL_0001_to_0014.py | test_T_RUL_0006_boolean_operands_parse |
| T-RUL-0007 | Comparison operators parse | fast | rules/test_T_RUL_0001_to_0014.py | test_T_RUL_0007_comparisons_parse |
| T-RUL-0008 | Decimal arithmetic operators parse | fast | rules/test_T_RUL_0001_to_0014.py | test_T_RUL_0008_arithmetic_parse |
| T-RUL-0009 | Set membership parses | fast | rules/test_T_RUL_0001_to_0014.py | test_T_RUL_0009_in_parses |
| T-RUL-0010 | Normalized string equality parses | fast | rules/test_T_RUL_0001_to_0014.py | test_T_RUL_0010_string_eq_parses |
| T-RUL-0011 | Date arithmetic parses | fast | rules/test_T_RUL_0001_to_0014.py | test_T_RUL_0011_date_arithmetic_parses |
| T-RUL-0012 | Quantifiers parse | fast | rules/test_T_RUL_0001_to_0014.py | test_T_RUL_0012_quantifiers_parse |
| T-RUL-0013 | Forbidden constructs rejected with stable error codes | fast | rules/test_T_RUL_0001_to_0014.py | test_T_RUL_0013_forbidden_constructs_rejected |
| T-RUL-0014 | Structural depth bound enforced | fast | rules/test_T_RUL_0001_to_0014.py | test_T_RUL_0014_depth_bound_enforced |
| T-RUL-0015 | Missing manifest field is rejected | fast | rules/test_T_RUL_0015_to_0026.py | test_T_RUL_0015_missing_manifest_field |
| T-RUL-0016 | Invalid window is rejected | fast | rules/test_T_RUL_0015_to_0026.py | test_T_RUL_0016_invalid_window |
| T-RUL-0017 | Rule without citation is rejected | fast | rules/test_T_RUL_0015_to_0026.py | test_T_RUL_0017_rule_without_citation |
| T-RUL-0018 | Rule without label is rejected | fast | rules/test_T_RUL_0015_to_0026.py | test_T_RUL_0018_rule_without_label |
| T-RUL-0019 | Declared label ceiling violation is rejected | fast | rules/test_T_RUL_0015_to_0026.py | test_T_RUL_0019_label_ceiling_violation |
| T-RUL-0020 | Overlapping windows without precedence rejected | fast | rules/test_T_RUL_0015_to_0026.py | test_T_RUL_0020_overlapping_no_precedence |
| T-RUL-0021 | Invalid condition expression rejected | fast | rules/test_T_RUL_0015_to_0026.py | test_T_RUL_0021_invalid_condition |
| T-RUL-0022 | Invalid outcome is rejected | fast | rules/test_T_RUL_0015_to_0026.py | test_T_RUL_0022_invalid_outcome |
| T-RUL-0023 | Valid pack loads with stable hash | fast | rules/test_T_RUL_0015_to_0026.py | test_T_RUL_0023_valid_pack_loads_stable_hash |
| T-RUL-0024 | Unknown citation source is rejected | fast | rules/test_T_RUL_0015_to_0026.py | test_T_RUL_0024_unknown_citation_source |
| T-RUL-0025 | Overlapping windows with precedence are accepted | fast | rules/test_T_RUL_0015_to_0026.py | test_T_RUL_0025_overlapping_with_precedence |
| T-RUL-0026 | Label at ceiling is accepted | fast | rules/test_T_RUL_0015_to_0026.py | test_T_RUL_0026_label_at_ceiling |
| T-RUL-0027 | Rule inside window is evaluated | fast | rules/test_T_RUL_0027_to_0042.py | test_T_RUL_0027_rule_inside_window |
| T-RUL-0028 | Rule outside window is skipped | fast | rules/test_T_RUL_0027_to_0042.py | test_T_RUL_0028_rule_outside_window |
| T-RUL-0029 | Window boundary inclusive at start | fast | rules/test_T_RUL_0027_to_0042.py | test_T_RUL_0029_window_boundary_start |
| T-RUL-0030 | Window boundary inclusive at end | fast | rules/test_T_RUL_0027_to_0042.py | test_T_RUL_0030_window_boundary_end |
| T-RUL-0031 | False condition gives NOT_APPLICABLE | fast | rules/test_T_RUL_0027_to_0042.py | test_T_RUL_0031_false_condition |
| T-RUL-0032 | Missing fact gives ABSTAIN | fast | rules/test_T_RUL_0027_to_0042.py | test_T_RUL_0032_missing_fact_abstain |
| T-RUL-0033 | Conflicted fact gives ESCALATE | fast | rules/test_T_RUL_0027_to_0042.py | test_T_RUL_0033_conflicted_fact_escalate |
| T-RUL-0034 | PROPOSED fact is not read | fast | rules/test_T_RUL_0027_to_0042.py | test_T_RUL_0034_proposed_fact_not_read |
| T-RUL-0035 | Decimal arithmetic uses Decimal | fast | rules/test_T_RUL_0027_to_0042.py | test_T_RUL_0035_decimal_arithmetic |
| T-RUL-0036 | Field condition matches | fast | rules/test_T_RUL_0027_to_0042.py | test_T_RUL_0036_field_condition_matches |
| T-RUL-0037 | Field condition does not match | fast | rules/test_T_RUL_0027_to_0042.py | test_T_RUL_0037_field_condition_no_match |
| T-RUL-0038 | Boolean operators evaluate correctly | fast | rules/test_T_RUL_0027_to_0042.py | test_T_RUL_0038_boolean_operators |
| T-RUL-0039 | Comparison operators evaluate correctly | fast | rules/test_T_RUL_0027_to_0042.py | test_T_RUL_0039_comparison_operators |
| T-RUL-0040 | Set membership evaluates correctly | fast | rules/test_T_RUL_0027_to_0042.py | test_T_RUL_0040_set_membership |
| T-RUL-0041 | Normalized string equality evaluates correctly | fast | rules/test_T_RUL_0027_to_0042.py | test_T_RUL_0041_string_eq_normalized |
| T-RUL-0042 | Multiple rules produce one result each | fast | rules/test_T_RUL_0027_to_0042.py | test_T_RUL_0042_multiple_rules |
| T-RUL-0043 | Byte-identical regeneration | fast | rules/differential/test_T_RUL_0043_to_0052.py | test_T_RUL_0043_byte_identical_regeneration |
| T-RUL-0044 | Both evaluators agree on simple boolean | fast | rules/differential/test_T_RUL_0043_to_0052.py | test_T_RUL_0044_agree_bool |
| T-RUL-0045 | Both evaluators agree on field access | fast | rules/differential/test_T_RUL_0043_to_0052.py | test_T_RUL_0045_agree_field |
| T-RUL-0046 | Both evaluators agree on comparisons | fast | rules/differential/test_T_RUL_0043_to_0052.py | test_T_RUL_0046_agree_comparison |
| T-RUL-0047 | Both evaluators agree on arithmetic | fast | rules/differential/test_T_RUL_0043_to_0052.py | test_T_RUL_0047_agree_arithmetic |
| T-RUL-0048 | Both evaluators agree on boolean operators | fast | rules/differential/test_T_RUL_0043_to_0052.py | test_T_RUL_0048_agree_boolean |
| T-RUL-0049 | Differential test on random fact sets | fast | rules/differential/test_T_RUL_0043_to_0052.py | test_T_RUL_0049_differential_random_1000 |
| T-RUL-0050 | Both evaluators agree on set membership | fast | rules/differential/test_T_RUL_0043_to_0052.py | test_T_RUL_0050_agree_in |
| T-RUL-0051 | Both evaluators agree on normalized string equality | fast | rules/differential/test_T_RUL_0043_to_0052.py | test_T_RUL_0051_agree_string_eq |
| T-RUL-0052 | Generated evaluator is marked | fast | rules/differential/test_T_RUL_0043_to_0052.py | test_T_RUL_0052_generated_marked |
| T-RUL-0053 | Combination takes the most severe | fast | rules/test_T_RUL_0053_to_0062.py | test_T_RUL_0053_most_severe |
| T-RUL-0054 | Combination keeps all reasons | fast | rules/test_T_RUL_0053_to_0062.py | test_T_RUL_0054_keeps_all_reasons |
| T-RUL-0055 | Combination is order independent | fast | rules/test_T_RUL_0053_to_0062.py | test_T_RUL_0055_order_independent |
| T-RUL-0056 | ALLOW blocked with SECONDARY datum | fast | rules/test_T_RUL_0053_to_0062.py | test_T_RUL_0056_allow_blocked_with_secondary |
| T-RUL-0057 | ALLOW allowed with OFFICIAL datum | fast | rules/test_T_RUL_0053_to_0062.py | test_T_RUL_0057_allow_with_official |
| T-RUL-0058 | Unresolved conflict yields ESCALATE | fast | rules/test_T_RUL_0053_to_0062.py | test_T_RUL_0058_unresolved_conflict |
| T-RUL-0059 | Resolved conflict with precedence | fast | rules/test_T_RUL_0053_to_0062.py | test_T_RUL_0059_resolved_with_precedence |
| T-RUL-0060 | Empty results give ABSTAIN | fast | rules/test_T_RUL_0053_to_0062.py | test_T_RUL_0060_empty_results_abstain |
| T-RUL-0061 | ESCALATE citations collected | fast | rules/test_T_RUL_0053_to_0062.py | test_T_RUL_0061_escalate_citations |
| T-RUL-0062 | Combination is monotone | fast | rules/test_T_RUL_0053_to_0062.py | test_T_RUL_0062_monotone |
| T-RUL-0063 | Reordering facts leaves results unchanged | fast | rules/metamorphic/test_T_RUL_0063_to_0072.py | test_T_RUL_0063_reorder_facts |
| T-RUL-0064 | Renaming IDs leaves outcomes unchanged | fast | rules/metamorphic/test_T_RUL_0063_to_0072.py | test_T_RUL_0064_rename_ids |
| T-RUL-0065 | Adding a non-referenced fact leaves results unchanged | fast | rules/metamorphic/test_T_RUL_0063_to_0072.py | test_T_RUL_0065_add_non_referenced_fact |
| T-RUL-0066 | Shifting time within a window leaves results unchanged | fast | rules/metamorphic/test_T_RUL_0063_to_0072.py | test_T_RUL_0066_shift_time_within_window |
| T-RUL-0067 | Reordering rules does not change combined outcome | fast | rules/metamorphic/test_T_RUL_0063_to_0072.py | test_T_RUL_0067_reorder_rules |
| T-RUL-0068 | Boolean and is commutative | fast | rules/metamorphic/test_T_RUL_0063_to_0072.py | test_T_RUL_0068_and_commutative |
| T-RUL-0069 | Boolean or is commutative | fast | rules/metamorphic/test_T_RUL_0063_to_0072.py | test_T_RUL_0069_or_commutative |
| T-RUL-0070 | Double negation is identity | fast | rules/metamorphic/test_T_RUL_0063_to_0072.py | test_T_RUL_0070_double_negation |
| T-RUL-0071 | Eq is symmetric | fast | rules/metamorphic/test_T_RUL_0063_to_0072.py | test_T_RUL_0071_eq_symmetric |
| T-RUL-0072 | Performance budget for 200 facts | fast | rules/perf/test_T_RUL_0072_perf.py | test_T_RUL_0072_perf_budget_200_facts |
| T-RUL-0073 | Determinism under same seed | fast | rules/determinism/test_T_RUL_0073_to_0080.py | test_T_RUL_0073_same_seed_identical |
| T-RUL-0074 | Locale independence | fast | rules/determinism/test_T_RUL_0073_to_0080.py | test_T_RUL_0074_locale_independence |
| T-RUL-0075 | Time zone independence | fast | rules/determinism/test_T_RUL_0073_to_0080.py | test_T_RUL_0075_timezone_independence |
| T-RUL-0076 | Thread count independence | fast | rules/determinism/test_T_RUL_0073_to_0080.py | test_T_RUL_0076_thread_count_independence |
| T-RUL-0077 | Working directory independence | fast | rules/determinism/test_T_RUL_0073_to_0080.py | test_T_RUL_0077_cwd_independence |
| T-RUL-0078 | Insertion order independence | fast | rules/determinism/test_T_RUL_0073_to_0080.py | test_T_RUL_0078_insertion_order_independence |
| T-RUL-0079 | Subprocess determinism | fast | rules/determinism/test_T_RUL_0073_to_0080.py | test_T_RUL_0079_subprocess_determinism |
| T-RUL-0080 | Iteration order dependence is caught | fast | rules/determinism/test_T_RUL_0073_to_0080.py | test_T_RUL_0080_iteration_order_caught |
| T-RUL-0081 | pack new creates a skeleton | fast | packkit/test_T_RUL_0081_to_0100.py | test_T_RUL_0081_pack_new_creates_skeleton |
| T-RUL-0082 | pack check validates a valid pack | fast | packkit/test_T_RUL_0081_to_0100.py | test_T_RUL_0082_pack_check_valid |
| T-RUL-0083 | pack check rejects an invalid pack | fast | packkit/test_T_RUL_0081_to_0100.py | test_T_RUL_0083_pack_check_invalid |
| T-RUL-0084 | pack explain shows rule details | fast | packkit/test_T_RUL_0081_to_0100.py | test_T_RUL_0084_pack_explain |
| T-RUL-0085 | pack explain fails for unknown rule | fast | packkit/test_T_RUL_0081_to_0100.py | test_T_RUL_0085_pack_explain_unknown |
| T-RUL-0086 | pack diff detects outcome change | fast | packkit/test_T_RUL_0081_to_0100.py | test_T_RUL_0086_pack_diff_outcome_change |
| T-RUL-0087 | pack diff reports no changes for identical packs | fast | packkit/test_T_RUL_0081_to_0100.py | test_T_RUL_0087_pack_diff_no_changes |
| T-RUL-0088 | pack simulate leaves the case chain untouched | fast | packkit/test_T_RUL_0081_to_0100.py | test_T_RUL_0088_pack_simulate_no_chain_change |
| T-RUL-0089 | pack provenance writes PROVENANCE.json | fast | packkit/test_T_RUL_0081_to_0100.py | test_T_RUL_0089_pack_provenance |
| T-RUL-0090 | pack provenance hash is stable | fast | packkit/test_T_RUL_0081_to_0100.py | test_T_RUL_0090_provenance_hash_stable |
| T-RUL-0091 | No kit command raises a label | fast | packkit/test_T_RUL_0081_to_0100.py | test_T_RUL_0091_no_label_change |
| T-RUL-0092 | No kit command sets a source to VERIFIED | fast | packkit/test_T_RUL_0081_to_0100.py | test_T_RUL_0092_no_source_status_change |
| T-RUL-0093 | Rule without firing fixture is reported | fast | packkit/test_T_RUL_0081_to_0100.py | test_T_RUL_0093_no_firing_fixture |
| T-RUL-0094 | Rule without non-firing fixture is reported | fast | packkit/test_T_RUL_0081_to_0100.py | test_T_RUL_0094_no_non_firing_fixture |
| T-RUL-0095 | Label above source ceiling is refused | fast | packkit/test_T_RUL_0081_to_0100.py | test_T_RUL_0095_label_ceiling_refused |
| T-RUL-0096 | Pack new creates an empty rules list | fast | packkit/test_T_RUL_0081_to_0100.py | test_T_RUL_0096_skeleton_empty_rules |
| T-RUL-0097 | Pack new creates an empty fixtures list | fast | packkit/test_T_RUL_0081_to_0100.py | test_T_RUL_0097_skeleton_empty_fixtures |
| T-RUL-0098 | pack check prints the label ceiling | fast | packkit/test_T_RUL_0081_to_0100.py | test_T_RUL_0098_check_prints_ceiling |
| T-RUL-0099 | pack provenance includes source ids | fast | packkit/test_T_RUL_0081_to_0100.py | test_T_RUL_0099_provenance_includes_sources |
| T-RUL-0100 | pack diff with version change exits 0 | fast | packkit/test_T_RUL_0081_to_0100.py | test_T_RUL_0100_diff_with_version_change |
| T-SEC-0001 | Token never stored in clear | fast | security/test_T_SEC_0001_to_0016.py | test_T_SEC_0001_token_never_stored_in_clear |
| T-SEC-0002 | Expired token fails | fast | security/test_T_SEC_0001_to_0016.py | test_T_SEC_0002_expired_token_fails |
| T-SEC-0003 | Revoked token fails | fast | security/test_T_SEC_0001_to_0016.py | test_T_SEC_0003_revoked_token_fails |
| T-SEC-0004 | Forged tenant in body ignored | fast | security/test_T_SEC_0001_to_0016.py | test_T_SEC_0004_forged_tenant_body_ignored |
| T-SEC-0005 | Forged tenant in header ignored | fast | security/test_T_SEC_0001_to_0016.py | test_T_SEC_0005_forged_tenant_header_ignored |
| T-SEC-0006 | Forged tenant in path ignored | fast | security/test_T_SEC_0001_to_0016.py | test_T_SEC_0006_forged_tenant_path_ignored |
| T-SEC-0007 | Forged tenant in claims ignored | fast | security/test_T_SEC_0001_to_0016.py | test_T_SEC_0007_forged_tenant_claims_ignored |
| T-SEC-0008 | Platform role has no tenant | fast | security/test_T_SEC_0001_to_0016.py | test_T_SEC_0008_platform_role_no_tenant |
| T-SEC-0009 | Platform denied tenant-scoped routes | fast | security/test_T_SEC_0001_to_0016.py | test_T_SEC_0009_platform_denied_tenant_routes |
| T-SEC-0010 | Platform reaches deployment routes | fast | security/test_T_SEC_0001_to_0016.py | test_T_SEC_0010_platform_reaches_deployment_routes |
| T-SEC-0011 | Viewer accesses tenant routes | fast | security/test_T_SEC_0001_to_0016.py | test_T_SEC_0011_viewer_can_access |
| T-SEC-0012 | Operator accesses tenant routes | fast | security/test_T_SEC_0001_to_0016.py | test_T_SEC_0012_operator_can_access |
| T-SEC-0013 | Reviewer can approve | fast | security/test_T_SEC_0001_to_0016.py | test_T_SEC_0013_reviewer_can_approve |
| T-SEC-0014 | Administrator can operate | fast | security/test_T_SEC_0001_to_0016.py | test_T_SEC_0014_administrator_can_operate |
| T-SEC-0015 | Session cookie signed | fast | security/test_T_SEC_0001_to_0016.py | test_T_SEC_0015_session_cookie_signed |
| T-SEC-0016 | Tampered cookie fails | fast | security/test_T_SEC_0001_to_0016.py | test_T_SEC_0016_tampered_cookie_fails |
| T-SEC-0017 | Ciphertext differs per tenant | fast | security/test_T_SEC_0017_to_0030.py | test_T_SEC_0017_ciphertext_differs_per_tenant |
| T-SEC-0018 | Cross-tenant decrypt fails | fast | security/test_T_SEC_0017_to_0030.py | test_T_SEC_0018_cross_tenant_decrypt_fails |
| T-SEC-0019 | Encrypt-decrypt round-trip | fast | security/test_T_SEC_0017_to_0030.py | test_T_SEC_0019_encrypt_decrypt_roundtrip |
| T-SEC-0020 | Erased payloads unrecoverable | fast | security/test_T_SEC_0017_to_0030.py | test_T_SEC_0020_erased_payloads_unrecoverable |
| T-SEC-0021 | Erasure recorded as event | fast | security/test_T_SEC_0017_to_0030.py | test_T_SEC_0021_erasure_recorded |
| T-SEC-0022 | Rotation keeps old records | fast | security/test_T_SEC_0017_to_0030.py | test_T_SEC_0022_rotation_keeps_old_records |
| T-SEC-0023 | Rotation default 90 days | fast | security/test_T_SEC_0017_to_0030.py | test_T_SEC_0023_rotation_default_90_days |
| T-SEC-0024 | Break-glass creates key | fast | security/test_T_SEC_0017_to_0030.py | test_T_SEC_0024_break_glass_creates_key |
| T-SEC-0025 | Break-glass disabled raises | fast | security/test_T_SEC_0017_to_0030.py | test_T_SEC_0025_break_glass_disabled_raises |
| T-SEC-0026 | Wrong key size raises | fast | security/test_T_SEC_0017_to_0030.py | test_T_SEC_0026_wrong_key_size_raises |
| T-SEC-0027 | Decrypt wrong key size raises | fast | security/test_T_SEC_0017_to_0030.py | test_T_SEC_0027_decrypt_wrong_key_size_raises |
| T-SEC-0028 | Erased payload marked | fast | security/test_T_SEC_0017_to_0030.py | test_T_SEC_0028_erased_payload_marked |
| T-SEC-0029 | Is erased after erasure | fast | security/test_T_SEC_0017_to_0030.py | test_T_SEC_0029_is_erased_after_erasure |
| T-SEC-0030 | Encrypt without key raises | fast | security/test_T_SEC_0017_to_0030.py | test_T_SEC_0030_encrypt_without_key_raises |
| T-SEC-0031 | Ceremony generates keys | fast | security/test_T_SEC_0031_to_0042.py | test_T_SEC_0031_ceremony_generates_keys |
| T-SEC-0032 | Keys are 32 bytes | fast | security/test_T_SEC_0031_to_0042.py | test_T_SEC_0032_ceremony_keys_are_32_bytes |
| T-SEC-0033 | Erasure drill passes | fast | security/test_T_SEC_0031_to_0042.py | test_T_SEC_0033_erasure_drill_passes |
| T-SEC-0034 | Rotation drill passes | fast | security/test_T_SEC_0031_to_0042.py | test_T_SEC_0034_rotation_drill_passes |
| T-SEC-0035 | Env store reads secret | fast | security/test_T_SEC_0031_to_0042.py | test_T_SEC_0035_env_store_reads_secret |
| T-SEC-0036 | Missing secret raises | fast | security/test_T_SEC_0031_to_0042.py | test_T_SEC_0036_missing_secret_raises |
| T-SEC-0037 | File store reads secret | fast | security/test_T_SEC_0031_to_0042.py | test_T_SEC_0037_file_store_reads_secret |
| T-SEC-0038 | Has returns False for missing | fast | security/test_T_SEC_0031_to_0042.py | test_T_SEC_0038_store_has_returns_false |
| T-SEC-0039 | Has returns True for present | fast | security/test_T_SEC_0031_to_0042.py | test_T_SEC_0039_store_has_returns_true |
| T-SEC-0040 | List keys returns names only | fast | security/test_T_SEC_0031_to_0042.py | test_T_SEC_0040_list_keys_no_values |
| T-SEC-0041 | Ceremony verify keys | fast | security/test_T_SEC_0031_to_0042.py | test_T_SEC_0041_ceremony_verify_keys |
| T-SEC-0042 | Drill result name | fast | security/test_T_SEC_0031_to_0042.py | test_T_SEC_0042_drill_result_name |
| T-SEC-0043 | Config changes on chain | fast | security/test_T_SEC_0043_to_0052.py | test_T_SEC_0043_config_changes_on_chain |
| T-SEC-0044 | Overlay cannot remove deployment | fast | security/test_T_SEC_0043_to_0052.py | test_T_SEC_0044_overlay_cannot_remove_deployment |
| T-SEC-0045 | Frozen tenant rejects commands | fast | security/test_T_SEC_0043_to_0052.py | test_T_SEC_0045_frozen_tenant_rejects |
| T-SEC-0046 | Unfrozen tenant accepts commands | fast | security/test_T_SEC_0043_to_0052.py | test_T_SEC_0046_unfrozen_tenant_accepts |
| T-SEC-0047 | Widening without platform refused | fast | security/test_T_SEC_0043_to_0052.py | test_T_SEC_0047_widening_without_platform_refused |
| T-SEC-0048 | Widening with platform succeeds | fast | security/test_T_SEC_0043_to_0052.py | test_T_SEC_0048_widening_with_platform_succeeds |
| T-SEC-0049 | Profile change on chain | fast | security/test_T_SEC_0043_to_0052.py | test_T_SEC_0049_profile_change_on_chain |
| T-SEC-0050 | No profile no external provider | fast | security/test_T_SEC_0043_to_0052.py | test_T_SEC_0050_no_profile_no_external |
| T-SEC-0051 | Freeze event on chain | fast | security/test_T_SEC_0043_to_0052.py | test_T_SEC_0051_freeze_event_on_chain |
| T-SEC-0052 | Overlay addition on chain | fast | security/test_T_SEC_0043_to_0052.py | test_T_SEC_0052_overlay_addition_on_chain |
| T-SEC-0053 | No write outside write path | fast | security/test_T_SEC_0053_to_0068.py | test_T_SEC_0053_no_write_outside_write_path |
| T-SEC-0054 | Model never writes memory | fast | security/test_T_SEC_0053_to_0068.py | test_T_SEC_0054_model_never_writes |
| T-SEC-0055 | Kernel write succeeds | fast | security/test_T_SEC_0053_to_0068.py | test_T_SEC_0055_kernel_write_succeeds |
| T-SEC-0056 | M3 never ALLOW | fast | security/test_T_SEC_0053_to_0068.py | test_T_SEC_0056_m3_never_allow |
| T-SEC-0057 | K-threshold enforced | fast | security/test_T_SEC_0053_to_0068.py | test_T_SEC_0057_k_threshold_enforced |
| T-SEC-0058 | Aggregate above threshold | fast | security/test_T_SEC_0053_to_0068.py | test_T_SEC_0058_aggregate_above_threshold |
| T-SEC-0059 | Expired entries tombstoned | fast | security/test_T_SEC_0053_to_0068.py | test_T_SEC_0059_expired_entries_tombstoned |
| T-SEC-0060 | Unexpired not tombstoned | fast | security/test_T_SEC_0053_to_0068.py | test_T_SEC_0060_unexpired_not_tombstoned |
| T-SEC-0061 | Quarantined excluded from reads | fast | security/test_T_SEC_0053_to_0068.py | test_T_SEC_0061_quarantined_excluded |
| T-SEC-0062 | Poisoning rejected | fast | security/test_T_SEC_0053_to_0068.py | test_T_SEC_0062_poisoning_rejected |
| T-SEC-0063 | M3 ALLOW raises | fast | security/test_T_SEC_0053_to_0068.py | test_T_SEC_0063_m3_allow_raises |
| T-SEC-0064 | Entry has required fields | fast | security/test_T_SEC_0053_to_0068.py | test_T_SEC_0064_entry_has_required_fields |
| T-SEC-0065 | Tombstone fields | fast | security/test_T_SEC_0053_to_0068.py | test_T_SEC_0065_tombstone_fields |
| T-SEC-0066 | K-threshold default 5 | fast | security/test_T_SEC_0053_to_0068.py | test_T_SEC_0066_k_threshold_default_5 |
| T-SEC-0067 | External source rejected | fast | security/test_T_SEC_0053_to_0068.py | test_T_SEC_0067_external_source_rejected |
| T-SEC-0068 | List tenant scoped | fast | security/test_T_SEC_0053_to_0068.py | test_T_SEC_0068_list_tenant_scoped |
| T-SEC-0069 | API foreign principal denied | fast | leakage/test_T_SEC_0069_to_0084.py | test_T_SEC_0069_api_foreign_principal_denied |
| T-SEC-0070 | API forged tenant body | fast | leakage/test_T_SEC_0069_to_0084.py | test_T_SEC_0070_api_forged_tenant_body |
| T-SEC-0071 | Repo foreign tenant read | fast | leakage/test_T_SEC_0069_to_0084.py | test_T_SEC_0071_repo_foreign_tenant_read |
| T-SEC-0072 | Repo forged tenant path | fast | leakage/test_T_SEC_0069_to_0084.py | test_T_SEC_0072_repo_forged_tenant_path |
| T-SEC-0073 | Cache tenant isolation | fast | leakage/test_T_SEC_0069_to_0084.py | test_T_SEC_0073_cache_tenant_isolation |
| T-SEC-0074 | Cache key collision | fast | leakage/test_T_SEC_0069_to_0084.py | test_T_SEC_0074_cache_key_collision |
| T-SEC-0075 | Ledger foreign decrypt | fast | leakage/test_T_SEC_0069_to_0084.py | test_T_SEC_0075_ledger_foreign_decrypt |
| T-SEC-0076 | Export tenant scoped | fast | leakage/test_T_SEC_0069_to_0084.py | test_T_SEC_0076_export_tenant_scoped |
| T-SEC-0077 | Log no tenant reveal | fast | leakage/test_T_SEC_0069_to_0084.py | test_T_SEC_0077_log_no_tenant_reveal |
| T-SEC-0078 | Timing oracle | fast | leakage/test_T_SEC_0069_to_0084.py | test_T_SEC_0078_timing_oracle |
| T-SEC-0079 | Error text oracle | fast | leakage/test_T_SEC_0069_to_0084.py | test_T_SEC_0079_error_text_oracle |
| T-SEC-0080 | Zero leaks all surfaces | fast | leakage/test_T_SEC_0069_to_0084.py | test_T_SEC_0080_zero_leaks_all_surfaces |
| T-SEC-0081 | Seeded uncovered surface fails | fast | leakage/test_T_SEC_0069_to_0084.py | test_T_SEC_0081_seeded_uncovered_surface_fails |
| T-SEC-0082 | Policy as application role | fast | leakage/test_T_SEC_0069_to_0084.py | test_T_SEC_0082_policy_as_application_role |
| T-SEC-0083 | Frozen tenant blocks | fast | leakage/test_T_SEC_0069_to_0084.py | test_T_SEC_0083_frozen_tenant_blocks |
| T-SEC-0084 | Tenant config isolation | fast | leakage/test_T_SEC_0069_to_0084.py | test_T_SEC_0084_tenant_config_isolation |
| T-SEC-0085 | No unmapped except deferred | fast | security/test_T_SEC_0085_to_0092.py | test_T_SEC_0085_no_unmapped_except_deferred |
| T-SEC-0086 | Seeded unmapped fails | fast | security/test_T_SEC_0085_to_0092.py | test_T_SEC_0086_seeded_unmapped_fails |
| T-SEC-0087 | Supply chain mapped to gates | fast | security/test_T_SEC_0085_to_0092.py | test_T_SEC_0087_supply_chain_mapped |
| T-SEC-0088 | Hostile files deferred to P14 | fast | security/test_T_SEC_0085_to_0092.py | test_T_SEC_0088_hostile_files_deferred |
| T-SEC-0089 | Deferred items name a phase | fast | security/test_T_SEC_0085_to_0092.py | test_T_SEC_0089_deferred_items_name_phase |
| T-SEC-0090 | Catalog JSON matches Python | fast | security/test_T_SEC_0085_to_0092.py | test_T_SEC_0090_catalog_json_matches |
| T-SEC-0091 | All new items covered | fast | security/test_T_SEC_0085_to_0092.py | test_T_SEC_0091_all_new_items_covered |
| T-SEC-0092 | Deferred items non-empty | fast | security/test_T_SEC_0085_to_0092.py | test_T_SEC_0092_deferred_items_nonempty |
| T-VAL-0001 | Consensus feeds both judgments | fast | pairs/test_valuation_classification.py | test_T_VAL_0001_consensus_feeds_both_judgments |
| T-VAL-0002 | Absent consensus causes both to abstain | fast | pairs/test_valuation_classification.py | test_T_VAL_0002_absent_consensus_causes_both_to_abstain |
| T-VAL-0003 | Description change marks both stale and recomputes | fast | pairs/test_valuation_classification.py | test_T_VAL_0003_description_change_marks_both_stale_and_recomputes |
| T-VAL-0004 | Secondary reference cannot allow | fast | pairs/test_valuation_classification.py | test_T_VAL_0004_secondary_reference_cannot_allow |
| T-VAL-0005 | Secondary tariff cannot allow | fast | pairs/test_valuation_classification.py | test_T_VAL_0005_secondary_tariff_cannot_allow |
| T-VAL-0006 | Secondary tariff contributes to skeleton decision | fast | pairs/test_valuation_classification.py | test_T_VAL_0006_secondary_tariff_contributes_to_skeleton_decision |
| T-VAL-0007 | Secondary reference contributes to skeleton decision | fast | pairs/test_valuation_classification.py | test_T_VAL_0007_secondary_reference_contributes_to_skeleton_decision |
| T-VAL-0008 | Both allow on synthetic consensus and replay | fast | pairs/test_valuation_classification.py | test_T_VAL_0008_both_allow_on_synthetic_consensus_and_replay |
| T-VAL-0009 | Judgment records are in the case chain | fast | pairs/test_valuation_classification.py | test_T_VAL_0009_judgment_records_are_in_the_case_chain |
| T-VAL-0010 | Agreed exact quantity reaches the judge | fast | pairs/test_valuation_classification.py | test_T_VAL_0010_agreed_exact_quantity_reaches_the_judge |
| T-VAL-0011 | Missing description is not inferred | fast | pairs/test_valuation_classification.py | test_T_VAL_0011_missing_description_is_not_inferred |
| T-VAL-0012 | Conflicting line codes are not canonical | fast | pairs/test_valuation_classification.py | test_T_VAL_0012_conflicting_line_codes_are_not_canonical |
| T-VAL-0013 | Tenant boundary covers judgment evidence | fast | pairs/test_valuation_classification.py | test_T_VAL_0013_tenant_boundary_covers_judgment_evidence |
| T-VAL-0014 | Repeated workflows commit to identical judgments | fast | pairs/test_valuation_classification.py | test_T_VAL_0014_repeated_workflows_commit_to_identical_judgments |
| T-VAL-0015 | Two judgments meet the deterministic budget | fast | pairs/test_valuation_classification.py | test_T_VAL_0015_two_judgments_meet_the_deterministic_budget |
| T-VAL-0016 | Cli evaluates the synthetic shipment | fast | pairs/test_valuation_classification.py | test_T_VAL_0016_cli_evaluates_the_synthetic_shipment |
