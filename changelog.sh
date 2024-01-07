#!/bin/bash
echo ""
echo ""
echo "<h5>$(date)</h5>"
echo "<p class=\"par changelog\">"
echo "<i>" `git diff --stat HEAD HEAD~1 | tail -n 1` "</i><br>"
status_list=`git diff --stat HEAD HEAD~1`
status_list="${status_list/docs\//}"
echo "$status_list" | grep '.html' | awk 'ORS="<br>\n"' | sed 's/-\{1,\}/<span class="rem">--<span>/g; s/+\{1,\}/<span class="add">++<span>/g'
echo "</p>"