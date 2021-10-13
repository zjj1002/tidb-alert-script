# alert.go解决的问题
- 链接TIDB的altermanager组件
- 解析alertmanager的报警消息
- 使用者可以把解析后的消息 用 命名行 | http接口方式 把这个报警用自己的方式发出去
- 脚本里展示了一个用命令行而且自定义发送格式的例子


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
