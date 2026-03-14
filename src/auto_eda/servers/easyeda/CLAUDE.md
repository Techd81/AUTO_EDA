[根目录](../../../../CLAUDE.md) > [src/auto_eda](../../) > [servers](../) > **easyeda**

# easyeda — 嘉立创EDA Pro MCP Server

## 模块职责

本模块是 AUTO_EDA 当前唯一已完成的 MCP Server，提供 23 个 MCP 工具，通过 WebSocket 桥接嘉立创EDA Pro 桌面客户端。核心能力：原理图绘制、PCB布局布线、DRC/ERC检查、制造文件导出，以及 STM32F103C8T6 最小系统板全自动 14 步设计流程。

---

## 入口与启动

```bash
python -m auto_eda easyeda    # stdio 传输，供 Claude Desktop 使用
auto-eda easyeda              # entry point 方式
```

Server 启动时自动在后台线程启动 WebSocket 服务端（`ws://127.0.0.1:9050/`），等待 jlc-bridge 扩展连接。

---

## 对外接口（23个 MCP 工具）

| 分类 | 工具名 | 功能 |
|------|--------|------|
| 连接 | `eda_ping` | 检查EDA客户端连接，返回版本信息 |
| 连接 | `eda_get_status` | 列出打开文档及活动文档 |
| 原理图 | `sch_get_state` | 获取原理图元数据 |
| 原理图 | `sch_place_symbol` | 按LCSC料号放置符号 |
| 原理图 | `sch_add_wire` | 绘制导线段（mil坐标）|
| 原理图 | `sch_add_net_label` | 添加网络标签 |
| 原理图 | `sch_add_power_symbol` | 放置电源符号(VCC/GND/3V3/5V/VBUS) |
| 原理图 | `sch_run_erc` | 运行ERC，返回违规列表 |
| 原理图 | `sch_get_netlist` | 导出网表 |
| 原理图 | `sch_update_pcb` | 同步原理图到PCB |
| PCB | `pcb_get_state` | 获取PCB元数据 |
| PCB | `pcb_place_component` | 按LCSC料号放置封装 |
| PCB | `pcb_move_component` | 移动元件 |
| PCB | `pcb_route_track` | 布线（网络/层/线宽）|
| PCB | `pcb_create_via` | 创建过孔 |
| PCB | `pcb_flood_fill` | 铜皮填充（默认GND，B_Cu）|
| PCB | `pcb_run_drc` | 运行DRC |
| PCB | `pcb_screenshot` | 截取PCB预览图 |
| 导出 | `export_gerber` | 导出Gerber+钻孔文件 |
| 导出 | `export_bom` | 导出BOM(CSV/JSON，含LCSC料号) |
| 导出 | `export_pick_place` | 导出贴片坐标CPL |
| 全流程 | `draw_stm32_minimum_system` | STM32最小系统板14步全自动流程 |

---

## STM32 14步全自动流程（stm32_flow.py）

| 步骤 | 名称 | 操作 |
|------|------|------|
| 1 | eda_ping | 确认EDA客户端在线 |
| 2 | sch_place_symbols | 放置19个元件（含STM32/LDO/晶振/电容等）|
| 3 | sch_add_power_symbols | VCC/GND/3V3/VBUS电源符号 |
| 4 | sch_add_net_labels | SWDIO/SWDCLK/NRST/BOOT0/USART1 |
| 5 | sch_add_wires | 去耦电容导线桩 |
| 6 | sch_run_erc | ERC验证，有错误时中止 |
| 7 | sch_save | 保存原理图 |
| 8 | sch_auto_layout | 自动整理布局 |
| 9 | pcb_place_components | 导入PCB并按预置坐标定位19个封装 |
| 10 | pcb_auto_route | 触发自动布线 |
| 11 | pcb_flood_fill | GND铜皮填充(B_Cu) |
| 12 | pcb_run_drc | DRC验证 |
| 13 | pcb_screenshot | 截取预览图 |
| 14 | export | 导出Gerber+BOM+CPL |

流程含 5s 保活 ping 防止 EDA 桥接8s空闲超时。`FlowResult` 记录每步结果和输出文件路径。

---

## 关键依赖与配置

- `websockets>=13.0`：WS服务端（`websockets.asyncio.server.serve`）
- `mcp>=1.3.0` / FastMCP：MCP协议层
- `pydantic>=2.0`：所有工具I/O验证
- EDA Bridge 协议：端口9050，jlc-bridge.eext v0.0.17
- EDA 版本：嘉立创EDA Pro v3.2.91
- api-types.d.ts：`D:/lceda-pro/resources/app/assets/pro-api/0.2.8.83658458/api-types.d.ts`

**关键常量（components.py）：**
- LCSC系统库UUID：`0819f05c4eef4c71ace90d822a990e87`
- STM32F103C8T6 UUID：`accfc2f6010745268febab2459577079`（C8734）
- 19个元件全部预置LCSC UUID（C160935/J2 SWD除外为空）

---

## 数据模型

`models.py` 定义 46 个 Pydantic 模型（`<ToolName>Input` / `<ToolName>Result`）。所有 Result 含 `suggested_next_steps: list[str]`。共享子模型：`ComponentInfo`、`Violation`。

---

## 测试与质量

| 文件 | 测试数 | 内容 |
|------|--------|------|
| `test_bridge.py` | 6 | WS通信、ping、断开、ID递增 |
| `test_stm32_flow.py` | 6 | 组件表验证、全流程happy path、ping失败中止 |

**已知测试问题：** `test_bridge.py` 基于旧WS客户端架构（`EDABridge(url=...)`），与当前WS服务端架构不匹配，运行会失败，需重写。

---

## 常见问题 (FAQ)

**Q: EDA桥接连不上怎么办？**
A: 确认嘉立创EDA Pro已打开，jlc-bridge扩展已安装并启用「外部交互」权限，Server监听9050端口未被占用。

**Q: `eda.invoke` 报错「path格式错误」？**
A: path每段必须是合法JS标识符，用点分隔，例如 `sch_PrimitiveComponent.create`，不能含空格或特殊字符。

**Q: 放置元件时某个LCSC UUID为空怎么办？**
A: `components.py` 中 C160935（SWD接头）的UUID为空字符串，stm32_flow.py 会跳过并记录警告，不影响流程继续。

**Q: server.py中logger在使用前定义了吗？**
A: 存在行序问题：`_start_ws_server_thread` 中引用了 `logger`，但 `logger` 定义在模块下方（行70）。需将 `logger` 定义移至模块顶部。

---

## 相关文件清单

```
src/auto_eda/servers/easyeda/
├── __init__.py        # main() 入口
├── server.py          # 23个 @mcp.tool + WS后台线程启动
├── bridge.py          # EDABridge WS服务端 + get_bridge() 单例
├── stm32_flow.py      # draw_minimum_system() 14步编排
├── components.py      # STM32_MIN_SYS(19个) + LCSC UUID映射
└── models.py          # 46个Pydantic模型

tests/test_servers/test_easyeda/
├── __init__.py
├── test_bridge.py     # 6个测试（需重写适配WS服务端架构）
└── test_stm32_flow.py # 6个测试（组件表+流程）
```

---

## 变更记录 (Changelog)

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-03-14 | 0.1.0 | EasyEDA MCP Server完成，commit 3cad6da |
| 2026-03-14 | 0.2.0 | 架构师增量扫描，生成完整CLAUDE.md |
