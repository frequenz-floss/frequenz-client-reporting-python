# Frequenz Reporting API Client Release Notes

## Summary

This release introduces the initial version of the Reporting API client with support for
retrieving single metric historical data for a single component.

## Upgrading

<!-- Here goes notes on how to upgrade from previous versions, including deprecations and what they should be replaced with -->

## New Features

* Introducing the initial version of the Reporting API client, streamlined for
retrieving single metric historical data for a single component. It incorporates
pagination handling and utilizes a wrapper data class that retains the raw
protobuf response while offering transformation capabilities limited here
to generators of structured data representation via named tuples.

* Current limitations include a single metric focus with plans for extensibility,
ongoing development for states and bounds integration, as well as support for
service-side features like resampling, streaming, and formula aggregations.

* Code examples are provided to guide users through the basic usage of the client.


## Bug Fixes

<!-- Here goes notable bug fixes that are worth a special mention or explanation -->
