import requests
import sys
import socket


def split_ip(ips):
    number_of_ip = len(ips.split(","))
    prometheus_ip = ips.split(",")
    return number_of_ip, prometheus_ip


def http_request(alert_name, prometheusIp, judge_prome_sql, source_prome_sql, warning_level):
    for i in prometheusIp:
        print('http://%s/api/v1/query' % i)
        try:
            response = requests.get('http://%s/api/v1/query' % i, params={'query': judge_prome_sql})
            if response.json()["data"]['result'] != []:
                response = requests.get('http://%s/api/v1/query' % i, params={'query': source_prome_sql})
                value = 0 if response.json()["data"]['result'] == [] else 1
                print("metric=%s|value=%s|type=gauge|tags=status:%s" % (alert_name, value, warning_level))
        except:
            continue


count, prometheus_ips = split_ip(sys.argv[1])
print(prometheus_ips, count)
hostname = socket.gethostname()
ip = socket.gethostbyname(hostname)

# Check current node type
judge_tidb_sql = 'probe_success{group="tidb",instance=~"%s.*"}' % ip
judge_tikv_sql = 'probe_success{group="tikv",instance=~"%s.*"}' % ip
judge_tiflash_sql = 'probe_success{group="tiflash",instance=~"%s.*"}' % ip
judge_pd_sql = 'probe_success{group="pd",instance=~"%s.*"}' % ip

# TiDB server is down
alert_name = 'TiDB.blacker.Tidb_server_is_down'
warning_level = 'critical'
source_prome_sql = 'probe_success{group="tidb",instance=~"%s.*"} == 0' % ip
http_request(alert_name, prometheus_ips, judge_tidb_sql, source_prome_sql, warning_level)

# TiKV server is down
alert_name = 'TiDB.blacker.Tikv_server_is_down'
warning_level = 'critical'
source_prome_sql = 'probe_success{group="tikv",instance=~"%s.*"} == 0' % ip
http_request(alert_name, prometheus_ips, judge_tikv_sql, source_prome_sql, warning_level)

# TiFlash server is down
alert_name = 'TiDB.blacker.Tiflash_server_is_down'
warning_level = 'critical'
source_prome_sql = 'probe_success{group="tiflash",instance=~"%s.*"} == 0' % ip
http_request(alert_name, prometheus_ips, judge_tiflash_sql, source_prome_sql, warning_level)

# PD server is down
alert_name = 'TiDB.blacker.pd_server_is_down'
warning_level = 'critical'
source_prome_sql = 'probe_success{group="pd",instance=~"%s.*"} == 0' % ip
http_request(alert_name, prometheus_ips, judge_pd_sql, source_prome_sql, warning_level)

# PD restart
alert_name = 'TiDB.pd.PD_node_restart'
warning_level = 'critical'
source_prome_sql = 'changes(process_start_time_seconds{job="pd",instance=~"%s.*"}[5m])> 0' % ip
http_request(alert_name, prometheus_ips, judge_pd_sql, source_prome_sql, warning_level)

# TiKV restart
alert_name = 'TiDB.tikv.TIKV_node_restart'
warning_level = 'critical'
source_prome_sql = 'changes(process_start_time_seconds{job="tikv",instance=~"%s.*"}[5m])> 0' % ip
http_request(alert_name, prometheus_ips, judge_tikv_sql, source_prome_sql, warning_level)

# TiDB restart
alert_name = 'TiDB.tidb.TIDB_node_restart'
warning_level = 'critical'
source_prome_sql = 'changes(process_start_time_seconds{job="tidb",instance=~"%s.*"}[5m])> 0' % ip
http_request(alert_name, prometheus_ips, judge_tidb_sql, source_prome_sql, warning_level)

# TiFlash restart
alert_name = 'TiDB.tiflash.TiFlash_proxy_node_restart'
warning_level = 'critical'
source_prome_sql = 'changes(process_start_time_seconds{job="tiflash",instance=~"%s.*"}[5m])> 0' % ip
http_request(alert_name, prometheus_ips, judge_tiflash_sql, source_prome_sql, warning_level)

# TiKV GC not working
alert_name = 'TiDB.tikv.TiKV_GC_can_not_work'
warning_level = 'critical'
source_prome_sql = 'increase(tikv_gcworker_gc_tasks_vec{task="gc",instance=~"%s.*"}[1d]) < 1 and increase(tikv_gc_compaction_filter_perform{instance=~"%s.*"}[1d]) < 1' % (
    ip, ip)
http_request(alert_name, prometheus_ips, judge_tikv_sql, source_prome_sql, warning_level)
