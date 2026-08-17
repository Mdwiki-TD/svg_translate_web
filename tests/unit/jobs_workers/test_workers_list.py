"""Unit tests for src/main_app/jobs/workers_list.py module."""

from __future__ import annotations

from src.main_app.jobs_workers.public_jobs_workers.workers_list_public import JobData, jobs_data_public


class TestJobData:
    def test_create_job_data(self):
        jd = JobData(
            job_type="test",
            job_name="Test Job",
            job_class=lambda: None,
            job_list_template="test/list.html",
            job_details_template="x.html",
        )
        assert jd.job_type == "test"
        assert jd.job_name == "Test Job"
        assert jd.job_list_template == "test/list.html"

    def test_custom_details_template(self):
        jd = JobData(
            job_type="test",
            job_name="Test",
            job_class=lambda: None,
            job_list_template="list.html",
            job_details_template="custom/details.html",
        )
        assert jd.job_details_template == "custom/details.html"


class TestJobsData:
    def test_jobs_data_is_dict(self):
        assert isinstance(jobs_data_public, dict)

    def test_all_values_are_job_data(self):
        for key, val in jobs_data_public.items():
            assert isinstance(val, JobData), f"jobs_data_public[{key!r}] is not JobData"

    def test_job_type_matches_key(self):
        for key, val in jobs_data_public.items():
            assert val.job_type == key, f"Mismatch: key={key!r}, job_type={val.job_type!r}"

    def test_all_have_callable(self):
        for key, val in jobs_data_public.items():
            assert callable(val.job_class), f"jobs_data_public[{key!r}].job_class not callable"

    def test_all_have_list_template(self):
        for key, val in jobs_data_public.items():
            assert val.job_list_template, f"jobs_data_public[{key!r}].job_list_template is empty"

    def test_all_have_non_empty_name(self):
        for key, val in jobs_data_public.items():
            assert val.job_name, f"jobs_data_public[{key!r}].job_name is empty"
