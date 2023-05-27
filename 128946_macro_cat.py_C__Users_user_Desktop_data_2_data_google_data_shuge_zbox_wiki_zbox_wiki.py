#!/usr/bin/env python
import logging
import os
import re
import commons

logging.getLogger("macro_cat").setLevel(logging.DEBUG)


def match_in_re(name, patterns):
    for p in patterns:
        re_obj = re.compile(p)
        if re_obj.match(name):
            return True

    return False

def get_files_list(path, ignore_patterns = ['^\.(.+?)$', '^(.+?)~$'], match_patterns = None):
    """ `ignore_patterns` is a list of regular expressions, ignore '.DS_Store', 'foo~' etc by default. """
    files = []
    for pending_filename in os.listdir(path):
        if ignore_patterns:
            if match_in_re(name = pending_filename, patterns = ignore_patterns):
                continue
        if match_patterns:
            if not match_in_re(name = pending_filename, patterns = match_patterns):
                continue
        files.append(pending_filename)
    return files


def fix_pattern(p):
    try:
        re.compile(p)
    except:
        if p.startswith("*.") and p.count("*.") == 1:
            suffix = p.split("*.")[-1]
            fixed = "^(.+?)\.%s$" % suffix
            return fixed
        else:
            msg = "expected regular expression or '*.suffix' style expression, got `%s`" % p
            logging.error(msg)
            return None

    return p


def parse_work_path(file_name, folder_pages_full_path, req_path):
    if os.path.exists(file_name):
        return file_name

    elif file_name.find("/") != -1:
        par = os.path.dirname(file_name)
        if os.path.exists(par):
            return par

        file_full_path = os.path.join(folder_pages_full_path, par)
        if os.path.exists(file_full_path):
            return file_full_path

    default_work_path = os.path.join(folder_pages_full_path, req_path)
    if req_path:
        par = os.path.dirname(default_work_path)
        if os.path.exists(par):
            return par

    return default_work_path


def cat_files(work_path, files):
    all = ""
    for filename in files:
        full_path = os.path.join(work_path, filename)
        chunk = filename + "\n"
        with open(full_path) as f:
            buf = commons.strutils.safeunicode(f.read())
            buf = "\n    ".join(buf.split("\n"))
            buf = commons.strutils.rstrips(buf, "    ")
            chunk += "\n\n    " + buf
        chunk += "\n"
        all += chunk

    return all


def macro_zw2md_cat(text, folder_pages_full_path, req_path, **view_settings):
    shebang_p = "#!zw"
    code_p = '(?P<code>[^\f\v]+?)'
    code_block_p = "^\{\{\{[\s]*%s*%s[\s]*\}\}\}" % (shebang_p, code_p)
    p_obj = re.compile(code_block_p, re.MULTILINE)

    def code_repl(match_obj):
        code = match_obj.group('code')
        code = code.split("\n")[1]

        if code.startswith("cat("):
            p = 'cat\((?P<file_name>.+?)\)'
            m = re.match(p, code, re.UNICODE | re.MULTILINE)
            file_name = m.group("file_name")
            file_name = file_name.strip()
            work_path = parse_work_path(file_name = file_name, folder_pages_full_path = folder_pages_full_path, req_path = req_path)

            match_pattern = file_name.strip("'").strip("\"")
            match_pattern = commons.strutils.lstrips(match_pattern, work_path)
            match_pattern = commons.strutils.strips(match_pattern, "/")
            match_pattern = fix_pattern(match_pattern)

            files = get_files_list(path = work_path, match_patterns = [match_pattern])

            buf = cat_files(work_path = work_path, files = files)
            return buf

#        return code
        buf_fixed = "{{{#!zw\n%s\n}}}" % code
        return buf_fixed

    return p_obj.sub(code_repl, text)

def test_fix_pattern():
    auto_patterns = (
        ("*.md", "^(.+?)\.md$"),
        ("^(.+?)\.md$", "^(.+?)\.md$"),
    )

    for e, g in auto_patterns:
        assert fix_pattern(e) == g


def test_macro_cat():
    text = """
{{{#!zw
cat("*.md")
}}}
"""
    req_path = ""
    folder_pages_full_path = "/tmp/lees_wiki/pages/"
    result = macro_zw2md_cat(text = text, folder_pages_full_path = folder_pages_full_path, req_path = req_path)
    result = commons.strutils.strips(result, "\n")
    print repr(result)


if __name__ == "__main__":
    test_fix_pattern()
    test_macro_cat()
