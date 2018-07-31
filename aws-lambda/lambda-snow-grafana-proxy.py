#!/usr/bin/python36
#from botocore.vendored import requests
import requests
import json
import logging

queries={ "get_my_incidents": 
   { "table": "incident", 
     "snowFilter": "sysparam_query=active=true^incident_stateNOT IN 6,7,8", 
     "attributes": [ 
	{ "name": "assigned_to", "displayName": "Assigned to", "interpreter": "object_attr_by_link", "interpreterParams": { "linkAttribute": "name", "default": "FailedToGetName" } } , 
        { "name": "number", "displayName": "Number", "interpreter": "none" } 
     ] 
   } 
}

snowAuth=(("admin","pass"))
snowUrl="https://dev67310.service-now.com/"

#def _set_headers(self):
#	self.send_response(200)
#	self.send_header('Content-type','application/json')
#	self.end_headers()

def _get_attr_by_link(attribute,interParams):
	get_attr_by_link_cache={}
	snow=requests.Session()
	snow.headers.update({"Accept": "application/json"})
	snow.auth=snowAuth

	try:
		link=attribute["link"]
	except:
		try:
			returnValue=interParams["default"]
			logging.warning("Unable to get link. If it happens for all requests, this may mean that you're using incorrect interpreter for this attribute. Returning default value.: "+str(attribute))
			return returnValue
		except:
			raise ValueError("Check your configuration of interpreterParameters. It should contain default value")
	try:
		attr=interParams["linkAttribute"]
	except:
		raise ValueError("Check your configuration of intepreterParameters. linkAttribute is missing or corrupted")

	try:
		returnValue=get_attr_by_link_cache[link][attr]
	except KeyError:
		logging.debug("Link missing in cache. I have:"+str(get_attr_by_link_cache))
		try:
			r=snow.get(attribute["link"])
			logging.debug("_get_person_by_name: Results from: '"+str(attribute)+"' show:"+str(json.dumps(r.json(),indent=4)));
			resultJSON=r.json()
			returnValue=resultJSON["result"][attr]
		except KeyError as e:
			try:
				logging.warning("Using default value for mapping, error"+str(e)+". Attribute was="+str(attribute))
				returnValue=interParams["default"]
			except KeyError:
				raise ValueError("Check your configuration interpreterParameters should contain default value")

	temp={}
	temp[attr]=returnValue
	get_attr_by_link_cache[link]=temp
	
	return returnValue

def __get_row(attributes,dataRow):
	resultRow=[]
	for attribute in attributes:
		if attribute["interpreter"] == "none":
			toAdd=dataRow[attribute["name"]]
		elif attribute["interpreter"] == "object_attr_by_link":
			toAdd=_get_attr_by_link(dataRow[attribute["name"]],attribute["interpreterParams"]);
		elif attribute["interpreter"] == "map":
			toAdd=attribute["map"][dataRow[attribute["name"]]]
		else:
			raise ValueError('Unsupported interpreter '+str(attribute["interpreter"]))
		resultRow.append(toAdd)
	return resultRow


def ping_get(event,context):
	logging.info("Send ping reply")
	return

def annotation_post(event,context):
	annoReply='[{"annotation:": '+rjson["annotation"]["name"]+', "time": "0", "title": "Snow title"}]'
	return annoReply

def search_post(event,context):
	response=[]
	for k,v in queries.items():
		response.append(k)
	return response

def query_post(received,context):	
	target_name=received["targets"][0]["target"]
	target=queries[target_name]
	logging.debug("My query target is:"+str(target))

	snow = requests.Session()
	snow.headers.update({"Accept": "application/json" })
	snow.auth=snowAuth
	logging.debug("My snow filter is:"+target["snowFilter"])

	snow.verify=False
	logging.info("Starting request to service-now, to "+str(snowUrl+"//api/now/table/"+target["table"]+" params="+target["snowFilter"]))
	r=snow.get(snowUrl+"//api/now/table/"+target["table"],params=target["snowFilter"])
	items=r.json()


	if r.status_code == 401:
		logging.error("Unauthorized request to service-now instance - check user and password")
		return
	elif r.text == "":
		logging.warning("Empty reply from service-now instance")
		return
	elif r.status_code == 400:
		logging.error("Bad request, service-now returned:"+items["error"]["message"])
		return



	logging.debug("Service-now returned "+ str(r.status_code)+" message in json format:"+json.dumps(items,indent=4,sort_keys=True))

	#For instance
	#queryReply[0]["columns"]=[{"text": "Number", "type": "string"}, {"text": "Short description", "type": "string"},{"text": "Last update by", "type": "string"}]
	queryReply=[ 0 ]
	queryReply[0]= { "columns": [] }
	for attr in target["attributes"]:
		queryReply[0]["columns"].append({"text": attr["displayName"], "type": "string"})
	queryReply[0]["rows"]=[]
	for row in items["result"]:
		oneResultRow=__get_row(target["attributes"],row)
		queryReply[0]["rows"].append(oneResultRow)
		
	queryReply[0]["type"]="table"
	return queryReply


if __name__ == "__main__":
	#Test search_post
	event={}
	context=[]
	print("Testin search_post function")
	result=search_post(event,context)
	print(result)


	print("Testing query_post function")
	query_json={ "targets": [ {"target": "get_my_incidents"} ]}
	result=query_post(query_json,context)
	print(result)
