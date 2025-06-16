# Frequenz Reporting API Client Release Notes

## Summary

<!-- Here goes a general summary of what this release is about -->

## Upgrading

* The `key` parameter of the client has been renamed to `auth_key`

## New Features

* Add HMAC generation capabilities.
    * The new CLI option "sign_secret" can be used to provide the server's HMAC secret.
    * The client itself now has a "sign_secret" argument in the constructor.
    * Update documentation describing how to use the above options.

## Bug Fixes

<!-- Here goes notable bug fixes that are worth a special mention or explanation -->
