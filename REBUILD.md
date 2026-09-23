# Rebuilding First Ballot

Written for an LLM with a shell and no other context. Follow it in order.

## 1. What this is

A single HTML page about Primetime Emmy acting nominations, 1979 through the 78th Emmys
(September 14, 2026). It regroups a messy source CSV into twelve categories — Lead/Supporting
x Actor/Actress x Drama/Comedy/Limited-or-Movie — and tracks every person's nomination history
in each one they were up for.

The finding it exists to show: **72.5% of the 1,573 acting careers in these categories since
1979 never won the category, not once. Of the 27% who did eventually win, 68.1% won on their
very first nomination.** A second or third nomination doesn't raise anyone's odds — the
distribution just collapses (294 first-nomination wins, 76 second, 32 third, 18 fourth, 7 fifth,
3 sixth, 2 eighth). Nomination streaks don't build toward a win; they're what's left over from
people the voters didn't pick immediately.

The news hook: at the 78th Emmys, Matthew Rhys won Lead Actor in a Comedy Series (*Widow's Bay*)
and Lead Actor in a Limited or Anthology Series or Movie (*The Beast in Me*) the same night, and
coverage called him the first person to win two lead-actor Emmys in one year. That's true, but
narrower than it sounds: two other people already won two of these twelve categories in a single
year — James Earl Jones in 1991 (one lead, one supporting) and Stockard Channing in 2002 (two
supporting). Rhys is the first to do it with two **Lead** trophies specifically. All three doubles
are checkable directly in the data (see §5).

The all-time drought record: **Angela Lansbury**, twelve consecutive Lead Actress-Drama
nominations for *Murder, She Wrote*, 1985-1996, zero wins. The runner-up mark is seven
nominations, shared by ten other people (Christine Baranski, John Goodman, Matt LeBlanc, Larry
David, Steve Carell, Anthony Anderson, Jane Kaczmarek, Jason Alexander, Peter Boyle, Julia Duffy).

## 2. Data source and its quirks

**`emmys-data`** (github.com/dmase2/emmys-data), a compiled Primetime Emmy nominations CSV built
for a now-defunct fan app:

```
https://raw.githubusercontent.com/dmase2/emmys-data/main/assets/data/emmy_nominations.csv
```

8,549 rows, 1949-2026, ~2.78 MB. No LICENSE file in the repo. The facts recorded (nominee,
category, year, winner) are historical record of the Television Academy's own public awards, not
the compiler's creative expression — treated the same way Request Denied treated unlicensed DMV
exports.

Columns used: `year`, `category` (free text), `nominee`, `work`, `winner` (`"true"`/`"false"`
string). **Do not trust the `canonical_category` column** — despite the name it does not
canonicalize anything; 364 distinct strings survive in it for what should be a much smaller set
of real categories, because it just passes through minor spelling/punctuation variants uncorrected.

**Mojibake**: some category strings contain U+FFFD or a literal `�` where an en dash or em dash
should be (e.g. `"Outstanding Lead Actor in a Special Program � Drama or Comedy"`). Normalize
these to a plain hyphen before pattern-matching, or the categories fragment further.

**Only ~10% of rows have a `nominee_id`.** It cannot be used as the join key for a person's
career — matching has to be done on the exact `nominee` name string instead (see the limitation
in §6).

## 3. Reclassifying into twelve families

The raw `category` string is regrouped by keyword, case-insensitive, after stripping everything
but letters to a single space:

1. Must contain `lead` or `supporting` → billing. Rows with neither are dropped (older
   categories, or non-acting categories like writing/directing).
2. Must contain `actor` or `actress` → gender-labelled category. (This is a limitation, not an
   endorsement — see §6.)
3. Must contain `drama` → drama. Must contain `comedy` → comedy. Must contain any of `limited`,
   `miniseries`, `mini series`, `movie`, `special`, `anthology` → limited. Rows matching none of
   these three are dropped.

That yields 12 families: `(lead|supporting) x (actor|actress) x (drama|comedy|limited)`. Running
this over the *entire* dataset (1949 on) produces 3,700+ classified rows across 364 raw
category spellings collapsing cleanly into 12 — a good sign the classifier is right, since actual
Emmy history only ever had this many acting-category shapes.

## 4. Why the analysis starts in 1979, not 1949

This is the trap that costs the most time if you don't check for it. Classifying by keyword and
then counting `winner == true` rows per (family, year) should give **exactly one winner per
category per year**, occasionally two for a genuine tie. Running that check back to 1949 turns
up years with three, four, even five simultaneous "winners" in one family — not real ties, but:

- **1959 and 1967-1978**: the Emmys ran concurrent single-performance / continuing-performance
  schemes and other short-lived category splits with inconsistent naming, so a single label like
  "Best Supporting Actress (Continuing Character) in a Dramatic Series" ends up covering rows that
  are clearly from *different* real categories — the 1959 rows under that label include Fred
  Astaire, Paul Muni, Mickey Rooney and Rod Steiger (all men, some of them for a TV special, not a
  performance) alongside the actual actresses nominated that year.
- This is a real defect in how the source data collapsed old category names, not a bug in the
  classifier here — re-checking the raw `category` text confirms the rows themselves are mislabeled
  going in.

Every year from **1979** onward was checked the same way (one winner per family per year) and
comes back clean, apart from genuine documented ties — e.g. 1995's Supporting Actress in a
Miniseries or Special split between Judy Davis and Shirley Knight, which really happened. So the
dataset here is filtered to `1979 <= year <= 2026`. `build_payload.py` prints the count of rows
excluded by this filter (652, in the run that produced the shipped `payload.json`) — if a rebuild
gives a very different number, something upstream changed and needs re-checking before trusting
the rest.

## 5. Processing pipeline

```
src/fetch_data.py     downloads emmy_nominations.csv (network required)
src/build_payload.py  classifies, filters to 1979-2026, computes payload.json
src/template.html     the static page, with a {{PAYLOAD}} placeholder
src/inject.py         splices payload.json into template.html -> index.html,
                       then runs wrap_for_pages.py and add_catalog_link.py
```

Run in order from the project root:

```bash
python src/fetch_data.py
python src/build_payload.py
python src/inject.py
```

`build_payload.py` computes, per family, every person's full nomination list
`[{year, work, won}, ...]` sorted by year, plus:

- **Global stats**: total careers, never-won count/percentage, and — among careers that did
  win — a histogram of which nomination number the first win landed on.
- **Longest droughts**: everyone with zero wins, ranked by total nominations, top 25.
- **Double wins**: scan every `(year, name)` pair for wins across more than one of the twelve
  families that year. This is what surfaces the Jones/Channing/Rhys list — cross-check it
  whenever the underlying CSV updates, since a future double-winner changes the lede.

## 6. What the page has to say about its own limits (and does, in its methodology panel)

- **Name matching is exact-string, not identity-resolved.** A career is every nomination under
  one spelling of a name within one family. A billing or legal name change would silently split
  what should be one streak into two, understating it. None of the leaderboard names here are
  known to have changed names across their nominated run, but there's no reliable person ID in
  the source (only ~10% populated) to verify this automatically.
- **Gender categories are inherited from the Emmys' own history**, not asserted here; the
  classifier only reads whichever of "actor"/"actress" appears in the category's official name.
- **1949-1978 is out of scope**, for the reason in §4, not because nothing interesting happened
  there.

## 7. Verification table

Re-running `build_payload.py` from a fresh download should reproduce, byte-for-byte in the
printed summary:

| check | expected value |
|---|---|
| families | 12 |
| total careers (1979-2026) | 1,573 |
| never-won count / pct | 1,141 / 72.5% |
| first-nomination win rate among eventual winners | 68.1% |
| win-distribution histogram | 1st: 294, 2nd: 76, 3rd: 32, 4th: 18, 5th: 7, 6th: 3, 8th: 2 |
| longest drought | Angela Lansbury, Lead Actress-Drama, 12 noms, 1985-1996 |
| runner-up droughts (7 noms each) | exactly 10 people, listed in §1 above |
| double wins | 1991 James Earl Jones; 2002 Stockard Channing; 2026 Matthew Rhys (only all-Lead one) |
| rows excluded by the 1979-2026 filter | 652 |
| payload.json size | ~247,700 bytes |

If any of these drift on a rebuild, the CSV upstream has been revised (check `version.json` in
the same GitHub repo) rather than the pipeline being wrong — Emmy history for 1979-2026 doesn't
change, but 2026 itself was current at build time and a later ceremony would extend it.

## 8. Page structure

Single self-contained HTML file (payload embedded as inline JSON, no runtime fetches). Sections,
top to bottom: hero stat dek -> lede paragraph + "every double-win" sidebar table (the news
verification) -> three headline stat tiles -> win-distribution bar chart -> longest-droughts
leaderboard (top 12, Lansbury's row visually called out) -> the interactive browser (three
independent toggle groups for billing/gender/genre, a name search that overrides the "2+
nominations" default filter, and a per-person SVG dot-timeline across 1979-2026 that expands to
the literal year-by-year list on click) -> methodology panel -> sources footer.

Visual identity: a warm ink/gold "backstage" palette (paper/charcoal background, brass gold for
wins and headline numbers, hollow grey-ring dots for losses), Fraunces for display type, Inter
for body/UI, IBM Plex Mono for all numbers. Light and dark themes both defined; dark is the
default via `prefers-color-scheme`.
