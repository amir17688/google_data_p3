#!/usr/bin/env python
#-*- coding:utf-8 -*-
import httplib
import os
import types

import BeautifulSoup
import config
import requests


content = """# this is a
the page name is a
"""

new_content = """# this is b
the page name is b
"""

def test_create_page():
    content_p = "the page name is a"
    page_name = "a"
    url = os.path.join(config.web_url + "~new")
    params = {"action" : "create"}
    data = {"path" : page_name, "content" : content}
    r = requests.post(url, data = data, params = params)
    assert r.status_code == httplib.SEE_OTHER

    url = os.path.join(config.web_url + page_name)
    r = requests.get(url)
    assert r.status_code == httplib.OK

    soup = BeautifulSoup.BeautifulSoup(r.text)
    tag_div = soup.findAll('div', id="content")[0]
    chunk = str(tag_div)
    assert chunk.find(content_p) != -1

    url = os.path.join(config.web_url + page_name)
    params = {"action" : "source"}
    r = requests.get(url, data = data, params = params)
    assert r.content_type
    assert r.text == content
    assert r.headers['content-type'] == "text/plain; charset=UTF-8"

def test_view_page_source():
    pass

def test_update_page():
    content_p = "the page name is b"
    page_name = "aaa"
    url = os.path.join(config.web_url + "~new")
    data = {"path": page_name, "content": content}
    r = requests.post(url, data = data, params = {"action": "create"})
    assert r.status_code == httplib.SEE_OTHER

    data = {"content" : new_content}
    r = requests.post(config.web_url, data = data, params = {"action" : "edit"})
    assert r.status_code == httplib.SEE_OTHER

    url = os.path.join(config.web_url + page_name)
    r = requests.get(url)
    assert r.status_code == httplib.OK

    soup = BeautifulSoup.BeautifulSoup(r.text)
    tag_div = soup.findAll('div', id="content")[0]
    chunk = str(tag_div)
    assert chunk.find(content_p) != -1

    url = os.path.join(config.web_url + page_name)
    params = {"action" : "source"}
    r = requests.get(url, data = data, params = params)
    assert r.content_type
    assert r.text == content
    assert r.headers['content-type'] == "text/plain; charset=UTF-8"


def test_delete_page():
    pass

def test_rename_page():
    pass


def test_view_folder_source():
    pass

def test_update_folder():
    pass

def test_delete_folder():
    pass

def test_rename_folder():
    pass

def main_suck():
    keys = locals().keys()
    for key in keys:
        obj = locals()[key]
        if isinstance(obj, types.FunctionType):
            func = obj
            if func.func_name.startswith("test_"):
                func()

if __name__ == "__main__":
    main_suck()
#    import nose
#    nose.main()