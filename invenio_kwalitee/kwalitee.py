# -*- coding: utf-8 -*-
##
## This file is part of Invenio-Kwalitee
## Copyright (C) 2014 CERN.
##
## Invenio-Kwalitee is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio-Kwalitee is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio-Kwalitee; if not, write to the Free Software Foundation,
## Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
##
## In applying this licence, CERN does not waive the privileges and immunities
## granted to it by virtue of its status as an Intergovernmental Organization
## or submit itself to any jurisdiction.

"""Kwalitee checks for PEP8, PEP257, PyFlakes and License."""

from __future__ import unicode_literals

import re
import pep8
import codecs
import pep257
import pyflakes
import pyflakes.checker
import tokenize
from datetime import datetime


# Max number of errors to be sent back
MAX = 130

_re_copyright_year = re.compile(r"^Copyright\s+(?:\([Cc]\)|\xa9)\s+"
                                r"(?:\d{4},\s+)*"
                                r"(?P<year>\d{4})\s+CERN\.?$",
                                re.UNICODE | re.MULTILINE)

_re_program = re.compile(r"^(?P<program>.*?) is free software;",
                         re.UNICODE | re.MULTILINE)
_re_program_2 = re.compile(r"^(?P<program>.*?) is distributed in",
                           re.UNICODE | re.MULTILINE)
_re_program_3 = re.compile(r"GNU General Public License\s+along\s+with "
                           r"(?P<program>.*?)[;\.]",
                           re.UNICODE | re.MULTILINE)

_messages_codes = {
    # Global
    "M100": "needs more reviewers",
    "M101": "signature is missing",
    "M102": "unrecognized bullet/signature",
    # First line
    "M110": "missing component name",
    "M111": "unrecognized component name: {0}",
    # Dots
    "M120": "missing empty line before bullet",
    "M121": "indentation of two spaces expected",
    # Signatures
    "M130": "no bullets are allowed after signatures",
    # Generic
    "M190": "line is too long ({1} > {0})",
    "M191": "must not end with a dot '.'",
}

_licenses_codes = {
    "I100": "license is missing",
    "I101": "copyright is missing",
    "I102": "copyright year is outdated, expected {0} but got {1}",
    "I103": "license is not GNU GPLv2",
}


def _check_1st_line(line, components, max_first_line=50, **kwargs):
    """First line check.

    Check that the first line has a known component name followed by a colon
    and then a short description of the commit.
    """
    errors = []
    lineno = 1
    if len(line) > max_first_line:
        errors.append(("M190", lineno, max_first_line, len(line)))

    if line.endswith("."):
        errors.append(("M191", lineno))

    if ':' not in line:
        errors.append(("M110", lineno))
    else:
        component, msg = line.split(':', 1)
        if component not in components:
            errors.append(("M111", lineno, component))

    return errors


def _check_bullets(lines, max_length=72, **kwargs):
    """Check that the bullet point list is well formatted.

    Each bullet point shall have one space before and after it. The bullet
    character is the "*" and there is no space before it but one after it
    meaning the next line are starting with two blanks spaces to respect the
    identation.
    """
    errors = []
    missed_lines = []
    skipped = []

    for (i, line) in enumerate(lines[1:]):
        if line.startswith('*'):
            if len(missed_lines) > 0:
                errors.append(("M130", i + 2))
            if lines[i].strip() != '':
                errors.append(("M120", i + 2))
            for (j, indented) in enumerate(lines[i + 2:]):
                if indented.strip() == '':
                    break
                if not re.search(r"^ {2}\S", indented):
                    errors.append(("M121", i + j + 3))
                else:
                    skipped.append(i + j + 1)
        elif i not in skipped and line.strip():
            missed_lines.append((i + 2, line))

        if len(line) > max_length:
            errors.append(("M190", i + 2, max_length, len(line)))

    return errors, missed_lines


