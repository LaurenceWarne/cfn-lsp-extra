# Cfn Lsp Extra

[![Python Version](https://img.shields.io/pypi/pyversions/cfn-lsp-extra)][python version]

An experimental cloudformation lsp server.

## Usage

```bash
git clone https://github.com/LaurenceWarne/cfn-lsp-extra
cd cfn-lsp-extra
pipx install .
```

### Emacs

```elisp
;; After lsp-mode has been loaded
(when-let ((exe (executable-find "cfn-lsp-extra")))

  ;; Copied from https://www.emacswiki.org/emacs/CfnLint
  (define-derived-mode cfn-yaml-mode yaml-mode
    "CFN-YAML"
    "Simple mode to edit CloudFormation template in YAML format.")
  (add-to-list 'magic-mode-alist
               '("\\(---\n\\)?AWSTemplateFormatVersion:" . cfn-yaml-mode))

  (lsp-register-client
   (make-lsp-client :new-connection (lsp-stdio-connection exe)
                    :activation-fn (lsp-activate-on "cloudformation")
                    :server-id 'cfn-lsp-extra)))
```
