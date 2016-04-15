#!/usr/bin/env python

import re
import commands

def getGITDiffLines():
    cmd = "git diff --cached"
    output = commands.getstatusoutput(cmd)
    if output[0] is 0:
        return output[1].split('\n')
    else:
        return None

def attactCPPDiffLines():
    diff_lines = getGITDiffLines()
    cpp_changes = {}
    line_number = 0
    for line in diff_lines:
        line_number += 1
        pattern = r'^\+{3} b/(.*\.(\w*))'
        pattern_matched = re.search(pattern, line)
        if pattern_matched is not None:
            filename, suffix = pattern_matched.group(1), pattern_matched.group(2)
            new_lines = list()
            if suffix in ['h', 'hpp', 'cc', 'cpp']:
                cpp_changes[filename] = new_lines
            continue

        pattern = r'^@@ -(\d+),(\d+) \+(\d+),(\d+) @@'
        pattern_matched = re.search(pattern, line)
        if pattern_matched is not None:
            line_number = int(pattern_matched.group(3)) - 1
            continue

        pattern = r'^\+{1}([^\+]*)$'
        pattern_matched = re.search(pattern, line)
        if pattern_matched is not None:
            new_line = (pattern_matched.group(1), line_number)
            new_lines.append(new_line)
            continue

        pattern = r'^-{1}([^-]*)$'
        pattern_matched = re.search(pattern, line)
        if pattern_matched is not None:
            line_number -= 1
            continue

    return cpp_changes

def checkNULL(line, file, line_number, errors):
    pattern = r'\W+NULL\W+'
    pattern_matched = re.search(pattern, line)
    if pattern_matched is not None:
        error = "{0}\nERROR: {1}: line: {2}: Use nullptr instead of NULL".format(line, file, line_number)
        errors.append(error)
        return 1
    else:
        return 0

def checkUint_t(line, file, line_number, errors):
    pattern = r'(^|[^:\w]+)(uint\d+_t)\W+'
    pattern_matched = re.search(pattern, line)
    if pattern_matched is not None:
        type = pattern_matched.group(2)
        error = "{0}\nERROR: {1}: line: {2}: std::{3} instead of {3}".format(line, file, line_number, type)
        errors.append(error)
        return 1
    else:
        return 0

def checkInline(line, file, line_number, errors):
    pattern = r'(^|\W+)inline\W+'
    pattern_matched = re.search(pattern, line)
    if pattern_matched is not None:
        pattern = r';'
        pattern_matched = re.search(pattern, line)
        if pattern_matched is not None:
            pattern = r'\{'
            pattern_matched = re.search(pattern, line)
            if pattern_matched is not None:
                error = "{0}\nERROR: {1}: line: {2}: Put inline functions definition outside of the class declaration"\
                .format(line, file, line_number)
                errors.append(error)
                return 1
            else:
                return 0
        else:
            error = "{0}\nERROR: {1}: line: {2}: Put inline functions definition outside of the class declaration"\
            .format(line, file, line_number)
            errors.append(error)
            return 1
    else:
        return 0

def checkDefine(line, file, line_number, errors):
    pattern = r'#define\s+\w+\s+\w+'
    pattern_matched = re.search(pattern, line)
    if pattern_matched is not None:
        error = "{0}\nERROR: {1}: line: {2}: Use const (static) instead of defined".format(line, file, line_number)
        errors.append(error)
        return 1
    else:
        return 0

def checkEndWhitespaces(line, file, line_number, errors):
    if line.endswith(' ') or line.endswith('\t'):
        error = "{0}\nERROR: {1}: line: {2}: Whitespaces in the end of a line".format(line, file, line_number)
        errors.append(error)
        return 1
    else:
        return 0

def checkEndOpenBrace(line, file, line_number, errors):
    if line.endswith('{') and not line.startswith('{'):
        error = "{0}\nERROR: {1}: line: {2}: Insert the braces under the command line with the same indentation"\
        .format(line, file, line_number)
        errors.append(error)
        return 1
    else:
        return 0

