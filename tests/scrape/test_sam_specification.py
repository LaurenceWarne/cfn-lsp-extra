import json
import pathlib
import urllib.request

import pytest
from cfn_lsp_extra.scrape.sam_specification import to_aws_context


def test_to_aws_context():
    p = pathlib.Path("/tmp/sam-schema.json")
    if not p.exists():
        with urllib.request.urlopen(
            "https://raw.githubusercontent.com/awslabs/goformation/master/schema/sam.schema.json"
        ) as f:
            p.write_text(f.read().decode("utf-8"))

    content = json.loads(p.read_text("utf-8"))
    from pprint import pprint

    pprint(to_aws_context(content, "/"))
