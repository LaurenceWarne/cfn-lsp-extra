import pytest
from pygls.lsp.types import Position
from pygls.workspace import Document

from cfn_lsp_extra.aws_data import AWSPropertyName
from cfn_lsp_extra.aws_data import AWSResourceName
from cfn_lsp_extra.completions import completions_for

from ..test_aws_data import aws_context
from ..test_aws_data import aws_context_dct
from ..test_aws_data import aws_property_string
from ..test_aws_data import aws_resource_string


@pytest.fixture
def document():
    return Document(uri="", source="\n" * 20)


@pytest.fixture
def resource_position():
    return Position(line=9, character=10)


@pytest.fixture
def property_position():
    return Position(line=40, character=50)


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


def test_intrinsic_function_completion(aws_context):
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
    position = Position(line=6, character=17)
    result = completions_for({}, aws_context, document, position).items
    assert len(result) > 0
    assert all(c.label.startswith("Fn::") for c in result)
