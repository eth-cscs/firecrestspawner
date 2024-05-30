import json
import re
import pytest
from werkzeug.wrappers import Response


def tasks_handler(request):
    taskid = request.args.get("tasks")
    if taskid == "acct_352_id":
        ret = {
            "tasks": {
                taskid: {
                    "data": [
                        {
                            "jobid": "352",
                            "name": "firecrest_job_test",
                            "nodelist": "nid06227",
                            "nodes": "3",
                            "partition": "normal",
                            "start_time": "2021-11-29T16:31:07",
                            "state": "COMPLETED",
                            "time": "00:48:00",
                            "time_left": "2021-11-29T16:31:47",
                            "user": "username",
                        },
                    ],
                    "description": "Finished successfully",
                    "hash_id": taskid,
                    "last_modify": "2021-12-06T09:53:48",
                    "service": "compute",
                    "status": "200",
                    "task_id": taskid,
                    "task_url": f"TASK_IP/tasks/{taskid}",
                    "user": "username",
                }
            }
        }
        ret_status = 200

    if taskid == "acct_353_id":
        ret = {
            "tasks": {
                taskid: {
                    "data": {
                        "0": {
                            "job_data_err": "",
                            "job_data_out": "",
                            "job_file": "(null)",
                            "job_file_err": "stderr-file-not-found",
                            "job_file_out": "stdout-file-not-found",
                            "jobid": "353",
                            "name": "interactive",
                            "nodelist": "nid02357",
                            "nodes": "1",
                            "partition": "debug",
                            "start_time": "6:38",
                            "state": "RUNNING",
                            "time": "2022-03-10T10:11:34",
                            "time_left": "23:22",
                            "user": "username",
                        }
                    },
                    "description": "Finished successfully",
                    "hash_id": taskid,
                    "last_modify": "2021-12-06T09:53:48",
                    "service": "compute",
                    "status": "200",
                    "task_id": taskid,
                    "task_url": f"TASK_IP/tasks/{taskid}",
                    "user": "username",
                }
            }
        }
        ret_status = 200

    if taskid == "acct_354_id":
        ret = {
            "tasks": {
                taskid: {
                    "data": {
                        "0": {
                            "job_data_err": "",
                            "job_data_out": "",
                            "job_file": "(null)",
                            "job_file_err": "stderr-file-not-found",
                            "job_file_out": "stdout-file-not-found",
                            "jobid": "354",
                            "name": "interactive",
                            "nodelist": "",
                            "nodes": "1",
                            "partition": "debug",
                            "start_time": "",
                            "state": "PENDING",
                            "time": "2022-03-10T10:11:34",
                            "time_left": "23:22",
                            "user": "username",
                        }
                    },
                    "description": "Finished successfully",
                    "hash_id": taskid,
                    "last_modify": "2021-12-06T09:53:48",
                    "service": "compute",
                    "status": "200",
                    "task_id": taskid,
                    "task_url": f"TASK_IP/tasks/{taskid}",
                    "user": "username",
                }
            }
        }
        ret_status = 200

    if taskid == "acct_355_id":
        ret = {
            "tasks": {
                taskid: {
                    "data": [
                        {
                            "jobid": "355",
                            "name": "firecrest_job_test",
                            "nodelist": "nid06227",
                            "nodes": "3",
                            "partition": "normal",
                            "start_time": "2021-11-29T16:31:07",
                            "state": "FAILED",
                            "time": "00:48:00",
                            "time_left": "2021-11-29T16:31:47",
                            "user": "username",
                        },
                    ],
                    "description": "Finished successfully",
                    "hash_id": taskid,
                    "last_modify": "2021-12-06T09:53:48",
                    "service": "compute",
                    "status": "200",
                    "task_id": taskid,
                    "task_url": f"TASK_IP/tasks/{taskid}",
                    "user": "username",
                }
            }
        }
        ret_status = 200

    if taskid == "cancel_job_id":
        ret = {
            "tasks": {
                taskid: {
                    "data": "",
                    "description": "Finished successfully",
                    "hash_id": taskid,
                    "last_modify": "2021-12-06T10:42:06",
                    "service": "compute",
                    "status": "200",
                    "task_id": taskid,
                    "task_url": f"TASK_IP/tasks/{taskid}",
                    "user": "username",
                }
            }
        }
        ret_status = 200

    if taskid == "submit_upload_job_id_good":
        jobid = 353
        ret = {
            "tasks": {
                taskid: {
                    "data": {
                        "job_data_err": "",
                        "job_data_out": "",
                        "job_file": f"/path/to/firecrest/{taskid}/script.sh",
                        "job_file_err": f"/path/to/firecrest/{taskid}/slurm-35342667.out",  # noqa E501
                        "job_file_out": f"/path/to/firecrest/{taskid}/slurm-35342667.out",  # noqa E501
                        "jobid": jobid,
                        "result": "Job submitted",
                    },
                    "description": "Finished successfully",
                    "hash_id": taskid,
                    "last_modify": "2021-12-04T11:52:11",
                    "service": "compute",
                    "status": "200",
                    "task_id": taskid,
                    "task_url": f"TASK_IP/tasks/{taskid}",
                    "user": "username",
                }
            }
        }
        ret_status = 200

    if taskid == "submit_upload_job_id_job_failed":
        jobid = 355
        ret = {
            "tasks": {
                taskid: {
                    "data": {
                        "job_data_err": "",
                        "job_data_out": "",
                        "job_file": f"/path/to/firecrest/{taskid}/script.sh",
                        "job_file_err": f"/path/to/firecrest/{taskid}/slurm-35342667.out",  # noqa E501
                        "job_file_out": f"/path/to/firecrest/{taskid}/slurm-35342667.out",  # noqa E501
                        "jobid": jobid,
                        "result": "Job submitted",
                    },
                    "description": "Finished successfully",
                    "hash_id": taskid,
                    "last_modify": "2021-12-04T11:52:11",
                    "service": "compute",
                    "status": "200",
                    "task_id": taskid,
                    "task_url": f"TASK_IP/tasks/{taskid}",
                    "user": "username",
                }
            }
        }
        ret_status = 200

    if taskid == "submit_upload_job_id_no_jobid":
        ret = {
            "tasks": {
                "a46bed48e1841ccf56f7dbd02e815bc4": {
                    "created_at": "2024-03-13T16:24:36",
                    "data": "sbatch: error: cli_filter plugin terminated with error",  # noqa E501
                    "description": "Finished with errors",
                    "hash_id": "a46bed48e1841ccf56f7dbd02e815bc4",
                    "last_modify": "2024-03-13T16:24:39",
                    "service": "compute",
                    "status": "400",
                    "system": "daint",
                    "task_id": "a46bed48e1841ccf56f7dbd02e815bc4",
                    "updated_at": "2024-03-13T16:24:39",
                    "user": "sarafael",
                }
            }
        }
        ret_status = 400

    return Response(json.dumps(ret), status=ret_status, content_type="application/json")


