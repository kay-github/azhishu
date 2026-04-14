import hashlib
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests


OUTPUT_FILE = Path("valuation_dashboard.html")
BASE_URL = "https://legulegu.com"
DANJUAN_URL = "https://danjuanfunds.com"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)
LEGU_MAX_WORKERS = 6

CARD_CONFIGS = [
    {
        "id": "all-a",
        "name": "全部A股",
        "tag": "近似口径",
        "type": "all_a",
        "danjuan_code": "SZ399317",
    },
    {
        "id": "shanghai",
        "name": "上证",
        "tag": "市场口径",
        "type": "market",
        "market_id": "1",
    },
    {
        "id": "shenzhen",
        "name": "深证成指",
        "tag": "指数口径",
        "type": "market",
        "market_id": "2",
        "danjuan_code": "SZ399001",
    },
    {
        "id": "star50",
        "name": "科创50",
        "tag": "指数口径",
        "type": "index",
        "index_code": "000688.SH",
        "danjuan_code": "SH000688",
    },
    {
        "id": "gem",
        "name": "创业板指",
        "tag": "指数口径",
        "type": "market",
        "market_id": "4",
        "danjuan_code": "SZ399006",
    },
    {
        "id": "hs300",
        "name": "沪深300",
        "tag": "指数口径",
        "type": "index",
        "index_code": "000300.SH",
        "danjuan_code": "SH000300",
    },
    {
        "id": "zz500",
        "name": "中证500",
        "tag": "指数口径",
        "type": "index",
        "index_code": "000905.SH",
        "danjuan_code": "SH000905",
    },
    {
        "id": "zz1000",
        "name": "中证1000",
        "tag": "指数口径",
        "type": "index",
        "index_code": "000852.SH",
        "danjuan_code": "SH000852",
    },
    {
        "id": "zz2000",
        "name": "中证2000",
        "tag": "指数口径",
        "type": "index",
        "index_code": "932000.CSI",
    },
    {
        "id": "a50",
        "name": "中证A50",
        "tag": "指数口径",
        "type": "index",
        "index_code": "930050.CSI",
    },
    {
        "id": "zz100",
        "name": "中证100",
        "tag": "指数口径",
        "type": "index",
        "index_code": "000903.SH",
        "danjuan_code": "SH000903",
    },
    {
        "id": "a500",
        "name": "中证A500",
        "tag": "指数口径",
        "type": "index",
        "index_code": "000510.CSI",
    },
]


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>估值分析复刻版</title>
  <style>
    :root {
      --bg: #f3f6f8;
      --card: #ffffff;
      --border: #dde5ea;
      --text: #23323d;
      --muted: #6f8190;
      --primary: #89d5db;
      --primary-line: #7ccdd4;
      --danger: #b55a54;
      --median: #8f9ca7;
      --chance: #2f9f80;
      --shadow: 0 10px 24px rgba(24, 47, 64, 0.06);
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      background: #f4f6f8;
      color: var(--text);
    }

    .page {
      max-width: 1360px;
      margin: 0 auto;
      padding: 14px 12px 24px;
    }

    .topbar {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 16px;
      margin-bottom: 10px;
      background: #fff;
      border: 1px solid #e2e8ee;
      border-radius: 8px;
      padding: 10px 12px;
      box-shadow: 0 1px 2px rgba(18, 38, 55, 0.04);
    }

    .title-wrap h1 {
      margin: 0;
      font-size: 22px;
      line-height: 1.1;
      letter-spacing: 0.2px;
      font-weight: 700;
    }

    .title-wrap p {
      margin: 6px 0 0;
      color: var(--muted);
      font-size: 12px;
    }

    .controls {
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
      justify-content: flex-end;
    }

    .btn-group {
      display: inline-flex;
      background: #f3f6f9;
      border: 1px solid #dbe5eb;
      border-radius: 6px;
      padding: 2px;
      box-shadow: none;
    }

    .btn-group button {
      border: 0;
      background: transparent;
      color: #667988;
      padding: 6px 12px;
      border-radius: 5px;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.16s ease;
      min-width: 46px;
    }

    .btn-group button.active {
      color: white;
      background: #55b6c6;
      box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.04);
    }

    .summary {
      display: flex;
      gap: 16px;
      align-items: center;
      justify-content: space-between;
      background: #fff;
      border: 1px solid #e2e8ee;
      border-radius: 8px;
      padding: 10px 12px;
      margin-bottom: 10px;
      box-shadow: 0 1px 2px rgba(18, 38, 55, 0.04);
    }

    .summary strong {
      display: block;
      margin-bottom: 4px;
      font-size: 13px;
    }

    .summary span,
    .summary li {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.6;
    }

    .summary ul {
      margin: 0;
      padding-left: 18px;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }

    .card {
      background: var(--card);
      border: 1px solid #dfe7ed;
      border-radius: 8px;
      padding: 10px 10px 8px;
      box-shadow: 0 1px 2px rgba(18, 38, 55, 0.04);
      min-height: 292px;
    }

    .card-head {
      display: block;
      margin-bottom: 6px;
    }

    .card-head-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
      margin-bottom: 4px;
    }

    .card-title {
      font-size: 16px;
      font-weight: 700;
      line-height: 1.15;
      margin: 0;
    }

    .metric-row {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      color: var(--text);
      font-size: 12px;
      font-weight: 700;
    }

    .metric-row span small {
      color: var(--muted);
      font-size: 12px;
      font-weight: 500;
      margin-right: 4px;
    }

    .tag {
      border-radius: 999px;
      border: 1px solid #dde7ed;
      background: #f7fafc;
      color: #7890a0;
      font-size: 10px;
      font-weight: 700;
      padding: 3px 8px;
      white-space: nowrap;
    }

    .chart-wrap {
      margin-top: 6px;
      border-radius: 6px;
      background: linear-gradient(180deg, #fcfefe 0%, #f5fbfb 100%);
      border: 1px solid #edf3f6;
      padding-top: 2px;
    }

    .card svg {
      width: 100%;
      height: 184px;
      display: block;
    }

    .legend {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      align-items: center;
      color: var(--muted);
      font-size: 11px;
      margin-top: 6px;
    }

    .legend-item {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }

    .dot,
    .dash {
      display: inline-block;
      flex: 0 0 auto;
    }

    .dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--primary-line);
      box-shadow: 0 0 0 3px rgba(124, 205, 212, 0.18);
    }

    .dash {
      width: 16px;
      height: 0;
      border-top: 2px dashed transparent;
    }

    .dash-danger {
      border-color: var(--danger);
    }

    .dash-median {
      border-color: var(--median);
    }

    .dash-chance {
      border-color: var(--chance);
    }

    .footer {
      margin-top: 12px;
      padding: 12px 14px;
      background: #fff;
      border: 1px solid #e2e8ee;
      border-radius: 8px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.7;
      box-shadow: 0 1px 2px rgba(18, 38, 55, 0.04);
    }

    .footer strong {
      color: var(--text);
    }

    .empty {
      color: var(--muted);
      font-size: 12px;
      padding: 60px 10px 0;
      text-align: center;
    }

    @media (max-width: 1180px) {
      .grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
    }

    @media (max-width: 760px) {
      .page {
        padding: 12px 10px 22px;
      }

      .topbar,
      .summary {
        flex-direction: column;
        align-items: stretch;
      }

      .controls {
        justify-content: flex-start;
      }

      .grid {
        grid-template-columns: 1fr;
      }

      .card {
        min-height: 278px;
      }
    }
  </style>
