#!/usr/bin/python

import requests
import json
import re
import time
import calendar

from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer

def MakeSnowRequestHandler(url,snowAuth,snowFilter):
	class SnowRequestsHandler(BaseHTTPRequestHandler,object):
		knownUsers={}
		lastQueryReply=[0,[]]
	        
		def __init__(self,*args,**kwargs): #url, snowAuth,snowFilter):
			self.snowUrl=url	
			self.snowAuth=snowAuth
			self.snowFilter=snowFilter
			super(SnowRequestsHandler, self).__init__(*args,**kwargs)

	
		def _set_headers(self):
			self.send_response(200)
			self.send_header('Content-type','application/json')
			self.end_headers()

		def _get_person_by_link(self,link):
			snow=requests.Session()
			snow.headers.update({"Accept": "application/json"})
			snow.auth.self.snowAuth
			r=snow.get(link)
			
			person=r.json()
			return person["result"]

		def do_GET(self):
			print("GET"+slef.path)

			if self.path=="/":
				self._set_headers()
				print("Send ping reply")
		

		def do_POST(self):
			print("POST"+self.path);
			content_len=int(self.headers.getheader('content-length',0))
			received=self.rfile.read(content_len)
			received=json.loads(received)
			print("Client send: "+str(json.dumps(received,indent=4)))
			if self.path=='/annotation':
				self._set_headers()
				try:
					rjson=json.loads(received)
					annoReply='[{"annotation:": '+rjson["annotation"]["name"]+', "time": "0", "title": "Snow title"}]'
					self.wfile.write(annoReply)
				except ValueError:
					print("Received incorrect json")	
			elif self.path=="/search":

				response=["SELECT incident_number,assigned_to_last_name FROM incidents where incident_state not in 6,7,8"]
				self._set_headers()
				self.wfile.write(json.dumps(response));

			elif self.path=='/query':

				incidents_description= { "1": "New" , "2": "Assigned", "12": "Referred", "4": "Await User", "5": "Await Evidance", "10": "Await Change", "8": "Await Vendor", "11": "Await Vendor Change", "6": "Resolved", "7": "Closed"}
				self._set_headers()

				
				now=calendar.timegm(time.gmtime())
				queryReply=[{}]
				if (now - self.lastQueryReply[0] > 60):
					url = 'https://delphi.service-now.com//api/now/table/incident' 
					#data = (("assignment_group","10a440771322a2c0929930ded144b022"),("incident_state", "2"))

#Do request to service-now
					snow = requests.Session()
					snow.headers.update({"Accept": "application/json" })
					snow.auth=self.snowAuth
					print(self.snowFilter)

					snow.verify=False
					r=snow.get(self.snowUrl+"//api/now/table/incident",params=self.snowFilter)

					incidents=r.json()

		
					
					print(json.dumps(incidents["result"],indent=4,sort_keys=True))
					#queryReply[0]["columns"]=[{"text": "Number", "type": "string"}, {"text": "Short description", "type": "string"},{"text": "Last update by", "type": "string"}]
					queryReply[0]["columns"]=[{"text": "Number", "type": "string"}, {"text": "Assigned to", "type": "string"}, { "text": "Incident state", "type": "string"}]
					queryReply[0]["rows"]=[]
					for incident in incidents["result"]:
						try:			
						
							if(incident["assigned_to"]==""):
								queryReply[0]["rows"].append([ incident["number"], "unassigned" , incidents_description[incident["incident_state"]]] )
							else:
								queryReply[0]["rows"].append([ incident["number"],  self.knownUsers[incident["assigned_to"]["value"]] , incidents_description[incident["incident_state"]]])

						except KeyError:
							self.knownUsers[incident["assigned_to"]["value"]]=self._get_person_by_link(incident["assigned_to"]["link"])["last_name"]
							print("User added to my cache")
							queryReply[0]["rows"].append([ incident["number"],  self.knownUsers[incident["assigned_to"]["value"]], incidents_description[incident["incident_state"]]])
					
					queryReply[0]["type"]="table"
					self.lastQueryReply[1]=queryReply
					self.lastQueryReply[0]=now
				else:
					queryReply=self.lastQueryReply[1]
					cacheAge=now - self.lastQueryReply[0]
					print("Reply from cache - "+str(cacheAge)+" seconds old")

				print(queryReply)
	#			queryReply='[{ "columns": [{"text": "Number", "type": "string"}, {"text": "Short description", "type": "string"}], "rows": ['
	#			for incident in incidents["result"]:
	#				queryReply=queryReply+'["'+incident["number"]+'", "'+re.escape(incident["short_description"])+'"]'
	#				break
	#			queryReply=queryReply+'], "type": "table"}]'
	#			print("Sending"+queryReply)

				
					
				self.wfile.write(json.dumps(queryReply))

	return SnowRequestsHandler				
			
		#	self.wfile.write(incidents["result"])


def run( handler_class, server_class=HTTPServer,port=8095,address='127.0.0.1'):
	server_address = (address,port)
	httpd= server_class(server_address,handler_class)
	print("Starting grafana simple json to snow proxy server")
	httpd.serve_forever()


if __name__ == "__main__":
	import configparser
	config=configparser.ConfigParser()
	config.read('/etc/snow-grafana-proxy.conf')
	port=int(config['service']['port'])
	
	run(port=int(config['service']['port']),address=config['service']['address'],handler_class=MakeSnowRequestHandler(url=config['service-now']['url'],snowAuth=(config['service-now']['user'],config['service-now']['password']),snowFilter=config['service-now']['filter']) )






 #curl -G --data-urlencode "assignment_group=10a440771322a2c0929930ded144b022" --header 'Accept: "application/json"' --user http://delphi.service-now.com/api/now/table/incident  > /tmp/allIncident



