#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com


from thumbor.detectors import BaseDetector


class Detector(BaseDetector):
    def detect(self, callback):
        self.context.request.prevent_result_storage = True
        callback()