def _check_signatures(lines, signatures, alt_signatures=None, trusted=None,
                      **kwargs):
    """Check that the signatures are valid.

    There should be at least three signatures. If not, one of them should be a
    trusted developer/reviewer.

    Formatting supported being: [signature] full name <email@address>

    :param lines: list of lines (lineno, content) to verify.
    :param signatures: list of supported signature, e.g. Signed-off-by
    :param alt_signatures: list of alternative signatures, not counted
    :param trusted: list of trusted reviewers, the e-mail address.
    :return: list of errors
    """
    matching = []
    errors = []
    trusted = trusted or []
    signatures = tuple(signatures) if signatures else []
    alt_signatures = tuple(alt_signatures) if alt_signatures else tuple()
    signatures += alt_signatures

    test_signatures = re.compile("^({0})".format("|".join(signatures)))
    test_alt_signatures = re.compile("^({0})".format("|".join(alt_signatures)))
    for i, line in lines:
        if signatures and test_signatures.search(line):
            if line.endswith("."):
                errors.append(("M191", i))
            if not alt_signatures or not test_alt_signatures.search(line):
                matching.append(line)
        else:
            errors.append(("M102", i))

    if len(matching) == 0:
        errors.append(("M101", 1))
        errors.append(("M100", 1))
    elif len(matching) <= 2:
        pattern = re.compile('|'.join(map(lambda x: '<' + re.escape(x) + '>',
                                          trusted)))
        trusted_matching = list(filter(None, map(pattern.search, matching)))
        if len(trusted_matching) == 0:
            errors.append(("M100", 1))

    return errors


def check_message(message, **kwargs):
    """Check the message format.

    Rules:
    * the first line must start by a component name
    * and a short description (52 chars),
    * then bullet points are expected
    * and finally signatures.

    Required kwargs:
    :param components: list of compontents, e.g. ('auth', 'utils', 'misc')
    :param signatures: list of signatrues, e.g. ('Signed-off-by',
                       'Reviewed-by')
    :param trusted: optional list of reviewers, e.g. ('john.doe@example.org',)
    :param max_length: optional maximum line length (by default 72)
    :param max_first_line: optional maximum first line length (by default 50)
    :param allow_empty: optional way to allow empty message (by default False)
    :return: list of errors found
    """
    if kwargs.pop("allow_empty", False):
        if not message or message.isspace():
            return []

    lines = re.split(r"\r\n|\r|\n", message)
    errors = _check_1st_line(lines[0], **kwargs)
    err, signature_lines = _check_bullets(lines, **kwargs)
    errors += err
    errors += _check_signatures(signature_lines, **kwargs)

    def _format(code, lineno, args):
        return "{0}: {1} {2}".format(lineno,
                                     code,
                                     _messages_codes[code].format(*args))

    errors.sort()
    return list(map(lambda x: _format(x[0], x[1], x[2:]), errors))


class _PyFlakesChecker(pyflakes.checker.Checker):

    """PEP8 compatible checker for pyFlakes (inspired by flake8)."""

    name = "pyflakes"
    version = pyflakes.__version__

    def run(self):
        """Yield the error messages."""
        for msg in self.messages:
            col = getattr(msg, 'col', 0)
            yield msg.lineno, col, (msg.tpl % msg.message_args), msg.__class__


def _register_pyflakes_check():
    """Register the pyFlakes checker into PEP8 set of checks."""
    # Resolving conflicts between pep8 and pyflakes.
    codes = {
        "UnusedImport": "F401",
        "ImportShadowedByLoopVar": "F402",
        "ImportStarUsed": "F403",
        "LateFutureImport": "F404",
        "Redefined": "F801",
        "RedefinedInListComp": "F812",
        "UndefinedName": "F821",
        "UndefinedExport": "F822",
        "UndefinedLocal": "F823",
        "DuplicateArgument": "F831",
        "UnusedVariable": "F841",
    }

    for name, obj in vars(pyflakes.messages).items():
        if name[0].isupper() and obj.message:
            obj.tpl = "{0} {1}".format(codes.get(name, "F999"), obj.message)

    pep8.register_check(_PyFlakesChecker, codes=['F'])
_registered_pyflakes_check = False


class _Report(pep8.BaseReport):

    """Custom reporter.

    It keeps a list of errors in a sortable list and never prints.
    """

    def __init__(self, options):
        super(_Report, self).__init__(options)
        self.errors = []

    def error(self, line_number, offset, text, check):
        code = super(_Report, self).error(line_number, offset, text, check)
        if code:
            self.errors.append((line_number, offset + 1, code, text, check))


def check_pep8(filename, **kwargs):
    """Perform static analysis on the given file.

    :param ignore: list of codes to ignore, e.g. ('E111', 'E123')
    :param select: list of codes to explicitly select.
    :param pyflakes: run the pyflakes checks too (default True)
    :return: list of errors
    """
    options = {
        "ignore": kwargs.get("ignore"),
        "select": kwargs.get("select"),
    }

    if not _registered_pyflakes_check and kwargs.get("pyflakes", True):
        _register_pyflakes_check()

    checker = pep8.Checker(filename, reporter=_Report, **options)
    checker.check_all()

    errors = []
    checker.report.errors.sort()
    for error in checker.report.errors:
        errors.append("{0}:{1}: {3}".format(*error))
    return errors


