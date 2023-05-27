#-*- coding: utf-8 -*-
#
# Created on Feb 28, 2013
#
# @author: Younes JAAIDI
#
# $Id: 6dfdee0f79d7413d69c22cb3e9568bb33ea476d3 $
#

from abc import abstractmethod

class IMemberDelegate:
    
    @abstractmethod
    def apply(self, cls, originalMemberNameList, memberName, classNamingConvention, getter, setter):
        raise NotImplementedError()

    @abstractmethod
    def remove(self, cls, originalMemberNameList, memberName, classNamingConvention):
        raise NotImplementedError()
