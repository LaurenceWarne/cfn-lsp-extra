import pytest
from pygls.lsp.types import Position

from cfn_lsp_extra.aws_data import AWSLogicalId
from cfn_lsp_extra.aws_data import AWSRefName
from cfn_lsp_extra.ref import resolve_ref

from .decode.test_extractors import document_mapping


@pytest.fixture
def document_mapping_with_logical_id_refs():
    return {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "An example CloudFormation template for Fargate.",
        "Parameters": {
            "Image": {
                "Type": "String",
                "Default": "123456789012.dkr.ecr.region.amazonaws.com/image:tag",
                "__position__Type": [14, 4],
                "__value_positions__": [
                    {"__position__String": [14, 10]},
                    {
                        "__position__123456789012.dkr.ecr.region.amazonaws.com/image:tag": [
                            16,
                            13,
                        ]
                    },
                ],
                "__position__Default": [16, 4],
            },
            "ServiceName": {
                "Type": "String",
                "Default": "MyService",
                "__position__Type": [18, 4],
                "__value_positions__": [
                    {"__position__String": [18, 10]},
                    {"__position__MyService": [20, 13]},
                ],
                "__position__Default": [20, 4],
            },
            "ContainerPort": {
                "Type": "Number",
                "Default": 80,
                "__position__Type": [22, 4],
                "__value_positions__": [
                    {"__position__Number": [22, 10]},
                    {"__position__80": [23, 13]},
                ],
                "__position__Default": [23, 4],
            },
            "__position__Image": [13, 2],
            "__position__ServiceName": [17, 2],
            "__position__ContainerPort": [21, 2],
        },
        "Resources": {
            "TaskDefinition": {
                "Type": "AWS::ECS::TaskDefinition",
                "DependsOn": "LogGroup",
                "Properties": {
                    "Family": {
                        "Fn::Join": [
                            "",
                            [
                                {
                                    "Ref": "ServiceName",
                                    "__value_positions__": [
                                        {"__position__ServiceName": [54, 31]}
                                    ],
                                },
                                "TaskDefinition",
                            ],
                        ]
                    },
                    "NetworkMode": "awsvpc",
                    "RequiresCompatibilities": ["FARGATE"],
                    "Cpu": 256,
                    "Memory": "0.5GB",
                    "ExecutionRoleArn": {
                        "Ref": "ExecutionRole",
                        "__value_positions__": [
                            {"__position__ExecutionRole": [69, 29]}
                        ],
                    },
                    "TaskRoleArn": {
                        "Ref": "TaskRole",
                        "__value_positions__": [{"__position__TaskRole": [71, 24]}],
                    },
                    "ContainerDefinitions": [
                        {
                            "Name": {
                                "Ref": "ServiceName",
                                "__value_positions__": [
                                    {"__position__ServiceName": [73, 21]}
                                ],
                            },
                            "Image": {
                                "Ref": "Image",
                                "__value_positions__": [
                                    {"__position__Image": [74, 22]}
                                ],
                            },
                            "PortMappings": [
                                {
                                    "ContainerPort": {
                                        "Ref": "ContainerPort",
                                        "__value_positions__": [
                                            {"__position__ContainerPort": [76, 34]}
                                        ],
                                    },
                                    "__position__ContainerPort": [76, 14],
                                }
                            ],
                            "LogConfiguration": {
                                "LogDriver": "awslogs",
                                "Options": {
                                    "awslogs-region": {
                                        "Ref": "AWS::Region",
                                        "__value_positions__": [
                                            {"__position__AWS::Region": [81, 35]}
                                        ],
                                    },
                                    "awslogs-group": {
                                        "Ref": "LogGroup",
                                        "__value_positions__": [
                                            {"__position__LogGroup": [82, 34]}
                                        ],
                                    },
                                    "awslogs-stream-prefix": "ecs",
                                    "__position__awslogs-region": [81, 14],
                                    "__position__awslogs-group": [82, 14],
                                    "__position__awslogs-stream-prefix": [83, 14],
                                    "__value_positions__": [
                                        {"__position__ecs": [83, 37]}
                                    ],
                                },
                                "__position__LogDriver": [79, 12],
                                "__value_positions__": [
                                    {"__position__awslogs": [79, 23]}
                                ],
                                "__position__Options": [80, 12],
                            },
                            "__position__Name": [73, 10],
                            "__position__Image": [74, 10],
                            "__position__PortMappings": [75, 10],
                            "__position__LogConfiguration": [78, 10],
                        }
                    ],
                    "__position__Family": [54, 6],
                    "__position__NetworkMode": [56, 6],
                    "__value_positions__": [
                        {"__position__awsvpc": [56, 19]},
                        {"__position__256": [59, 11]},
                        {"__position__0.5GB": [65, 14]},
                    ],
                    "__position__RequiresCompatibilities": [57, 6],
                    "__position__Cpu": [59, 6],
                    "__position__Memory": [65, 6],
                    "__position__ExecutionRoleArn": [69, 6],
                    "__position__TaskRoleArn": [71, 6],
                    "__position__ContainerDefinitions": [72, 6],
                },
                "__position__Type": [50, 4],
                "__value_positions__": [
                    {"__position__AWS::ECS::TaskDefinition": [50, 10]},
                    {"__position__LogGroup": [52, 15]},
                ],
                "__position__DependsOn": [52, 4],
                "__position__Properties": [53, 4],
            },
            "ExecutionRole": {
                "Type": "AWS::IAM::Role",
                "Properties": {
                    "RoleName": {
                        "Fn::Join": [
                            "",
                            [
                                {
                                    "Ref": "ServiceName",
                                    "__value_positions__": [
                                        {"__position__ServiceName": [87, 33]}
                                    ],
                                },
                                "ExecutionRole",
                            ],
                        ]
                    },
                    "AssumeRolePolicyDocument": {
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {
                                    "Service": "ecs-tasks.amazonaws.com",
                                    "__position__Service": [92, 14],
                                    "__value_positions__": [
                                        {
                                            "__position__ecs-tasks.amazonaws.com": [
                                                92,
                                                23,
                                            ]
                                        }
                                    ],
                                },
                                "Action": "sts:AssumeRole",
                                "__position__Effect": [90, 12],
                                "__value_positions__": [
                                    {"__position__Allow": [90, 20]},
                                    {"__position__sts:AssumeRole": [93, 20]},
                                ],
                                "__position__Principal": [91, 12],
                                "__position__Action": [93, 12],
                            }
                        ],
                        "__position__Statement": [89, 8],
                    },
                    "ManagedPolicyArns": [
                        "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
                    ],
                    "__position__RoleName": [87, 6],
                    "__position__AssumeRolePolicyDocument": [88, 6],
                    "__position__ManagedPolicyArns": [94, 6],
                },
                "__position__Type": [85, 4],
                "__value_positions__": [{"__position__AWS::IAM::Role": [85, 10]}],
                "__position__Properties": [86, 4],
            },
            "TaskRole": {
                "Type": "AWS::IAM::Role",
                "Properties": {
                    "RoleName": {
                        "Fn::Join": [
                            "",
                            [
                                {
                                    "Ref": "ServiceName",
                                    "__value_positions__": [
                                        {"__position__ServiceName": [100, 33]}
                                    ],
                                },
                                "TaskRole",
                            ],
                        ]
                    },
                    "AssumeRolePolicyDocument": {
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {
                                    "Service": "ecs-tasks.amazonaws.com",
                                    "__position__Service": [105, 14],
                                    "__value_positions__": [
                                        {
                                            "__position__ecs-tasks.amazonaws.com": [
                                                105,
                                                23,
                                            ]
                                        }
                                    ],
                                },
                                "Action": "sts:AssumeRole",
                                "__position__Effect": [103, 12],
                                "__value_positions__": [
                                    {"__position__Allow": [103, 20]},
                                    {"__position__sts:AssumeRole": [106, 20]},
                                ],
                                "__position__Principal": [104, 12],
                                "__position__Action": [106, 12],
                            }
                        ],
                        "__position__Statement": [102, 8],
                    },
                    "__position__RoleName": [100, 6],
                    "__position__AssumeRolePolicyDocument": [101, 6],
                },
                "__position__Type": [98, 4],
                "__value_positions__": [{"__position__AWS::IAM::Role": [98, 10]}],
                "__position__Properties": [99, 4],
            },
            "LogGroup": {
                "Type": "AWS::Logs::LogGroup",
                "Properties": {
                    "LogGroupName": {
                        "Fn::Join": [
                            "",
                            [
                                "/ecs/",
                                {
                                    "Ref": "ServiceName",
                                    "__value_positions__": [
                                        {"__position__ServiceName": [110, 44]}
                                    ],
                                },
                                "TaskDefinition",
                            ],
                        ]
                    },
                    "__position__LogGroupName": [110, 6],
                },
                "__position__Type": [108, 4],
                "__value_positions__": [{"__position__AWS::Logs::LogGroup": [108, 10]}],
                "__position__Properties": [109, 4],
            },
            "__position__LogGroup": [107, 2],
            "__position__TaskDefinition": [49, 2],
            "__position__ExecutionRole": [84, 2],
            "__position__TaskRole": [97, 2],
        },
        "__position__AWSTemplateFormatVersion": [0, 0],
        "__value_positions__": [
            {"__position__2010-09-09": [0, 26]},
            {"__position__An example CloudFormation template for Fargate.": [1, 13]},
        ],
        "__position__Description": [1, 0],
        "__position__Parameters": [2, 0],
        "__position__Resources": [48, 0],
    }


