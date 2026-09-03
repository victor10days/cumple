#!/bin/zsh
# Build "cumple QC.app", a drag-and-drop front end for cumple check.
# Usage: zsh integrations/macos/build_app.sh [output dir]   (default: ~/Applications)
set -e
here=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$here/../.." && pwd)
out=${1:-"$HOME/Applications"}
mkdir -p "$out"
bin=$(command -v cumple 2>/dev/null || true)
[ -z "$bin" ] && [ -x "$repo/.venv/bin/cumple" ] && bin="$repo/.venv/bin/cumple"
if [ -z "$bin" ]; then echo "cumple is not installed; run 'uv sync' in $repo or 'uv tool install cumple' first" >&2; exit 1; fi
tmp=$(mktemp -t cumple-qc).applescript
sed "s|CUMPLE_BIN_PLACEHOLDER|$bin|" "$here/cumple-qc.applescript" > "$tmp"
rm -rf "$out/cumple QC.app"
osacompile -o "$out/cumple QC.app" "$tmp"
# Let Finder offer it for audio files and folders (droplet apps accept anything by default).
echo "built: $out/cumple QC.app  (cumple at $bin)"
echo "Drop a WAV or a delivery folder on it, pick the destination, and the QC sheet opens."
