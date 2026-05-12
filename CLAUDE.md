# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **主要規則真源：`AGENTS.md`**。本文件是 Claude Code 生態的介面層，所有 AI 協作硬規則、工作流程、驗證矩陣以 `AGENTS.md` 為準。

---

## 常用命令

### 後端

```bash
# 安裝依賴
pip install -r requirements.txt

# 執行分析（各模式）
python main.py
python main.py --debug
python main.py --dry-run
python main.py --stocks 600519,hk00700,AAPL
python main.py --market-review
python main.py --schedule

# 啟動 API 服務（含 Web UI）
python main.py --serve-only
uvicorn server:app --reload --host 0.0.0.0 --port 8000

# 啟動 Web UI
python main.py --webui
python main.py --webui-only   # 訪問 http://127.0.0.1:8000
```

### 測試與 CI

```bash
# 完整 CI 驗證（本地執行）
./scripts/ci_gate.sh

# 只執行離線測試（不需要網路）
python -m pytest -m "not network"

# 執行特定測試
python -m pytest tests/test_foo.py

# 語法快速檢查
python -m py_compile <changed_python_files>

# Flake8 只檢查嚴重錯誤
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# AI 協作資產一致性檢查
python scripts/check_ai_assets.py
```

### 前端（`apps/dsa-web/`）

```bash
cd apps/dsa-web
npm ci
npm run lint
npm run build
npm run dev          # 本地開發
npm run test         # 單元測試
npx playwright test  # E2E 測試
```

### 桌面端（`apps/dsa-desktop/`）

```bash
cd apps/dsa-desktop
npm install
npm run build   # 需先構建 dsa-web
```

---

## 架構總覽

系統是**股票智能分析平台**，支援 A 股、港股、美股。主流程：**資料抓取 → 技術分析/新聞檢索 → LLM 分析 → 報告生成 → 通知推送**。

### 主要入口

| 入口 | 說明 |
|------|------|
| `main.py` | 分析任務主排程器，CLI 入口，含線程池並發控制 |
| `server.py` | FastAPI 服務啟動器，委派給 `api/app.py` |
| `apps/dsa-web/` | React + Vite 前端，對應 `/api/v1` 路由 |
| `apps/dsa-desktop/` | Electron 桌面殼，內嵌 dsa-web |
| `.github/workflows/` | CI、每日排程、Docker 發布、自動 tag |

### 後端層次

```
main.py
  └─ src/core/pipeline.py        # 整個分析流水線，並發控制，異常隔離
       ├─ data_provider/          # 多資料源適配層（優先級 0-5，自動 fallback）
       │    ├─ efinance_fetcher   # Priority 0（東方財富）
       │    ├─ akshare_fetcher    # Priority 1
       │    ├─ tushare/pytdx      # Priority 2
       │    ├─ baostock           # Priority 3
       │    ├─ yfinance           # Priority 4
       │    └─ longbridge         # Priority 5（港股/美股兜底）
       ├─ src/analyzer.py         # LLM 分析層，透過 LiteLLM 統一呼叫各模型
       ├─ src/search_service.py   # 多搜索源聚合（Tavily/SerpAPI/Anspire 等）
       ├─ src/notification.py     # 通知路由，分發到各 sender
       └─ src/notification_sender/ # 各通知渠道實作（WeChat/飛書/TG/Discord 等）

src/
  ├─ core/           # 主流程編排（pipeline, market_review, trading_calendar）
  ├─ agent/          # Agent 系統（多 Agent 編排、策略問股）
  │    ├─ agents/    # 各專職 Agent（decision/intel/risk/technical/portfolio）
  │    ├─ tools/     # Agent 可呼叫工具（資料/搜索/分析/回測）
  │    └─ strategies/ # 策略路由，對應 strategies/*.yaml
  ├─ services/       # 業務服務層（分析/歷史/回測/持倉/匯入）
  ├─ repositories/   # 資料存取層（SQLAlchemy ORM）
  ├─ schemas/        # Pydantic schema（報告結構契約）
  └─ notification_sender/ # 通知渠道各自實作

api/
  └─ v1/endpoints/   # FastAPI RESTful 端點（analysis/history/agent/backtest 等）

strategies/          # YAML 格式的內建策略定義（均線/纏論/波浪等 11 種）
```

### 設定系統

- 所有設定從 `.env` 讀取，範本在 `.env.example`
- `src/config.py` 提供單例 `Config`，透過 `get_config()` 取得
- LLM 透過 LiteLLM 統一路由，支援多 API Key 輪詢與 fallback
- 自動 tag 觸發條件：commit title 含 `#patch`、`#minor` 或 `#major`

### 高風險區域

修改以下區域時需特別注意兼容性與 fallback 路徑：
- `data_provider/`：資料源優先級與降級邏輯
- `src/schemas/`：報告結構契約（後端+前端均依賴）
- `api/v1/endpoints/`：API 行為（Web/Desktop 客戶端依賴）
- `src/services/image_stock_extractor.py`：`EXTRACT_PROMPT` 變更需在 PR 中附完整新 prompt
- `.github/workflows/`：排程觸發、Docker 發布、自動 tag

### 目錄邊界

- 後端邏輯：`src/`、`data_provider/`、`api/`、`bot/`
- Web 前端：`apps/dsa-web/`
- 桌面端：`apps/dsa-desktop/`
- 部署/流水線：`scripts/`、`.github/workflows/`、`docker/`
- 策略定義：`strategies/*.yaml`
- 測試：`tests/`（pytest，離線測試標記 `not network`）
