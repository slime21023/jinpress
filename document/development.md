# 開發指南

本指南介紹如何使用 JinPress 的開發功能，包括開發伺服器、即時重載和除錯技巧。

## 開發伺服器

JinPress 提供內建的開發伺服器，支援即時重載和錯誤處理。

### 啟動開發伺服器

```bash
# 基本啟動
jinpress serve

# 自定義主機和埠號
jinpress serve --host 0.0.0.0 --port 3000

# 使用自定義配置檔案
jinpress serve --config custom-config.yml

# 詳細模式（顯示除錯資訊）
jinpress serve --verbose
```

### 開發伺服器功能

- **即時重載**：檔案變更時自動重新構建和刷新瀏覽器
- **錯誤處理**：構建錯誤會顯示在終端中
- **靜態檔案服務**：提供構建後的靜態檔案
- **優雅關閉**：使用 Ctrl+C 停止伺服器

### 監控的檔案類型

開發伺服器會監控以下檔案變更：

```
docs/**/*.md          # Markdown 檔案
config.yml            # 配置檔案
static/**/*           # 用戶靜態檔案
templates/**/*        # 自定義模板（如果存在）
```

## 即時重載

### 工作原理

1. **檔案監控**：使用 `watchdog` 庫監控檔案系統變更
2. **去抖動**：短時間內的多次變更會被合併處理
3. **增量構建**：只重新處理變更的檔案（如果可能）
4. **瀏覽器刷新**：構建完成後自動刷新瀏覽器

### 支援的變更類型

- **Markdown 檔案**：內容變更、新增、刪除
- **配置檔案**：`config.yml` 變更會觸發完整重建
- **靜態檔案**：CSS、JS、圖片等檔案變更
- **模板檔案**：自定義模板變更

### 除外檔案

以下檔案變更不會觸發重建：

```
dist/**/*             # 輸出目錄
.jinpress/cache/**/*  # 快取目錄
.git/**/*             # Git 目錄
node_modules/**/*     # Node.js 模組
__pycache__/**/*      # Python 快取
*.pyc                 # Python 編譯檔案
.DS_Store             # macOS 系統檔案
Thumbs.db             # Windows 系統檔案
```

## 開發工作流程

### 典型的開發流程

1. **初始化專案**
   ```bash
   jinpress init my-docs
   cd my-docs
   ```

2. **啟動開發伺服器**
   ```bash
   jinpress serve
   ```

3. **編輯內容**
   - 修改 `docs/` 中的 Markdown 檔案
   - 更新 `config.yml` 配置
   - 添加靜態資源到 `static/`

4. **即時預覽**
   - 瀏覽器會自動刷新顯示變更
   - 檢查終端中的構建日誌

5. **構建生產版本**
   ```bash
   jinpress build
   ```

### 多人協作

```bash
# 團隊成員克隆專案
git clone https://github.com/team/docs.git
cd docs

# 安裝 JinPress
pip install jinpress

# 啟動開發伺服器
jinpress serve

# 創建功能分支
git checkout -b feature/new-section

# 編輯內容...

# 提交變更
git add .
git commit -m "Add new section"
git push origin feature/new-section
```

## 除錯技巧

### 詳細日誌

啟用詳細模式查看詳細的構建資訊：

```bash
jinpress serve --verbose
```

輸出範例：

```
DEBUG    jinpress.builder:builder.py:58 Cleaning output directory
DEBUG    jinpress.builder:builder.py:63 Created output directory: /path/to/project/dist
INFO     jinpress.builder:builder.py:67 Processed 5 pages
DEBUG    jinpress.theme.engine:engine.py:195 Copied theme assets
DEBUG    jinpress.search:search.py:89 Generated search index with 5 documents
INFO     jinpress.builder:builder.py:81 Site built successfully in /path/to/project/dist
```

### 常見錯誤和解決方案

#### 1. 配置檔案錯誤

```
❌ Configuration error: Invalid YAML in config file
```

