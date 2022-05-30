#!/usr/bin/python
# -*- coding: utf-8 -*-
import json,logging, inspect, functools

class APIError(Exception):
    """the base APIError which contains error(required), data(optional) and message(optional)."""
    def __init__(self, error, data='',message=''):
        super(APIError, self).__init__(message)
        self.error=error
        self.data=data
        self.message=message

class APIValueError(APIError):
    '''
    Indicate the input value has error or invalid. The data specifies the error field of input form.
    '''
    def __init__(self,field,message=''):
        #?field有什么用?
        super(APIValueError,self).__init__('value:invalid',field,message)

class APIResourceNotFoundError(APIError):
    """
    Indicate the resource was not found. The data specifies the resource name.
    """
    def __init__(self,field,message=''):
        super(APIResourceNotFoundError, self).__init__('value:notfound',field,message)

class APIPermissionError(object):
    """
    Indicate the resource was not found. The data specifies the resource name.
    """
    def __init__(self, message=''):
        super(APIPermissionError, self).__init__('permission:forbidden','permission',message)

class Page(object):
    """
        >>> p1 = Page(100, 1)
        >>> p1.page_count
        10
        >>> p1.offset
        0
        >>> p1.limit
        10
        >>> p2 = Page(90, 9, 10)
        >>> p2.page_count
        9
        >>> p2.offset
        80
        >>> p2.limit
        10
    """
    def __init__(self, item_count,page_index=1,page_size=10):
        self.item_count=item_count
        self.page_size = page_size
        self.page_count=item_count//page_size+(1 if item_count%page_size>0 else 0)
        if (item_count==0) or (page_index>self.page_count):
            self.offset=0
            self.limit=0
            self.page_index=1
        else:
            self.page_index=page_index
            self.offset=self.page_size*(page_index-1)
            self.limit=self.page_size
        self.has_next=self.page_index<self.page_count
        self.has_pre=self.page_index>1

        def __str__(self):
            return 'item_count:%s,page_count:%s,page_size:%s,offset:%s,limit:%s'%(self.item_count,self.page_count,self.page_size,self.offset,self.limit)
        #用__str__覆盖__repr__
        #__str__在print时输出，__repr__在直接显示对象时输出
        __repr__=__str__