def check_pep257(filename, **kwargs):
    """Perform static analysis on the given file docstrings.

    :param ignore: list of codes to ignore, e.g. ('D400')
    :return: list of errors
    """
    ignore = kwargs.get("ignore")

    errors = []
    checker = pep257.PEP257Checker()
    with open(filename) as fp:
        try:
            for error in checker.check_source(fp.read(), filename):
                if ignore is None or error.code not in ignore:
                    # Removing the colon ':' after the error code
                    message = re.sub("(D[0-9]{3}): ?(.*)",
                                     r"\1 \2",
                                     error.message)
                    errors.append("{0}: {1}".format(error.line, message))
        except tokenize.TokenError as e:
            errors.append("{0}:{1}:{2}".format(e.args[0], *e.args[1]))
        except pep257.AllError as e:
            errors.append(str(e))

    return errors


def check_license(filename, **kwargs):
    """Perform a license check on the given file.

    The license format should be commented using ## and live at the top of the
    file. Also, the year should be the current one.

    Supported filetypes: python, jinja, javascript

    :param year: default current year
    :param ignore: list of codes to ignore, e.g. ('L100', 'L101')
    :param python_style: False for JavaScript or CSS files
    :return: list of errors
    """
    year = kwargs.pop("year", datetime.now().year)
    python_style = kwargs.pop("python_style", True)
    ignores = kwargs.get("ignore")
    template = "{0}: {1} {2}"

    if python_style:
        re_comment = re.compile(r"^#.*|\{#.*|[\r\n]+$")
        starter = "## "
    else:
        re_comment = re.compile(r"^/\*.*| \*.*|[\r\n]+$")
        starter = " *"

    errors = []
    lines = []
    file_is_empty = False
    license = ""
    lineno = 0
    with codecs.open(filename, "r", "utf-8") as fp:
        line = fp.readline()
        blocks = []
        while re_comment.match(line):
            if line.startswith(starter):
                line = line[len(starter):].lstrip()
                blocks.append(line)
                lines.append((lineno, line.strip()))
            lineno, line = lineno + 1, fp.readline()
        file_is_empty = line == ""
        license = "".join(blocks)

    if file_is_empty and not license.strip():
        return errors

    match_year = _re_copyright_year.search(license)
    if match_year is None:
        errors.append((lineno + 1, "I101"))
    elif int(match_year.group("year")) != year:
        theline = match_year.group(0)
        lno = lineno
        for no, l in lines:
            if theline.strip() == l:
                lno = no
                break
        errors.append((lno + 1, "I102", year, match_year.group("year")))
    else:
        program_match = _re_program.search(license)
        program_2_match = _re_program_2.search(license)
        program_3_match = _re_program_3.search(license)
        if program_match is None:
            errors.append((lineno, "I100"))
        elif (program_2_match is None or
              program_3_match is None or
              (program_match.group("program").upper() !=
               program_2_match.group("program").upper() !=
               program_3_match.group("program").upper())):
            errors.append((lineno, "I103"))

    def _format_error(lineno, code, *args):
        return template.format(lineno, code,
                               _licenses_codes[code].format(*args))

    def _filter_codes(error):
        if not ignores or error[1] not in ignores:
            return error

    return list(map(lambda x: _format_error(*x),
                    filter(_filter_codes, errors)))


def check_file(filename, **kwargs):
    """Perform static analysis on the given file.

    See: check_pep8 and check_license
    """
    errors = []
    if filename.endswith(".py"):
        if kwargs.get("pep8", True):
            errors += check_pep8(filename, **kwargs)
        if kwargs.get("pep257", True):
            errors += check_pep257(filename, **kwargs)
        if kwargs.get("license", True):
            errors += check_license(filename, **kwargs)
    elif filename.endswith(".html"):
        errors += check_license(filename, **kwargs)
    elif filename.endswith(".js") or filename.endswith(".css"):
        errors += check_license(filename, python_style=False, **kwargs)
    errors.sort()
    return errors


def get_options(config):
    """Build the options from the Flask config."""
    return {
        "components": config.get("COMPONENTS"),
        "signatures": config.get("SIGNATURES"),
        "alt_signatures": config.get("ALT_SIGNATURES"),
        "trusted": config.get("TRUSTED_DEVELOPERS"),
        "pep8": config.get("CHECK_PEP8", True),
        "pep257": config.get("CHECK_PEP257", True),
        "license": config.get("CHECK_LICENSE", True),
        "pyflakes": config.get("CHECK_PYFLAKES", True),
        "ignore": config.get("IGNORE"),
        "select": config.get("SELECT"),
        "match": config.get("PEP257_MATCH"),
        "match_dir": config.get("PEP257_MATCH_DIR")
    }
