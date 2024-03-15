# Cfn Lsp Extra

![Python Version](https://img.shields.io/pypi/pyversions/cfn-lsp-extra) [![PyPI](https://img.shields.io/pypi/v/cfn-lsp-extra)](CHANGELOG.md) [![codecov](https://codecov.io/gh/LaurenceWarne/cfn-lsp-extra/branch/master/graph/badge.svg?token=48ixiDIBpq)](https://codecov.io/gh/LaurenceWarne/cfn-lsp-extra)

An experimental cloudformation language server (with support for SAM templates) built on top of [cfn-lint](https://github.com/aws-cloudformation/cfn-lint) and the [Cloudformation user guide](https://github.com/awsdocs/aws-cloudformation-user-guide), aiming to provide hovering, completion, etc.  YAML and JSON are supported, though YAML has more features currently implemented (for example snippets) and will give a better experience.  Trust me.

https://user-images.githubusercontent.com/17688577/176939586-df1d9ed8-5ec6-46d5-9f26-7222644047bd.mp4

## Features

| Method                            | Status                                                                                                                                                             |
|-----------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `textDocument/hover`              | Done for resources (in particular, required properties for a resource will be auto-expanded), resource properties, subproperties, `!Ref`s and intrinsic functions. |
| `textDocument/completion`         | Done for resources, resource properties, subproperties, property values (for enums), refs, !GetAtts and intrinsic functions. *TODO* `Fn::GetAtt`.                  |
| `textDocument/definition`         | Done for `!Ref`s and `!GetAtt`s.  *TODO* mappings.                                                                                                                 |
| `textDocument/publishDiagnostics` | Done through `cfnlint`.                                                                                                                                            |

Also checkout the [changelog](/CHANGELOG.md).

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

### Neovim

Make sure you're running at least `0.8`, then add the following in `~/.config/nvim/filetype.lua`:

```lua
vim.filetype.add {
  pattern = {
    ['.*'] = {
      priority = math.huge,
      function(path, bufnr)
        local line1 = vim.filetype.getlines(bufnr, 1)
        local line2 = vim.filetype.getlines(bufnr, 2)
        if vim.filetype.matchregex(line1, [[^AWSTemplateFormatVersion]] ) or
           vim.filetype.matchregex(line1, [[AWS::Serverless-2016-10-31]] ) then
          return 'yaml.cloudformation'
        elseif vim.filetype.matchregex(line1, [[["']AWSTemplateFormatVersion]] ) or
           vim.filetype.matchregex(line2, [[["']AWSTemplateFormatVersion]] ) or
           vim.filetype.matchregex(line1, [[AWS::Serverless-2016-10-31]] ) or
           vim.filetype.matchregex(line2, [[AWS::Serverless-2016-10-31]] ) then
          return 'json.cloudformation'
        end
      end,
    },
  },
}
```

Then you can use one of:

1. Neovim's [built-in LSP client](https://neovim.io/doc/user/lsp.html):

```lua
require('lspconfig.configs').cfn_lsp = {
  default_config = {
    cmd = { os.getenv("HOME") .. '/.local/bin/cfn-lsp-extra' },
    filetypes = { 'yaml.cloudformation', 'json.cloudformation' },
    root_dir = function(fname)
      return require('lspconfig').util.find_git_ancestor(fname) or vim.fn.getcwd()
    end,
    settings = {
      documentFormatting = false,
    },
  },
}
require('lspconfig').cfn_lsp.setup{}
```

2. [LanguageClient-neovim](https://github.com/autozimu/LanguageClient-neovim):

```vim
let g:LanguageClient_serverCommands = {
    \ 'yaml.cloudformation': ['~/.local/bin/cfn-lsp-extra'],
    \ 'json.cloudformation': ['~/.local/bin/cfn-lsp-extra']
    \ }
```

Patches documenting integration for other editors are very welcome!

## Development

`cfn-lsp-extra` uses [nox](https://github.com/wntrblm/nox) for virtualenv management and [poetry](https://github.com/python-poetry/poetry) for dependency management.  You can install both of them using:

```bash
pipx install nox
pipx install poetry
```

And then run tests, linting, etc (switching `3.9` for whichever Python version):

```bash
nox --session tests-3.9              # unit tests
nox --session integration-tests-3.9  # integration tests
nox --session lint-3.9               # flake8 lints
nox --session mypy-3.9               # mypy checks
```

## Alternatives

### [vscode-cfn-lint](https://github.com/aws-cloudformation/cfn-lint-visual-studio-code)

### [cfn-lint](https://github.com/aws-cloudformation/cfn-lint)

Note this is used by `cfn-lsp-extra` under the hood to generate [diagnostics](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#diagnostic).  One difference with `cfn-lsp-extra` is that diagnostics will be refreshed every time you make a change to the document, in other words you don't need to save the file.

### [yamlls](https://github.com/redhat-developer/yaml-language-server)

You can use `yamlls` in conjunction with the Cloudformation schema at https://www.schemastore.org/json/ as an alternative.  For Emacs, `lsp-mode` can install `yamlls` for you, from there you could do something like:

```elisp
(defun my-yamlls-cloudformation-setup ()
  ;; There's also one for serverless
  (lsp-yaml-set-buffer-schema "https://raw.githubusercontent.com/awslabs/goformation/master/schema/cloudformation.schema.json")
  (setq-local
   lsp-yaml-custom-tags
   ["!And"
    "!Base64"
    "!Cidr"
    "!Equals"
    "!FindInMap sequence"
    "!GetAZs"
    "!GetAtt"
    "!If"
    "!ImportValue"
    "!Join sequence"
    "!Not"
    "!Or"
    "!Ref Scalar"
    "!Ref"
    "!Select"
    "!Split"
    "!Sub"
    "!fn"]))

;; Using the mode defined by https://www.emacswiki.org/emacs/CfnLint
(add-hook 'cfn-yaml-mode-hook #'my-yamlls-cloudformation-setup)
(add-hook 'cfn-yaml-mode-hook #'lsp-deferred)
```

This will give you completions (and some support for value completions?), though no hover documentation.
