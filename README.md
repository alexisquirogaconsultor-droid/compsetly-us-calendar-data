# Compsetly independent calendar data

Three small, source-linked datasets compiled independently by Compsetly. The
CSV and iCalendar files are copied byte for byte from the publisher's existing
public assets. Their original timestamps remain unchanged. This repository is
a dated snapshot, not an official feed or a live subscription.

Browse the [Compsetly data catalog](https://trends.compsetly.com/data-catalog/).

| Dataset | Included files | Canonical guide |
| --- | --- | --- |
| November 2026 SSI / Social Security payment cycles | Five-row CSV and five separate one-cycle calendars | [Assigned-cycle dates and calendars](https://trends.compsetly.com/ssi-payment-dates-2026/) |
| Mexico GP 2026 time conversions | Two-row CSV and a calendar containing qualifying and race sessions | [US clock change, qualifying and race](https://trends.compsetly.com/mexico-gp-2026-start-time-us-daylight-saving/) |
| Three 2027 service-calendar differences | Three-row OPM / Federal Reserve / NYSE comparison and three all-day reminders | [Observed dates and service differences](https://trends.compsetly.com/federal-holidays-2027-observed-calendar-ics/#calendar-differences) |


## Download the included files

| Dataset | Files |
| --- | --- |
| SSI and Social Security payment cycles | [ssi-november-payment-cycles.csv](ssi-november-payment-cycles.csv); [social-security-fourth-wednesday-november-2026.ics](social-security-fourth-wednesday-november-2026.ics); [social-security-second-wednesday-november-2026.ics](social-security-second-wednesday-november-2026.ics); [social-security-third-day-november-2026.ics](social-security-third-day-november-2026.ics); [social-security-third-wednesday-november-2026.ics](social-security-third-wednesday-november-2026.ics); [ssi-november-2026.ics](ssi-november-2026.ics) |
| Mexico GP starts across the US clock change | [mexico-gp-2026-times.csv](mexico-gp-2026-times.csv); [mexico-gp-2026.ics](mexico-gp-2026.ics) |
| Three 2027 holiday-calendar differences | [holiday-differences-2027.csv](holiday-differences-2027.csv); [holiday-differences-2027.ics](holiday-differences-2027.ics) |

## Scope

**SSI and Social Security.** The SSI November benefit is scheduled for October
30, 2026. The other rows describe assigned Social Security payment cycles in
November; they do not determine an individual's cycle or bank posting time.
Read the SSA exceptions before selecting a calendar. No personal benefit,
identity or bank information is included or needed.

**Mexico GP.** Each scheduled session has its own UTC start, so the US clock
change between qualifying and the race is represented correctly. Columns
include Mexico City, Eastern, Central, Mountain, Pacific, Phoenix, Honolulu and
Anchorage. Phoenix is a location, not a rule for all Arizona; Anchorage is not a
rule for all Alaska. Times are scheduled and subject to changes. The race end
is the published session window, not a prediction of its actual finish.

**Service calendars.** Only June 18, December 24 and December 31, 2027 are
compared. The rows distinguish most Monday-Friday federal employees, Federal
Reserve Banks and Branches, the Board of Governors and NYSE's holiday calendar.
This is not a complete closure calendar, a schedule of private bank branches,
a FedACH schedule or a market operating-hours guide. December 31 concerns the
observance of New Year's Day 2028.

## Sources and timestamps

The machine-readable [release manifest](release-manifest.json) records each
canonical page, included asset, SHA-256 checksum, original source URL, scope
and existing check/conversion timestamp. `checked_utc`, `reviewed_utc`,
`conversion_updated_utc` and calendar `DTSTAMP` values retain their distinct
meanings. Preparing this repository did not recheck or reset the schedules.

- Payment rules: [SSA Handbook section 121](https://www.ssa.gov/OP_Home/handbook/handbook.01/handbook-0121.html).
- Federal observances: [OPM federal holidays](https://www.opm.gov/policy-data-oversight/pay-leave/federal-holidays/).
- Race sessions: [F1 Mexico 2026 timetable](https://www.formula1.com/en/latest/article/formula-1-gran-premio-de-la-ciudad-de-mexico-2026.14b3wTWzNNLJ5Wd8cG7HCQ).
- US clock change: [NIST daylight-saving rules](https://www.nist.gov/pml/time-and-frequency-division/popular-links/daylight-saving-time-dst).
- Institution differences: [Federal Reserve holiday policy](https://www.federalreserve.gov/aboutthefed/k8.htm) and [NYSE hours and calendars](https://www.nyse.com/trade/hours-calendars).

## Verify locally

Use Python 3.10 or later; no additional packages, credentials or network access
are required:

```sh
python verify_release.py
```

The command checks every listed checksum, the three expected datasets, CSV row
counts, calendar event counts, date/UTC alignment, exclusive all-day ends and
duplicate event UIDs. For the Mexico CSV it checks the displayed clock
arithmetic using the abbreviations recorded in this snapshot. This is an
integrity and consistency check, not a new source review or a complete RFC
5545 validator.

To compare the copied files with an existing local public-root directory:

```sh
python verify_release.py --source-root /path/to/public/root
```

The script prints its result and does not change any data or contact external
services. A nonzero exit code indicates failure. The printed verification time
describes the local check, not a new publication or source-review date.

This repository uses a flat layout. The three CSV files and seven ICS files have unique filenames, and the manifest maps each file to its canonical public download. No local source directory is required to run the verifier.

## Attribution and rights

Please attribute this independent compilation to Compsetly, link the canonical
guide, and retain the responsible publisher's source citation for factual
claims. [CITATION.cff](CITATION.cff) supplies dataset citation metadata; its JSON
format is also a valid YAML 1.2 subset.

Compsetly is not SSA, OPM, the Federal Reserve, NYSE, F1 or NIST. No affiliation,
endorsement, DOI or blanket reuse license is asserted. Source attribution does
not grant rights to third-party material. See [RIGHTS.md](RIGHTS.md).
