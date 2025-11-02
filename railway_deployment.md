# Railway 部署指南 - 自動交易機器人

## 📋 環境變量配置清單

在 Railway 的 Variables 標籤中，添加以下環境變量：

### 🔧 系統配置

```
# 環境設定
ENVIRONMENT=production

# 日誌級別
LOG_LEVEL=INFO

# 數據存儲路徑（Railway持久化存儲）
DATA_PATH=/app/data

# 模型存儲路徑
MODELS_PATH=/app/models

# Railway自動提供的PORT變量（無需手動設置）
# PORT=自動設置
```

### 🔑 Binance API 配置

```
# Binance API 密鑰（如需實盤交易）
BINANCE_API_KEY=你的Binance_API_Key

# Binance API 秘密（如需實盤交易）
BINANCE_API_SECRET=你的Binance_API_Secret

# 是否使用測試網（True/False）
BINANCE_TESTNET=False
```

### 💰 交易配置

```
# 是否啟用真實交易（False=模擬交易）
TRADING_ENABLED=False

# 是否使用模擬交易模式
PAPER_TRADING=True

# 最大並發持倉數量
MAX_CONCURRENT_POSITIONS=5

# 最大槓桿倍數
MAX_LEVERAGE=125

# 每日損失限額（百分比）
DAILY_LOSS_LIMIT=0.05

# 最大回撤（百分比）
MAX_DRAWDOWN=0.10
```

### 📊 數據庫配置（可選）

如果使用Railway PostgreSQL插件，會自動提供：
```
DATABASE_URL=自動生成
```

---

## 🚀 部署步驟

### 1. 在 Railway 創建新項目

1. 前往 [Railway.app](https://railway.app)
2. 點擊 "New Project"
3. 選擇 "Deploy from GitHub repo" 或 "Empty Project"

### 2. 連接 GitHub Repository（推薦）

1. 將代碼推送到 GitHub
2. 在 Railway 中授權 GitHub 訪問
3. 選擇您的倉庫

### 3. 配置環境變量

在 Railway 項目的 **Variables** 標籤中：

**方法一：逐個添加**
- 點擊 "New Variable"
- 輸入變量名和值（不要加引號）
- 點擊 "Add"

**方法二：批量導入（RAW Editor）**
- 點擊 "RAW Editor"
- 複製下方完整配置並粘貼
- 點擊 "Update Variables"

```plaintext
ENVIRONMENT=production
LOG_LEVEL=INFO
DATA_PATH=/app/data
MODELS_PATH=/app/models
BINANCE_API_KEY=
BINANCE_API_SECRET=
BINANCE_TESTNET=False
TRADING_ENABLED=False
PAPER_TRADING=True
MAX_CONCURRENT_POSITIONS=5
MAX_LEVERAGE=125
DAILY_LOSS_LIMIT=0.05
MAX_DRAWDOWN=0.10
```

### 4. 添加啟動命令

在 Railway 項目設置中：
- **Start Command**: `python main.py`
- **Build Command**: `pip install -r requirements.txt`（通常自動檢測）

### 5. 配置持久化存儲（重要！）

Railway 預設不保留重啟後的文件，需要添加 Volume：

1. 在 Service 設置中點擊 "Volumes"
2. 添加 Volume：
   - **Mount Path**: `/app/data`
   - **Size**: 1GB（根據需求調整）
3. 再添加一個 Volume：
   - **Mount Path**: `/app/models`
   - **Size**: 1GB

### 6. 部署應用

1. 點擊 "Deploy"
2. 查看部署日誌確認成功

---

## 📝 重要配置說明

### 安全建議

**⚠️ 絕對不要在代碼中硬編碼 API 密鑰！**

1. **模擬交易模式**（推薦用於測試）
   ```
   TRADING_ENABLED=False
   PAPER_TRADING=True
   BINANCE_API_KEY=（可留空）
   BINANCE_API_SECRET=（可留空）
   ```

2. **實盤交易模式**（充分測試後）
   ```
   TRADING_ENABLED=True
   PAPER_TRADING=False
   BINANCE_API_KEY=你的真實密鑰
   BINANCE_API_SECRET=你的真實秘密
   BINANCE_TESTNET=False
   ```

3. **測試網模式**（Binance Testnet）
   ```
   TRADING_ENABLED=True
   PAPER_TRADING=False
   BINANCE_API_KEY=測試網密鑰
   BINANCE_API_SECRET=測試網秘密
   BINANCE_TESTNET=True
   ```

### Railway 特定注意事項

1. **PORT 環境變量**
   - Railway 自動提供 `PORT` 變量
   - 應用必須綁定到 `0.0.0.0:$PORT`
   - 本項目已配置為 `0.0.0.0:5000`（需要調整）

2. **持久化存儲**
   - 必須使用 Railway Volumes 保存數據庫和模型
   - 未配置 Volume 的數據會在重啟後丟失

3. **環境變量安全**
   - 可使用 "Seal" 功能隱藏敏感變量
   - 點擊變量右側三點菜單 → "Seal"

---

## 🔍 訪問 Web 儀表板

部署成功後，Railway 會提供一個公開 URL：
- 格式：`https://你的項目名.up.railway.app`
- 訪問此 URL 即可查看交易儀表板

---

## 🐛 故障排除

### 問題1: 應用無法啟動
**檢查項目**：
- 確認 `requirements.txt` 包含所有依賴
- 查看 Railway 部署日誌
- 確認 PORT 綁定正確

### 問題2: 數據丟失
**解決方案**：
- 確保配置了 Railway Volumes
- 檢查 Mount Path 是否正確

### 問題3: WebSocket 連接失敗
**可能原因**：
- Binance API 地區限制
- 系統會自動重連，屬於正常情況

### 問題4: 環境變量未生效
**解決方案**：
- 添加變量後點擊 "Deploy"
- 檢查變量名稱是否正確（區分大小寫）
- 不要在值周圍加引號

---

## 📊 監控和日誌

### 查看應用日誌
1. 在 Railway 項目中點擊 "Deployments"
2. 選擇當前部署
3. 查看實時日誌

### 性能監控
Railway 提供基本的 CPU/內存監控：
- 在 Service 概覽中查看資源使用情況

---

## 💡 優化建議

1. **生產環境優化**
   - 設置 `ENVIRONMENT=production`
   - 啟用錯誤追蹤（如 Sentry）
   - 配置自動重啟策略

2. **成本優化**
   - 使用 Railway 的 Sleep 功能（閒置時暫停）
   - 注意：交易機器人需要24/7運行

3. **安全加固**
   - 定期輪換 API 密鑰
   - 使用 IP 白名單
   - 監控異常交易

---

## 📞 支援資源

- Railway 官方文檔：https://docs.railway.app
- 本項目 README：查看 `README.md`
- 系統架構：查看 `replit.md`

---

## ✅ 部署檢查清單

- [ ] GitHub 倉庫已創建並推送代碼
- [ ] Railway 項目已創建
- [ ] 環境變量已全部配置
- [ ] Volumes 已添加（/app/data 和 /app/models）
- [ ] 啟動命令已設置
- [ ] 部署成功並查看日誌
- [ ] Web 儀表板可訪問
- [ ] 模擬交易模式測試通過
- [ ] （可選）實盤交易前充分測試

---

**注意**：首次部署建議使用模擬交易模式（PAPER_TRADING=True）進行測試！
