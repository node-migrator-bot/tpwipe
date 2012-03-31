'''
TP-WIPE thePlatform Web Information Parser & Extractor - now with logging you filthy animals! 
'''
import urllib
import configparser
import os 
import logging
import json
import urllib.parse
import urllib.request
import socket
import time
from urllib.error import URLError, HTTPError
import http.client
import sys
import getpass

__version__ = "0.2b"
__author__ = "Adam Garcia <adam.garcia@theplatform.com>"

module_logger = logging.getLogger('tpwipe')

#class ThreadUrl(threading.Thread):
#    """threaded url grabber"""
#    def __init__(self, myqueue):
#        threading.Thread.__init__(self)
#        self.q = myqueue
#          
#    def run(self):
#        while True:
#            #grabs img url from queue
#            qi = self.q.get()
#            url = qi
#            try:
#                resp = urllib.request.urlopen(url)
#                logger.debug("now getting data from: {}".format(url))
#            except HTTPError as he:
#                logger.error('http error: {}'.format(he))
#                logger.critical("now exiting!")
#                sys.exit()
#            except URLError as ue:
#                logger.error("url error: {}".format(ue))
#                logger.critical("now exiting!")
#                sys.exit()
#            with open(lf, 'wb') as output:
#                output.write(resp.read())
#            #signals to queue job is done
#            self.q.task_done()


def init_config(dir, cf):
    '''
    These config options will get initialized in case there's no config file 
    '''
    config = configparser.ConfigParser()
    print('No config file found, initializing defaults')
    user = input("What user do you wish to use? ")
    password = getpass.getpass()
    config['DEFAULT'] = {
         'identity_service'       : 'https://identity.auth.theplatform.com',
         'media_data_service'     : 'http://data.media.theplatform.com',
         'legacy_data_service'    : 'http://mps.theplatform.com',
         'file_management_service': 'http://fms.theplatform.com',
         'access_service'         : 'http://access.auth.theplatform.com',
         'watchfolder_service'    : 'http://watchfolder.ingest.theplatform.com',
         'task_service'           : 'http://data.task.theplatform.com',
         'feed_service'           : 'http://data.feed.theplatform.com'}
    config['DEFAULT']['user'] = user
    config['DEFAULT']['pass'] = password
    if not os.path.exists(dir):
        os.makedirs(dir)
        module_logger.debug("created: {}".format(dir))
    with open(cf, 'w') as configfile:
        config.write(configfile)

class ConfigurationError(Exception):
    pass

class AuthorizationException(Exception):
    pass

class ServiceException(Exception):
    pass

class InvalidResource(Exception):
    pass

def requester(host, url, http_method="GET", body=None, headers={}):
    if host.lower().startswith('https'):
        conn = http.client.HTTPSConnection(host[8:], 443, timeout=239)
    elif host.lower().startswith('http'):
        conn = http.client.HTTPConnection(host[7:], 80, timeout=239)
    else:
        raise InvalidResource('Invalid Host: {}'.format(host))
    if "getTokenCount" not in url and 'signIn' not in url:
        module_logger.debug("url: '{}{}' method: '{}' body: '{}' headers: '{}'"
                            .format(host, url, http_method, body, headers))
    try:
        conn.request(http_method, url)
        resp = conn.getresponse()
        module_logger.debug(resp.getheaders())
        data = resp.read()
        if resp.status != 200:
            module_logger.critical("HTTP {} with {}{}".format(resp.status, host,url))
            conn.close()
            sys.exit()
        if data is not None:
            #create test for BOM, if it's there decode properly
            bom_test = "".encode("utf-8-sig")
            if data[0:1] == bom_test[0:1]:
                jsonData = json.loads(data.decode("utf-8-sig"))
            else:
                jsonData = json.loads(data.decode("utf-8"))
            if 'isException' not in json.dumps(jsonData):
                return jsonData
            elif 'Invalid security token.' in json.dumps(jsonData):
                module_logger.error("Token Expired")
                return "EXPIRED TOKEN"
            else:
                module_logger.critical("Critical error: {}".format(jsonData))
                sys.exit()
        else:
           module_logger.warn("Got empty payload with {}{}".format(host, url))
           conn.close()
           requester(host, url, http_method, body, headers)
    except http.client.HTTPException as e:
        if hasattr(e, 'reason'):
            logger.warn('We failed to reach a server. HTTPException')
            logger.warn('Reason: {}'.format(e.reason))
        elif hasattr(e, 'code'):
            logger.warn("The server couldn\'t fulfill the request, here's the reason")
            logger.error('Error code: {}'.format(e.code))
        time.sleep(115)
        requester(host, url, http_method, body, headers) 
    except socket.timeout as st:
        module_logger.error("Connection timed out with {}{}".format(host, url))
        conn.close()
        return "CONNECTION TIMEOUT"
    except socket.error as se:
        module_logger.error(se)
        module_logger.error("An existing connection was forcibly closed by the Data Service with {}{}".format(host, url))
        conn.close()
        return "FORCED CLOSURE"
    finally:
        conn.close()

