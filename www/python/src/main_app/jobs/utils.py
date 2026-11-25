# src/main_app/jobs_workers/utils.py


def generate_result_file_name(job_id: int, job_type: str) -> str:
    result_file = f"{job_type}_job_{job_id}.json"
    return result_file


def generate_cancelled_file_name(
    job_id: int | None = None,
    job_type: str | None = None,
    result_file: str | None = None,
) -> str:
    if result_file:
        return f"{result_file}.cancelled"

    if job_type and job_id:
        return f"{job_type}_job_{job_id}.json.cancelled"

    raise ValueError("Either result_file ot (job_type and job_id) must be provided")


__all__ = [
    "generate_cancelled_file_name",
    "generate_result_file_name",
]
