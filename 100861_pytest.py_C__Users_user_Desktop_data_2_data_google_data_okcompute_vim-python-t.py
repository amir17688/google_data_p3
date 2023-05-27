#!/usr/bin/env python
# encoding: utf-8


"""
Parse *pytest* error output and insert a formatted line this plugin understand
when an error is found. It works with py.test error and failure output. It also
parse python standard traceback.
"""

from __future__ import print_function

import os
import re
from itertools import (
    chain,
)
from platform import system

from . import (
    make_error_format,
    match_pattern,
)
from .python import (
    parse_traceback,
)


COMMAND = "py.test --tb=short"
"""
Terminal command to start nosetests.
"""

if system().lower() == 'windows':
    COMMAND = "py.test.exe --tb=short"


def match_fixture_scope_mismatch(line):
    """
    Extract error description from a *pytest's* `ScopeMismatch` exception
    output.

    :param line: A string to pattern match against.

    :returns: A dictionary where the key `error` holds the error description. If
        not matched, the dictionary is empty.
    """
    return match_pattern(r"ScopeMismatch: (?P<error>.*)$", line).get('error')


def match_file_location(line):
    """
    Extract filename path and line number from a *pytest* formatted file
    location string.

    :param line: A string to pattern match against.

    :returns: A dictionary where the key `file_path` holds the file path and the
        key `line_no` the line number. If not matched, the dictionary is empty.
    """
    return match_pattern(r"(?P<file_path>\S+):(?P<line_no>\d+)(:| in)\s.*$", line)


def match_error(line):
    """
    Extract error description from *pytest* error description.

    :param line: A string to pattern match against.

    :returns: A dictionary where the key `error` holds the error description. If
        not matched, the dictionary is empty.
    """
    return match_pattern(r"E\s+(?P<error>.*)$", line).get('error')


match_failure = match_error
"""
Alias for `match_error`.
"""


def match_conftest_error(line):
    """
    Extract `ConftestImportFailure` error message from a string.

    :param line: A string to pattern match against.

    :returns: A dictionary where the key `file_path` holds the file path and the
        key `error` the error description. If not matched, the dictionary is
        empty.
    """
    return match_pattern(
        r"^E\s+.*ConftestImportFailure: "
        "\(local\('(?P<file_path>.*)'\), \((?P<error>.*)\)\)$",
        line,
    )


def match_fixture_not_found_file_location(line):
    """
    Extract filename path and line number from 'fixture not found' error report.

    :param line: A string to pattern match against.

    :returns: A dictionary where the key `file_path` holds the file path and the
        key `line_no` the line number. If not matched, the dictionary is empty.
    """
    return match_pattern(
        r'file (?P<file_path>.*), line (?P<line_no>.*)$',
        line,
    )


def match_fixture_not_found_error(line):
    """
    Extract `fixture xxxx not found` error message from a string.

    :param line: A string to pattern match against.

    :returns: A dictionary where the key `error` holds the error description.
    """
    return match_pattern(r"^\s+(?P<error>fixture '.*' not found)$", line)


def parse_fixture_error(root_dir, lines):
    """
    Parse *pytest* output of a *fixture error* section.

    :param root_dir: Tested project root directory
    :param lines: List of lines from a pytest error report.

    :returns: *pytest* output augmented with specially formatted lines adapted
        to this plugin errorformat which will populate Vim clist.
    """
    result = []
    file_location = None
    stderr_call = re.compile("-{2,} Captured stderr setup -{2,}")

    lines_ = iter(lines)
    for line in lines_:
        result.append(line)
        # File location  can come first if the fixture error is a 'fixture not
        # found' error type.
        location = match_fixture_not_found_file_location(line)
        if location:
            file_location = location
            continue
        location = match_file_location(line)
        if location:
            file_location = location
            continue
        error = match_fixture_not_found_error(line)
        if error:
            result.append(
                make_error_format(
                    file_location.get('file_path', ""),
                    file_location.get('line_no', ""),
                    error['error'],
                ),
            )
            break
        error = match_fixture_scope_mismatch(line)
        if error:
            line = next(lines_)
            result.append(line)
            location = match_file_location(line)
            if location:
                file_path = location['file_path']
                if root_dir:
                    file_path = os.path.join(root_dir, file_path)
                result.append(
                    make_error_format(
                        file_path,
                        location['line_no'],
                        error,
                    ),
                )
            break
        if stderr_call.match(line):
            result.extend(parse_traceback(lines_))
            break

    # Consume left over prior returning
    result.extend(lines_)
    return result


