import json

import pytest
from pytest_mock import mocker

from cfn_lsp_extra.aws_data import AWSResourceName
from cfn_lsp_extra.context import load_context

from .test_aws_data import aws_context_dct


@pytest.fixture
def aws_context_str(aws_context_dct):
    return str(aws_context_dct)


@pytest.fixture
def mocker_cache_file(mocker, aws_context_dct, aws_context_str):
    cache_file = mocker.MagicMock(__open__=aws_context_str, exists=True)
    mocker.patch("json.load", lambda f: aws_context_dct)
    return cache_file


@pytest.fixture
def mocker_inexistant_cache_file(mocker):
    cache_file = mocker.MagicMock(exists=False)
    return cache_file


def test_load_context_reads_override_file(mocker, mocker_cache_file, aws_context_dct):
    result = load_context(mocker_cache_file)
    assert result == aws_context_dct


def test_load_context_reads_package_file(mocker_inexistant_cache_file):
    load_context(mocker_inexistant_cache_file)
