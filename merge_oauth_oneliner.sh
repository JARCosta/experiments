#!/bin/bash

# One-liner version to merge OAuth files
echo "{$(for f in *_OAUTH; do [ -f "$f" ] && echo -n "\"$(basename "$f" _OAUTH)\": \"$(cat "$f" | tr -d '\n\r')\", "; done | sed 's/, $//')}" > OAUTH.json && echo "OAuth files merged into OAUTH.json" 