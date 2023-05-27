#-*- coding: utf-8 -*-
#
# Created on Dec 17, 2012
#
# @author: Younes JAAIDI
#
# $Id: c69b21969e0b3c4ed7bf08321ce575c23542e0cb $
#

from abc import abstractmethod

class INamingConvention:
    
    @abstractmethod
    def getterName(self, memberName):
        raise NotImplementedError()

    @abstractmethod
    def setterName(self, memberName):
        raise NotImplementedError()
