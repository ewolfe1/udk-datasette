
# Running Datasette instance for KU student newspaper project

1. start virtual environment and install libraries

    `source venv/bin/activate`

    `pip install -r requirements.txt`

2. start Datasette

    datasette serve -i kansan.db \
      --inspect-file counts.json \
      --metadata kansan.yaml \
      --template-dir templates/ \
      --static static:static/ \
      --plugins-dir plugins/ \
      --setting sql_time_limit_ms 15000 \
      --setting max_returned_rows 10000

3. now running at http://127.0.0.1:8001

4. To check flagged OCR items:

    datasette serve flags.db --port 8002

    now running at http://127.0.0.1:8002
