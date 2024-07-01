"""
LSP features leveraging cfnlint.

https://github.com/aws-cloudformation/cfn-lint/blob/main/docs/getting_started/integration.md
"""
import logging
from typing import Dict, List

import cfnlint
from cfnlint.api import lint
from cfnlint.config import ConfigFileArgs
from lsprotocol.types import Diagnostic, DiagnosticSeverity, Position, Range

logger = logging.getLogger(__name__)


def diagnostics(yaml_content: str, file_path: str) -> List[Diagnostic]:
    """Return diagnostics for the template file at file_path."""

    try:
        config = load_cfnlint_config(log_exceptions=False)
    except Exception:
        config = {}

    matches = lint(yaml_content, config=config)

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


def load_cfnlint_config(log_exceptions: bool) -> Dict[str, str]:
    try:
        # https://github.com/aws-cloudformation/cfn-lint/blob/main/src/cfnlint/config.py
        config = ConfigFileArgs()
        config.load()
        return config.file_args  # type: ignore[no-any-return]
    except Exception as e:
        if log_exceptions:
            logger.error("Error reading cfnlint configuration %s", e)
        return {}


def match_filter(rule_match: cfnlint.rules.Match) -> bool:
    # TODO we should probably log this
    return not rule_match.message.lower().startswith(
        "unknown exception while processing rule"
    )
