"""Mutable runtime state — NOT part of public contracts."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RuntimeAnalysisState:
    """Accumulated state during preprocessing. Converted to contract at end."""

    removed_rows: list[int] = field(default_factory=list)
    filled_columns: dict[str, int] = field(default_factory=dict)
    encoded_columns: list[str] = field(default_factory=list)
    parsed_datetime_columns: list[str] = field(default_factory=list)
    changes_log: list[str] = field(default_factory=list)

    def log_change(self, message: str) -> None:
        """Append a change description to the log."""
        self.changes_log.append(message)

    def to_tuple(self) -> tuple[str, ...]:
        """Return the changes log as an immutable tuple."""
        return tuple(self.changes_log)
