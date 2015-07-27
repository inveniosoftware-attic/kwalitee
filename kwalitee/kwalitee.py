# -*- coding: utf-8 -*-
#
# This file is part of kwalitee
# Copyright (C) 2014, 2015 CERN.
#
# kwalitee is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# kwalitee is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kwalitee; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
#
# In applying this licence, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

"""Kwalitee checks for PEP8, PEP257, PyFlakes and License."""

from __future__ import unicode_literals

import codecs
import os
import re
import tokenize

from datetime import datetime

import pep257

import pep8

import pyflakes
import pyflakes.checker


SUPPORTED_FILES = '.py', '.html', '.tpl', '.js', '.jsx', '.css', '.less'
"""Supported file types."""

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

_re_bullet_label = re.compile(r"^\* (?P<label>[A-Z]{1,70}) ", re.UNICODE)

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
    "M122": "unrecognized bullet label: {0}",
    # Signatures
    "M130": "no bullets are allowed after signatures",
    # Generic
    "M190": "line is too long ({1} > {0})",
    "M191": "must not end with a dot '.'",
}

_licenses_codes = {
    "L100": "license is missing",
    "L101": "copyright is missing",
    "L102": "copyright year is outdated, expected {0} but got {1}",
    "L103": "license is not GNU GPLv2",
    "L190": "file cannot be decoded as {0}"
}


def _check_1st_line(line, **kwargs):
    """First line check.

    Check that the first line has a known component name followed by a colon
    and then a short description of the commit.

    :param line: first line
    :type line: str
    :param components: list of known component names
    :type line: list
    :param max_first_line: maximum length of the first line
    :type max_first_line: int
    :return: errors as in (code, line number, *args)
    :rtype: list

    """
    components = kwargs.get("components", ())
    max_first_line = kwargs.get("max_first_line", 50)

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


def _check_bullets(lines, **kwargs):
    """Check that the bullet point list is well formatted.

    Each bullet point shall have one space before and after it. The bullet
    character is the "*" and there is no space before it but one after it
    meaning the next line are starting with two blanks spaces to respect the
    indentation.

    :param lines: all the lines of the message
    :type lines: list
    :param max_lengths: maximum length of any line. (Default 72)
    :return: errors as in (code, line number, *args)
    :rtype: list

    """
    max_length = kwargs.get("max_length", 72)
    labels = {l for l, _ in kwargs.get("commit_msg_labels", tuple())}

    errors = []
    missed_lines = []
    skipped = []

    for (i, line) in enumerate(lines[1:]):
        if line.startswith('*'):
            if len(missed_lines) > 0:
                errors.append(("M130", i + 2))
            if lines[i].strip() != '':
                errors.append(("M120", i + 2))

            label = _re_bullet_label.search(line)
            if label and label.group('label') not in labels:
                errors.append(("M122", i + 2, label.group('label')))

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


def _check_signatures(lines, **kwargs):
    """Check that the signatures are valid.

    There should be at least three signatures. If not, one of them should be a
    trusted developer/reviewer.

    Formatting supported being: [signature] full name <email@address>

    :param lines: lines (lineno, content) to verify.
    :type lines: list
    :param signatures: list of supported signature
    :type signatures: list
    :param alt_signatures: list of alternative signatures, not counted
    :type alt_signatures: list
    :param trusted: list of trusted reviewers, the e-mail address.
    :type trusted: list
    :param min_reviewers: minimal number of reviewers needed. (Default 3)
    :type min_reviewers: int
    :return: errors as in (code, line number, *args)
    :rtype: list

    """
    trusted = kwargs.get("trusted", ())
    signatures = tuple(kwargs.get("signatures", ()))
    alt_signatures = tuple(kwargs.get("alt_signatures", ()))
    min_reviewers = kwargs.get("min_reviewers", 3)

    matching = []
    errors = []
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

    if not matching:
        errors.append(("M101", 1))
        errors.append(("M100", 1))
    elif len(matching) < min_reviewers:
        pattern = re.compile('|'.join(map(lambda x: '<' + re.escape(x) + '>',
                                          trusted)))
        trusted_matching = list(filter(None, map(pattern.search, matching)))
        if len(trusted_matching) == 0:
            errors.append(("M100", 1))

    return errors


