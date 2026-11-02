# Frequenz Reporting API Client Release Notes

## Summary

<!-- Here goes a general summary of what this release is about -->

## Upgrading

- `start_time` and `end_time` must now be timezone-aware. The client raises `ValueError` on a naive datetime instead of letting it be read inconsistently (UTC on the wire, local time elsewhere), and the CLI `--start`/`--end` reject a value without an offset. Add an offset such as `+00:00` to existing naive values.

## New Features

- The CLI now rejects `--end` before `--start`.
- `reporting-cli` falls back to `FREQUENZ_API_KEY` and `FREQUENZ_API_SECRET` when neither `--auth_key` nor `--sign_secret` is given.

## Bug Fixes

<!-- Here goes notable bug fixes that are worth a special mention or explanation -->

* Implement `close()` on the receiver returned by the streaming methods, which raised `NotImplementedError` before.
