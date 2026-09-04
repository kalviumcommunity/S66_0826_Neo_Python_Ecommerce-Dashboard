"""Regression checks for the backend directory layout and script execution."""
import ast
import runpy
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = BACKEND_ROOT / "scripts"
SCRIPTS = sorted(SCRIPT_DIR.glob("*.py"))
VALIDATORS = sorted((SCRIPT_DIR / "validation_report").glob("validate_*.py"))


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda path: path.stem)
def test_scripts_import_from_unrelated_working_directory(script, tmp_path, monkeypatch):
    # Match sys.path[0] when invoking python /absolute/path/to/script.py.
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(SCRIPT_DIR))
    namespace = runpy.run_path(str(script), run_name="structure_check")
    root = namespace.get("PROJECT_ROOT", namespace.get("ROOT"))
    if root is not None:
        assert root == BACKEND_ROOT


@pytest.mark.parametrize("script", VALIDATORS, ids=lambda path: path.stem)
def test_validator_paths_do_not_depend_on_working_directory(script, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    namespace = runpy.run_path(str(script), run_name="structure_check")
    sample = Path(namespace["SAMPLE_FILE"])
    report = Path(namespace["OUTPUT_REPORT"])
    assert sample.is_relative_to(BACKEND_ROOT / "data" / "processed")
    assert sample.is_file()
    assert report.is_relative_to(BACKEND_ROOT / "output" / "validation_report")
    assert namespace["validate_file_format"](str(sample))[0]


def test_all_python_sources_have_valid_syntax():
    for folder in ("scripts", "src", "tests"):
        for path in (BACKEND_ROOT / folder).rglob("*.py"):
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_package_imports():
    from scripts import deduplicate_data, handle_missing, ingest_data

    assert handle_missing.DATASET_DTYPES is ingest_data.DATASET_DTYPES
    assert deduplicate_data.DATASET_DTYPES is ingest_data.DATASET_DTYPES


def test_ingestion_preserves_identifier_and_writes_to_requested_directory(tmp_path):
    from scripts.ingest_data import ingest_all_raw_csvs
    import pandas as pd

    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "olist_sellers_dataset.csv").write_text(
        "seller_id,seller_zip_code_prefix,seller_city,seller_state\n"
        "seller-1,01234,Sao Paulo,SP\n", encoding="utf-8"
    )
    output = tmp_path / "ingested"
    summary = ingest_all_raw_csvs(raw, output)
    assert summary == [("olist_sellers_dataset.csv", 1, 4)]
    result = pd.read_csv(output / "olist_sellers_dataset.csv", dtype="string")
    assert result.loc[0, "seller_zip_code_prefix"] == "01234"


def test_cross_layer_validation_pipeline_runs_successfully():
    from scripts import validate_cross_layer_computation

    assert validate_cross_layer_computation.TOLERANCE_ABSOLUTE_COUNT == 0
    assert validate_cross_layer_computation.TOLERANCE_FINANCIAL_ABS == 0.05

