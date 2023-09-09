"""
Test user configuration methods.
"""
import pytest
from lsprotocol.types import DidChangeConfigurationParams

from cfn_lsp_extra.config.user_configuration import DiagnosticPublishingMethod
from cfn_lsp_extra.config.user_configuration import (
    diagnostic_publishing_method_from_string,
)
from cfn_lsp_extra.config.user_configuration import from_did_change_config
from cfn_lsp_extra.config.user_configuration import from_get_configuration_response


@pytest.mark.parametrize(
    "input_str,expected_publishing_method",
    [
        ("ON_DID_CHANGE", DiagnosticPublishingMethod.ON_DID_CHANGE),
        ("ON_DID_SAVE", DiagnosticPublishingMethod.ON_DID_SAVE),
    ],
)
def test_from_get_configuration_response(input_str, expected_publishing_method):
    config_input = [input_str]

    conf = from_get_configuration_response(config_input)
    assert conf.diagnostic_publishing_method == expected_publishing_method


@pytest.mark.parametrize(
    "bad_input",
    [[], [None], [3], {"foo", "bar"}],
)
def test_from_get_configuration_response_defaults_to_on_did_change(bad_input):
    conf = from_get_configuration_response(bad_input)
    assert conf.diagnostic_publishing_method == DiagnosticPublishingMethod.ON_DID_CHANGE


@pytest.mark.parametrize(
    "input_str,expected_publishing_method",
    [
        ("ON_DID_CHANGE", DiagnosticPublishingMethod.ON_DID_CHANGE),
        ("ON_DID_SAVE", DiagnosticPublishingMethod.ON_DID_SAVE),
    ],
)
def test_from_did_change_config(input_str, expected_publishing_method):
    params = DidChangeConfigurationParams(
        settings={"cfn": {"diagnosticPublishingMethod": input_str}}
    )
    conf = from_did_change_config(params)
    assert conf.diagnostic_publishing_method == expected_publishing_method