def tc(secs):
    """
    This function takes time from the data service, which is epoch time in 
    milliseconds, and converts it to the system localtime.
    """
    shrink = secs / 1000
    localize = time.localtime(shrink)
    formatted = time.asctime(localize)
    return formatted

class SingleRequests():
    """Creates all the single requests you wish to use in a one off situation"""
    #first test for what platform it's running under
    _HOME = os.path.expanduser("~")
    _CONFIG_DIR = os.path.join(_HOME, "tp")
    _CONFIG_FILE = "tpconfig.ini"
    _cd = _CONFIG_DIR
    _DEFAULT_CONFIG_FILE = os.path.join(_CONFIG_DIR, _CONFIG_FILE)
    _cf = _DEFAULT_CONFIG_FILE
    if not os.path.exists(_DEFAULT_CONFIG_FILE):
        module_logger.warn("Initializing config: {}"
                           .format(_cd, _DEFAULT_CONFIG_FILE))
        init_config(_CONFIG_DIR, _DEFAULT_CONFIG_FILE)
    _config = configparser.ConfigParser()
    _cached_token = [None, None]
    _last_token_time = 0
    def __init__(self, method="GET"):
        self.logger = logging.getLogger('tpwipe.SingleRequests')    
        try:
            self._config.read(self._DEFAULT_CONFIG_FILE)
            #check for config
        except ConfigurationError:
            print("something is wrong with the config file!")
        else:
            self.user     = self._config['DEFAULT']['user']
            self.password = self._config['DEFAULT']['pass']
            self.identity = self._config['DEFAULT']['identity_service']
            self.mds      = self._config['DEFAULT']['media_data_service']
            self.mps      = self._config['DEFAULT']['legacy_data_service']
            self.fms      = self._config['DEFAULT']['file_management_service']
            self.waf      = self._config['DEFAULT']['watchfolder_service']
            self.access   = self._config['DEFAULT']['access_service']
            self.feed     = self._config['DEFAULT']['feed_service']
            self.task     = self._config['DEFAULT']['task_service']
            self.method   = method
#           self.log_file = self._config['DEFAULT']['log_file']


    def newToken(self, dur="short"):
        #6minutes, the data service should timeout at about 5 minutes
        short_idle = 360000
        long_idle = 7400000
        systime = int(time.time())
        data = None
        self.logger.debug("getting a token at this time: {}".format(systime))
        if self._cached_token[0] is not None:
            if self._cached_token[1] == "short" and self._last_token_time + (short_idle / 1000) > systime:
                self.logger.debug("returning cached token: {}".format(self._cached_token[0]))
                return self._cached_token[0]
            if self._cached_token[1] == "long" and self._last_token_time + (long_idle / 1000) > systime:
                self.logger.debug("returning cached token: {}".format(self._cached_token[0]))
                return self._cached_token[0]
            else:
                self._cached_token[0], self._cached_token[1] = [None, dur]
                self.newToken(dur)
        if dur == "long":
            duration = long_idle
        elif dur == "short":
            duration = short_idle
        schema = "/idm/web/Authentication/signIn?schema=1.0&form=json&"
        params = urllib.parse.urlencode({'username': self.user, 
                                         'password': self.password,
                                         '_idleTimeout': duration})
        url = schema + params         
        data = requester(self.identity, url)
        if data is not None:
            self.logger.debug(data)
            self.token = data.get("signInResponse")['token']
            token_count = "/idm/web/Authentication/getTokenCount?schema=1.0&form=json&username="+\
            self.user + "&password=" + self.password
            get_tc = requester(self.identity, token_count)
            token_count = get_tc["getTokenCountResponse"]
            self.logger.debug("Using: {} tokens".format(token_count))
            self._cached_token[0], self._cached_token[1] = [self.token, dur] 
            self._last_token_time = int(time.time())
            self.logger.debug("Here's the last token time: {}".format
                              (self._last_token_time))
            self.logger.debug("New token: {}".format(self.token))
            return self.token

    def signTokenOut(self, token):
        """ Sign out """
        if self._cached_token[0] is None:
            return
        url = "/idm/web/Authentication/signOut?form=json&schema=1.0&_token={}".format(self.token)
        body = requester(self.identity, url)
        if body is not None:
            self.token = None
            self._cached_token = [None, None]  
