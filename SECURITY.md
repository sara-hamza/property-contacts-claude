# Security

## Reporting a vulnerability
Report security issues privately through GitHub's **[Report a vulnerability](../../security/advisories/new)** form on this repository. Please don't open a public issue. You should get a reply within 5 business days.

## What this plugin can and cannot do
- **The skill** is Markdown instructions. It runs no code of its own.
- **The MCP server** (`plugins/property-contacts/mcp/property_data_server.py`) runs locally as your user, over stdio. It:
  - makes **outbound HTTPS GET/POST requests only** to OpenStreetMap Nominatim, Overpass, Photon and the Australian Business Register;
  - exposes **four read-only tools** (annotated `readOnlyHint`). It never writes files, other than its cache in your user cache directory, and never sends messages, submits forms or makes purchases;
  - reads `ABR_GUID`, `NOMINATIM_EMAIL`, `OVERPASS_URLS`, `PHOTON_URL` and `PROPERTY_DATA_CACHE_DIR` from the environment;
  - **never returns `ABR_GUID`** in tool output or errors.
- **Third-party text is untrusted.** Business names and tags come from public, volunteer-edited data. The skill treats everything tools and web pages return as data, never as instructions.

## Hardening notes for organisations
- Change `OVERPASS_URLS` / `PHOTON_URL` only to servers you trust. The server will send coordinates to whatever endpoint you configure.
- Keep `ABR_GUID` in your secrets manager or shell profile, not in the repository.
- To run only the skill, without the local server, disable the `property-data` MCP server in Claude Code (`/mcp`) or ask admins to block local MCP. The skill falls back to web research.

## Supported versions
Only the latest release receives fixes.
