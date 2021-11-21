import os
import re
import sys
import time
import json
import glob
import psutil
import logging
import requests
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from datetime import datetime
from signal import signal, SIGINT
from os import walk
import queryfilter

VERSION = "0.0.1"


def handler(signal_received, frame) -> None:
    """ Handler for correct termination """
    log.warning("SIGINT or CTRL-C detected. Exiting gracefully")
    exit(0)


def tail(stream_file: object) -> None:
    """ Monitor changes in the log file and read updates at the time they happen """
    stream_file.seek(0, os.SEEK_END)
    while True:
        if stream_file.closed:
            raise StopIteration
        line = stream_file.readline()
        yield line


def parse(log_path: str, slack_webhook_url: str, instance_type: str) -> None:
    """ Read log (JSON format) """

    with open(log_path, "r") as log_file:
        for line in tail(log_file):
            try:
                log_data = json.loads(line)
            except ValueError:
                continue

            record_dict ={}
            valid_record = True

            # Parse JSON payload and return a JSON string with selected keys
            for key in log_data.keys():
                # Select necessary fields
                if key in ["starttime", "username", "query", "rows_affected"]:
                    # Parse the query string
                    if key in ["query"]:
                        # Send only queries that don't contain specific SQL keywords
                        if not any(keyword.lower() in log_data[key].lower() for keyword in queryfilter.SQL_KEYWORDS):
                            # Remove comments from query statement (everything within /* */)
                            query = re.sub('.*\*/ ', "", log_data[key])
                            query = re.sub('.*\*/', "", query)

                            # Check whether a statement starts with an unwanted word
                            if not query.lower().startswith(tuple(queryfilter.SQL_STATEMENTS)):
                                # Replace \n symbol with space in query statement
                                query = re.sub('\n', " ", query)
                                record_dict[key] = query
                            else:
                                valid_record = False
                                invalid_query = log_data[key]
                        else:
                            valid_record = False
                            invalid_query = log_data[key]
                    else:
                        record_dict[key] = log_data[key]

            if valid_record:
                # Construct payload
                payload = json.dumps({
                    "text": "*Query executed*\n\n ```" + record_dict["query"] + "```",
                    "attachments": [{
                        "fields": [{
                            "title": "Username",
                            "value": record_dict["username"],
                            "short": "true"
                        }, {
                            "title": "Rows Effected",
                            "value": str(record_dict["rows_affected"]),
                            "short": "true"
                        }, {
                            "title": "Instance type",
                            "value": instance_type,
                            "short": "true"
                        }],
                        "ts": datetime.timestamp(datetime.strptime(record_dict["starttime"], "%Y-%m-%d %H:%M:%S.%f"))
                    }]
                })

                log.debug("Slack message: %s" % payload)
                log.debug("Query: %s" % query)

                # Send logged queries to Slack
                slack_send(slack_webhook_url, payload)
            else:
                log.debug("Query (invalid): %s" % invalid_query)


def proxysql_log_file(log_dir: str, log_file_name: str) -> str:
    """ Finds and returns the latest ProxySQL query log file """

    log_files_list = []

    # Verify whether log directory exists
    if not os.path.exists(log_dir):
        log.error("Directory %s/ does not exist. Abort" % log_dir)
        exit(1)

    # Get a list of files in regards with the pattern provided
    for _, _, filenames in walk(log_dir, topdown=True):
        for file in filenames:
            if file.startswith(log_file_name):
                log_files_list.append(file)
    
    # Check if the list of files is empty
    if log_files_list == []:
        log.error("Directory %s/ contains no log files (%s) to read. Abort" % (log_dir, log_file_name))
        exit(1)
    else:
        # Sort the list to find the biggest number of all log files
        log_files_list.sort()
        return log_dir + '/' + log_files_list[-1]


def slack_send(slack_webhook_url: str, payload: str) -> tuple:
    """ Sends notification to Slack """

    # Send message as a JSON string
    try:
        response = requests.post(
            slack_webhook_url,
            headers={'Content-Type': 'application/json', 'Accept-Charset': 'UTF-8'},
            data=payload
        )
    except requests.exceptions.ConnectionError as err:
        log.error("Connection error: %s" % err)
    except requests.exceptions.Timeout as err:
        log.error("Timeout occurred: %s" % err)
    except requests.exceptions.HTTPError as err:
        log.error("HTTP error occurred: %s" % err)
    else:
        # Return HTTP status code and description for further analysis
        return response.status_code, response.text


def restart_proc():
    """Restarts the main process"""

    try:
        p = psutil.Process(os.getpid())
    except Exception as error:
        log.error(error)

    python = sys.executable
    os.execl(python, python, *sys.argv)


def on_created(event):
    """Handles event for creating new files"""
    log.info("New logfile %s has been created. Restarting the application" % event.src_path)
    restart_proc()


def main():
    # Define variables
    slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    query_log_file = os.getenv('QUERY_LOG_FILE', '/var/log/proxysql/queries.log')
    instance_type = os.getenv('INSTANCE_TYPE')
    log_level = os.getenv('LOG_LEVEL', 'info') # info, debug

    if log_level == '' or log_level not in ('info', 'debug'):
        log_level = 'info'

    global log
    log = logging.getLogger('stdout')
    logging.basicConfig(format='%(asctime)s [ %(levelname)s ] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    log.setLevel(getattr(logging, log_level.upper()))

    if not slack_webhook_url:
        log.error("A mandatory environment variable is not defined: SLACK_WEBHOOK_URL")
        sys.exit(1)

    if instance_type == 'mysql':
        instance_type = 'MySQL'
        # For ProxySQL/MySQL the latest log file must be determined

        # Parse path to log files
        log_dir = os.path.dirname(query_log_file)
        log_file_name = os.path.basename(query_log_file)

        query_log_file = proxysql_log_file(log_dir, log_file_name)

        # Watchdog
        watchdog_patterns = ["*"]
        ignore_patterns = None
        ignore_directories = True
        case_sensitive = True
        watchdog_event_handler = PatternMatchingEventHandler(watchdog_patterns, ignore_patterns, ignore_directories, case_sensitive)
        watchdog_event_handler.on_created = on_created

        # Observer
        watchdog_path = log_dir
        watchdog_observer = Observer()
        watchdog_observer.schedule(watchdog_event_handler, watchdog_path, recursive=False)
        watchdog_observer.start()
        log.info("Started watchdog for %s" % (watchdog_path))

    elif instance_type == 'postgres':
        instance_type = 'PostgreSQL'
    elif instance_type == '':
        log.error("A mandatory environment variable is not defined: INSTANCE_TYPE")
        sys.exit(1)
    else:
        log.error("A mandatory environment variable is not defined: INSTANCE_TYPE")
        sys.exit(1)

    log.info("Starting Query Log Publisher v%s. Press CTRL-C to exit" % VERSION)
    log.info("Queries are read from %s" % query_log_file)
    log.info("Log level: %s" % log_level.upper())
    log.info("Log format: %s" % instance_type)

    signal(SIGINT, handler)

    while True:
       parse(query_log_file, slack_webhook_url, instance_type)


if __name__ == "__main__":
    main()
