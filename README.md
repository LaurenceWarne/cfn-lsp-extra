# Cfn Lsp Extra

![Python Version](https://img.shields.io/pypi/pyversions/cfn-lsp-extra) [![Version](https://img.shields.io/github/v/tag/laurencewarne/cfn-lsp-extra?label=release)](CHANGELOG.md)

An experimental cloudformation lsp server built on top of [cfn-lint](https://github.com/aws-cloudformation/cfn-lint) aiming to provide hovering, completion, etc.

https://user-images.githubusercontent.com/17688577/166110762-71058f8f-4cb6-44ae-960b-9370a166125a.mp4

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

You need to install an lsp client like [lsp-mode](https://github.com/emacs-lsp/lsp-mode) and register `cfn-lsp-extra`.  [yaml-mode](https://github.com/yoshiki/yaml-mode) is also highly recommended.

```elisp
;; After lsp-mode and yaml-mode have been loaded
(when-let ((exe (executable-find "cfn-lsp-extra")))

  ;; Copied from https://www.emacswiki.org/emacs/CfnLint
  (define-derived-mode cfn-json-mode js-mode
    "CFN-JSON"
    "Simple mode to edit CloudFormation template in JSON format."
  (setq js-indent-level 2))

  (add-to-list 'magic-mode-alist
               '("\\({\n *\\)? *[\"']AWSTemplateFormatVersion" . cfn-json-mode))
  (add-to-list 'lsp-language-id-configuration
               '(cfn-json-mode . "cloudformation"))
  (add-hook 'cfn-json-mode-hook #'lsp)
  
  (when (featurep 'yaml-mode)
    (define-derived-mode cfn-yaml-mode yaml-mode
      "CFN-YAML"
      "Simple mode to edit CloudFormation template in YAML format.")
    (add-to-list 'magic-mode-alist
                 '("\\(---\n\\)?AWSTemplateFormatVersion:" . cfn-yaml-mode))
    (add-to-list 'lsp-language-id-configuration
                 '(cfn-yaml-mode . "cloudformation"))
    (add-hook 'cfn-yaml-mode-hook #'lsp))
  
  (lsp-register-client
   (make-lsp-client :new-connection (lsp-stdio-connection exe)
                    :activation-fn (lsp-activate-on "cloudformation")
                    :server-id 'cfn-lsp-extra)))
```

Patches detailing integration steps for other editors are very welcome 🙏

## Alternatives

### [vscode-cfn-lint](https://github.com/aws-cloudformation/cfn-lint-visual-studio-code)

### [cfn-lint](https://github.com/aws-cloudformation/cfn-lint)

Note this is used by `cfn-lsp-extra` under the hood.

