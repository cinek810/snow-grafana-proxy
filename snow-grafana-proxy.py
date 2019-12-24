#!/usr/bin/python

import requests
import json
import time
import logging
import signal

from jinja2 import Template
from http.server import BaseHTTPRequestHandler, HTTPServer


def shutdown(signum, frame):  # signum and frame are mandatory
    sys.exit(0)


def run(handler_class, server_class=HTTPServer, port=8095, address='127.0.0.1', foreground=False):
    server_address = (address, port)
    httpd = server_class(server_address, handler_class)
    logging.info("Starting grafana simple json to snow proxy server")
    httpd.serve_forever()


def MakeSnowRequestHandler(snowParams):
    class SnowRequestsHandler(BaseHTTPRequestHandler, object):
        get_attr_by_link_cache = {}
        lastQueryReply = {}

        def __init__(self, *args, **kwargs):  # url, snowAuth, snowFilter):
            self.snowUrl = snowParams["instance"]["url"]
            self.snowAuth = (snowParams["instance"]["user"], snowParams["instance"]["password"])
            # by default verify SSL
            self.snowVerifySsl = snowParams["instance"].get("verifySSL", True)
            self.queries = snowParams["queries"]
            for k, v in self.queries.items():
                self.lastQueryReply[k] = dict(time=0)
            super(SnowRequestsHandler, self).__init__(*args, **kwargs)

        def _set_headers(self):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

        def _get_attr_by_link(self, attribute, interParams):
            snow = requests.Session()
            snow.headers.update({"Accept": "application/json"})
            snow.auth = self.snowAuth

            try:
                link = attribute["link"]
            except Exception:
                try:
                    returnValue = interParams["default"]
                    logging.warning("Unable to get link. If it happens for all requests, this may mean that "
                                    "you're using incorrect interpreter for this attribute. "
                                    "Returning default value.: %s", returnValue)
                    return returnValue
                except Exception:
                    raise ValueError("Check your configuration of interpreterParameters. "
                                     "It should contain default value")
            try:
                attr = interParams["linkAttribute"]
            except Exception:
                raise ValueError("Check your configuration of intepreterParameters. "
                                 "linkAttribute is missing or corrupted")

            try:
                returnValue = self.get_attr_by_link_cache[link][attr]
            except KeyError:
                logging.debug("Link missing in cache. I have: %s", self.get_attr_by_link_cache)
                try:
                    r = snow.get(attribute["link"])
                    logging.debug("_get_person_by_name: Results from: '%s' show: %s",
                                  attribute, json.dumps(r.json(), indent=4))
                    resultJSON = r.json()
                    returnValue = resultJSON["result"][attr]
                except KeyError as e:
                    try:
                        logging.warning("Using default value for mapping, error %s. Attribute was=%s", e, attribute)
                        returnValue = interParams["default"]
                    except KeyError:
                        raise ValueError("Check your configuration interpreterParameters should contain default value")

            temp = {}
            temp[attr] = returnValue
            self.get_attr_by_link_cache[link] = temp

            return returnValue

        def __get_row(self, attributes, dataRow):
            resultRow = []
            for attribute in attributes:
                if attribute["interpreter"] == "none":
                    toAdd = dataRow[attribute["name"]]
                elif attribute["interpreter"] == "object_attr_by_link":
                    toAdd = self._get_attr_by_link(dataRow[attribute["name"]], attribute["interpreterParams"])
                elif attribute["interpreter"] == "map":
                    toAdd = attribute["map"].get(dataRow[attribute["name"]], attribute["name"])
                else:
                    raise ValueError('Unsupported interpreter %s' % attribute["interpreter"])
                resultRow.append(toAdd)
            return resultRow

        def do_GET(self):
            logging.info("GET %s", self.path)

            if self.path == "/":
                self._set_headers()
                logging.info("Send ping reply")

        def do_POST(self):
            logging.info("POST %s", self.path)
            content_len = int(self.headers.get('content-length', 0))
            received = self.rfile.read(content_len)
            received = json.loads(received)
            logging.debug("Client send: %s", json.dumps(received, indent=4))
            if self.path == '/annotation':
                self._set_headers()
                try:
                    rjson = json.loads(received)
                    annoReply = json.dumps([{
                        'annotation': rjson["annotation"]["name"],
                        'time': '0',
                        'title': 'Snow title'
                    }])
                    self.wfile.write(annoReply.encode("utf-8"))
                except ValueError:
                    logging.warning("Received incorrect json")

            elif self.path == "/search":
                response = []
                for k, v in self.queries.items():
                    response.append(k)
                self._set_headers()
                self.wfile.write(json.dumps(response).encode("utf-8"))
                logging.debug("Service reply is: %s", json.dumps(response))

            elif self.path == '/query':
                target_name = received["targets"][0]["target"]
                target_type = received["targets"][0]["type"]
                target = self.queries[target_name]
                logging.debug("My query target is: %s", target)

                self._set_headers()

                grafana_variables = {}
                scoped_vars = received.get('scopedVars', {})
                for var in scoped_vars:
                    grafana_variables[var] = scoped_vars[var]['value']
                snowFilter = Template(target['snowFilter']).render(**grafana_variables)
                logging.debug("My snow filter is: %s", snowFilter)

                queryReply = [{}]
                if (snowFilter in self.lastQueryReply and
                        (time.time() - self.lastQueryReply[snowFilter]['time'] < target['cacheTime'])):
                    cache_age = time.time() - self.lastQueryReply[snowFilter]['time']
                    logging.debug('Found filter in cache - %s seconds old' % cache_age)
                    items = self.lastQueryReply[snowFilter]['response']
                else:
                    # cache is too old - do new request to service-now
                    snow = requests.Session()
                    snow.headers.update({"Accept": "application/json"})
                    snow.verify = self.snowVerifySsl
                    snow.auth = self.snowAuth

                    logging.info("Starting request to service-now, to %s/api/now/table/%s params=%s",
                                 self.snowUrl, target["table"], snowFilter)
                    r = snow.get("%s/api/now/table/%s" % (self.snowUrl, target["table"]),
                                 params=snowFilter)

                    items = r.json()
                    self.lastQueryReply[snowFilter] = {
                        'time': time.time(),
                        'response': items
                    }

                    if r.status_code == 401:
                        logging.error("Unauthorized request to service-now instance - check user and password")
                        return
                    elif r.text == "":
                        logging.warning("Empty reply from service-now instance")
                        return
                    elif r.status_code == 400:
                        logging.error("Bad request, service-now returned: %s", items["error"]["message"])
                        return
                    # ---------------- Request to service-now done ----------------
                    logging.debug("Service-now returned %s message in json format: %s",
                                  r.status_code, json.dumps(items, indent=4, sort_keys=True))

                # queryReply[0]["columns"]=[
                #     {"text": "Number", "type": "string"},
                #     {"text": "Short description", "type": "string"},
                #     {"text": "Last update by", "type": "string"}
                # ]
                queryReply[0]["columns"] = []
                for attr in target["attributes"]:
                    queryReply[0]["columns"].append({"text": attr["displayName"], "type": "string"})
                queryReply[0]["rows"] = []
                for row in items["result"]:
                    oneResultRow = self.__get_row(target["attributes"], row)
                    queryReply[0]["rows"].append(oneResultRow)

                # set table/timeseries as per query - not cached
                queryReply[0]["type"] = target_type

                # for timeseries convert to single record with count of rows timestamped as now
                if target_type == "timeseries":
                    queryReply[0]["target"] = target_name
                    # convert now to ns precision
                    queryReply[0]["datapoints"] = [[len(queryReply[0]["rows"]), time.time() * 1000]]
                    # save some bandwidth - delete unnecessary data
                    del queryReply[0]["columns"]
                    del queryReply[0]["rows"]

                # prepare data - convert python object to json
                queryReply = json.dumps(queryReply)

                logging.debug("Reply to grafana: %s", queryReply)
                self.wfile.write(queryReply.encode("utf-8"))

    return SnowRequestsHandler