</head>
<body>
  <div class="page">
    <div class="topbar">
      <div class="title-wrap">
        <h1 id="page-title">估值分析（近10年）</h1>
        <p>公共数据复刻版。切换周期和指标后，卡片上的当前值、分位数、危险值/中位数/机会值会同步重算。</p>
      </div>
      <div class="controls">
        <div class="btn-group" id="period-buttons"></div>
        <div class="btn-group" id="metric-buttons"></div>
      </div>
    </div>

    <div class="summary">
      <div>
        <strong id="updated-label">最新数据</strong>
        <span id="updated-value"></span>
      </div>
      <div>
        <strong>估值区间说明</strong>
        <span>危险值 = 80% 分位，中位数 = 50% 分位，机会值 = 20% 分位。页面通过本地服务实时拉取公共数据，并每 15 分钟自动刷新一次。</span>
      </div>
    </div>

    <div class="grid" id="card-grid"></div>

    <div class="footer">
      <strong>口径说明：</strong>
      <div>1. 数据源来自乐咕乐股公开接口，页面为静态快照，不依赖后端。</div>
      <div>2. “全部A股”卡片使用公开“全部A股等权估值”替代截图中的“万得全A”。</div>
      <div>3. “上证 / 深证 / 创业板”使用公开市场板块估值口径；其余卡片使用公开指数估值口径。</div>
      <div>4. 优先使用 Danjuan 当前估值快照来贴近目标产品；历史曲线继续使用稳定公共历史源，以兼顾覆盖度和可持续更新。</div>
    </div>
  </div>

  <script id="valuation-data" type="application/json">__DATA__</script>
  <script>
    let dataModel = JSON.parse(document.getElementById('valuation-data').textContent);

    const PERIOD_OPTIONS = [5, 10, 15, 20];
    const METRIC_OPTIONS = [
      { key: 'pe', label: 'PE(TTM)' },
      { key: 'pb', label: 'PB(LF)' },
    ];

    const state = {
      years: 10,
      metric: 'pe',
    };

    const pageTitle = document.getElementById('page-title');
    const updatedValue = document.getElementById('updated-value');
    const cardGrid = document.getElementById('card-grid');

    function formatDate(dateStr) {
      const d = new Date(dateStr + 'T00:00:00');
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      return `${y}-${m}-${day}`;
    }

    function formatDateShort(dateStr) {
      const d = new Date(dateStr + 'T00:00:00');
      const y = String(d.getFullYear()).slice(-2);
      const m = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      return `${y}-${m}-${day}`;
    }

    function formatValue(value) {
      if (!Number.isFinite(value)) {
        return '--';
      }
      return `${value.toFixed(2)}x`;
    }

    function formatPercent(value) {
      if (!Number.isFinite(value)) {
        return '--';
      }
      return `${value.toFixed(2)}%`;
    }

    function quantile(values, q) {
      if (!values.length) {
        return NaN;
      }
      const sorted = [...values].sort((a, b) => a - b);
      if (sorted.length === 1) {
        return sorted[0];
      }
      const pos = (sorted.length - 1) * q;
      const base = Math.floor(pos);
      const rest = pos - base;
      const lower = sorted[base];
      const upper = sorted[Math.min(base + 1, sorted.length - 1)];
      return lower + (upper - lower) * rest;
    }

    function percentile(values, current) {
      if (!values.length || !Number.isFinite(current)) {
        return NaN;
      }
      let count = 0;
      for (const value of values) {
        if (value <= current) {
          count += 1;
        }
      }
      return (count / values.length) * 100;
    }

    function filterSeries(points, years) {
      if (!points || !points.length) {
        return [];
      }
      const last = new Date(points[points.length - 1].date + 'T00:00:00');
      const start = new Date(last);
      start.setFullYear(last.getFullYear() - years);
      const filtered = points.filter((point) => new Date(point.date + 'T00:00:00') >= start);
      return filtered.length ? filtered : points;
    }

    function createPath(points, xScale, yScale, baseline) {
      if (!points.length) {
        return '';
      }
      const first = points[0];
      let path = `M ${xScale(first.ts).toFixed(2)} ${baseline.toFixed(2)}`;
      for (const point of points) {
        path += ` L ${xScale(point.ts).toFixed(2)} ${yScale(point.value).toFixed(2)}`;
      }
      const last = points[points.length - 1];
      path += ` L ${xScale(last.ts).toFixed(2)} ${baseline.toFixed(2)} Z`;
      return path;
    }

    function createLine(points, xScale, yScale) {
      if (!points.length) {
        return '';
      }
      let path = '';
      points.forEach((point, index) => {
        const x = xScale(point.ts).toFixed(2);
        const y = yScale(point.value).toFixed(2);
        path += `${index === 0 ? 'M' : 'L'} ${x} ${y} `;
      });
      return path.trim();
    }

    function renderChart(points, stats) {
      if (!points.length) {
        return '<div class="empty">当前卡片没有可用数据</div>';
      }

      const width = 360;
      const height = 212;
      const margin = { top: 10, right: 10, bottom: 28, left: 42 };
      const plotWidth = width - margin.left - margin.right;
      const plotHeight = height - margin.top - margin.bottom;
      const times = points.map((point) => point.ts);
      const values = points.map((point) => point.value);
      const refs = [stats.q20, stats.q50, stats.q80].filter(Number.isFinite);
      const minValue = Math.min(...values, ...refs);
      const maxValue = Math.max(...values, ...refs);
      const spread = Math.max(maxValue - minValue, 0.5);
      const yMin = minValue - spread * 0.14;
      const yMax = maxValue + spread * 0.10;
      const xMin = Math.min(...times);
      const xMax = Math.max(...times);
      const xScale = (value) => {
        if (xMax === xMin) {
          return margin.left + plotWidth / 2;
        }
        return margin.left + ((value - xMin) / (xMax - xMin)) * plotWidth;
      };
      const yScale = (value) => margin.top + ((yMax - value) / (yMax - yMin)) * plotHeight;
      const baseline = margin.top + plotHeight;

      const areaPath = createPath(points, xScale, yScale, baseline);
      const linePath = createLine(points, xScale, yScale);

      const yTicks = [];
      for (let i = 0; i < 4; i += 1) {
        const ratio = i / 3;
        const value = yMax - (yMax - yMin) * ratio;
        yTicks.push({ value, y: yScale(value) });
      }

      const xTicks = [];
      const tickCount = Math.min(4, points.length);
      for (let i = 0; i < tickCount; i += 1) {
        const index = Math.round(((points.length - 1) * i) / Math.max(tickCount - 1, 1));
        const point = points[index];
        xTicks.push({ label: formatDateShort(point.date), x: xScale(point.ts) });
      }

      const refLines = [
        { value: stats.q80, color: 'var(--danger)' },
        { value: stats.q50, color: 'var(--median)' },
        { value: stats.q20, color: 'var(--chance)' },
      ].filter((item) => Number.isFinite(item.value));

      return `
        <svg viewBox="0 0 ${width} ${height}" aria-hidden="true">
          <defs>
            <linearGradient id="fill-gradient" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stop-color="rgba(124, 205, 212, 0.95)"></stop>
              <stop offset="100%" stop-color="rgba(124, 205, 212, 0.42)"></stop>
            </linearGradient>
          </defs>
          <rect x="0" y="0" width="${width}" height="${height}" rx="14" fill="transparent"></rect>
          ${yTicks.map((tick) => `
            <g>
              <line x1="${margin.left}" y1="${tick.y.toFixed(2)}" x2="${(margin.left + plotWidth).toFixed(2)}" y2="${tick.y.toFixed(2)}" stroke="#e7eef3" stroke-dasharray="3 4"></line>
              <text x="${(margin.left - 8).toFixed(2)}" y="${(tick.y + 4).toFixed(2)}" text-anchor="end" font-size="11" fill="#8093a0">${tick.value.toFixed(tick.value < 10 ? 2 : 0)}</text>
            </g>
          `).join('')}
          ${refLines.map((line) => `
            <line x1="${margin.left}" y1="${yScale(line.value).toFixed(2)}" x2="${(margin.left + plotWidth).toFixed(2)}" y2="${yScale(line.value).toFixed(2)}" stroke="${line.color}" stroke-width="1.8" stroke-dasharray="7 5"></line>
          `).join('')}
          <path d="${areaPath}" fill="url(#fill-gradient)"></path>
          <path d="${linePath}" fill="none" stroke="var(--primary-line)" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"></path>
          ${xTicks.map((tick) => `
            <text x="${tick.x.toFixed(2)}" y="${(baseline + 18).toFixed(2)}" text-anchor="middle" font-size="11" fill="#8093a0">${tick.label}</text>
          `).join('')}
        </svg>
      `;
    }

    function buildCard(card) {
      const rawPoints = card.metrics[state.metric] || [];
      const points = filterSeries(rawPoints, state.years).map((point) => ({
        ...point,
        ts: new Date(point.date + 'T00:00:00').getTime(),
      }));

      if (!points.length) {
        return `
          <section class="card">
            <div class="card-head">
              <div class="card-head-top">
                <h2 class="card-title">${card.name}</h2>
                <span class="tag">${card.tag}</span>
              </div>
              <div class="metric-row"><span><small>${state.metric === 'pe' ? 'PE' : 'PB'}</small>--</span></div>
            </div>
            <div class="chart-wrap"><div class="empty">当前指标暂无可用数据</div></div>
          </section>
        `;
      }

      const values = points.map((point) => point.value).filter(Number.isFinite);
      const snapshot = card.snapshots && card.snapshots[state.metric] ? card.snapshots[state.metric] : null;
      const current = snapshot && Number.isFinite(snapshot.value) ? snapshot.value : points[points.length - 1].value;
      const stats = {
        q20: quantile(values, 0.2),
        q50: quantile(values, 0.5),
        q80: quantile(values, 0.8),
        percentile: percentile(values, current),
      };
      const displayPercentile = snapshot && state.years === 10 && Number.isFinite(snapshot.percentile)
        ? snapshot.percentile
        : stats.percentile;

      const chart = renderChart(points, stats);

      return `
        <section class="card">
          <div class="card-head">
            <div class="card-head-top">
              <h2 class="card-title">${card.name}</h2>
              <span class="tag">${card.tag}</span>
            </div>
            <div class="metric-row">
              <span><small>${state.metric === 'pe' ? 'PE' : 'PB'}</small>${formatValue(current)}</span>
              <span><small>分位数</small>${formatPercent(displayPercentile)}</span>
            </div>
          </div>
          <div class="chart-wrap">${chart}</div>
          <div class="legend">
            <span class="legend-item"><span class="dot"></span>${state.metric === 'pe' ? 'PE(TTM)' : 'PB(LF)'}</span>
            <span class="legend-item"><span class="dash dash-danger"></span>危险值</span>
            <span class="legend-item"><span class="dash dash-median"></span>中位数</span>
            <span class="legend-item"><span class="dash dash-chance"></span>机会值</span>
          </div>
        </section>
      `;
    }

    function renderButtons() {
      const periodRoot = document.getElementById('period-buttons');
      const metricRoot = document.getElementById('metric-buttons');

      periodRoot.innerHTML = PERIOD_OPTIONS.map((years) => `
        <button data-years="${years}" class="${years === state.years ? 'active' : ''}">${years}Y</button>
      `).join('');

      metricRoot.innerHTML = METRIC_OPTIONS.map((item) => `
        <button data-metric="${item.key}" class="${item.key === state.metric ? 'active' : ''}">${item.label}</button>
      `).join('');

      periodRoot.querySelectorAll('button').forEach((button) => {
        button.addEventListener('click', () => {
          state.years = Number(button.dataset.years);
          rerender();
        });
      });

      metricRoot.querySelectorAll('button').forEach((button) => {
        button.addEventListener('click', () => {
          state.metric = button.dataset.metric;
          rerender();
        });
      });
    }

    function rerender() {
      pageTitle.textContent = `估值分析（近${state.years}年）`;
      updatedValue.textContent = formatDate(dataModel.updated_at);
      renderButtons();
      cardGrid.innerHTML = dataModel.cards.map(buildCard).join('');
    }

    function applyData(nextData) {
      dataModel = nextData;
      rerender();
    }

    async function refreshLiveData() {
      if (!window.location.protocol.startsWith('http')) {
        return;
      }

      try {
        const response = await fetch('./data?_=' + Date.now(), { cache: 'no-store' });
        if (!response.ok) {
          return;
        }
        const nextData = await response.json();
        applyData(nextData);
      } catch (error) {
        console.warn('Live data refresh failed:', error);
      }
    }

    rerender();
    refreshLiveData();
    window.setInterval(refreshLiveData, 15 * 60 * 1000);
  </script>
