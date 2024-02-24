"""
Utilities for handling user configuration.

See also:
https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace_configuration
https://pygls.readthedocs.io/en/latest/pages/advanced_usage.html#configuration
"""
from enum import Enum, auto, unique
from typing import Any, List

from attrs import define
from lsprotocol.types import (
    ConfigurationItem,
    ConfigurationParams,
    DidChangeConfigurationParams,
    WorkspaceConfigurationParams,
)

SECTION = "cfn"


@unique
class DiagnosticPublishingMethod(Enum):
    ON_DID_SAVE = auto()
    ON_DID_CHANGE = auto()


DIAGNOSTIC_PUBLISHING_METHOD_KEY = "diagnosticPublishingMethod"
DIAGNOSTIC_PUBLISHING_METHOD_DEFAULT = DiagnosticPublishingMethod.ON_DID_CHANGE


@define
class UserConfiguration:
    diagnostic_publishing_method: DiagnosticPublishingMethod = (
        DIAGNOSTIC_PUBLISHING_METHOD_DEFAULT
    )


# TODO in 3.11+ https://docs.python.org/3/library/enum.html#enum.StrEnum is much nicer for this
def diagnostic_publishing_method_from_string(string: str) -> DiagnosticPublishingMethod:
    if string.upper() == "ON_DID_SAVE":
        return DiagnosticPublishingMethod.ON_DID_SAVE
    return DIAGNOSTIC_PUBLISHING_METHOD_DEFAULT


def workspace_configuration_params(uri: str) -> WorkspaceConfigurationParams:
    return WorkspaceConfigurationParams(
        items=[
            ConfigurationItem(scope_uri=uri, section=DIAGNOSTIC_PUBLISHING_METHOD_KEY)
        ]
    )


def configuration_params() -> ConfigurationParams:
    items = [ConfigurationItem(section=f"{SECTION}.{DIAGNOSTIC_PUBLISHING_METHOD_KEY}")]
    return ConfigurationParams(items=items)


def from_get_configuration_response(config: List[Any]) -> UserConfiguration:
    """Obtain config from the response of a workspace/configuration response.

    https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace_configuration
    """
    user_config = UserConfiguration()
    if config and isinstance(config, list) and len(config) > 0:
        diagnostic_publishing_method, *_ = config
        if diagnostic_publishing_method and isinstance(
            diagnostic_publishing_method, str
        ):
            user_config.diagnostic_publishing_method = (
                diagnostic_publishing_method_from_string(diagnostic_publishing_method)
            )
    return user_config


def from_did_change_config(config: DidChangeConfigurationParams) -> UserConfiguration:
    """Obtain config from a DidChangeConfigurationParams object.

    Example object:
    DidChangeConfigurationParams(settings={'cfn': {'diagnosticPublishingMethod': 'ON_DID_CHANGE'}})
    """
    user_config = UserConfiguration()
    if config.settings:
        relevant_settings = config.settings.get(SECTION, {})
        user_config.diagnostic_publishing_method = (
            diagnostic_publishing_method_from_string(
                relevant_settings.get(
                    DIAGNOSTIC_PUBLISHING_METHOD_KEY,
                    str(DIAGNOSTIC_PUBLISHING_METHOD_DEFAULT),
                )
            )
        )
    return user_config
