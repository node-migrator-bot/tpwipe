"""
tpwipe.sessions
"""

import urllib
import json
import requests
from .defaults import defaults
from .utils import get_login


class Session(object):
    """A tpwipe session."""
    __attrs__ = [ 'username', 'password', 'token', 'options','config'
                  'schema', 'form'] 

    def __init__(self,
        schema=None,
        form=None,
        username=None,
        password=None,
        token=None,
        options=None,
        config=None):

        self.username = username or defaults['username']
        self.password = password or defaults['password']
        self.token    = token    or defaults['token']
        self.schema   = schema   or defaults['schema']
        self.form     = form     or defaults['form']
        self.options  = options  or {}
        self.config   = config   or {}


        for (k, v) in list(defaults.items()):
            self.config.setdefault(k, v)

    def __getattr__(self, name):
        def _missing(*args, **kwargs):
            print("\nA missing method was called.")
            print("The object was %r, the method was %r. " % (self, name))
            print("It was called with %r and %r as arguments" % (args, kwargs))
            method = name[len('request_'):]
            print("Method: "+method)




            return self.request(method, *args, **kwargs)
        return _missing

    def get_token(self,**kwargs):
        url = defaults['get_token']+'?'+urllib.parse.urlencode(kwargs)
        return json.loads(self.request_get_token(**kwargs).text)['signInResponse']['token']


    def set_token(self, token=None):
        if token is not None:
            self.token = token
        return token == self.token

    def get_token_count(self,username= None,password= None):
        return json.loads(self.request_token_count(
                                       username=username or self.username, 
                                       password=password or self.password,
                                       ).text)['getTokenCountResponse']

    def login(self,username=None,password=None, schema=None, form=None):
        if self.username is None and self.password is None:
            self.username, self.password = get_login(username=username, 
                                                     password=password)
        self.token = self.get_token(username=username or self.username, 
                                    password=password or self.password,
                                    form=form         or self.form,
                                    schema=schema     or self.schema)
        return self.token

    def logout(self):
        #self.password = None
        #self.username = None
        state = self.destroy_token(token=self.token)
        self.token = None #if state #is OK 
        return state

    def get_new_token(self,username=None,password=None):
        self.destroy_token(self.token)
        return self.login()

    def destroy_token(self, token=None):#pesky _token
        return self.request_destroy_token(_token=token or self.token)

    def request(self,
                method,
                *args,
                **kwargs):
        print("\nrequest() was called.")
        print("The object is %r, the method is %r. " % (self, method))
        print("It was called with %r and %r as arguments." % (args, kwargs))

        requests_kwargs_keys = ['params', 'timeout']
        requests_kwargs={}
        local_kwargs={}
        
        if method not in defaults:
            defaults[method] = method  

        path = kwargs['url'] if 'url' in kwargs else defaults[method] 
        subpath = '/'+'/'.join(args) if len(args) >1 else '/'+''.join(args)
        params = '?'

        for key in kwargs:
            if key not in requests_kwargs_keys:
                local_kwargs[key] = kwargs[key]
            else:
                requests_kwargs[key] = kwargs[key]

        if 'token' not in local_kwargs:
            if self.token is not None:
                local_kwargs['token'] = self.token  
            else:
                # I don't like this way of excluding the creation of a token
                # on these types...
                if method not in ['destroy_token','get_token','token_count']:
                    local_kwargs['token'] = self.login() 

        if 'schema' not in local_kwargs:
            if self.schema is not None:
                local_kwargs['schema'] = self.schema  

        if 'form' not in local_kwargs:
            if self.form is not None:
                local_kwargs['form'] = self.form  


        params+= urllib.parse.urlencode(local_kwargs)


        url = path+subpath+params

        print("\nRequesting: "+url)

        return requests.get(url, **requests_kwargs)

    def __repr__(self):
        return '<tpwipe-client at 0x%x>' % (id(self))

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if self.token: self.logout()

    def __getstate__(self):
        return dict((attr, getattr(self, attr, None)) for attr in self.__attrs__)

    def __setstate__(self, state):
        for attr, value in state.items():
            setattr(self, attr, value)

def session(**kwargs):
    """Returns a :class:`Session` for context-management."""
    return Session(**kwargs)