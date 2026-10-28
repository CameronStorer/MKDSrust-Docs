#!/bin/sh
# ROM-free wrapper regression checks; run with sh tests/shell_scripts.sh.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
REPO="$TMP/repo with spaces"
mkdir -p "$REPO" "$TMP/bin" "$TMP/caller"
cp "$ROOT/build.sh" "$ROOT/play.sh" "$REPO/"
export CALLS="$TMP/calls"
cat > "$TMP/bin/cargo" <<'EOF'
#!/bin/sh
printf '%s\n' "$@" > "$CALLS.cargo"
[ "${FAIL_CARGO:-0}" -eq 0 ] || exit 17
while [ "$1" != --target-dir ]; do shift; done
mkdir -p "$2/release"
cat > "$2/release/mkds_builder" <<'BUILDER'
#!/bin/sh
printf '%s\n' "$@" > "$CALLS.builder"
exit "${FAIL_BUILDER:-0}"
BUILDER
chmod +x "$2/release/mkds_builder"
EOF
chmod +x "$TMP/bin/cargo"
export PATH="$TMP/bin:$PATH"
cd "$TMP/caller"
touch 'my game.nds'
if sh "$REPO/build.sh" >/dev/null 2>&1; then exit 1; fi
if sh "$REPO/build.sh" missing.nds >/dev/null 2>&1; then exit 1; fi
sh "$REPO/build.sh" 'my game.nds' 'custom output' >/dev/null
printf '%s\n' 'my game.nds' --build --source "$REPO" --out 'custom output' > "$TMP/expected"
cmp "$TMP/expected" "$CALLS.builder"
sh "$REPO/build.sh" 'my game.nds' >/dev/null
test "$(tail -n 1 "$CALLS.builder")" = "$REPO/builds/mkds"
if FAIL_CARGO=17 sh "$REPO/build.sh" 'my game.nds' >/dev/null 2>&1; then exit 1; else test "$?" -eq 17; fi
if FAIL_BUILDER=19 sh "$REPO/build.sh" 'my game.nds' >/dev/null 2>&1; then exit 1; else test "$?" -eq 19; fi
if sh "$REPO/play.sh" >/dev/null 2>&1; then exit 1; fi
mkdir -p "$REPO/builds/mkds"
cat > "$REPO/builds/mkds/play" <<'EOF'
#!/bin/sh
printf '%s\n' "$@" > "$CALLS.play"
exit 23
EOF
chmod +x "$REPO/builds/mkds/play"
if sh "$REPO/play.sh" --capture 'path with spaces' >/dev/null; then exit 1; else test "$?" -eq 23; fi
printf '%s\n' --capture 'path with spaces' > "$TMP/expected"
cmp "$TMP/expected" "$CALLS.play"
echo 'Shell wrapper checks passed.'
