import requests
import sys
import socket


# returns the ip of current machine
def get_ip():
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)


self_ip = get_ip()

# here defines the target metrics we wanna check for each role
# role metrics are define as follow:
# each key is the alert name, and value associated with the given key is a dictionary of warning level and pql

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
        'pql': 'probe_success{group="Node_exporter",instance=~"%s.*"} == 0' % self_ip
    },
}


# split the input prometheus ip by ","
def split_prome_ips(ips):
    number_of_ip = len(ips.split(","))
    prometheus_ip = ips.split(",")
    return number_of_ip, prometheus_ip


# send given prometheus query to target prometheus
# return the http response
def request_prome(prome_ip, query):
    print('http://%s/api/v1/query' % prome_ip)
    return requests.get('http://%s/api/v1/query' % prome_ip, params={'query': query})


# check if sending the given query to target prometheus will return result
def has_response(prome_ip, query):
    response = request_prome(prome_ip, query)
    try:
        if response.json()["data"]['result']:
            return True
        else:
            return False
    except:
        return False


# check if the given prometheus is alive
# returns true if target is alive, false otherwise
def check_prome_alive(prome_ip):
    # dummy query is used to judge if prometheus is alive
    dummy_query = 'probe_success{}'
    return has_response(prome_ip, dummy_query)


# check_role populate role dictionary to see if it has current role
# must be sure that given prometheus is alive
def populate_tasks(prometheus_ip):
    # pqls to check role
    # note that key must be same as roles dictionary
    judge_pqls = {
        'tidb': 'probe_success{group="tidb",instance=~"%s.*"}' % self_ip,
        'tikv': 'probe_success{group="tikv",instance=~"%s.*"}' % self_ip,
        'tiflash': 'probe_success{group="tiflash",instance=~"%s.*"}' % self_ip,
        'pd': 'probe_success{group="pd",instance=~"%s.*"}' % self_ip,
    }

    tasks = []

    if has_response(prometheus_ip, judge_pqls['tidb']):
        tasks.append(TiDB_metrics)

    if has_response(prometheus_ip, judge_pqls['tikv']):
        tasks.append(TiKV_metrics)

    if has_response(prometheus_ip, judge_pqls['tiflash']):
        tasks.append(TiFlash_metrics)

    if has_response(prometheus_ip, judge_pqls['pd']):
        tasks.append(PD_metrics)

    tasks.append(Blacker_metrics)
    tasks.append(Node_exporter_metrics)

    return tasks


# return the first alive prometheus ip from the ip list
# return None if no prometheus is alive
def find_alive_prome(prome_ips):
    for prome_ip in prome_ips:
        if check_prome_alive(prome_ip):
            return prome_ip
    return None


# check metric and print out warning by send out pql to the given prometheus
def check_metric(alert_name, prometheus_ip, pql, warning_level):
    try:
        print('http://%s/api/v1/query' % prometheus_ip)
        response = request_prome(prometheus_ip, pql)
        value = 0 if response.json()["data"]['result'] == [] else 1
        print("metric=%s|value=%s|type=gauge|tags=status:%s" % (alert_name, value, warning_level))
    except:
        return


# check all metrics defined in a role dictionary
def check_role_metrics(role_metrics, prometheus_ip):
    for alert in role_metrics:
        pql = role_metrics[alert]['pql']
        warning_level = role_metrics[alert]['warning_level']
        check_metric(alert, prometheus_ip, pql, warning_level)


# ----------------------------------script starts here------------------------------------
count, prometheus_ips = split_prome_ips(sys.argv[1])
print(prometheus_ips, count)

prometheus_ip = find_alive_prome(prometheus_ips)
# check if all prometheus are down
if not prometheus_ip:
    print("metric=TiDB.prometheus.Prometheus_is_down|value=1|type=gauge|tags=status:critical")
    sys.exit()

tasks = populate_tasks(prometheus_ip)
for task in tasks:
    check_role_metrics(task, prometheus_ip)
