import pytest

from cfn_lsp_extra.aws_data import AWSContext
from cfn_lsp_extra.aws_data import AWSResourceName
from cfn_lsp_extra.aws_data import OverridingKeyNotInContextException


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
def nested_aws_context_dct():
    return {
        "resources": {
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
    }


@pytest.fixture
def aws_context(aws_context_dct):
    return AWSContext(resources=aws_context_dct["resources"])


@pytest.fixture
def nested_aws_context(nested_aws_context_dct):
    return AWSContext(resources=nested_aws_context_dct["resources"])


def test_aws_property_split():
    property_name = (
        AWSResourceName(value="AWS::EC2::CapacityReservation") / "AvailabilityZone"
    )
    assert property_name.split() == [
        "AWS::EC2::CapacityReservation",
        "AvailabilityZone",
    ]


def test_aws_context_getitem_for_resource(aws_context):
    resource_name = AWSResourceName(value="AWS::EC2::CapacityReservation")
    assert aws_context[resource_name] == aws_context.resources[resource_name.value]


def test_aws_context_getitem_for_property(aws_context):
    property_name = (
        AWSResourceName(value="AWS::EC2::CapacityReservation") / "AvailabilityZone"
    )
    assert (
        aws_context[property_name]
        == aws_context.resources[property_name.parent.value]["properties"][
            property_name.property_
        ]
    )


def test_aws_context_getitem_errors_for_bad_type(aws_context):
    with pytest.raises(ValueError):
        aws_context["resource_name"]


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


def test_aws_context_description_for_nested_property(nested_aws_context):
    property_name = (
        AWSResourceName(value="AWS::ACMPCA::Certificate")
        / "ApiPassthrough"
        / "Extensions"
    )
    assert (
        nested_aws_context.description(property_name)
        == nested_aws_context.resources[property_name.parent.parent.value][
            "properties"
        ][property_name.parent.property_]["properties"][property_name.property_][
            "description"
        ]
    )


def test_aws_context_description_errors_for_bad_type(aws_context):
    with pytest.raises(ValueError):
        aws_context.description("resource_name")


def test_aws_context_same_level_for_property(aws_context):
    resource_name = AWSResourceName(value="AWS::EC2::CapacityReservation")
    assert aws_context.same_level(resource_name / "AvailabilityZone") == [
        "AvailabilityZone"
    ]


def test_aws_context_same_level_for_resource(aws_context):
    resource_name = AWSResourceName(value="AWS::EC2::CapacityReservation")
    assert aws_context.same_level(resource_name) == ["AWS::EC2::CapacityReservation"]


def test_aws_context_same_level_nested_property(nested_aws_context):
    property_name = (
        AWSResourceName(value="AWS::ACMPCA::Certificate")
        / "ApiPassthrough"
        / "Extensions"
    )
    assert nested_aws_context.same_level(property_name) == ["Extensions"]


def test_aws_update(aws_context):
    new_name = "foobar"
    new_ctx = AWSContext(
        resources={"AWS::EC2::CapacityReservation": {"name": new_name}}
    )
    aws_context.update(new_ctx)
    assert aws_context["AWS::EC2::CapacityReservation"]["name"] == new_name


def test_aws_update_nested(nested_aws_context):
    new_description = "foobar"
    new_ctx = AWSContext(
        resources={
            "AWS::ACMPCA::Certificate": {
                "properties": {
                    "ApiPassthrough": {
                        "properties": {"Extensions": {"description": new_description}},
                    }
                },
            }
        }
    )
    nested_aws_context.update(new_ctx)
    assert (
        nested_aws_context["AWS::ACMPCA::Certificate"]["properties"]["ApiPassthrough"][
            "properties"
        ]["Extensions"]["description"]
        == new_description
    )


def test_aws_update_errors_if_key_not_in_ctx(aws_context):
    bad_key = "notakey"
    new_ctx = AWSContext(
        resources={"AWS::EC2::CapacityReservation": {bad_key: "new_name"}}
    )
    with pytest.raises(OverridingKeyNotInContextException) as e:
        aws_context.update(new_ctx)
    assert e.value.path == f"resources/AWS::EC2::CapacityReservation/{bad_key}"


def test_aws_update_no_errors_if_key_not_in_ctx(aws_context):
    new_ctx = AWSContext(
        resources={"AWS::EC2::CapacityReservation": {"notakey": "new_name"}}
    )
    aws_context.update(new_ctx, error_if_new=False)
