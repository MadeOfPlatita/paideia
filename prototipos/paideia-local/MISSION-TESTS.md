# Mission session offline regression

The guarded runner initially reported six failures and one pass for `tests/test_mission_session.py` (the full-suite baseline is recorded in `docs/ia-groq-estructurada/ejecuciones/20261102T233227/regression-first.json` at the workspace root). The failing cases used transports no longer accepted by the closed synthetic session contract, or GUI mocks incompatible with lazy imports. The repair changes test setup, not production.

Run with the offline guard (blocks native Tk construction and non-loopback socket operations):

```text
python scripts/run_offline_regression.py --json <writable-output.json> tests/test_mission_session.py
```

The guarded targeted run passes all seven `MissionSessionTests`:

- `test_cli_passes_fixed_mission_config_to_window_without_network`
- `test_closed_lock_revokes_active_session_before_any_send`
- `test_corrupt_ledger_revokes_on_status`
- `test_final_remaining_slot_revokes_key`
- `test_final_remaining_slot_survives_connect_and_auto_close`
- `test_transport_failure_consumes_persisted_reservation`
- `test_window_requires_separate_confirmation_and_button_for_benchmark`

The final-slot connect barrier and actual connection exception use the real counted HTTPS transport with `HTTPSConnection` replaced by a synthetic connection. A temporary mission directory, manifest lookup and clock are substituted to avoid touching an authorized ledger or depending on the wall clock. The failure asserts the sanitized transport error, call count and persisted reservation. Other injected test sessions use the exact closed `StructuredSessionFixture`. GUI tests use only manual widget doubles and verify separate authorization; no Tk interpreter is opened.

Limits: this run does not verify real TLS, an external provider, native Tk controls or real interactive button invocation. It is a targeted run, not a full-suite result. The runner excludes six native-Tk tests from a full run; see its explicit exclusion list.