if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser(description='Simple JSON data source for grafana retreving data from service-now')
    parser.add_argument('-c', '--configFile',
                        help='Configuration file to use',
                        dest='configFile',
                        default='/etc/snow-grafana-proxy.conf')
    parser.add_argument('-d', '--debug',
                        help='Start in foreground and print all logs to stdout',
                        action='store_true',
                        dest='debugMode')

    args = parser.parse_args()

    import yaml
    import sys
    with open(args.configFile) as configStream:
        config = yaml.load(configStream)

    port = int(config['service']['port'])
    if args.debugMode:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
        logging.info("My loglevel is: %s", config['service']['loglevel'])
        run(port=int(config['service']['port']),
            address=config['service']['address'],
            handler_class=MakeSnowRequestHandler(config['service-now']))
    else:
        logging.basicConfig(filename=config['service']['logfile'],
                            level=getattr(logging, config['service']['loglevel'].upper()))
        logging.info("My loglevel is: %s", config['service']['loglevel'])
        import daemon
        print("Starting in daemon mode...")
        with daemon.DaemonContext(signal_map={signal.SIGTERM: shutdown, signal.SIGTSTP: shutdown}):
            run(port=int(config['service']['port']),
                address=config['service']['address'],
                handler_class=MakeSnowRequestHandler(config['service-now']))

    logging.shutdown()
