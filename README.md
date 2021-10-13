# alert.go解决的问题
- 链接TIDB的altermanager组件
- 解析alertmanager的报警消息
- 使用者可以把解析后的消息 用 命名行 | http接口方式 把这个报警用自己的方式发出去
- 脚本里展示了一个用命令行而且自定义发送格式的例子

prometheus_alert_script.py解决的问题
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

## Phase 1 完成的报警
* Prometheus is down
* TiDB server is down
* TiDB node restart
* TiKV server is down
* TiKV node restart
* TiKV GC cannot work
* TiFlash server is down
* TiFlash proxy node restart
* PD server is down
* PD node restart
* Backbox exporter server is down
* Node exporter server is down
* Grafana server is down
