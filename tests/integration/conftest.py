import asyncio
import pathlib
import sys

import pygls.uris as uri
import pytest
import pytest_lsp
from lsprotocol.types import CompletionParams
from lsprotocol.types import InitializeParams
from lsprotocol.types import Position
from lsprotocol.types import TextDocumentIdentifier
from pytest_lsp import ClientServerConfig
from pytest_lsp import LanguageClient
from pytest_lsp import client_capabilities
from pytest_lsp import make_test_client


root_path = pathlib.Path(__file__).parent / "workspace"


@pytest.fixture(scope="session")
def event_loop():
    # We need to redefine the event_loop fixture to match the scope of our
    # client_server fixture.
    #
    # https://github.com/pytest-dev/pytest-asyncio/issues/68#issuecomment-334083751

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_lsp.fixture(
    config=ClientServerConfig(
        server_command=["cfn-lsp-extra"],
    ),
)
async def client(lsp_client: LanguageClient):
    # Setup
    response = await lsp_client.initialize_session(
        InitializeParams(
            capabilities=client_capabilities("neovim"),
            root_uri=uri.from_fs_path(str(root_path)),
        )
    )

    yield

    # Teardown
    await lsp_client.shutdown_session()
