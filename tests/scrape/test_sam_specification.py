import json
import pathlib
import urllib.request
from pprint import pprint

import pytest
from cfn_lsp_extra.scrape.sam_specification import DEFAULT_SPEC_URL, run


@pytest.mark.skip(reason="Very slow")
def test_to_aws_context():
    p = pathlib.Path("/tmp/sam-schema.json")
    doc_dir = pathlib.Path("/tmp/sam-doc-dir")
    try:
        doc_dir.mkdir()
    except FileExistsError as e:
        pass
    if not p.exists():
        with urllib.request.urlopen(to_aws_context) as f:
            p.write_text(f.read().decode("utf-8"))

    content = json.loads(p.read_text("utf-8"))
    pprint(run(p, doc_dir, None))
