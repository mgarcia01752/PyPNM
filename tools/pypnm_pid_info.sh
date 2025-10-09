#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia
#
# pypnm_pid_info.sh — quick snapshot of PIDs, RSS, ports, and ancestry
#
# Usage:
#   ./pypnm_pid_info.sh                 # scan common names: python|uvicorn|gunicorn|pypnm
#   ./pypnm_pid_info.sh -n 'pypnm'      # scan by name/cmdline regex
#   ./pypnm_pid_info.sh -p 8000         # include processes listening on port 8000
#   ./pypnm_pid_info.sh -n 'gunicorn' -p 8000
#
# Linux & macOS compatible (uses lsof for ports; falls back to ss on Linux).

set -euo pipefail

NAME_REGEX='python|uvicorn|gunicorn|pypnm'
PORT_FILTER=''
SHOW_PORTS=0

while getopts ":n:p:h" opt; do
  case "$opt" in
    n) NAME_REGEX="$OPTARG" ;;
    p) PORT_FILTER="$OPTARG"; SHOW_PORTS=1 ;;
    h)
      echo "Usage: $0 [-n name_regex] [-p port]"
      exit 0
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2; exit 2 ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2; exit 2 ;;
  esac
done

_have() { command -v "$1" >/dev/null 2>&1; }

# Humanize RSS (KB -> MB)
kb_to_mb() { awk -v kb="$1" 'BEGIN { printf "%.1f", kb/1024 }'; }

hr() { printf '%s\n' "$(printf '%.0s-' {1..72})"; }

echo "📌 Name regex: $NAME_REGEX"
if [[ $SHOW_PORTS -eq 1 ]]; then echo "📌 Port filter: $PORT_FILTER"; fi
hr

# 1) Listening ports → PIDs (if requested)
if [[ $SHOW_PORTS -eq 1 ]]; then
  echo "🔎 Listening sockets on port $PORT_FILTER"
  if _have lsof; then
    # PID,COMMAND,USER,FD,TYPE,DEVICE,SIZE/OFF,NODE,NAME
    lsof -nP -iTCP:"$PORT_FILTER" -sTCP:LISTEN 2>/dev/null | awk 'NR==1 || NR>1{print}'
  elif _have ss; then
    ss -lptn "sport = :$PORT_FILTER" || true
  else
    echo "lsof/ss not found; skipping port inspection."
  fi
  hr
fi

# 2) Process snapshot
# Fields: PID PPID CPU% MEM% RSS(KB) START TIME COMMAND
if [[ "$(uname -s)" == "Darwin" ]]; then
  # macOS ps fields differ slightly
  PS_FMT="pid,ppid,pcpu,pmem,rss,lstart,command"
  PS_CMD="ps -axo $PS_FMT"
else
  PS_FMT="pid,ppid,pcpu,pmem,rss,lstart,args"
  PS_CMD="ps -eo $PS_FMT"
fi

echo "🧵 Matching processes:"
# shellcheck disable=SC2009
$PS_CMD | awk -v re="$NAME_REGEX" 'NR==1 || $0 ~ re' | while IFS= read -r line; do
  if [[ "$line" == *PID*PPID* ]] || [[ "$line" =~ ^[[:space:]]*PID ]]; then
    printf "%s\n" "PID   PPID  CPU  MEM  RSS(MB)   START                 CMD"
    continue
  fi
  # Parse columns robustly: first 5 numeric/known fields, then the rest is CMD
  pid=$(echo "$line" | awk '{print $1}')
  ppid=$(echo "$line" | awk '{print $2}')
  cpu=$(echo "$line" | awk '{print $3}')
  mem=$(echo "$line" | awk '{print $4}')
  rss_kb=$(echo "$line" | awk '{print $5}')
  start=$(echo "$line" | awk '{print $6" "$7" "$8" "$9" "$10}')
  cmd=$(echo "$line" | cut -d ' ' -f 11-)
  rss_mb=$(kb_to_mb "${rss_kb:-0}")
  printf "%-5s %-5s %-4s %-4s %-8s %-20s %s\n" "$pid" "$ppid" "$cpu" "$mem" "$rss_mb" "$start" "$cmd"

  # Children (one level)
  if _have ps; then
    kids=$(ps -o pid=,comm= -pp "$pid" 2>/dev/null | sed 's/^/      child /')
    if [[ -n "${kids// /}" ]]; then
      echo "$kids"
    fi
  fi

  # Gunicorn workers (if master)
  if echo "$cmd" | grep -qi 'gunicorn' && _have pgrep; then
    workers=$(pgrep -P "$pid" 2>/dev/null || true)
    if [[ -n "$workers" ]]; then
      echo "      gunicorn workers: $workers"
    fi
  fi
done
hr

# 3) Optional: map port PIDs back to processes
if [[ $SHOW_PORTS -eq 1 && $(_have lsof || _have ss) ]]; then
  echo "🔗 Processes bound to port $PORT_FILTER (condensed)"
  if _have lsof; then
    lsof -nP -iTCP:"$PORT_FILTER" -sTCP:LISTEN 2>/dev/null \
      | awk 'NR>1{print $2}' \
      | sort -u \
      | while read -r p; do
          [[ -z "$p" ]] && continue
          $PS_CMD | awk -v P="$p" 'NR>1 && $1==P {pid=$1;ppid=$2;cpu=$3;mem=$4;rss=$5;cmd=""; for(i=11;i<=NF;i++) cmd=cmd" "$i; printf("  PID %s  CPU %s  MEM %s  RSS %s MB  CMD%s\n", pid,cpu,mem,rss/1024,cmd)}'
        done
  elif _have ss; then
    ss -lptn "sport = :$PORT_FILTER" | sed -n '2,$p' | while read -r ln; do
      pid=$(echo "$ln" | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' | head -n1)
      [[ -z "$pid" ]] && continue
      $PS_CMD | awk -v P="$pid" 'NR>1 && $1==P {pid=$1;ppid=$2;cpu=$3;mem=$4;rss=$5;cmd=""; for(i=11;i<=NF;i++) cmd=cmd" "$i; printf("  PID %s  CPU %s  MEM %s  RSS %s MB  CMD%s\n", pid,cpu,mem,rss/1024,cmd)}'
    done
  fi
  hr
fi

echo "✅ Done."
