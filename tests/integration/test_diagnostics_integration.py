"""
Integration tests for textDocument/definition.
"""

import pytest
from lsprotocol.types import (
    TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS,
    DidOpenTextDocumentParams,
    TextDocumentItem,
)
from pytest_lsp import LanguageClient

from .conftest import root_path

# See
# https://docs.pytest.org/en/latest/example/markers.html#marking-whole-classes-or-modules
pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    "file_name,diagnostics",
    [
        ("template.yaml", ["'OriginAccessIdentity' dependency already enforced by a 'GetAtt' at 'Resources/WebBucketPolicy/Properties/PolicyDocument/Statement/0/Principal/CanonicalUser'", "'OriginAccessIdentity' dependency already enforced by a 'Ref' at 'Resources/Distribution/Properties/DistributionConfig/Origins/0/S3OriginConfig/OriginAccessIdentity/Fn::Join/1/2'", "'Suspe' is not one of ['Enabled', 'Suspended']", "'AccessControl' is a legacy property. Consider using 'AWS::S3::BucketPolicy' instead", "A bucket with 'AccessControl' set should also have at least one 'OwnershipControl' configured", "'Type' is a required property", "None is not of type 'string'", "'A' is not one of ['Arn', 'RoleId'] in ['us-east-1']"]),
        ("template.json", ["'OriginAccessIdentity' dependency already enforced by a 'GetAtt' at 'Resources/WebBucketPolicy/Properties/PolicyDocument/Statement/0/Principal/CanonicalUser'", "'OriginAccessIdentity' dependency already enforced by a 'Ref' at 'Resources/Distribution/Properties/DistributionConfig/Origins/0/S3OriginConfig/OriginAccessIdentity/Fn::Join/1/2'", "'Suspend' is not one of ['Enabled', 'Suspended']", "'AccessControl' is a legacy property. Consider using 'AWS::S3::BucketPolicy' instead", "A bucket with 'AccessControl' set should also have at least one 'OwnershipControl' configured", "Resource type '' does not exist in 'us-east-1'"]),
    ],
)
@pytest.mark.asyncio
async def test_diagnostics(client: LanguageClient, file_name, diagnostics):
    uri = str(root_path / file_name)
    with open(uri, "r") as f:
        text = f.read()

    client.text_document_did_open(
        DidOpenTextDocumentParams(
            text_document=TextDocumentItem(
            uri=uri,
            language_id="cloudformation",
            version=1,
            text=text,
        )
        )
    )

    await client.wait_for_notification(TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)

    assert uri in client.diagnostics

    diags = [m.message for m in client.diagnostics[uri]]
    assert diags == diagnostics
