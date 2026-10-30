# Profile C or Python code with Postman

Start SMART with the [Docker guide](run-with-docker.md) or the [native guide](run-native.md), and confirm that `GET http://127.0.0.1:8000/health` succeeds. Classical C and Python profiling does not require a model service or API key.

This guide uses `http://127.0.0.1:8000` as the server address. The screenshots show an earlier Python profiling session using a Postman variable named `url`; set that variable to your server's base URL or enter the URL directly. Use the task ID and result path returned by your own requests.

## Submit a profiling task

In Postman, create a **POST** request to `http://127.0.0.1:8000/tasks`. Under **Body → form-data**, add:

| Field | Postman field type | Value |
|---|---|---|
| `task_type` | Text | `profile` |
| `language` | Text | `python` for a `.py` file, or `c` for a `.c` file |
| `file` | File | Select the source file from the machine running Postman |

Send the request. Postman uploads the selected file, so the source file does not need to be mounted into the server container. The response contains a `task_id` and the initial task status.

![Postman submitting a Python profiling task with multipart form data and receiving a task ID](../images/use_case_2_1.png)

## Check the task status

Create a **GET** request to `http://127.0.0.1:8000/tasks/REPLACE_WITH_TASK_ID`, replacing the placeholder with the returned ID. Repeat while the status is `pending` or `running`.

When the status becomes `completed`, copy `task_result.file_path`. If it becomes `failed`, inspect `task_result.error` and the server log.

![Postman polling a completed profiling task and displaying its result file path](../images/use_case_2_2.png)

## Retrieve the profiling report

Create a **GET** request to `http://127.0.0.1:8000/files/download`. In **Params**, add `file_path` and paste the value returned by the completed task. Send the request to retrieve the report.

![Postman downloading a profiling report using the file_path query parameter](../images/use_case_2_3.png)

Paths, task IDs, and profiling timings in these screenshots are examples from that session. For request fields and result persistence, see the [REST and MCP API reference](../reference/api.md).

[Back to README](../../README.md)
