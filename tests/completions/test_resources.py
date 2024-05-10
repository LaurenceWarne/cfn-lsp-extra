"""
Tests for resource completions.
"""
import pytest
from cfn_lsp_extra.aws_data import AWSResourceName, AWSSpecification
from cfn_lsp_extra.completions.resources import resource_completions

from ..test_aws_data import (
    aws_context,
    aws_context_resource_dct,
    aws_property_string,
    aws_resource_string,
)
from .test_completions import document, resource_position


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
    aws_context.resource_map[aws_resource_string][AWSSpecification.PROPERTIES][
        aws_property_string
    ][AWSSpecification.REQUIRED] = True
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
    aws_context.resource_map[aws_resource_string][AWSSpecification.PROPERTIES][
        aws_property_string
    ][AWSSpecification.REQUIRED] = False
    result = resource_completions(
        AWSResourceName(value=aws_resource_string),
        aws_context,
        document,
        resource_position,
    )
    assert len(result.items) == 1
    assert f"{aws_property_string}: $1" not in result.items[0].text_edit.new_text
