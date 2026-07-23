"""Generate the pCIV demo's GPC assets from the eval-service source of truth.

Produces, deterministically, from the full GPC taxonomy (all levels):
  1. taxonomy/gpc_taxonomy.json — every L1 + L2 (21 + 192 = 213 entries),
     id -> full path name, ordered by (L1 name, level, L2 name)
  2. the prompt's GPC list block — one line per L1 with its L2s as id:Name|
     entries (names = leaf, spaces stripped, matching the existing compact
     style), plus a final line of all L1 IDs for the "no fitting L2" rule.

It patches prompts/pciv_extraction.txt IN PLACE, replacing only the list
between "=== GPC ===" and "Key disambiguations:". The disambiguation rules
and examples are editorial — they stay hand-maintained in the prompt file.

Usage:
  python generate_gpc_assets.py --source <full_gpc_taxonomy.json> --repo <pciv-demo-service dir>
"""

import argparse
import json
from pathlib import Path


def compact(name: str) -> str:
    return name.replace(" ", "")


def build(source: dict):
    l1 = {k: v for k, v in source.items() if ">" not in v}
    l2 = {k: v for k, v in source.items() if v.count(">") == 1}

    l1_by_name = sorted(l1.items(), key=lambda kv: kv[1])
    l2_by_parent = {}
    for gid, path in l2.items():
        parent, _, leaf = (p.strip() for p in path.partition(">"))
        l2_by_parent.setdefault(parent, []).append((leaf, gid))

    taxonomy = {}
    lines = []
    for gid, l1_name in l1_by_name:
        taxonomy[gid] = l1_name
        children = sorted(l2_by_parent.get(l1_name, []))
        for leaf, cid in children:
            taxonomy[cid] = f"{l1_name} > {leaf}"
        entries = "|".join(f"{cid}:{compact(leaf)}" for leaf, cid in children)
        lines.append(f"{compact(l1_name)}: {entries}")
    l1_line = "|".join(f"{gid}:{compact(name)}" for gid, name in l1_by_name)
    lines.append(f"L1 IDs (only when no fitting L2 exists): {l1_line}")
    return taxonomy, "\n".join(lines)


def patch_prompt(prompt_path: Path, block: str):
    text = prompt_path.read_text()
    start = text.index("=== GPC ===")
    end = text.index("Key disambiguations:")
    prompt_path.write_text(text[:start] + "=== GPC ===\n\n" + block + "\n\n" + text[end:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, type=Path, help="full GPC taxonomy json (all levels)")
    ap.add_argument("--repo", required=True, type=Path, help="pciv-demo-service checkout to patch")
    args = ap.parse_args()

    source = json.loads(args.source.read_text())
    taxonomy, block = build(source)

    tax_path = args.repo / "taxonomy" / "gpc_taxonomy.json"
    tax_path.write_text(json.dumps(taxonomy, indent=2) + "\n")
    patch_prompt(args.repo / "prompts" / "pciv_extraction.txt", block)

    n_l1 = sum(1 for v in taxonomy.values() if ">" not in v)
    print(f"taxonomy: {len(taxonomy)} entries ({n_l1} L1 + {len(taxonomy) - n_l1} L2)")
    print(f"GPC block: ~{len(block) // 4} tokens (rough), {len(block.splitlines())} lines")


if __name__ == "__main__":
    main()
