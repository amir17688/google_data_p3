import logging
import os

import commons


logging.getLogger("static_file").setLevel(logging.DEBUG)


def append_static_file(text, file_path, file_type, add_newline=False):
    assert file_type in ("css", "js")

    if file_type == "css":
        ref = '<link href="%s" rel="stylesheet" type="text/css">' % file_path
    else:
        ref = '<script type="text/javascript" src="%s"></script>' % file_path

    if not add_newline:
        static_files = "%s\n    %s" % (text, ref)
    else:
        static_files = "%s\n\n    %s" % (text, ref)

    return static_files

def get_global_static_files(**view_settings):
    static_files = ""

    css_files = ("zw-base.css",)
    for i in css_files:
        path = os.path.join("/static", view_settings["theme_name"], "css", i)
        static_files = append_static_file(static_files, path, file_type = "css")

    if view_settings["reader_mode"]:
        path = os.path.join("/static", view_settings["theme_name"], "css", "zw-reader.css")
        static_files = append_static_file(static_files, path, file_type = "css")

    if view_settings["auto_toc"]:
        path = os.path.join("/static", view_settings["theme_name"], "css", "zw-toc.css")
        static_files = append_static_file(static_files, path, file_type = "css")

    if view_settings["highlight_code"]:
        path = os.path.join("/static", view_settings["theme_name"], "js", "prettify", "prettify.css")
        static_files = append_static_file(static_files, path, file_type = "css", add_newline = True)


    static_files = "%s\n" % static_files

    js_files = ("jquery.js", "jquery-ui.js")
    static_files += "\n"
    for i in js_files:
        path = os.path.join("/static", view_settings["theme_name"], "js", i)
        static_files = append_static_file(static_files, path, file_type = "js")

    js_files = ("zw-base.js", )
    static_files += "\n"
    for i in js_files:
        path = os.path.join("/static", view_settings["theme_name"], "js", i)
        static_files = append_static_file(static_files, path, file_type = "js")

    if view_settings["auto_toc"]:
        static_files += "\n"
        path = os.path.join("/static", view_settings["theme_name"], "js", "zw-toc.js")
        static_files = append_static_file(static_files, path, file_type = "js")

    if view_settings["highlight_code"]:
        static_files += "\n"
        js_files = (os.path.join("prettify", "prettify.js"), "highlight.js")
        for i in js_files:
            path = os.path.join("/static", view_settings["theme_name"], "js", i)
            static_files = append_static_file(static_files, path, file_type = "js")

    return static_files

def get_folder_static_full_path(config_agent):
    folder_static_name = config_agent.config.get("paths", "static_path")

    if os.path.isabs(folder_static_name):
        path = folder_static_name
    else:
        folder_pages_name = config_agent.config.get("paths", "pages_path")
        path = "/%s/%s" % (folder_static_name, folder_pages_name)

    return path

def get_static_file_prefix_by_local_full_path(config_agent, local_full_path, req_path):
    folder_static_name = config_agent.config.get("paths", "static_path")
    components = []

    if os.path.isfile(folder_static_name):
        chunk = os.path.basename(folder_static_name)
        components.append(chunk)
    elif isinstance(folder_static_name, basestring):
        chunk = folder_static_name
        components.append(chunk)

    folder_pages_name = config_agent.config.get("paths", "pages_path")
    chunk = os.path.basename(folder_pages_name)
    components.append(chunk)

    if os.path.isdir(local_full_path):
        components.append(req_path)
    elif os.path.isfile(local_full_path):
        chunk = os.path.dirname(req_path)
        components.append(chunk)

    prefix = '/' + '/'.join(components)

    return prefix