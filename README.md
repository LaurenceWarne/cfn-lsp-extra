# Cfn Lsp Extra

![Python Version](https://img.shields.io/pypi/pyversions/cfn-lsp-extra) [![Version](https://img.shields.io/github/v/tag/laurencewarne/cfn-lsp-extra?label=release)](CHANGELOG.md) [![codecov](https://codecov.io/gh/LaurenceWarne/cfn-lsp-extra/branch/master/graph/badge.svg?token=48ixiDIBpq)](https://codecov.io/gh/LaurenceWarne/cfn-lsp-extra)

An experimental cloudformation lsp server built on top of [cfn-lint](https://github.com/aws-cloudformation/cfn-lint) aiming to provide hovering, completion, etc.  YAML and JSON are supported, though YAML has more features currently implemented (for example snippets) and will give a better experience.  Trust me.

https://user-images.githubusercontent.com/17688577/166110762-71058f8f-4cb6-44ae-960b-9370a166125a.mp4

## Features

| Method                            | Status                                                                                                                 |
|-----------------------------------|------------------------------------------------------------------------------------------------------------------------|
| `textDocument/hover`              | Done for resources, resource properties, subproperties and parameter `!Ref`s. *TODO* all `!Ref`s, intrinsic functions. |
| `textDocument/completion`         | Done for resources, resource properties, subproperties and intrinsic functions. *TODO* `!Ref`s, `!GetAtt`.             |
| `textDocument/definition`         | Done for parameter `!Ref`s.  *TODO* resource `!Ref`s, mappings.                                                        |
| `textDocument/publishDiagnostics` | Done through `cfnlint`.                                                                                                |

## Installation

First install the executable, [`pipx`](https://pypa.github.io/pipx/) is recommended, but you can use `pip` instead if you like to live dangerously:

```bash
pipx install cfn-lsp-extra
```

Or get the bleeding edge from source:

```bash
pipx install git+https://github.com/laurencewarne/cfn-lsp-extra.git@$(git ls-remote git@github.com:laurencewarne/cfn-lsp-extra.git | head -1 | cut -f1)
```

Updating:

```bash
pipx upgrade cfn-lsp-extra
```

### Emacs

Install the [lsp-cfn.el](https://github.com/LaurenceWarne/lsp-cfn.el) package.

Patches detailing integration steps for other editors are very welcome 🙏

## Alternatives

### [vscode-cfn-lint](https://github.com/aws-cloudformation/cfn-lint-visual-studio-code)

### [cfn-lint](https://github.com/aws-cloudformation/cfn-lint)

Note this is used by `cfn-lsp-extra` under the hood to generate [diagnostics](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#diagnostic).  One difference with `cfn-lsp-extra` is that diagnostics will be refreshed every time you make a change to the document, in other words you don't need to save the file.
