import pytest
from cfn_lsp_extra.aws_data import (
    AWSLogicalId,
    AWSParameter,
    AWSRefName,
    AWSResourceName,
)
from cfn_lsp_extra.completions.static import RESOURCE_PATH
from cfn_lsp_extra.decode.extractors import (
    AllowedValuesExtractor,
    CompositeExtractor,
    Extractor,
    KeyExtractor,
    LogicalIdExtractor,
    ParameterExtractor,
    RecursiveExtractor,
    ResourceExtractor,
    ResourcePropertyExtractor,
    StaticExtractor,
)
from cfn_lsp_extra.decode.position import Spanning

from ..test_aws_data import full_aws_context


@pytest.fixture
def document_mapping():
    return {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "My template",
        "Parameters": {
            "DefaultVpcId": {
                "Default": "vpc-1431243213",
                "Type": "String",
                "__position__Default": [6, 4],
                "__position__Type": [5, 4],
                "__value_positions__": [
                    {"__position__String": [5, 10]},
                    {"__position__vpc-1431243213": [6, 13]},
                ],
            },
            "__position__DefaultVpcId": [4, 2],
        },
        "Resources": {
            "PrivateSubnet": {
                "Properties": {
                    "CidrBlock": "172.31.64.0/20",
                    "Tags": [
                        {
                            "Key": "MyKey",
                            "Value": {
                                "Fn::Join": [
                                    "",
                                    [
                                        {
                                            "Ref": "DefaultVpcId",
                                            "__value_positions__": [
                                                {"__position__DefaultVpcId": [23, 34]}
                                            ],
                                        },
                                        "VPC",
                                    ],
                                ]
                            },
                            "__position__Key": [22, 10],
                            "__position__Value": [23, 10],
                            "__value_positions__": [{"__position__MyKey": [22, 15]}],
                        }
                    ],
                    "VpcId": {
                        "Ref": "DefaultVpcId",
                        "__position__Ref": [20, 8],
                        "__value_positions__": [{"__position__DefaultVpcId": [20, 13]}],
                    },
                    "__position__CidrBlock": [18, 6],
                    "__position__Tags": [21, 6],
                    "__position__VpcId": [19, 6],
                    "__value_positions__": [{"__position__172.31.64.0/20": [18, 17]}],
                },
                "Type": "AWS::EC2::Subnet",
                "__position__Properties": [17, 4],
                "__position__Type": [16, 4],
                "__value_positions__": [{"__position__AWS::EC2::Subnet": [16, 10]}],
            },
            "PublicSubnet": {
                "Properties": {
                    "CidrBlock": "172.31.48.0/20",
                    "MapPublicIpOnLaunch": True,
                    "VpcId": {
                        "Ref": "DefaultVpcId",
                        "__value_positions__": [{"__position__DefaultVpcId": [13, 18]}],
                    },
                    "__position__CidrBlock": [11, 6],
                    "__position__MapPublicIpOnLaunch": [12, 6],
                    "__position__VpcId": [13, 6],
                    "__value_positions__": [
                        {"__position__172.31.48.0/20": [11, 17]},
                        {"__position__true": [12, 27]},
                    ],
                },
                "Type": "AWS::EC2::Subnet",
                "__position__Properties": [10, 4],
                "__position__Type": [9, 4],
                "__value_positions__": [{"__position__AWS::EC2::Subnet": [9, 10]}],
            },
            "__position__PrivateSubnet": [15, 2],
            "__position__PublicSubnet": [8, 2],
        },
        "__position__AWSTemplateFormatVersion": [0, 0],
        "__position__Description": [2, 0],
        "__position__Parameters": [3, 0],
        "__position__Resources": [7, 0],
        "__value_positions__": [
            {"__position__2010-09-09": [0, 26]},
            {"__position__My template": [2, 13]},
        ],
    }


@pytest.fixture
def incomplete_logical_id_document_mapping():
    return {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Resources": {
            "MyResource": 3,
            "MyTaskde": None,
            "__position__MyResource": [2, 2],
            "__value_positions__": [
                {"__position__3": [2, 8]},
                {"__position__": [3, 11]},
            ],
            "__position__MyTaskde": [3, 2],
        },
        "__position__AWSTemplateFormatVersion": [0, 0],
        "__value_positions__": [{"__position__2010-09-09": [0, 26]}],
        "__position__Resources": [1, 0],
    }


