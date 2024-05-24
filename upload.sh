#!/bin/bash
python3 scfl_build.py
echo "lartu.net" > docs/CNAME
git add --all
git commit -m "Upload $(date)"
git push
