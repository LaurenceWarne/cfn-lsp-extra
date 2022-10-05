# Cfn Lsp Extra

![Python Version](https://img.shields.io/pypi/pyversions/cfn-lsp-extra) [![PyPI](https://img.shields.io/pypi/v/cfn-lsp-extra)](CHANGELOG.md) [![codecov](https://codecov.io/gh/LaurenceWarne/cfn-lsp-extra/branch/master/graph/badge.svg?token=48ixiDIBpq)](https://codecov.io/gh/LaurenceWarne/cfn-lsp-extra)

An experimental cloudformation lsp server (with support for SAM templates) built on top of [cfn-lint](https://github.com/aws-cloudformation/cfn-lint) aiming to provide hovering, completion, etc.  YAML and JSON are supported, though YAML has more features currently implemented (for example snippets) and will give a better experience.  Trust me.

https://user-images.githubusercontent.com/17688577/176939586-df1d9ed8-5ec6-46d5-9f26-7222644047bd.mp4

## Features

| Method                            | Status                                                                                                               |
|-----------------------------------|----------------------------------------------------------------------------------------------------------------------|
| `textDocument/hover`              | Done for resources, resource properties, subproperties and `!Ref`s. *TODO* `!GetAtt`s, intrinsic functions.          |
| `textDocument/completion`         | Done for resources, resource properties, subproperties, refs, !GetAtts and intrinsic functions. *TODO* `Fn::GetAtt`. |
| `textDocument/definition`         | Done for `!Ref`s.  *TODO* mappings.                                                                                  |
| `textDocument/publishDiagnostics` | Done through `cfnlint`.                                                                                              |

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
        if vim.filetype.matchregex(line1, [[^AWSTemplateFormatVersion]] ) then
          return 'yaml.cloudformation'
        elseif vim.filetype.matchregex(line1, [[["']AWSTemplateFormatVersion]] ) or
		   vim.filetype.matchregex(line2, [[["']AWSTemplateFormatVersion]] ) then
          return 'json.cloudformation'
        end
      end,
    },
  },
}
```

Then you can use [LanguageClient-neovim](https://github.com/autozimu/LanguageClient-neovim) to start the server on those file types:

```vim
let g:LanguageClient_serverCommands = {
    \ 'yaml.cloudformation': ['~/.local/bin/cfn-lsp-extra'],
    \ 'json.cloudformation': ['~/.local/bin/cfn-lsp-extra']
    \ }
```


Patches documenting integration for other editors are very welcome!

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
