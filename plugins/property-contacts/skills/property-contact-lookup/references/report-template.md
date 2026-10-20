# Report template: Property & Building Contacts

Start with one or two sentences that give the answer: who to contact first, and how confident you are.

## Address summary
- **Input address:** <as given>
- **Confirmed address:** <normalised> · **Building name:** <name / none>
- **Alternative / corner addresses:** <e.g. 96–100 King William St / none>
- **Property type:** <residential strata | commercial office | retail | industrial | mixed-use | greenfield lot>
- **Parts (mixed-use only):** <e.g. retail podium at 28 Broadway; West tower at 2 Chippendale Way>
- **Strata / plan number:** <e.g. SP87881 (1 source) / not found>
- **Geocode:** <exact | approximate (suburb-level)>
- **Researched on:** <YYYY-MM-DD>

## Part A: Businesses at this address
| # | Business | Unit/Level | Category | Phone | Email / contact form | Website | Hours | Confidence | Notes / flags | Sources |
|---|---|---|---|---|---|---|---|---|---|---|

Flags: `next door` · `snippet only` · `OSM only` · `Permanently closed` · `Moved`

## Part B: Building management
| # | Part | Role | Company | Published contact name & title | Phone | Email / enquiry form | Office address | Confidence | Source last seen | Notes / flags | Sources |
|---|---|---|---|---|---|---|---|---|---|---|---|

Roles: Onsite building / operations manager · Strata / owners corporation / body corporate manager · Commercial property manager · Facilities manager · Leasing agent · Owner / asset manager · Developer project team · Developer sales centre · Builders' portal / design review · Council · Community corporation.

## Part C: Site access and security
| # | Item | Detail | Contact (phone / email / form) | Hours | Confidence | Notes / flags | Sources |
|---|---|---|---|---|---|---|---|

Items: Onsite security / security control room · Concierge · After-hours / emergency line · Loading dock & booking · Contractor induction (link) · Sign-in / access cards / escort · Usual paperwork (insurance, SWMS) · Contracted security provider (only if publicly named for this site).

Never include rosters, shift times, camera locations, patrol routes, codes or access weak points.

## Recommended first contact
<Who to contact first for the stated purpose (access authority first, then confidence), and why. A backup contact. Then the access steps on the day, from Part C, e.g. "book via B1, complete the induction (C4), sign in at the security desk (C1)".>

## Gaps and how to confirm
- <What wasn't found> → <exact next step, e.g. "Landata OC search for PS437659 (paid, user to order)">

## Sources
1. <Title> — <URL> (accessed <date>; mark *snippet only* / *stale* where relevant)

Map data © OpenStreetMap contributors, where used.

## Appendix: search plan (only if a lookup couldn't be completed)
1. <query or site> — <what it should show>

---
### CSV columns (batch mode)
`input_address,confirmed_address,component,section (A/B/C),role_or_category,organisation,unit_level,contact_name,phone,email_or_form,website,confidence,flags,source_urls,source_date,notes`
