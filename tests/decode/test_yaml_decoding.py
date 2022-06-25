import pytest
import yaml

from cfn_lsp_extra.decode.yaml_decoding import POSITION_PREFIX
from cfn_lsp_extra.decode.yaml_decoding import VALUES_POSITION_PREFIX
from cfn_lsp_extra.decode.yaml_decoding import SafePositionLoader


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


def test_safe_position_loader_data(yaml_string):
    data = yaml.load(yaml_string, Loader=SafePositionLoader)
    assert "AWSTemplateFormatVersion" in data
    assert "Description" in data
    assert "Parameters" in data
    assert "Resources" in data


def test_safe_position_loader_property_positions(yaml_string):
    data = yaml.load(yaml_string, Loader=SafePositionLoader)
    assert (
        POSITION_PREFIX + "CidrBlock" in data["Resources"]["PublicSubnet"]["Properties"]
    )
    assert (
        POSITION_PREFIX + "MapPublicIpOnLaunch"
        in data["Resources"]["PublicSubnet"]["Properties"]
    )
    assert POSITION_PREFIX + "VpcId" in data["Resources"]["PublicSubnet"]["Properties"]


def test_safe_position_loader_ref_positions(yaml_string):
    data = yaml.load(yaml_string, Loader=SafePositionLoader)
    prop1 = data["Resources"]["PublicSubnet"]["Properties"]["VpcId"]
    assert prop1[VALUES_POSITION_PREFIX][0][POSITION_PREFIX + "DefaultVpcId"] == [
        13,
        18,
    ]
    prop2 = data["Resources"]["PrivateSubnet"]["Properties"]["VpcId"]
    assert prop2[VALUES_POSITION_PREFIX][0][POSITION_PREFIX + "DefaultVpcId"] == [
        20,
        13,
    ]
