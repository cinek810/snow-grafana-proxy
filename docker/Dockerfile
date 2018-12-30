FROM python:2.7
RUN  git clone https://github.com/cinek810/snow-grafana-proxy
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8095

CMD /usr/local/bin/python  /snow-grafana-proxy/snow-grafana-proxy.py -d

