def generate_result_file_name(job_id: int, job_type: str) -> str:
    result_file = f"{job_type}_job_{job_id}.json"
    return result_file


__all__ = [
    "generate_result_file_name",
]
