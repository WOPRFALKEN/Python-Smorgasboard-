#Script for monitor TCP monitoring to give IP & port list
#
# Prerequisite : None
#
#@---------------------------------------------------
#@ History
#@---------------------------------------------------
#@ Date   : 26 Dec, 2016
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

import os.path, os, sys, time, socket, commands

api = None
try:
    sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
    from ScriptMonitorPythonApi import ScriptMonitorPythonApi
    api = ScriptMonitorPythonApi(sys.argv)
except Exception, emsg:
    sys.exit()

TIMEOUT = 45

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
        pass

def executeCommand(cmd, args=[], ignoreOnError=True):
    for arg in args:
        cmd = cmd + ' ' + str(arg)
    try:
            result = commands.getstatusoutput(cmd)
    except Exception, errmsg:
        return 1, 'Exception caught - ' + str(errmsg)

    if result[0] != 0 and ignoreOnError == False:
        raise Exception("Failed to execute command: " + cmd)
    return result[0] >> 8 , result[1]
    
def is_valid_ipv4_address(address):
    try:
        socket.inet_pton(socket.AF_INET, address)
    except AttributeError:  # no inet_pton here, sorry
        try:
            socket.inet_aton(address)
        except socket.error:
            return False
        return address.count('.') == 3
    except socket.error:  # not a valid address
        return False

    return True

def is_valid_ipv6_address(address):
    try:
        socket.inet_pton(socket.AF_INET6, address)
    except socket.error:  # not a valid address
        return False
    return True

def checkServerConnectivity(host, port):
    try:
        response_time = 0
        state = 0
        if not host:
            return False, "NA", state, response_time
        
        start = time.time()
        if is_valid_ipv6_address(host):
            conn = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        else:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    
        conn.settimeout(TIMEOUT)
        try:
            conn.connect((host, int(port)))
        except socket.error, errmsg:
            conn.close()
            return False, errmsg, state, response_time

        response_time = (time.time() - start)*1000
        state = 1
        conn.close()
        del conn
        
        return True, "Successfully Connected.", state, response_time
    except Exception, errmsg:
        return False, errmsg, state, response_time

monitor_names = api.metricNames
metrics = api.metrics
warning_thres = api.warnings
critical_thres = api.criticals
do_alerts = api.doAlerts
user_params = api.userParams

print "<DataValues>"
perfdataOutput = ""
for i in range(0, len(api.metricNames)):
    monitor_name = monitor_names[i]
    metric_name = metrics[i]
    warn_thresh = warning_thres[i]
    crit_thresh = critical_thres[i]
    param_list = user_params[i]
    do_alert = do_alerts[i]
    
    try:
        if param_list != "":
            host_port_list = param_list.split(",")
            for host_port in host_port_list:
                port_list = host_port.split("-")
                host = port_list[0].strip()
                port = port_list[1].strip()
               
                IP = host.replace("/", "_")
                state_file  = '/opt/vistara/agent/tmp/%s_%s_%s_state.txt' % (monitor_name, IP, port)

                status, check_result, state, resp_time = checkServerConnectivity(host, port)
                mon_state = 'Ok'
                old_state = readState(state_file)
                alert_sub = "Successfully connected to %s on %s port." % (host, port)
                alert_desc = alert_sub + " " + str(check_result)
        
                if not status:
                    alert_sub = "Failed to connect to %s on %s port" % (host, port)
                    alert_desc = alert_sub + " " + str(check_result)
                    mon_state = 'Critical'

                if str(do_alert) == "1":
                    if old_state != mon_state:
                        alert_group = monitor_name + "_" + host + "_" + port
                        api.sendAlertMsg(monitor=metric_name, subject=alert_sub, description=alert_desc, newState=mon_state, oldState=old_state, alertGroup=alert_group, alertType=None, alertTime=None)
                        saveState(state_file, mon_state)

                if perfdataOutput != "":
                    perfdataOutput += ", "
                            
                perfdataOutput +=  '%s_%s=%s' % (host,port,str(resp_time))

            print "<Monitor name='%s' output='%s'></Monitor>" % (monitor_name, perfdataOutput)
    except Exception as e:
        mon_state = "Critical"
        alert_sub = mon_state + ": " + str(e)
        alert_desc = alert_sub
        metric_value = 0

        if str(do_alert) == "1":
            state_file = "/opt/vistara/agent/tmp/%s_%s.txt" % (monitor_name,metric_name)
            old_state = readState(state_file)
            
            if old_state != mon_state:
                alert_group = monitor_name + "_" + metric_name
                api.sendAlertMsg(monitor=metric_name, subject=alert_sub, description=alert_desc, newState=mon_state, oldState=old_state, alertGroup=alert_group, alertType=None, alertTime=None)
                saveState(state_file, mon_state)

print "</DataValues>"
sys.exit(0)
