# Test Index

| id | title | level | file | function |
|---|---|---|---|---|
| T-BASELINE-0001 | Empty baselines are seeded with the measured floor | fast | gate/test_baseline.py | test_update_baselines_seeds_empty |
| T-BASELINE-0002 | A higher measured value ratchets the floor up | fast | gate/test_baseline.py | test_update_baselines_ratchets_up |
| T-BASELINE-0003 | A lowered measured value is rejected and the floor is kept | fast | gate/test_baseline.py | test_update_baselines_rejects_decrease |
| T-BASELINE-0004 | Mixed measured values keep the improved key and reject the decreased one | fast | gate/test_baseline.py | test_update_baselines_mixed_up_and_down |
| T-BASELINE-0005 | check_baseline_decrease flags a lowered value | fast | gate/test_baseline.py | test_check_baseline_decrease_flags_and_clears |
| T-BASELINE-0006 | baselines.json validates against its schema | fast | gate/test_baseline.py | test_baselines_schema_valid_and_invalid |
| T-BASELINE-0007 | A missing measured component reports a decrease | fast | gate/test_baseline.py | test_check_baseline_decrease_missing_component |
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
| T-DOCS-0001 | A missing honesty line makes the docs gate fail | fast | gate/test_docs.py | test_missing_honesty_line_fails |
| T-DOCS-0002 | A fenced code block makes the docs gate fail | fast | gate/test_docs.py | test_code_block_fails |
| T-DOCS-0003 | A Build Progress row count mismatch makes the docs gate fail | fast | gate/test_docs.py | test_row_mismatch_fails |
| T-DOCS-0004 | A broken local link makes the docs gate fail | fast | gate/test_docs.py | test_broken_link_fails |
| T-DOCS-0005 | A hand-edited tick in Build Progress makes the docs gate fail | fast | gate/test_docs.py | test_hand_edited_tick_fails |
| T-DOCS-0006 | A forbidden pattern in the README makes the docs gate fail | fast | gate/test_docs.py | test_forbidden_pattern_fails |
| T-DOCS-LINKS | check_links skips http, https and anchor links | fast | gate/test_docs.py | test_check_links_skips_external_and_anchor |
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
