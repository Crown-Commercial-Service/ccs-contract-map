import asyncio
from pathlib import Path

import pandas as pd
import pytest

import evaluation.run_evaluation as run_evaluation


class _DummyRunContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeMLflow:
    def __init__(self):
        self.tracking_uri = None
        self.experiment_name = None
        self.start_run_name = None
        self.params: dict[str, object] = {}
        self.metrics: dict[str, float] = {}
        self.artifacts: list[tuple[str, str]] = []

    def set_tracking_uri(self, uri: str) -> None:
        self.tracking_uri = uri

    def set_experiment(self, name: str) -> None:
        self.experiment_name = name

    def start_run(self, run_name: str | None = None):
        self.start_run_name = run_name
        return _DummyRunContext()

    def log_param(self, key: str, value) -> None:
        self.params[key] = value

    def log_metric(self, key: str, value: float) -> None:
        self.metrics[key] = value

    def log_artifact(self, path: str, artifact_path: str | None = None) -> None:
        self.artifacts.append((path, artifact_path))


def test_load_truthset_raises_when_required_columns_missing(tmp_path):
    truth_set = tmp_path / "truth.csv"
    pd.DataFrame({"Description": ["desc only"]}).to_csv(truth_set, index=False)

    with pytest.raises(ValueError, match="Truth set must include columns"):
        run_evaluation._load_truthset(truth_set)


def test_run_evaluation_writes_default_output_csv(monkeypatch, tmp_path):
    repo_root = tmp_path
    truth_set = repo_root / "truth.csv"
    prompt_file = repo_root / "prompts" / "custom_prompt.md"
    prompt_file.parent.mkdir(parents=True, exist_ok=True)
    prompt_file.write_text("prompt")

    # Use the correct column names
    pd.DataFrame(
        {
            "Title": ["title-a", "title-b"],
            "Description": ["desc-a", "desc-b"],
            "Category": ["cat-a", "cat-b"],
        }
    ).to_csv(truth_set, index=False)

    # Return tuple (result, reason, heuristic_score) as expected
    async def fake_keywords_and_llm(
        description: str, threshold: int, margin: int, system_prompt_file_location: Path
    ) -> tuple[str, str, float]:
        mapping = {
            "title-a : desc-a": ("cat-a", "matched", 15.0),
            "title-b : desc-b": ("wrong-cat", "mismatched", 8.0),
        }
        return mapping[description]

    monkeypatch.setattr(run_evaluation, "REPO_ROOT", repo_root)
    monkeypatch.setattr(
        run_evaluation, "_resolve_prompt_file", lambda *args, **kwargs: prompt_file
    )
    # Mock the actual classification function
    monkeypatch.setattr(
        "core.classification_v2_mix_v5.keywords_and_llm", fake_keywords_and_llm
    )
    monkeypatch.setattr(run_evaluation, "_get_mlflow_module", lambda: FakeMLflow())

    asyncio.run(
        run_evaluation.evaluate_truthset(
            truthset_path=truth_set,
            threshold=10,
            margin=0,
            prompt_name="custom_prompt.md",
            output_path=None,
            mlflow_tracking_uri="azureml://unit-test",
        )
    )

    # Expect CSV output with correct naming pattern
    output_file = repo_root / "data/results/eval_keywords_llm_t10_m0.csv"
    assert output_file.exists()

    result_df = pd.read_csv(output_file)
    assert result_df["AI_Prediction"].tolist() == ["cat-a", "wrong-cat"]


def test_run_evaluation_logs_mlflow_params_metrics_and_artifacts(monkeypatch, tmp_path):
    truth_set = tmp_path / "truth.csv"
    prompt_file = tmp_path / "prompts" / "custom_prompt.md"
    output_path = tmp_path / "results.csv"
    prompt_file.parent.mkdir(parents=True, exist_ok=True)
    prompt_file.write_text("prompt")
    pd.DataFrame(
        {
            "Title": ["title-a", "title-b"],
            "Description": ["desc-a", "desc-b"],
            "Category": ["cat-a", "cat-b"],
        }
    ).to_csv(truth_set, index=False)

    async def fake_keywords_and_llm(
        description: str, threshold: int, margin: int, system_prompt_file_location: Path
    ) -> tuple[str, str, float]:
        mapping = {
            "title-a : desc-a": ("cat-a", "matched", 15.0),
            "title-b : desc-b": ("wrong-cat", "mismatched", 8.0),
        }
        return mapping[description]

    fake_mlflow = FakeMLflow()
    monkeypatch.setattr(run_evaluation, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        run_evaluation, "_resolve_prompt_file", lambda *args, **kwargs: prompt_file
    )
    monkeypatch.setattr(
        "core.classification_v2_mix_v5.keywords_and_llm", fake_keywords_and_llm
    )
    monkeypatch.setattr(run_evaluation, "_get_mlflow_module", lambda: fake_mlflow)

    asyncio.run(
        run_evaluation.evaluate_truthset(
            truthset_path=truth_set,
            threshold=10,
            margin=0,
            prompt_name="custom_prompt.md",
            output_path=output_path,
            mlflow_tracking_uri="http://mlflow.local:5000",
            mlflow_experiment_name="ContractMap-Evaluation-Test",
            mlflow_run_name="unit-test-run",
        )
    )

    assert fake_mlflow.tracking_uri == "http://mlflow.local:5000"
    assert fake_mlflow.experiment_name == "ContractMap-Evaluation-Test"
    assert fake_mlflow.start_run_name == "unit-test-run"

    assert fake_mlflow.params["prompt_name"] == "custom_prompt.md"
    assert fake_mlflow.params["prompt_path"] == str(prompt_file.resolve())
    assert fake_mlflow.params["num_samples"] == 2

    assert fake_mlflow.metrics["accuracy_percent"] == 50.0
    assert fake_mlflow.metrics["correct_predictions"] == 1
    assert "evaluation_duration_seconds" in fake_mlflow.metrics

    assert (str(prompt_file.resolve()), "prompts") in fake_mlflow.artifacts
    assert (str(output_path.resolve()), "results") in fake_mlflow.artifacts
