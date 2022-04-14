# type: ignore
# flake8: noqa
"""
LSP features leveraging cfnlint.
"""

from typing import Dict
from typing import List
from typing import no_type_check

import cfnlint.config
import cfnlint.core
import cfnlint.decode
import cfnlint.runner
from cfnlint.rules import ParseError
from cfnlint.rules import RulesCollection
from cfnlint.rules import TransformError
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pygls.lsp.types.basic_structures import Diagnostic
from pygls.lsp.types.basic_structures import DiagnosticSeverity


def diagnostics(yaml_content: str, file_path: str) -> List[Diagnostic]:
    """Return diagnostics for the template file at file_path."""
    conf, _, _ = cfnlint.core.get_args_filenames([])
    template, rules, errors = _get_template_rules(yaml_content, file_path, conf)

    if not errors:
        runner = cfnlint.runner.Runner(
            rules, file_path, template, regions=conf.regions, mandatory_rules=None
        )
        errors: List[cfnlint.rules.Match] = runner.run()

    severity_mapping: Dict[str, DiagnosticSeverity] = {
        "INFORMATIONAL": DiagnosticSeverity.Information,
        "ERROR": DiagnosticSeverity.Error,
        "WARNING": DiagnosticSeverity.Warning,
    }
    return [
        Diagnostic(
            range=Range(
                start=Position(line=m.linenumber - 1, character=m.columnnumber - 1),
                end=Position(line=m.linenumberend - 1, character=m.columnnumberend - 1),
            ),
            message=m.message,
            source="cfn-lsp-extra",
            severity=severity_mapping.get(m.rule.severity, DiagnosticSeverity.Error),
        )
        for m in errors
    ]


"""
We make alterations here to `cfnlint.core.get_template_rules` and
`cfnlint.decode.decode` so they work on (yaml) strings rather than files.
This is a bit

⣶⣶⣶⣦⠀⠀⠀⣰⣷⣦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣴⣾⣆⠀⠀⠀⣴⣶⣶⣶
⠛⠻⣿⣿⡀⠀⢠⣿⣿⠏⠀⠀⢀⠀⢤⣴⣆⠀⠀⠀⠹⣿⣿⡄⠀⢀⣿⣿⠟⠛
⠀⠀⢿⣿⣧⠀⢸⣿⡟⠀⠸⣿⡿⠄⠘⠋⠉⣠⣤⣄⠀⢻⣿⡇⠀⣼⣿⡿⠀⠀
⠀⠀⠸⣿⣿⡀⢸⣿⣇⠀⠀⠁⠀⠀⠀⠀⣠⣿⣿⠇⠀⣸⣿⡇⢀⣿⣿⠇⠀⠀
⠀⠀⠀⣿⣿⣇⣸⣿⣿⡀⠀⠀⠀⢀⣤⣾⣿⡿⠋⠀⢀⣿⣿⣇⣸⣿⣿⠀⠀⠀
⠀⠀⠀⠸⣿⣿⣿⣿⣿⣷⡀⠀⠀⠘⡿⠟⠋⠀⠀⢀⣾⣿⣿⣿⣿⣿⠇⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠻⡿⠋⠀⠀⠀⠀⠀⠀⠀⠀⠙⢿⠟⠀⠀⠀⠀⠀⠀⠀⠀

An alternative would be to create our own interpreter for the set of rules
from `cfnlint.core.get_rules`.
"""


def _get_template_rules(yaml_content, filename, args):
    """Get Template Configuration items and set them as default values"""

    ignore_bad_template = False
    if args.ignore_bad_template:
        ignore_bad_template = True
    else:
        # There is no collection at this point so we need to handle this
        # check directly
        if not ParseError().is_enabled(
            include_experimental=False,
            ignore_rules=args.ignore_checks,
            include_rules=args.include_checks,
            mandatory_rules=args.mandatory_checks,
        ):
            ignore_bad_template = True

    (template, errors) = _decode(yaml_content, filename)

    if errors:
        if len(errors) == 1 and ignore_bad_template and errors[0].rule.id == "E0000":
            return (template, [], [])
        return (template, [], errors)

    args.template_args = template

    rules = cfnlint.core.get_rules(
        args.append_rules,
        args.ignore_checks,
        args.include_checks,
        args.configure_rules,
        args.include_experimental,
        args.mandatory_checks,
        args.custom_rules,
    )

    return (template, rules, [])


import json

from cfnlint.decode import *


def _decode(yaml_content, filename):
    """
    Decode filename into an object
    """

    template = None
    matches = []
    try:
        template = cfnlint.decode.cfn_yaml.loads(yaml_content, filename)
    except IOError as e:
        if e.errno == 2:
            LOGGER.error("Template file not found: %s", filename)
            matches.append(
                create_match_file_error(
                    filename, "Template file not found: %s" % filename
                )
            )
        elif e.errno == 21:
            LOGGER.error("Template references a directory, not a file: %s", filename)
            matches.append(
                create_match_file_error(
                    filename,
                    "Template references a directory, not a file: %s" % filename,
                )
            )
        elif e.errno == 13:
            LOGGER.error("Permission denied when accessing template file: %s", filename)
            matches.append(
                create_match_file_error(
                    filename,
                    "Permission denied when accessing template file: %s" % filename,
                )
            )

        if matches:
            return (None, matches)
    except UnicodeDecodeError as err:
        LOGGER.error("Cannot read file contents: %s", filename)
        matches.append(
            create_match_file_error(
                filename, "Cannot read file contents: %s" % filename
            )
        )
    except cfn_yaml.CfnParseError as err:
        matches = err.matches
    except ParserError as err:
        matches = [create_match_yaml_parser_error(err, filename)]
    except ScannerError as err:
        if err.problem in [
            "found character '\\t' that cannot start any token",
            "found unknown escape character",
        ] or err.problem.startswith("found unknown escape character"):
            try:
                template = json.loads(yaml_content, cls=cfn_json.CfnJSONDecoder)
            except cfn_json.JSONDecodeError as json_err:
                for e in json_err.matches:
                    e.filename = filename
                matches = json_err.matches
            except JSONDecodeError as json_err:
                if hasattr(json_err, "message"):
                    if (
                        json_err.message == "No JSON object could be decoded"
                    ):  # pylint: disable=no-member
                        matches = [create_match_yaml_parser_error(err, filename)]
                    else:
                        matches = [create_match_json_parser_error(json_err, filename)]
                if hasattr(json_err, "msg"):
                    if json_err.msg == "Expecting value":  # pylint: disable=no-member
                        matches = [create_match_yaml_parser_error(err, filename)]
                    else:
                        matches = [create_match_json_parser_error(json_err, filename)]
            except Exception as json_err:  # pylint: disable=W0703
                LOGGER.error("Template %s is malformed: %s", filename, err.problem)
                LOGGER.error(
                    "Tried to parse %s as JSON but got error: %s",
                    filename,
                    str(json_err),
                )
                return (
                    None,
                    [
                        create_match_file_error(
                            filename,
                            "Tried to parse %s as JSON but got error: %s"
                            % (filename, str(json_err)),
                        )
                    ],
                )
        else:
            matches = [create_match_yaml_parser_error(err, filename)]
    except YAMLError as err:
        matches = [create_match_file_error(filename, err)]

    if not isinstance(template, dict) and not matches:
        # Template isn't a dict which means nearly nothing will work
        matches = [
            Match(
                1,
                1,
                1,
                1,
                filename,
                ParseError(),
                message="Template needs to be an object.",
            )
        ]
    return (template, matches)
