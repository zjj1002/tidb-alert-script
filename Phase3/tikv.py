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
               'by (instance)  > 3' % self_ip
    },
    'TiDB.tikv.TiKV_thread_apply_worker_cpu_seconds': {
        'warning_level': 'critical',
        'pql': 'sum(rate(tikv_thread_cpu_seconds_total{name="apply_worker", instance=~"%s.*"}[1m])) '
               'by (instance) > 3' % self_ip
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
