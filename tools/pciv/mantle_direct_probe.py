"""Direct laptop -> Bedrock Mantle latency probe at the REAL pciv prompt.

Upper bound for provider latency (laptop->us-east-1 adds network the EKS pod
won't have). Bypasses the service entirely: no LangChain, no FastAPI, no
DynamoDB. Each model is measured two ways:

  persistent : one httpx client + one bearer token reused for every request
  fresh      : new httpx client + new bearer token per request (what the
               service does today -- providers.get_chat_model is not cached)

The delta between the two IS the connection-churn/token-generation tax.

Captures per request: e2e, input/cached/output/reasoning tokens, finish
reason, Mantle request id.

WHAT e2e_ms ACTUALLY MEASURES: client.post() alone -- serialization, network
round trip, server prefill+generation, and reading the full (non-streamed)
response body. It EXCLUDES bearer-token generation (timed separately as
token_gen_ms), the TLS handshake (paid once in the persistent case), and all
service overhead. The field is named e2e_ms for continuity with
dev_eval_latency.py, but it is a provider round trip. Do not quote it as a
product latency.

Run (laptop):
    cd ~/Documents/llm-evaluator-service-online-pciv
    AWS_PROFILE=dev PROBE_N=12 .venv/bin/python \
        ~/pilots-nest/tools/pciv/mantle_direct_probe.py out.jsonl

Run (EC2/pod in the dev VPC -- the in-network number, next step as of
2026-07-31): needs boto3-resolvable creds (instance role or IRSA with
bedrock-mantle:CallWithBearerToken + CreateInference), httpx,
aws-bedrock-token-generator, and copies of pciv_extraction.txt and the FR
query CSV. Override PROMPT/QUERIES below if the paths differ. Running this
from inside vpc-0317d6910f3add39a also settles the PrivateLink question:
compare against the laptop numbers in
state/mantle-direct-pciv-prompt-20260731.md.
"""

import csv
import json
import os
import random
import statistics
import sys
import time

import httpx
from aws_bedrock_token_generator import provide_token

REGION = "us-east-1"
os.environ.setdefault("AWS_REGION", REGION)  # provide_token() reads this
ROOT = f"https://bedrock-mantle.{REGION}.api.aws"
SVC = os.path.expanduser("~/Documents/llm-evaluator-service-online-pciv")
PROMPT = f"{SVC}/src/main/python/domains/pciv_online/prompts/pciv_extraction.txt"
QUERIES = os.path.expanduser(
    "~/pilots-nest/review/qwant_fr_queries_sample_20260724.csv")

# mirrors llm/config/models.json finalist entries exactly
MODELS = [
    {"key": "luna", "id": "openai.gpt-5.6-luna", "path": "openai/v1",
     "api": "responses", "temperature": 1, "reasoning_effort": "none"},
    {"key": "gemma4-31b", "id": "google.gemma-4-31b", "path": "openai/v1",
     "api": "chat", "temperature": 0.0},
    {"key": "qwen3-next-80b", "id": "qwen.qwen3-next-80b-a3b-instruct",
     "path": "v1", "api": "chat", "temperature": 0.0},
    {"key": "ministral-3-14b", "id": "mistral.ministral-3-14b-instruct",
     "path": "v1", "api": "chat", "temperature": 0.0},
]

MAX_TOKENS = 2000
TIMEOUT = 30.0
WARMUP = int(os.environ.get("PROBE_WARMUP", "3"))
N = int(os.environ.get("PROBE_N", "12"))


