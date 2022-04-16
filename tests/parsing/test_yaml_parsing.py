import pytest
import yaml

from cfn_lsp_extra.aws_data import AWSProperty
from cfn_lsp_extra.parsing.yaml_parsing import SafePositionLoader
from cfn_lsp_extra.parsing.yaml_parsing import flatten_mapping


@pytest.fixture
def yaml_string():
    return """AWSTemplateFormatVersion: "2010-09-09"
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


def test_safe_position_loader(yaml_string):
    data = yaml.load(yaml_string, Loader=SafePositionLoader)


def test_flatten_mapping(yaml_string):
    data = yaml.load(yaml_string, Loader=SafePositionLoader)
    positions = flatten_mapping(data)
    print(positions)
    assert [(11, 6, 9), (18, 6, 9)] == sorted(
        positions[AWSProperty(resource="AWS::EC2::Subnet", property_="CidrBlock")]
    )
    assert [(12, 6, 19)] == sorted(
        positions[
            AWSProperty(resource="AWS::EC2::Subnet", property_="MapPublicIpOnLaunch")
        ]
    )
    assert [(13, 6, 5), (19, 6, 5)] == sorted(
        positions[AWSProperty(resource="AWS::EC2::Subnet", property_="VpcId")]
    )
    assert len(positions) == 3
