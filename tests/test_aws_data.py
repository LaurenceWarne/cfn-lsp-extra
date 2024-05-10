import pytest
from cfn_lsp_extra.aws_data import AWSContext, AWSResourceName, AWSSpecification
from cfn_lsp_extra.context import load_cfn_context


@pytest.fixture
def aws_resource_string():
    return "AWS::EC2::CapacityReservation"


@pytest.fixture
def nested_aws_resource_string():
    return "AWS::ACMPCA::Certificate"


@pytest.fixture
def aws_property_string():
    return "AvailabilityZone"


@pytest.fixture
def aws_context_resource_dct(aws_resource_string, aws_property_string):
    return {
        aws_resource_string: {
            "MarkdownDocumentation": "`AWS::EC2::CapacityReservation`\nCreates a new Capacity Reservation with the specified attributes. For more information,\n see [Capacity\n Reservations](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-capacity-reservations.html) in the *Amazon EC2 User Guide*.\n\n",
            "RefReturnValue": "\n When you pass the logical ID of this resource to the intrinsic `Ref` function, `Ref` returns the resource ID, such as\n `cr-1234ab5cd6789e0f1`.\n\nFor more information about using the `Ref` function, see [`Ref`](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-ref.html).\n\n",
            "Documentation": "http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-ec2-capacityreservation.html",
            "Properties": {
                aws_property_string: {
                    "MarkdownDocumentation": "`AvailabilityZone`\n\nThe Availability Zone in which to create the Capacity Reservation.\n\n\n*Required*: Yes\n\n*Type*: String\n\n*Update requires*: [Replacement](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-update-behaviors.html#update-replacement)\n\n",
                    "RefReturnValue": "",
                    "Documentation": "http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-ec2-capacityreservation.html#cfn-ec2-capacityreservation-availabilityzone",
                    "UpdateType": "Immutable",
                    "Required": True,
                    "PrimitiveType": "String",
                }
            },
        }
    }


@pytest.fixture
def nested_aws_context_resource_dct(nested_aws_resource_string):
    return {
        nested_aws_resource_string: {
            "MarkdownDocumentation": "`AWS::ACMPCA::Certificate`\nThe `AWS::ACMPCA::Certificate` resource is used to issue a certificate\n using your private certificate authority. For more information, see the [IssueCertificate](https://docs.aws.amazon.com/privateca/latest/APIReference/API_IssueCertificate.html) action.\n\n",
            "RefReturnValue": "This reference should not be used in CloudFormation templates. Instead, use\n `AWS::ACMPCA::Certificate.Arn` to identify a certificate, and use\n `AWS::ACMPCA::Certificate.CertificateAuthorityArn` to identify a\n certificate authority.\n\n",
            "Documentation": "http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-acmpca-certificate.html",
            "Properties": {
                "ApiPassthrough": {
                    "MarkdownDocumentation": "`ApiPassthrough`\n\nSpecifies X.509 certificate information to be included in the issued certificate. An\n `APIPassthrough` or `APICSRPassthrough` template variant must\n be selected, or else this parameter is ignored.\n\n\n*Required*: No\n\n*Type*: [ApiPassthrough](./aws-properties-acmpca-certificate-apipassthrough.html)\n\n*Update requires*: [Replacement](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-update-behaviors.html#update-replacement)\n\n",
                    "RefReturnValue": "",
                    "Documentation": "http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-acmpca-certificate.html#cfn-acmpca-certificate-apipassthrough",
                    "UpdateType": "Immutable",
                    "Required": False,
                    "Type": "ApiPassthrough",
                }
            },
        }
    }


