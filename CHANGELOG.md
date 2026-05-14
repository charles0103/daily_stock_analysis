# Changelog

### 🐛 2026-05-14 - 台股股票名稱無法動態查詢
**影響範圍**: `data_provider/base.py`、`data_provider/yfinance_fetcher.py`
**問題**: `get_stock_name` 未過濾台股不支援的 fetcher（baostock/pytdx/tushare），且 `YfinanceFetcher` 缺少 `get_stock_name` 方法，導致任何台股代碼皆無法取得名稱
**解決**: 新增台股 fetcher 過濾器；為 `YfinanceFetcher` 實作 `get_stock_name`，透過 yfinance `ticker.info` 動態查詢，查詢結果寫入快取
**成果**: ✅ 任意台股代碼（TW2330、TW2357、TW2423 等）皆可動態取得名稱，無需維護靜態映射表
