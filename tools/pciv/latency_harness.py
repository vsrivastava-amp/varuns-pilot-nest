"""Provider-level latency A/B harness for the pCIV demo prompt change.

Measures TTFT / time-to-DELIM (reply done) / total stream time by calling the
provider's chat-completions API directly with the demo's assembled system
prompt — no changes to pciv-demo-service needed. Reads cached_tokens from
usage so every sample is labeled with its true cache state.

Arms are paths to a checkout's prompts/ dir; the system prompt is assembled
exactly as main.py does (chat + output_protocol.format(DELIM) + extraction).

Usage (see README.md):

    uv run --env-file ~/Documents/pciv-demo-service/.env python latency_harness.py \
        --arm-a ~/Documents/pciv-demo-service/prompts \
        --arm-b /path/to/new-checkout/prompts \
        --queries queries.txt --n 50 --mode warm \
        --out results.jsonl

Cold mode busts the prefix cache by prepending a per-request nonce line to
the system prompt (identical overhead in both arms, ~10 tokens). This lets a
cold run finish in minutes instead of waiting out the provider's cache TTL
between samples. Caveat: measures cold *prefill*, not the exact production
prompt bytes.
"""

import argparse
import json
import os
import statistics
import sys
import time
import urllib.request
import uuid
from pathlib import Path

DELIM = "<<<PCIV_DELIM>>>"  # must match main.py
TEMPERATURE = 0.3
MAX_TOKENS = 10_000

PROVIDERS = {
    "openai": ("https://api.openai.com/v1", "OPENAI_API_KEY"),
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_KEY"),
}


def build_system_prompt(prompts_dir: Path) -> str:
    """Mirror main.py's PROMPT_WITH_PCIV assembly."""
    chat = (prompts_dir / "publisher_chat.txt").read_text()
    protocol = (prompts_dir / "output_protocol.txt").read_text().format(DELIM=DELIM)
    extraction = (prompts_dir / "pciv_extraction.txt").read_text()
    return "\n".join([chat, protocol, extraction])


def stream_request(base_url, token, model, system_prompt, query, timeout):
    """One streamed chat completion. Returns a sample dict with timings + usage."""
    # OpenAI's newer models reject max_tokens (langchain maps this inside the
    # service); OpenRouter still expects max_tokens.
    max_tok_param = "max_completion_tokens" if "openai.com" in base_url else "max_tokens"
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ],
        "stream": True,
        "stream_options": {"include_usage": True},
        max_tok_param: MAX_TOKENS,
        "temperature": TEMPERATURE,
    }
    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST",
    )

    t_start = time.perf_counter()
    t_first = t_delim = None
    content = ""
    usage = {}
    finish_reason = None

    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code}: {exc.read().decode()[:500]}") from exc
    for line in resp:
        line = line.decode().strip()
        if not line.startswith("data: "):
            continue
        payload = line[len("data: "):]
        if payload == "[DONE]":
            break
        chunk = json.loads(payload)
        if chunk.get("usage"):
            usage = chunk["usage"]
        choices = chunk.get("choices") or []
        if choices and choices[0].get("finish_reason"):
            finish_reason = choices[0]["finish_reason"]
        delta = choices[0].get("delta", {}) if choices else {}
        piece = delta.get("content") or ""
        if piece:
            if t_first is None:
                t_first = time.perf_counter()
            content += piece
            if t_delim is None and DELIM in content:
                t_delim = time.perf_counter()
    t_end = time.perf_counter()

    details = usage.get("prompt_tokens_details") or {}
    return {
        "ttft_ms": round((t_first - t_start) * 1000, 1) if t_first else None,
        "reply_done_ms": round((t_delim - t_start) * 1000, 1) if t_delim else None,
        "total_ms": round((t_end - t_start) * 1000, 1),
        "prompt_tokens": usage.get("prompt_tokens"),
        "cached_tokens": details.get("cached_tokens", 0),
        "completion_tokens": usage.get("completion_tokens"),
        "delim_seen": t_delim is not None,
        "finish_reason": finish_reason,
        "content": content,
    }


def grade_pciv(sample, tax_ids):
    """Parse and validate the post-DELIM pCIV exactly as main.py would.

    Adds parse_ok / bad_gpc_ids to the sample; replaces raw content with a
    short tail kept only for failed samples (diagnosis without bloating rows).
    """
    content = sample.pop("content")
    parse_ok = False
    bad_ids = []
    if sample["delim_seen"]:
        raw = content.split(DELIM, 1)[1]
        start, end = raw.find("{"), raw.rfind("}")
        if start != -1 and end != -1:
            try:
                pciv = json.loads(raw[start:end + 1])
                parse_ok = True
                for target in pciv.get("targets") or []:
                    for gid in target.get("gpc") or []:
                        if str(gid) not in tax_ids:
                            bad_ids.append(gid)
            except json.JSONDecodeError:
                pass
    sample["parse_ok"] = parse_ok
    sample["bad_gpc_ids"] = bad_ids
    if not sample["delim_seen"] or not parse_ok or bad_ids:
        sample["tail"] = content[-400:]
    return sample


def pctl(values, p):
    if not values:
        return None
    values = sorted(values)
    k = (len(values) - 1) * p / 100
    lo, hi = int(k), min(int(k) + 1, len(values) - 1)
    return round(values[lo] + (values[hi] - values[lo]) * (k - lo), 1)


