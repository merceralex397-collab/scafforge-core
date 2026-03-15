# Host Adapter Contract

This directory separates **how a host runs Scafforge** from **what Scafforge generates**.

Core package responsibilities:

- normalize messy inputs
- render the OpenCode-oriented scaffold
- enforce the generated repo contract
- validate template and documentation consistency

Adapter responsibilities:

- explain installation for the host
- show the host-specific command that invokes the Scafforge package
- explain how the host should pass provider/model choices
- keep host-specific startup wording out of core generator docs

Use `adapters/manifest.json` as the machine-readable version of this split.