def checkEmptyLine(line, file, line_number, warnings):
    if not line:
        warning = "{0}\nWARNING: {1}: line: {2}: Is this empty line really needed?".format(line, file, line_number)
        warnings.append(warning)
        return 1
    else:
        return 0

def checkLen(line, file, line_number, warnings):
    if len(line) > 80:
        warning = "{0}\nWARNING: {1}: line: {2}: Line length exceeds 80 characters. Considering divide it into several lines"\
        .format(line, file, line_number)
        warnings.append(warning)
        return 1
    else:
        return 0

def checkTab(line, file, line_number, errors):
    pattern = r'\t'
    pattern_matched = re.search(pattern, line)
    if pattern_matched is not None:
        error = "{0}\nERROR: {1}: line: {2}: Avoid using tab in your code".format(line, file, line_number)
        errors.append(error)
        return 1
    else:
        return 0

def checkElse(line, file, line_number, errors):
    pattern = r'\W+else(\W+|$)'
    pattern_matched = re.search(pattern, line)
    if pattern_matched is not None:
        if not line.startswith('else'):
            error = "{0}\nERROR: {1}: line: {2}: Else statement should be considered in a new line"\
            .format(line, file, line_number)
            errors.append(error)
            return 1
        else:
            return 0
    else:
        return 0

def checkMemoryAllocate(line, file, line_number, warnings):
    pattern = r'=\s*new\s*'
    pattern_matched = re.search(pattern, line)
    if pattern_matched is not None:
        warning = "{0}\nWARNING: {1}: line: {2}: Remember to deallocate the memory after use to avoid leaking"\
        .format(line, file, line_number)
        warnings.append(warning)
        return 1
    else:
        return 0

def checkMemoryDeallocate(line, file, line_number, warnings):
    pattern = r'(^|\W+)delete[\[\s]+'
    pattern_matched = re.search(pattern, line)
    if pattern_matched is not None:
        warning = "{0}\nWARNING: {1}: line: {2}: Is this 'delete' in the same form with the corresponding 'new'?"\
        .format(line, file, line_number)
        warnings.append(warning)
        return 1
    else:
        return 0

def checkComparison(line, file, line_number, errors):
    pattern = r'(==|!=)\s*(\w+)'
    pattern_matched = re.search(pattern, line)
    if pattern_matched is not None:
        operator, value = pattern_matched.group(1), pattern_matched.group(2)
        if value in ("nullptr") or value.isdigit() or value.isupper():
            error = "{0}\nERROR: {1}: line: {2}: Put {4} to the left of {3} operator to avoid incorrect assignment"\
            .format(line, file, line_number, operator, value)
            errors.append(error)
            return 1
        else:
            return 0
    else:
        return 0


def checking():
    cpp_changes = attactCPPDiffLines()
    warnings = []
    errors = []
    error_function_list = [checkEndWhitespaces,
                           checkEndOpenBrace,
                           checkNULL,
                           checkUint_t,
                           checkInline,
                           checkDefine,
                           checkTab,
                           checkElse,
                           checkComparison]

    warning_function_list = [checkEmptyLine,
                             checkLen,
                             checkMemoryAllocate,
                             checkMemoryDeallocate]

    for file, lines in cpp_changes.items():
        for line, line_number in lines:
            line = line.lstrip()
            args_error = (line, file, line_number, errors)
            args_warning = (line, file, line_number, warnings)

            for func in error_function_list:
                func(*args_error)
            for func in warning_function_list:
                func(*args_warning)

    return (warnings, errors)

def printResult(warnings, errors):
    if errors:
        print "\nERRORS:\n"
        for i, error in enumerate(errors, 1):
            print "[{0}] {1}".format(i, error)
    if warnings:
        print "\nWARNINGS:\n"
        for i, warning in enumerate(warnings, 1):
            print "[{0}] {1}".format(i, warning)

def main():
    printResult(*checking())

if __name__ == '__main__':
    main()
