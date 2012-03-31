#!/usr/bin/env

"""
tpwipe.example.get_4_media
"""

import json
import tpwipe

def run():
    query = tpwipe.Session()
    print("*****BEFORE LOGIN*****: {}".format(query.get_token_count()))
    query.login()
    print("*****AFTER LOGIN*****: {}".format(query.get_token_count()))
    entries = query.request_media_data('Media',
                                       account="FarrinReid(VMS) - E2E Solution",
                                       fields ="title,id,description",
                                       range="1-4"
                                      )
    query.logout()
    print("*****AFTER LOGOUT*****: {}".format(query.get_token_count()))

    print(json.dumps(json.loads(entries.text), indent=4))

    input("Press any key to exit...")
    
if __name__ == '__main__':
    run()