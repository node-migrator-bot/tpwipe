"""
tpwipe.util
"""

import getpass
from .defaults import defaults

def get_login(username=None, password=None):
	username=input("Username:") if username is None else username
	password=getpass.getpass()  if password is None else password
	return username, password