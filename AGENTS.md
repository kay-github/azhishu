# Agent 指南：azhishu

## 产品目标
做一个可部署到线上、风格尽量贴近参考截图的 A 股宽基估值分析单页。

当前重点不是做通用金融终端，而是做一页可直接访问的估值面板：
- 12 张卡片
- 支持 `5Y / 10Y / 15Y / 20Y`
- 支持 `PE(TTM) / PB(LF)` 切换
- 默认视觉和文案尽量接近参考图

## 当前产品形态
- 首页是 `valuation_dashboard.html` 静态快照，保证线上首屏稳定可打开。
- 当前线上版本以“静态快照发布”为主，不再依赖运行时多源刷新。
- 卡片上的当前值、分位数、危险值 / 中位数 / 机会值会随当前周期和指标切换而重算。
- GitHub Actions 会在工作日定时重新生成快照并提交，进而触发 Vercel 自动部署。

## 关键文件
- `valuation_dashboard.py`
  - 生成页面所需 payload，并输出 `valuation_dashboard.html`
  - 这里是数据抓取、口径处理、页面模板的核心入口
- `valuation_dashboard.html`
  - 发布到线上后直接作为首页静态快照
  - 不要手改，应通过运行 `python valuation_dashboard.py` 重新生成
- `valuation_dashboard_server.py`
  - 本地 HTTP 服务
  - 提供本地重新抓数和调试用接口
- `api/data.py`
  - Vercel 使用的 Python Serverless Function
  - 线上读取当前已发布快照 JSON 的接口
- `vercel.json`
  - 线上路由配置
  - 当前是 `/` 和 `/index.html` 重写到 `valuation_dashboard.html`，`/data` 重写到 `api/data.py`
- `start_valuation_dashboard.bat`
  - Windows 本地一键启动脚本
- `.github/workflows/update-dashboard.yml`
  - GitHub Actions 定时更新快照并自动提交

## 当前数据源策略

### 乐咕乐股（LeguLegu）
用途：
- 当前唯一主数据源
- 提供页面所需的历史曲线、当前值和字段级估值数据

当前主要承担：
- 各卡片历史 `PE / PB` 序列
- 当前值与分位计算所需的基础数据
- 所有卡片的统一主源口径

## 当前口径现状
- 当前统一使用 Legu 单源，不再混用 Danjuan、东方财富等其他估值源
- `PE(TTM)` 统一规则：
  - 全部A股：`averagePETTM`
  - 市场卡：`pe`
  - 指数卡：`addTtmPe`
- `PB(LF)` 统一规则：
  - 全部A股：`equalWeightAveragePB`
  - 其余卡片：`addPb`
- 各周期分位均按当前展示曲线样本重算，不再单独引入其他来源的默认 10 年快照

## 已知仍不完全一致的点
- `全部A股`：当前使用 Legu 的“全部A股等权”口径，不等于截图常见的“万得全A”
- `上证 / 深证成指 / 创业板指`：当前使用 Legu 市场口径，不是严格的指数代码口径复刻
- `科创50 / 中证2000 / 中证A50 / 中证A500`：即便统一到 Legu 单源，和参考截图仍可能存在显著差异
- 新指数历史长度天然不足，无法真实覆盖完整 `10Y / 15Y / 20Y`

## 本地运行
生成静态快照：

```bash
python valuation_dashboard.py
```

本地起服务：

```bash
python valuation_dashboard_server.py
```

## 修改约束
- 对产品层面比较重大的改动，都要回头更新本文件
- “重大改动”包括但不限于：
  - 页面卡片数量或标的集合变化
  - 数据源策略变化
  - 分位/估值计算逻辑变化
  - 部署方式变化
  - 首页静态 / 动态策略变化
  - 用户可见交互或产品定位变化
- 不要手改 `valuation_dashboard.html`，应通过脚本重新生成
