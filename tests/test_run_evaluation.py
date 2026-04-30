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


def test_load_truth_set_raises_when_required_columns_missing(tmp_path):
    truth_set = tmp_path / "truth.csv"
    pd.DataFrame({"Description": ["desc only"]}).to_csv(truth_set, index=False)

    with pytest.raises(ValueError, match="Truth set must include columns"):
        run_evaluation._load_truth_set(truth_set)


def test_resolve_prompt_file_uses_mapper_default(monkeypatch, tmp_path):
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    v1_prompt = prompts_dir / "new_system_prompt.md"
    v2_prompt = prompts_dir / "system_prompt_v2.md"
    v1_prompt.write_text("v1")
    v2_prompt.write_text("v2")

    monkeypatch.setattr(run_evaluation, "PROMPTS_DIR", prompts_dir)

    assert run_evaluation._resolve_prompt_file(None, "v1") == v1_prompt
    assert run_evaluation._resolve_prompt_file(None, "v2") == v2_prompt


def test_run_evaluation_writes_default_output_csv(monkeypatch, tmp_path):
    repo_root = tmp_path
    truth_set = repo_root / "truth.csv"
    prompt_file = repo_root / "prompts" / "custom_prompt.md"
    prompt_file.parent.mkdir(parents=True, exist_ok=True)
    prompt_file.write_text("prompt")
    pd.DataFrame(
        {
            "Description": ["desc-a", "desc-b"],
            "Category": ["cat-a", "cat-b"],
        }
    ).to_csv(truth_set, index=False)

    async def fake_classify(description: str, mapper: str, prompt_file: Path) -> str:
        mapping = {"desc-a": "cat-a", "desc-b": "wrong-cat"}
        return mapping[description]

    monkeypatch.setattr(run_evaluation, "REPO_ROOT", repo_root)
    monkeypatch.setattr(
        run_evaluation, "_resolve_prompt_file", lambda *args, **kwargs: prompt_file
    )
    monkeypatch.setattr(run_evaluation, "_classify_description", fake_classify)
    monkeypatch.setattr(run_evaluation, "_get_mlflow_module", lambda: FakeMLflow())

    asyncio.run(
        run_evaluation.run_evaluation(
            truth_set_path=truth_set,
            mapper="v2",
            prompt_name=None,
            output_path=None,
            mlflow_tracking_uri="azureml://unit-test",
        )
    )

    output_csv = repo_root / "data/results/eval_v2_custom_prompt.csv"
    assert output_csv.exists()

    result_df = pd.read_csv(output_csv)
    assert result_df["AI classification"].tolist() == ["cat-a", "wrong-cat"]
    assert result_df["correct"].tolist() == [True, False]


def test_run_evaluation_logs_mlflow_params_metrics_and_artifacts(monkeypatch, tmp_path):
    truth_set = tmp_path / "truth.csv"
    prompt_file = tmp_path / "prompts" / "custom_prompt.md"
    output_path = tmp_path / "results.csv"
    prompt_file.parent.mkdir(parents=True, exist_ok=True)
    prompt_file.write_text("prompt")
    pd.DataFrame(
        {
            "Description": ["desc-a", "desc-b"],
            "Category": ["cat-a", "cat-b"],
        }
    ).to_csv(truth_set, index=False)

    async def fake_classify(description: str, mapper: str, prompt_file: Path) -> str:
        mapping = {"desc-a": "cat-a", "desc-b": "wrong-cat"}
        return mapping[description]

    fake_mlflow = FakeMLflow()
    monkeypatch.setattr(
        run_evaluation, "_resolve_prompt_file", lambda *args, **kwargs: prompt_file
    )
    monkeypatch.setattr(run_evaluation, "_classify_description", fake_classify)
    monkeypatch.setattr(run_evaluation, "_get_mlflow_module", lambda: fake_mlflow)

    asyncio.run(
        run_evaluation.run_evaluation(
            truth_set_path=truth_set,
            mapper="v2",
            prompt_name=None,
            output_path=output_path,
            mlflow_tracking_uri="http://mlflow.local:5000",
            mlflow_experiment_name="ContractMap-Evaluation-Test",
            mlflow_run_name="unit-test-run",
        )
    )

    assert fake_mlflow.tracking_uri == "http://mlflow.local:5000"
    assert fake_mlflow.experiment_name == "ContractMap-Evaluation-Test"
    assert fake_mlflow.start_run_name == "unit-test-run"

    assert fake_mlflow.params["mapper"] == "v2"
    assert fake_mlflow.params["truth_set_path"] == str(truth_set.resolve())
    assert fake_mlflow.params["prompt_name"] == "custom_prompt.md"
    assert fake_mlflow.params["prompt_path"] == str(prompt_file.resolve())
    assert fake_mlflow.params["num_samples"] == 2

    assert fake_mlflow.metrics["accuracy_percent"] == 50.0
    assert fake_mlflow.metrics["accuracy_fraction"] == 0.5
    assert fake_mlflow.metrics["correct_predictions"] == 1
    assert "evaluation_duration_seconds" in fake_mlflow.metrics

    assert (str(prompt_file.resolve()), "prompts") in fake_mlflow.artifacts
    assert (str(output_path.resolve()), "results") in fake_mlflow.artifacts