@pytest.fixture
def no_resources_document_mapping():
    return {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Resources": "MyTaskde",
        "__position__AWSTemplateFormatVersion": [0, 0],
        "__value_positions__": [
            {"__position__2010-09-09": [0, 26]},
            {"__position__MyTaskde": [2, 2]},
        ],
        "__position__Resources": [1, 0],
    }


def test_recursive_extractor():
    class TestExtractor(RecursiveExtractor[str]):
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
        positions[AWSResourceName(value="AWS::EC2::Subnet") / "CidrBlock"]
    )
    assert [(12, 6, 19)] == sorted(
        positions[AWSResourceName(value="AWS::EC2::Subnet") / "MapPublicIpOnLaunch"]
    )
    assert [(13, 6, 5), (19, 6, 5)] == sorted(
        positions[AWSResourceName(value="AWS::EC2::Subnet") / "VpcId"]
    )
    assert len(positions) == 7


def test_resource_property_extractor_nested(document_mapping):
    document_mapping = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "My template",
        "Resources": {
            "ECSService": {
                "Type": "AWS::ECS::Service",
                "Properties": {
                    "DesiredCount": 1,
                    "Cluster": {"Ref": "ECSCluster"},
                    "LaunchType": "FARGATE",
                    "NetworkConfiguration": {
                        "AwsvpcConfiguration": {
                            "AssignPublicIp": "ENABLED",
                            "SecurityGroups": [{"Ref": "HTTPSecurityGroup"}],
                            "Subnets": [{"Ref": "PublicSubnet"}],
                            "__position__AssignPublicIp": [17, 10],
                            "__value_positions__": [{"__position__ENABLED": [17, 26]}],
                            "__position__SecurityGroups": [18, 10],
                            "__position__Subnets": [20, 10],
                        },
                        "__position__AwsvpcConfiguration": [16, 8],
                    },
                    "TaskDefinition": {"Ref": "ECSTaskDefinition"},
                    "__position__DesiredCount": [11, 6],
                    "__value_positions__": [
                        {"__position__1": [11, 20]},
                        {"__position__ECSCluster": [12, 15]},
                        {"__position__FARGATE": [13, 18]},
                        {"__position__ECSTaskDefinition": [22, 22]},
                    ],
                    "__position__Cluster": [12, 6],
                    "__position__LaunchType": [13, 6],
                    "__position__NetworkConfiguration": [15, 6],
                    "__position__TaskDefinition": [22, 6],
                },
                "__position__Type": [9, 4],
                "__value_positions__": [{"__position__AWS::ECS::Service": [9, 10]}],
                "__position__Properties": [10, 4],
            },
            "__position__ECSService": [8, 2],
        },
        "__position__AWSTemplateFormatVersion": [0, 0],
        "__value_positions__": [
            {"__position__2010-09-09": [0, 26]},
            {"__position__My template": [2, 13]},
        ],
        "__position__Description": [2, 0],
        "__position__Resources": [7, 0],
    }
    extractor = ResourcePropertyExtractor()
    positions = extractor.extract(document_mapping)
    assert [(16, 8, 19)] == positions[
        AWSResourceName(value="AWS::ECS::Service")
        / "NetworkConfiguration"
        / "AwsvpcConfiguration"
    ]
    assert [(17, 10, 14)] == positions[
        AWSResourceName(value="AWS::ECS::Service")
        / "NetworkConfiguration"
        / "AwsvpcConfiguration"
        / "AssignPublicIp"
    ]