@pytest.mark.parametrize(
    "position",
    [
        Position(line=13, character=18),
        Position(line=20, character=13),
        Position(line=23, character=34),
    ],
)
def test_ref_extracts_correct_source_and_target_for_parameter(
    document_mapping, position
):
    result = resolve_ref(position, document_mapping)
    assert result.target_span.value == AWSRefName(value="DefaultVpcId")
    assert result.source_span.value.logical_name == "DefaultVpcId"


@pytest.mark.parametrize(
    "src_position,ref_position, expected",
    [
        (
            Position(
                line=97,
                character=2,
            ),
            Position(
                line=71,
                character=24,
            ),
            AWSLogicalId(logical_name="TaskRole", type_="AWS::IAM::Role"),
        ),
        (
            Position(
                line=84,
                character=2,
            ),
            Position(
                line=69,
                character=29,
            ),
            AWSLogicalId(logical_name="ExecutionRole", type_="AWS::IAM::Role"),
        ),
        (
            Position(
                line=107,
                character=2,
            ),
            Position(
                line=82,
                character=34,
            ),
            AWSLogicalId(logical_name="LogGroup", type_="AWS::Logs::LogGroup"),
        ),
    ],
)
def test_ref_extracts_correct_source_and_target_for_logical_id(
    document_mapping_with_logical_id_refs, src_position, ref_position, expected
):
    result = resolve_ref(ref_position, document_mapping_with_logical_id_refs)
    assert result.source_span.line == src_position.line
    assert result.source_span.char == src_position.character
    assert result.source_span.value == expected


def test_ref_extracts_nothing_when_position_not_at_ref(document_mapping):
    position = Position(line=13, character=31)
    result = resolve_ref(position, document_mapping)
    assert result is None
