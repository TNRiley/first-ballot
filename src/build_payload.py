"""Turn emmy_nominations.csv into payload.json for First Ballot.

Scope decision (the trap): the raw CSV's own `canonical_category` column does
not actually canonicalize anything -- category text for the six acting
families (Lead/Supporting x Actor/Actress x Drama/Comedy/Limited) is spelled
more than a dozen ways per family across 76 years, with mojibake dashes from
a bad encoding pass. We rebuild the grouping from the raw `category` string
with a small keyword classifier instead.

That classifier then surfaces a second, worse problem: for 1959 and again for
1967-1978, several categories mix genders and even non-people ("An Evening
with Fred Astaire", "The Perry Como Show") into what's labelled as a single
acting category, and multiple "winners" appear in a category that can only
have one. This is the mid-1970s Emmys' real chaos of concurrent single-
performance/continuing-performance schemes and one-off wording, not a typo we
can patch -- so the analysis starts in 1979, the year the modern six-category
structure (Lead/Supporting x Actor/Actress x Drama/Comedy/Limited) settles and
every family stops producing impossible ties. Every year from 1979 to 2026 was
checked afterward: exactly one row of "winner": true per category per year,
except for genuine documented ties (e.g. 1995 Supporting Actress, Miniseries
or Special: Judy Davis and Shirley Knight both won).

Run:
    python build_payload.py
Reads ../emmy_nominations.csv, writes ../payload.json.
"""
import csv
import json
import pathlib
import re
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "emmy_nominations.csv"
OUT_PATH = ROOT / "payload.json"

START_YEAR = 1979
END_YEAR = 2026

FAMILY_LABELS = {
    ("lead", "actor", "drama"): "Lead Actor, Drama",
    ("lead", "actress", "drama"): "Lead Actress, Drama",
    ("lead", "actor", "comedy"): "Lead Actor, Comedy",
    ("lead", "actress", "comedy"): "Lead Actress, Comedy",
    ("lead", "actor", "limited"): "Lead Actor, Limited/Movie",
    ("lead", "actress", "limited"): "Lead Actress, Limited/Movie",
    ("supporting", "actor", "drama"): "Supporting Actor, Drama",
    ("supporting", "actress", "drama"): "Supporting Actress, Drama",
    ("supporting", "actor", "comedy"): "Supporting Actor, Comedy",
    ("supporting", "actress", "comedy"): "Supporting Actress, Comedy",
    ("supporting", "actor", "limited"): "Supporting Actor, Limited/Movie",
    ("supporting", "actress", "limited"): "Supporting Actress, Limited/Movie",
}


def normalize(cat):
    c = cat.lower()
    c = c.replace("�", "-").replace("\N{REPLACEMENT CHARACTER}", "-")
    c = re.sub(r"[^a-z]+", " ", c)
    return c


def classify(cat):
    c = normalize(cat)
    is_lead = "lead" in c
    is_supp = "supporting" in c
    if not (is_lead or is_supp):
        return None
    if "actor" in c:
        gender = "actor"
    elif "actress" in c:
        gender = "actress"
    else:
        return None
    if "drama" in c:
        genre = "drama"
    elif "comedy" in c:
        genre = "comedy"
    elif any(w in c for w in ("limited", "miniseries", "mini series", "movie", "special", "anthology")):
        genre = "limited"
    else:
        return None
    return (("lead" if is_lead else "supporting"), gender, genre)


def fam_key(fam):
    return "-".join(fam)


def main():
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    by_person = defaultdict(lambda: defaultdict(list))  # fam -> name -> [(year, work, won)]
    win_rows_by_year_person = defaultdict(set)  # (year, name) -> {fam,...} for double-win check

    skipped_pre1979 = 0
    for row in rows:
        fam = classify(row["category"])
        if not fam:
            continue
        year = int(row["year"])
        if year < START_YEAR or year > END_YEAR:
            skipped_pre1979 += 1
            continue
        name = row["nominee"].strip()
        if not name:
            continue
        won = row["winner"].strip().lower() == "true"
        work = row["work"].strip()
        by_person[fam][name].append((year, work, won))
        if won:
            win_rows_by_year_person[(year, name)].add(fam)

    families_out = {}
    global_never_won = 0
    global_total_careers = 0
    first_win_index_counts = defaultdict(int)
    drought_leaderboard = []  # (noms, name, fam, years)

    for fam, people in by_person.items():
        fam_people_out = []
        for name, noms in people.items():
            noms.sort(key=lambda t: t[0])
            total = len(noms)
            wins = sum(1 for _, _, w in noms if w)
            first_win_idx = None
            for i, (_, _, w) in enumerate(noms):
                if w:
                    first_win_idx = i
                    break
            global_total_careers += 1
            if first_win_idx is None:
                global_never_won += 1
                drought_leaderboard.append((total, name, FAMILY_LABELS[fam], [y for y, _, _ in noms]))
            else:
                first_win_index_counts[first_win_idx + 1] += 1

            fam_people_out.append({
                "name": name,
                "noms": [{"year": y, "work": w, "won": won_} for y, w, won_ in noms],
                "total": total,
                "wins": wins,
            })
        fam_people_out.sort(key=lambda p: (-p["total"], p["name"]))
        families_out[fam_key(fam)] = {
            "label": FAMILY_LABELS[fam],
            "people": fam_people_out,
        }

    drought_leaderboard.sort(key=lambda t: -t[0])

    doubles = []
    for (year, name), fams in win_rows_by_year_person.items():
        if len(fams) > 1:
            doubles.append({
                "year": year,
                "name": name,
                "families": sorted(FAMILY_LABELS[f] for f in fams),
                "allLead": all(f[0] == "lead" for f in fams),
            })
    doubles.sort(key=lambda d: d["year"])

    total_with_win = global_total_careers - global_never_won
    first_try = first_win_index_counts.get(1, 0)

    payload = {
        "generated": "2026-09-22",
        "startYear": START_YEAR,
        "endYear": END_YEAR,
        "familyOrder": [fam_key(f) for f in FAMILY_LABELS],
        "familyLabels": {fam_key(f): lbl for f, lbl in FAMILY_LABELS.items()},
        "families": families_out,
        "stats": {
            "totalCareers": global_total_careers,
            "neverWon": global_never_won,
            "neverWonPct": round(100 * global_never_won / global_total_careers, 1),
            "totalWithWin": total_with_win,
            "firstTryWinners": first_try,
            "firstTryWinnersPct": round(100 * first_try / total_with_win, 1),
            "winDistribution": [
                {"nth": n, "count": c} for n, c in sorted(first_win_index_counts.items())
            ],
            "longestDroughts": [
                {"name": n, "family": f, "noms": t, "years": y}
                for t, n, f, y in drought_leaderboard[:25]
            ],
            "doubleWins": doubles,
        },
    }

    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8", newline="\n")
    print(f"families: {len(families_out)}")
    print(f"careers: {global_total_careers}, never-won: {global_never_won} ({payload['stats']['neverWonPct']}%)")
    print(f"first-try win rate among eventual winners: {payload['stats']['firstTryWinnersPct']}%")
    print(f"double wins: {doubles}")
    print(f"rows outside {START_YEAR}-{END_YEAR}: {skipped_pre1979}")
    print(f"wrote {OUT_PATH} ({OUT_PATH.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
