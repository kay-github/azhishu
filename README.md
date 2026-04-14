# azhishu

基于公共数据源的 A 股估值面板单页项目。

## 当前功能

- 12 张估值卡片面板
- 支持 `5Y / 10Y / 15Y / 20Y`
- 支持 `PE(TTM) / PB(LF)` 切换
- 页面打开时拉取最新公共数据
- 前端每 15 分钟自动刷新一次
- 提供本地一键启动脚本

## 本地运行

安装依赖：

```bash
pip install -r requirements.txt
```

启动本地服务：

```bash
python valuation_dashboard_server.py
```

浏览器打开：

```text
http://127.0.0.1:8765/
```

或直接双击：

```text
start_valuation_dashboard.bat
```

## 文件说明

- `valuation_dashboard.py`: 数据抓取与单页 HTML 生成
- `valuation_dashboard_server.py`: 本地 HTTP 服务与实时数据接口
- `valuation_dashboard.html`: 生成后的单页快照
- `start_valuation_dashboard.bat`: Windows 一键启动脚本

## 说明

当前版本优先保证公共数据源可用性和刷新稳定性。后续会继续优化口径一致性，使结果更贴近目标产品截图。
