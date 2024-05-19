#!/bin/bash
echo "lartu.net" > docs/CNAME
git add --all
git commit -m "Upload $(date)"
git push
