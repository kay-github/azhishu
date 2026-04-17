# azhishu

基于公共数据源的 A 股估值面板单页项目。

## 当前功能

- 12 张估值卡片面板
- 支持 `5Y / 10Y / 15Y / 20Y`
- 支持 `PE(TTM) / PB(LF)` 切换
- 统一使用单一主源 `Legulegu`
- 首页默认展示静态快照，适合直接部署到线上
- 提供本地一键启动脚本
- 提供 GitHub Actions 定时更新快照，推送后可自动触发 Vercel 重新部署

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
- `valuation_dashboard_server.py`: 本地 HTTP 服务，可按需重新抓取当前数据
- `valuation_dashboard.html`: 生成后的单页快照
- `api/data.py`: 线上读取当前发布快照 JSON 的接口
- `start_valuation_dashboard.bat`: Windows 一键启动脚本
- `.github/workflows/update-dashboard.yml`: 工作日定时更新快照并推送

## 说明

当前版本优先保证单一数据源、字段口径一致和线上可持续部署。

## 数据源说明

- 当前统一使用 `Legulegu` 公开接口，不再混用 Danjuan、东方财富等其他估值源。
- `PE(TTM)` 统一规则：
  - 全部A股：`averagePETTM`
  - 市场卡：`pe`
  - 指数卡：`addTtmPe`
- `PB(LF)` 统一规则：
  - 全部A股：`equalWeightAveragePB`
  - 其余卡片：`addPb`

## 自动更新

- GitHub Actions 会在工作日定时运行 `python valuation_dashboard.py`
- 若快照有变化，会自动提交 `valuation_dashboard.html`
- 推送到 GitHub 后，Vercel 会自动重新部署
