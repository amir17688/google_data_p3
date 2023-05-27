import api

def test_paginator():
    po = api.zbox_wiki.paginator.Paginator()

    po.total = 10
    po.limit = 3

    po.current_offset = 0
    assert po.count == 4
    assert po.has_previous_page == False
    assert po.has_next_page == True

    po.current_offset = 1
    assert po.count == 4
    assert po.has_previous_page == True
    assert po.has_next_page == True

    po.current_offset = 2
    assert po.count == 4
    assert po.has_previous_page == True
    assert po.has_next_page == True

    po.current_offset = 3
    assert po.count == 4
    assert po.has_previous_page == True
    assert po.has_next_page == False