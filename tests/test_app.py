from pathlib import Path

from streamlit.testing.v1 import AppTest


APP = Path(__file__).parents[1] / "app.py"


def test_initial_page_waits_for_user_input() -> None:
    app = AppTest.from_file(str(APP)).run()

    assert not app.exception
    assert len(app.metric) == 0
    assert len(app.download_button) == 0
    assert app.checkbox[0].value is False


def test_generate_without_csv_keeps_page_in_idle_state() -> None:
    app = AppTest.from_file(str(APP)).run()

    app.button[0].click().run()

    assert not app.exception
    assert len(app.metric) == 0
    assert len(app.download_button) == 0
    assert app.warning


def test_explicit_sample_analysis_exposes_pdf_download() -> None:
    app = AppTest.from_file(str(APP)).run()

    app.checkbox[0].set_value(True)
    app.button[0].click().run(timeout=10)

    assert not app.exception
    assert len(app.metric) == 10
    assert len(app.download_button) == 4
    assert app.download_button[1].label == "下载 PDF 报告"
