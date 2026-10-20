---
description: Find business contacts and the building / strata manager for an address
argument-hint: "<address>  [businesses|manager|both]  [purpose]"
---

Use the `property-contact-lookup` skill on this request: $ARGUMENTS

If no address was given, ask for one (street, suburb, state, postcode). Default the scope to "both". Return the report in the skill's template format, with sources and confidence for every contact.
