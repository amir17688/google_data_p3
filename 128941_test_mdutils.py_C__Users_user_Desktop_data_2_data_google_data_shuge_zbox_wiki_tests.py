import api

def test_path2hierarchy():
    for i in [
        ("/", [("index", "/~index")]), # name, link pairs

        ("/system-management/gentoo/abc",
         [("system-management", "/system-management"),("gentoo", "/system-management/gentoo"),("abc", "/system-management/gentoo/abc"),]),

        ("/programming-language",
         [("programming-language", "/programming-language"),]),

        ("/programming-language/",
         [("programming-language", "/programming-language"),]),
                                       ]:
        req_path = i[0]
        links = i[1]
        assert api.zbox_wiki.mdutils.path2hierarchy(req_path) == links