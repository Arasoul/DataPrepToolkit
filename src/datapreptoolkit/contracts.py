"""Contract adapter: builds PreprocessingResult from internal state."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from automation_core._version import CONTRACT_VERSION
from automation_core.contracts import ContractEnvelope, ContractType
from automation_core.results import (
    PreprocessingArtifacts,
    PreprocessingCore,
    PreprocessingResult,
)
from automation_core.types import DataHandle
from automation_core.utils import identify_column_types

from datapreptoolkit._internal.models import RuntimeAnalysisState


def build_preprocessing_result(
    df: Any,
    *,
    original_df: Any,
    state: RuntimeAnalysisState,
) -> PreprocessingResult:
    """Convert internal runtime state to an immutable public contract."""
    handle = DataHandle(df)
    col_types = identify_column_types(df)

    envelope = ContractEnvelope(
        contract_type=ContractType.PREPROCESSING,
        version=CONTRACT_VERSION,
        produced_by="datapreptoolkit",
        produced_at=datetime.now(UTC).isoformat(),
    )

    core = PreprocessingCore(
        data_handle=handle,
        column_types=col_types,
        original_row_count=len(original_df),
        original_column_count=len(original_df.columns),
        removed_duplicates=state.filled_columns.get("__duplicates__", 0),
        filled_missing=sum(
            v for k, v in state.filled_columns.items() if k != "__duplicates__"
        ),
        parsed_datetimes=tuple(state.parsed_datetime_columns),
        encoded_columns=tuple(state.encoded_columns),
    )

    artifacts = (
        PreprocessingArtifacts(changes_log=state.to_tuple())
        if state.changes_log
        else None
    )

    return PreprocessingResult(
        envelope=envelope,
        core=core,
        artifacts=artifacts,
    )
