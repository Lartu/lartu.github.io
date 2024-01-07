#!/bin/bash
status_list=$(git diff --stat HEAD HEAD~1 | grep -q '.html')
status_list="${status_list/docs\//}"
status_list=$(echo "$status_list" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | tr -d '\n')

if [ ${#status_list} -gt 0 ] ; then
    echo ""
    echo ""
    echo "<h5>$(date)</h5>"
    echo "<p class=\"par changelog\">"
    # echo "<i>" `git diff --stat HEAD HEAD~1 | tail -n 1` "</i><br>"
    echo "$status_list" | grep '.html' | awk 'ORS="<br>\n"' | sed 's/-\{1,\}/<span class="rem">--<\/span>/g; s/+\{1,\}/<span class="add">++<\/span>/g'
    echo "</p>"
fi