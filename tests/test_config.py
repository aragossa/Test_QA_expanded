import pytest

from src.utils.config import load_config


def test_missing_config_has_clear_error(tmp_path):
    missing = tmp_path / "missing.yaml"

    with pytest.raises(ValueError, match=f"Configuration file not found: {missing}"):
        load_config(str(missing))


@pytest.mark.parametrize("content", ["", "- not\n- a\n- mapping"])
def test_config_root_must_be_mapping(tmp_path, content):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match="must contain a YAML mapping"):
        load_config(str(config_path))


def test_invalid_yaml_has_clear_error(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("testing: [", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid YAML"):
        load_config(str(config_path))


def test_missing_required_config_sections_are_reported(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("testing: {}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="ammeters, result_management"):
        load_config(str(config_path))

