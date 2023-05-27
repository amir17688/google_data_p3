import logging
import os
import web

import config_agent


logging.getLogger("search").setLevel(logging.DEBUG)


def search_by_filename_and_file_content(keywords, limit):
    """
    Following doesn't works if cmd contains pipe character:

        p_obj = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)
        p_obj.wait()
        resp = p_obj.stdout.read().strip()

    So we have to do use deprecated syntax ```os.popen```, for more detail, see
    http://stackoverflow.com/questions/89228/how-to-call-external-command-in-python .
    """

    find_by_filename_matched = " -o -name ".join([" '*%s*' " % i for i in keywords.split()])
    find_by_content_matched = " \| ".join(keywords.split())
    is_multiple_keywords = find_by_content_matched.find("\|") != -1
    folder_page_full_path = config_agent.get_full_path("paths", "pages_path")

    if is_multiple_keywords:
        find_by_filename_cmd = " cd %s; "\
                               " find . \( -name %s \) -type f | " \
                               " grep -E '(.md$|.markdown$)' | head -n %d " % \
                               (folder_page_full_path, find_by_filename_matched, limit)

        find_by_content_cmd = " cd %s; " \
                              " grep ./ --recursive --ignore-case --include=*.{md,markdown} --regexp ' \(%s\) ' | " \
                              " awk -F ':' '{print $1}' | uniq | head -n %d " % \
                              (folder_page_full_path, find_by_content_matched, limit)
    else:
        find_by_filename_cmd = " cd %s; " \
                               " find . -name %s -type f | " \
                               " grep -E '(.md$|.markdown$)' | head -n %d " % \
                               (folder_page_full_path, find_by_filename_matched, limit)

        find_by_content_cmd = " cd %s; " \
                              " grep ./ --recursive --ignore-case --include=*.{md,markdown} --regexp '%s' | " \
                              " awk -F ':' '{print $1}' | uniq | head -n %d " % \
                              (folder_page_full_path, find_by_content_matched, limit)

    msg = "find files by name >>>" + find_by_filename_cmd
    logging.debug(msg)

    msg = "find files by content >>>" + find_by_content_cmd
    logging.debug(msg)


    matched_content_lines = os.popen(find_by_content_cmd).read().strip()
    matched_content_lines = web.utils.safeunicode(matched_content_lines)
    if matched_content_lines:
        matched_content_lines = web.utils.safeunicode(matched_content_lines)
        matched_content_lines = matched_content_lines.split("\n")

    matched_filename_lines = os.popen(find_by_filename_cmd).read().strip()
    matched_filename_lines = web.utils.safeunicode(matched_filename_lines)
    if matched_filename_lines:
        matched_filename_lines = web.utils.safeunicode(matched_filename_lines)
        matched_filename_lines = matched_filename_lines.split("\n")

    if matched_content_lines and matched_filename_lines:
        # NOTICE: build-in function set() doesn't keep order, we shouldn't use it.
        # mixed = set(matched_filename_lines)
        # mixed.update(set(matched_content_lines))
        mixed = web.utils.uniq(matched_filename_lines + matched_content_lines)
    elif matched_content_lines and not matched_filename_lines:
        mixed = matched_content_lines
    elif not matched_content_lines and matched_filename_lines:
        mixed = matched_filename_lines
    else:
        return None

    lines = mixed
    return lines
