import nox

package = "cfn_lsp_extra"
python_versions = ["3.13", "3.12", "3.11", "3.10", "3.9", "3.8"]
nox.needs_version = ">= 2024.10.9"
nox.options.sessions = ("tests", "integration_tests", "lint", "mypy", "coverage")


@nox.session(python=python_versions)
def tests(session):
    session.run("poetry", "install", "--all-extras", external=True)
    session.run("pytest", "-s", *session.posargs)


@nox.session(name="integration-tests", python=python_versions)
def integration_tests(session):
    session.run("poetry", "install", "--all-extras", external=True)
    session.run("pytest", "--run-integration", "-s", *session.posargs)


@nox.session(python=python_versions)
def lint(session):
    session.run("poetry", "install", "--all-extras", external=True)
    session.run("ruff", "check", package)


@nox.session(python=python_versions)
def mypy(session):
    session.run("poetry", "install", "--all-extras", external=True)
    session.install(".")
    session.run("mypy", package)


@nox.session(python=python_versions)
def coverage(session):
    session.run("poetry", "install", "--all-extras", external=True)
    session.run("coverage", "run", "-m", "pytest")
    session.run("coverage", "xml")
