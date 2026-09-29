# Frequenz Reporting API Client Release Notes

## Summary

<!-- Here goes a general summary of what this release is about -->

## Upgrading

- `start_time` and `end_time` must now be timezone-aware. The client raises `ValueError` on a naive datetime instead of letting it be read inconsistently (UTC on the wire, local time elsewhere), and the CLI `--start`/`--end` reject a value without an offset. Add an offset such as `+00:00` to existing naive values.

## New Features

- The CLI now warns when `--end` is before `--start`. The request still runs, but the inverted range returns no data, so the warning flags what is almost always a typo.

## Bug Fixes

<!-- Here goes notable bug fixes that are worth a special mention or explanation -->