def test_resource_property_extractor_for_nested_list():
    document_mapping = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "My template",
        "Resources": {
            "SSHSecurityGroup": {
                "Type": "AWS::EC2::SecurityGroup",
                "Properties": {
                    "GroupDescription": "SSH access",
                    "VpcId": {
                        "Ref": "DefaultVpcId",
                        "__position__Ref": [11, 9],
                        "__value_positions__": [{"__position__DefaultVpcId": [11, 14]}],
                    },
                    "SecurityGroupIngress": [
                        {
                            "IpProtocol": "tcp",
                            "FromPort": 22,
                            "ToPort": 22,
                            "CidrIp": "0.0.0.0/0",
                            "__position__IpProtocol": [13, 8],
                            "__value_positions__": [
                                {"__position__tcp": [13, 20]},
                                {"__position__22": [14, 18]},
                                {"__position__22": [15, 16]},
                                {"__position__0.0.0.0/0": [16, 16]},
                            ],
                            "__position__FromPort": [14, 8],
                            "__position__ToPort": [15, 8],
                            "__position__CidrIp": [16, 8],
                        }
                    ],
                    "__position__GroupDescription": [9, 6],
                    "__value_positions__": [{"__position__SSH access": [9, 24]}],
                    "__position__VpcId": [10, 6],
                    "__position__SecurityGroupIngress": [12, 6],
                },
                "__position__Type": [7, 4],
                "__value_positions__": [
                    {"__position__AWS::EC2::SecurityGroup": [7, 10]}
                ],
                "__position__Properties": [8, 4],
            },
            "__position__SSHSecurityGroup": [6, 2],
        },
        "__position__AWSTemplateFormatVersion": [1, 0],
        "__value_positions__": [
            {"__position__2010-09-09": [1, 26]},
            {"__position__My template": [3, 13]},
        ],
        "__position__Description": [3, 0],
        "__position__Resources": [5, 0],
    }
    extractor = ResourcePropertyExtractor()
    positions = extractor.extract(document_mapping)
    assert [(13, 8, 10)] == positions[
        AWSResourceName(value="AWS::EC2::SecurityGroup")
        / "SecurityGroupIngress"
        / "IpProtocol"
    ]


def test_resource_property_extractor_for_resource_with_one_incomplete_property():
    document_mapping = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "My template",
        "Resources": {
            "PublicSubnet": {
                "Type": "AWS::EC2::Subnet",
                "Properties": "CidrBlock",
                "__position__Type": [5, 4],
                "__value_positions__": [
                    {"__position__AWS::EC2::Subnet": [5, 10]},
                    {"__position__CidrBlock": [7, 6]},
                ],
                "__position__Properties": [6, 4],
            },
            "__position__PublicSubnet": [4, 2],
        },
        "__position__AWSTemplateFormatVersion": [0, 0],
        "__value_positions__": [
            {"__position__2010-09-09": [0, 26]},
            {"__position__My template": [2, 13]},
        ],
        "__position__Description": [2, 0],
        "__position__Resources": [3, 0],
    }
    extractor = ResourcePropertyExtractor()
    positions = extractor.extract(document_mapping)
    assert [(7, 6, 9)] == positions[
        AWSResourceName(value="AWS::EC2::Subnet") / "CidrBlock"
    ]


def test_resource_property_extractor_unfinished_subproperty():
    extractor = ResourcePropertyExtractor()
    template_data = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Resources": {
            "__position__DDB": [10, 2],
            "DDB": {
                "Properties": {
                    "KeySchema": ["foo"],
                    "StreamSpecification": ".",
                    "__position__KeySchema": [13, 6],
                    "__position__StreamSpecification": [15, 6],
                    "__value_positions__": [{"__position__.": [16, 8]}],
                },
                "Type": "AWS::DynamoDB::Table",
                "__position__Properties": [12, 4],
                "__position__Type": [11, 4],
                "__value_positions__": [{"__position__AWS::DynamoDB::Table": [11, 10]}],
            },
        },
        "__position__AWSTemplateFormatVersion": [0, 0],
        "__position__Description": [1, 0],
        "__position__Resources": [2, 0],
        "__value_positions__": [
            {"__position__2010-09-09": [0, 26]},
            {"__position__An example CloudFormation template for Fargate.": [1, 13]},
        ],
    }

    positions = extractor.extract(template_data)
    assert (
        AWSResourceName(value="AWS::DynamoDB::Table") / "StreamSpecification" / "."
        in positions
    )


def test_resource_extractor(document_mapping):
    extractor = ResourceExtractor()
    positions = extractor.extract(document_mapping)
    assert [(9, 10, 16), (16, 10, 16)] == sorted(
        positions[AWSResourceName(value="AWS::EC2::Subnet")]
    )


