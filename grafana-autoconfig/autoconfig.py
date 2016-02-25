import sys
import requests
import json 
import time

# Supervisor will start all programs at the same time, so allow 
# 10 seconds for grafana to start up before we try to configure it
time.sleep(10)

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
