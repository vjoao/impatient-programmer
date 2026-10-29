#!/bin/sh
# Usage: scripts/link-skills.sh [skills-dir]   (default: ~/.cursor/skills)
# Links every skill in skills/ into skills-dir, so the agent loads them from this repo.
set -eu

repo=$(cd "$(dirname "$0")/.." && pwd)
target=${1:-"$HOME/.cursor/skills"}
mkdir -p "$target"

for skill in "$repo"/skills/*/; do
  name=$(basename "$skill")
  link="$target/$name"
  if [ -e "$link" ] && [ ! -L "$link" ]; then
    echo "skipped $name: $link is a real folder, not a link" >&2
    continue
  fi
  ln -sfn "$repo/skills/$name" "$link"
  echo "linked $link"
done
