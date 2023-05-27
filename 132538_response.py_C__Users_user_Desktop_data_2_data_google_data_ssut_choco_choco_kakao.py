#-*- coding: utf-8 -*-
from choco.contrib.constants import ContentType

class KakaoResponse(object):
    def __init__(self, content, content_type=ContentType.Text):
        self.content = content
        self.content_type = content_type
