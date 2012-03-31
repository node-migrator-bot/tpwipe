'''
Created on Feb 15, 2012
This script looks for all open tasks and counts fortress capable tasks
@author: adam.garcia
'''

import tpwipe
import datetime
import logging
import logging.handlers
import urllib
import re
import http.client
http.client.HTTPConnection.debuglevel = 0
logger = logging.getLogger('Task Checker')
tplogger = logging.getLogger('tp')
logger.setLevel(logging.DEBUG)
tplogger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
tplogger.addHandler(ch)
get = tpwipe.SingleRequests()
token = get.newToken()
get.tas = tpwipe.TAS()
rng = '1-1'
start_index = 1
end_index = 100
tp_cap = None
tp_count = 0
tp_joblist = []
#custom request string
cs = "schema=1.2.0&form=json&pretty=true&byStatus=inProgress%7CpendingBatchReady%7CpendingOther%7CinQueue%7CinProgressWithErrors&range=myrange&count=true&entries=true&token="

def rb(rng, cs, token):
    req_string = cs.replace("myrange", rng)
    return req_string + token

def task_getter(func):
    data = None
    attempts = 10
    try:
        while data == None and attempts >= 1:
            data = func
            attempts -= 1
    except Exception as e:
        logger.critical(e)
    return data

def loop_gen(token):
    status = "inProgress|pendingBatchReady|pendingOther|inQueue|inProgressWithErrors"
    data = task_getter(get.tas.bystatus(status, token))
    tc = data["totalResults"]
    return tc

task_count = loop_gen(token)
loops = int(task_count) / 100
for h in range(int(loops)):
    if h == 0:
        start = datetime.datetime.now()
    rng = "{}-{}".format(start_index, end_index)
    custom_req = rb(rng, cs, token)
    logger.debug(custom_req)
    data = task_getter(get.tas.custom(custom_req, token))
    try:
        for i in range(100):
            cap_agents = data["entries"][i]["pltask$capableAgents"]
            for entry in cap_agents:
                if "sea1" in entry or "phl1" in entry:
                    tp_count += 1
                    tp_joblist.append(data["entries"][i]["id"])
                    break
    except IndexError:
        break
    start_index += 100
    end_index += 100
    if end_index > task_count:
        end_index = task_count
##

##
for i, job in enumerate(tp_joblist):
    logger.info("{} tp job: {}".format(i, job))
logger.info("started check at: {}".format(start.strftime("%H:%M")))
logger.info("tp capable: {} out of: {}".format(tp_count, task_count))
logger.info("ended check at: {}".format(datetime.datetime.now().strftime("%H:%M")))
get.signTokenOut(token)
input("Press any key to exit...\n")