import os
import json
import ibmiotf.application

from statsd import StatsClient

from collections import Mapping
from itertools import chain
from operator import add

from numbers import Number

import iso8601
import base64
from bottle import Bottle, template
import urllib
import argparse
import logging
from logging.handlers import RotatingFileHandler

_FLAG_FIRST = object()

# See: http://stackoverflow.com/questions/6027558/flatten-nested-python-dictionaries-compressing-keys
def flattenDict(d, join=add, lift=lambda x:x):
	results = []
	def visit(subdict, results, partialKey):
		for k,v in subdict.items():
			newKey = lift(k) if partialKey==_FLAG_FIRST else join(partialKey,lift(k))
			if isinstance(v,Mapping):
				visit(v, results, newKey)
			else:
				results.append((newKey,v))
	visit(d, results, _FLAG_FIRST)
	return results


class Server():

	def __init__(self, args):
		# Setup logging - Generate a default rotating file log handler and stream handler
		logFileName = 'connector-cloudant.log'
		fhFormatter = logging.Formatter('%(asctime)-25s %(name)-30s ' + ' %(levelname)-7s %(message)s')
		rfh = RotatingFileHandler(logFileName, mode='a', maxBytes=26214400 , backupCount=2, encoding=None, delay=True)
		rfh.setFormatter(fhFormatter)
		
		self.logger = logging.getLogger("server")
		self.logger.addHandler(rfh)
		self.logger.setLevel(logging.DEBUG)
		
		
		self.port = int(os.getenv('VCAP_APP_PORT', '9666'))
		self.host = str(os.getenv('VCAP_APP_HOST', 'localhost'))

		if args.bluemix == True:
			# Bluemix VCAP lookups
			application = json.loads(os.getenv('VCAP_APPLICATION'))
			service = json.loads(os.getenv('VCAP_SERVICES'))
			
			# IoTF
			self.options = ibmiotf.application.ParseConfigFromBluemixVCAP()
		else:
			self.options = ibmiotf.application.ParseConfigFile(args.config)
		
		
		self.dbName = self.options['org'] + "-events"
		
		# Bottle
		self._app = Bottle()
		self._route()
		
		# Init statsd client
		self.statsdHost = "localhost"
		self.statsd = StatsClient(self.statsdHost, prefix=self.options['org'])
		
		# Init IOTF client
		self.client = ibmiotf.application.Client(self.options, logHandlers=[rfh])
	
	
	def _route(self):
		self._app.route('/', method="GET", callback=self._status)
	
	
	def myEventCallback(self, evt):
		#self.logger.info("%-33s%-30s%s" % (evt.timestamp.isoformat(), evt.device, evt.event + ": " + json.dumps(evt.data)))
		#self.logger.info(evt.data)
		
		flatData = flattenDict(evt.data, join=lambda a,b:a+'.'+b)
		
		print(flatData)
		eventNamespace = evt.deviceType +  "." + evt.deviceId + "." + evt.event
		
		self.statsd.incr(eventNamespace)
		for datapoint in flatData:
			if isinstance(datapoint[1], Number):
				self.statsd.gauge(eventNamespace + "." + datapoint[0], datapoint[1])
	
	def start(self):
		self.client.connect()
		self.client.deviceEventCallback = self.myEventCallback
		self.client.subscribeToDeviceEvents()
		self.logger.info("Serving at %s:%s" % (self.host, self.port))
		self._app.run(host=self.host, port=self.port)
	
	def stop(self):
		self.client.disconnect()
		
	def _status(self):
		return template('status', env_options=os.environ)



# Initialize the properties we need
parser = argparse.ArgumentParser()
parser.add_argument('-b', '--bluemix', required=False, action='store_true')
parser.add_argument('-c', '--config', required=False)

args, unknown = parser.parse_known_args()

server = Server(args)
server.start()