#-----------------------------------------------------------------------------   
class MPS(SingleRequests):
    def __init__(self):
        SingleRequests.__init__(self)
        self.logger = logging.getLogger('tpwipe.MPS')
        self.params = urllib.parse.urlencode({'schema': "1.2.0", "form":'json'})        
    def mediabyq(self, q, token):
        """
        Get facade media object by Q query
        """
        fields = urllib.parse.urlencode({'count': 'true', 'q': q, +\
                'fields': "id,added,ownerId,title,content", 'token': token})
        url = "/data/Media?" + self.params + "&" + fields
        data = requester(self.mps, url)
        return data
 
    def mediarequestsbytimestamp(self, acc, date, token):
        """
        Get media requests over a specific time period by account name.
        """
        fields = urllib.parse.urlencode({'fields': 'adPolicyId,requestCount',\
                                         'byTimestamp': date, 'byOwner': acc,\
                                         'count': 'false'})
        url = "/data/MediaRequest?" + self.params + "&token=" + token + "&" + fields
        data = requester(self.mps, url)
        return data

    def tasksbyrange(self, rng, token, feed=False, body=None):
        """
        Get all tasks by range
        """
        fields = urllib.parse.urlencode({'token': token, 
                                         'range': rng,
                                         'count': 'true'})
        if feed:
            url = "/data/Task/feed?" + self.params + "&" + fields
        else:
            url = "/data/Task?" + self.params + "&" + fields
        data = requester(self.mps, url, self.method)
        return data     

    def servers(self, id, token):
        """
        Get servers in an account
        """
        fields = urllib.parse.urlencode({'token': token, 'byOwnerId': id})
        url = "/data/Server?" + self.params + "&" + fields
        data = requester(self.mps, url)
        return data

    def tasksbyaccountname(self, acc, token, feed=False, body=None):
        """
        Get all non-vms tasks by account name
        """
        fields = urllib.parse.urlencode({'token': token, 
                                         'account': acc,
                                         'count': 'true'})
        if feed:
            url = "/data/Task/feed?" + self.params + "&" + fields
        else:
            url = "/data/Task?" + self.params + "&" + fields
        data = requester(self.mps, url, self.method)
        return data

    def tasksbyownerid(self, id, token, feed=False, body=None):
        """
        Get all non-vms tasks by account name
        """
        fields = urllib.parse.urlencode({'token': token, 
                                         'byOwnerid': id,
                                         'count': 'true'})
        if feed:
            url = "/data/Task/feed?" + self.params + "&" + fields
        else:
            url = "/data/Task?" + self.params + "&" + fields
        data = requester(self.mps, url, self.method)
        return data

    def mediabyid(self, id, token):
        """
        Get non-vms media object by its id
        """
        fields = urllib.parse.urlencode({'token': token, 
                                         'fields': 'id,title,ownerId'})
        url = "/data/Media/" + id + "?" + self.params + "&" + fields
        data = requester(self.mps, url)
        return data

    def mediabyrange(self, acc, rng, token, feed=False, body=None):
        """
        Get all media by account name with a range
        """
        fields = urllib.parse.urlencode({'token': token, 
                                         'account': acc,
                                         'count': 'true',
                                         'range': rng})
        if feed:
            url = "/data/Media/feed?" + self.params + "&" + fields
        else:
            url = "/data/Media?" + self.params + "&" + fields
        data = requester(self.mps, url, self.method)
        return data

    def serverbyownerid(self, id, token, feed=False, body=None):
        fields = urllib.parse.urlencode({'byOwnerId': id, 'token': token,
                                         'fields':
        'id,title,password,userName,storageUrl,zones'})
        if feed:
            url = "/data/Server/feed?" + self.params + "&" + fields
        else:
            url = "/data/Server?" + self.params + "&" + fields
        data = requester(self.mps, url, self.method)
        return data

