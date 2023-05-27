#!/usr/bin/env python
import os
import sys

PWD = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, PWD)

import conf
from zbox_wiki.main import web, Robots, SpecialWikiPage, WikiPage, mapping

application = web.application(mapping, globals()).wsgifunc()
