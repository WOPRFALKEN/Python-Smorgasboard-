import sys,re,os,json

api = None
try:
    sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
    from ScriptMonitorPythonApi import ScriptMonitorPythonApi
    api = ScriptMonitorPythonApi(sys.argv)
except Exception, emsg:
    sys.exit()

##########################################################################
#     Block for comparing thresholds. 
##########################################################################

def calculateCurrentState(value,warn,crit):
	MonState = 'OK'
	try:
	
		if value:
			value = float(value)
		else :
			value = 0.0
		warn = float(warn)
		crit = float(crit)
		if warn != crit:
			if warn < crit :
				if value >= warn and value <= crit:
					MonState = 'Warning'
				elif value >crit:
					MonState = 'Critical'
			else :
				if warn > crit :
					MonState = 'Critical'
		else:
			MonState = 'Critical'

	except Exception,emsg:
		 print "Check thresholds exception {}, {} - {}".format(warn, crit, emsg)
	return MonState


##########################################################################
#     Block for formatting the output to Agent readable format 
##########################################################################


def prepareJSONDictionary(metric, component, value, state, alert_desc) :
	__dict = {}
	__dict["metric"] = metric
	__dict["component"] = component
	__dict["value"] = value
	__dict["state"] = state
	__dict["alert_desc"] = alert_desc
	
	return __dict
	
monitor_names = api.metricNames
metrics = api.metrics
warning_thres = api.warnings
critical_thres = api.criticals
do_alerts = api.doAlerts
user_params = api.userParams
components1 = "Max Base Size Allocated"
components2 = "Swap Usage"
JSONList = []

##########################################################################
#     Block for Getting the swap memory utilization. 
##########################################################################

def Utilization():

	total, used, free = map(int, os.popen('free -t -m').readlines()[-2].split()[1:])
	total = float(total)
	used = float(used)
	free = float(free)
	util = used/total*100
	util =round(util,2)
	util = int(util)
	return util
def VirtualMemoryStats():

	total, used, free = map(int, os.popen('free -t -m').readlines()[-2].split()[1:])

	return total,used

for i in range(0, len(api.metrics)):
	monitor_name = monitor_names[i]
	metric_name = metrics[i]
	warn_thre = warning_thres[i]
	critical_thre = critical_thres[i]
	do_alert = do_alerts[i]
	result = Utilization()
	result1, result2 = VirtualMemoryStats()
	MonState = "Ok"
	MonState = calculateCurrentState(result,warn_thre,critical_thre)
	alert_desc = "Monitor State :{} ,Total swap memory Utilization is {}%".format(MonState,result)
	JSONDictionary = prepareJSONDictionary(metric_name, components1, result1, MonState, alert_desc)	 
	JSONList.append(JSONDictionary) 
	JSONDictionary = prepareJSONDictionary(metric_name, components2, result2, MonState, alert_desc)	 
	JSONList.append(JSONDictionary) 

	if i == len(metrics)-1:
		CustomScriptPayload =  json.dumps(JSONList)

print(CustomScriptPayload)
sys.exit(0)