import os
import sys
import requests
import json 
import time

# Supervisor will start all programs at the same time, so allow 
# 20 seconds for grafana to start up before we try to configure it
time.sleep(20)


dashboardHome = "/opt/grafana-autoconfig/dashboards"

uri = 'http://localhost:3000/api/datasources'
r = requests.get(uri, auth=('admin', 'admin'))
if (r.status_code == 200):
	if len(r.json()) == 0:
		headers = {
			"Content-Type": "application/json;charset=UTF-8"
		}
		payload = {
			"name" : "Graphite",
			"type" : "graphite",
			"url" : "http://localhost:8000",
			"isDefault" : True,
			"access" : "proxy"
		}
		r = requests.post(uri, data=json.dumps(payload), headers=headers, auth=('admin', 'admin'))
		print(r.status_code)
		print(r.json())
	else:
		print("Datasource already registered")
else:
	# If the API didn't respond then it's likely we tried before grafana
	# was ready, supervisor will perform an auto restart with non-zero exit code
	print("Error getting datasources from %s" % uri)
	sys.exit(1)
	
uri = 'http://localhost:3000/api/dashboards/db'
for filename in os.listdir(dashboardHome):
	if filename.endswith(".json"):
		with open(os.path.join(dashboardHome, filename), "r") as dashboardFile:
			dashboardData = json.load(dashboardFile)
			
			requestData = { "dashboard": dashboardData, "overwrite": True }
			requestHeaders = {"Accept": "application/json", "Content-Type": "application/json"} 
			r = requests.post(uri, auth=('admin', 'admin'), data=json.dumps(requestData), headers=requestHeaders)
			
			# 200 - Created
			# 400 - Errors (invalid json, missing or invalid fields, etc)
			# 401 - Unauthorized
			# 412 - Precondition failed
			# The 412 status code is used when a newer dashboard already 
			# exists (newer, its version is greater than the version that was sent). 
			# The same status code is also used if another dashboard exists 
			# with the same title. The response body will look like this:
			print("%s - %s" % (filename, r.status_code))
