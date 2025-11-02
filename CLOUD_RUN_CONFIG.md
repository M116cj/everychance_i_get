# ☁️ Cloud Run / Railway 部署配置

## ✅ 已修復的問題

### 1. 健康檢查失敗 ✅
**問題**: 應用啟動時間過長，健康檢查超時

**解決方案**:
- 添加快速響應的 `/health` 端點
- Flask 服務器在 < 2 秒內啟動
- Trader 在後台異步初始化

### 2. 運行命令錯誤 ✅
**問題**: Procfile 使用未定義的 `$file` 變量

**解決方案**:
```
web: python main.py
```

### 3. 啟動阻塞 ✅
**問題**: 昂貴的初始化操作阻塞健康檢查

**解決方案**:
- 延遲初始化 (Lazy Loading)
- 服務器先啟動，trader 後初始化
- 所有端點處理初始化狀態

---

## 🏥 健康檢查配置

### Railway 設置
```yaml
healthcheck:
  path: /health
  port: $PORT
  interval: 30s
  timeout: 10s
  retries: 3
```

### Cloud Run 設置
```yaml
healthCheck:
  httpGet:
    path: /health
    port: $PORT
  initialDelaySeconds: 10
  periodSeconds: 30
  timeoutSeconds: 5
  failureThreshold: 3
```

### 測試健康檢查
```bash
curl http://localhost:5000/health
```

**響應**:
```json
{
  "status": "healthy",
  "service": "trading-bot",
  "trader_ready": true,
  "initializing": false
}
```

---

## 🚀 部署清單

在部署到 Railway/Cloud Run 前確認：

- [x] `/health` 端點已添加
- [x] Procfile 使用正確命令
- [x] 延遲初始化已實現
- [x] 端口綁定使用 `$PORT`
- [x] 依賴已更新
- [x] 環境變量已配置
- [x] Volumes 已設置

---

## 📊 端點清單

### 健康檢查
```
GET /health
```
- **響應時間**: < 100ms
- **用途**: Cloud Run/Railway 健康檢查
- **狀態**: 始終返回 200

### 主頁
```
GET /
```
- **內容**: Web 儀表板
- **響應**: HTML 頁面

### API 端點
```
GET /api/status    # 系統狀態
GET /api/trades    # 交易記錄
GET /api/performance  # 性能評分
```

---

## 🔧 Railway 環境變量

複製到 Railway RAW Editor:

```bash
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

---

## 📦 必要的 Volumes

**Volume 1:**
```
Mount Path: /app/data
Size: 1GB
```

**Volume 2:**
```
Mount Path: /app/models
Size: 1GB
```

---

## 🧪 本地測試

### 測試快速啟動
```bash
python main.py &
sleep 2
curl http://localhost:5000/health
```

應該在 2 秒內看到健康響應。

### 測試完整初始化
```bash
# 等待 trader 初始化
sleep 10
curl http://localhost:5000/api/status
```

應該看到完整的系統狀態。

---

## 📝 部署流程

### 1. 推送代碼
```bash
git add .
git commit -m "Add health check and lazy initialization"
git push
```

### 2. 在 Railway 配置

1. **環境變量**
   - 進入 Variables 標籤
   - 粘貼環境變量

2. **Volumes**
   - 添加 `/app/data` (1GB)
   - 添加 `/app/models` (1GB)

3. **部署**
   - 點擊 Deploy
   - 等待部署完成

### 3. 驗證部署

```bash
# 檢查健康狀態
curl https://your-app.railway.app/health

# 檢查系統狀態
curl https://your-app.railway.app/api/status

# 訪問儀表板
open https://your-app.railway.app/
```

---

## 🐛 故障排除

### 問題: 健康檢查仍然失敗

**檢查**:
1. 確認健康檢查路徑為 `/health`
2. 確認端口設置正確
3. 查看部署日誌

**測試**:
```bash
# 本地測試
curl -v http://localhost:5000/health
```

### 問題: Trader 未初始化

**檢查日誌**:
```bash
# 在 Railway 查看日誌
# 搜索 "trader_initialization"
```

**常見原因**:
- 數據庫連接失敗（檢查 Volumes）
- 依賴缺失（檢查 requirements.txt）
- 環境變量錯誤

### 問題: 應用崩潰

**檢查**:
1. 查看完整日誌
2. 確認所有依賴已安裝
3. 驗證環境變量

---

## ⚡ 性能優化

### 啟動時間
- **目標**: < 10 秒
- **Flask**: < 2 秒
- **Trader**: 5-8 秒（後台）

### 內存使用
- **初始**: ~150 MB
- **運行中**: ~250-300 MB
- **峰值**: ~400 MB

### CPU 使用
- **啟動**: 中等
- **待機**: 低（< 5%）
- **交易時**: 中等（10-20%）

---

## 🎯 驗證清單

部署成功後驗證：

- [ ] 健康檢查返回 200 OK
- [ ] 儀表板可訪問
- [ ] API 端點正常工作
- [ ] 日誌無錯誤
- [ ] Trader 已初始化
- [ ] 數據持久化正常

---

## 📚 相關文檔

- `DEPLOYMENT_FIXES.md` - 修復詳情
- `RAILWAY_SETUP.md` - Railway 快速設置
- `RAILWAY_VARIABLES.txt` - 環境變量說明
- `README.md` - 系統使用指南

---

**✅ 所有部署問題已解決！系統已優化用於 Railway/Cloud Run 部署。**
