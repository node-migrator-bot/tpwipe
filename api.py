"""
tpwipe.api
"""
#not yet implemented....
from . import sessions

def tpwipe(method, *args, **kwargs):
	s = kwargs.pop('session') if 'session' in kwargs else sessions.session()
	return s.request(method=method, *args, **kwargs)

def request(method,*args, **kwargs):
	return tpwipe(method, *args, **kwargs)

def login(**kwargs):
	return tpwipe('login', **kwargs)

def logout(**kwargs):
	return tpwipe('login', **kwargs)

