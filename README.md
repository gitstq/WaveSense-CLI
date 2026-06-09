# WaveSense-CLI 项目方案设计文档

## 1. 项目定位

**WaveSense-CLI** — 轻量级终端Wi-Fi CSI（Channel State Information）运动感知与检测引擎

基于Wi-Fi信号的信道状态信息，无需额外硬件即可实现室内人体运动检测、存在感知、跌倒检测等功能。纯Python实现，零额外依赖，支持实时监控与历史数据分析。

## 2. 灵感来源与差异化

- **灵感来源**：参考espectre项目的Wi-Fi CSI运动检测理念
- **自研差异化**：
  - 纯Python零依赖实现（espectre依赖特定硬件驱动）
  - 支持多种CSI数据源（Linux nl80211、pcap文件、模拟数据）
  - 内置多种检测算法（幅度差分、相位变化、子载波相关性）
  - TUI实时可视化仪表板
  - 支持Home Assistant MQTT自动上报
  - 跨平台兼容（Linux/macOS/Windows模拟模式）

## 3. 技术栈选型

- **核心语言**：Python 3.8+
- **标准库**：socket, struct, subprocess, json, csv, argparse, threading, collections, math, statistics, time, datetime, signal, os, sys, pathlib, typing
- **零第三方依赖**：所有功能基于Python标准库实现

## 4. 核心功能清单

### 4.1 CSI数据采集模块
- [ ] Linux nl80211接口CSI数据读取（需兼容网卡）
- [ ] pcap文件离线解析
- [ ] 模拟数据生成器（用于测试与演示）
- [ ] 数据预处理与滤波

### 4.2 运动检测算法模块
- [ ] 幅度差分检测算法
- [ ] 相位变化检测算法
- [ ] 子载波间相关性分析
- [ ] 多算法融合决策引擎
- [ ] 自适应阈值调整

### 4.3 实时监控模块
- [ ] TUI终端仪表板（ASCII图表）
- [ ] 实时信号强度可视化
- [ ] 运动事件日志
- [ ] 检测灵敏度调节

### 4.4 数据输出模块
- [ ] CSV历史数据导出
- [ ] JSON实时数据流
- [ ] MQTT上报（Home Assistant集成）
- [ ] 告警通知（终端/日志）

### 4.5 系统管理模块
- [ ] 配置文件管理
- [ ] 后台服务模式
- [ ] 日志轮转
- [ ] 性能监控

## 5. 技术架构

```
WaveSense-CLI
├── core/
│   ├── csi_reader.py      # CSI数据读取接口
│   ├── csi_parser.py      # CSI数据解析
│   ├── csi_simulator.py   # 模拟数据生成
│   └── preprocessor.py    # 数据预处理
├── detection/
│   ├── amplitude_detector.py   # 幅度检测
│   ├── phase_detector.py       # 相位检测
│   ├── correlation_detector.py # 相关性检测
│   └── fusion_engine.py        # 融合决策
├── ui/
│   └── dashboard.py       # TUI仪表板
├── output/
│   ├── csv_exporter.py    # CSV导出
│   ├── mqtt_publisher.py  # MQTT上报
│   └── json_stream.py     # JSON流
├── utils/
│   ├── config.py          # 配置管理
│   ├── logger.py          # 日志工具
│   └── helpers.py         # 辅助函数
├── tests/
│   └── test_*.py          # 单元测试
├── main.py                # 入口程序
├── setup.py               # 安装配置
└── requirements.txt       # 依赖声明（空/标准库）
```

## 6. 工程化配置

- setup.py / pyproject.toml
- .gitignore
- Makefile（构建、测试、打包）
- 单元测试覆盖核心算法
- GitHub Actions CI（可选）

## 7. 自测标准

- [ ] 模拟数据模式下检测算法正常运行
- [ ] TUI仪表板无崩溃、刷新流畅
- [ ] CSV/JSON输出格式正确
- [ ] MQTT连接与上报正常
- [ ] 跨平台启动无报错
- [ ] 代码无高危安全漏洞

## 8. 项目类型

**插件/脚本/工具库类项目**
- 无需Release打包
- 通过pip安装或直接使用Python运行
- README需包含完整安装、使用、集成指南
