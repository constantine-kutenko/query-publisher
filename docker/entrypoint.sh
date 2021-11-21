#!/bin/bash

set -e

QUERY_LOG_FILE="${QUERY_LOG_FILE:-/var/log/proxysql/queries.log.00000001}"

if [[ $1 = 'publisher' && "${INSTANCE_TYPE}" != 'mysql' ]]; then
    if [ -f "${QUERY_LOG_FILE}" ]
    then
        if [ -r "${QUERY_LOG_FILE}" ]
        then
            echo "[ INFO ] Starting Query Log Publisher..."
            exec python -u app.py
        else
            echo "[ ERROR ] Query log file is not readable. Exit."
        fi
    else
        echo "[ INFO ] Waiting for query log file for 10 seconds..."
        # Wait for 10 second and try again
        sleep 10
        if [ -f "${QUERY_LOG_FILE}" ]
        then
            echo "[ INFO ] Starting Query Log Publisher..."
            exec python -u app.py
        else
            echo "[ ERROR ] Query log file not found. Exit."
            exit 1
        fi
    fi
elif [[ $1 = "publisher" && ${INSTANCE_TYPE} == 'postgres' ]]; then
    exec python -u app.py
else
    exec $@
fi