def check_message(message, **kwargs):
    """Check the message format.

    Rules:

    - the first line must start by a component name
    - and a short description (52 chars),
    - then bullet points are expected
    - and finally signatures.

    :param components: compontents, e.g. ``('auth', 'utils', 'misc')``
    :type components: `list`
    :param signatures: signatures, e.g. ``('Signed-off-by', 'Reviewed-by')``
    :type signatures: `list`
    :param alt_signatures: alternative signatures, e.g. ``('Tested-by',)``
    :type alt_signatures: `list`
    :param trusted: optional list of reviewers, e.g. ``('john.doe@foo.org',)``
    :type trusted: `list`
    :param max_length: optional maximum line length (by default: 72)
    :type max_length: int
    :param max_first_line: optional maximum first line length (by default: 50)
    :type max_first_line: int
    :param allow_empty: optional way to allow empty message (by default: False)
    :type allow_empty: bool
    :return: errors sorted by line number
    :rtype: `list`
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

    return list(map(lambda x: _format(x[0], x[1], x[2:]),
                    sorted(errors, key=lambda x: x[0])))


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
    from flake8_import_order.flake8_linter import Linter
    from flake8_blind_except import check_blind_except

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
    # FIXME parser hack
    parser = pep8.get_parser('', '')
    Linter.add_options(parser)
    options, args = parser.parse_args([])
    Linter.parse_options(options)
    # end of hack
    pep8.register_check(Linter, codes=['I'])
    pep8.register_check(check_blind_except, codes=['B90'])
_registered_pyflakes_check = False


class _Report(pep8.BaseReport):

    """Custom reporter.

    It keeps a list of errors in a sortable list and never prints.
    """

    def __init__(self, options):
        """Initialize the reporter."""
        super(_Report, self).__init__(options)
        self.errors = []

    def error(self, line_number, offset, text, check):
        """Run the checks and collect the errors."""
        code = super(_Report, self).error(line_number, offset, text, check)
        if code:
            self.errors.append((line_number, offset + 1, code, text, check))


def is_file_excluded(filename, excludes):
    """Check if the file should be excluded.

    :param filename: file name
    :param excludes: list of regex to match
    :return: True if the file should be excluded
    """
    # check if you need to exclude this file
    return any([exclude and re.match(exclude, filename) is not None
                for exclude in excludes])


def check_pep8(filename, **kwargs):
    """Perform static analysis on the given file.

    :param filename: path of file to check.
    :type filename: str
    :param ignore: codes to ignore, e.g. ``('E111', 'E123')``
    :type ignore: `list`
    :param select: codes to explicitly select.
    :type select: `list`
    :param pyflakes: run the pyflakes checks too (default ``True``)
    :type pyflakes: bool
    :return: errors
    :rtype: `list`

    .. seealso:: :py:class:`pep8.Checker`

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
    for error in sorted(checker.report.errors, key=lambda x: x[0]):
        errors.append("{0}:{1}: {3}".format(*error))
    return errors


def check_pep257(filename, **kwargs):
    """Perform static analysis on the given file docstrings.

    :param filename: path of file to check.
    :type filename: str
    :param ignore: codes to ignore, e.g. ('D400',)
    :type ignore: `list`
    :param match: regex the filename has to match to be checked
    :type match: str
    :param match_dir: regex everydir in path should match to be checked
    :type match_dir: str
    :return: errors
    :rtype: `list`

    .. seealso:: `GreenSteam/pep257 <https://github.com/GreenSteam/pep257/>`_

    """
    ignore = kwargs.get("ignore")
    match = kwargs.get("match", None)
    match_dir = kwargs.get("match_dir", None)

    errors = []

    if match and not re.match(match, os.path.basename(filename)):
        return errors

    if match_dir:
        # FIXME here the full path is checked, be sure, if match_dir doesn't
        # match the path (usually temporary) before the actual application path
        # it may not run the checks when it should have.
        path = os.path.split(os.path.abspath(filename))[0]
        while path != "/":
            path, dirname = os.path.split(path)
            if not re.match(match_dir, dirname):
                return errors

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
            errors.append("{1}:{2} {0}".format(e.args[0], *e.args[1]))
        except pep257.AllError as e:
            errors.append(str(e))

    return errors


