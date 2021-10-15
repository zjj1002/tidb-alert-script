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
pd_metrics = {
    # Phase 1
    'TiDB.pd.PD_server_is_down': {
        'warning_level': 'critical',
        'pql': 'probe_success{group="pd",instance=~"%s.*"} == 0' % self_ip
    },
    'TiDB.pd.PD_node_restart': {
        'warning_level': 'critical',
        'pql': 'changes(process_start_time_seconds{job="pd",instance=~"%s.*"}[5m])> 0' % self_ip
    },
}

# TiDB
tidb_metrics = {
    # phase 1
    'TiDB.tidb.TiDB_server_is_down': {
        'warning_level': 'critical',
        'pql': 'probe_success{group="tidb",instance=~"%s.*"} == 0' % self_ip
    },
    'TiDB.tidb.TiDB_node_restart': {
        'warning_level': 'critical',
        'pql': 'changes(process_start_time_seconds{job="tidb",instance=~"%s.*"}[5m])> 0' % self_ip
    },

    # Phase 2
    'TiDB.tidb.TiDB_schema_error': {
        'warning_level': 'emergency',
        'pql': 'increase(tidb_session_schema_lease_error_total{type="outdated",instance=~"%s.*"}[5m])> 0' % self_ip
    },
    'TiDB.tidb.TiDB_monitor_keep_alive': {
        'warning_level': 'emergency',
        'pql': 'increase(tidb_monitor_keep_alive_total{job="tidb",instance=~"%s.*"}[10m]) < 100' % self_ip
    },
    'TiDB.tidb.TiDB_monitor_time_jump_back_error': {
        'warning_level': 'warning',
        'pql': 'increase(tidb_monitor_time_jump_back_total{instance=~"%s.*"}[10m])  > 0' % self_ip
    },
    'TiDB.tidb.TiDB_ddl_waiting_jobs': {
        'warning_level': 'warning',
        'pql': 'sum(tidb_ddl_waiting_jobs{instance=~"%s.*"}) > 5' % self_ip
    },
    'TiDB.tidb.TiDB_server_panic_total': {
        'warning_level': 'critical',
        'pql': 'increase(tidb_server_panic_total{instance=~"%s.*"}[10m]) > 0' % self_ip
    },
}

