import requests
import sys
import socket


# returns the ip of current machine
def get_ip():
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)


# This should be the only global variable
self_ip = get_ip()

"""
--------------------------------------------------------------------------
target metrics for each role
role metrics are define as follow:
    each key is the alert name
    value associated with the given key is a dictionary of warning level and pql

Modify this block to add more metrics to monitor
--------------------------------------------------------------------------
"""

# PD
# Alert rules under the PD Node
PD_metrics = {
    'TiDB.blacker.PD_server_is_down': {
        'warning_level': 'critical',
        'pql': 'probe_success{group="pd",instance=~"%s.*"} == 0' % self_ip
    },
    'TiDB.pd.PD_node_restart': {
        'warning_level': 'critical',
        'pql': 'changes(process_start_time_seconds{job="pd",instance=~"%s.*"}[5m])> 0' % self_ip
    },
}

# TiDB
# Alert rules under the TiDB Node
TiDB_metrics = {
    'TiDB.blacker.TiDB_server_is_down': {
        'warning_level': 'critical',
        'pql': 'probe_success{group="tidb",instance=~"%s.*"} == 0' % self_ip
    },
    'TiDB.tidb.TiDB_node_restart': {
        'warning_level': 'critical',
        'pql': 'changes(process_start_time_seconds{job="tidb",instance=~"%s.*"}[5m])> 0' % self_ip
    },
}

# TiKV
# Alert rules under the TiKV Node
TiKV_metrics = {
    'TiDB.blacker.TiKV_server_is_down': {
        'warning_level': 'critical',
        'pql': 'probe_success{group="tikv",instance=~"%s.*"} == 0' % self_ip
    },
    'TiDB.tikv.TiKV_node_restart': {
        'warning_level': 'critical',
        'pql': 'changes(process_start_time_seconds{job="tikv",instance=~"%s.*"}[5m])> 0' % self_ip
    },
    'TiDB.tikv.TiKV_GC_can_not_work': {
        'warning_level': 'critical',
        'pql': 'increase(tikv_gcworker_gc_tasks_vec{task="gc",instance=~"%s.*"}[1d]) < 1 and increase('
               'tikv_gc_compaction_filter_perform{instance=~"%s.*"}[1d]) < 1' % (self_ip, self_ip)
    },
}

# TiFlash
# Alert rules under the TiFlash Node
TiFlash_metrics = {
    'TiDB.blacker.TiFlash_server_is_down': {
        'warning_level': 'critical',
        'pql': 'probe_success{group="tikv",instance=~"%s.*"} == 0' % self_ip
    },
    'TiDB.tiflash.TiFlash_proxy_node_restart': {
        'warning_level': 'critical',
        'pql': 'changes(process_start_time_seconds{job="tiflash",instance=~"%s.*"}[5m])> 0' % self_ip
    },
}

# Blackbox Exporter
# Alert rules under the Blackbox_exporter Node
Blacker_metrics = {
    'TiDB.blacker.Blackbox_exporter_server_is_down': {
        'warning_level': 'critical',
        'pql': 'probe_success{group="blackbox_exporter",instance=~"%s.*"} == 0' % self_ip
    },
}

# Node Exporter
# Alert rules under the Blackbox_exporter Node
Node_exporter_metrics = {
    'TiDB.blacker.Node_exporter_server_is_down': {
        'warning_level': 'critical',
        'pql': 'probe_success{group="node_exporter",instance=~"%s.*"} == 0' % self_ip
    },
}

# Grafana
# Alert rules under the Grafana node
Grafana_metrics = {
    'TiDB.blacker.Grafana_server_is_down': {
        'warning_level': 'critical',
        'pql': 'probe_success{group="grafana",instance=~"%s.*"} == 0' % self_ip
    },
}

# Prometheus
Prometheus_metrics = {
    'TiDB.prometheus.Prometheus_is_down': {
        'warning_level': 'critical',
        'pql': 'probe_success{}',
    }
}

"""
--------------------------------------------------------------------------
functions to be used by script
--------------------------------------------------------------------------
"""


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


# check_role populate role dictionary to see if it has current role
# must be sure that given prometheus is alive
def populate_tasks(prometheus_address):
    # pqls to check role
    # note that key must be same as roles dictionary
    judge_pqls = {
        'tidb': 'probe_success{group="tidb",instance=~"%s.*"}' % self_ip,
        'tikv': 'probe_success{group="tikv",instance=~"%s.*"}' % self_ip,
        'tiflash': 'probe_success{group="tiflash",instance=~"%s.*"}' % self_ip,
        'pd': 'probe_success{group="pd",instance=~"%s.*"}' % self_ip,
        'node_exporter': 'probe_success{group="node_exporter",instance=~"%s.*"}' % self_ip,
        'blackbox_exporter': 'probe_success{group="blackbox_exporter",instance=~"%s.*"}' % self_ip,
        'grafana': 'probe_success{group="grafana",instance=~"%s.*"}' % self_ip,
    }

    return_tasks = []

    if has_response(prometheus_address, judge_pqls['tidb']):
        return_tasks.append(TiDB_metrics)

    if has_response(prometheus_address, judge_pqls['tikv']):
        return_tasks.append(TiKV_metrics)

    if has_response(prometheus_address, judge_pqls['tiflash']):
        return_tasks.append(TiFlash_metrics)

    if has_response(prometheus_address, judge_pqls['pd']):
        return_tasks.append(PD_metrics)

    if has_response(prometheus_address, judge_pqls['blackbox_exporter']):
        return_tasks.append(Blacker_metrics)

    if has_response(prometheus_address, judge_pqls['node_exporter']):
        return_tasks.append(Node_exporter_metrics)

    if has_response(prometheus_address, judge_pqls['grafana']):
        return_tasks.append(Grafana_metrics)

    return return_tasks


# return the first alive prometheus ip from the ip list
# return None if no prometheus is alive
def find_alive_prome(prometheus_addresses):
    for prometheus_address in prometheus_addresses:
        if check_prome_alive(prometheus_address):
            return prometheus_address
    return None


# check metric and print out warning by send out pql to the given prometheus
def check_metric(alert_name, prometheus_address, pql, warning_level):
    try:
        response = request_prome(prometheus_address, pql)
        value = 0 if response.json()["data"]['result'] == [] else 1
        print("metric=%s|value=%s|type=gauge|tags=status:%s" % (alert_name, value, warning_level))
    except:
        return


# check all metrics defined in a role dictionary
def check_role_metrics(role_metrics, prometheus_address):
    for alert in role_metrics:
        pql = role_metrics[alert]['pql']
        warning_level = role_metrics[alert]['warning_level']
        check_metric(alert, prometheus_address, pql, warning_level)


"""
--------------------------------------------------------------------------
script starts here
note that self ip is obtained at the beginning of the script
--------------------------------------------------------------------------
"""


def run_script():
    count, prometheus_addresses = split_prome_addresses(sys.argv[1])
    print(prometheus_addresses, count)

    for prometheus_address in prometheus_addresses:
        if self_ip == prometheus_address.split(':')[0]:
            if not check_prome_alive(prometheus_address):
                print("metric=TiDB.prometheus.Prometheus_is_down|value=1|type=gauge|tags=status:critical")
            else:
                print("metric=TiDB.prometheus.Prometheus_is_down|value=0|type=gauge|tags=status:critical")

    active_prometheus_address = find_alive_prome(prometheus_addresses)

    # check if all prometheus are down
    if not active_prometheus_address:
        sys.exit()

    tasks = populate_tasks(active_prometheus_address)
    for task in tasks:
        check_role_metrics(task, active_prometheus_address)


run_script()
