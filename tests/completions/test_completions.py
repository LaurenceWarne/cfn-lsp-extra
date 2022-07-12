import pytest
from pygls.lsp.types import Position
from pygls.workspace import Document

from cfn_lsp_extra.aws_data import AWSPropertyName
from cfn_lsp_extra.aws_data import AWSResourceName
from cfn_lsp_extra.completions import completions_for

from ..test_aws_data import aws_context
from ..test_aws_data import aws_context_dct
from ..test_aws_data import aws_context_map
from ..test_aws_data import aws_property_string
from ..test_aws_data import aws_resource_string


@pytest.fixture
def document():
    return Document(uri="", source="\n" * 50)


@pytest.fixture
def resource_position():
    return Position(line=9, character=10)


@pytest.fixture
def property_position():
    return Position(line=40, character=50)


@pytest.fixture
def ref_position():
    return Position(line=9, character=18)


@pytest.fixture
def document_mapping_incomplete_service_provider(
    aws_resource_string, aws_property_string, resource_position
):
    incomplete_resource = aws_resource_string.split("::", 1)[0]
    return {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "My template",
        "Resources": {
            "PublicSubnet": {
                "Type": incomplete_resource,
                "__value_positions__": [
                    {
                        f"__position__{incomplete_resource}": [
                            resource_position.line,
                            resource_position.character,
                        ]
                    }
                ],
            },
        },
    }


@pytest.fixture
def document_mapping_incomplete_property(
    aws_resource_string, aws_property_string, resource_position, property_position
):
    incomplete_property = aws_property_string[:-5]
    return {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "My template",
        "Resources": {
            "PublicSubnet": {
                "Type": aws_resource_string,
                "Properties": {
                    incomplete_property: "",
                    f"__position__{incomplete_property}": [
                        property_position.line,
                        property_position.character,
                    ],
                },
                "__value_positions__": [
                    {
                        f"__position__{aws_resource_string}": [
                            resource_position.line,
                            resource_position.character,
                        ]
                    }
                ],
            }
        },
    }


@pytest.fixture
def document_mapping_incomplete_ref():
    return {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "My template",
        "Parameters": {
            "MyVpcId": {
                "Type": "AWS::EC2::VPC::Id",
                "__position__Type": [4, 4],
                "__value_positions__": [{"__position__AWS::EC2::VPC::Id": [4, 10]}],
            },
            "__position__MyVpcId": [3, 2],
        },
        "Resources": {
            "PublicSubnet": {
                "Type": "AWS::EC2::Subnet",
                "Properties": {
                    "VpcId": {
                        "Ref": ".",
                        "__value_positions__": [{"__position__.": [9, 18]}],
                    },
                    "CidrBlock": "192.168.0.0/24",
                    "__position__VpcId": [9, 6],
                    "__position__CidrBlock": [10, 6],
                    "__value_positions__": [{"__position__192.168.0.0/24": [10, 17]}],
                },
                "__position__Type": [7, 4],
                "__value_positions__": [{"__position__AWS::EC2::Subnet": [7, 10]}],
                "__position__Properties": [8, 4],
            },
            "__position__PublicSubnet": [6, 2],
        },
        "__position__AWSTemplateFormatVersion": [0, 0],
        "__value_positions__": [
            {"__position__2010-09-09": [0, 26]},
            {"__position__My template": [1, 13]},
        ],
        "__position__Description": [1, 0],
        "__position__Parameters": [2, 0],
        "__position__Resources": [5, 0],
    }


def test_property_completions(
    aws_context,
    document,
    document_mapping_incomplete_property,
    aws_property_string,
    property_position,
):
    result = completions_for(
        document_mapping_incomplete_property, aws_context, document, property_position
    )
    assert len(result.items) == 1
    assert result.items[0].label == aws_property_string
    assert result.items[0].text_edit.new_text == aws_property_string + ": "


def test_property_completions_with_colon(
    aws_context,
    document_mapping_incomplete_property,
    aws_property_string,
    property_position,
):
    document = Document(
        uri="",
        source="\n".join(
            (":" if i == property_position.line else "") for i in range(60)
        ),
    )
    result = completions_for(
        document_mapping_incomplete_property, aws_context, document, property_position
    )
    assert len(result.items) == 1
    assert result.items[0].label == aws_property_string
    assert result.items[0].text_edit.new_text == aws_property_string


def test_resource_completions(
    aws_context,
    document,
    document_mapping_incomplete_service_provider,
    aws_resource_string,
    resource_position,
):
    result = completions_for(
        document_mapping_incomplete_service_provider,
        aws_context,
        document,
        resource_position,
    )
    assert len(result.items) == 1
    assert result.items[0].label == aws_resource_string


def test_ref_completion(
    document, aws_context, document_mapping_incomplete_ref, ref_position
):
    result = completions_for(
        document_mapping_incomplete_ref,
        aws_context,
        document,
        ref_position,
    )
    assert len(result.items) == 2
    assert sorted(item.label for item in result.items) == ["MyVpcId", "PublicSubnet"]


def test_intrinsic_function_completions(aws_context):
    document = Document(
        uri="",
        source="""AWSTemplateFormatVersion: 2010-09-09
Description: My template
Resources:
  PublicSubnet:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: Fn
      CidrBlock: 192.168.0.0/24""",
    )
    position = Position(line=6, character=15)
    result = completions_for({}, aws_context, document, position).items
    assert len(result) > 0
    assert all(c.label.startswith("Fn::") for c in result)
