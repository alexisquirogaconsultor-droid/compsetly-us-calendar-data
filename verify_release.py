"""Offline integrity and consistency checks for the three public datasets."""
from __future__ import annotations

import argparse
import csv
from datetime import date, datetime, timedelta, timezone
import hashlib
import io
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
EXPECTED = {"ssi-november-cycles": (5, 5), "mexico-gp-2026": (2, 2), "service-calendar-differences-2027": (3, 3)}
OFFSET_HOURS = {"CST": -6, "CDT": -5, "EST": -5, "EDT": -4, "MST": -7, "MDT": -6, "PST": -8, "PDT": -7, "HST": -10, "AKST": -9, "AKDT": -8}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def safe_path(relative):
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Unsafe manifest path")
    return HERE / path


def parse_calendar(raw):
    """Parse the fields needed by these seven non-recurring snapshot exports."""
    if b"\r\n" not in raw or not raw.endswith(b"END:VCALENDAR\r\n"):
        raise ValueError("Calendar must use CRLF and end with VCALENDAR")
    if any(len(line) > 75 for line in raw.split(b"\r\n")):
        raise ValueError("Calendar physical line exceeds 75 octets")
    text = raw.decode("utf-8").replace("\r\n ", "").replace("\r\n\t", "")
    result = []
    current = None
    for line in text.split("\r\n"):
        if line == "BEGIN:VEVENT":
            if current is not None:
                raise ValueError("Nested VEVENT")
            current = {}
        elif line == "END:VEVENT":
            if current is None:
                raise ValueError("Unmatched END:VEVENT")
            if not current.get("UID") or not current.get("DTSTART"):
                raise ValueError("Missing UID or DTSTART")
            start = current["DTSTART"]
            if current.get("DTSTART_TYPE") == "DATE":
                start = datetime.strptime(start, "%Y%m%d").date()
                if current.get("DTEND_TYPE") != "DATE":
                    raise ValueError("All-day DTEND must be DATE")
                end = datetime.strptime(current["DTEND"], "%Y%m%d").date()
                if end != start + timedelta(days=1):
                    raise ValueError("These snapshot all-day reminders must span one day with an exclusive end")
            else:
                start = datetime.strptime(start, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
                end = datetime.strptime(current["DTEND"], "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc) if current.get("DTEND") else start
                if end < start:
                    raise ValueError("Calendar end precedes start")
            current["start"] = start
            current["end"] = end
            result.append(current)
            current = None
        elif current is not None and ":" in line:
            field, value = line.split(":", 1)
            key = field.split(";", 1)[0]
            if key in ["UID", "DTSTART", "DTEND", "DTSTAMP", "SUMMARY"]:
                if key in current:
                    raise ValueError("Repeated event property")
                current[key] = value
                if key in ["DTSTART", "DTEND"]:
                    current[key + "_TYPE"] = "DATE" if ";VALUE=DATE" in field else "DATE-TIME"
    if current is not None or not result:
        raise ValueError("Unclosed event or empty calendar")
    return result


def verify(source_root=None):
    errors = []
    sums = {}
    for line in (HERE / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, path = line.split("  ", 1)
        if path in sums:
            errors.append("Duplicate checksum path: " + path)
        sums[path] = digest
        if not safe_path(path).is_file() or sha(safe_path(path).read_bytes()) != digest:
            errors.append("Checksum mismatch: " + path)
    actual_files = {p.relative_to(HERE).as_posix() for p in HERE.rglob("*") if p.is_file() and not any(part in [".git", "__pycache__", "upload-flat"] for part in p.relative_to(HERE).parts) and p.name not in ["SHA256SUMS", "acquisition-data-release-flat.zip"]}
    if actual_files != set(sums):
        errors.append("Checksum inventory differs from repository files")
    manifest = json.loads((HERE / "release-manifest.json").read_text(encoding="utf-8"))
    citation = json.loads((HERE / "CITATION.cff").read_text(encoding="utf-8"))
    if citation.get("cff-version") != "1.2.0" or citation.get("type") != "dataset" or citation.get("authors") != [{"name": "Compsetly", "website": "https://trends.compsetly.com/"}]:
        errors.append("CFF independent-compilation identity mismatch")
    if not all(citation.get(x) for x in ["title", "message"]):
        errors.append("Missing required CFF field")
    if any(x in citation for x in ["doi", "license", "license-url", "date-released"]):
        errors.append("Unexpected unasserted DOI, rights or release date")
    datasets = manifest["datasets"]
    if {d["id"] for d in datasets} != set(EXPECTED) or len(datasets) != 3:
        errors.append("Exactly the three documented datasets are required")
    results = []
    global_uids = set()
    for dataset in datasets:
        events = []
        csv_rows = []
        for asset in dataset["files"]:
            raw = safe_path(asset["path"]).read_bytes()
            if sha(raw) != asset["sha256"] or len(raw) != asset["bytes"]:
                errors.append("Manifest hash or byte count mismatch: " + asset["path"])
            if asset["path"].endswith(".csv"):
                csv_rows.extend(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
            elif asset["path"].endswith(".ics"):
                parsed = parse_calendar(raw)
                if len(parsed) != asset["events"]:
                    errors.append("Calendar count mismatch: " + asset["path"])
                for event in parsed:
                    if event["UID"] in global_uids:
                        errors.append("Duplicate event UID: " + event["UID"])
                    global_uids.add(event["UID"])
                events.extend(parsed)
            else:
                errors.append("Unexpected data type")
            if source_root is not None:
                original = source_root / asset["sourceAssetPath"]
                if not original.is_file() or original.read_bytes() != raw:
                    errors.append("Copied bytes differ from local public root: " + asset["path"])
        expected_rows, expected_events = EXPECTED[dataset["id"]]
        if len(csv_rows) != expected_rows or len(events) != expected_events:
            errors.append("Dataset row/event count mismatch: " + dataset["id"])
        if dataset["id"] == "ssi-november-cycles":
            if {r["payment_date"] for r in csv_rows} != {e["start"].isoformat() for e in events}:
                errors.append("SSI CSV/calendar dates differ")
        if dataset["id"] == "service-calendar-differences-2027":
            if {r["date"] for r in csv_rows} != {e["start"].isoformat() for e in events}:
                errors.append("Service comparison CSV/calendar dates differ")
        if dataset["id"] == "mexico-gp-2026":
            if {datetime.fromisoformat(r["start_utc"]) for r in csv_rows} != {e["start"] for e in events}:
                errors.append("Mexico CSV/calendar UTC starts differ")
            for row in csv_rows:
                utc = datetime.fromisoformat(row["start_utc"])
                for field in ["mexico", "eastern", "central", "mountain", "pacific", "phoenix", "honolulu", "anchorage"]:
                    clock, abbreviation = row[field].rsplit(" ", 1)
                    expected = (utc + timedelta(hours=OFFSET_HOURS[abbreviation])).strftime("%b %d %H:%M")
                    if clock != expected:
                        errors.append("Mexico clock arithmetic differs: " + field)
        results.append({"id":dataset["id"], "csvRows":len(csv_rows), "calendarEvents":len(events), "dataFiles":len(dataset["files"])})
    return {"verifiedUtc":datetime.now(timezone.utc).isoformat(), "checksPassed":not errors, "datasets":results, "checksummedFiles":len(sums), "sourceRootComparisonPerformed":source_root is not None, "networkRequests":0, "filesChanged":False, "errors":errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, help="Optional local public root for byte-for-byte comparison")
    args = parser.parse_args()
    try:
        result = verify(args.source_root)
    except Exception as exc:
        result = {"checksPassed":False, "errors":[type(exc).__name__ + ": " + str(exc)], "networkRequests":0, "filesChanged":False}
    print(json.dumps(result, indent=2))
    return 0 if result["checksPassed"] else 1


if __name__ == "__main__":
    sys.exit(main())