def parse_conftest_error(lines):
    """
    Parse conftest import error (`ConftestImportFailure`) coming from an error
    report.

    :param lines: List of lines from a pytest error report.

    :returns: The original lines augmented with an additional error *marker*.
    """
    result = []
    lines_ = iter(lines)
    for line in lines_:
        result.append(line)
        # File location  can come first if the fixture error is a 'fixture not
        # found' error type.
        error = match_conftest_error(line)
        if error:
            result.append(
                make_error_format(
                    error.get('file_path', ""),
                    1,
                    error['error'],
                ),
            )
            break
    result.extend(lines_)
    return result


def parse_test_error(lines):
    """
    Parse test error coming from an error report.

    :param lines: List of lines from a pytest error report.

    :returns: The original lines augmented with an additional error *marker*.
    """
    result = []
    lines_ = iter(lines)
    location = {'file_path': '', 'line_no': 1}
    for line in lines_:
        result.append(line)
        failure = match_error(line)
        if failure and location['file_path']:
            result.append(
                make_error_format(
                    location['file_path'],
                    location['line_no'],
                    failure,
                ),
            )
            break
        else:
            file_location = match_file_location(line)
            if file_location:
                location = file_location
    result.extend(lines_)
    return result


def parse_error(root_dir, lines):
    """
    Parse an error coming from a pytest error report.

    :param lines: List of lines from a pytest error report.

    :returns: The original lines augmented with an additional error *marker*.
    """
    FIXTURE_ERROR = re.compile("_{2,} ERROR at setup of .{2,}")
    CONFTEST_IMPORT_ERROR = re.compile("_{2,} ERROR collecting _{2,}")

    if FIXTURE_ERROR.match(lines[0]):
        result = parse_fixture_error(root_dir, lines)
    elif CONFTEST_IMPORT_ERROR.match(lines[0]):
        result = parse_conftest_error(lines)
    else:
        result = parse_test_error(lines)

    if len(lines) == len(result):
        result.append(
            make_error_format(
                'Unknown',
                'Unknown',
                "An error was found but could not be parsed. This is probably "
                "a missing error pattern. Please post an issue on GitHub.",
            ),
        )

    return result


def parse_failure(lines):
    """
    Parse a failure coming from a pytest failure report.

    :param lines: List of lines from a pytest failure report.

    :returns: The original lines augmented with an additional error *marker*.
    """
    lines_ = iter(lines)
    result = [next(lines_)]
    location = {'file_path': 'Unknown', 'line_no': 'Unknown'}
    stderr_call = re.compile("-{2,} Captured stderr call -{2,}")

    for line in lines_:
        result.append(line)
        failure = match_failure(line)
        if failure and location['file_path'] != 'Unknown':
            result.append(
                make_error_format(
                    location['file_path'],
                    location['line_no'],
                    failure,
                ),
            )
            break
        else:
            file_location = match_file_location(line)
            if file_location:
                location = file_location

    for line in lines_:
        result.append(line)
        if stderr_call.match(line):
            result.extend(parse_traceback(lines_))
            break

    result.extend(lines_)
    if len(lines) == len(result):
        # Nothing was found! This is probably because of
        result.append(
            make_error_format(
                location['file_path'],
                location['line_no'],
                "An error was found but could not be parsed. This is probably "
                "a missing error pattern. Please post an issue on GitHub.",
            ),
        )

    return result


