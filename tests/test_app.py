from datetime import date

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


def test_dashboard_handles_one_day_selection():
    app = AppTest.from_file("../app.py", default_timeout=15).run()
    first = app.date_input[0].value[0]
    assert isinstance(first, date)
    app.date_input[0].set_value((first, first)).run()
    assert not app.exception
    assert any("30 days" in message.value for message in app.info)
