#!/usr/bin/python

import requests
import json
import re

from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer


class SnowRequestsHandler(BaseHTTPRequestHandler):
	knownUsers={}
	def _set_headers(self):
		self.send_response(200)
		self.send_header('Content-type','application/json')
		self.end_headers()

	def _get_person_by_link(self,link):
		snow=requests.Session()
		snow.headers.update({"Accept": "application/json"})
		snow.auth=("user","pass!")
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
			self._set_headers()

			#Do request to service-now
			snow = requests.Session()
			snow.headers.update({"Accept": "application/json" })
			snow.auth=("user","pass!") 

			url = 'https://instance.service-now.com//api/now/table/incident' 
			#data = (("assignment_group","10a440771322a2c0929930ded144b022"),("incident_state", "2"))
			filterQuery = 'sysparm_query=assignment_group=10a440771322a2c0929930ded144b022^active=true^incident_stateNOT IN 6,7,8'

			snow.verify=False
			r=snow.get(url,params=filterQuery)


			incidents=r.json()
			
			#print(json.dumps(incidents["result"],indent=4,sort_keys=True))
			queryReply=[{}]
			#queryReply[0]["columns"]=[{"text": "Number", "type": "string"}, {"text": "Short description", "type": "string"},{"text": "Last update by", "type": "string"}]
			queryReply[0]["columns"]=[{"text": "Number", "type": "string"}, {"text": "Assigned to", "type": "string"}]
			queryReply[0]["rows"]=[]
			for incident in incidents["result"]:
				try:			
				
					if(incident["assigned_to"]==""):
						queryReply[0]["rows"].append([ incident["number"], "unassigned" ] )
					else:
						queryReply[0]["rows"].append([ incident["number"],  self.knownUsers[incident["assigned_to"]["value"]]])

				except KeyError:
					self.knownUsers[incident["assigned_to"]["value"]]=self._get_person_by_link(incident["assigned_to"]["link"])["last_name"]
					print("User added to my cache")
					queryReply[0]["rows"].append([ incident["number"],  self.knownUsers[incident["assigned_to"]["value"]]])
			
			queryReply[0]["type"]="table"

			print queryReply
#			queryReply='[{ "columns": [{"text": "Number", "type": "string"}, {"text": "Short description", "type": "string"}], "rows": ['
#			for incident in incidents["result"]:
#				queryReply=queryReply+'["'+incident["number"]+'", "'+re.escape(incident["short_description"])+'"]'
#				break
#			queryReply=queryReply+'], "type": "table"}]'
#			print("Sending"+queryReply)

			
				
			self.wfile.write(json.dumps(queryReply))

			
		
	#	self.wfile.write(incidents["result"])


def run(server_class=HTTPServer, handler_class=SnowRequestsHandler,port=8095):
	server_address = ( '127.0.0.1',port)
	httpd= server_class(server_address,handler_class)
	print("Starting grafana simple json to snow proxy server")
	httpd.serve_forever()

if __name__ == "__main__":
	from sys import argv
	if len(argv)==2:
		run(port=int(argv[1]))
	else:
		run()






 #curl -G --data-urlencode "assignment_group=10a440771322a2c0929930ded144b022" --header 'Accept: "application/json"' --user http://delphi.service-now.com/api/now/table/incident  > /tmp/allIncident



