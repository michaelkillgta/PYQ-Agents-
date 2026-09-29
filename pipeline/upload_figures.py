#!/usr/bin/env python3
"""Phase 2 - SHA-256 dedupe, upload Laws of Motion figures, insert pyq_figures.

Idempotent: re-running overwrites the same object names and upserts the same
figure_key rows. It never duplicates.
"""
import collections
import json
import mimetypes

import pyq_common as p


def build_dedupe(manifest):
    """Group distinct figure_keys by file checksum. Tolerates repeated keys."""
    by_key = {}
    repeats = collections.Counter()
    for row in manifest:
        key = row["figure_key"]
        repeats[key] += 1
        by_key.setdefault(key, row)      # first placement wins; do not raise

    by_checksum = collections.defaultdict(list)
    missing = []
    for key in sorted(by_key):
        path = p.OUT / "figures" / f"{key}.png"
        if not path.exists():
            missing.append(key)
            continue
        by_checksum[p.sha256_file(path)].append(key)

    return by_key, by_checksum, missing, [k for k, n in repeats.items() if n > 1]


def main():
    sb = p.supabase_client()
    manifest = p.load_figures_manifest()
    skeleton = p.load_skeleton()

    by_key, by_checksum, missing, repeated = build_dedupe(manifest)
    groups = [keys for keys in by_checksum.values() if len(keys) > 1]

    (p.OUT / "figure_dedupe.json").write_text(json.dumps({
        "manifest_rows": len(manifest),
        "distinct_keys": len(by_key),
        "unique_checksums": len(by_checksum),
        "duplicate_groups": sorted(groups),
        "repeated_manifest_keys": sorted(repeated),
        "missing_files": sorted(missing),
        # canonical = lexicographically first key of the checksum group
        "canonical": {k: sorted(keys)[0] for keys in by_checksum.values() for k in keys},
    }, indent=2), encoding="utf-8")

    print(f"manifest rows     : {len(manifest)}")
    print(f"distinct keys     : {len(by_key)}")
    print(f"unique checksums  : {len(by_checksum)}")
    print(f"duplicate groups  : {len(groups)}")
    print(f"repeated keys     : {repeated}")
    print(f"missing files     : {len(missing)}")

    # --- pilot chapter only ---
    wanted = sorted({k for r in skeleton if r["chapter_no"] == p.CHAPTER_5
                     for k in r["figure_keys"]})
    canonical = {k: sorted(keys)[0] for keys in by_checksum.values() for k in keys}

    uploaded, rows = set(), []
    for key in wanted:
        canon = canonical[key]
        object_name = f"{p.FIGURE_PREFIX}/{canon}.png"
        local = p.OUT / "figures" / f"{canon}.png"
        if canon not in uploaded:
            sb.storage.from_(p.BUCKET).upload(
                object_name,
                local.read_bytes(),
                {"content-type": mimetypes.guess_type(local.name)[0] or "image/png",
                 "upsert": "true"},
            )
            uploaded.add(canon)
        meta = by_key[key]
        rows.append({
            "figure_key": key,
            "storage_path": f"{p.BUCKET}/{object_name}",
            "public_url": sb.storage.from_(p.BUCKET).get_public_url(object_name),
            "px_width": meta["px_width"],
            "px_height": meta["px_height"],
            "bytes": meta["bytes"],
            "checksum": p.sha256_file(local),
            "source_page": meta["page"],
            "source_bbox": meta["bbox"],
        })

    sb.table("pyq_figures").upsert(rows, on_conflict="figure_key").execute()
    print(f"chapter 5 keys    : {len(wanted)}")
    print(f"objects uploaded  : {len(uploaded)}")
    print(f"pyq_figures rows  : {len(rows)}")


if __name__ == "__main__":
    main()
