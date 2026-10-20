# Property & Building Contacts for Claude

[![CI](https://github.com/sara-hamza/property-contacts-claude/actions/workflows/ci.yml/badge.svg)](https://github.com/sara-hamza/property-contacts-claude/actions/workflows/ci.yml)

Give Claude an address. It returns:

- **Part A: businesses at the address.** Name, ABN and status, phone, email or contact form, website.
- **Part B: who manages the property.** Onsite building manager, strata / owners corporation managing agent, commercial property manager, leasing agent, facilities manager or, for greenfield estates, the developer and council.

Every contact comes with a **source link, date and High / Medium / Low confidence**. The report also gives a recommended first contact for your purpose (e.g. site access) and lists the gaps, each with a way to confirm it. Built for Australian addresses (ABN Lookup, NSW Strata Hub, state title registers); the method works elsewhere with local registers.

## Install

**Claude Code: as a plugin marketplace**
```
/plugin marketplace add sara-hamza/property-contacts-claude
/plugin install property-contacts@property-contacts-marketplace
```

**Claude Cowork (desktop)**
**Customize → Plugins → Add marketplace**, enter `sara-hamza/property-contacts-claude`, then install **property-contacts**. Or upload `property-contacts-plugin.zip`. In Cowork, run the command as `/property-contacts:property-contacts`.

**Claude.ai: upload as a skill or plugin**
Download the ZIPs from the [latest release](../../releases/latest):
- `property-contact-lookup-skill.zip`: upload under **Customize → Skills**
- `property-contacts-plugin.zip`: upload under **Customize → Plugins** (where available)

## Use
- Just ask: *"Who manages 100 King William St, Adelaide SA 5000? We need site access for a comms room survey."*
- Or, in Claude Code: `/property-contacts <address> [businesses|manager|both] [purpose]` (full name: `/property-contacts:property-contacts`)
- Restart Claude Code after installing or updating so the plugin loads.
- Batches: paste a list or CSV of addresses and ask for the CSV output.

Needs a web research tool (web search/fetch, a browser, or Bright Data / Firecrawl). Without one, the skill returns a manual search plan instead of guessing.

## Built-in data tools (local MCP server)
The plugin includes a small **local MCP server** (`property-data`), which starts automatically in Claude Code when the plugin is enabled. It gives the skill structured, read-only lookups, so it does fewer web searches:

| Tool | What it returns | Data source | Key needed |
|---|---|---|---|
| `normalise_address` | Lot / unit / level / number-range parsing, geocoded candidates with building name and coordinates, warnings (lot numbers, number ranges, approximate matches) | OpenStreetMap Nominatim | No |
| `businesses_at` | Named businesses mapped at a point, with neighbours flagged; phone, website and hours where mapped | OpenStreetMap via Overpass, falling back to Photon | No |
| `abn_search` | ABR name matches plus a single **safe** match, or "ambiguous" | ABR web services | `ABR_GUID` |
| `abn_details` | Entity name, status, type, GST, location, business names | ABR web services | `ABR_GUID` |

**Requirements:** [`uv`](https://docs.astral.sh/uv/). The server declares its own Python dependencies and `uv` installs them on first run, so there's no virtualenv to manage.

**ABN tools:** register free for an ABR web services GUID at https://abr.business.gov.au/Tools/WebServices, then add it to your shell profile and restart Claude Code:
```bash
export ABR_GUID="your-guid-here"
```
Without it, the ABN tools return a clear message and the skill falls back to ABN Lookup on the web.

**Optional:** `NOMINATIM_EMAIL` (a contact address sent to Nominatim, per its usage policy). `OVERPASS_URLS` (comma-separated Overpass servers, if you run your own).

**Speed:** with `businesses_at`, the first lookup in a session can take about 15 seconds while the server works out which public Overpass servers are up (they're often busy). Servers that fail are skipped for 15 minutes, and later lookups take about 1 second. Results are cached on disk (geocodes 30 days, businesses 7 days, ABN results 1 day) in `~/.cache/property-contacts-claude` (override with `PROPERTY_DATA_CACHE_DIR`).

**Fair use:** Nominatim is limited to 1 request per second and results are cached. These are free community services, so use them for one-off lookups, not bulk geocoding. For large batches, host your own Nominatim / Overpass, or use G-NAF.

**Evals:** `claude plugin eval plugins/property-contacts --mocks off --allow-tools WebSearch WebFetch "mcp__plugin_property-contacts_property-data__*" --runs 1` runs behavioural cases (strata access authority, private-home refusal, greenfield path) with and without the plugin.

**Tests:** `uv run --with pytest --with "mcp>=2.3,<2.4" --with "httpx>=0.27,<1" pytest plugins/property-contacts/mcp/tests -q`

**Which zip includes what:** `property-contacts-plugin.zip` contains the skill, the command **and** the data server. `property-contact-lookup-skill.zip` contains the skill only. The data server runs wherever local MCP servers can run (see Compatibility).

## Compatibility
| Feature | Claude Code | Cowork (local session) | Claude.ai chat |
|---|---|---|---|
| Skill (auto-triggers) | ✅ tested | ✅ documented | ✅ skill zip |
| `/property-contacts` command | ✅ tested | ✅ as `/property-contacts:property-contacts` | — |
| `property-data` MCP server | ✅ tested (needs `uv`) | ⚠️ not yet verified: runs only in local sessions, needs `uv` in the session VM, admins can disable local MCP | ❌ |
| Web research fallback | ✅ | ✅ web search / browser | ✅ if web search is on |

If the MCP server isn't available, the skill uses web research automatically. Results stay the same in kind; lookups are just slower.

## How it handles different properties
| Property type | Who "manages" it | Typical route |
|---|---|---|
| Commercial tower, single owner | Owner / asset manager → facilities manager | Owner's head office; building website lists leasing agents only |
| Strata / apartments | Licensed strata managing agent | Strata plan number → register → agent |
| Mixed-use precinct | A different manager per part (retail podium vs each tower) | Split by address; check for a Building Management Statement |
| Greenfield lot / new estate | Developer project team + council | Developer's state office, builders' portal, council |

Worked examples, one per type: [`examples/`](examples/).

## Boundaries
- **Public, role-based business contacts only.** No personal mobiles, residents, owners, lot purchasers or people-search / data-broker sources.
- **No guessing.** Email formats, phone numbers, ABNs and strata plan numbers are never guessed. Anything not found is marked *Not found*, with a next step.
- **Read-only.** It never calls, emails, submits forms or buys register searches for you.
- **Untrusted content.** Instructions embedded in web pages are ignored.

Independent community prototype, not affiliated with Opticomm, Uniti or Anthropic. Check your organisation's privacy and Spam Act obligations before contacting anyone.

## Layout
```
.claude-plugin/marketplace.json
plugins/property-contacts/
  .claude-plugin/plugin.json
  commands/property-contacts.md
  skills/property-contact-lookup/SKILL.md
  skills/property-contact-lookup/references/report-template.md
  .mcp.json                       # registers the local property-data server
  mcp/property_data_server.py     # MCP server (4 read-only tools)
  mcp/tests/test_offline.py
examples/            # three test-run reports
```

## Data, privacy and security
See [DATA-AND-PRIVACY.md](DATA-AND-PRIVACY.md) for sources, licences and **OpenStreetMap attribution**, and [SECURITY.md](SECURITY.md) for what the server can access and how to report issues. Release history: [CHANGELOG.md](CHANGELOG.md).

## License
MIT. Map data © OpenStreetMap contributors (ODbL).
