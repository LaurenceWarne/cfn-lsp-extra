"""
Tests for resource completions.
"""
import pytest

from cfn_lsp_extra.aws_data import AWSResourceName
from cfn_lsp_extra.completions.resources import resource_completions

from ..test_aws_data import aws_context
from ..test_aws_data import aws_context_dct
from ..test_aws_data import aws_context_map
from ..test_aws_data import aws_property_string
from ..test_aws_data import aws_resource_string
from .test_completions import document
from .test_completions import resource_position


def test_resource_completions_start(
    aws_context,
    document,
    resource_position,
    aws_resource_string,
):
    result = resource_completions(
        AWSResourceName(value=aws_resource_string),
        aws_context,
        document,
        resource_position,
    )
    assert len(result.items) == 1
    assert result.items[0].label == aws_resource_string


def test_resource_completions_end(
    aws_context,
    document,
    resource_position,
    aws_resource_string,
):
    result = resource_completions(
        AWSResourceName(value=aws_resource_string),
        aws_context,
        document,
        resource_position,
    )
    assert len(result.items) == 1
    assert result.items[0].label == aws_resource_string


def test_resource_completions_snippet_required(
    aws_context,
    document,
    resource_position,
    aws_resource_string,
    aws_property_string,
):
    aws_context.resource_map.resources[aws_resource_string]["properties"][
        aws_property_string
    ]["required"] = True
    result = resource_completions(
        AWSResourceName(value=aws_resource_string),
        aws_context,
        document,
        resource_position,
    )
    assert len(result.items) == 1
    assert f"{aws_property_string}: $1" in result.items[0].text_edit.new_text


def test_resource_completions_snippet_not_required(
    aws_context,
    document,
    resource_position,
    aws_resource_string,
    aws_property_string,
):
    result = resource_completions(
        AWSResourceName(value=aws_resource_string),
        aws_context,
        document,
        resource_position,
    )
    assert len(result.items) == 1
    assert f"{aws_property_string}: $1" not in result.items[0].text_edit.new_text
