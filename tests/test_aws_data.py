import pytest
from cfn_lsp_extra.aws_data import AWSContext, AWSContextMap, AWSResourceName
from cfn_lsp_extra.context import load_cfn_context


@pytest.fixture
def aws_resource_string():
    return "AWS::EC2::CapacityReservation"


@pytest.fixture
def aws_property_string():
    return "AvailabilityZone"


@pytest.fixture
def aws_context_dct(aws_resource_string, aws_property_string):
    return {
        "resources": {
            aws_resource_string: {
                "name": "AWS::EC2::CapacityReservation",
                "description": """Creates a new Capacity Reservation with the specified attributes. For more information, see Capacity Reservations in the Amazon EC2 User Guide.""",
                "properties": {
                    aws_property_string: {
                        "description": """`AvailabilityZone`\nThe Availability Zone in which to create the Capacity Reservation\\ """,
                        "required": False,
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
def aws_context_map(aws_context_dct):
    return AWSContextMap(resources=aws_context_dct["resources"])


@pytest.fixture
def nested_aws_context_map(nested_aws_context_dct):
    return AWSContextMap(resources=nested_aws_context_dct["resources"])


@pytest.fixture
def aws_context(aws_context_map):
    return AWSContext(resource_map=aws_context_map)


@pytest.fixture
def full_aws_context():
    return load_cfn_context()


@pytest.fixture
def nested_aws_context(nested_aws_context_map):
    return AWSContext(resource_map=nested_aws_context_map)


def test_aws_property_split():
    property_name = (
        AWSResourceName(value="AWS::EC2::CapacityReservation") / "AvailabilityZone"
    )
    assert property_name.split() == [
        "AWS::EC2::CapacityReservation",
        "AvailabilityZone",
    ]


def test_aws_context_getitem_for_resource(aws_context, aws_resource_string):
    resource_name = AWSResourceName(value=aws_resource_string)
    assert (
        aws_context[resource_name]
        == aws_context.resource_map.resources[resource_name.value]
    )


def test_aws_context_getitem_for_property(
    aws_resource_string, aws_property_string, aws_context
):
    property_name = AWSResourceName(value=aws_resource_string) / aws_property_string
    assert (
        aws_context[property_name]
        == aws_context.resource_map.resources[property_name.parent.value]["properties"][
            property_name.property_
        ]
    )


def test_aws_context_getitem_errors_for_bad_type(aws_context):
    with pytest.raises(KeyError):
        aws_context["resource_name"]


def test_aws_context_description_for_resource(aws_resource_string, aws_context):
    resource_name = AWSResourceName(value=aws_resource_string)
    assert (
        aws_context.description(resource_name)
        == aws_context.resource_map.resources[resource_name.value]["description"]
    )


def test_aws_context_description_for_property(
    aws_resource_string, aws_property_string, aws_context
):
    property_name = AWSResourceName(value=aws_resource_string) / aws_property_string
    assert (
        aws_context.description(property_name)
        == aws_context.resource_map.resources[property_name.parent.value]["properties"][
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
        == nested_aws_context.resource_map.resources[property_name.parent.parent.value][
            "properties"
        ][property_name.parent.property_]["properties"][property_name.property_][
            "description"
        ]
    )


def test_aws_context_description_errors_for_bad_type(aws_context):
    with pytest.raises(KeyError):
        aws_context.description("resource_name")


def test_aws_context_same_level_for_property(aws_resource_string, aws_context):
    resource_name = AWSResourceName(value=aws_resource_string)
    assert aws_context.same_level(resource_name / "AvailabilityZone") == [
        resource_name / "AvailabilityZone"
    ]


def test_aws_context_same_level_for_resource(aws_resource_string, aws_context):
    resource_name = AWSResourceName(value=aws_resource_string)
    assert aws_context.same_level(resource_name) == [resource_name]


def test_aws_context_same_level_nested_property(nested_aws_context):
    property_name = (
        AWSResourceName(value="AWS::ACMPCA::Certificate")
        / "ApiPassthrough"
        / "Extensions"
    )
    assert nested_aws_context.same_level(property_name) == [property_name]


def test_aws_context_contains(aws_context, aws_resource_string, aws_property_string):
    resource_name = AWSResourceName(value=aws_resource_string)
    property_name = resource_name / aws_property_string
    assert resource_name in aws_context
    assert property_name in aws_context


def test_aws_context_contains_negative(aws_context, aws_resource_string):
    resource_name = AWSResourceName(value=aws_resource_string)
    assert AWSResourceName(value="notaresource") not in aws_context
    assert resource_name / "notaproperty" not in aws_context