@pytest.fixture
def nested_aws_context_property_dct(aws_context_resource_dct):
    return {
        "AWS::ACMPCA::Certificate.ApiPassthrough": {
            "MarkdownDocumentation": "`AWS::ACMPCA::Certificate.ApiPassthrough`\n",
            "RefReturnValue": "",
            "Documentation": "http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-acmpca-certificate-apipassthrough.html",
            "Properties": {
                "Extensions": {
                    "MarkdownDocumentation": "",
                    "RefReturnValue": "",
                    "Documentation": "http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-acmpca-certificate-apipassthrough.html#cfn-acmpca-certificate-apipassthrough-extensions",
                    "UpdateType": "Immutable",
                    "Required": False,
                    "Type": "Extensions",
                },
                "Subject": {
                    "MarkdownDocumentation": "",
                    "RefReturnValue": "",
                    "Documentation": "http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-acmpca-certificate-apipassthrough.html#cfn-acmpca-certificate-apipassthrough-subject",
                    "UpdateType": "Immutable",
                    "Required": False,
                    "Type": "Subject",
                },
            },
        }
    }


@pytest.fixture
def aws_context(aws_context_resource_dct):
    return AWSContext(resource_map=aws_context_resource_dct, property_map={})


@pytest.fixture
def full_aws_context():
    return load_cfn_context()


@pytest.fixture
def nested_aws_context(
    nested_aws_context_resource_dct, nested_aws_context_property_dct
):
    return AWSContext(
        resource_map=nested_aws_context_resource_dct,
        property_map=nested_aws_context_property_dct,
    )


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
    assert aws_context[resource_name] == aws_context.resource_map[resource_name.value]


def test_aws_context_getitem_for_property(
    aws_resource_string, aws_property_string, aws_context
):
    property_name = AWSResourceName(value=aws_resource_string) / aws_property_string
    assert (
        aws_context[property_name]
        == aws_context.resource_map[property_name.parent.value][
            AWSSpecification.PROPERTIES
        ][property_name.property_]
    )


def test_aws_context_getitem_errors_for_bad_type(aws_context):
    with pytest.raises(KeyError):
        aws_context["resource_name"]


def test_aws_context_description_for_resource(aws_resource_string, aws_context):
    resource_name = AWSResourceName(value=aws_resource_string)
    assert (
        aws_context.description(resource_name)
        == aws_context.resource_map[resource_name.value][
            AWSSpecification.MARKDOWN_DOCUMENTATION
        ]
    )


def test_aws_context_description_for_property(
    aws_resource_string, aws_property_string, aws_context
):
    property_name = AWSResourceName(value=aws_resource_string) / aws_property_string
    assert (
        aws_context.description(property_name)
        == aws_context.resource_map[property_name.parent.value][
            AWSSpecification.PROPERTIES
        ][property_name.property_][AWSSpecification.MARKDOWN_DOCUMENTATION]
    )


def test_aws_context_description_for_nested_property(
    nested_aws_resource_string, nested_aws_context
):
    property_name = (
        AWSResourceName(value=nested_aws_resource_string)
        / "ApiPassthrough"
        / "Extensions"
    )
    assert (
        nested_aws_context.description(property_name)
        == nested_aws_context.property_map[
            f"{nested_aws_resource_string}.{property_name.parent.property_}"
        ][AWSSpecification.PROPERTIES][property_name.property_][
            AWSSpecification.MARKDOWN_DOCUMENTATION
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


def test_aws_context_same_level_nested_property(
    nested_aws_context,
    nested_aws_resource_string,
    nested_aws_context_resource_dct,
    nested_aws_context_property_dct,
):
    property_name = (
        AWSResourceName(value=nested_aws_resource_string)
        / "ApiPassthrough"
        / "Extensions"
    )
    key = f"{nested_aws_resource_string}.ApiPassthrough"
    assert [p.property_ for p in nested_aws_context.same_level(property_name)] == list(
        nested_aws_context_property_dct[key][AWSSpecification.PROPERTIES].keys()
    )


def test_aws_context_contains(aws_context, aws_resource_string, aws_property_string):
    resource_name = AWSResourceName(value=aws_resource_string)
    property_name = resource_name / aws_property_string
    assert resource_name in aws_context
    assert property_name in aws_context


def test_aws_context_contains_negative(aws_context, aws_resource_string):
    resource_name = AWSResourceName(value=aws_resource_string)
    assert AWSResourceName(value="notaresource") not in aws_context
    assert resource_name / "notaproperty" not in aws_context