def summarize(samples, arm, mode):
    rows = [s for s in samples if s["arm"] == arm and s["mode"] == mode and s["ttft_ms"]]
    if not rows:
        return None
    ttft = [s["ttft_ms"] for s in rows]
    reply = [s["reply_done_ms"] for s in rows if s["reply_done_ms"]]
    total = [s["total_ms"] for s in rows]
    cached = [s["cached_tokens"] for s in rows]
    return {
        "arm": arm, "mode": mode, "n": len(rows),
        "ttft_p50": pctl(ttft, 50), "ttft_p95": pctl(ttft, 95),
        "reply_done_p50": pctl(reply, 50), "reply_done_p95": pctl(reply, 95),
        "total_p50": pctl(total, 50), "total_p95": pctl(total, 95),
        "prompt_tokens": rows[0]["prompt_tokens"],
        "cached_tokens_mean": round(statistics.mean(cached), 1),
        "cache_hit_rate": round(sum(1 for c in cached if c > 0) / len(cached), 2),
        "completion_tokens_mean": round(statistics.mean(
            s["completion_tokens"] for s in rows if s["completion_tokens"]), 1),
        "delim_rate": round(sum(1 for s in rows if s["delim_seen"]) / len(rows), 3),
        "parse_ok_rate": round(sum(1 for s in rows if s.get("parse_ok")) / len(rows), 3),
        "bad_gpc_rate": round(sum(1 for s in rows if s.get("bad_gpc_ids")) / len(rows), 3),
        "finish_reasons": {fr: sum(1 for s in rows if s.get("finish_reason") == fr)
                           for fr in {s.get("finish_reason") for s in rows}},
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--arm-a", required=True, type=Path, help="prompts/ dir for arm A (baseline)")
    ap.add_argument("--arm-b", type=Path, help="prompts/ dir for arm B (candidate); omit for single-arm/noise-floor A-vs-A")
    ap.add_argument("--taxonomy-a", type=Path, help="gpc_taxonomy.json for arm A (enables pCIV grading)")
    ap.add_argument("--taxonomy-b", type=Path, help="gpc_taxonomy.json for arm B (defaults to taxonomy-a)")
    ap.add_argument("--queries", required=True, type=Path, help="one user query per line; # lines ignored")
    ap.add_argument("--n", type=int, default=50, help="samples per arm per mode")
    ap.add_argument("--mode", choices=["warm", "cold", "both"], default="warm")
    ap.add_argument("--model", default="gpt-5.4-nano")
    ap.add_argument("--provider", choices=PROVIDERS, default="openai")
    ap.add_argument("--out", type=Path, required=True, help="results JSONL (appended)")
    ap.add_argument("--timeout", type=int, default=120)
    args = ap.parse_args()

    base_url, token_env = PROVIDERS[args.provider]
    token = os.environ.get(token_env)
    if not token:
        sys.exit(f"missing {token_env} in environment")

    queries = [q.strip() for q in args.queries.read_text().splitlines()
               if q.strip() and not q.startswith("#")]
    if not queries:
        sys.exit("no queries")

    arms = {"A": build_system_prompt(args.arm_a)}
    arms["B"] = build_system_prompt(args.arm_b) if args.arm_b else arms["A"]
    tax = {}
    if args.taxonomy_a:
        tax["A"] = set(json.loads(args.taxonomy_a.read_text()))
        tax["B"] = set(json.loads((args.taxonomy_b or args.taxonomy_a).read_text()))
    modes = ["warm", "cold"] if args.mode == "both" else [args.mode]

    run_id = uuid.uuid4().hex[:8]
    samples = []
    args.out.parent.mkdir(parents=True, exist_ok=True)

    with args.out.open("a") as out:
        for mode in modes:
            if mode == "warm":  # prime each arm's prefix once, unmeasured
                for arm, prompt in arms.items():
                    print(f"[{mode}] priming arm {arm} ...", flush=True)
                    stream_request(base_url, token, args.model, prompt, queries[0], args.timeout)

            for i in range(args.n):
                for arm in ("A", "B"):  # interleaved to cancel provider drift
                    prompt = arms[arm]
                    if mode == "cold":
                        prompt = f"# cache-bust {uuid.uuid4().hex}\n{prompt}"
                    query = queries[i % len(queries)]
                    try:
                        s = stream_request(base_url, token, args.model, prompt, query, args.timeout)
                    except Exception as exc:
                        print(f"  [{mode} {arm} #{i}] ERROR {exc}", flush=True)
                        continue
                    if arm in tax:
                        s = grade_pciv(s, tax[arm])
                    else:
                        s.pop("content", None)
                    s.update(run_id=run_id, arm=arm, mode=mode, model=args.model,
                             query_idx=i % len(queries), ts=time.time())
                    samples.append(s)
                    out.write(json.dumps(s) + "\n")
                    out.flush()
                    flags = "" if s.get("parse_ok", True) and s["delim_seen"] else " ** PCIV FAIL"
                    print(f"  [{mode} {arm} #{i}] ttft={s['ttft_ms']}ms total={s['total_ms']}ms "
                          f"cached={s['cached_tokens']}/{s['prompt_tokens']}{flags}", flush=True)

    print("\n=== summary ===")
    for mode in modes:
        for arm in ("A", "B"):
            summary = summarize(samples, arm, mode)
            if summary:
                print(json.dumps(summary, indent=2))
    print("\nNote: in cold mode expect cached_tokens=0; in warm mode expect "
          "cached_tokens ≈ prompt size (rounded down to 128-tok increment). "
          "Samples violating that are mislabeled cache states — filter before comparing.")


if __name__ == "__main__":
    main()
