<div align="center">

# 🌊 WaveSense-CLI

**轻量级终端无线信号智能感知与分析引擎**
**Lightweight Terminal Wireless Signal Intelligence & Analysis Engine**

[简体中文](#简体中文) | [繁體中文](#繁體中文) | [English](#english)

</div>

---

## 简体中文

### 🎉 项目介绍

> 在拥挤的城市中，你身边至少有十几个WiFi信号在空气中交织。它们从哪里来？有多强？哪个信道最干净？——**WaveSense-CLI** 用一行命令告诉你答案。

**WaveSense-CLI** 是一个零外部依赖的 Python CLI 工具，专为无线信号扫描、智能分析与终端可视化而生。灵感来源于 GitHub 热门项目 [RuView](https://github.com/nicehash/RuView) 中 WiFi 信号空间智能的概念，我们在此基础上做了大量差异化创新：

- **零依赖哲学** —— 仅使用 Python 标准库，`pip install` 即用，无需纠结环境配置
- **真正的跨平台** —— Linux（nmcli/iwlist）、macOS（airport）、Windows（netsh）三端通吃
- **ASCII 可视化引擎** —— 热力图、条形图、折线图、分布直方图，全部在终端渲染
- **TUI 实时仪表盘** —— 键盘交互、自动刷新、异常告警，像用 htop 一样监控 WiFi
- **智能分析算法** —— Z-Score 异常检测、线性回归趋势、FSPL 距离估算，让数据说话

无论你是网络工程师排查信号干扰、开发者调试 IoT 设备，还是极客想了解身边的无线环境，WaveSense-CLI 都是你的瑞士军刀。

---

### ✨ 核心特性

| 特性 | 描述 |
|------|------|
| 📡 **跨平台扫描** | Linux / macOS / Windows 三端原生支持，自动检测平台并调用最优扫描命令 |
| 🧮 **智能分析** | Z-Score 异常检测、线性回归趋势分析、FSPL 自由空间路径损耗距离估算 |
| 🎨 **ASCII 可视化** | 信号热力图、强度条形图、趋势折线图、分布直方图 —— 全部 Unicode + ANSI 彩色渲染 |
| 🖥️ **TUI 仪表盘** | 实时刷新的终端仪表盘，支持键盘交互（排序/过滤/详情）、异常告警 |
| 📈 **持续监控** | 定时扫描 + 历史记录，追踪信号变化趋势，捕捉异常波动 |
| 📤 **多格式导出** | 一键导出 JSON / CSV / Markdown 格式报告，方便后续处理与分享 |
| 🪶 **零外部依赖** | 纯 Python 标准库实现，Python >= 3.7 即可运行，离线环境也毫无压力 |
| ⚡ **极速启动** | 毫秒级初始化，缓存机制避免重复扫描，`--simple` 模式兼容受限终端 |
| 🔍 **信道分析** | 自动分析 2.4GHz / 5GHz 信道拥挤度，推荐最优信道 |
| 🛡️ **健壮容错** | 多扫描器自动降级、超时重试、权限检测，优雅处理各种异常场景 |

---

### 🚀 快速开始

#### 环境要求

- **Python** >= 3.7（支持 3.7 ~ 3.12）
- **操作系统**：Linux / macOS / Windows
- **扫描权限**：部分平台需要管理员/root 权限执行 WiFi 扫描

#### 安装

```bash
# 方式一：pip 安装（推荐）
pip install wavesense-cli

# 方式二：pipx 安装（隔离环境）
pipx install wavesense-cli

# 方式三：从源码安装
git clone https://github.com/wavesense-cli/wavesense-cli.git
cd wavesense-cli
pip install .
```

#### 快速体验

```bash
# 扫描一次周围 WiFi 信号
wavesense scan

# 查看版本信息
wavesense -V

# 持续监控（每 5 秒刷新）
wavesense monitor -i 5

# 启动 TUI 实时仪表盘
wavesense dashboard

# 生成 Markdown 报告
wavesense report -f markdown -o report.md

# 查看信号热力图
wavesense heatmap
```

---

### 📖 详细使用指南

#### `wavesense scan` —— WiFi 信号扫描

```bash
# 基础扫描
wavesense scan

# 指定网络接口
wavesense scan -i wlan0

# 详细模式（显示统计信息）
wavesense scan -v

# JSON 格式输出
wavesense scan --json

# 导出为 CSV 文件
wavesense scan -f csv -o signals.csv

# 导出到指定路径
wavesense scan -f json -o /tmp/scan_result.json
```

#### `wavesense monitor` —— 持续监控模式

```bash
# 每 5 秒扫描一次（默认）
wavesense monitor

# 自定义扫描间隔（每 3 秒）
wavesense monitor -i 3

# 限制扫描次数（扫描 20 次后停止）
wavesense monitor -i 5 -n 20

# 指定网络接口
wavesense monitor -i 10 --interface wlan0
```

#### `wavesense dashboard` —— TUI 实时仪表盘

```bash
# 启动完整仪表盘（支持键盘交互）
wavesense dashboard

# 自定义刷新间隔
wavesense dashboard -i 3

# 简易模式（不依赖 select，最大兼容性）
wavesense dashboard --simple
```

**键盘快捷键：**

| 按键 | 功能 |
|------|------|
| `q` / `ESC` | 退出仪表盘 |
| `r` | 手动刷新 |
| `s` | 切换排序方式（RSSI / SSID / 信道） |
| `d` | 切换详细模式 |
| `1-5` | 按信号等级过滤 |
| `0` | 清除过滤 |
| `UP/DOWN` | 选择信号 |

#### `wavesense analyze` —— 信号数据分析

```bash
# 扫描并即时分析
wavesense analyze

# 分析历史数据文件
wavesense analyze --file history.json

# 自定义异常检测阈值（Z-Score）
wavesense analyze --threshold 1.5
```

#### `wavesense report` —— 生成报告

```bash
# 生成 Markdown 报告（默认）
wavesense report

# 生成 JSON 报告
wavesense report -f json

# 生成 CSV 报告并指定输出路径
wavesense report -f csv -o report.csv

# 指定输出目录
wavesense report --dir ./output
```

#### `wavesense heatmap` —— 信号热力图

```bash
# 显示信道使用热力图 + 信号分布
wavesense heatmap
```

#### 全局参数

| 参数 | 缩写 | 说明 |
|------|------|------|
| `--verbose` | `-v` | 详细输出模式 |
| `--version` | `-V` | 显示版本号 |
| `--format` | `-f` | 输出格式（json / csv / markdown） |
| `--output` | `-o` | 输出文件路径 |
| `--interface` | `-i` | 指定网络接口 |

---

### 📊 可视化展示

#### 信号强度条形图

```
  SSID                      RSSI  信号强度
  ──────────────────────── ────── ───────────────────────────────
  MyHomeWiFi               -42dBm  ████████████████████████████████
  Office_5G                -55dBm  ██████████████████████████░░░░░░
  CoffeeShop_Free          -62dBm  ████████████████████░░░░░░░░░░░
  Neighbor_Network         -70dBm  ██████████████░░░░░░░░░░░░░░░░
  Hidden_Network           -78dBm  █████████░░░░░░░░░░░░░░░░░░░░░
  IoT_Sensor               -85dBm  ██████░░░░░░░░░░░░░░░░░░░░░░░
```

#### 信道使用热力图

```
  2.4GHz 信道使用热力图

       1   2   3   4   5   6   7   8   9  10  11  12  13  14
       ▇   ▁   ▂   ▁   ▃   █   ▄   ▁   ▂   ▁   ▇   ▁   ▁   ▁
       5   1   2   1   3   8   4   1   2   1   5   1   0   0

  图例: ▁ 弱  ▄ 中  █ 强
```

#### 信号强度分布直方图

```
  信号强度分布

  极强/Excellent     ████████████████████████████████████   8
  强/Strong         ██████████████████████░░░░░░░░░░░░░   5
  中/Good           ██████████████░░░░░░░░░░░░░░░░░░░░░░   3
  弱/Weak           ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   2
  极弱/V.Weak       ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   1
  ────────────────────────────────────────────────────────
  总计/Total         ████████████████████████████████████  19
```

#### 信号趋势折线图

```
  信号趋势: MyHomeWiFi
  数据点: 20 | 范围: -45 ~ -38 dBm

   -38  │                                    ●
        │                              ╱╱╱╱╱╱╱╱╱╱╱
   -40  │                        ●╱╱╱╱╱╱
        │                  ╱╱╱╱╱╱
   -42  │            ●╱╱╱╱╱
        │      ╱╱╱╱╱╱
   -44  │ ●╱╱╱╱╱
        │╱╱
   -46  └──────────────────────────────────────────────
        14:30:00                          14:35:00
```

---

### 💡 设计思路与迭代规划

#### 技术选型

| 决策 | 原因 |
|------|------|
| **纯标准库** | 零依赖 = 零安装痛苦，离线可用，Docker 镜像极小 |
| **argparse** | Python 内置，无需引入 click/typer 等框架 |
| **非 curses TUI** | 避免 curses 兼容性问题，用简单刷新机制实现最大兼容 |
| **Unicode 方块字符** | ▁▂▃▄▅▆▇█ 比 ASCII art 更美观，现代终端均支持 |
| **Z-Score + 线性回归** | 经典统计算法，无需 numpy/scipy，标准库 math 足矣 |

#### 架构设计

```
wavesense_cli/
├── cli.py          # CLI 命令解析与分发
├── scanner.py      # 跨平台 WiFi 扫描引擎
├── analyzer.py     # 信号数据分析（统计/异常/趋势/距离）
├── visualizer.py   # ASCII 可视化渲染引擎
├── dashboard.py    # TUI 实时仪表盘
├── exporter.py     # 多格式报告导出
├── models.py       # 数据模型定义
├── config.py       # 配置与平台检测
└── utils.py        # 工具函数集
```

#### 后续迭代计划

- [ ] **蓝牙信号扫描** —— 扩展支持 BLE/Classic Bluetooth 信号检测
- [ ] **信号指纹定位** —— 基于 RSSI 指纹的室内定位算法
- [ ] **历史数据回放** —— 加载历史扫描数据进行回放分析
- [ ] **Web 仪表盘** —— 内置 HTTP 服务器，浏览器查看可视化
- [ ] **插件系统** —— 支持自定义分析算法和可视化插件
- [ ] **配置文件** —— `~/.wavesense.conf` 持久化用户偏好
- [ ] **信号地图** —— 结合 GPS 坐标生成信号覆盖热力地图

---

### 📦 安装与部署

#### pip 安装

```bash
pip install wavesense-cli
```

#### pipx 安装（推荐用于隔离环境）

```bash
pipx install wavesense-cli
```

#### 从源码安装

```bash
git clone https://github.com/wavesense-cli/wavesense-cli.git
cd wavesense-cli
pip install .

# 开发模式安装（可编辑）
pip install -e ".[dev]"
```

#### Docker 使用（可选）

```bash
# 构建镜像
docker build -t wavesense-cli .

# 运行扫描（需要 NET_ADMIN 权限）
docker run --rm --net=host --cap-add=NET_ADMIN wavesense-cli scan

# 运行仪表盘
docker run --rm -it --net=host --cap-add=NET_ADMIN wavesense-cli dashboard
```

---

### 🤝 贡献指南

我们欢迎任何形式的贡献！无论是修 Bug、加功能、改文档还是提建议。

#### PR 提交规范

1. **Fork** 本仓库，创建特性分支：`git checkout -b feature/amazing-feature`
2. **提交** 你的改动：`git commit -m 'feat: add amazing feature'`
3. **推送** 到远程分支：`git push origin feature/amazing-feature`
4. **发起** Pull Request

提交信息请遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

- `feat:` 新功能
- `fix:` 修复 Bug
- `docs:` 文档更新
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建/工具链

#### Issue 反馈规则

- 使用清晰的标题描述问题
- 附上运行环境（OS / Python 版本 / 终端类型）
- 贴出完整的错误信息和复现步骤
- 如有截图，请一并提供

#### 开发环境搭建

```bash
# 克隆仓库
git clone https://github.com/wavesense-cli/wavesense-cli.git
cd wavesense-cli

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 运行测试（含覆盖率）
pytest --cov=wavesense_cli

# 类型检查
mypy wavesense_cli
```

---

### 📄 开源协议

本项目基于 [MIT License](./LICENSE) 开源。

```
MIT License

Copyright (c) 2024 WaveSense-CLI Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

简而言之：你可以自由使用、修改、分发本项目，只需保留版权声明即可。

---

## 繁體中文

### 🎉 專案介紹

> 在擁擠的城市中，你身邊至少有十幾個 WiFi 訊號在空氣中交織。它們從哪裡來？有多強？哪個通道最乾淨？——**WaveSense-CLI** 用一行指令告訴你答案。

**WaveSense-CLI** 是一個零外部依賴的 Python CLI 工具，專為無線訊號掃描、智慧分析與終端視覺化而生。靈感來源於 GitHub 熱門專案 [RuView](https://github.com/nicehash/RuView) 中 WiFi 訊號空間智慧的概念，我們在此基礎上做了大量差異化創新：

- **零依賴哲學** —— 僅使用 Python 標準函式庫，`pip install` 即用，無需煩惱環境配置
- **真正的跨平台** —— Linux（nmcli/iwlist）、macOS（airport）、Windows（netsh）三端通吃
- **ASCII 視覺化引擎** —— 熱力圖、條形圖、折線圖、分佈直方圖，全部在終端渲染
- **TUI 即時儀表板** —— 鍵盤互動、自動刷新、異常告警，像用 htop 一樣監控 WiFi
- **智慧分析演算法** —— Z-Score 異常偵測、線性迴歸趨勢、FSPL 距離估算，讓資料說話

無論你是網路工程師排查訊號干擾、開發者除錯 IoT 裝置，還是極客想了解身邊的無線環境，WaveSense-CLI 都是你的瑞士軍刀。

---

### ✨ 核心特性

| 特性 | 描述 |
|------|------|
| 📡 **跨平台掃描** | Linux / macOS / Windows 三端原生支援，自動偵測平台並呼叫最佳掃描指令 |
| 🧮 **智慧分析** | Z-Score 異常偵測、線性迴歸趨勢分析、FSPL 自由空間路徑損耗距離估算 |
| 🎨 **ASCII 視覺化** | 訊號熱力圖、強度條形圖、趨勢折線圖、分佈直方圖 —— 全部 Unicode + ANSI 彩色渲染 |
| 🖥️ **TUI 儀表板** | 即時刷新的終端儀表板，支援鍵盤互動（排序/篩選/詳情）、異常告警 |
| 📈 **持續監控** | 定時掃描 + 歷史記錄，追蹤訊號變化趨勢，捕捉異常波動 |
| 📤 **多格式匯出** | 一鍵匯出 JSON / CSV / Markdown 格式報告，方便後續處理與分享 |
| 🪶 **零外部依賴** | 純 Python 標準函式庫實作，Python >= 3.7 即可執行，離線環境也毫無壓力 |
| ⚡ **極速啟動** | 毫秒級初始化，快取機制避免重複掃描，`--simple` 模式相容受限終端 |
| 🔍 **通道分析** | 自動分析 2.4GHz / 5GHz 通道擁擠度，推薦最佳通道 |
| 🛡️ **穩健容錯** | 多掃描器自動降級、逾時重試、權限偵測，優雅處理各種異常場景 |

---

### 🚀 快速開始

#### 環境需求

- **Python** >= 3.7（支援 3.7 ~ 3.12）
- **作業系統**：Linux / macOS / Windows
- **掃描權限**：部分平台需要管理員/root 權限執行 WiFi 掃描

#### 安裝

```bash
# 方式一：pip 安裝（推薦）
pip install wavesense-cli

# 方式二：pipx 安裝（隔離環境）
pipx install wavesense-cli

# 方式三：從原始碼安裝
git clone https://github.com/wavesense-cli/wavesense-cli.git
cd wavesense-cli
pip install .
```

#### 快速體驗

```bash
# 掃描一次周圍 WiFi 訊號
wavesense scan

# 查看版本資訊
wavesense -V

# 持續監控（每 5 秒刷新）
wavesense monitor -i 5

# 啟動 TUI 即時儀表板
wavesense dashboard

# 產生 Markdown 報告
wavesense report -f markdown -o report.md

# 查看訊號熱力圖
wavesense heatmap
```

---

### 📖 詳細使用指南

#### `wavesense scan` —— WiFi 訊號掃描

```bash
# 基礎掃描
wavesense scan

# 指定網路介面
wavesense scan -i wlan0

# 詳細模式（顯示統計資訊）
wavesense scan -v

# JSON 格式輸出
wavesense scan --json

# 匯出為 CSV 檔案
wavesense scan -f csv -o signals.csv

# 匯出到指定路徑
wavesense scan -f json -o /tmp/scan_result.json
```

#### `wavesense monitor` —— 持續監控模式

```bash
# 每 5 秒掃描一次（預設）
wavesense monitor

# 自訂掃描間隔（每 3 秒）
wavesense monitor -i 3

# 限制掃描次數（掃描 20 次後停止）
wavesense monitor -i 5 -n 20

# 指定網路介面
wavesense monitor -i 10 --interface wlan0
```

#### `wavesense dashboard` —— TUI 即時儀表板

```bash
# 啟動完整儀表板（支援鍵盤互動）
wavesense dashboard

# 自訂刷新間隔
wavesense dashboard -i 3

# 簡易模式（不依賴 select，最大相容性）
wavesense dashboard --simple
```

**鍵盤快捷鍵：**

| 按鍵 | 功能 |
|------|------|
| `q` / `ESC` | 離開儀表板 |
| `r` | 手動刷新 |
| `s` | 切換排序方式（RSSI / SSID / 通道） |
| `d` | 切換詳細模式 |
| `1-5` | 依訊號等級篩選 |
| `0` | 清除篩選 |
| `UP/DOWN` | 選擇訊號 |

#### `wavesense analyze` —— 訊號資料分析

```bash
# 掃描並即時分析
wavesense analyze

# 分析歷史資料檔案
wavesense analyze --file history.json

# 自訂異常偵測閾值（Z-Score）
wavesense analyze --threshold 1.5
```

#### `wavesense report` —— 產生報告

```bash
# 產生 Markdown 報告（預設）
wavesense report

# 產生 JSON 報告
wavesense report -f json

# 產生 CSV 報告並指定輸出路徑
wavesense report -f csv -o report.csv

# 指定輸出目錄
wavesense report --dir ./output
```

#### `wavesense heatmap` —— 訊號熱力圖

```bash
# 顯示通道使用熱力圖 + 訊號分佈
wavesense heatmap
```

#### 全域參數

| 參數 | 縮寫 | 說明 |
|------|------|------|
| `--verbose` | `-v` | 詳細輸出模式 |
| `--version` | `-V` | 顯示版本號 |
| `--format` | `-f` | 輸出格式（json / csv / markdown） |
| `--output` | `-o` | 輸出檔案路徑 |
| `--interface` | `-i` | 指定網路介面 |

---

### 📊 視覺化展示

#### 訊號強度條形圖

```
  SSID                      RSSI  訊號強度
  ──────────────────────── ────── ───────────────────────────────
  MyHomeWiFi               -42dBm  ████████████████████████████████
  Office_5G                -55dBm  ██████████████████████████░░░░░░
  CoffeeShop_Free          -62dBm  ████████████████████░░░░░░░░░░░
  Neighbor_Network         -70dBm  ██████████████░░░░░░░░░░░░░░░░
  Hidden_Network           -78dBm  █████████░░░░░░░░░░░░░░░░░░░░░
  IoT_Sensor               -85dBm  ██████░░░░░░░░░░░░░░░░░░░░░░░
```

#### 通道使用熱力圖

```
  2.4GHz 通道使用熱力圖

       1   2   3   4   5   6   7   8   9  10  11  12  13  14
       ▇   ▁   ▂   ▁   ▃   █   ▄   ▁   ▂   ▁   ▇   ▁   ▁   ▁
       5   1   2   1   3   8   4   1   2   1   5   1   0   0

  圖例: ▁ 弱  ▄ 中  █ 強
```

#### 訊號強度分佈直方圖

```
  訊號強度分佈

  極強/Excellent     ████████████████████████████████████   8
  強/Strong         ██████████████████████░░░░░░░░░░░░░   5
  中/Good           ██████████████░░░░░░░░░░░░░░░░░░░░░░   3
  弱/Weak           ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   2
  極弱/V.Weak       ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   1
  ────────────────────────────────────────────────────────
  總計/Total         ████████████████████████████████████  19
```

#### 訊號趨勢折線圖

```
  訊號趨勢: MyHomeWiFi
  資料點: 20 | 範圍: -45 ~ -38 dBm

   -38  │                                    ●
        │                              ╱╱╱╱╱╱╱╱╱╱╱
   -40  │                        ●╱╱╱╱╱╱
        │                  ╱╱╱╱╱╱
   -42  │            ●╱╱╱╱╱
        │      ╱╱╱╱╱╱
   -44  │ ●╱╱╱╱╱
        │╱╱
   -46  └──────────────────────────────────────────────
        14:30:00                          14:35:00
```

---

### 💡 設計思路與迭代規劃

#### 技術選型

| 決策 | 原因 |
|------|------|
| **純標準函式庫** | 零依賴 = 零安裝痛苦，離線可用，Docker 映像檔極小 |
| **argparse** | Python 內建，無需引入 click/typer 等框架 |
| **非 curses TUI** | 避免 curses 相容性問題，用簡單刷新機制實現最大相容 |
| **Unicode 方塊字元** | ▁▂▃▄▅▆▇█ 比 ASCII art 更美觀，現代終端均支援 |
| **Z-Score + 線性迴歸** | 經典統計演算法，無需 numpy/scipy，標準函式庫 math 足矣 |

#### 架構設計

```
wavesense_cli/
├── cli.py          # CLI 指令解析與分發
├── scanner.py      # 跨平台 WiFi 掃描引擎
├── analyzer.py     # 訊號資料分析（統計/異常/趨勢/距離）
├── visualizer.py   # ASCII 視覺化渲染引擎
├── dashboard.py    # TUI 即時儀表板
├── exporter.py     # 多格式報告匯出
├── models.py       # 資料模型定義
├── config.py       # 組態與平台偵測
└── utils.py        # 工具函式集
```

#### 後續迭代計畫

- [ ] **藍牙訊號掃描** —— 擴充支援 BLE/Classic Bluetooth 訊號偵測
- [ ] **訊號指紋定位** —— 基於 RSSI 指紋的室內定位演算法
- [ ] **歷史資料回放** —— 載入歷史掃描資料進行回放分析
- [ ] **Web 儀表板** —— 內建 HTTP 伺服器，瀏覽器查看視覺化
- [ ] **外掛系統** —— 支援自訂分析演算法和視覺化外掛
- [ ] **組態檔** —— `~/.wavesense.conf` 持久化使用者偏好
- [ ] **訊號地圖** —— 結合 GPS 座標產生訊號覆蓋熱力地圖

---

### 📦 安裝與部署

#### pip 安裝

```bash
pip install wavesense-cli
```

#### pipx 安裝（推薦用於隔離環境）

```bash
pipx install wavesense-cli
```

#### 從原始碼安裝

```bash
git clone https://github.com/wavesense-cli/wavesense-cli.git
cd wavesense-cli
pip install .

# 開發模式安裝（可編輯）
pip install -e ".[dev]"
```

#### Docker 使用（可選）

```bash
# 建置映像檔
docker build -t wavesense-cli .

# 執行掃描（需要 NET_ADMIN 權限）
docker run --rm --net=host --cap-add=NET_ADMIN wavesense-cli scan

# 執行儀表板
docker run --rm -it --net=host --cap-add=NET_ADMIN wavesense-cli dashboard
```

---

### 🤝 貢獻指南

我們歡迎任何形式的貢獻！無論是修 Bug、加功能、改文件還是提建議。

#### PR 提交規範

1. **Fork** 本儲存庫，建立特性分支：`git checkout -b feature/amazing-feature`
2. **提交** 你的變更：`git commit -m 'feat: add amazing feature'`
3. **推送** 到遠端分支：`git push origin feature/amazing-feature`
4. **發起** Pull Request

提交資訊請遵循 [Conventional Commits](https://www.conventionalcommits.org/) 規範：

- `feat:` 新功能
- `fix:` 修復 Bug
- `docs:` 文件更新
- `refactor:` 程式碼重構
- `test:` 測試相關
- `chore:` 建置/工具鏈

#### Issue 回饋規則

- 使用清晰的標題描述問題
- 附上執行環境（OS / Python 版本 / 終端類型）
- 貼上完整的錯誤資訊和重現步驟
- 如有截圖，請一併提供

#### 開發環境建置

```bash
# 複製儲存庫
git clone https://github.com/wavesense-cli/wavesense-cli.git
cd wavesense-cli

# 安裝開發依賴
pip install -e ".[dev]"

# 執行測試
pytest

# 執行測試（含覆蓋率）
pytest --cov=wavesense_cli

# 型別檢查
mypy wavesense_cli
```

---

### 📄 開源授權

本專案基於 [MIT License](./LICENSE) 開源。

```
MIT License

Copyright (c) 2024 WaveSense-CLI Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

簡而言之：你可以自由使用、修改、散佈本專案，只需保留著作權聲明即可。

---

## English

### 🎉 About

> In a crowded city, at least a dozen WiFi signals weave through the air around you. Where do they come from? How strong are they? Which channel is cleanest? -- **WaveSense-CLI** answers all of that with a single command.

**WaveSense-CLI** is a zero-dependency Python CLI tool purpose-built for wireless signal scanning, intelligent analysis, and terminal visualization. Inspired by the WiFi signal spatial intelligence concept from the popular GitHub project [RuView](https://github.com/nicehash/RuView), we've taken that idea and built something uniquely different:

- **Zero-dependency philosophy** -- Built entirely on the Python standard library. `pip install` and go. No environment headaches.
- **True cross-platform** -- Linux (nmcli/iwlist), macOS (airport), and Windows (netsh) -- all first-class citizens.
- **ASCII visualization engine** -- Heatmaps, bar charts, line charts, distribution histograms -- all rendered beautifully in your terminal.
- **TUI real-time dashboard** -- Keyboard-driven, auto-refreshing, anomaly-alerting. Monitor WiFi like you use `htop`.
- **Intelligent analysis** -- Z-Score anomaly detection, linear regression trend analysis, FSPL distance estimation. Let the data speak.

Whether you're a network engineer troubleshooting interference, a developer debugging IoT devices, or a tech enthusiast curious about the wireless landscape around you, WaveSense-CLI is your Swiss Army knife.

---

### ✨ Core Features

| Feature | Description |
|---------|-------------|
| 📡 **Cross-platform Scanning** | Native support for Linux / macOS / Windows with automatic platform detection and optimal scanner selection |
| 🧮 **Intelligent Analysis** | Z-Score anomaly detection, linear regression trend analysis, FSPL free-space path loss distance estimation |
| 🎨 **ASCII Visualization** | Signal heatmaps, strength bar charts, trend line charts, distribution histograms -- all with Unicode + ANSI color rendering |
| 🖥️ **TUI Dashboard** | Real-time terminal dashboard with keyboard interaction (sort/filter/detail), anomaly alerts |
| 📈 **Continuous Monitoring** | Timed scans with history tracking, trend analysis, and anomaly capture |
| 📤 **Multi-format Export** | One-click export to JSON / CSV / Markdown reports for further processing and sharing |
| 🪶 **Zero Dependencies** | Pure Python standard library. Runs on Python >= 3.7. Works offline without any issues |
| ⚡ **Instant Startup** | Millisecond initialization, caching to avoid redundant scans, `--simple` mode for restricted terminals |
| 🔍 **Channel Analysis** | Automatic 2.4GHz / 5GHz channel congestion analysis with optimal channel recommendations |
| 🛡️ **Robust Error Handling** | Multi-scanner auto-fallback, timeout retries, permission detection, graceful handling of edge cases |

---

### 🚀 Quick Start

#### Requirements

- **Python** >= 3.7 (supports 3.7 through 3.12)
- **OS**: Linux / macOS / Windows
- **Permissions**: Some platforms require admin/root privileges for WiFi scanning

#### Installation

```bash
# Option 1: pip install (recommended)
pip install wavesense-cli

# Option 2: pipx install (isolated environment)
pipx install wavesense-cli

# Option 3: Install from source
git clone https://github.com/wavesense-cli/wavesense-cli.git
cd wavesense-cli
pip install .
```

#### Quick Demo

```bash
# Scan surrounding WiFi signals
wavesense scan

# Check version
wavesense -V

# Continuous monitoring (refresh every 5 seconds)
wavesense monitor -i 5

# Launch the TUI real-time dashboard
wavesense dashboard

# Generate a Markdown report
wavesense report -f markdown -o report.md

# View signal heatmap
wavesense heatmap
```

---

### 📖 Detailed Usage Guide

#### `wavesense scan` -- WiFi Signal Scan

```bash
# Basic scan
wavesense scan

# Specify network interface
wavesense scan -i wlan0

# Verbose mode (show statistics)
wavesense scan -v

# JSON output
wavesense scan --json

# Export to CSV
wavesense scan -f csv -o signals.csv

# Export to a specific path
wavesense scan -f json -o /tmp/scan_result.json
```

#### `wavesense monitor` -- Continuous Monitoring

```bash
# Scan every 5 seconds (default)
wavesense monitor

# Custom interval (every 3 seconds)
wavesense monitor -i 3

# Limit scan count (stop after 20 scans)
wavesense monitor -i 5 -n 20

# Specify network interface
wavesense monitor -i 10 --interface wlan0
```

#### `wavesense dashboard` -- TUI Real-time Dashboard

```bash
# Launch full dashboard (with keyboard interaction)
wavesense dashboard

# Custom refresh interval
wavesense dashboard -i 3

# Simple mode (no select dependency, maximum compatibility)
wavesense dashboard --simple
```

**Keyboard Shortcuts:**

| Key | Action |
|-----|--------|
| `q` / `ESC` | Quit dashboard |
| `r` | Manual refresh |
| `s` | Toggle sort method (RSSI / SSID / Channel) |
| `d` | Toggle detail mode |
| `1-5` | Filter by signal level |
| `0` | Clear filter |
| `UP/DOWN` | Select signal |

#### `wavesense analyze` -- Signal Data Analysis

```bash
# Scan and analyze immediately
wavesense analyze

# Analyze a history data file
wavesense analyze --file history.json

# Custom anomaly detection threshold (Z-Score)
wavesense analyze --threshold 1.5
```

#### `wavesense report` -- Generate Report

```bash
# Generate Markdown report (default)
wavesense report

# Generate JSON report
wavesense report -f json

# Generate CSV report with specific output path
wavesense report -f csv -o report.csv

# Specify output directory
wavesense report --dir ./output
```

#### `wavesense heatmap` -- Signal Heatmap

```bash
# Display channel usage heatmap + signal distribution
wavesense heatmap
```

#### Global Options

| Option | Short | Description |
|--------|-------|-------------|
| `--verbose` | `-v` | Verbose output mode |
| `--version` | `-V` | Show version number |
| `--format` | `-f` | Output format (json / csv / markdown) |
| `--output` | `-o` | Output file path |
| `--interface` | `-i` | Specify network interface |

---

### 📊 Visualization Showcase

#### Signal Strength Bar Chart

```
  SSID                      RSSI  Signal Strength
  ──────────────────────── ────── ───────────────────────────────
  MyHomeWiFi               -42dBm  ████████████████████████████████
  Office_5G                -55dBm  ██████████████████████████░░░░░░
  CoffeeShop_Free          -62dBm  ████████████████████░░░░░░░░░░░
  Neighbor_Network         -70dBm  ██████████████░░░░░░░░░░░░░░░░
  Hidden_Network           -78dBm  █████████░░░░░░░░░░░░░░░░░░░░░
  IoT_Sensor               -85dBm  ██████░░░░░░░░░░░░░░░░░░░░░░░
```

#### Channel Usage Heatmap

```
  2.4GHz Channel Usage Heatmap

       1   2   3   4   5   6   7   8   9  10  11  12  13  14
       ▇   ▁   ▂   ▁   ▃   █   ▄   ▁   ▂   ▁   ▇   ▁   ▁   ▁
       5   1   2   1   3   8   4   1   2   1   5   1   0   0

  Legend: ▁ Weak  ▄ Medium  █ Strong
```

#### Signal Strength Distribution

```
  Signal Strength Distribution

  Excellent         ████████████████████████████████████   8
  Strong            ██████████████████████░░░░░░░░░░░░░   5
  Good              ██████████████░░░░░░░░░░░░░░░░░░░░░░   3
  Weak              ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   2
  Very Weak         ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   1
  ────────────────────────────────────────────────────────
  Total             ████████████████████████████████████  19
```

#### Signal Trend Line Chart

```
  Signal Trend: MyHomeWiFi
  Data points: 20 | Range: -45 ~ -38 dBm

   -38  │                                    ●
        │                              ╱╱╱╱╱╱╱╱╱╱╱
   -40  │                        ●╱╱╱╱╱╱
        │                  ╱╱╱╱╱╱
   -42  │            ●╱╱╱╱╱
        │      ╱╱╱╱╱╱
   -44  │ ●╱╱╱╱╱
        │╱╱
   -46  └──────────────────────────────────────────────
        14:30:00                          14:35:00
```

---

### 💡 Design Philosophy & Roadmap

#### Technical Choices

| Decision | Rationale |
|----------|-----------|
| **Pure standard library** | Zero deps = zero install pain. Works offline. Minimal Docker image. |
| **argparse** | Built into Python. No need for click/typer or other frameworks. |
| **Non-curses TUI** | Avoids curses compatibility issues. Simple refresh mechanism for maximum portability. |
| **Unicode block chars** | ▁▂▃▄▅▆▇█ looks better than ASCII art. All modern terminals support it. |
| **Z-Score + Linear Regression** | Classic statistical algorithms. No numpy/scipy needed. `math` module is sufficient. |

#### Architecture

```
wavesense_cli/
├── cli.py          # CLI command parsing and dispatch
├── scanner.py      # Cross-platform WiFi scanning engine
├── analyzer.py     # Signal data analysis (stats/anomaly/trend/distance)
├── visualizer.py   # ASCII visualization rendering engine
├── dashboard.py    # TUI real-time dashboard
├── exporter.py     # Multi-format report export
├── models.py       # Data model definitions
├── config.py       # Configuration and platform detection
└── utils.py        # Utility functions
```

#### Roadmap

- [ ] **Bluetooth Scanning** -- Add BLE/Classic Bluetooth signal detection support
- [ ] **Signal Fingerprinting** -- RSSI fingerprint-based indoor positioning algorithm
- [ ] **History Playback** -- Load and replay historical scan data for analysis
- [ ] **Web Dashboard** -- Built-in HTTP server for browser-based visualization
- [ ] **Plugin System** -- Support custom analysis algorithms and visualization plugins
- [ ] **Config File** -- `~/.wavesense.conf` for persistent user preferences
- [ ] **Signal Mapping** -- Generate signal coverage heatmaps with GPS coordinates

---

### 📦 Installation & Deployment

#### pip Install

```bash
pip install wavesense-cli
```

#### pipx Install (Recommended for Isolated Environments)

```bash
pipx install wavesense-cli
```

#### Install from Source

```bash
git clone https://github.com/wavesense-cli/wavesense-cli.git
cd wavesense-cli
pip install .

# Development mode (editable)
pip install -e ".[dev]"
```

#### Docker Usage (Optional)

```bash
# Build image
docker build -t wavesense-cli .

# Run scan (requires NET_ADMIN capability)
docker run --rm --net=host --cap-add=NET_ADMIN wavesense-cli scan

# Run dashboard
docker run --rm -it --net=host --cap-add=NET_ADMIN wavesense-cli dashboard
```

---

### 🤝 Contributing

We welcome contributions of all kinds! Whether it's fixing bugs, adding features, improving documentation, or suggesting ideas.

#### PR Submission Guidelines

1. **Fork** this repo and create a feature branch: `git checkout -b feature/amazing-feature`
2. **Commit** your changes: `git commit -m 'feat: add amazing feature'`
3. **Push** to the remote branch: `git push origin feature/amazing-feature`
4. **Open** a Pull Request

Please follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation update
- `refactor:` Code refactoring
- `test:` Test-related changes
- `chore:` Build/tooling

#### Issue Reporting Guidelines

- Use a clear, descriptive title
- Include your environment (OS / Python version / terminal type)
- Paste the full error message and reproduction steps
- Include screenshots if applicable

#### Development Setup

```bash
# Clone the repository
git clone https://github.com/wavesense-cli/wavesense-cli.git
cd wavesense-cli

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=wavesense_cli

# Type checking
mypy wavesense_cli
```

---

### 📄 License

This project is licensed under the [MIT License](./LICENSE).

```
MIT License

Copyright (c) 2024 WaveSense-CLI Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

In short: you are free to use, modify, and distribute this project, as long as you preserve the copyright notice.

---

<div align="center">

### ⭐ Star History

```
    ★
   ★ ★
  ★   ★
 ★     ★
★       ★
 ★     ★
  ★   ★
   ★ ★
    ★
   ★ ★
  ★   ★
 ★     ★
★       ★ ★
 ★     ★   ★
  ★   ★     ★
   ★ ★       ★
    ★ ★     ★
   ★ ★ ★   ★
  ★ ★ ★ ★ ★
 ★ ★ ★ ★ ★ ★
★ ★ ★ ★ ★ ★ ★
 ★ ★ ★ ★ ★ ★
  ★ ★ ★ ★ ★
   ★ ★ ★ ★
    ★ ★ ★
     ★ ★
      ★
  WaveSense-CLI
```

**If you find this project useful, please consider giving it a star! It means a lot to us.**

---

<img src="https://img.shields.io/badge/Python-%3E%3D3.7-blue?logo=python&logoColor=white" alt="Python Version">
<img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
<img src="https://img.shields.io/badge/Zero_Dependencies-✓-success" alt="Zero Dependencies">
<img src="https://img.shields.io/badge/Cross_Platform-Linux%20%7C%20macOS%20%7C%20Windows-informational" alt="Cross Platform">
<img src="https://img.shields.io/badge/CLI-TUI%20%20Dashboard-orange" alt="TUI Dashboard">
<img src="https://img.shields.io/badge/Version-v1.0.0-brightgreen" alt="Version">

</div>
