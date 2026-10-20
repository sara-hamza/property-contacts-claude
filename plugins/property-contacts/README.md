# Property & Building Contacts (Claude plugin)

Give Claude an address and it returns:
- **Part A:** businesses at the address (name, ABN, phone, email/contact form, website).
- **Part B:** building management (onsite building manager, strata / owners corporation manager, commercial property manager, leasing agent, facilities manager).

Every contact is cited and scored High / Medium / Low confidence. The plugin also recommends who to contact first and lists the gaps.

## Contents
- `skills/property-contact-lookup`: the research workflow (triggers automatically on address / building-manager questions).
- `skills/property-contact-lookup/references/report-template.md`: the output and CSV format.
- `commands/property-contacts.md`: `/property-contacts <address> [businesses|manager|both] [purpose]` (Claude Code).

## Requirements
Needs a web research tool (web search/fetch, a browser, or Bright Data / Firecrawl). Without one, the skill returns a manual search plan instead of guessing.

## Boundaries
Uses only public, business-published, role-based contact details. No personal mobiles, residents, owners or data-broker sources. Read-only: it never calls, emails or submits forms. Independent prototype, not affiliated with Opticomm.