def test_resource_extractor_for_incomplete_resource():
    document_mapping = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Resources": {
            "PublicSubnet": {
                "Type": "AWS::EC2::Subnet",
                "__position__Type": [9, 4],
                "__value_positions__": [{"__position__AWS::EC2::Subnet": [9, 10]}],
            },
            "__position__PublicSubnet": [8, 2],
        },
        "__position__AWSTemplateFormatVersion": [0, 0],
        "__value_positions__": [
            {"__position__2010-09-09": [0, 26]},
            {"__position__Description": [2, 0]},
        ],
        "__position__Parameters": [3, 0],
        "__position__Resources": [7, 0],
    }
    extractor = ResourceExtractor()
    positions = extractor.extract(document_mapping)
    assert [(9, 10, 16)] == positions[AWSResourceName(value="AWS::EC2::Subnet")]


def test_resource_extractor_for_empty_resources(no_resources_document_mapping):
    extractor = ResourceExtractor()
    positions = extractor.extract(no_resources_document_mapping)
    assert not positions


def test_resource_extractor_for_incomplete_logical_id(
    incomplete_logical_id_document_mapping,
):
    extractor = ResourceExtractor()
    positions = extractor.extract(incomplete_logical_id_document_mapping)
    assert not positions


def test_composite_extractor(document_mapping):
    extractor = CompositeExtractor(ResourceExtractor(), ResourcePropertyExtractor())
    positions = extractor.extract(document_mapping)
    assert [(9, 10, 16), (16, 10, 16)] == sorted(
        positions[AWSResourceName(value="AWS::EC2::Subnet")]
    )
    assert [(9, 10, 16), (16, 10, 16)] == sorted(
        positions[AWSResourceName(value="AWS::EC2::Subnet")]
    )
    assert [(11, 6, 9), (18, 6, 9)] == sorted(
        positions[AWSResourceName(value="AWS::EC2::Subnet") / "CidrBlock"]
    )
    assert [(12, 6, 19)] == positions[
        AWSResourceName(value="AWS::EC2::Subnet") / "MapPublicIpOnLaunch"
    ]
    assert [(13, 6, 5), (19, 6, 5)] == sorted(
        positions[AWSResourceName(value="AWS::EC2::Subnet") / "VpcId"]
    )


def test_key_extractor(document_mapping):
    extractor = KeyExtractor[AWSRefName]("Ref", lambda s: AWSRefName(value=s))
    positions = extractor.extract(document_mapping)
    assert [(13, 18, 12), (20, 13, 12), (23, 34, 12)] == sorted(
        positions[AWSRefName(value="DefaultVpcId")]
    )


def test_logical_id_extractor(document_mapping):
    extractor = LogicalIdExtractor()
    positions = extractor.extract(document_mapping)
    assert [(15, 2, 13)] == positions[
        AWSLogicalId(logical_name="PrivateSubnet", type_="AWS::EC2::Subnet")
    ]
    assert [(8, 2, 12)] == positions[
        AWSLogicalId(logical_name="PublicSubnet", type_="AWS::EC2::Subnet")
    ]


def test_logical_id_extractor_incomplete_logical_id(
    incomplete_logical_id_document_mapping,
):
    extractor = LogicalIdExtractor()
    positions = extractor.extract(incomplete_logical_id_document_mapping)
    assert [(3, 2, 8)] == positions[AWSLogicalId(logical_name="MyTaskde", type_=None)]
    assert [(2, 2, 10)] == positions[
        AWSLogicalId(logical_name="MyResource", type_=None)
    ]


def test_static_extractor(document_mapping):
    extractor = StaticExtractor(paths={RESOURCE_PATH})
    positions = extractor.extract(document_mapping)
    assert [(9, 4, 4), (10, 4, 10), (16, 4, 4), (17, 4, 10)] == sorted(
        positions[RESOURCE_PATH]
    )


def test_static_resource_key_extractor_for_empty_resources(
    no_resources_document_mapping,
):
    extractor = StaticExtractor(paths={RESOURCE_PATH})
    positions = extractor.extract(no_resources_document_mapping)
    assert not positions


def test_static_resource_key_extractor_for_empty_resource():
    document_mapping = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "My template",
        "Resources": {
            "PublicSubnet": "foo",
            "__position__PublicSubnet": [4, 2],
        },
        "__position__AWSTemplateFormatVersion": [0, 0],
        "__value_positions__": [
            {"__position__2010-09-09": [0, 26]},
            {"__position__My template": [2, 13]},
        ],
        "__position__Description": [2, 0],
        "__position__Resources": [3, 0],
    }
    extractor = StaticExtractor(paths={RESOURCE_PATH})
    positions = extractor.extract(document_mapping)
    assert not positions


