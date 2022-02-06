# multi ping解决的问题
- 从某台机器同时ping一个列表里的所有IP
- 超过某个延迟的ping的结果会被记录
- 可以并发N个gorutine去同时ping多台机器

# alert.go解决的问题
- 链接TIDB的altermanager组件
- 解析alertmanager的报警消息
- 使用者可以把解析后的消息 用 命名行 | http接口方式 把这个报警用自己的方式发出去
- 脚本里展示了一个用命令行而且自定义发送格式的例子

# prometheus_alert_script.py解决的问题
* 因为某个客户的监控系统不支持PROMSQL，并且不支持string方式的报警方式
* 而且客户部署了两个Prometheus，进行HA
* 客户的报警方式是 在每台机器上都有一个agent，只能监控本机的情况 ，所以本脚本的逻辑是 通过在每台机器上 访问本地的Prometheus来处理promsql，然后把结果用0和1发给客户系统即可
* 因为客户无法处理string，所以，需要对promsql进行重写，只处理混和部署情况下 本机已有的组件
* 需要处理的情况有：
* 1.   单个prometheus down 如何识别自身，混部情况下 如何保证其他组件的报警
* 2.   如何和龙舟的分组策略结合
* 3.  两个Prometheus HA情况下，如果两个都挂了 如何报警
* 4.  两个Pormetheus 一个down了 另外一个活着 如何报警
* 5.  blackbox里的probe_sucess group里没有Prometheus 探活如何实现

## 已完成的报警信息

### 报警名称命名规律

`[产品名].[组件名].[警告名]`

示例: `TiDB.pd.PD_server_is_down`

## 一，二期已完成的报警

| Phase | Component         | Alert Name                                               |
| ----- | ----------------- | -------------------------------------------------------- |
| 1     | pd                | TiDB.pd.PD_server_is_down                                |
| 1     | pd                | TiDB.pd.PD_node_restart                                  |
| 1     | tidb              | TiDB.tidb.TiDB_server_is_down                            |
| 1     | tidb              | TiDB.tidb.TiDB_node_restart                              |
| 2     | tidb              | TiDB.tidb.TiDB_schema_error                              |
| 2     | tidb              | TiDB.tidb.TiDB_monitor_keep_alive                        |
| 2     | tidb              | TiDB.tidb.TiDB_monitor_time_jump_back_error              |
| 2     | tidb              | TiDB.tidb.TiDB_ddl_waiting_jobs                          |
| 2     | tidb              | TiDB.tidb.TiDB_server_panic_total                        |
| 1     | tikv              | TiDB.tikv.TiKV_server_is_down                            |
| 1     | tikv              | TiDB.tikv.TiKV_node_restart                              |
| 1     | tikv              | TiDB.tikv.TiKV_GC_can_not_work                           |
| 2     | tikv              | TiDB.tikv.TiKV_coprocessor_request_error                 |
| 2     | tikv              | TiDB.tikv.TiKV_raft_append_log_duration_secs             |
| 2     | tikv              | TiDB.tikv.TiKV_raftstore_thread_cpu_seconds_total        |
| 2     | tikv              | TiDB.tikv.TiKV_thread_apply_worker_cpu_seconds           |
| 2     | tikv              | TiDB.tikv.TiKV_approximate_region_size                   |
| 2     | tikv              | TiDB.tikv.TiKV_async_request_write_duration_seconds      |
| 2     | tikv              | TiDB.tikv.TiKV_coprocessor_pending_request               |
| 2     | tikv              | TiDB.tikv.TiKV_raft_apply_log_duration_secs              |
| 2     | tikv              | TiDB.tikv.TiKV_scheduler_command_duration_seconds        |
| 2     | tikv              | TiDB.tikv.TiKV_scheduler_latch_wait_duration_seconds     |
| 2     | tikv              | TiDB.tikv.TiKV_write_stall                               |
| 1     | tiflash           | TiDB.tiflash.TiFlash_server_is_down                      |
| 1     | tiflash           | TiDB.tiflash.TiFlash_proxy_node_restart                  |
| 2     | tiflash           | TiDB.tiflash.TiFlash_schema_error                        |
| 1     | blackbox_exporter | TiDB.blackbox_exporter.Blackbox_exporter_server_is_down  |
| 2     | blackbox_exporter | TiDB.blackbox_exporter.BLACKER_ping_latency_more_than_1s |
| 1     | node_exporter     | TiDB.node_exporter.Node_exporter_server_is_down          |
| 2     | node_exporter     | TiDB.node_exporter.Node_exporter_node_restart            |
| 1     | grafana           | TiDB.grafana.Grafana_server_is_down                      |
| 2     | cluster           | TiDB.prometheus.Prometheus_is_down                       |
| 2     | cluster           | TiDB.cluster.PD_cluster_down_tikv_nums                   |
| 2     | cluster           | TiDB.cluster.PD_cluster_lost_connect_tikv_nums           |
| 2     | cluster           | TiDB.cluster.PD_leader_change                            |
| 2     | cluster           | TiDB.cluster.TiKV_space_used_more_than_80                |
| 2     | cluster           | TiDB.cluster.PD_miss_peer_region_count                   |
| 2     | cluster           | TiDB.cluster.PD_no_store_for_making_replica              |
| 2     | cluster           | TiDB.cluster.PD_system_time_slow                         |
| 2     | cluster           | TiDB.cluster.PD_cluster_low_space                        |
| 2     | cluster           | TiDB.cluster.PD_down_peer_region_nums                    |

共41个，其中：
* 1期报警: 12个
* 2期报警: 29个
