import pytest
import yaml

from cfn_lsp_extra.parsing import SafePositionLoader, flatten_mapping
from cfn_lsp_extra.properties import AWSProperty

content = """AWSTemplateFormatVersion: "2010-09-09"
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
    assert [10, 6] in positions[AWSProperty("AWS::EC2::Subnet", "CidrBlock")]
