import json
from unittest import mock as mocker

import pytest

from cfn_lsp_extra.aws_data import AWSContextMap
from cfn_lsp_extra.aws_data import AWSResourceName
from cfn_lsp_extra.context import load_context
from cfn_lsp_extra.context import with_custom

from .test_aws_data import aws_context
from .test_aws_data import aws_context_dct
from .test_aws_data import aws_context_map
from .test_aws_data import aws_property_string
from .test_aws_data import aws_resource_string


@pytest.fixture
def aws_context_str(aws_context_dct):
    return str(aws_context_dct)


@pytest.fixture
def mocker_cache_file(mocker, aws_context_dct, aws_context_str):
    opened_file = mocker.MagicMock(read=lambda: aws_context_str)
    cache_file = mocker.MagicMock(__open__=lambda _: opened_file, exists=lambda: True)
    mocker.patch("json.load", lambda f: aws_context_dct)
    return cache_file


@pytest.fixture
def mocker_inexistant_cache_file(mocker):
    cache_file = mocker.MagicMock(exists=lambda: False)
    return cache_file


@pytest.fixture
def mocker_custom_file(mocker):
    def _mocker_custom_file(new_description):
        custom_context_dct = {
            "resources": {
                "AWS::EC2::CapacityReservation": {"description": new_description}
            }
        }
        opened_file = mocker.MagicMock(read=lambda: str(custom_context_dct))
        cache_file = mocker.MagicMock(
            __open__=lambda _: opened_file, exists=lambda: True
        )
        mocker.patch("json.load", lambda f: custom_context_dct)
        return cache_file

    return _mocker_custom_file


def test_load_context_reads_override_file(mocker, mocker_cache_file, aws_context_dct):
    result = load_context(mocker_cache_file)
    assert [r.value for r in result.resource_map.keys()] == list(
        aws_context_dct["resources"].keys()
    )


def test_load_context_reads_package_file(mocker_inexistant_cache_file):
    load_context(mocker_inexistant_cache_file)


def test_with_custom(aws_context, mocker_custom_file):
    new_description = "new_description"
    result = with_custom(aws_context, custom_path=mocker_custom_file(new_description))
    assert (
        result[AWSResourceName(value="AWS::EC2::CapacityReservation")]["description"]
        == new_description
    )
