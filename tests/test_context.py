import json

import pytest
from pytest_mock import mocker

from cfn_lsp_extra.aws_data import AWSResourceName
from cfn_lsp_extra.context import cache

from .test_aws_data import aws_context_dct


@pytest.fixture
def aws_context_str(aws_context_dct):
    return str(aws_context_dct)


@pytest.fixture
def mocker_cache_file(mocker, aws_context_dct, aws_context_str):
    cache_file = mocker.MagicMock(__open__=aws_context_str, exists=True)
    mocker.patch("json.load", lambda f: aws_context_dct)
    return cache_file


def test_cache_reads_file(mocker, mocker_cache_file, aws_context_dct):
    result = cache(mocker_cache_file, False)
    assert result == aws_context_dct