**解決方案**：
- 檢查 YAML 語法
- 確認縮排正確
- 使用 YAML 驗證器

```bash
# 使用 Python 驗證 YAML
python -c "import yaml; yaml.safe_load(open('config.yml'))"
```

#### 2. Markdown 處理錯誤

```
WARNING  jinpress.builder:builder.py:116 Failed to process /path/to/file.md: Invalid YAML front matter
```

**解決方案**：
- 檢查 front matter 語法
- 確認 YAML 格式正確
- 檢查特殊字符轉義

#### 3. 模板錯誤

```
❌ Build error: Error rendering template 'page.html': template not found
```

**解決方案**：
- 確認模板檔案存在
- 檢查模板路徑
- 驗證模板語法

#### 4. 靜態檔案問題

```
WARNING  jinpress.builder:builder.py:186 Failed to copy static files: Permission denied
```

**解決方案**：
- 檢查檔案權限
- 確認目錄存在
- 檢查磁碟空間

### 除錯工具

#### 1. 檢查專案資訊

```bash
jinpress info
```

輸出專案的詳細資訊，包括配置、檔案統計等。

#### 2. 驗證構建

```bash
# 構建並檢查輸出
jinpress build --verbose
ls -la dist/

# 檢查生成的 HTML
head dist/index.html
```

#### 3. 測試本地伺服器

```bash
# 使用 Python 內建伺服器測試構建結果
cd dist
python -m http.server 8000
```

#### 4. 檢查搜尋索引

```bash
# 檢查搜尋索引是否正確生成
cat dist/search-index.json | python -m json.tool
```

## 效能優化

### 開發時的效能考慮

#### 1. 大型專案優化

對於包含大量檔案的專案：

```bash
# 使用增量構建（避免 --clean）
jinpress build --no-clean

# 只監控特定目錄
# （需要在自定義腳本中實現）
```

#### 2. 圖片優化

```bash
# 開發時使用較小的圖片
# 生產時使用優化後的圖片
```

#### 3. 快取利用

JinPress 會自動使用 `.jinpress/cache/` 目錄快取處理結果。

### 記憶體使用優化

```python
# 如果遇到記憶體問題，可以調整 Python 設定
export PYTHONHASHSEED=0
export PYTHONOPTIMIZE=1
```

## 自定義開發工具

### 自動化腳本

創建 `scripts/dev.py` 來自動化開發任務：

```python
#!/usr/bin/env python3
"""
開發輔助腳本
"""
import subprocess
import sys
from pathlib import Path

def serve():
    """啟動開發伺服器"""
    subprocess.run(['jinpress', 'serve', '--verbose'])

def build():
    """構建網站"""
    subprocess.run(['jinpress', 'build'])

def deploy():
    """構建並部署"""
    subprocess.run(['jinpress', 'build'])
    # 添加部署邏輯
    print("部署完成！")

def new_page(title):
    """創建新頁面"""
    slug = title.lower().replace(' ', '-')
    filename = f"docs/{slug}.md"
    
    content = f"""---
title: "{title}"
description: ""
---

# {title}

頁面內容...
"""
    
    Path(filename).write_text(content, encoding='utf-8')
    print(f"創建新頁面：{filename}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("使用方法：python scripts/dev.py [serve|build|deploy|new] [args...]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'serve':
        serve()
    elif command == 'build':
        build()
    elif command == 'deploy':
        deploy()
    elif command == 'new':
        if len(sys.argv) < 3:
            print("請提供頁面標題")
            sys.exit(1)
        new_page(sys.argv[2])
    else:
        print(f"未知命令：{command}")
```

使用方式：

```bash
# 啟動開發伺服器
python scripts/dev.py serve

# 構建網站
python scripts/dev.py build

# 創建新頁面
python scripts/dev.py new "新頁面標題"
```

### Git Hooks

設定 Git hooks 來自動化任務：

```bash
# .git/hooks/pre-commit
#!/bin/bash
echo "檢查構建..."
jinpress build
if [ $? -ne 0 ]; then
    echo "構建失敗，提交被拒絕"
    exit 1
fi
echo "構建成功"
```