class MDS(SingleRequests):
    def __init__(self):
        SingleRequests.__init__(self)
        self.logger = logging.getLogger('tpwipe.MediaDataService(VMS)')
        self.params = urllib.parse.urlencode({'schema': '1.2.0', 
                                              'form': 'json'})

    def assettypefield(self, account, token, feed=False, body=None):
        fields = urllib.parse.urlencode({'account': account, 'token': token})
        if feed:
            url = "/media/data/AssetType/Field/feed?" + self.params + "&" + fields
        else:
            url = "/media/data/AssetType/Field?" + self.params + "&" + fields
        data = requester(self.mds, url, self.method)
        return data

    def mediafield(self, account, token, feed=False):
        fields = urllib.parse.urlencode({'account': account, 'token': token})
        url = "/media/data/Media/Field?" + self.params + "&" + fields
        data = requester(self.mds, url)
        return data

    def serverbyownerid(self, id, token, feed=False, body=None):
        fields = urllib.parse.urlencode({'byOwnerId': id, 'token': token})
        if feed:
            url = "/media/data/Server/feed?" + self.params + "&" + fields
        else:
            url = "/media/data/Server?" + self.params + "&" + fields
        data = requester(self.mds, url, self.method)
        return data
    
    def serverbyid(self, id, token, feed=False, body=None):
        fields = urllib.parse.urlencode({'token': token})
        if feed:
            url = "/media/data/Server/feed?" + str(id) + "&" + self.params + \
                  "&" + fields
        else:
            url = "/media/data/Server?" + str(id) + "&" + self.params + "&" + fields
        data = requester(self.mds, url, self.method)
        return data

    def media(self, id, token, feed=False, body=None):
        fields = urllib.parse.urlencode({'token': token})
        if feed:
            url = "/media/data/Media/feed?" + str(id) + "?" + self.params + \
                  "&" + fields
        else:
            url = "/media/data/Media/" + str(id) + "?" + self.params + "&" + \
                  fields
        data = requester(self.mds, url, self.method)
        return data
   
#    def mediabycategory(self, category, token):
#        """
#        Get mds media object by its title using an account context
#        """
#        fields = urllib.parse.urlencode({'count': 'true', 'byCategories': category, 
#                                         'token': token, 'pretty': 'true'})
#        query = self.mds + "/media/data/Media?" + self.params + "&" + fields
#        data = requester(query)
#        return data
#
#-----------------------------------------------------------------------------
class WAF(SingleRequests):
    def __init__(self):
        SingleRequests.__init__(self)
        self.logger = logging.getLogger('tpwipe.WatchFolder')
        self.params = urllib.parse.urlencode({'schema': '1.1.0', 
                                              'form': 'json'})

    def servers(self, account, token):
        fields = urllib.parse.urlencode({'fields': 
                        'folderUrl,folderZones,folderPassword,folderUserName', 
                        'account': account, 'token': token})
        url = "/wf/data/WatchFolder?" + self.params + "&" + fields        
        data = requester(self.waf, url)
        return data

#-----------------------------------------------------------------------------

