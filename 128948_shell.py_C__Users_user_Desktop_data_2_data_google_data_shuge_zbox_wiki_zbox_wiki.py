import os
import logging

import web


logging.getLogger("shell").setLevel(logging.DEBUG)


def get_page_file_list_by_req_path(folder_pages_full_path, req_path, sort_by_modified_ts = False, max_depth = None, limit = None):
    if req_path in ("~all", "~recent"):
        path = "."
    else:
        path = web.utils.strips(req_path, "/")

    if max_depth is None:
        cmd = " cd %s; find %s -follow -name '*.md' -or -name '*.markdown'  " % \
            (folder_pages_full_path, path)
    else:
        cmd = " cd %s; find %s -maxdepth %d -follow -name '*.md' -or -name '*.markdown'  " % \
            (folder_pages_full_path, path, max_depth)
    cmd += " | grep -v  -E '(.index.md|.index.markdown)' "

    if sort_by_modified_ts:
        cmd += " | xargs ls -t "
    if limit is not None:
        cmd += " | head -n %d " % limit
    logging.info(cmd)

    buf = os.popen(cmd).read().strip()
    return buf