def test_allowed_values_extractor(full_aws_context):
    extractor = AllowedValuesExtractor()

    document_mapping = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Parameters": {
            "BaseStackName": {
                "Type": "String",
                "Description": "Name of the base stack",
                "__position__Type": [3, 4],
                "__value_positions__": [
                    {"__position__String": [3, 10]},
                    {"__position__Name of the base stack": [4, 17]},
                ],
                "__position__Description": [4, 4],
            },
            "LayerKey": {
                "Type": "String",
                "Description": (
                    "Name of the S3 key pointing to the lambda layer containg the"
                    " executable"
                ),
                "__position__Type": [6, 4],
                "__value_positions__": [
                    {"__position__String": [6, 10]},
                    {
                        "__position__Name of the S3 key pointing to the lambda layer containg the executable": [
                            7,
                            17,
                        ]
                    },
                ],
                "__position__Description": [7, 4],
            },
            "__position__BaseStackName": [2, 2],
            "__position__LayerKey": [5, 2],
        },
        "Resources": {
            "ExeLambdaLayer": {
                "Type": "AWS::Lambda::LayerVersion",
                "Properties": {
                    "Content": {
                        "S3Bucket": {
                            "Fn::ImportValue": {
                                "Fn::Sub": "${BaseStackName}-MiscBucket",
                                "__position__Fn::Sub": [16, 10],
                                "__value_positions__": [
                                    {
                                        "__position__${BaseStackName}-MiscBucket": [
                                            16,
                                            21,
                                        ]
                                    }
                                ],
                            }
                        },
                        "S3Key": {
                            "Ref": "LayerKey",
                            "__value_positions__": [{"__position__LayerKey": [17, 20]}],
                        },
                        "__position__S3Bucket": [15, 8],
                        "__position__S3Key": [17, 8],
                    },
                    "__position__Content": [14, 6],
                },
                "__position__Type": [12, 4],
                "__value_positions__": [
                    {"__position__AWS::Lambda::LayerVersion": [12, 10]}
                ],
                "__position__Properties": [13, 4],
            },
            "LambdaFunction": {
                "Type": "AWS::Lambda::Function",
                "Properties": {
                    "Layers": [
                        "arn:aws:lambda:us-east-1:553035198032:layer:git-lambda2:8",
                        {
                            "Ref": "ExeLambdaLayer",
                            "__value_positions__": [
                                {"__position__ExeLambdaLayer": [25, 15]}
                            ],
                        },
                    ],
                    "Role": {
                        "Fn::GetAtt": ["LambdaFunctionRole", "Arn"],
                        "__value_positions__": [
                            {"__position__LambdaFunctionRole.Arn": [26, 20]}
                        ],
                    },
                    "Runtime": "provided.al2",
                    "Handler": "bootstrap",
                    "Timeout": 120,
                    "MemorySize": 512,
                    "__position__Layers": [22, 6],
                    "__position__Role": [26, 6],
                    "__position__Runtime": [27, 6],
                    "__value_positions__": [
                        {"__position__provided.al2": [27, 15]},
                        {"__position__bootstrap": [28, 15]},
                        {"__position__120": [29, 15]},
                        {"__position__512": [30, 18]},
                    ],
                    "__position__Handler": [28, 6],
                    "__position__Timeout": [29, 6],
                    "__position__MemorySize": [30, 6],
                },
                "__position__Type": [20, 4],
                "__value_positions__": [
                    {"__position__AWS::Lambda::Function": [20, 10]}
                ],
                "__position__Properties": [21, 4],
            },
            "__position__ExeLambdaLayer": [11, 2],
            "__position__LambdaFunction": [19, 2],
        },
        "__position__AWSTemplateFormatVersion": [0, 0],
        "__value_positions__": [{"__position__2010-09-09": [0, 26]}],
        "__position__Parameters": [1, 0],
        "__position__Resources": [9, 0],
    }

    positions = extractor.extract(document_mapping)
    assert [(27, 15, 12)] in positions.values()
