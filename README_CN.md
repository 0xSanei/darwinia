# 🧬 Darwinia

**让你的 AI Agent 自己进化出交易策略。**

交易 Agent 通过达尔文自然选择和对抗式自我博弈发现策略——不是人类手写规则。

[![Tests](https://img.shields.io/github/actions/workflow/status/0xSanei/darwinia/test.yml?style=flat-square&label=tests)](https://github.com/0xSanei/darwinia/actions)
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-blue?style=flat-square)](https://www.python.org)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-skill-red?style=flat-square)](docs/OPENCLAW.md)
[![Claude Code](https://img.shields.io/badge/Claude_Code-兼容-blueviolet?style=flat-square)](https://claude.ai)

[English](README.md) | 中文

---

## OpenClaw / Claude Code 用户

```
直接告诉你的 Agent：

"安装 Darwinia，帮我进化一个 BTC 交易策略。"
```

Darwinia 是 [OpenClaw skill](.openclaw/SKILL.md) 和 [Claude Code skill](.claude/SKILL.md)。你的 Agent 可以自动安装、运行进化、返回结果——全程自然语言。

---

## 痛点

你手写 `RSI > 70 = 卖出`。市场变了，策略失效。手动调参数，周而复始。

## Darwinia 的做法

50 个带随机 DNA 的 Agent 在真实 BTC 数据上竞争。弱者淘汰，强者繁殖。50 代之后，幸存者能应对 rug pull、假突破、慢性下跌——不是因为你教了它们，而是**不能应对这些攻击的 Agent 已经被淘汰了**。

```
之前：人类写规则 → Agent 执行 → 市场变化 → 策略失效
之后：人类设环境 → Agent 进化 → 幸存者适应 → 模式涌现
```

---

## 快速开始

```bash
git clone https://github.com/0xSanei/darwinia.git
cd darwinia
pip install -e ".[dev]"

# 进化交易策略（30秒）
python -m darwinia evolve -g 10

# 对冠军进行对抗测试
python -m darwinia arena

# 启动可视化仪表盘
python -m darwinia dashboard
```

无需 API Key。无需云服务。纯 Python + numpy。数据已内置。

<details>
<summary>运行示例</summary>

**进化过程：**
```
🧬 Darwinia — Evolution Engine
   Generations: 20 | Population: 30 | Data: BTC/USDT 1h (10,946 candles)

   Gen   0 | ██████░░░░░░░░░░░░░░ | champ=0.32 avg=0.04 div=1.56
   Gen   5 | █████████████████████████████ | champ=1.46 avg=0.43 div=0.81
   Gen  19 | ████████████████████████ | champ=1.24 avg=0.64 div=0.57

✅ Evolution complete! 16 patterns discovered.
```

**对抗竞技场：**
```
⚔️ Darwinia — Adversarial Arena

   whipsaw              | PnL: +0.00% | ✅ survived
   fake_breakout        | PnL: +0.00% | ✅ survived
   rug_pull             | PnL: -3.21% | ✅ survived
   slow_bleed           | PnL: -1.05% | ✅ survived

   Survival rate: 100.0%
```

</details>

---

## 核心机制

### 17 基因 DNA 编码

| 类别 | 基因数 | 控制 |
|------|--------|------|
| **信号权重** | 5 | 关注什么——动量、成交量、波动率、均值回归、趋势 |
| **阈值** | 4 | 何时行动——入场、出场、止损、止盈 |
| **性格** | 5 | 如何行为——风险偏好、时间偏好、逆向程度、耐心、仓位 |
| **适应** | 3 | 如何适应——regime 敏感度、记忆长度、噪声过滤 |

### 对抗竞技场

对手**读取 Agent 的 DNA 找到弱点**，生成定向攻击：Rug Pull、假突破、慢性下跌、来回割、虚假成交量、拉高出货。

### 自动模式发现

进化结束后分析幸存者**为什么活下来**——基因收敛揭示涌现式交易规则，映射为人类可读的策略概念。

---

## Agent 集成

所有命令支持 `--json` 输出：

```bash
python -m darwinia evolve -g 50 --json
```

| 平台 | 集成方式 |
|------|----------|
| **OpenClaw** | `.openclaw/SKILL.md` → [集成指南](docs/OPENCLAW.md) |
| **Claude Code** | `.claude/SKILL.md` 自动检测 |
| **任何 CLI Agent** | `python -m darwinia evolve --json` |

---

## 超越交易

进化引擎与领域无关。DNA → 适应度 → 选择 → 繁殖 的循环可以进化任何可评分的 Agent 行为：投资组合优化、风险调优、资源分配、博弈策略。

---

## 开发

```bash
make setup       # 安装依赖
make test        # 运行 22 项测试
make evolve      # 50 代进化
make arena       # 对抗竞技场
make dashboard   # Streamlit 仪表盘
```

## 许可

MIT — 见 [LICENSE](LICENSE)
