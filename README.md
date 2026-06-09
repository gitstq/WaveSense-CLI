<div align="center">

# 📡 WaveSense-CLI

**Lightweight Wi-Fi CSI Motion Detection Engine**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero-orange)]()
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey)]()

[English](#english) | [简体中文](#simplified-chinese) | [繁體中文](#traditional-chinese)

</div>

---

<a name="english"></a>
## English

### Introduction

**WaveSense-CLI** is a lightweight, zero-dependency Wi-Fi Channel State Information (CSI) based motion detection engine. It transforms your existing Wi-Fi infrastructure into a powerful presence and motion sensing system — no additional hardware required!

**Core Value:**
- Leverages Wi-Fi CSI (physical layer signal information) for detection
- Perfect for smart home presence sensing, intrusion detection, and elderly care
- Pure Python implementation with zero external dependencies
- Real-time TUI dashboard with ASCII visualization
- Native Home Assistant MQTT integration

**Inspiration & Differentiation:**
Inspired by the espectre project, WaveSense-CLI differentiates itself through:
- **Zero hardware dependencies** — works with simulated data for testing
- **Multiple data sources** — supports simulation, pcap files, and Linux nl80211
- **Multi-algorithm fusion** — combines amplitude, phase, and correlation detection
- **Cross-platform compatibility** — runs on Linux, macOS, and Windows

---

### Core Features

| Feature | Description |
|---------|-------------|
| **Multi-Source CSI** | Simulated data, pcap files, Linux nl80211 interface |
| **Triple Detection** | Amplitude difference + Phase variation + Subcarrier correlation |
| **Smart Fusion** | Weighted voting, majority vote, sequential confirmation |
| **TUI Dashboard** | Real-time ASCII amplitude spectrum and motion status |
| **CSV Export** | Historical data export for analysis |
| **Home Assistant** | Native MQTT discovery and state publishing |
| **Adaptive Threshold** | Auto-adjusting sensitivity for different environments |
| **Simulation Mode** | Test with random, periodic, or burst motion patterns |

---

### Quick Start

#### Requirements
- Python 3.8 or higher
- Linux with monitor mode capable Wi-Fi card (for live CSI)
- Or just use simulation mode for testing!

#### Installation

```bash
# Clone the repository
git clone https://github.com/gitstq/WaveSense-CLI.git
cd WaveSense-CLI

# Run directly (no dependencies to install!)
python main.py --source simulated --pattern periodic

# Or install as a package
pip install -e .
wavesense --source simulated
```

#### Basic Usage

```bash
# Simulated data with periodic motion pattern
python main.py --source simulated --pattern periodic

# Read from pcap file
python main.py --source pcap --file capture.pcap

# Live CSI from Linux interface (requires root)
sudo python main.py --source linux --interface wlan0 --channel 36

# Export to CSV + MQTT to Home Assistant
python main.py --source simulated --csv output.csv --mqtt --broker 192.168.1.100

# Disable dashboard, quiet mode
python main.py --source simulated --no-dashboard --quiet --csv data.csv
```

---

### Detailed Usage Guide

#### Command-Line Options

```
Data Source Options:
  --source {simulated,pcap,linux}  CSI data source (default: simulated)
  --file, -f PATH                  pcap file path
  --interface, -i NAME             Wireless interface (default: wlan0)
  --channel, -c NUMBER             Wi-Fi channel (default: 36)
  --pattern {random,periodic,burst} Simulated motion pattern
  --subcarriers NUMBER             Number of subcarriers (default: 64)

Detection Options:
  --threshold FLOAT                Detection threshold (default: 0.15)
  --fusion {majority_vote,weighted_average,sequential}
                                   Fusion method (default: weighted_average)

Output Options:
  --csv PATH                       Export to CSV file
  --mqtt                           Enable MQTT output
  --broker ADDRESS                 MQTT broker (default: localhost)
  --port NUMBER                    MQTT port (default: 1883)

UI Options:
  --no-dashboard                   Disable TUI dashboard
  --quiet, -q                      Quiet mode
```

#### Typical Scenarios

**Research & Development**
```bash
# Test detection algorithms with different motion patterns
python main.py --source simulated --pattern burst --subcarriers 128 --threshold 0.2
```

**Smart Home Integration**
```bash
# Continuous monitoring with Home Assistant
python main.py --source linux --interface wlan0 --mqtt --broker homeassistant.local
```

**Data Collection**
```bash
# Record CSI data for offline analysis
python main.py --source simulated --csv experiment_$(date +%Y%m%d).csv --no-dashboard
```

---

### Design Philosophy & Roadmap

**Design Principles:**
- **Zero dependencies** — runs anywhere Python is available
- **Modular architecture** — easy to extend with new detectors or data sources
- **Adaptive intelligence** — thresholds auto-adjust to environment
- **Developer friendly** — clean APIs for integration

**Technology Choices:**
- Pure Python standard library for maximum portability
- Abstract base classes for extensible reader/detector design
- Dataclasses for clean data structures
- ANSI escape codes for terminal UI (no curses dependency)

**Future Roadmap:**
- [ ] Support for more CSI chipsets (Atheros, Broadcom, Qualcomm)
- [ ] Machine learning-based detection enhancement
- [ ] Fall detection algorithm
- [ ] Multi-room localization
- [ ] Web-based remote dashboard
- [ ] REST API server mode

---

### Deployment Guide

**As a Python Package:**
```bash
pip install -e .
wavesense --help
```

**As a Standalone Script:**
```bash
python main.py [options]
```

**Systemd Service (Linux):**
```ini
# /etc/systemd/system/wavesense.service
[Unit]
Description=WaveSense CSI Motion Detection
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/wavesense/main.py --source linux --mqtt
Restart=always
User=root

[Install]
WantedBy=multi-user.target
```

**Docker (Future):**
```dockerfile
FROM python:3.11-slim
COPY . /app
WORKDIR /app
ENTRYPOINT ["python", "main.py"]
```

---

### Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork** the repository
2. Create a **feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'feat: add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. Open a **Pull Request**

**Commit Convention:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation update
- `refactor:` Code refactoring
- `test:` Test additions/changes

---

### License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<a name="simplified-chinese"></a>
## 简体中文

### 项目介绍

**WaveSense-CLI** 是一款轻量级、零依赖的 Wi-Fi 信道状态信息（CSI）运动检测引擎。它能将您现有的 Wi-Fi 基础设施转化为强大的存在感知与运动检测系统 —— 无需任何额外硬件！

**核心价值：**
- 利用 Wi-Fi CSI（物理层信号信息）进行检测
- 完美适用于智能家居存在感知、入侵检测、老人看护
- 纯 Python 实现，零外部依赖
- 实时 TUI 终端仪表板，ASCII 可视化
- 原生 Home Assistant MQTT 集成

**灵感来源与差异化：**
受 espectre 项目启发，WaveSense-CLI 的差异化亮点：
- **零硬件依赖** —— 支持模拟数据测试
- **多数据源支持** —— 模拟数据、pcap 文件、Linux nl80211
- **多算法融合** —— 幅度、相位、相关性三重检测
- **跨平台兼容** —— 支持 Linux、macOS、Windows

---

### 核心特性

| 特性 | 说明 |
|------|------|
| **多源CSI** | 模拟数据、pcap 文件、Linux nl80211 接口 |
| **三重检测** | 幅度差分 + 相位变化 + 子载波相关性 |
| **智能融合** | 加权投票、多数表决、序列确认 |
| **TUI仪表板** | 实时 ASCII 幅度频谱与运动状态 |
| **CSV导出** | 历史数据导出供分析 |
| **Home Assistant** | 原生 MQTT 发现与状态上报 |
| **自适应阈值** | 根据环境自动调整灵敏度 |
| **模拟模式** | 随机、周期、突发三种运动模式 |

---

### 快速开始

#### 环境要求
- Python 3.8 或更高版本
- 支持监听模式的 Wi-Fi 网卡（实时 CSI 需要）
- 或者直接使用模拟模式测试！

#### 安装

```bash
# 克隆仓库
git clone https://github.com/gitstq/WaveSense-CLI.git
cd WaveSense-CLI

# 直接运行（无需安装任何依赖！）
python main.py --source simulated --pattern periodic

# 或安装为包
pip install -e .
wavesense --source simulated
```

#### 基础用法

```bash
# 模拟数据 + 周期运动模式
python main.py --source simulated --pattern periodic

# 从 pcap 文件读取
python main.py --source pcap --file capture.pcap

# Linux 接口实时 CSI（需要 root）
sudo python main.py --source linux --interface wlan0 --channel 36

# 导出 CSV + MQTT 上报 Home Assistant
python main.py --source simulated --csv output.csv --mqtt --broker 192.168.1.100

# 关闭仪表板，静默模式
python main.py --source simulated --no-dashboard --quiet --csv data.csv
```

---

### 详细使用指南

#### 命令行选项

```
数据源选项：
  --source {simulated,pcap,linux}  CSI 数据源（默认：simulated）
  --file, -f PATH                  pcap 文件路径
  --interface, -i NAME             无线网卡接口（默认：wlan0）
  --channel, -c NUMBER             Wi-Fi 信道（默认：36）
  --pattern {random,periodic,burst} 模拟运动模式
  --subcarriers NUMBER             子载波数量（默认：64）

检测选项：
  --threshold FLOAT                检测阈值（默认：0.15）
  --fusion {majority_vote,weighted_average,sequential}
                                   融合方法（默认：weighted_average）

输出选项：
  --csv PATH                       导出 CSV 文件
  --mqtt                           启用 MQTT 输出
  --broker ADDRESS                 MQTT 代理（默认：localhost）
  --port NUMBER                    MQTT 端口（默认：1883）

UI 选项：
  --no-dashboard                   禁用 TUI 仪表板
  --quiet, -q                      静默模式
```

#### 典型使用场景

**研究与开发**
```bash
# 使用不同运动模式测试检测算法
python main.py --source simulated --pattern burst --subcarriers 128 --threshold 0.2
```

**智能家居集成**
```bash
# 持续监控并接入 Home Assistant
python main.py --source linux --interface wlan0 --mqtt --broker homeassistant.local
```

**数据采集**
```bash
# 记录 CSI 数据用于离线分析
python main.py --source simulated --csv experiment_$(date +%Y%m%d).csv --no-dashboard
```

---

### 设计思路与迭代规划

**设计原则：**
- **零依赖** —— 只要有 Python 就能运行
- **模块化架构** —— 易于扩展新的检测器或数据源
- **自适应智能** —— 阈值根据环境自动调整
- **开发者友好** —— 干净的 API 便于集成

**技术选型原因：**
- 纯 Python 标准库，最大化可移植性
- 抽象基类设计，支持可扩展的读取器/检测器
- 数据类定义清晰的数据结构
- ANSI 转义码实现终端 UI（无需 curses 依赖）

**后续迭代计划：**
- [ ] 支持更多 CSI 芯片（Atheros、Broadcom、Qualcomm）
- [ ] 基于机器学习的检测增强
- [ ] 跌倒检测算法
- [ ] 多房间定位
- [ ] Web 远程仪表板
- [ ] REST API 服务器模式

---

### 打包与部署指南

**作为 Python 包：**
```bash
pip install -e .
wavesense --help
```

**作为独立脚本：**
```bash
python main.py [选项]
```

**Systemd 服务（Linux）：**
```ini
# /etc/systemd/system/wavesense.service
[Unit]
Description=WaveSense CSI 运动检测
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/wavesense/main.py --source linux --mqtt
Restart=always
User=root

[Install]
WantedBy=multi-user.target
```

**Docker（未来）：**
```dockerfile
FROM python:3.11-slim
COPY . /app
WORKDIR /app
ENTRYPOINT ["python", "main.py"]
```

---

### 贡献指南

欢迎贡献！请遵循以下规范：

1. **Fork** 本仓库
2. 创建**功能分支**（`git checkout -b feature/amazing-feature`）
3. **提交**更改（`git commit -m 'feat: add amazing feature'`）
4. **推送**到分支（`git push origin feature/amazing-feature`）
5. 发起 **Pull Request**

**提交规范：**
- `feat:` 新功能
- `fix:` 修复问题
- `docs:` 文档更新
- `refactor:` 代码重构
- `test:` 测试相关

---

### 开源协议

本项目采用 **MIT 协议** 开源 —— 详见 [LICENSE](LICENSE) 文件。

---

<a name="traditional-chinese"></a>
## 繁體中文

### 專案介紹

**WaveSense-CLI** 是一款輕量級、零依賴的 Wi-Fi 信道狀態資訊（CSI）運動檢測引擎。它能將您現有的 Wi-Fi 基礎設施轉化為強大的存在感知與運動檢測系統 —— 無需任何額外硬體！

**核心價值：**
- 利用 Wi-Fi CSI（物理層信號資訊）進行檢測
- 完美適用於智慧家居存在感知、入侵檢測、老人看護
- 純 Python 實現，零外部依賴
- 即時 TUI 終端儀表板，ASCII 視覺化
- 原生 Home Assistant MQTT 整合

**靈感來源與差異化：**
受 espectre 專案啟發，WaveSense-CLI 的差異化亮點：
- **零硬體依賴** —— 支援模擬資料測試
- **多資料源支援** —— 模擬資料、pcap 檔案、Linux nl80211
- **多演算法融合** —— 幅度、相位、相關性三重檢測
- **跨平臺相容** —— 支援 Linux、macOS、Windows

---

### 核心特性

| 特性 | 說明 |
|------|------|
| **多源CSI** | 模擬資料、pcap 檔案、Linux nl80211 介面 |
| **三重檢測** | 幅度差分 + 相位變化 + 子載波相關性 |
| **智慧融合** | 加權投票、多數表決、序列確認 |
| **TUI儀表板** | 即時 ASCII 幅度頻譜與運動狀態 |
| **CSV匯出** | 歷史資料匯出供分析 |
| **Home Assistant** | 原生 MQTT 發現與狀態上報 |
| **自適應閾值** | 根據環境自動調整靈敏度 |
| **模擬模式** | 隨機、週期、突發三種運動模式 |

---

### 快速開始

#### 環境要求
- Python 3.8 或更高版本
- 支援監聽模式的 Wi-Fi 網卡（即時 CSI 需要）
- 或者直接使用模擬模式測試！

#### 安裝

```bash
# 克隆倉庫
git clone https://github.com/gitstq/WaveSense-CLI.git
cd WaveSense-CLI

# 直接執行（無需安裝任何依賴！）
python main.py --source simulated --pattern periodic

# 或安裝為套件
pip install -e .
wavesense --source simulated
```

#### 基礎用法

```bash
# 模擬資料 + 週期運動模式
python main.py --source simulated --pattern periodic

# 從 pcap 檔案讀取
python main.py --source pcap --file capture.pcap

# Linux 介面即時 CSI（需要 root）
sudo python main.py --source linux --interface wlan0 --channel 36

# 匯出 CSV + MQTT 上報 Home Assistant
python main.py --source simulated --csv output.csv --mqtt --broker 192.168.1.100

# 關閉儀表板，靜默模式
python main.py --source simulated --no-dashboard --quiet --csv data.csv
```

---

### 詳細使用指南

#### 命令列選項

```
資料源選項：
  --source {simulated,pcap,linux}  CSI 資料源（預設：simulated）
  --file, -f PATH                  pcap 檔案路徑
  --interface, -i NAME             無線網卡介面（預設：wlan0）
  --channel, -c NUMBER             Wi-Fi 信道（預設：36）
  --pattern {random,periodic,burst} 模擬運動模式
  --subcarriers NUMBER             子載波數量（預設：64）

檢測選項：
  --threshold FLOAT                檢測閾值（預設：0.15）
  --fusion {majority_vote,weighted_average,sequential}
                                   融合方法（預設：weighted_average）

輸出選項：
  --csv PATH                       匯出 CSV 檔案
  --mqtt                           啟用 MQTT 輸出
  --broker ADDRESS                 MQTT 代理（預設：localhost）
  --port NUMBER                    MQTT 埠（預設：1883）

UI 選項：
  --no-dashboard                   禁用 TUI 儀表板
  --quiet, -q                      靜默模式
```

#### 典型使用場景

**研究與開發**
```bash
# 使用不同運動模式測試檢測演算法
python main.py --source simulated --pattern burst --subcarriers 128 --threshold 0.2
```

**智慧家居整合**
```bash
# 持續監控並接入 Home Assistant
python main.py --source linux --interface wlan0 --mqtt --broker homeassistant.local
```

**資料採集**
```bash
# 記錄 CSI 資料用於離線分析
python main.py --source simulated --csv experiment_$(date +%Y%m%d).csv --no-dashboard
```

---

### 設計思路與迭代規劃

**設計原則：**
- **零依賴** —— 只要有 Python 就能執行
- **模組化架構** —— 易於擴充新的檢測器或資料源
- **自適應智慧** —— 閾值根據環境自動調整
- **開發者友好** —— 乾淨的 API 便於整合

**技術選型原因：**
- 純 Python 標準庫，最大化可攜性
- 抽象基類設計，支援可擴充的讀取器/檢測器
- 資料類定義清晰的資料結構
- ANSI 轉義碼實現終端 UI（無需 curses 依賴）

**後續迭代計劃：**
- [ ] 支援更多 CSI 晶片（Atheros、Broadcom、Qualcomm）
- [ ] 基於機器學習的檢測增強
- [ ] 跌倒檢測演算法
- [ ] 多房間定位
- [ ] Web 遠端儀表板
- [ ] REST API 伺服器模式

---

### 打包與部署指南

**作為 Python 套件：**
```bash
pip install -e .
wavesense --help
```

**作為獨立指令碼：**
```bash
python main.py [選項]
```

**Systemd 服務（Linux）：**
```ini
# /etc/systemd/system/wavesense.service
[Unit]
Description=WaveSense CSI 運動檢測
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/wavesense/main.py --source linux --mqtt
Restart=always
User=root

[Install]
WantedBy=multi-user.target
```

**Docker（未來）：**
```dockerfile
FROM python:3.11-slim
COPY . /app
WORKDIR /app
ENTRYPOINT ["python", "main.py"]
```

---

### 貢獻指南

歡迎貢獻！請遵循以下規範：

1. **Fork** 本倉庫
2. 建立**功能分支**（`git checkout -b feature/amazing-feature`）
3. **提交**更改（`git commit -m 'feat: add amazing feature'`）
4. **推送**到分支（`git push origin feature/amazing-feature`）
5. 發起 **Pull Request**

**提交規範：**
- `feat:` 新功能
- `fix:` 修復問題
- `docs:` 文件更新
- `refactor:` 程式碼重構
- `test:` 測試相關

---

### 開源協議

本專案採用 **MIT 協議** 開源 —— 詳見 [LICENSE](LICENSE) 檔案。