def build_body(m, system_prompt, query):
    if m["api"] == "responses":
        return f"{ROOT}/{m['path']}/responses", {
            "model": m["id"],
            "instructions": system_prompt,
            "input": query,
            "reasoning": {"effort": m["reasoning_effort"]},
            "max_output_tokens": MAX_TOKENS,
            "temperature": m["temperature"],
        }
    return f"{ROOT}/{m['path']}/chat/completions", {
        "model": m["id"],
        "messages": [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": query}],
        "max_tokens": MAX_TOKENS,
        "temperature": m["temperature"],
    }


def parse_usage(m, payload):
    u = payload.get("usage") or {}
    out = {}
    if m["api"] == "responses":
        out["tokens_in"] = u.get("input_tokens")
        out["tokens_out"] = u.get("output_tokens")
        out["tokens_cached"] = (u.get("input_tokens_details") or {}).get("cached_tokens")
        out["tokens_reasoning"] = (u.get("output_tokens_details") or {}).get("reasoning_tokens")
        out["finish"] = payload.get("status")
        texts = []
        for item in payload.get("output") or []:
            for c in item.get("content") or []:
                if c.get("type") == "output_text":
                    texts.append(c.get("text", ""))
        out["reply_chars"] = len("".join(texts))
    else:
        out["tokens_in"] = u.get("prompt_tokens")
        out["tokens_out"] = u.get("completion_tokens")
        out["tokens_cached"] = (u.get("prompt_tokens_details") or {}).get("cached_tokens")
        out["tokens_reasoning"] = (u.get("completion_tokens_details") or {}).get("reasoning_tokens")
        choices = payload.get("choices") or [{}]
        out["finish"] = choices[0].get("finish_reason")
        out["reply_chars"] = len(((choices[0].get("message") or {}).get("content")) or "")
    return out


def call(client, token, m, system_prompt, query):
    url, body = build_body(m, system_prompt, query)
    sample = {"model": m["key"], "query": query, "ts": time.time()}
    t0 = time.perf_counter()
    try:
        r = client.post(url, json=body, timeout=TIMEOUT,
                        headers={"Authorization": f"Bearer {token}",
                                 "Content-Type": "application/json"})
        sample["e2e_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        sample["http_status"] = r.status_code
        sample["mantle_request_id"] = (r.headers.get("x-amzn-requestid")
                                       or r.headers.get("x-request-id"))
        if r.status_code != 200:
            sample["error"] = r.text[:300]
            return sample
        sample.update(parse_usage(m, r.json()))
    except Exception as exc:
        sample["e2e_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        sample["http_status"] = None
        sample["error"] = f"{type(exc).__name__}: {exc}"[:300]
    return sample


def pctl(vals, p):
    if not vals:
        return None
    vals = sorted(vals)
    k = (len(vals) - 1) * p / 100
    lo, hi = int(k), min(int(k) + 1, len(vals) - 1)
    return round(vals[lo] + (vals[hi] - vals[lo]) * (k - lo), 1)


def main():
    system_prompt = open(PROMPT, encoding="utf-8").read()
    rows = list(csv.DictReader(open(QUERIES, encoding="utf-8")))
    rnd = random.Random(1538)
    pool = [r["query"] for r in rows if len(r["query"].split()) >= 2]
    queries = rnd.sample(pool, WARMUP + N)

    out_path = sys.argv[1]
    print(f"prompt={len(system_prompt)}B  queries={len(queries)} "
          f"(warmup {WARMUP} + measured {N})  models={[m['key'] for m in MODELS]}",
          flush=True)

    samples = []
    with open(out_path, "a", encoding="utf-8") as fh:
        def rec(s, connection, warm=False):
            s["connection"] = connection
            if warm:
                s["warmup"] = True
            samples.append(s)
            fh.write(json.dumps(s, ensure_ascii=False) + "\n")
            fh.flush()

        # ---- persistent connection + token reused ----
        token = provide_token()
        with httpx.Client(http2=False, limits=httpx.Limits(
                max_keepalive_connections=8, keepalive_expiry=120)) as client:
            for i in range(WARMUP):
                for m in MODELS:
                    s = call(client, token, m, system_prompt, queries[i])
                    rec(s, "persistent", warm=True)
                    print(f"  [warm persistent {m['key']} #{i}] {s['e2e_ms']}ms "
                          f"in={s.get('tokens_in')} cached={s.get('tokens_cached')} "
                          f"{str(s.get('error',''))[:70]}", flush=True)
            for i in range(N):
                for m in MODELS:  # interleaved
                    s = call(client, token, m, system_prompt, queries[WARMUP + i])
                    rec(s, "persistent")
                    print(f"  [persistent {m['key']} #{i}] {s['e2e_ms']}ms "
                          f"in={s.get('tokens_in')} cached={s.get('tokens_cached')} "
                          f"out={s.get('tokens_out')} reas={s.get('tokens_reasoning')} "
                          f"{str(s.get('error',''))[:70]}", flush=True)

        # ---- new connection + fresh token per request ----
        for i in range(N):
            for m in MODELS:
                t0 = time.perf_counter()
                tok = provide_token()
                tok_ms = round((time.perf_counter() - t0) * 1000, 1)
                with httpx.Client() as client:
                    s = call(client, tok, m, system_prompt, queries[WARMUP + i])
                s["token_gen_ms"] = tok_ms
                rec(s, "fresh")
                print(f"  [fresh {m['key']} #{i}] {s['e2e_ms']}ms "
                      f"tokengen={tok_ms}ms in={s.get('tokens_in')} "
                      f"cached={s.get('tokens_cached')} "
                      f"{str(s.get('error',''))[:70]}", flush=True)

    print("\n=== summary (measured only, ms) ===")
    for conn in ("persistent", "fresh"):
        for m in MODELS:
            rs = [s for s in samples if s["model"] == m["key"]
                  and s["connection"] == conn and not s.get("warmup")]
            ok = [s for s in rs if s.get("http_status") == 200]
            e2e = [s["e2e_ms"] for s in ok]
            cached = [s.get("tokens_cached") or 0 for s in ok]
            reas = [s.get("tokens_reasoning") or 0 for s in ok]
            print(json.dumps({
                "connection": conn, "model": m["key"], "n": len(rs), "ok": len(ok),
                "p50": pctl(e2e, 50), "p95": pctl(e2e, 95), "p99": pctl(e2e, 99),
                "min": round(min(e2e), 1) if e2e else None,
                "max": round(max(e2e), 1) if e2e else None,
                "in_mean": round(statistics.mean(
                    [s["tokens_in"] for s in ok if s.get("tokens_in")]), 0) if ok else None,
                "out_mean": round(statistics.mean(
                    [s["tokens_out"] for s in ok if s.get("tokens_out")]), 0) if ok else None,
                "cached_mean": round(statistics.mean(cached), 0) if cached else None,
                "cache_hit_rate": round(sum(1 for c in cached if c > 0) / len(cached), 2) if cached else None,
                "reasoning_mean": round(statistics.mean(reas), 1) if reas else None,
                "token_gen_p50": pctl([s["token_gen_ms"] for s in rs if s.get("token_gen_ms")], 50),
            }))
    print(f"\nrows -> {out_path}")


if __name__ == "__main__":
    main()
