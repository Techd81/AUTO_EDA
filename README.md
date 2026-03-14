# AUTO_EDA — 嘉立创EDA Pro MCP Server

> 用 AI 驱动嘉立创EDA Pro，一句话完成 STM32 最小系统板全流程设计。

## 简介

AUTO_EDA 是一个 [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) Server，专为**嘉立创EDA Pro**桌面客户端设计。
通过 WebSocket 桥接 EDA 内部 API，让 Claude 等 AI 模型能够直接操控 EDA 软件，完成原理图绘制、PCB 布局、DRC 检查、导出制造文件等完整流程。

### 核心特性

- **一句话绘板**：输入「帮我画一个 STM32F103C8T6 最小系统板」，自动完成14步全流程
- **真实 EDA 操作**：通过官方 Extension API 操控嘉立创EDA Pro，不是截图模拟
- **JLCPCB 直连**：BOM 含 LCSC 料号，Gerber/BOM/CPL 导出后可直接上传下单
- **23 个 MCP 工具**：涵盖原理图、PCB、库搜索、导出全链路

## 架构

```
Claude (AI)
    │ MCP Protocol (stdio)
    ▼
auto_eda/servers/easyeda/server.py   ← Python MCP Server (23 tools)
    │ WebSocket (ws://127.0.0.1:9050/)
    ▼
JLCEDA MCP Bridge 扩展               ← 嘉立创EDA Pro 内置扩展
    │ globalThis.eda.* Extension API
    ▼
嘉立创EDA Pro 桌面客户端
```

## 安装

### 前置要求

- Python 3.11+
- [嘉立创EDA Pro](https://lceda.cn/editor) 桌面客户端
- JLCEDA MCP Bridge 扩展（在 EDA 扩展广场搜索安装）

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/your-org/auto-eda.git
cd auto-eda

# 2. 安装依赖
pip install -e .

# 3. 在嘉立创EDA Pro 扩展管理器中：
#    - 搜索并安装「JLCEDA MCP Bridge」
#    - 启用扩展，开启「外部交互」权限

# 4. 启动 MCP Server
python -m auto_eda easyeda
```

### Claude Desktop 配置

在 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "auto-eda-easyeda": {
      "command": "python",
      "args": ["-m", "auto_eda", "easyeda"]
    }
  }
}
```

## 使用示例

### STM32 最小系统板全自动绘制

打开嘉立创EDA Pro，新建空白原理图，然后对 Claude 说：

```
帮我画一个 STM32F103C8T6 最小系统板
```

Claude 将自动执行 14 步流程：

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | 连接检查 | 确认 EDA 客户端在线 |
| 2 | 放置元件 | 18个器件（STM32/LDO/晶振/电容等）|
| 3 | 电源符号 | VCC/GND/3V3/VBUS |
| 4 | 网络标签 | SWDIO/SWDCLK/NRST/BOOT0/USART1 |
| 5 | 连线 | 去耦电容导线 |
| 6 | ERC检查 | 电气规则验证 |
| 7 | 保存 | 原理图保存 |
| 8 | 自动布局 | 原理图自动整理 |
| 9-12 | PCB流程 | 布局/布线/铺铜/DRC |
| 14 | 导出 | Gerber + BOM + CPL |

## MCP 工具列表

| 工具 | 功能 |
|------|------|
| `eda_ping` | 检查 EDA 连接状态 |
| `eda_get_status` | 获取当前文档信息 |
| `sch_place_symbol` | 放置原理图元件 |
| `sch_add_wire` | 添加导线 |
| `sch_add_net_label` | 添加网络标签 |
| `sch_add_power_symbol` | 添加电源符号 |
| `sch_run_erc` | 运行 ERC 检查 |
| `sch_get_netlist` | 导出网表 |
| `pcb_place_component` | PCB 放置元件 |
| `pcb_run_drc` | 运行 DRC 检查 |
| `export_gerber` | 导出 Gerber |
| `export_bom` | 导出 BOM（含 LCSC 料号）|
| `export_pick_place` | 导出贴片坐标 |
| `draw_stm32_minimum_system` | **STM32最小系统板全流程** |
| ...更多 | 共 23 个工具 |

## 项目结构

```
src/auto_eda/
├── __main__.py
├── core/
│   ├── base_server.py
│   ├── errors.py
│   └── result.py
└── servers/
    └── easyeda/
        ├── server.py      # 23个 MCP 工具
        ├── bridge.py      # WebSocket 桥接服务端
        ├── models.py      # Pydantic 数据模型
        ├── components.py  # STM32 元件库（含 LCSC UUID）
        └── stm32_flow.py  # 14步自动化流程
```

## 开发

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT
