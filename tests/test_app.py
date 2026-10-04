from streamlit.testing.v1 import AppTest


def test_dashboard_renders_without_errors():
    app = AppTest.from_file("../app.py", default_timeout=15).run()
    assert not app.exception
    assert [metric.label for metric in app.metric] == [
        "Revenue",
        "Customers",
        "Avg. order value",
        "Repeat customer rate",
    ]
