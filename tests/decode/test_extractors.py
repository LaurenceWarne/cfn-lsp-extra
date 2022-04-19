"""

"""
from types import SimpleNamespace

import pytest

from cfn_lsp_extra.aws_data import AWSProperty
from cfn_lsp_extra.decode.extractors import Extractor
from cfn_lsp_extra.decode.extractors import ResourceExtractor
from cfn_lsp_extra.decode.extractors import ResourcePropertyExtractor
from cfn_lsp_extra.decode.position import Spanning


@pytest.fixture
def document_mapping():
    return {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "My template",
        "Parameters": {
            "DefaultVpcId": {
                "Type": "String",
                "Default": "vpc-1431243213",
                "__position__Type": [5, 4],
                "__value_positions__": [
                    {"__position__String": [5, 10]},
                    {"__position__Default": [6, 4]},
                ],
                "__position__Default": [6, 4],
            },
            "__position__DefaultVpcId": [4, 2],
        },
        "Resources": {
            "PublicSubnet": {
                "Type": "AWS::EC2::Subnet",
                "Properties": {
                    "CidrBlock": "172.31.48.0/20",
                    "MapPublicIpOnLaunch": True,
                    "VpcId": {"Ref": "DefaultVpcId"},
                    "__position__CidrBlock": [11, 6],
                    "__value_positions__": [
                        {"__position__172.31.48.0/20": [11, 17]},
                        {"__position__MapPublicIpOnLaunch": [12, 6]},
                        {"__position__VpcId": [13, 6]},
                    ],
                    "__position__MapPublicIpOnLaunch": [12, 6],
                    "__position__VpcId": [13, 6],
                },
                "__position__Type": [9, 4],
                "__value_positions__": [{"__position__AWS::EC2::Subnet": [9, 10]}],
                "__position__Properties": [10, 4],
            },
            "PrivateSubnet": {
                "Type": "AWS::EC2::Subnet",
                "Properties": {
                    "CidrBlock": "172.31.64.0/20",
                    "VpcId": {
                        "Ref": "DefaultVpcId",
                        "__position__Ref": [20, 8],
                        "__value_positions__": [{"__position__DefaultVpcId": [20, 13]}],
                    },
                    "__position__CidrBlock": [18, 6],
                    "__value_positions__": [{"__position__172.31.64.0/20": [18, 17]}],
                    "__position__VpcId": [19, 6],
                },
                "__position__Type": [16, 4],
                "__value_positions__": [{"__position__AWS::EC2::Subnet": [16, 10]}],
                "__position__Properties": [17, 4],
            },
            "__position__PublicSubnet": [8, 2],
            "__position__PrivateSubnet": [15, 2],
        },
        "__position__AWSTemplateFormatVersion": [0, 0],
        "__value_positions__": [
            {"__position__2010-09-09": [0, 26]},
            {"__position__Description": [2, 0]},
        ],
        "__position__Description": [2, 0],
        "__position__Parameters": [3, 0],
        "__position__Resources": [7, 0],
    }


def test_extract():
    class TestExtractor(Extractor[str]):
        def extract_node(self, node):
            return [Spanning(value="prop", line=0, char=0, span=1)]

    test_extractor = TestExtractor()
    mapping = {"foo": {"bar": "baz"}}
    positions = test_extractor.extract(mapping)
    assert positions == {"prop": [(0, 0, 1), (0, 0, 1)]}


def test_resource_property_extractor(document_mapping):
    extractor = ResourcePropertyExtractor()
    positions = extractor.extract(document_mapping)
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


def test_resource_extractor(document_mapping):
    extractor = ResourceExtractor()
    positions = extractor.extract(document_mapping)
    assert [(9, 10, 16), (16, 10, 16)] == sorted(positions["AWS::EC2::Subnet"])
