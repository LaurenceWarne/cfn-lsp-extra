"""
Integration tests for completions.
"""
import pytest


# See
# https://docs.pytest.org/en/latest/example/markers.html#marking-whole-classes-or-modules
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_property_completion(client):
    test_uri = client.root_uri + "/template.yaml"
    result = await client.completion_request(test_uri, line=57, character=6)

    labels = [c.label for c in result.items]
    assert "Bucket" in labels
    assert "PolicyDocument" in labels


@pytest.mark.asyncio
async def test_nested_property_completion(client):
    test_uri = client.root_uri + "/template.yaml"
    result = await client.completion_request(test_uri, line=51, character=8)

    labels = [c.label for c in result.items]
    assert "LogFilePrefix" in labels
    assert "DestinationBucketName" in labels
