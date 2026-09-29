def coverage_diff(skeleton_q: set, parsed_q: set) -> dict:
    return {
        "missing": sorted(skeleton_q - parsed_q),
        "extra": sorted(parsed_q - skeleton_q),
    }
