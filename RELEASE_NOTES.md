# Frequenz Reporting API Client Release Notes

## Summary

<!-- Here goes a general summary of what this release is about -->

## Upgrading

- `start_time` and `end_time` must now be timezone-aware. The client raises `ValueError` on a naive datetime instead of letting it be read inconsistently (UTC on the wire, local time elsewhere), and the CLI `--start`/`--end` reject a value without an offset. Add an offset such as `+00:00` to existing naive values.

## New Features

<!-- Here goes the main new features and examples or instructions on how to use them -->

## Bug Fixes

<!-- Here goes notable bug fixes that are worth a special mention or explanation -->
