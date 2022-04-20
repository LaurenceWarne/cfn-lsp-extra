"""
Tests for json_parsing
"""
import json

import pytest

from cfn_lsp_extra.decode.json_decoding import CfnJSONDecoder


@pytest.fixture
def json_string():
    return """{
    "AWSTemplateFormatVersion": "2010-09-09",
    "Resources": {
        "taskdefinition": {
            "Type": "AWS::ECS::TaskDefinition",
            "Properties": {
                "RequiresCompatibilities": [
                    "EC2"
                ],
                "ContainerDefinitions": [
                    {
                        "Name": "my-app",
                        "MountPoints": [
                            {
                                "SourceVolume": "my-vol",
                                "ContainerPath": "/var/www/my-vol"
                            }
                        ],
                        "Image": "amazon/amazon-ecs-sample",
                        "Cpu": 256,
                        "EntryPoint": [
                            "/usr/sbin/apache2",
                            "-D",
                            "FOREGROUND"
                        ],
                        "Memory": 512,
                        "Essential": true
                    },
                    {
                        "Name": "busybox",
                        "Image": "busybox",
                        "Cpu": 256,
                        "EntryPoint": [
                            "sh",
                            "-c"
                        ],
                        "Memory": 512,
                        "Command": [
                            "/bin/sh -c 'while true; do /bin/date > /var/www/my-vol/date; sleep 1; done'"
                        ],
                        "Essential": false,
                        "DependsOn": [
                            {
                                "ContainerName": "my-app",
                                "Condition": "START"
                            }
                        ],
                        "VolumesFrom": [
                            {
                                "SourceContainer": "my-app"
                            }
                        ]
                    }
                ],
                "Volumes": [
                    {
                        "Host": {
                            "SourcePath": "/var/lib/docker/vfs/dir/"
                        },
                        "Name": "my-vol"
                    }
                ]
            }
        }
    }
}"""


def test_parsing(json_string):
    content = json.loads(json_string, cls=CfnJSONDecoder)
    assert content["__position__AWSTemplateFormatVersion"] == [1, 5]
    assert content["__position__Resources"] == [2, 5]
    assert content["Resources"]["__position__taskdefinition"] == [3, 9]
