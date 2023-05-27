import os
import api

def test_req_path_to_local_full_path():
    config_agent = api.zbox_wiki.config_agent
    config_path = os.path.join(api.instance_full_path, "default.cfg")
    config = config_agent.load_config([config_path], instance_full_path = api.instance_full_path)
    api.zbox_wiki.config_agent.config = config


    folder_pages_full_path = config.get("paths", "pages_path")

    for req_path, expected in (
            ("sandbox1", '/tmp/pages/sandbox1.md'),
            ("sandbox1/", '/tmp/pages/sandbox1/'),
            ("hacking/fetion/fetion-protocol/", '/tmp/pages/hacking/fetion/fetion-protocol/'),
            ("hacking/fetion/fetion-protocol/method-option.md", '/tmp/pages/hacking/fetion/fetion-protocol/method-option.md'),
            ("~all", '/tmp/pages/'),
            ("/", '/tmp/pages/'),
            ("", '/tmp/pages/')
        ):
        got = api.zbox_wiki.mdutils.req_path_to_local_full_path(req_path = req_path, folder_pages_full_path = folder_pages_full_path)
        assert got == expected

test_req_path_to_local_full_path()