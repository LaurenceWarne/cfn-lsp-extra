from cfn_lsp_extra.aws_data import AWSContext
from cfn_lsp_extra.server import server


def test_create_server():
    lsp_server = server(AWSContext(resource_map=dict()))
