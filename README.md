<a href="https://scan.coverity.com/projects/cinek810-snow-grafana-proxy">
  <img alt="Coverity Scan Build Status"
       src="https://scan.coverity.com/projects/18331/badge.svg"/>
</a>

# snow-grafana-proxy

![Connections schema](https://raw.githubusercontent.com/cinek810/snow-grafana-proxy/master/docs/grafana-snow-proxy.svg?sanitize=true)

This is a proxy-like service translating [grafana simplejson](https://github.com/grafana/simple-json-datasource)  data source calls into calls to [ServiceNow](https://www.servicenow.com/) REST API getting the items from incident table. Effectively allowing allowing integration of grafana dashboard with ServiceNow.  

Configuration file is preatty self-explanatory. You just have to give the details like your ServiceNow instance URL, user and password allowed to access ServiceNow API and configure queries you'd like to make available for grafana. If you want you can find some "explanation" of those options on my blog post: https://funinit.wordpress.com/2018/07/20/integration-for-servicenow-table-api-and-grafana/

If you'd like to learn more about 1st version of snow-grafana-proxy you can check my blog post: https://funinit.wordpress.com/2018/02/20/simple-integration-of-servicenow-and-grafana/

# Runtime options
snow-grafana-proxy.py accepts two options, as explained by help:

```# ./snow-grafana-proxy.py --help
usage: snow-grafana-proxy.py [-h] [-c CONFIGFILE] [-d]

Simple JSON data source for grafana retreving data from service-now

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIGFILE, --configFile CONFIGFILE
                        Configuration file to use
  -d, --debug           Start in foreground and print all logs to stdout
```

## Commercial support and feature development

Snow grafana proxy is distributed under MIT license, however, if anyone is interested in getting a commercial support model or sponsoring a certain feature development for ServiceNow and grafana integration proxy please contact [Snow-grafana-proxy support](mailto:stolarek.marcin@gmail.com?subject=[SnowGrafanaProxySupport]%20Support%20question)

# Configuration file
Current configuration file schema is in YAML format with two basic dictionaries: "service" and "service-now". In service dictionary you define parameters of your snow-grafana-proxy service like address to bind, port, log level and file to log output. In "service-now" section we have basic parameters like service-now instance address, api user and password for simple authntication and queries dictionary. 

## Queries configuration
Each query will appear as separate option available under metrics configuration in grafana(remember to pick table time, not timeseries from the first list). Query will use service-now table API to get the information from configured table, using value of a snowFilter option as an argument allowing to filter results on snow side. snow-grafana-proxy will forward to grafana only parameters listed in attributes list. For some attributes to make them more meaningful there is a need to use an interpreter, currently supported interpreters are:

### none
Simply return value of attribute specified in "name" argumnet.

### map
Use map dictionary defined and send corresponding values assuming that service-now returned value is a key for map dictionary, 

### object_attr_by_link
Assumes that for this attribute service-now API returns value/link pair. In this case additional lookup to link is required to get really meaningful data. This interpreter requires additional parameters specified in interpreterParameters dictionary, for instance:  ```interpreterParams: { linkAttribute: "name", default: "FailedToGetName"}``` will get the value of name returned from the link from previous call in case of failure returning the value "FailedToGetName". Default value is important since sometimes the value is realy undefined - like assignemnt group for unassigned incident.

# Changelog
22-02-2019
First contributor joined the project with merge request. Thanks to @vasekch for:
 - Making the code compliant with PEP8
 - Adding verifySSL option to configuration file (instead of ignoring SSL by default)

22-08-2018
Merge of aws-lambda "subproject"

17-07-2018
beta release of second version commited. It allows much more flexible configuration, getting data from any service-now table and arbitrary set of attributes.

15-03-2018
Use logging instead of dirty print.

20-02-2018
Initial working version. 
