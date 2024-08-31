#!/bin/bash
set -e
rm -rf docs
sh regenerate.sh
mkdir docs
mv *.html docs
cp -r include docs
cp -r images docs
cp -r files docs  # EF!! PDR!!
echo "lartu.net" > docs/CNAME
git add --all
git commit -m "Upload $(date)"
git push
