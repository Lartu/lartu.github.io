#!/bin/bash
cd "$(dirname "$0")"

date >> changelog
git diff --stat --relative source | grep -E ".*\.coso.*" >> changelog
python3 coso2/coso_fp.py --save-changelog
sleep 1
git add --all
git commit -m "Upload $(date)"
git push
