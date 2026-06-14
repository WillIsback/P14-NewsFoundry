#!/bin/sh
set -e

echo "[entrypoint] Démarrage du backend NewsFoundry..."
exec python src/main.py