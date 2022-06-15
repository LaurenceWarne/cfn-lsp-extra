import pytest
from pygls.lsp.types.basic_structures import Position
from pygls.workspace import Document

from cfn_lsp_extra.completions import intrinsic_function_completions


def test_intrinsic_function_completion_short_form():
    document = Document(
        uri="",
        source="""AWSTemplateFormatVersion: 2010-09-09
  Description: My template
  Resources:
    PublicSubnet:
      Type: AWS::EC2::Subnet
      Properties:
        VpcId: !
        CidrBlock: 192.168.0.0/24""",
    )
    position = Position(line=6, character=16)
    result = intrinsic_function_completions(document, position).items
    assert len(result) > 0
    assert all(c.label.startswith("!") for c in result)


def test_intrinsic_function_completion_full_name():
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
    result = intrinsic_function_completions(document, position).items
    assert len(result) > 0
    assert all(c.label.startswith("Fn::") for c in result)