def submit_upload_handler(request):
    if request.headers["Authorization"] != "Bearer VALID_TOKEN":
        return Response(
            json.dumps({"message": "Bad token; invalid JSON"}),
            status=401,
            content_type="application/json",
        )

    if request.headers["X-Machine-Name"] != "cluster1":
        return Response(
            json.dumps(
                {
                    "description": "Failed to submit job",
                    "error": "Machine does not exist",
                }
            ),
            status=400,
            headers={"X-Machine-Does-Not-Exist": "Machine does not exist"},
            content_type="application/json",
        )

    extra_headers = None
    if request.files["file"].filename == "script.batch":
        if "job_failed" in str(request._cached_data):
            ret = {
                "success": "Task created",
                "task_id": "submit_upload_job_id_job_failed",
                "task_url": "TASK_IP/tasks/submit_upload_job_id_job_failed",
            }
            status_code = 201
        elif "no_jobid" in str(request._cached_data):
            ret = {
                "success": "Task created",
                "task_id": "submit_upload_job_id_no_jobid",
                "task_url": "TASK_IP/tasks/submit_upload_job_id_no_jobid",
            }
            status_code = 201
        else:
            ret = {
                "success": "Task created",
                "task_id": "submit_upload_job_id_good",
                "task_url": "TASK_IP/tasks/submit_upload_job_id_good",
            }
            status_code = 201
    else:
        extra_headers = {"X-Invalid-Path": f"path is an invalid path."}
        ret = {"description": "Failed to submit job"}
        status_code = 400

    return Response(
        json.dumps(ret),
        status=status_code,
        headers=extra_headers,
        content_type="application/json",
    )


