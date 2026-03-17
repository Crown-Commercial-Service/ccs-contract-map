import asyncio
from pathlib import Path

import pandas as pd
import pytest

import evaluation.run_evaluation as run_evaluation


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
    monkeypatch.setattr(run_evaluation, "_resolve_prompt_file", lambda *args, **kwargs: prompt_file)
    monkeypatch.setattr(run_evaluation, "_classify_description", fake_classify)

    asyncio.run(
        run_evaluation.run_evaluation(
            truth_set_path=truth_set,
            mapper="v2",
            prompt_name=None,
            output_path=None,
        )
    )

    output_csv = repo_root / "data/results/eval_v2_custom_prompt.csv"
    assert output_csv.exists()

    result_df = pd.read_csv(output_csv)
    assert result_df["AI classification"].tolist() == ["cat-a", "wrong-cat"]
    assert result_df["correct"].tolist() == [True, False]
