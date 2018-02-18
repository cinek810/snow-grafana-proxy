# snow-grafana-proxy

![Connections schema](https://raw.githubusercontent.com/cinek810/snow-grafana-proxy/master/docs/grafana-snow-proxy.svg?sanitize=true)

This is a proxy-like service translating [grafana simplejson](https://github.com/grafana/simple-json-datasource)  data source calls into calls to [ServiceNow](https://www.servicenow.com/) REST API getting the items from incident table. Effectively allowing allowing integration of grafana dashboard with ServiceNow.  

Configuration file is preatty self-explanatory. You just have to give the details like your ServiceNow instance URL, user and password allowed to access ServiceNow API and adjust the filter. If you your goal is to get information about incidents beeing "in-progress" in your assignemnt group just adjust the filter with appropriate value instead of "YOURASSIGNEMNTGROUP" used in the example snow-grafana-proxy.conf 

