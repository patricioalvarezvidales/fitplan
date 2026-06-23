#!/usr/bin/env bash
set -euo pipefail

printf "Git:    "; git --version
printf "Docker: "; docker --version
printf "Compose:"; docker compose version
printf "Node:   "; node --version
printf "npm:    "; npm --version
printf "Python: "; python3 --version

echo
echo "Entorno básico disponible."
