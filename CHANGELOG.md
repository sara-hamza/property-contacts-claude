# Changelog

All notable changes to this plugin are listed here. Versions follow [Semantic Versioning](https://semver.org/).

## [1.2.0] - 2026-10-20
Production hardening.

### Added
- CI on every push and pull request: manifest validation, version consistency, skill frontmatter, offline tests, MCP stdio smoke test.
- Tag-driven release workflow, building plugin and skill zips with SHA-256 checksums.
- Behavioural eval suite (`evals/`) for `claude plugin eval`.
- `SECURITY.md`, `DATA-AND-PRIVACY.md` (sources, licences, attribution), this changelog.
- Cowork install notes.

### Changed
- MCP server: retries with backoff on rate limits and busy servers, a persistent on-disk cache, input-size limits, a pinned dependency range.
- README: corrected which zip includes the data server.

## [1.1.0] - 2026-10-20
### Added
- Local `property-data` MCP server with `normalise_address`, `businesses_at`, `abn_search` and `abn_details`. The skill uses these tools first, then web research.

## [1.0.1] - 2026-10-20
### Changed
- Per-state strata / owners corporation register guide.
- For residential strata, the owners corporation manager is ranked first for common-property access.
- ABN Lookup is mandatory; ambiguous matches are marked "not assigned".
- Obfuscated emails are no longer decoded.

## [1.0.0] - 2026-10-20
### Added
- `property-contact-lookup` skill, `/property-contacts` command, report template, worked examples.
