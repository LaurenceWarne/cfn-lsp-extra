import pytest
import yaml

from cfn_lsp_extra.parsing import SafePositionLoader
from cfn_lsp_extra.parsing import flatten_mapping
from cfn_lsp_extra.aws_data import AWSProperty


content = """AWSTemplateFormatVersion: "2010-09-09"
# Pointless comment
Description: My template
Parameters:
  DefaultVpcId:
    Type: String
    Default: vpc-1431243213
Resources:
  PublicSubnet:
    Type: AWS::EC2::Subnet
    Properties:
      CidrBlock: 172.31.48.0/20
      MapPublicIpOnLaunch: true
      VpcId: !Ref DefaultVpcId

  PrivateSubnet:
    Type: AWS::EC2::Subnet
    Properties:
      CidrBlock: 172.31.64.0/20
      VpcId:
        Ref: DefaultVpcId"""


def test_safe_line_loader():
    data = yaml.load(content, Loader=SafePositionLoader)
    positions = flatten_mapping(data)
    assert [[11, 6], [18, 6]] == sorted(
        positions[AWSProperty("AWS::EC2::Subnet", "CidrBlock")]
    )
    assert [[12, 6]] == sorted(
        positions[AWSProperty("AWS::EC2::Subnet", "MapPublicIpOnLaunch")]
    )
    assert [[13, 6], [19, 6]] == sorted(
        positions[AWSProperty("AWS::EC2::Subnet", "VpcId")]
    )
    assert len(positions) == 3
