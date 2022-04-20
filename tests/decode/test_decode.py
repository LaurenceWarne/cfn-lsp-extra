"""
Tests for cfn_lsp_extra/decode/__init__.py
"""

import pytest

from cfn_lsp_extra.decode import CfnDecodingException
from cfn_lsp_extra.decode import decode
from cfn_lsp_extra.decode.extractors import Extractor
from cfn_lsp_extra.decode.position import PositionLookup
from cfn_lsp_extra.decode.position import Spanning
from cfn_lsp_extra.decode.yaml_decoding import POSITION_PREFIX

from .test_json_decoding import json_string
from .test_yaml_decoding import yaml_string


@pytest.fixture
def extractor():
    class TestExtractor(Extractor[str]):
        def extract_node(self, node):
            spans = []
            for key, value in node.items():
                if key.startswith(POSITION_PREFIX):
                    name = key.lstrip(POSITION_PREFIX)
                    line, char = value
                    spans.append(Spanning(value=name, line=line, char=char, span=1))
            return spans

    return TestExtractor()


def test_decode_for_json(extractor, json_string):
    result = decode(json_string, "f.json", extractor)
    assert "AWSTemplateFormatVersion" in result


def test_decode_for_yaml(extractor, yaml_string):
    result = decode(yaml_string, "f.yaml", extractor)
    assert "AWSTemplateFormatVersion" in result


def test_decode_for_invalid_json(extractor, yaml_string):
    with pytest.raises(CfnDecodingException):
        decode(yaml_string, "f.json", extractor)


def test_decode_for_invalid_yaml(extractor):
    invalid_yaml = "foo: {bar"
    with pytest.raises(CfnDecodingException):
        decode(invalid_yaml, "f.yaml", extractor)
