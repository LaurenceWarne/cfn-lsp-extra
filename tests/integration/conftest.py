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


root_path = pathlib.Path(__file__).parent / "workspace"


# https://github.com/swyddfa/lsp-devtools/blob/develop/lib/pytest-lsp/README.md
@pytest_lsp.fixture(
    config=ClientServerConfig(
        server_command=["cfn-lsp-extra"],
    ),
)
async def client(lsp_client: LanguageClient):
    capabilities = client_capabilities("neovim")
    response = await lsp_client.initialize_session(
        InitializeParams(
            capabilities=capabilities,
            root_uri=uri.from_fs_path(str(root_path)),
        )
    )
    yield

    await lsp_client.shutdown_session()
