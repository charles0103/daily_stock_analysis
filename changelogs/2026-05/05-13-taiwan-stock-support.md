# 2026-05-13 新增台灣股市支援

## 🎯 功能概述

- 影響範圍：資料源路由、代碼正規化、市場識別、交易日曆、LLM 分析框架
- 複雜度：中等（修改 5 個核心檔案，無需新增資料源）

## ⚡ 實作方案

### `data_provider/base.py`
- 新增 `_is_tw_market()`：識別 `TW2330`、`2330.TW`、`6488.TWO`、純 4 位數字等格式
- 更新 `normalize_stock_code()`：`.TW`/`.TWO` 後綴正規化為 `TW` 前綴（`2330.TW` → `TW2330`）
- 更新 `_market_tag()`：加入 `tw` 市場標籤，台股不再被誤判為 A 股
- 更新 `_DAILY_MARKET_FETCHER_SUPPORT`：`YfinanceFetcher` 加入 `tw`
- 更新 `_filter_daily_fetchers_for_market()`：合法市場集合加入 `tw`

### `data_provider/yfinance_fetcher.py`
- 更新 `_convert_stock_code()`：`TW2330` → `2330.TW`（Yahoo Finance 格式）
- 新增 `_get_tw_stock_realtime_quote()`：透過 yfinance history 取得台股即時報價
- 更新 `get_realtime_quote()`：加入台股路由

### `src/core/trading_calendar.py`
- `MARKET_EXCHANGE` 加入 `"tw": "XTAI"`
- `MARKET_TIMEZONE` 加入 `"tw": "Asia/Taipei"`
- `get_market_for_stock()` 識別台股代碼，回傳 `"tw"`

### `src/config.py`
- `_parse_stock_market_filter()` 加入 `tw` 合法值

### `src/market_context.py`
- `detect_market()` 加入台股識別邏輯，修正 `TW2330` 被誤判為 `cn` 的問題
- `_MARKET_ROLES` 加入台股中英文描述
- `_MARKET_GUIDELINES` 加入台股 LLM 分析框架（±10% 漲跌停、T+2 交割、外資動向等）

## ✅ 驗證結果

- Python 語法檢查全部通過
- `normalize_stock_code` / `_is_tw_market` / `_market_tag` 單元邏輯驗證通過
- `detect_market("TW2330")` 正確回傳 `"tw"`

## 📊 修改統計

- 修改 5 個檔案，新增 157 行，修改 13 行
- 無新增資料源依賴（yfinance 本身支援 `.TW` 後綴）

## 使用方式

```env
# .env 或 GitHub Actions Variables
STOCK_LIST=TW2330,TW2317,TW0050
STOCK_MARKET_FILTER=tw        # 純台股；留空則混合分析

# 或混合分析
STOCK_LIST=AAPL,TSLA,TW2330,TW2317
STOCK_MARKET_FILTER=           # 留空
```
