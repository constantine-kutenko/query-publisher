# ProxySQL Query Log Publisher (`query-publisher`)

## Overview

ProxySQL Query Log Publisher is a Python 3 application that publishes SQL queries to a Slack channel.

## Purpose

The image is used to provide information on which queries are run against production databases and can work along with [Postgres Relay](https://github.com/constantine-kutenko/postgresrelay). The application constantly reads the ProxySQL query log file, filters its records removing those don't fit requirements and publishes users' queries to an arbitrary private Slack channel.

## Requirements

The application to be built and run requires Docker - a containerization platform. Check [upstream documentation](https://docs.docker.com/install) for how to install Docker on your system.
The application works with JSON formatted log files created by [ProxySQL](https://github.com/sysown/proxysql).

## Building

To build an image run following command in application root path:

```bash
docker build \
    --pull \
    --tag query-publisher:0.0.1 \
    -f Dockerfile .
```

To run the image use:

```bash
docker run \
    --rm \
    --name query-publisher \
    --hostname query-publisher \
    -e VERBOSITY="false" \
    -e DEBUG="false" \
    -e QUERY_LOG_FILE=/var/log/proxysql/queries.log.00000001 \
    -e SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX \
    -v ${PWD}/logs/:/var/log/proxysql/ \
    -it query-publisher:0.0.1
```

## Environment variables

Environment variables is the main mechanism of manipulating application settings inside a container.

| Variable | Default value | Description |
| ----------------- | ------------- | ----------- |
| VERBOSITY | false | Defines if queries go to stdout |
| DEBUG | false | Defines if invalid queries go to stdout |
| QUERY_LOG_FILE | /var/log/proxysql/queries.log.00000001 | Specifies the path to the ProxySQL query log file |
| SLACK_WEBHOOK_URL | Null | Specifies a Slack application endpoint URL in the following format: https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX |
| INSTANCE_TYPE | null | Specifies the database instance type. Can take the following values: `mysql` or `postgres` |
