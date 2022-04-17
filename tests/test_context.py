import json

import pytest
from pytest_mock import mocker

from cfn_lsp_extra.context import cache


@pytest.fixture
def aws_context():
    return {
        "resources": {
            "AWS::EC2::CapacityReservation": {
                "name": "AWS::EC2::CapacityReservation",
                "description": """Creates a new Capacity Reservation with the specified attributes. For more information, see Capacity Reservations in the Amazon EC2 User Guide.""",
                "property_descriptions": {
                    "AvailabilityZone": """`AvailabilityZone`\nThe Availability Zone in which to create the Capacity Reservation\\ """
                },
            }
        }
    }


@pytest.fixture
def aws_context_str(aws_context):
    return str(aws_context)


@pytest.fixture
def mocker_cache_file(mocker, aws_context, aws_context_str):
    cache_file = mocker.MagicMock(__open__=aws_context_str, exists=True)
    mocker.patch("json.load", lambda f: aws_context)
    return cache_file


def test_cache_reads_file(mocker, mocker_cache_file, aws_context):
    result = cache(mocker_cache_file, False)
    assert result == aws_context