### VS Code 整合

創建 `.vscode/tasks.json`：

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "JinPress: Serve",
            "type": "shell",
            "command": "jinpress",
            "args": ["serve"],
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "new"
            },
            "problemMatcher": []
        },
        {
            "label": "JinPress: Build",
            "type": "shell",
            "command": "jinpress",
            "args": ["build"],
            "group": {
                "kind": "build",
                "isDefault": true
            },
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            },
            "problemMatcher": []
        }
    ]
}
```

創建 `.vscode/launch.json`：

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "JinPress Debug",
            "type": "python",
            "request": "launch",
            "module": "jinpress.cli",
            "args": ["serve", "--verbose"],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        }
    ]
}
```

## 測試和品質保證

### 內容驗證

創建內容驗證腳本：

```python
# scripts/validate.py
import re
from pathlib import Path

def validate_markdown_files():
    """驗證 Markdown 檔案"""
    docs_dir = Path('docs')
    errors = []
    
    for md_file in docs_dir.rglob('*.md'):
        content = md_file.read_text(encoding='utf-8')
        
        # 檢查 front matter
        if not content.startswith('---\n'):
            errors.append(f"{md_file}: 缺少 front matter")
        
        # 檢查標題結構
        lines = content.split('\n')
        h1_count = sum(1 for line in lines if line.startswith('# '))
        if h1_count != 1:
            errors.append(f"{md_file}: 應該只有一個 H1 標題")
        
        # 檢查連結
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        for text, url in links:
            if url.startswith('./') and url.endswith('.md'):
                target_file = md_file.parent / url[2:]
                if not target_file.exists():
                    errors.append(f"{md_file}: 連結目標不存在 {url}")
    
    return errors

if __name__ == '__main__':
    errors = validate_markdown_files()
    if errors:
        print("發現以下問題：")
        for error in errors:
            print(f"  - {error}")
    else:
        print("所有檔案驗證通過！")
```

### 自動化測試

```bash
# 創建測試腳本
cat > scripts/test.sh << 'EOF'
#!/bin/bash
set -e

echo "開始測試..."

# 驗證內容
python scripts/validate.py

# 構建測試
echo "測試構建..."
jinpress build

# 檢查輸出檔案
echo "檢查輸出檔案..."
if [ ! -f "dist/index.html" ]; then
    echo "錯誤：index.html 未生成"
    exit 1
fi

if [ ! -f "dist/search-index.json" ]; then
    echo "錯誤：搜尋索引未生成"
    exit 1
fi

echo "所有測試通過！"
EOF

chmod +x scripts/test.sh
```

## 最佳實踐

### 開發環境設定

1. **使用虛擬環境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate     # Windows
   pip install jinpress
   ```

2. **版本控制**
   ```gitignore
   # .gitignore
   dist/
   .jinpress/cache/
   __pycache__/
   *.pyc
   .env
   venv/
   ```

3. **文檔結構**
   ```
   docs/
   ├── index.md              # 首頁
   ├── guide/                # 指南
   │   ├── index.md
   │   └── ...
   ├── api/                  # API 文檔
   └── examples/             # 範例
   ```

### 內容編寫

1. **一致的 Front Matter**
   ```yaml
   ---
   title: "頁面標題"
   description: "頁面描述"
   date: "2025-01-19"
   ---
   ```

2. **清晰的檔案命名**
   ```
   getting-started.md        # 好
   GettingStarted.md         # 避免
   getting_started.md        # 可以，但不推薦
   ```

3. **合理的目錄結構**
   ```
   docs/
   ├── guide/
   │   ├── index.md          # 指南首頁
   │   ├── installation.md
   │   └── configuration.md
   └── api/
       ├── index.md          # API 首頁
       └── reference.md
   ```

### 效能考慮

1. **圖片優化**：使用適當大小和格式的圖片
2. **內容分頁**：避免單個頁面過長
3. **合理的導航結構**：不要過深的層級結構