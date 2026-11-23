#!/bin/bash
# Startet die App mit dem Python aus dem Projekt-venv.
cd "$(dirname "$0")" || exit 1
if [ ! -x venv/bin/python ]; then
    echo "Kein venv gefunden – zuerst ./install_desktop.sh ausführen." >&2
    exit 1
fi
exec venv/bin/python main.py "$@"