</body>
</html>
"""


class LeguClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9",
            }
        )
        self.token = hashlib.md5(datetime.now().date().isoformat().encode("utf-8")).hexdigest()
        self.csrf_token = self._prepare_session()

    def _prepare_session(self):
        page = self.session.get(f"{BASE_URL}/stockdata/hs300-ttm-lyr", timeout=20)
        page.raise_for_status()
        match = re.search(r'<meta name="_csrf" content="([^"]+)"', page.text)
        if not match:
            raise RuntimeError("Failed to extract CSRF token from Legulegu page")

        # Warm up cookies for the older all-A endpoints.
        self.session.get(f"{BASE_URL}/stockdata/a-ttm-lyr", timeout=20)
        self.session.get(f"{BASE_URL}/stockdata/all-pb", timeout=20)
        return match.group(1)

    def _json(self, url, params, use_csrf=False):
        headers = None
        if use_csrf:
            headers = {"X-CSRF-Token": self.csrf_token, "User-Agent": USER_AGENT}

        last_error = None
        for _ in range(3):
            try:
                response = self.session.get(url, params=params, headers=headers, timeout=20)
                response.raise_for_status()
                payload = response.json()
                return payload.get("data") or []
            except Exception as exc:
                last_error = exc
                time.sleep(0.5)
        raise RuntimeError(f"Failed to fetch {url}: {last_error}")

    def fetch_market_pe(self, market_id):
        return self._json(
            f"{BASE_URL}/api/stock-data/market-pe",
            params={"marketId": market_id, "token": self.token},
            use_csrf=True,
        )

    def fetch_market_pb(self, market_id):
        return self._json(
            f"{BASE_URL}/api/stockdata/index-basic-pb",
            params={"indexCode": market_id, "token": self.token},
            use_csrf=True,
        )

    def fetch_index_pe(self, index_code):
        return self._json(
            f"{BASE_URL}/api/stockdata/index-basic-pe",
            params={"indexCode": index_code, "token": self.token},
            use_csrf=True,
        )

    def fetch_index_pb(self, index_code):
        return self._json(
            f"{BASE_URL}/api/stockdata/index-basic-pb",
            params={"indexCode": index_code, "token": self.token},
            use_csrf=True,
        )

    def fetch_all_a_pe(self):
        return self._json(
            f"{BASE_URL}/api/stock-data/market-ttm-lyr",
            params={"marketId": "5", "token": self.token},
        )

    def fetch_all_a_pb(self):
        return self._json(
            f"{BASE_URL}/api/stock-data/market-index-pb",
            params={"marketId": "ALL", "token": self.token},
        )


class DanjuanClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Referer": f"{DANJUAN_URL}/djmodule/value-center",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9",
            }
        )

    def fetch_snapshots(self):
        response = self.session.get(f"{DANJUAN_URL}/djapi/index_eva/dj", timeout=20)
        response.raise_for_status()
        payload = response.json().get("data") or {}
        items = payload.get("items") or []
        return {item.get("index_code"): item for item in items if item.get("index_code")}


def month_end_points(records):
    records = sorted(records, key=lambda item: item["date"])
    if not records:
        return []

    buckets = {}
    for item in records:
        bucket = item["date"][:7]
        buckets[bucket] = item

    result = [buckets[key] for key in sorted(buckets.keys())]
    if result[-1]["date"] != records[-1]["date"]:
        result.append(records[-1])
    return result


def normalize_points(records, value_key):
    points = []
    for item in records:
        value = item.get(value_key)
        date = item.get("date")
        if value in (None, "") or not date:
            continue
        try:
            value = float(value)
        except (TypeError, ValueError):
            continue
        if value <= 0:
            continue
        points.append({"date": str(date), "value": round(value, 4)})
    return month_end_points(points)


def format_snapshot_date(item):
    date_text = item.get("date")
    ts = item.get("ts")
    if date_text and ts:
        shanghai_tz = timezone(timedelta(hours=8))
        year = datetime.fromtimestamp(int(ts) / 1000, tz=shanghai_tz).year
        return f"{year}-{date_text.replace('/', '-')}"
    if date_text:
        year = datetime.now().year
        return f"{year}-{date_text.replace('/', '-')}"
    if ts:
        shanghai_tz = timezone(timedelta(hours=8))
        return datetime.fromtimestamp(int(ts) / 1000, tz=shanghai_tz).strftime("%Y-%m-%d")
    return None


def build_snapshots(item):
    snapshot_date = format_snapshot_date(item)
    snapshots = {}
    pe_value = item.get("pe")
    pb_value = item.get("pb")
    pe_percentile = item.get("pe_percentile")
    pb_percentile = item.get("pb_percentile")

    if pe_value not in (None, ""):
        snapshots["pe"] = {
            "value": round(float(pe_value), 4),
            "percentile": round(float(pe_percentile) * 100, 2) if pe_percentile not in (None, "") else None,
            "date": snapshot_date,
            "source": "danjuan",
        }
    if pb_value not in (None, ""):
        snapshots["pb"] = {
            "value": round(float(pb_value), 4),
            "percentile": round(float(pb_percentile) * 100, 2) if pb_percentile not in (None, "") else None,
            "date": snapshot_date,
            "source": "danjuan",
        }
    return snapshots


def merge_snapshot_point(points, snapshot):
    if not snapshot or not snapshot.get("date") or snapshot.get("value") in (None, ""):
        return points

    merged = [dict(point) for point in points]
    merged.append({"date": snapshot["date"], "value": round(float(snapshot["value"]), 4)})
    return month_end_points(merged)


def build_card(config, danjuan_snapshots):
    snapshots = {}
    danjuan_item = danjuan_snapshots.get(config.get("danjuan_code")) if config.get("danjuan_code") else None
    if danjuan_item:
        snapshots = build_snapshots(danjuan_item)

    pe_points = []
    pb_points = []
    try:
        legu_client = LeguClient()
        if config["type"] == "all_a":
            pe_rows = legu_client.fetch_all_a_pe()
            pb_rows = legu_client.fetch_all_a_pb()
            pe_points = normalize_points(pe_rows, "averagePETTM")
            pb_points = normalize_points(pb_rows, "equalWeightAveragePB")
        elif config["type"] == "market":
            pe_rows = legu_client.fetch_market_pe(config["market_id"])
            pb_rows = legu_client.fetch_market_pb(config["market_id"])
            pe_points = normalize_points(pe_rows, "pe")
            pb_points = normalize_points(pb_rows, "addPb")
        else:
            pe_rows = legu_client.fetch_index_pe(config["index_code"])
            pb_rows = legu_client.fetch_index_pb(config["index_code"])
            pe_points = normalize_points(pe_rows, "ttmPe")
            pb_points = normalize_points(pb_rows, "addPb")
    except Exception:
        # Preserve the page even if one upstream call fails.
        pe_points = []
        pb_points = []

    pe_points = merge_snapshot_point(pe_points, snapshots.get("pe"))
    pb_points = merge_snapshot_point(pb_points, snapshots.get("pb"))

    return {
        "id": config["id"],
        "name": config["name"],
        "tag": config["tag"],
        "metrics": {
            "pe": pe_points,
            "pb": pb_points,
        },
        "snapshots": snapshots,
    }


def build_cards(danjuan_snapshots):
    with ThreadPoolExecutor(max_workers=min(LEGU_MAX_WORKERS, len(CARD_CONFIGS))) as executor:
        return list(executor.map(lambda config: build_card(config, danjuan_snapshots), CARD_CONFIGS))


def latest_date(cards):
    candidates = []
    for card in cards:
        for metric in card["metrics"].values():
            if metric:
                candidates.append(metric[-1]["date"])
        for snapshot in card.get("snapshots", {}).values():
            if snapshot and snapshot.get("date"):
                candidates.append(snapshot["date"])
    return max(candidates)


def build_html(payload):
    data_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    return HTML_TEMPLATE.replace("__DATA__", data_json)


def build_live_payload(base_payload):
    payload = json.loads(json.dumps(base_payload, ensure_ascii=False))
    cards_by_id = {card["id"]: card for card in payload["cards"]}

    danjuan_snapshots = DanjuanClient().fetch_snapshots()
    for config in CARD_CONFIGS:
        card = cards_by_id.get(config["id"])
        if not card:
            continue

        danjuan_item = danjuan_snapshots.get(config.get("danjuan_code")) if config.get("danjuan_code") else None
        if danjuan_item:
            snapshots = build_snapshots(danjuan_item)
            card["snapshots"] = snapshots
            for metric_key in ("pe", "pb"):
                card["metrics"][metric_key] = merge_snapshot_point(card["metrics"].get(metric_key, []), snapshots.get(metric_key))

    payload["updated_at"] = latest_date(payload["cards"])
    return payload


def build_payload():
    danjuan_client = DanjuanClient()
    cards = build_cards(danjuan_client.fetch_snapshots())
    return {
        "updated_at": latest_date(cards),
        "cards": cards,
    }


def main():
    payload = build_payload()
    html = build_html(payload)
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"Saved valuation dashboard to {OUTPUT_FILE.resolve()}")


if __name__ == "__main__":
    main()
