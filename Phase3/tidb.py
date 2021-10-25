import requests
import sys
import socket


# returns the ip of current machine
def get_ip():
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)


# This should be the only global variable
self_ip = get_ip()

tasks = {
    # phase 1
    'TiDB.tidb.TiDB_server_is_down': {
        'warning_level': 'critical',
        'pql': 'probe_success{group="tidb",instance=~"%s.*"} == 0' % self_ip,
        'is_value': False
    },
    'TiDB.tidb.TiDB_node_restart': {
        'warning_level': 'critical',
        'pql': 'changes(process_start_time_seconds{job="tidb",instance=~"%s.*"}[5m])> 0' % self_ip,
        'is_value': False
    },

    # Phase 2
    'TiDB.tidb.TiDB_schema_error': {
        'warning_level': 'emergency',
        'pql': 'increase(tidb_session_schema_lease_error_total{type="outdated",instance=~"%s.*"}[5m])> 0' % self_ip,
        'is_value': False
    },
    'TiDB.tidb.TiDB_monitor_keep_alive': {
        'warning_level': 'emergency',
        'pql': 'increase(tidb_monitor_keep_alive_total{job="tidb",instance=~"%s.*"}[10m]) < 100' % self_ip,
        'is_value': False
    },
    'TiDB.tidb.TiDB_monitor_time_jump_back_error': {
        'warning_level': 'warning',
        'pql': 'increase(tidb_monitor_time_jump_back_total{instance=~"%s.*"}[10m])  > 0' % self_ip,
        'is_value': False
    },
    'TiDB.tidb.TiDB_ddl_waiting_jobs': {
        'warning_level': 'warning',
        'pql': 'sum(tidb_ddl_waiting_jobs{instance=~"%s.*"})' % self_ip,
        'is_value': True
    },
    'TiDB.tidb.TiDB_server_panic_total': {
        'warning_level': 'critical',
        'pql': 'increase(tidb_server_panic_total{instance=~"%s.*"}[10m]) > 0' % self_ip,
        'is_value': False
    },
}


# split the input prometheus addresses by ","
def split_prome_addresses(addresses):
    number_of_addresses = len(addresses.split(","))
    prometheus_addresses = addresses.split(",")
    return number_of_addresses, prometheus_addresses


# send given prometheus query to target prometheus
# return the http response
# return none if failed to get response
def request_prome(prometheus_address, query):
    try:
        response = requests.get('http://%s/api/v1/query' % prometheus_address, params={'query': query})
        return response
    except:
        return None


# check if sending the given query to target prometheus will return result
def has_response(prometheus_address, query):
    response = request_prome(prometheus_address, query)
    if not response:
        return False
    try:
        if response.json()["data"]['result']:
            return True
        else:
            return False
    except:
        return False


# check if the given prometheus is alive
# returns true if target is alive, false otherwise
def check_prome_alive(prometheus_address):
    # dummy query is used to judge if prometheus is alive
    dummy_query = 'probe_success{}'
    return has_response(prometheus_address, dummy_query)


# return the first alive prometheus ip from the ip list
# return None if no prometheus is alive
def find_alive_prome(prometheus_addresses):
    for prometheus_address in prometheus_addresses:
        if check_prome_alive(prometheus_address):
            return prometheus_address
    return None


# check metric and print out warning by send out pql to the given prometheus
# when is_value is true, this will print out value of pql,
# otherwise, this will print out 1 if theres any response from the pql
def check_metric(alert_name, prometheus_address, pql, warning_level, is_value):
    try:
        response = request_prome(prometheus_address, pql)
        # if we are in value mode
        if is_value:
            result = response.json()['data']['result']
            value = 0 if len(result) == 0 else result[0]['value'][1]
        else:
            value = 0 if response.json()['data']['result'] == [] else 1
        print("metric=%s|value=%s|type=gauge|tags=status:%s" % (alert_name, value, warning_level))
    except:
        return


# check all metrics defined in a role dictionary
def run_tasks(role_metrics, prometheus_address):
    for alert in role_metrics:
        pql = role_metrics[alert]['pql']
        warning_level = role_metrics[alert]['warning_level']
        is_value = role_metrics[alert]['is_value']
        check_metric(alert, prometheus_address, pql, warning_level, is_value)


def run_script():
    # prometheus_addresses_string should be injected by outside program
    count, prometheus_addresses = split_prome_addresses(prometheus_addresses_string)
    print(prometheus_addresses, count)

    active_prometheus_address = find_alive_prome(prometheus_addresses)

    # check if all prometheus are down
    if not active_prometheus_address:
        sys.exit()

    run_tasks(tasks, active_prometheus_address)


run_script()
