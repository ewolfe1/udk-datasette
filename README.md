
# Running Datasette instance for KU student newspaper project

1. start virtual environment and install py libraries: `requirements.txt`

2. start Datasette

    datasette serve -i kansan.db \
      --inspect-file counts.json \
      --metadata kansan.yaml \
      --template-dir templates/ \
      --static static:static/ \
      --setting sql_time_limit_ms 15000 \
      --setting max_returned_rows 10000

3. now running at http://127.0.0.1:8001
