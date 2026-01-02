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
        ("template.yaml", {("'OriginAccessIdentity' dependency already enforced by a 'GetAtt' at 'Resources/WebBucketPolicy/Properties/PolicyDocument/Statement/0/Principal/CanonicalUser'", (55, 4), (55, 13)), ("'OriginAccessIdentity' dependency already enforced by a 'Ref' at 'Resources/Distribution/Properties/DistributionConfig/Origins/0/S3OriginConfig/OriginAccessIdentity/Fn::Join/1/2'", (74, 4), (74, 13)), ("'Suspe' is not one of ['Enabled', 'Suspended']", (135, 8), (135, 14)), ("'AccessControl' is a legacy property. Consider using 'AWS::S3::BucketPolicy' instead", (133, 6), (133, 19)), ("A bucket with 'AccessControl' set should also have at least one 'OwnershipControl' configured", (132, 4), (132, 14)), ("'Type' is a required property", (148, 2), (148, 20)), ("None is not of type 'string'", (149, 4), (149, 8)), ("'A' is not one of ['Arn', 'RoleId'] in ['us-east-1']", (172, 6), (172, 22))}),
        ("template.json", {("'OriginAccessIdentity' dependency already enforced by a 'GetAtt' at 'Resources/WebBucketPolicy/Properties/PolicyDocument/Statement/0/Principal/CanonicalUser'", (67, 12), (67, 23)), ("'OriginAccessIdentity' dependency already enforced by a 'Ref' at 'Resources/Distribution/Properties/DistributionConfig/Origins/0/S3OriginConfig/OriginAccessIdentity/Fn::Join/1/2'", (109, 12), (109, 23)), ("'Suspend' is not one of ['Enabled', 'Suspended']", (244, 20), (244, 28)), ("'AccessControl' is a legacy property. Consider using 'AWS::S3::BucketPolicy' instead", (242, 16), (242, 31)), ("A bucket with 'AccessControl' set should also have at least one 'OwnershipControl' configured", (241, 12), (241, 24)), ("Resource type '' does not exist in 'us-east-1'", (275, 12), (275, 18))
}),
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
    diags = [(m.message, (m.range.start.line, m.range.start.character), (m.range.end.line, m.range.end.character)) for m in client.diagnostics[uri]]
    assert set(diags) == diagnostics
