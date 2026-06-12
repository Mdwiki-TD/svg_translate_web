from src.main_app.app_routes.utils.routes_utils import get_job_detail_url


def test_get_job_detail_url_public(app):
    with app.test_request_context():
        url = get_job_detail_url(1, "copy_svg_langs")
        assert "/jobs/copy_svg_langs/1" in url


def test_get_job_detail_url_admin(app):
    with app.test_request_context():
        url = get_job_detail_url(1, "collect_templates_data")
        assert "/admin/jobs/collect_templates_data/1" in url
