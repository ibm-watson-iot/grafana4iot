# Grafana4IoT

[![Build Status](https://travis-ci.org/ibm-watson-iot/grafana4iot.svg?branch=master)](https://travis-ci.org/ibm-watson-iot/grafana4iot)


Easily hook up your IBM Watson IoT organization to Grafana to generate powerful visualizations and 
dashboards quickly and easily.  Works great in conjunction with the [Watson IoT Connector for statsd](https://github.com/ibm-watson-iot/connector-statsd).

## Usage
The easiest way to use this project is with [Docker Compose](https://www.docker.com/products/docker-compose).  The default compose file will launch a single instance of the statsd connector and grafana4iot.  Additional connectors can be deployed to bring data from multiple organizations into grafana.

```
export WIOTP_API_KEY=<your api key>
export WIOTP_API_TOKEN=<your auth token>
wget https://github.com/ibm-watson-iot/grafana4iot/blob/master/docker-compose.yml
docker-compose up
```

To update an existing instance of the service:
```
wget https://github.com/ibm-watson-iot/grafana4iot/blob/master/docker-compose.yml
docker-compose build && docker-compose up -d
```
