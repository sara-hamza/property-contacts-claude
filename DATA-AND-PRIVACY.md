# Data sources, licences and privacy

## Sources used by the MCP server
| Source | Used for | Licence / terms | Notes |
|---|---|---|---|
| [OpenStreetMap](https://www.openstreetmap.org/copyright) via [Nominatim](https://operations.osmfoundation.org/policies/nominatim/) | Address normalisation, geocoding | **© OpenStreetMap contributors, [ODbL 1.0](https://opendatacommons.org/licenses/odbl/)** | Max 1 request/second, identifying User-Agent, results cached. No bulk geocoding. |
| OpenStreetMap via [Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API) public instances | Businesses at a point | © OpenStreetMap contributors, ODbL 1.0 | Shared community servers; low volume only. |
| OpenStreetMap via [Photon](https://photon.komoot.io/) | Fallback business lookup | © OpenStreetMap contributors, ODbL 1.0 | Fair use. |

**Attribution:** reports that include OpenStreetMap-derived data must credit **"© OpenStreetMap contributors"**. The tools return this in their `source` field, and the skill cites it.

For high volumes (batches of hundreds of addresses or more), don't use the public community servers. Host your own Nominatim / Overpass, or use G-NAF / a commercial provider.

## Privacy model
- **Business and role contacts only.** The skill returns contact details only as businesses or management companies publish them for that role.
- **Never collected:** personal mobiles, home addresses, residents', owners' or lot purchasers' names, or data from people-search / data-broker sites.
- **No guessing:** email formats, phone numbers and plan numbers are never guessed.
- **Data flow:**
  - The server sends **only the address text or coordinates** to OpenStreetMap services.
  - Nothing is sent to the plugin author.
  - The local cache holds public lookup results only, in your user cache directory.
- **Read-only:** nothing is sent to the businesses found.

## Your obligations
- Contacting businesses found with this tool is your responsibility. Follow the **Privacy Act 1988 (Cth)** and the **Spam Act 2003 (Cth)** (consent, identification and unsubscribe rules for commercial electronic messages), and your organisation's policies.
- Results are leads, not verified records. Confirm before relying on them for contracts, access or legal notices.

This plugin is an independent community project, not affiliated with Opticomm, Uniti, Anthropic or the OpenStreetMap Foundation.
