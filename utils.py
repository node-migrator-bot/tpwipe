"""
tpwipe.util
"""

import getpass
from .defaults import defaults

def get_login(username=None, password=None):
	username=input("Username: ") if username is None else username
	password=getpass.getpass()   if password is None else password
	return username, password
    
def split_kwargs(**kwargs):
    requests_kwargs={}
    local_kwargs={}
    #TODO: flesh out requests passable kwargs
    requests_kwargs_keys = ['params', 'timeout']

    for key in kwargs:
        if key not in requests_kwargs_keys:
            local_kwargs[key] = kwargs[key]
        else:
            requests_kwargs[key] = kwargs[key]

    return local_kwargs, requests_kwargs