import pytest

from utils.file_to_string import file_to_string_processor


def test_file_to_string_processor_reads_file_content(tmp_path):
    test_file = tmp_path / "sample.txt"
    expected_content = "line 1\nline 2"
    test_file.write_text(expected_content)

    result = file_to_string_processor(test_file)

    assert result == expected_content


def test_file_to_string_processor_raises_for_missing_file(tmp_path):
    missing_file = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError):
        file_to_string_processor(missing_file)