def systems_handler(request):
    if request.headers["Authorization"] != "Bearer VALID_TOKEN":
        return Response(
            json.dumps({"message": "Bad token; invalid JSON"}),
            status=401,
            content_type="application/json",
        )

    ret = {
        "description": "List of systems with status and description.",
        "out": [
            {
                "description": "System ready",
                "status": "available",
                "system": "cluster1",
            },
            {
                "description": "System ready",
                "status": "available",
                "system": "cluster2",
            },
        ],
    }
    ret_status = 200
    return Response(json.dumps(ret), status=ret_status, content_type="application/json")


def sacct_handler(request):
    if request.headers["Authorization"] != "Bearer VALID_TOKEN":
        return Response(
            json.dumps({"message": "Bad token; invalid JSON"}),
            status=401,
            content_type="application/json",
        )

    if request.headers["X-Machine-Name"] != "cluster1":
        return Response(
            json.dumps(
                {
                    "description": "Failed to retrieve account information",
                    "error": "Machine does not exist",
                }
            ),
            status=400,
            headers={"X-Machine-Does-Not-Exist": "Machine does not exist"},
            content_type="application/json",
        )

    jobs = request.args.get("jobs", "").split(",")
    if set(jobs) == {"352"}:
        ret = {
            "success": "Task created",
            "task_id": "acct_352_id",
            "task_url": "TASK_IP/tasks/acct_352_id",
        }
        status_code = 200
    elif set(jobs) == {"353"}:
        ret = {
            "success": "Task created",
            "task_id": "acct_353_id",
            "task_url": "TASK_IP/tasks/acct_353_id",
        }
        status_code = 200
    elif set(jobs) == {"354"}:
        ret = {
            "success": "Task created",
            "task_id": "acct_354_id",
            "task_url": "TASK_IP/tasks/acct_354_id",
        }
        status_code = 200
    elif set(jobs) == {"355"}:
        ret = {
            "success": "Task created",
            "task_id": "acct_355_id",
            "task_url": "TASK_IP/tasks/acct_355_id",
        }
        status_code = 200

    return Response(
        json.dumps(ret), status=status_code, content_type="application/json"
    )


def cancel_handler(request):
    uri = request.url
    jobid = uri.split("/")[-1]
    if jobid in ("352", "353", "354"):
        ret = {
            "success": "Task created",
            "task_id": "cancel_job_id",
            "task_url": "TASK_IP/tasks/cancel_job_id",
        }
    status_code = 200

    return Response(
        json.dumps(ret), status=status_code, content_type="application/json"
    )


@pytest.fixture
def fc_server(httpserver):
    httpserver.expect_request(
        "/compute/jobs/upload", method="POST"
    ).respond_with_handler(submit_upload_handler)
    httpserver.expect_request(
        re.compile("^/status/systems.*"), method="GET"
    ).respond_with_handler(systems_handler)
    httpserver.expect_request("/tasks", method="GET").respond_with_handler(
        tasks_handler
    )
    httpserver.expect_request("/compute/acct", method="GET").respond_with_handler(
        sacct_handler
    )
    httpserver.expect_request(
        re.compile("^/compute/jobs.*"), method="DELETE"
    ).respond_with_handler(cancel_handler)
    return httpserver
