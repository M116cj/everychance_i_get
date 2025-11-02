# 🚀 Railway 部署環境變量

## 快速配置（複製到 Railway RAW Editor）

```bash
# 系統配置
ENVIRONMENT=production
LOG_LEVEL=INFO
DATA_PATH=/app/data
MODELS_PATH=/app/models

# Binance API（模擬交易可留空）
BINANCE_API_KEY=
BINANCE_API_SECRET=
BINANCE_TESTNET=False

# 交易配置
TRADING_ENABLED=False
PAPER_TRADING=True
MAX_CONCURRENT_POSITIONS=5
MAX_LEVERAGE=125
DAILY_LOSS_LIMIT=0.05
MAX_DRAWDOWN=0.10
```

## 📋 環境變量說明

| 變量名 | 說明 | 預設值 | 必填 |
|--------|------|--------|------|
| `ENVIRONMENT` | 環境類型 (development/production) | production | ❌ |
| `LOG_LEVEL` | 日誌級別 (DEBUG/INFO/WARNING/ERROR) | INFO | ❌ |
| `DATA_PATH` | 數據庫存儲路徑 | /app/data | ❌ |
| `MODELS_PATH` | 模型存儲路徑 | /app/models | ❌ |
| `BINANCE_API_KEY` | Binance API 密鑰 | 空 | 實盤必填 |
| `BINANCE_API_SECRET` | Binance API 秘密 | 空 | 實盤必填 |
| `BINANCE_TESTNET` | 是否使用測試網 | False | ❌ |
| `TRADING_ENABLED` | 是否啟用真實交易 | False | ❌ |
| `PAPER_TRADING` | 是否模擬交易 | True | ❌ |
| `MAX_CONCURRENT_POSITIONS` | 最大並發持倉 | 5 | ❌ |
| `MAX_LEVERAGE` | 最大槓桿倍數 | 125 | ❌ |
| `DAILY_LOSS_LIMIT` | 每日損失限額 | 0.05 (5%) | ❌ |
| `MAX_DRAWDOWN` | 最大回撤限制 | 0.10 (10%) | ❌ |

**注意**: `PORT` 由 Railway 自動提供，無需設置

---

## 🔧 Railway 部署步驟

### 1️⃣ 創建項目
1. 登入 [Railway.app](https://railway.app)
2. New Project → Deploy from GitHub repo
3. 選擇您的倉庫

### 2️⃣ 配置環境變量
1. 進入項目 → Variables 標籤
2. 點擊 **RAW Editor**
3. 複製上方環境變量配置並粘貼
4. 點擊 **Update Variables**

### 3️⃣ 添加持久化存儲 ⚠️ **重要！**
1. 進入 Service 設置 → Volumes
2. 添加第一個 Volume:
   - **Mount Path**: `/app/data`
   - **Size**: 1GB
3. 添加第二個 Volume:
   - **Mount Path**: `/app/models`
   - **Size**: 1GB

### 4️⃣ 部署
1. 點擊 **Deploy**
2. 查看部署日誌確認成功
3. 訪問生成的 URL 查看儀表板

---

## 🎯 三種部署模式

### 模式 1：完全模擬（推薦首次部署）
```bash
TRADING_ENABLED=False
PAPER_TRADING=True
BINANCE_API_KEY=         # 留空
BINANCE_API_SECRET=      # 留空
```
✅ 無需 API 密鑰，安全測試系統

### 模式 2：測試網交易
```bash
TRADING_ENABLED=True
PAPER_TRADING=False
BINANCE_TESTNET=True
BINANCE_API_KEY=你的測試網密鑰
BINANCE_API_SECRET=你的測試網秘密
```
✅ 使用 Binance Testnet，無真實資金風險

### 模式 3：實盤交易（充分測試後）
```bash
TRADING_ENABLED=True
PAPER_TRADING=False
BINANCE_TESTNET=False
BINANCE_API_KEY=你的真實密鑰
BINANCE_API_SECRET=你的真實秘密
```
⚠️ 使用真實資金，謹慎操作

---

## 📊 訪問儀表板

部署成功後，Railway 會生成公開 URL:
- 格式: `https://你的項目名.up.railway.app`
- 直接訪問即可查看實時交易數據

---

## 🔐 安全建議

1. ✅ **使用 Railway 的 Seal 功能隱藏 API 密鑰**
   - 點擊變量右側 ⋮ → Seal
   
2. ✅ **在 Binance 啟用 IP 白名單**
   - 只允許 Railway IP 訪問

3. ✅ **定期輪換 API 密鑰**

4. ⚠️ **首次部署必須使用模擬模式測試**

---

## 🐛 常見問題

### Q: 部署後數據丟失？
**A**: 必須配置 Railway Volumes，否則重啟會丟失數據

### Q: 無法連接 Binance？
**A**: 檢查 API 密鑰是否正確，是否使用了測試網/主網配置

### Q: WebSocket 顯示錯誤？
**A**: HTTP 451 錯誤是地區限制，系統會自動重連，不影響功能

### Q: 環境變量修改後沒生效？
**A**: 修改變量後必須點擊 "Deploy" 重新部署

---

## 📞 技術支援

- 詳細部署文檔: `railway_deployment.md`
- 環境變量詳細說明: `RAILWAY_VARIABLES.txt`
- 系統使用說明: `README.md`

---

**⚡ 快速開始**: 複製上方環境變量 → 粘貼到 Railway → 添加 Volumes → 部署 ✨
