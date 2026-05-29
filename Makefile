# WaveSense-CLI Makefile
# =======================
# 构建、测试和安装命令 / Build, test, and install commands

.PHONY: all install test lint clean help run-scan run-dashboard

# 默认目标 / Default target
all: help

# 安装 / Install
install:
	pip install -e .

# 开发安装（含测试依赖）/ Dev install (with test deps)
install-dev:
	pip install -e ".[dev]"

# 运行测试 / Run tests
test:
	python -m pytest tests/ -v

# 运行测试（含覆盖率）/ Run tests with coverage
test-cov:
	python -m pytest tests/ -v --cov=wavesense_cli --cov-report=term-missing

# 运行特定测试 / Run specific test
test-%:
	python -m pytest tests/test_$*.py -v

# 类型检查 / Type check
lint:
	python -m mypy wavesense_cli/

# 清理 / Clean
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ .mypy_cache/ .coverage htmlcov/
	rm -rf reports/

# 帮助 / Help
help:
	@echo "WaveSense-CLI 构建命令 / Build Commands"
	@echo "========================================"
	@echo "  make install      - 安装项目 / Install project"
	@echo "  make install-dev  - 开发安装 / Dev install with test deps"
	@echo "  make test         - 运行测试 / Run tests"
	@echo "  make test-cov     - 测试+覆盖率 / Tests with coverage"
	@echo "  make lint         - 类型检查 / Type check"
	@echo "  make clean        - 清理 / Clean build artifacts"
	@echo "  make help         - 显示帮助 / Show this help"
	@echo ""
	@echo "快速运行 / Quick Run:"
	@echo "  make run-scan     - 扫描WiFi / Scan WiFi"
	@echo "  make run-dashboard - 仪表盘 / Dashboard"
	@echo "  make run-heatmap  - 热力图 / Heatmap"

# 快速运行命令 / Quick run commands
run-scan:
	python -m wavesense_cli scan -v

run-dashboard:
	python -m wavesense_cli dashboard --simple

run-heatmap:
	python -m wavesense_cli heatmap
