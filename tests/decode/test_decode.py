"""
Tests for cfn_lsp_extra/decode/__init__.py
"""

import pytest
from pygls.lsp.types import Position

from cfn_lsp_extra.decode import CfnDecodingException
from cfn_lsp_extra.decode import decode
from cfn_lsp_extra.decode import decode_unfinished
from cfn_lsp_extra.decode.extractors import Extractor
from cfn_lsp_extra.decode.extractors import remove_prefix
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
                    name = remove_prefix(key, POSITION_PREFIX)
                    line, char = value
                    spans.append(Spanning(value=name, line=line, char=char, span=1))
            return spans

    return TestExtractor()


@pytest.fixture
def partial_property():
    return "RequiresCompatibili"


@pytest.fixture
def resource_of_partial_property():
    return "taskdefinition"


@pytest.fixture
def unfinished_json_string(partial_property, resource_of_partial_property):
    return f"""{{
    "AWSTemplateFormatVersion": "2010-09-09",
    "Resources": {{
        "{resource_of_partial_property}": {{
            "Type": "AWS::ECS::TaskDefinition",
            "Properties": {{
                "{partial_property}"
                "Volumes": [
                    {{
                        "Host": {{
                            "SourcePath": "/var/lib/docker/vfs/dir/"
                        }},
                        "Name": "my-vol"
                    }}
                ]
            }}
        }}
    }}
}}"""


@pytest.fixture
def unfinished_yaml_string(partial_property, resource_of_partial_property):
    return f"""AWSTemplateFormatVersion: "2010-09-09"
# Pointless comment
Description: My template
Parameters:
  DefaultVpcId:
    Type: String
    Default: vpc-1431243213
Resources:
  {resource_of_partial_property}:
    Type: AWS::ECS::TaskDefinition
    Properties:
      NetworkMode: awsvpc
      {partial_property}"""


def test_decode_for_json(extractor, json_string):
    result = decode(json_string, "f.json")
    assert "AWSTemplateFormatVersion" in result


def test_decode_for_yaml(extractor, yaml_string):
    result = decode(yaml_string, "f.yaml")
    assert "AWSTemplateFormatVersion" in result


def test_decode_for_invalid_json(extractor, yaml_string):
    with pytest.raises(CfnDecodingException):
        decode(yaml_string, "f.json")


def test_decode_for_invalid_yaml(extractor):
    invalid_yaml = "foo: {bar"
    with pytest.raises(CfnDecodingException):
        decode(invalid_yaml, "f.yaml")


def test_decode_unfinished_for_json(extractor, json_string):
    result = decode_unfinished(json_string, "f.json", Position(line=6, character=0))
    assert "AWSTemplateFormatVersion" in result


def test_decode_unfinished_for_yaml(extractor, yaml_string):
    result = decode_unfinished(yaml_string, "f.yaml", Position(line=12, character=0))
    assert "AWSTemplateFormatVersion" in result


def test_decode_unfinished_for_unfinished_json(
    extractor, unfinished_json_string, resource_of_partial_property, partial_property
):
    result = decode_unfinished(
        unfinished_json_string, "f.json", Position(line=6, character=0)
    )
    assert (
        partial_property
        in result["Resources"][resource_of_partial_property]["Properties"]
    )


def test_decode_unfinished_for_unfinished_yaml(
    extractor, unfinished_yaml_string, resource_of_partial_property, partial_property
):
    result = decode_unfinished(
        unfinished_yaml_string, "f.yaml", Position(line=12, character=0)
    )
    assert (
        partial_property
        in result["Resources"][resource_of_partial_property]["Properties"]
    )


def test_decode_unfinished_for_yaml_with_empty_line_property(
    extractor, resource_of_partial_property
):
    doc = f"""AWSTemplateFormatVersion: "2010-09-09"
Description: My template
Parameters:
  DefaultVpcId:
    Type: String
    Default: vpc-1431243213
Resources:
  {resource_of_partial_property}:
    Type: AWS::ECS::TaskDefinition
    Properties:
      
      NetworkMode: awsvpc"""
    result = decode_unfinished(doc, "f.yaml", Position(line=10, character=6))
    assert "." in result["Resources"][resource_of_partial_property]["Properties"]


def test_decode_unfinished_for_yaml_with_resource_type(
    extractor, resource_of_partial_property
):
    doc = f"""AWSTemplateFormatVersion: "2010-09-09"
Description: My template
Parameters:
  DefaultVpcId:
    Type: String
    Default: vpc-1431243213
Resources:
  {resource_of_partial_property}:
    Type: """
    result = decode_unfinished(doc, "f.yaml", Position(line=8, character=10))
    assert "." == result["Resources"][resource_of_partial_property]["Type"]
