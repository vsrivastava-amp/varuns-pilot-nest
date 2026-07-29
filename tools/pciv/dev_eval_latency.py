"""General latency test for online-pciv-service / llm-evaluator-service eval ids.

Fires single-query POSTs at a service endpoint (default: the dev
online-pciv-service ingress, /v1/intent/civ where the 6xx screen/finalist
evals live) and reports p50/p95/p99 end-to-end latency per eval id.

Ballpark tool, not a load rig (AI-1538 / AI-1542; sustained-rate soak
de-scoped 2026-07-29). Designed to run as a Databricks spark_python task on a
CLASSIC cluster (serverless cannot resolve *.ric1.admarketplace.net) or from
any VPN-connected shell. stdlib-only; spark is used only if --queries-table.

Examples:

    # DBX job / VPN shell — finalists from dev, 50 samples each:
    python dev_eval_latency.py --eval-ids 601,604,607,609,610,612,613 \
        --queries-file queries.txt --n 50 --out /tmp/pciv_dev_latency.jsonl

    # Query source = Bhupesh's AI-1556 table (DBX only):
    python dev_eval_latency.py --eval-ids 601 \
        --queries-table dev_amplify.qwantai_testing_data.us_queries_gpc_lvl_3 \
        --queries-column query --n 30

Notes:
- bypassCache=true by default: we are measuring the LLM path, not DynamoDB.
- Eval ids interleave round-robin so provider-side drift over the run affects
  all evals equally.
- --warmup N (default 3) fires unmeasured requests per eval first: Mantle
  throughput ramps gradually and prompt caches need priming; warmup rows are
  still written to the JSONL with "warmup": true — filter, don't discard.
- Timestamps in rows are Unix epoch (UTC).
"""

import argparse
import json
import statistics
import sys
import time
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "https://dev-online-pciv-service.ric1.admarketplace.net"
DEFAULT_ENDPOINT = "/v1/intent/civ"