def parse_session_failure(lines):
    """
    Parse the output when *pytest* failed to start a session. One or more
    traceback block are displayed. Last traceback error is formatted to the
    plugin errorformat.

    :param lines: list of *pytest* error output lines.

    :returns: *pytest* output augmented with specially formatted lines adapted to
        this plugin errorformat which will populate Vim clist.
    """
    def get_traceback(lines):
        """ Iterates  on traceback block found in lines.  """
        traceback = []
        for line in lines:
            traceback.append(line)
            if line == '':
                yield traceback
                traceback = []
        yield traceback

    tracebacks = list(get_traceback(lines))

    # Note: It is possible for a session failure to output a sequence of
    # tracebacks. In all scenarios, parse only the last one because it is the
    # error origin.
    last_traceback = iter(tracebacks[-1])

    return list(
        chain(
            chain(*tracebacks[:-1]),
            parse_traceback(last_traceback),
            last_traceback,  # Note: `parse_traceback` may have not fully consumed the iterator
        ),
    )


def group_lines(lines, delimiter):
    """
    Group a list of lines into sub-lists. The list is split at line matching the
    `delimiter` pattern.

    :param lines: Lines of string.
    :parma delimiter: Regex matching the delimiting line pattern.

    :returns: A list of lists.
    """
    if not lines:
        return []
    lines_ = iter(lines)
    delimiter_ = re.compile(delimiter)
    result = []
    result.append([next(lines_)])
    for line in lines_:
        if delimiter_.match(line):
            result.append([])
        result[-1].append(line)
    return result


def parse_sections(lines):
    """
    Parse pytest output and group lines per section (Errors, failures,
    summary,etc.).

    :param lines: pytest output segmented in lines

    :returns: A dictionary where keys are section names and values are the
        grouped line for the section.
    """
    section_types = {
        'session': re.compile(r"={2,} test session starts ={2,}"),
        'errors': re.compile(r"={2,} ERRORS ={2,}"),
        'failures': re.compile(r"={2,} FAILURES ={2,}"),
        'summary': re.compile(r"={2,} .* failed in .* seconds ={2,}"),
    }
    sections = {}
    for lines in group_lines(lines, r"={2,} .* ={2,}"):
        for section_type, regex in section_types.iteritems():
            if regex.match(lines[0]):
                sections[section_type] = lines
                break
    return sections


def parse_errors(root_dir, lines):
    """
    Parse and add special markers to all error found in the `ERRORS` section.

    :param root_dir: This is the test root dir found in the pytest report.
    :param lines: All reported output lines from the `ERRORS` section.

    :returns: The original input list augmented with special markers where
        errors were found
    """
    result = [lines.pop(0)]
    for error in group_lines(lines, r"_{2,} (?<!Captured stder call).* _{2,}"):
        result.extend(parse_error(root_dir, error))
    return result


def parse_failures(lines):
    """
    Parse and add special markers to all failures found in the `FAILURES`
    section.

    :param root_dir: This is the test root dir found in the pytest report.
    :param lines: All reported output lines from the `FAILURES` section.

    :returns: The original input list augmented with special markers where
        errors were found
    """
    result = [lines.pop(0)]
    for failure in group_lines(lines, r"_{2,} (?<!Captured stder call).* _{2,}"):
        result.extend(parse_failure(failure))
    return result


def parse_session(lines):
    """
    Parse the pytest `session` section to extract the `root dir` of the test
    session.

    :param lines: All reported output lines from the `test session start`
        section.

    :returns: The test session root path.
    """
    session = re.compile(r"={2,} test session starts ={2,}")

    if not session.match(lines[0]):
        return None

    m = re.match(r"rootdir: (?P<root>.*), inifile: (?P<ini>.*)$", lines[2])
    if not m:
        return None
    return m.group('root')


def parse(lines):
    """
    Parse the pytest report.

    :param lines: List of lines from the pytest report

    :returns: The input lines augmented with special error markers the *Vim*
        plugin will understand through a custom `errorformat` setting.
    """
    sections = parse_sections(lines)

    if 'session' not in sections:
        return parse_session_failure(lines)

    result = sections['session']
    root_dir = parse_session(sections['session'])

    # Errors
    if 'errors' in sections:
        result.extend(parse_errors(root_dir, sections['errors']))

    # Failures
    if 'failures' in sections:
        result.extend(parse_failures(sections['failures']))

    # Summary
    if 'summary' in sections:
        result.extend(sections['summary'])

    return result
