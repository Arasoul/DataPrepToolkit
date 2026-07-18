"""Tests for config module."""

from __future__ import annotations

import pytest

from datapreptoolkit import EncodingStrategy, ToolkitConfig, ZScoreMethod


class TestToolkitConfig:
    """Tests for ToolkitConfig dataclass."""

    def test_default_config(self, default_config: ToolkitConfig) -> None:
        """Default config should have expected values."""
        assert default_config.remove_duplicates is False
        assert default_config.parse_datetimes is True
        assert default_config.optimise_memory is True
        assert default_config.detect_outliers is True
        assert default_config.outlier_method == "iqr"
        assert default_config.iqr_multiplier == 1.5
        assert default_config.zscore_threshold == 3.0
        assert default_config.encoding_strategy == EncodingStrategy.LABEL
        assert default_config.log_level == "INFO"

    def test_custom_config(self) -> None:
        """Custom config should override defaults."""
        config = ToolkitConfig(
            remove_duplicates=True,
            iqr_multiplier=2.0,
            zscore_threshold=2.5,
            encoding_strategy=EncodingStrategy.ONE_HOT,
        )
        assert config.remove_duplicates is True
        assert config.iqr_multiplier == 2.0
        assert config.zscore_threshold == 2.5
        assert config.encoding_strategy == EncodingStrategy.ONE_HOT

    def test_quality_weights_default(self, default_config: ToolkitConfig) -> None:
        """Default quality weights should be set."""
        weights = default_config.quality_weights
        assert "missing" in weights
        assert "duplicate" in weights
        assert "constant" in weights
        assert "high_cardinality" in weights
        assert "outlier" in weights
        assert weights["missing"] == 40.0
        assert weights["duplicate"] == 20.0

    def test_custom_quality_weights(self) -> None:
        """Custom quality weights should override defaults."""
        custom_weights = {
            "missing": 50.0,
            "duplicate": 30.0,
            "constant": 5.0,
            "high_cardinality": 2.0,
            "outlier": 4.0,
        }
        config = ToolkitConfig(quality_weights=custom_weights)
        assert config.quality_weights == custom_weights

    def test_invalid_iqr_multiplier(self) -> None:
        """Invalid iqr_multiplier should raise ValueError."""
        with pytest.raises(ValueError, match="iqr_multiplier must be positive"):
            ToolkitConfig(iqr_multiplier=-1.0)

    def test_invalid_zscore_threshold(self) -> None:
        """Invalid zscore_threshold should raise ValueError."""
        with pytest.raises(ValueError, match="zscore_threshold must be positive"):
            ToolkitConfig(zscore_threshold=0.0)

    def test_invalid_high_cardinality_threshold(self) -> None:
        """Invalid high_cardinality_threshold should raise ValueError."""
        with pytest.raises(ValueError, match="high_cardinality_threshold"):
            ToolkitConfig(high_cardinality_threshold=1.5)

    def test_invalid_constant_threshold(self) -> None:
        """Invalid constant_threshold should raise ValueError."""
        with pytest.raises(ValueError, match="constant_threshold"):
            ToolkitConfig(constant_threshold=0.0)

    def test_invalid_id_column_threshold(self) -> None:
        """Invalid id_column_threshold should raise ValueError."""
        with pytest.raises(ValueError, match="id_column_threshold"):
            ToolkitConfig(id_column_threshold=1.5)

    def test_invalid_duplicate_keep(self) -> None:
        """Invalid duplicate_keep should raise ValueError."""
        with pytest.raises(ValueError, match="duplicate_keep"):
            ToolkitConfig(duplicate_keep="invalid")

    def test_invalid_quality_weights_keys(self) -> None:
        """Invalid quality_weights keys should raise ValueError."""
        with pytest.raises(ValueError, match="quality_weights must have keys"):
            ToolkitConfig(quality_weights={"invalid_key": 1.0})


class TestEncodingStrategy:
    """Tests for EncodingStrategy enum."""

    def test_values(self) -> None:
        """EncodingStrategy should have expected values."""
        assert EncodingStrategy.LABEL.value == "label"
        assert EncodingStrategy.ONE_HOT.value == "one_hot"
        assert EncodingStrategy.FREQUENCY.value == "frequency"
        assert EncodingStrategy.NONE.value == "none"


class TestZScoreMethod:
    """Tests for ZScoreMethod enum."""

    def test_values(self) -> None:
        """ZScoreMethod should have expected values."""
        assert ZScoreMethod.STANDARD.value == "standard"
        assert ZScoreMethod.MODIFIED.value == "modified"