def post_eval(base_url, endpoint, eval_id, query, ad_request_id, bypass_cache, timeout):
    """One single-query extraction call. Returns a sample dict."""
    body = {
        "evalId": eval_id,
        "queries": [{"adRequestId": ad_request_id, "qt": query}],
        "bypassCache": bypass_cache,
    }
    req = urllib.request.Request(
        f"{base_url}{endpoint}",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    sample = {"eval_id": eval_id, "query": query, "ts": time.time()}
    t0 = time.perf_counter()
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        raw = resp.read()
        sample["http_status"] = resp.status
    except urllib.error.HTTPError as exc:
        sample["http_status"] = exc.code
        sample["error"] = exc.read().decode()[:300]
        sample["e2e_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        return sample
    except Exception as exc:  # timeout, DNS, connection reset
        sample["http_status"] = None
        sample["error"] = f"{type(exc).__name__}: {exc}"[:300]
        sample["e2e_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        return sample
    sample["e2e_ms"] = round((time.perf_counter() - t0) * 1000, 1)

    try:
        payload = json.loads(raw)
        summary = payload.get("summary") or {}
        sample["processing_ms"] = summary.get("processingMs")
        sample["success_count"] = summary.get("successCount")
        sample["failure_count"] = summary.get("failureCount")
        sample["llm_calls"] = summary.get("llmCalls")
        tokens = summary.get("tokensUsed") or {}
        sample["tokens_in"] = tokens.get("input")
        sample["tokens_out"] = tokens.get("output")
        sample["tokens_cache_read"] = tokens.get("cacheRead")
        if summary.get("failureCount"):
            errors = [e for r in payload.get("results", [])
                      for e in ([r.get("error")] if r.get("error") else [])]
            if errors:
                sample["error"] = json.dumps(errors[0])[:300]
    except (json.JSONDecodeError, AttributeError):
        sample["error"] = "unparseable response: " + raw[:200].decode(errors="replace")
    return sample


def load_queries(args):
    if args.queries_file:
        lines = [q.strip() for q in open(args.queries_file, encoding="utf-8")
                 if q.strip() and not q.startswith("#")]
        if not lines:
            sys.exit(f"no queries in {args.queries_file}")
        return lines
    if args.queries_table:
        from pyspark.sql import SparkSession  # DBX only
        spark = SparkSession.builder.getOrCreate()
        rows = (spark.table(args.queries_table)
                .select(args.queries_column).distinct()
                .limit(args.n * 4).collect())
        return [r[0] for r in rows if r[0] and r[0].strip()]
    sys.exit("need --queries-file or --queries-table")


def pctl(values, p):
    if not values:
        return None
    values = sorted(values)
    k = (len(values) - 1) * p / 100
    lo, hi = int(k), min(int(k) + 1, len(values) - 1)
    return round(values[lo] + (values[hi] - values[lo]) * (k - lo), 1)


def summarize(samples, eval_id):
    rows = [s for s in samples if s["eval_id"] == eval_id and not s.get("warmup")]
    ok = [s for s in rows if s.get("success_count") == 1 and s.get("http_status") == 200]
    if not rows:
        return None
    e2e = [s["e2e_ms"] for s in ok]
    proc = [s["processing_ms"] for s in ok if s.get("processing_ms") is not None]
    cache = [s["tokens_cache_read"] or 0 for s in ok]
    return {
        "eval_id": eval_id,
        "n": len(rows),
        "ok": len(ok),
        "errors": len(rows) - len(ok),
        "e2e_p50_ms": pctl(e2e, 50),
        "e2e_p95_ms": pctl(e2e, 95),
        "e2e_p99_ms": pctl(e2e, 99),
        "processing_p50_ms": pctl(proc, 50),
        "processing_p95_ms": pctl(proc, 95),
        "tokens_in_mean": round(statistics.mean(
            s["tokens_in"] for s in ok if s.get("tokens_in")), 0) if ok else None,
        "tokens_out_mean": round(statistics.mean(
            s["tokens_out"] for s in ok if s.get("tokens_out")), 0) if ok else None,
        "cache_read_mean": round(statistics.mean(cache), 0) if cache else None,
        "cache_hit_rate": round(sum(1 for c in cache if c > 0) / len(cache), 2) if cache else None,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL)
    ap.add_argument("--endpoint", default=DEFAULT_ENDPOINT,
                    help="/v1/intent/civ for the 6xx evals; /v1/intent/pciv for 10x")
    ap.add_argument("--eval-ids", required=True,
                    help="comma-separated, e.g. 601,604,607,609,610,612,613")
    ap.add_argument("--queries-file", help="one query per line, # comments ignored")
    ap.add_argument("--queries-table", help="spark table with a query column (DBX only)")
    ap.add_argument("--queries-column", default="query")
    ap.add_argument("--n", type=int, default=50, help="measured samples per eval id")
    ap.add_argument("--warmup", type=int, default=3,
                    help="unmeasured priming requests per eval id (cache/ramp)")
    ap.add_argument("--no-bypass-cache", action="store_true",
                    help="let DynamoDB cache serve hits (default bypasses it)")
    ap.add_argument("--timeout", type=int, default=60, help="per-request timeout, seconds")
    ap.add_argument("--out", default="/tmp/pciv_dev_latency.jsonl",
                    help="JSONL rows, append mode")
    args = ap.parse_args()

    eval_ids = [int(e) for e in args.eval_ids.split(",")]
    queries = load_queries(args)
    bypass = not args.no_bypass_cache
    run_id = f"latency-{int(time.time())}"
    print(f"run_id={run_id} base={args.base_url}{args.endpoint} evals={eval_ids} "
          f"n={args.n} warmup={args.warmup} bypassCache={bypass} queries={len(queries)}",
          flush=True)

    samples = []
    with open(args.out, "a", encoding="utf-8") as out:
        def record(sample, warmup=False):
            sample["run_id"] = run_id
            if warmup:
                sample["warmup"] = True
            samples.append(sample)
            out.write(json.dumps(sample, ensure_ascii=False) + "\n")
            out.flush()

        for ev in eval_ids:
            for i in range(args.warmup):
                s = post_eval(args.base_url, args.endpoint, ev,
                              queries[i % len(queries)], 90_000_000 + i, bypass, args.timeout)
                record(s, warmup=True)
                print(f"  [warmup {ev} #{i}] e2e={s['e2e_ms']}ms "
                      f"err={s.get('error', '')[:80]}", flush=True)

        for i in range(args.n):
            for ev in eval_ids:  # interleaved: drift hits all evals equally
                q = queries[(args.warmup + i) % len(queries)]
                s = post_eval(args.base_url, args.endpoint, ev, q,
                              91_000_000 + i, bypass, args.timeout)
                record(s)
                flag = "" if s.get("success_count") == 1 else f" ** {s.get('error', 'FAIL')[:80]}"
                print(f"  [{ev} #{i}] e2e={s['e2e_ms']}ms proc={s.get('processing_ms')}ms "
                      f"cacheRead={s.get('tokens_cache_read')}{flag}", flush=True)

    print("\n=== summary (measured samples only; times in ms) ===")
    for ev in eval_ids:
        summary = summarize(samples, ev)
        if summary:
            print(json.dumps(summary))
    print(f"\nrows appended to {args.out}. e2e = caller wall time (network included); "
          "processing = server-reported. Quote e2e for the SSP conversation.", flush=True)


if __name__ == "__main__":
    main()
