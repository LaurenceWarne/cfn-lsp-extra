from cfn_lsp_extra.aws_data import AWSPropertyName
from cfn_lsp_extra.aws_data import AWSResourceName
from cfn_lsp_extra.completions import completions_for

from .test_aws_data import aws_context
from .test_aws_data import aws_context_dct
from .test_aws_data import aws_property_string
from .test_aws_data import aws_resource_string


def test_property_completions(aws_resource_string, aws_property_string, aws_context):
    result = completions_for(
        AWSPropertyName(
            parent=AWSResourceName(value=aws_resource_string),
            property_=aws_property_string,
        ),
        aws_context,
    )
    assert len(result.items) == 1
    assert result.items[0].label == aws_property_string


def test_resource_completions_start(
    aws_resource_string, aws_property_string, aws_context
):
    result = completions_for(
        AWSResourceName(value=aws_resource_string.split("::")[0]),
        aws_context,
    )
    assert len(result.items) == 1
    assert result.items[0].label == aws_resource_string.rsplit("::", 1)[0]


def test_resource_completions_end(
    aws_resource_string, aws_property_string, aws_context
):
    result = completions_for(
        AWSResourceName(value=aws_resource_string.rsplit("::", 1)[0]),
        aws_context,
    )
    assert len(result.items) == 1
    assert result.items[0].label == aws_resource_string
