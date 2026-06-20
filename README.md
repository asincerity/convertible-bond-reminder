# convertible-bond-reminder

可转债提醒 + 股票/基金技术分析与量化回测框架。

## 功能概览

### 1) 现有功能：可转债提醒
- 脚本：`/home/runner/work/convertible-bond-reminder/convertible-bond-reminder/check_bonds.py`
- 通过 GitHub Actions 定时运行，推送可转债申购与天气信息。

### 2) 新增功能：股票+基金技术分析与量化回测框架
- 入口脚本：`/home/runner/work/convertible-bond-reminder/convertible-bond-reminder/run_backtest.py`
- 配置文件：`/home/runner/work/convertible-bond-reminder/convertible-bond-reminder/configs/backtest.yaml`
- 核心模块目录：`/home/runner/work/convertible-bond-reminder/convertible-bond-reminder/quant_framework`

## 架构分层

- 数据层（data）
  - 统一 OHLCV+NAV 字段模型
  - 复权/分红/拆分处理
  - 数据质量校验（缺失、停牌、异常跳点）
- 研究层（indicators / factors / signals）
  - 技术指标：MA / MACD / RSI / KDJ / BOLL / ATR
  - 因子：动量、反转、波动率、质量代理
  - 信号标准化、阈值、冲突处理、衰减
- 策略层（strategies）
  - 趋势跟随、均值回归、横截面打分
  - 多策略加权融合
- 执行层（execution / backtest）
  - 交易成本、滑点、最小手数、T+1、流动性约束
  - 信号延迟、周期再平衡
- 风控层（risk）
  - 单标的仓位上限
  - 最大回撤防护、波动率目标、止损止盈
- 评估层（metrics / report）
  - 年化收益、Sharpe、Sortino、Calmar、最大回撤、胜率
  - 净值曲线、回撤曲线、持仓与交易明细
- 编排层（config / experiment）
  - 参数配置化、实验记录与可复现

## 目录结构

```text
/home/runner/work/convertible-bond-reminder/convertible-bond-reminder
├── check_bonds.py
├── run_backtest.py
├── configs/
│   └── backtest.yaml
├── quant_framework/
│   ├── __init__.py
│   ├── backtest.py
│   ├── config.py
│   ├── data.py
│   ├── execution.py
│   ├── experiment.py
│   ├── factors.py
│   ├── indicators.py
│   ├── metrics.py
│   ├── models.py
│   ├── report.py
│   ├── risk.py
│   ├── signals.py
│   └── strategies.py
└── requirements.txt
```

## 快速开始

1. 安装依赖

```bash
cd /home/runner/work/convertible-bond-reminder/convertible-bond-reminder
pip install -r requirements.txt
```

2. 生成默认配置（可选）

```bash
python run_backtest.py --init-config --config configs/backtest.yaml
```

3. 运行示例回测（自动生成演示数据）

```bash
python run_backtest.py --strategy blend --config configs/backtest.yaml --output outputs
```

4. 使用你自己的 CSV 数据

```bash
python run_backtest.py --data /absolute/path/to/your_data.csv --strategy cross_section --config configs/backtest.yaml --output outputs
```

CSV 需包含至少以下字段（小写或可自动转小写）：
- `symbol,date,open,high,low,close,volume`

可选字段：
- `amount,nav,adj_factor,dividend,split_ratio,is_suspended,asset_type`

## 分阶段落地路线

- Phase 1：日频数据 + 单策略回测闭环（已提供可运行骨架）
- Phase 2：多策略组合 + 风控增强
- Phase 3：基金专属处理 + 稳健性验证 + 自动报告扩展
- Phase 4：接入模拟盘/实盘执行接口（按券商/平台适配）

## 注意事项

- 当前回测引擎为通用研究框架，适合策略原型和离线评估。
- 实盘前请补充：更真实的成交模型、交易日历、停牌/涨跌停细则、风控审计、监控告警。
