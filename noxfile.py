import nox
from nox_poetry import session


package = "cfn_lsp_extra"
python_versions = ["3.10", "3.9", "3.8", "3.7"]
nox.needs_version = ">= 2021.6.6"
nox.options.sessions = ("tests",)


@session(python=python_versions)
def tests(session):
    session.install("pytest", ".")
    session.install("pytest-asyncio", ".")
    session.run("pytest")