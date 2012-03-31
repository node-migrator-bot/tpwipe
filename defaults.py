"""
tpwipe.defaults
"""

from . import __version__

defaults = dict()

defaults['verbose']                = None
defaults['identity_service']       = 'https://identity.auth.theplatform.com'
defaults['media']                  = 'http://data.media.theplatform.com'
defaults['media_data']             = 'http://data.media.theplatform.com/media/data'
defaults['legacy']                 = 'http://mps.theplatform.com'
defaults['fms']                    = 'http://fms.theplatform.com'
defaults['access']                 = 'http://access.auth.theplatform.com'
defaults['watchfolder']            = 'http://watchfolder.ingest.theplatform.com'
defaults['task']                   = 'http://data.task.theplatform.com'
defaults['feed']                   = 'http://data.feed.theplatform.com'
defaults['destroy_token']          = 'https://identity.auth.theplatform.com'+\
                                      '/idm/web/Authentication/signOut'
defaults['get_token']              = 'https://identity.auth.theplatform.com'+\
                                      '/idm/web/Authentication/signIn'
defaults['token_count']            = 'https://identity.auth.theplatform.com'+\
                                      '/idm/web/Authentication/getTokenCount'
defaults['username']               = None
defaults['password']               = None
defaults['token']                  = None
defaults['schema']                 = '1.0'
defaults['form']                   = 'json'

