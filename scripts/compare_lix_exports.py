import sys
from collections import Counter

import pandas as pd


FOCUS_COLUMNS = [
    "Organisation ID",
    "Organisation Website",
    "Organisation Size",
    "Job Function",
]


def clean_value(value):
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.endswith(".0") and text[:-2].isdigit():
        return text[:-2]
    return " ".join(text.split())


def load_rows(path):
    frame = pd.read_excel(path, dtype=str).fillna("")
    frame.columns = [clean_value(column) for column in frame.columns]
    rows = []
    for _, row in frame.iterrows():
        item = {column: clean_value(row.get(column, "")) for column in frame.columns}
        if item.get("ID"):
            rows.append(item)
    return frame.columns.tolist(), rows


def count_filled(rows, column):
    return sum(1 for row in rows if row.get(column, ""))


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: compare_lix_exports.py <lix.xlsx> <addon.xlsx>")

    lix_path, addon_path = sys.argv[1], sys.argv[2]
    lix_columns, lix_rows = load_rows(lix_path)
    addon_columns, addon_rows = load_rows(addon_path)

    lix_by_id = {row["ID"]: row for row in lix_rows}
    addon_by_id = {row["ID"]: row for row in addon_rows}
    matched_ids = sorted(set(lix_by_id) & set(addon_by_id))
    lix_only = sorted(set(lix_by_id) - set(addon_by_id))
    addon_only = sorted(set(addon_by_id) - set(lix_by_id))

    print("SHAPE")
    print(f"LIX rows: {len(lix_rows)}")
    print(f"Add-on rows: {len(addon_rows)}")
    print(f"Matched by ID: {len(matched_ids)}")
    print(f"LIX-only IDs: {len(lix_only)}")
    print(f"Add-on-only IDs: {len(addon_only)}")
    print()

    print("COLUMNS")
    print(f"LIX columns ({len(lix_columns)}): {', '.join(lix_columns)}")
    print(f"Add-on columns ({len(addon_columns)}): {', '.join(addon_columns)}")
    print()

    common_columns = [column for column in lix_columns if column in addon_columns]
    print("ALL COLUMN EXACT MATCHES ON MATCHED IDS")
    for column in common_columns:
        same = sum(
            1
            for lead_id in matched_ids
            if lix_by_id[lead_id].get(column, "") == addon_by_id[lead_id].get(column, "")
        )
        print(f"{column}: {same}/{len(matched_ids)}")
    print()

    print("FOCUS COLUMN SUMMARY")
    for column in FOCUS_COLUMNS:
        same = 0
        lix_blank_addon_filled = 0
        lix_filled_addon_blank = 0
        both_filled_diff = 0
        examples = []
        addon_values = Counter()
        lix_values = Counter()
        for lead_id in matched_ids:
            lix_value = lix_by_id[lead_id].get(column, "")
            addon_value = addon_by_id[lead_id].get(column, "")
            if lix_value:
                lix_values[lix_value] += 1
            if addon_value:
                addon_values[addon_value] += 1
            if lix_value == addon_value:
                same += 1
            elif lix_value and not addon_value:
                lix_filled_addon_blank += 1
            elif addon_value and not lix_value:
                lix_blank_addon_filled += 1
            else:
                both_filled_diff += 1
            if lix_value != addon_value and len(examples) < 8:
                examples.append((lead_id, lix_value, addon_value))

        print(f"{column}:")
        print(f"  LIX filled: {count_filled(lix_rows, column)}/{len(lix_rows)}")
        print(f"  Add-on filled: {count_filled(addon_rows, column)}/{len(addon_rows)}")
        print(f"  Exact match on matched IDs: {same}/{len(matched_ids)}")
        print(f"  LIX filled, add-on blank: {lix_filled_addon_blank}")
        print(f"  LIX blank, add-on filled: {lix_blank_addon_filled}")
        print(f"  Both filled but different: {both_filled_diff}")
        if column == "Job Function":
            print(f"  Top LIX values: {lix_values.most_common(10)}")
            print(f"  Top add-on values: {addon_values.most_common(10)}")
        print("  Examples:")
        for lead_id, lix_value, addon_value in examples:
            name = lix_by_id[lead_id].get("LinkedIn Name") or addon_by_id[lead_id].get("LinkedIn Name")
            print(f"    {lead_id} | {name} | LIX={lix_value!r} | Add-on={addon_value!r}")
        print()

    print("ROW SET SAMPLES")
    print(f"LIX-only sample: {lix_only[:10]}")
    print(f"Add-on-only sample: {addon_only[:10]}")


if __name__ == "__main__":
    main()
