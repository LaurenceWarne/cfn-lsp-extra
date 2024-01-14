# Changelog

## v0.5.1
- [a378823](https://github.com/LaurenceWarne/cfn-lsp-extra/commit/a378823c127b76abbf81bcf3d8ca6bfe5bf01fef) Fix for configuration error with Neovim (https://github.com/LaurenceWarne/cfn-lsp-extra/issues/7).

## v0.5.0
- [9e5416c](https://github.com/LaurenceWarne/cfn-lsp-extra/commit/9e5416cb282547d0bb428e525b80619286c74c98) `textDocument/definition` for `!GetAtt`s.
- [6826623](https://github.com/LaurenceWarne/cfn-lsp-extra/commit/682662354d52252716b3cba943fb77b527039a39) Completions for enum property values.
- [b10f249](https://github.com/LaurenceWarne/cfn-lsp-extra/commit/b10f249a72e49b0b240c21f11a63a440ba58be44) Support `textDocument/hover` for `!GetAtts`

## v0.4.4
- [#5](https://github.com/LaurenceWarne/cfn-lsp-extra/pull/5) Respect `cfn-lint` config if it exists, thanks to [@mbarneyjr](https://github.com/mbarneyjr)
- [445a824](https://github.com/LaurenceWarne/cfn-lsp-extra/commit/445a8248cd03b87c5292a361a6b17fc446cb797c) Fix for [#4](https://github.com/LaurenceWarne/cfn-lsp-extra/issues/4) - error with Python 3.11

## v0.4.3
- [fbc8a90](https://github.com/LaurenceWarne/cfn-lsp-extra/commit/fbc8a906621bf7dfd2a52f3f8df1519f24c779a0) Fix for [#3](https://github.com/LaurenceWarne/cfn-lsp-extra/issues/3) - SAM templates being treated as Cloudformation templates by `cfn-lint`.

## v0.4.2
- [f7e4198](https://github.com/LaurenceWarne/cfn-lsp-extra/commit/f7e4198044b5c23601a1cb33cfa3ab4afe27be05) Use `us-east-1` by default for all diagnostics so diagnostics are not duplicated in some circumstances
- [91b217f](https://github.com/LaurenceWarne/cfn-lsp-extra/commit/91b217ffdbf8a3afd7411510e7f6e55f371fb395) Partial support for `!GetAtt` completions

## v0.4.1
- [b5ffc84](https://github.com/LaurenceWarne/cfn-lsp-extra/commit/b5ffc8411eb258bfa051b026070e59c7b2092cc3) SAM template Support
- [8e80c6d](https://github.com/LaurenceWarne/cfn-lsp-extra/commit/8e80c6daa0aaf41e717b3619c01c14c62138a194) Fix warning and informational diagnostics shown as warnings

## v0.3.1
- [ed0de4a](https://github.com/LaurenceWarne/cfn-lsp-extra/commit/ed0de4a73be454c382786e0af744d5f3262a9de2)/[e57e9f1](https://github.com/LaurenceWarne/cfn-lsp-extra/commit/ed0de4a73be454c382786e0af744d5f3262a9de2) Switch to using `TextEdits` for `CompletionItems`

## v0.3.0
- [0f0155e](https://github.com/LaurenceWarne/cfn-lsp-extra/commit/0f0155ed9f7867ab18260722e983314590bf9a2c) Support `textDocument/completion` for refs
- [7394fc3](https://github.com/LaurenceWarne/cfn-lsp-extra/commit/7394fc399fa85b7baf431644184e98cb4739dac6)/[9aa81e0](https://github.com/LaurenceWarne/cfn-lsp-extra/commit/9aa81e07ce24a3e3781cda5aef66ad22339fe177) Support `textDocument/hover` for refs
- [6a9be31](https://github.com/LaurenceWarne/cfn-lsp-extra/commit/6a9be317f7594b623c03b272012c52917c1efbe3)/[7394fc3](https://github.com/LaurenceWarne/cfn-lsp-extra/commit/7394fc399fa85b7baf431644184e98cb4739dac6) Support `textDocument/definition` for refs

## v0.2.0
- [3e7479f](https://github.com/LaurenceWarne/cfn-lsp-extra/commit/3e7479fbd0b447bdba6422afff6ddb53e4bb74b4) Support for snippet expansion (autogen of required properties) after resource completion 
- [98c060e](https://github.com/LaurenceWarne/cfn-lsp-extra/commit/98c060e12381dfd28da912c32f0cf5ba74a813c2) (Some) support for intrinsic function completions
- [261f1e7](https://github.com/LaurenceWarne/cfn-lsp-extra/commit/261f1e7018f854d14eb91b95b11eae83dc9b63d8) Hover support for JSON resources