def check_license(filename, **kwargs):
    """Perform a license check on the given file.

    The license format should be commented using # and live at the top of the
    file. Also, the year should be the current one.

    :param filename: path of file to check.
    :type filename: str
    :param year: default current year
    :type year: int
    :param ignore: codes to ignore, e.g. ``('L100', 'L101')``
    :type ignore: `list`
    :param python_style: False for JavaScript or CSS files
    :type python_style: bool
    :return: errors
    :rtype: `list`

    """
    year = kwargs.pop("year", datetime.now().year)
    python_style = kwargs.pop("python_style", True)
    ignores = kwargs.get("ignore")
    template = "{0}: {1} {2}"

    if python_style:
        re_comment = re.compile(r"^#.*|\{#.*|[\r\n]+$")
        starter = "# "
    else:
        re_comment = re.compile(r"^/\*.*| \*.*|[\r\n]+$")
        starter = " *"

    errors = []
    lines = []
    file_is_empty = False
    license = ""
    lineno = 0
    try:
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
    except UnicodeDecodeError:
        errors.append((lineno + 1, "L190", "utf-8"))
        license = ""

    if file_is_empty and not license.strip():
        return errors

    match_year = _re_copyright_year.search(license)
    if match_year is None:
        errors.append((lineno + 1, "L101"))
    elif int(match_year.group("year")) != year:
        theline = match_year.group(0)
        lno = lineno
        for no, l in lines:
            if theline.strip() == l:
                lno = no
                break
        errors.append((lno + 1, "L102", year, match_year.group("year")))
    else:
        program_match = _re_program.search(license)
        program_2_match = _re_program_2.search(license)
        program_3_match = _re_program_3.search(license)
        if program_match is None:
            errors.append((lineno, "L100"))
        elif (program_2_match is None or
              program_3_match is None or
              (program_match.group("program").upper() !=
               program_2_match.group("program").upper() !=
               program_3_match.group("program").upper())):
            errors.append((lineno, "L103"))

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

    .. seealso::

        - :data:`.SUPPORTED_FILES`
        - :func:`.check_pep8`
        - :func:`.check_pep257`
        - and :func:`.check_license`

    :param filename: path of file to check.
    :type filename: str
    :return: errors sorted by line number or None if file is excluded
    :rtype: `list`

    """
    excludes = kwargs.get("excludes", [])
    errors = []

    if is_file_excluded(filename, excludes):
        return None

    if filename.endswith(".py"):
        if kwargs.get("pep8", True):
            errors += check_pep8(filename, **kwargs)
        if kwargs.get("pep257", True):
            errors += check_pep257(filename, **kwargs)
        if kwargs.get("license", True):
            errors += check_license(filename, **kwargs)
    elif re.search("\.(tpl|html)$", filename):
        errors += check_license(filename, **kwargs)
    elif re.search("\.(js|jsx|css|less)$", filename):
        errors += check_license(filename, python_style=False, **kwargs)

    def try_to_int(value):
        try:
            return int(value.split(':', 1)[0])
        except ValueError:
            return 0

    return sorted(errors, key=try_to_int)


def get_options(config):
    """Build the options from the Flask config."""
    base = {
        "components": config.get("COMPONENTS"),
        "signatures": config.get("SIGNATURES"),
        "commit_msg_template": config.get("COMMIT_MSG_TEMPLATE"),
        "commit_msg_labels": config.get("COMMIT_MSG_LABELS"),
        "alt_signatures": config.get("ALT_SIGNATURES"),
        "trusted": config.get("TRUSTED_DEVELOPERS"),
        "pep8": config.get("CHECK_PEP8", True),
        "pep257": config.get("CHECK_PEP257", True),
        "license": config.get("CHECK_LICENSE", True),
        "pyflakes": config.get("CHECK_PYFLAKES", True),
        "ignore": config.get("IGNORE"),
        "select": config.get("SELECT"),
        "match": config.get("PEP257_MATCH"),
        "match_dir": config.get("PEP257_MATCH_DIR"),
        "min_reviewers": config.get("MIN_REVIEWERS"),
        "colors": config.get("COLORS", True),
        "excludes": config.get("EXCLUDES", [])
    }
    options = {}
    for k, v in base.items():
        if v is not None:
            options[k] = v
    return options
