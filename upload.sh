#!/bin/bash
git add --all
git commit -m "Upload $(date)"
sh changelog.sh >> docs/changelog.html
git add --all
git commit -m "Update changelog"
git push
