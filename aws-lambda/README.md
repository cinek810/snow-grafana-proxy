# AWS Lambda version of snow-grafana-proxy

This version is really simplified, the configuration is hardcoded so you have to build your own Lambda package before publishing/using it. If you have any interest in making it more comfortable - let me know or (preferable) create a merge request with appropriate changes. If your ServiceNow instance replies to API reuqests slowly AWS Lambda may not be the best choice for you - _you'll pay for execution time wich includes the time you'll wait for SerciceNow replies._

## How to make it running
### Update configuration 
This is simply easy - on top of lambda-snow-grafana-proxy.py you'll see:
'''
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
'''
queries is a dictionary defining query names - each query will be displayed as separate option available for grafana as a search. Configuration follows the same scheme as for the full version - please check docs there. 
snowAuth and snowUrl are pretty much self-explanatory, those are ServiceNow user credentials used to connect to snow and instance address.
####Test locally
Simply execute: ''' ./lambda-snow-grafana-proxy.py''' if you have requiremenst installed it should print JSON replies from service-now. Query may takie some time... from my experience it may take some time to get ServiceNow reply.
###Build
I recommend building AWS Lambda package with virtualenv, a commands I used are:
'''
git clone snow-grafana-proxy
cd snow-grafana-proxy/aws-lambda
virtualenv -p /usr/bin/python36 venv
source ./venv/bin/activate
pip install logging
pip install requests
pip install json
cd venv/lib/python3.6/site-packages/
zip -r9 ~/lambda-snow-grafana-proxy.zip .
cd -
zip -g ~/lambda-snow-grafana-proxy.zip lambda-snow-grafana-proxy.py 
'''
I everything finished successfully you should have lambda-snow-grafana-proxy.zip package in your $HOME directory
###Creating AWS Lambda functions
You need to configure awscli and have "basicLambdaRole" created first
'''
cd ~ 
aws lambda create-function --function-name search_post --runtime python3.6 --role arn:aws:iam::039238228955:role/basicLambdaRole --handler lambda-snow-grafana-proxy.search_post --zip-file fileb://lambda-snow-grafana-proxy.zip
aws lambda create-function --function-name query_post --timeout 30 --runtime python3.6 --role arn:aws:iam::039238228955:role/basicLambdaRole --handler lambda-snow-grafana-proxy.query_post --zip-file fileb://lambda-snow-grafana-proxy.zip
'''
###Test with dummy invoke
'''
#aws lambda invoke --function-name search_post out
cat out
aws lambda invoke --function-name query_post --payload '{"targets": [ {"target": "get_my_incidents" } ] }' out
cat out
'''
