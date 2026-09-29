import mimetypes

import httpx

import pyq_common as p
from upload_figures import build_dedupe


def missing_figure_gets(key_to_url: dict[str, str], get_status) -> list[str]:
    bad = []
    for key, url in sorted(key_to_url.items()):
        if get_status(url) != 200:
            bad.append(key)
    return bad


def http_get_status(url: str) -> int:
    r = httpx.head(url, follow_redirects=True, timeout=30)
    if r.status_code in (405, 403, 400):
        r = httpx.get(url, follow_redirects=True, timeout=30)
    return r.status_code


def chapter_figure_keys(skeleton: list, chapter_no: int) -> list[str]:
    return sorted({k for r in skeleton if r["chapter_no"] == chapter_no for k in r["figure_keys"]})


def upload_chapter_figures(chapter_no: int, sb) -> dict[str, str]:
    """Upload this chapter's figure keys. Returns figure_key → public_url."""
    manifest = p.load_figures_manifest()
    skeleton = p.load_skeleton()
    by_key, by_checksum, missing_files, _repeated = build_dedupe(manifest)
    wanted = chapter_figure_keys(skeleton, chapter_no)
    canonical = {k: sorted(keys)[0] for keys in by_checksum.values() for k in keys}
    urls = {}
    uploaded = set()
    rows = []
    for key in wanted:
        if key in missing_files or key not in canonical:
            continue
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
        public_url = sb.storage.from_(p.BUCKET).get_public_url(object_name)
        urls[key] = public_url
        rows.append({
            "figure_key": key,
            "storage_path": f"{p.BUCKET}/{object_name}",
            "public_url": public_url,
            "px_width": meta["px_width"],
            "px_height": meta["px_height"],
            "bytes": meta["bytes"],
            "checksum": p.sha256_file(local),
            "source_page": meta["page"],
            "source_bbox": meta["bbox"],
        })
    if rows:
        sb.table("pyq_figures").upsert(rows, on_conflict="figure_key").execute()
    return urls
