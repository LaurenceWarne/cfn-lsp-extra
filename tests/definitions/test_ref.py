"""
Test definitions for !Refs.
"""

from lsprotocol.types import Location
from lsprotocol.types import Position
from lsprotocol.types import Range
from pygls.workspace import TextDocument

from cfn_lsp_extra.decode import decode
from cfn_lsp_extra.definitions.ref import ref_definition

from ..test_aws_data import full_aws_context


def test_ref_definition_for_resource(full_aws_context):
    document_string = """AWSTemplateFormatVersion: "2010-09-09"
Description: My template

Resources:
  MyVpc:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 172.31.0.0/16

  PublicSubnet:
    Type: AWS::EC2::Subnet
    Properties:
      CidrBlock: 172.31.48.0/20
      VpcId: !Ref MyVpc"""
    document = TextDocument(uri="", source=document_string)
    template_data = decode(document_string, "f.yaml")
    position = Position(line=13, character=22)
    result = ref_definition(template_data, document, position, full_aws_context)
    assert result.range.start == Position(line=4, character=2)


def test_ref_definition_for_parameter(full_aws_context):
    document_string = """AWSTemplateFormatVersion: "2010-09-09"
Description: My template
Parameters:
  DefaultVpcId:
    Type: String
    Default: vpc-id

Resources:
  PublicSubnet:
    Type: AWS::EC2::Subnet
    Properties:
      CidrBlock: 172.31.48.0/20
      VpcId: !Ref DefaultVpcId"""
    document = TextDocument(uri="", source=document_string)
    template_data = decode(document_string, "f.yaml")
    position = Position(line=12, character=26)
    result = ref_definition(template_data, document, position, full_aws_context)
    assert result.range.start == Position(line=3, character=2)


def test_ref_definition_not_valid(full_aws_context):
    document_string = """AWSTemplateFormatVersion: "2010-09-09"
Description: My template
Parameters:
  DefaultVpcId:
    Type: String
    Default: vpc-id

Resources:
  PublicSubnet:
    Type: AWS::EC2::Subnet
    Properties:
      CidrBlock: 172.31.48.0/20
      VpcId: !Ref DefaultVpcId"""
    document = TextDocument(uri="", source=document_string)
    template_data = decode(document_string, "f.yaml")
    position = Position(line=11, character=26)
    result = ref_definition(template_data, document, position, full_aws_context)
    assert result is None
