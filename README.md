**Active repo moved to `ku-applications` 2026-10-06. Retaining this repo temporarily for reference.**

This repo contains the files necessary for running a customized front end for Datasette 
(https://datasette.io/). The script to build the SQLite db and the source metadata files
are hosted separately on KU servers.

# Running Datasette locally for KU student newspaper project

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

   *(now running at http://127.0.0.1:8001)(

# Check for flagged OCR items

3. start new instance of Datasette with different db

    datasette serve flags.db --port 8002

    *(now running at http://127.0.0.1:8002)*
