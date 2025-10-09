#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import argparse, os, sys, time, json, subprocess
from typing import List, Optional

# optional psutil (preferred). Falls back to resource where possible.
try:
    import psutil
    HAS_PSUTIL = True
except Exception:
    HAS_PSUTIL = False

try:
    import resource  # unix only
    HAS_RESOURCE = True
except Exception:
    HAS_RESOURCE = False

def _rss_bytes_pid(pid: int) -> int:
    if HAS_PSUTIL:
        try:
            p = psutil.Process(pid)
            return int(p.memory_info().rss)
        except Exception:
            return 0
    # best-effort on Unix without psutil
    if HAS_RESOURCE and pid == os.getpid():
        r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(r * 1024 if sys.platform.startswith("linux") else r)
    return 0

def _mb(n: int) -> float:
    return round(n / (1024 * 1024), 3)

def cmd_rss(pid: int, interval: float, duration: float, json_out: bool) -> int:
    end = time.time() + duration if duration > 0 else None
    samples = []
    while True:
        rss = _rss_bytes_pid(pid)
        ts = time.time()
        samples.append({"ts": ts, "rss_mb": _mb(rss)})
        if not json_out:
            print(f"{ts:.3f} rss_mb={_mb(rss):.3f}")
        if end and time.time() >= end:
            break
        time.sleep(interval)
    if json_out:
        print(json.dumps({"pid": pid, "samples": samples}, indent=2))
    return 0

def cmd_profile(argv: List[str], top: int, json_out: bool) -> int:
    # Run a command under tracemalloc in a child Python that prints metrics on exit.
    # This avoids mixing our CLI with the target process logic.
    code = f"""
import tracemalloc, json, sys, time, runpy
tracemalloc.start()
t0=time.time()
try:
    runpy.run_path(sys.argv[1], run_name="__main__")
    rc=0
except SystemExit as e:
    rc = e.code if isinstance(e.code,int) else 1
except Exception:
    rc=1
t1=time.time()
cur,peak = tracemalloc.get_traced_memory()
snap = tracemalloc.take_snapshot()
stats = [str(s) for s in snap.statistics("lineno")[:{top}]]
payload = {{"elapsed_s": round(t1-t0,3), "heap_current_mb": round(cur/1048576,3), "heap_peak_mb": round(peak/1048576,3), "top": stats}}
print(json.dumps(payload, indent=2))
sys.exit(rc)
"""
    if not argv:
        print("profile: missing target script; usage: pypnm-mem profile -- python your_script.py [args...]", file=sys.stderr)
        return 2
    cmd = [sys.executable, "-c", code] + argv
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.stdout:
        if json_out:
            # proc already prints JSON; forward
            print(proc.stdout.strip())
        else:
            print(proc.stdout.strip())
    if proc.stderr:
        print(proc.stderr.strip(), file=sys.stderr)
    return proc.returncode

def cmd_http(url: str, timeout: float, json_out: bool) -> int:
    # very small dependency-free HTTP (no TLS). Use curl for HTTPS or add requests if you prefer.
    import http.client, urllib.parse
    u = urllib.parse.urlparse(url)
    if u.scheme not in ("http",):
        print("http mode supports 'http://' only for stdlib client. Use curl for https.", file=sys.stderr)
        return 2
    conn = http.client.HTTPConnection(u.hostname, u.port or 80, timeout=timeout)
    path = u.path or "/"
    if u.query:
        path += "?" + u.query
    try:
        conn.request("GET", path)
        resp = conn.getresponse()
        data = resp.read().decode("utf-8", errors="replace")
        if json_out:
            print(data)
        else:
            print(data)
        return 0
    finally:
        conn.close()

def main() -> int:
    p = argparse.ArgumentParser(prog="pypnm-mem", description="PyPNM memory monitoring CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    s_rss = sub.add_parser("rss", help="Poll RSS of an existing PID")
    s_rss.add_argument("--pid", type=int, required=True)
    s_rss.add_argument("--interval", type=float, default=1.0)
    s_rss.add_argument("--duration", type=float, default=0.0, help="0 = run once")
    s_rss.add_argument("--json", action="store_true")

    s_prof = sub.add_parser("profile", help="Run a Python script under tracemalloc and report heap stats")
    s_prof.add_argument("--top", type=int, default=20, help="Top allocation lines to show")
    s_prof.add_argument("--json", action="store_true")
    s_prof.add_argument("sep", nargs=1, help="Use '--' then your script and args", metavar="--")
    s_prof.add_argument("argv", nargs=argparse.REMAINDER)

    s_http = sub.add_parser("http", help="Fetch memory metrics JSON from a management endpoint")
    s_http.add_argument("--url", required=True, help="http://host:port/path")
    s_http.add_argument("--timeout", type=float, default=5.0)
    s_http.add_argument("--json", action="store_true")

    args = p.parse_args()

    if args.cmd == "rss":
        return cmd_rss(args.pid, args.interval, args.duration, args.json)
    elif args.cmd == "profile":
        # Expect args.argv to begin with your script; allow optional leading 'python ...'
        argv = args.argv
        # Strip an optional leading 'python' placed by habit
        if argv and argv[0] in ("python", "python3"):
            argv = argv[1:]
        return cmd_profile(argv, args.top, args.json)
    elif args.cmd == "http":
        return cmd_http(args.url, args.timeout, args.json)
    return 0

if __name__ == "__main__":
    sys.exit(main())
