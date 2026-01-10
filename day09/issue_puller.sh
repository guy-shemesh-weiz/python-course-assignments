gh issue list -R Code-Maven/wis-python-course-2025-10 --limit 10000 --state all \
  --json number,state,title,createdAt,closedAt \
| jq -r '
  .[]
  | [
      .number,
      .state,
      .title,
      .createdAt,
      (.closedAt // "")
    ]
  | @tsv
' > issues.txt
