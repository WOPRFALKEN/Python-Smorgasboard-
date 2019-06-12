#!/usr/bin/env python
#
# Script for monitor Process status
#
# Prerequisite : None
#
#@---------------------------------------------------
#@ History
#@---------------------------------------------------
#@ Date   : 13 Feb, 2017
#@ Author : Anji Devarasetty
#@ Reason : Initial release
#@---------------------------------------------------
#@ Date   : 
#@ Author : 
#@ Reason : 
#@---------------------------------------------------
#
'''
/*
 * This computer program is the confidential information and proprietary trade
 * secret of VistaraIT, Inc. Possessions and use of this program must  conform
 * strictly to the license agreement between the user and VistaraIT, Inc., and
 * receipt or possession does not convey any rights to divulge, reproduce,  or
 * allow others to use this program without specific written authorization  of
 * VistaraIT, Inc.
 * 
 * Copyright (c) 2016 VistaraIT, Inc. All rights reserved. 
 */
'''

import os, sys, commands

##########################################################################
#     Use the below block of code in all the Custom monitor scripts. 
##########################################################################

api = None
try:
    sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
    from ScriptMonitorPythonApi import ScriptMonitorPythonApi
    api = ScriptMonitorPythonApi(sys.argv)
except Exception, emsg:
    sys.exit()

##########################################################################

def checkProcessRunning(process_name):
    total_occurrence = 0
    pids_list = []
    command = """ps -e -o pid,args | grep '%s' | grep -v grep | grep -v 'metricName::metric' | awk '{print $1}'""" % process_name
    pids = commands.getstatusoutput(command)[1].strip()
    if pids != '':
        pids_list = pids.split("\n")
    if pids_list:
        total_occurrence = len(pids_list)
    return str(total_occurrence), pids
    
def readState(filepath):
    try:
        fileContent = 'Ok'
        if os.path.exists(filepath):
            f = open(filepath, 'r')
            fileContent = f.read()
            f.close()
        return fileContent.strip()
    except:
        return 'Ok'

def saveState(filepath, fileContent):
    try:
        f = open(filepath, 'w')
        f.write(fileContent)
        f.close()
    except Exception, emsg:
        print emsg

def getRCount(filepath):
    try:
        fileContent = '0'
        if os.path.exists(filepath):
            f = open(filepath, 'r')
            fileContent = f.read()
            f.close()
        return fileContent.strip()
    except:
        return '0'

def setRCount(filepath, countValue):
    try:
        f = open(filepath, 'w')
        f.write(countValue)
        f.close()
    except Exception, emsg:
        print emsg

monitor_names = api.metricNames
metrics = api.metrics
warning_thres = api.warnings
critical_thres = api.criticals
do_alerts = api.doAlerts
user_params = api.userParams

print "<DataValues>"
for i in range(0, len(api.metrics)):
    monitor_name = monitor_names[i]
    metric_name = metrics[i]
    user_param = user_params[i]
    do_alert = do_alerts[i]
    perfdataOutput = ""

    input_params = user_param.split("^")
    process_list = input_params[0]
    repeatCount = 0
    
    if len(input_params) == 2:
        repeatCount = input_params[1]

    processList = process_list.split(",")

    for j in range(0, len(processList)):
        process = processList[j]
        processName = processList[j].replace("/", "$")
        bNeedAlert = False
        temp_file  = '/opt/vistara/agent/tmp/process_%s_state.txt' % processName
        instanceCount, pid = checkProcessRunning(process)
        
        monState = 'Ok'
        oldState = readState(temp_file)
        
        _desc = instanceCount + " process(es) running with name '" + process + "'"
        _sub = "Ok. " + _desc
                
        if not pid:
            _desc = "No process running with name '" + process + "'"
            _sub = "Critical. " + _desc
            monState = 'Critical'
            
        if str(do_alert) == "1":
            RC_filepath = "/opt/vistara/agent/tmp/RC_process_%s.txt" % processName
            if oldState != monState:
                if monState != 'Ok':
                    Count = getRCount(RC_filepath)
                    if int(Count) >= int(repeatCount):
                        setRCount(RC_filepath, "0")                      
                        bNeedAlert = True
                    else:
                        setRCount(RC_filepath, str(int(Count)+1))
                else:
                    setRCount(RC_filepath, "0")
                    bNeedAlert = True
            else:
                setRCount(RC_filepath, "0")

        if bNeedAlert == True:
            alert_group = monitor_name + "_" + metric_name + "_" + process
            api.sendAlertMsg(monitor=monitor_name, subject=_sub, description=_desc, newState=monState, oldState=oldState, alertGroup=alert_group, alertType=None, alertTime=None)
            saveState(temp_file, monState)

        if j != 0:
            perfdataOutput += ","

        perfdataOutput +=  process + "=" + instanceCount

    print "<Monitor name='%s' output='%s'></Monitor>" % (monitor_name, perfdataOutput)
print "</DataValues>"

sys.exit(0)