class TAS(SingleRequests):
    def __init__(self):
        SingleRequests.__init__(self)
        self.logger = logging.getLogger('tpwipe.Task')
        self.params = urllib.parse.urlencode({'schema': '1.2.0', 
                                              'form': 'json'})

    def tasksbyaccount(self, acc, token, feed=False):
        """
        Get all tasks by account name
        """
        fields = urllib.parse.urlencode({'token': token, 
                                         'account': acc,
                                         'count': 'true'})
        if feed:
            url = "/task/data/Task/feed?" + self.params + "&" + fields
        else:
            url = "/task/data/Task/?" + self.params + "&" + fields 
        data = requester(self.task, url)
        return data
    
    def tasksbyownerid(self, id, token, feed=False, body=None):
        """
        Get all tasks by account name
        """
        fields = urllib.parse.urlencode({'token': token, 
                                         'byOwnerid': id,
                                         'count': 'true'})
        if feed:
            url = "/task/data/Task/feed?" + self.params + "&" + fields
        else:
            url = "/task/data/Task?" + self.params + "&" + fields
        data = requester(self.task, url, self.method)
        return data

    def byrange(self, rng, token, feed=False, body=None):
        """
        Get all tasks by range
        """
        fields = urllib.parse.urlencode({'token': token, 
                                         'range': rng,
                                         'count': 'true'})
        if feed:
            url = "/task/data/Task/feed?" + self.params + "&" + fields
        else:
            url = "/task/data/Task?" + self.params + "&" + fields
        data = requester(self.task, url, self.method)
        return data    

    def bystatus(self, status, token, feed=False, body=None):
        """
        Get all tasks by status
        """
        fields = urllib.parse.urlencode({'token': token, 
                                         'byStatus': status,
                                         'count': 'true'})
        if feed:
            url = "/task/data/Task/feed?" + self.params + "&" + fields
        else:
            url = "/task/data/Task?" + self.params + "&" + fields
        data = requester(self.task, url, self.method)
        return data   

    def custom(self, custom_req, token, feed=False, body=None):
        """
        Get all tasks by custom request
        """
        fields = urllib.parse.urlencode({'token': token, 
                                         'count': 'true'})
        if feed:
            url = "/task/data/Task/feed?" + custom_req + "&" + fields
        else:
            url = "/task/data/Task?" + custom_req + "&" + fields
        data = requester(self.task, url, self.method)
        return data 

#-----------------------------------------------------------------------------

class IDM(SingleRequests):
    def __init__(self):
        SingleRequests.__init__(self)
        self.logger = logging.getLogger('tpwipe.Identity')
        self.params = urllib.parse.urlencode({'schema': '1.0', 
                                         'form': 'json'})

    def usernamebyid(self, id, token):
        fields = urllib.parse.urlencode({'_ids[0]': id, 'token': token})        
        url = "/idm/web/Lookup/getUserInfoByIds?" + self.params + "&" + fields
        data = requester(self.identity, url)
        return data

    def useridbyname(self, name, token):
        '''
        Takes in an account name as a stringt and returns the data service 
        response for the getUserInfoByUserNames business endpoint
        '''
        fields = urllib.parse.urlencode({'_userNames[0]': name, 
                                         'token': token})
        url = "/idm/web/Lookup/getUserInfoByUserNames?" + self.params + "&" +\
              fields       
        data = requester(self.identity, url)
        return data
#-----------------------------------------------------------------------------
class ACC(SingleRequests):
    def __init__(self):
        SingleRequests.__init__(self)
        self.logger = logging.getLogger('tpwipe.Access')
        self.params = urllib.parse.urlencode({'schema': '1.2.0', 
                                         'form': 'json'})
    # v Future:
    # ACC.account{?}(*args, **kwargs={options}) # ? _and_ to search multiple?
    #def __getattr__(self, name):
        #def _missing(account, token, **kwargs):
            #pass
            #if not name.startswith("account"):
            #   raise AttributeError(name)
            # method = name[len("account"):] # byTitle, ?
            # fields = urllib.parse.urlencode({'{}'.format(method): account, 'token': token})                     
            # url = "/data/Account?"+self.parms+"&"+ fields
            #return requester(self.access, url)
        #return _missing
    # ^ Future
    def accountidbytitle(self, account, token):
        fields = urllib.parse.urlencode({'byTitle': account, 'token': 
                                         token})
        url = "/data/Account?" + self.params + "&" + fields
        data = requester(self.access, url)
        return data

    def accounttitlebyid(self, account, token):
        fields = urllib.parse.urlencode({'token': token})
        url = "/data/Account/{}".format(account) + "?" + self.params + "&" + \
              fields
        data = requester(self.access, url)
        return data
    
    def subaccounts(self, account, token):
        '''
        This will grab all sub accounts
        '''
        fields = urllib.parse.urlencode({'token': token, 'account': account,
                                         'count': 'true'})
        url = "/data/Account?" + self.params + "&" + fields 
        data = requester(self.access, url)
        return data
    
    def accounts(self, token):
        '''
        This will grab all accounts
        '''
        fields = urllib.parse.urlencode({'token': token, 'count': 'true'})
        url = "/data/Account?" + self.params + "&" + fields 
        data = requester(self.access, url)
        return data
#-----------------------------------------------------------------------------
