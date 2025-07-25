#!/bin/bash
set -e
python3 makompile.py
echo "lartu.net" > docs/CNAME
git add --all
git commit -m "Upload $(date)"
git push
