# type: ignore
"""
LSP features leveraging cfnlint.
"""

from typing import Dict, List

import cfnlint.config
import cfnlint.core
import cfnlint.decode
import cfnlint.runner
from cfnlint.api import lint_all
from lsprotocol.types import Diagnostic, DiagnosticSeverity, Position, Range


def diagnostics(yaml_content: str, file_path: str) -> List[Diagnostic]:
    """Return diagnostics for the template file at file_path."""

    matches = lint_all(yaml_content)

    severity_mapping: Dict[str, DiagnosticSeverity] = {
        "informational": DiagnosticSeverity.Information,
        "error": DiagnosticSeverity.Error,
        "warning": DiagnosticSeverity.Warning,
    }
    return [
        Diagnostic(
            range=Range(
                start=Position(line=m.linenumber - 1, character=m.columnnumber - 1),
                end=Position(line=m.linenumberend - 1, character=m.columnnumberend - 1),
            ),
            message=m.message,
            source="cfn-lsp-extra",
            severity=severity_mapping.get(
                m.rule.severity.lower(), DiagnosticSeverity.Error
            ),
        )
        for m in filter(match_filter, matches)
    ]


def match_filter(rule_match: cfnlint.rules.Match) -> bool:
    # TODO we should probably log this
    return not rule_match.message.lower().startswith(
        "unknown exception while processing rule"
    )
