"""Tests for exceptions module."""

from __future__ import annotations

from datapreptoolkit.exceptions import (
    CleaningError,
    ConfigError,
    DataPrepError,
    EmptyDatasetError,
    FileFormatError,
    IncompatibleDataError,
    InvalidColumnError,
    LoadError,
    QualityThresholdError,
    ReportError,
    ValidationError,
)


class TestDataPrepError:
    """Tests for DataPrepError base exception."""

    def test_message(self) -> None:
        """Should store message."""
        error = DataPrepError("test message")
        assert str(error) == "test message"
        assert error.message == "test message"

    def test_is_exception(self) -> None:
        """Should be an Exception subclass."""
        assert issubclass(DataPrepError, Exception)


class TestLoadError:
    """Tests for LoadError exception."""

    def test_message(self) -> None:
        """Should store message."""
        error = LoadError("load failed")
        assert "load failed" in str(error)

    def test_source(self) -> None:
        """Should store source."""
        error = LoadError("load failed", source="test.csv")
        assert error.source == "test.csv"

    def test_is_data_prep_error(self) -> None:
        """Should be a DataPrepError subclass."""
        assert issubclass(LoadError, DataPrepError)


class TestFileFormatError:
    """Tests for FileFormatError exception."""

    def test_message(self) -> None:
        """Should store message with path."""
        error = FileFormatError("test.txt")
        assert "test.txt" in str(error)

    def test_is_load_error(self) -> None:
        """Should be a LoadError subclass."""
        assert issubclass(FileFormatError, LoadError)


class TestEmptyDatasetError:
    """Tests for EmptyDatasetError exception."""

    def test_message(self) -> None:
        """Should store message."""
        error = EmptyDatasetError()
        assert "empty" in str(error).lower()

    def test_is_load_error(self) -> None:
        """Should be a LoadError subclass."""
        assert issubclass(EmptyDatasetError, LoadError)


class TestCleaningError:
    """Tests for CleaningError exception."""

    def test_is_data_prep_error(self) -> None:
        """Should be a DataPrepError subclass."""
        assert issubclass(CleaningError, DataPrepError)


class TestInvalidColumnError:
    """Tests for InvalidColumnError exception."""

    def test_message(self) -> None:
        """Should store message with column name."""
        error = InvalidColumnError("missing_col")
        assert "missing_col" in str(error)

    def test_available_columns(self) -> None:
        """Should store available columns."""
        error = InvalidColumnError("missing_col", available=["col1", "col2"])
        assert error.available == ["col1", "col2"]

    def test_suggestion(self) -> None:
        """Should suggest similar column names."""
        error = InvalidColumnError("age", available=["age_group", "salary"])
        assert (
            "Did you mean" in str(error)
            or error.available == ["age_group", "salary"]
        )

    def test_is_cleaning_error(self) -> None:
        """Should be a CleaningError subclass."""
        assert issubclass(InvalidColumnError, CleaningError)


class TestIncompatibleDataError:
    """Tests for IncompatibleDataError exception."""

    def test_is_cleaning_error(self) -> None:
        """Should be a CleaningError subclass."""
        assert issubclass(IncompatibleDataError, CleaningError)


class TestValidationError:
    """Tests for ValidationError exception."""

    def test_is_data_prep_error(self) -> None:
        """Should be a DataPrepError subclass."""
        assert issubclass(ValidationError, DataPrepError)


class TestQualityThresholdError:
    """Tests for QualityThresholdError exception."""

    def test_message(self) -> None:
        """Should store score and threshold."""
        error = QualityThresholdError(0.5, 0.8)
        assert error.score == 0.5
        assert error.threshold == 0.8
        assert "0.50" in str(error) or "50.00%" in str(error)

    def test_is_validation_error(self) -> None:
        """Should be a ValidationError subclass."""
        assert issubclass(QualityThresholdError, ValidationError)


class TestReportError:
    """Tests for ReportError exception."""

    def test_is_data_prep_error(self) -> None:
        """Should be a DataPrepError subclass."""
        assert issubclass(ReportError, DataPrepError)


class TestConfigError:
    """Tests for ConfigError exception."""

    def test_is_data_prep_error(self) -> None:
        """Should be a DataPrepError subclass."""
        assert issubclass(ConfigError, DataPrepError)
