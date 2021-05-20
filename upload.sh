date >> changelog
git diff --stat --relative source | grep -E ".*\.coso.*" >> changelog
python3 coso.py --save-changelog
git add --all
git commit -m "Upload $(date)"
git push
