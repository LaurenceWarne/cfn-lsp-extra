import pytest

from cfn_lsp_extra.aws_data import AWSContext
from cfn_lsp_extra.aws_data import AWSResourceName


@pytest.fixture
def aws_context_dct():
    return {
        "resources": {
            "AWS::EC2::CapacityReservation": {
                "name": "AWS::EC2::CapacityReservation",
                "description": """Creates a new Capacity Reservation with the specified attributes. For more information, see Capacity Reservations in the Amazon EC2 User Guide.""",
                "properties": {
                    "AvailabilityZone": {
                        "description": """`AvailabilityZone`\nThe Availability Zone in which to create the Capacity Reservation\\ """,
                        "properties": {},
                    }
                },
            }
        }
    }


@pytest.fixture
def aws_context(aws_context_dct):
    return AWSContext(resources=aws_context_dct["resources"])


def test_aws_context_description_for_resource(aws_context):
    resource_name = AWSResourceName(value="AWS::EC2::CapacityReservation")
    assert (
        aws_context.description(resource_name)
        == aws_context.resources[resource_name.value]["description"]
    )


def test_aws_context_description_for_property(aws_context):
    property_name = (
        AWSResourceName(value="AWS::EC2::CapacityReservation") / "AvailabilityZone"
    )
    assert (
        aws_context.description(property_name)
        == aws_context.resources[property_name.parent.value]["properties"][
            property_name.property_
        ]["description"]
    )


def test_aws_context_description_for_nested_property():
    aws_context = AWSContext(
        resources={
            "AWS::ACMPCA::Certificate": {
                "description": (
                    "# AWS::ACMPCA::Certificate\n\nThe `AWS::ACMPCA::Certificate`"
                ),
                "properties": {
                    "ApiPassthrough": {
                        "description": (
                            "# AWS::ACMPCA::Certificate/ApiPassthrough\n\nContains"
                        ),
                        "properties": {
                            "Extensions": {
                                "description": (
                                    "# AWS::ACMPCA::Certificate/ApiPassthrough/Extensions\n\nContains"
                                ),
                                "properties": {},
                            }
                        },
                    }
                },
            }
        }
    )

    property_name = (
        AWSResourceName(value="AWS::ACMPCA::Certificate")
        / "ApiPassthrough"
        / "Extensions"
    )
    assert (
        aws_context.description(property_name)
        == aws_context.resources[property_name.parent.parent.value]["properties"][
            property_name.parent.property_
        ]["properties"][property_name.property_]["description"]
    )