# TiKV
tikv_metrics = {
    # Phase 1
    'TiDB.tikv.TiKV_server_is_down': {
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

    # Phase 2
    'TiDB.tikv.TiKV_coprocessor_request_error': {
        'warning_level': 'warning',
        'pql': 'increase(tikv_coprocessor_request_error{reason!="lock", instance=~"%s.*"}[10m]) > 100' % self_ip
    },
    'TiDB.tikv.TiKV_raft_append_log_duration_secs': {
        'warning_level': 'critical',
        'pql': 'histogram_quantile(0.99, sum(rate(tikv_raftstore_append_log_duration_seconds_bucket{'
               'instance=~"%s.*"}[1m])) by (le, instance)) > 1' % self_ip
    },
    'TiDB.tikv.TiKV_raftstore_thread_cpu_seconds_total': {
        'warning_level': 'critical',
        'pql': 'sum(rate(tikv_thread_cpu_seconds_total{name=~"raftstore_.*", instance=~"%s.*"}[1m])) '
               'by (instance)  > 1.6 ' % self_ip
    },
    'TiDB.tikv.TiKV_thread_apply_worker_cpu_seconds': {
        'warning_level': 'critical',
        'pql': 'sum(rate(tikv_thread_cpu_seconds_total{name="apply_worker", instance=~"%s.*"}[1m])) '
               'by (instance) > 1.8' % self_ip
    },
    'TiDB.tikv.TiKV_approximate_region_size': {
        'warning_level': 'warning',
        'pql': 'histogram_quantile(0.99, sum(rate(tikv_raftstore_region_size_bucket{instance=~"%s.*"}[1m])) '
               'by (le)) > 1073741824' % self_ip
    },
    'TiDB.tikv.TiKV_async_request_write_duration_seconds': {
        'warning_level': 'critical',
        'pql': 'histogram_quantile(0.99, sum(rate(tikv_storage_engine_async_request_duration_seconds_bucket'
               '{type="write", instance=~"%s.*"}[1m])) by (le, instance, type)) > 1' % self_ip
    },
    'TiDB.tikv.TiKV_coprocessor_pending_request': {
        'warning_level': 'warning',
        'pql': 'delta('
               'tikv_coprocessor_pending_request{instance=~"%s.*"}[10m]) > 5000' % self_ip
    },
    'TiDB.tikv.TiKV_raft_apply_log_duration_secs': {
        'warning_level': 'critical',
        'pql': 'histogram_quantile(0.99, sum(rate('
               'tikv_raftstore_apply_log_duration_seconds_bucket{instance=~"%s.*"}[1m]))'
               ' by (le, instance)) > 1' % self_ip
    },
    'TiDB.tikv.TiKV_scheduler_command_duration_seconds': {
        'warning_level': 'warning',
        'pql': 'histogram_quantile(0.99, sum(rate('
               'tikv_scheduler_command_duration_seconds_bucket{instance=~"%s.*"}[1m]))'
               ' by (le, instance, type)  / 1000)  > 1' % self_ip
    },
    'TiDB.tikv.TiKV_scheduler_latch_wait_duration_seconds': {
        'warning_level': 'critical',
        'pql': 'histogram_quantile(0.99, sum(rate('
               'tikv_scheduler_latch_wait_duration_seconds_bucket{instance=~"%s.*"}[1m]))'
               ' by (le, instance, type))  > 1' % self_ip
    },
    'TiDB.tikv.TiKV_write_stall': {
        'warning_level': 'critical',
        'pql': 'delta('
               'tikv_engine_write_stall{instance=~"%s.*"}[10m]) > 0' % self_ip
    },
}

# TiFlash
tiflash_metrics = {
    # Phase 1
    'TiDB.tiflash.TiFlash_server_is_down': {
        'warning_level': 'critical',
        'pql': 'probe_success{group="tiflash",instance=~"%s.*"} == 0' % self_ip
    },
    'TiDB.tiflash.TiFlash_proxy_node_restart': {
        'warning_level': 'critical',
        'pql': 'changes(tiflash_proxy_process_start_time_seconds{job="tiflash",instance=~"%s.*"}[5m]) > 0' % self_ip
    },

    # Phase 2
    'TiDB.tiflash.TiFlash_schema_error': {
        'warning_level': 'emergency',
        'pql': 'increase(tiflash_schema_apply_count{type="failed", instance=~"%s.*"}[15m]) > 0' % self_ip
    }
}

# Blackbox Exporter
blackbox_exporter_metrics = {
    # Phase 1
    'TiDB.blackbox_exporter.Blackbox_exporter_server_is_down': {
        'warning_level': 'critical',
        'pql': 'probe_success{group="blackbox_exporter",instance=~"%s.*"} == 0' % self_ip
    },

    # Phase 2
    'TiDB.blackbox_exporter.BLACKER_ping_latency_more_than_1s': {
        'warning_level': 'warning',
        'pql': 'max_over_time(probe_duration_seconds'
               '{job=~"blackbox_exporter.*_icmp", instance=~"%s.*"}[1m]) > 1' % self_ip
    }
}

# Node Exporter
node_exporter_metrics = {
    # Phase 1
    'TiDB.node_exporter.Node_exporter_server_is_down': {
        'warning_level': 'critical',
        'pql': 'probe_success{group="node_exporter",instance=~"%s.*"} == 0' % self_ip
    },

    # Phase 2
    'TiDB.node_exporter.Node_exporter_node_restart': {
        'warning_level': 'warning',
        'pql': 'changes(process_start_time_seconds{job="overwritten-nodes", instance=~"%s.*"}[5m]) > 0' % self_ip
    },
}

# Grafana
grafana_metrics = {
    # Phase 1
    'TiDB.grafana.Grafana_server_is_down': {
        'warning_level': 'critical',
        'pql': 'probe_success{group="grafana",instance=~"%s.*"} == 0' % self_ip
    },
}

# Cluster_metrics
cluster_metrics = {
    # Phase 2
    'TiDB.cluster.PD_cluster_down_tikv_nums': {
        'warning_level': 'emergency',
        'pql': '(sum(pd_cluster_status{type="store_down_count"}) by (instance) > 0) '
               'and (sum(etcd_server_is_leader) by (instance) > 0)',
    },
    'TiDB.cluster.PD_cluster_lost_connect_tikv_nums': {
        'warning_level': 'warning',
        'pql': '(sum ( pd_cluster_status{type="store_disconnected_count"} ) by (instance) > 0) '
               'and (sum(etcd_server_is_leader) by (instance) > 0)',
    },
    'TiDB.cluster.PD_leader_change': {
        'warning_level': 'warning',
        'pql': 'count(changes(pd_server_tso{type="save"}[10m]) > 0) >= 2',
    },
    'TiDB.cluster.TiKV_space_used_more_than_80%': {
        'warning_level': 'warning',
        'pql': 'sum(pd_cluster_status{type="storage_size"}) '
               '/sum(pd_cluster_status{type="storage_capacity"}) * 100  > 80',
    },
    'TiDB.cluster.PD_miss_peer_region_count': {
        'warning_level': 'warning',
        'pql': '(sum(pd_regions_status{type="miss_peer_region_count"}) by (instance)  > 100) '
               'and (sum(etcd_server_is_leader) by (instance) > 0)',
    },
    'TiDB.cluster.PD_no_store_for_making_replica': {
        'warning_level': 'warning',
        'pql': 'increase(pd_checker_event_count{type="replica_checker", name="no_target_store"}[1m]) > 0',
    },
    'TiDB.cluster.PD_system_time_slow': {
        'warning_level': 'warning',
        'pql': 'changes(pd_server_tso{type="system_time_slow"}[10m]) >= 1',
    },
    'TiDB.cluster.PD_cluster_low_space': {
        'warning_level': 'warning',
        'pql': '(sum ( pd_cluster_status{type="store_low_space_count"} ) by (instance) > 0) '
               'and (sum(etcd_server_is_leader) by (instance) > 0)',
    },
    'TiDB.cluster.PD_down_peer_region_nums': {
        'warning_level': 'warning',
        'pql': '(sum(pd_regions_status{type="down_peer_region_count"}) by (instance)  > 10) '
               'and (sum(etcd_server_is_leader) by (instance) > 0)',
    },
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
        return_tasks.append(tidb_metrics)

    if has_response(prometheus_address, judge_pqls['tikv']):
        return_tasks.append(tikv_metrics)

    if has_response(prometheus_address, judge_pqls['tiflash']):
        return_tasks.append(tiflash_metrics)

    if has_response(prometheus_address, judge_pqls['pd']):
        return_tasks.append(pd_metrics)

    if has_response(prometheus_address, judge_pqls['blackbox_exporter']):
        return_tasks.append(blackbox_exporter_metrics)

    if has_response(prometheus_address, judge_pqls['node_exporter']):
        return_tasks.append(node_exporter_metrics)

    if has_response(prometheus_address, judge_pqls['grafana']):
        return_tasks.append(grafana_metrics)

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
    # prometheus_addresses_string should be injected by outside program
    count, prometheus_addresses = split_prome_addresses(prometheus_addresses_string)
    print(prometheus_addresses, count)

    for prometheus_address in prometheus_addresses:
        if self_ip == prometheus_address.split(':')[0]:
            if not check_prome_alive(prometheus_address):
                print("metric=TiDB.prometheus.Prometheus_is_down|value=1|type=gauge|tags=status:critical")
            else:
                print("metric=TiDB.prometheus.Prometheus_is_down|value=0|type=gauge|tags=status:critical")
                check_role_metrics(cluster_metrics, prometheus_address)

    active_prometheus_address = find_alive_prome(prometheus_addresses)

    # check if all prometheus are down
    if not active_prometheus_address:
        sys.exit()

    tasks = populate_tasks(active_prometheus_address)
    for task in tasks:
        check_role_metrics(task, active_prometheus_address)


run_script()
