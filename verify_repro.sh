#!/usr/bin/env bash
# Reproducibility harness: run every figures/*.py offline, from cached data,
# and report OK/FAIL per script. This is the proof the papers' 40+
# "reproducible from the scripts" claims were missing.
set -u
PY="${PY:-python}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT" || exit 1
total=0; ok=0; skip=0; fail=0
echo "REPRODUCIBILITY RUN  $(date '+%Y-%m-%d %H:%M:%S')"
echo "python: $("$PY" -c 'import sys;print(sys.version.split()[0])')"
echo "================================================================"
while IFS= read -r f; do
  dir=$(dirname "$f"); base=$(basename "$f")
  total=$((total+1))
  out=$( cd "$dir" && timeout 60 "$PY" "$base" 2>&1 ); rc=$?
  if printf "%s" "$out" | grep -q '^SKIPPED'; then
    skip=$((skip+1)); printf "[SKIP] %s :: %s\n" "$f" "$(printf '%s' "$out" | grep -m1 '^SKIPPED')"
  elif [ $rc -eq 0 ]; then
    ok=$((ok+1)); printf "[OK]   %s\n" "$f"
  else
    fail=$((fail+1))
    last=$(printf "%s" "$out" | grep -viE '^\s*$' | tail -1)
    printf "[FAIL] %s :: %s\n" "$f" "$last"
  fi
done < <(find . -path '*/figures/*.py' -not -path './.git*' | sort)
echo "================================================================"
echo "RESULT: total=$total  ok=$ok  skipped=$skip  fail=$fail"
echo "(skipped = needs private data, disclosed in the caption; not reproducible by design)"
