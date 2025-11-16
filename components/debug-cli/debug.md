docker compose up -d debug-cli

### Step 1: Get the Presigned POST Data

First, you need the Presigned POST URL and the required fields from your FastAPI backend. We'll use `curl` to simulate the frontend's API call.

1.  **Find the `debug-cli` container ID:**
    ```bash
    docker ps

2.  **Create a dummy file locally:**
    ```bash
    echo "This is a test file for S3 upload debug." > dummy.txt

3.  **Copy the dummy file into the running CLI container:**
    ```bash
    docker cp dummy.txt debates-debug-cli-1:/tmp/dummy.txt

### Step 2: Get the Presigned POST Upload

4.  **Execute the API call from the CLI container:** (Replace `[CONTAINER_ID]` with the ID from the previous step.)

    ```bash
    docker exec -it debates-debug-cli-1 sh -c "
    curl -s -X POST http://backend:8000/get-presigned-post \
    -H 'Content-Type: application/json' \
    -d '{\"filename\":\"dummy.txt\"}'
    "
    ```

    The output will be a JSON object containing the POST URL and the hidden fields:
    ```json
    {"postUrl":"http://minio-instance:9000/debates","fields":{"acl":"public-read","success_action_status":"201","key":"6bf076c9-6822-442f-a004-607b16d10c81/media/dummy.txt","AWSAccessKeyId":"minio_user","policy":"eyJleHBpcmF0aW9uIjogIjIwMjUtMTEtMTZUMDY6Mzk6NDZaIiwgImNvbmRpdGlvbnMiOiBbeyJhY2wiOiAicHVibGljLXJlYWQifSwgeyJidWNrZXQiOiAiZGViYXRlcyJ9LCBbInN0YXJ0cy13aXRoIiwgIiRrZXkiLCAiNmJmMDc2YzktNjgyMi00NDJmLWEwMDQtNjA3YjE2ZDEwYzgxL21lZGlhL2R1bW15LnR4dCJdLCBbImNvbnRlbnQtbGVuZ3RoLXJhbmdlIiwgMSwgNTI0Mjg4MDAwXSwgeyJzdWNjZXNzX2FjdGlvbl9zdGF0dXMiOiAiMjAxIn0sIHsiYnVja2V0IjogImRlYmF0ZXMifSwgeyJrZXkiOiAiNmJmMDc2YzktNjgyMi00NDJmLWEwMDQtNjA3YjE2ZDEwYzgxL21lZGlhL2R1bW15LnR4dCJ9XX0=","signature":"AgUlTh2R7hNP7vj2ccUXKE7lG4M="},"jobId":"6bf076c9-6822-442f-a004-607b16d10c81","s3Key":"6bf076c9-6822-442f-a004-607b16d10c81/media/dummy.txt"}%
    ```

### Step 3: Execute the Presigned POST Upload

Now we use the `postUrl` and `fields` to upload a dummy file. You'll need to create a small dummy file (e.g., `dummy.txt`) locally for this test.

3.  **Execute the `curl` POST command:** (Replace the values below with the actual output from Step 2.)

    ```bash
        docker exec -it debates-debug-cli-1 sh -c "
        curl -v -X POST 'http://minio-instance:9000/debates' \
        -F 'key=6bf076c9-6822-442f-a004-607b16d10c81/media/dummy.txt' \
        -F 'AWSAccessKeyId=minio_user' \
        -F 'policy=eyJleHBpcmF0aW9uIjogIjIwMjUtMTEtMTZUMDY6Mzk6NDZaIiwgImNvbmRpdGlvbnMiOiBbeyJhY2wiOiAicHVibGljLXJlYWQifSwgeyJidWNrZXQiOiAiZGViYXRlcyJ9LCBbInN0YXJ0cy13aXRoIiwgIiRrZXkiLCAiNmJmMDc2YzktNjgyMi00NDJmLWEwMDQtNjA3YjE2ZDEwYzgxL21lZGlhL2R1bW15LnR4dCJdLCBbImNvbnRlbnQtbGVuZ3RoLXJhbmdlIiwgMSwgNTI0Mjg4MDAwXSwgeyJzdWNjZXNzX2FjdGlvbl9zdGF0dXMiOiAiMjAxIn0sIHsiYnVja2V0IjogImRlYmF0ZXMifSwgeyJrZXkiOiAiNmJmMDc2YzktNjgyMi00NDJmLWEwMDQtNjA3YjE2ZDEwYzgxL21lZGlhL2R1bW15LnR4dCJ9XX0=' \
        -F 'signature=AgUlTh2R7hNP7vj2ccUXKE7lG4M=' \
        -F 'acl=public-read' \
        -F 'success_action_status=201' \
        -F 'file=@/tmp/dummy.txt'
        "
        *Note: The `-F` flag handles multipart form data. The field for the file **must** be the last one and **must be named `file`** (or whatever you set in your S3 policy), using `@/path/to/file`.*

### 🔍 Debugging the Output

* **Success:** You should see an HTTP status of **`201 Created`** in the verbose output (`-v`).
* **Failure:** If you get an error (e.g., `403 Forbidden`, `400 Bad Request`), the output text will contain the S3 XML error message (`<Error><Code>...</Code><Message>...</Message>`). This message will tell you *exactly* which policy or signature field is invalid, allowing you to fix the Python logic in `backend/s3.py`.