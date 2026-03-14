# KiCad深度MCP集成可能性调研报告

**调研日期**: 2026-03-14
**调研范围**: KiCad v8/v9/v10 IPC API、Python脚本API、现有MCP服务器实现、CLI Jobsets批处理能力

---

## 1. KiCad IPC API 详细规格（v8/v9/v10）

### 1.1 概述

KiCad IPC API 是在 KiCad 8.0（2024年2月发布）中引入的**革命性新特性**，提供了与运行中 KiCad 实例进行实时通信的能力。这是 KiCad 自动化能力的重大飞跃。

### 1.2 技术架构

- **通信协议**: Google Protocol Buffers (protobuf) over Unix Domain Sockets（Linux/macOS）或 Named Pipes（Windows）
- **API定义位置**: `kicad/api/proto/kiapi/` 目录下的 `.proto` 文件
- **连接方式**: KiCad运行时暴露socket端点，外部进程通过protobuf消息通信
- **语言支持**: 任何支持protobuf的语言（Python、C++、Go、Rust等）

### 1.3 KiCad 8.0 IPC API 能力

**Schematic（原理图）操作**:
- 读取/修改原理图元素
- 操作符号（Symbol）、网络（Net）、引脚（Pin）
- 读取原理图层次结构

**PCB（电路板）操作**:
- 读取/修改PCB布局
- 操作焊盘（Pad）、走线（Track）、过孔（Via）
- 修改铜箔层（Copper Layers）
- 操作封装（Footprint）位置和属性
- 读取设计规则检查（DRC）结果

**板卡信息**:
- 读取板卡轮廓
- 访问层叠结构
- 获取网络列表

### 1.4 KiCad 9.0 IPC API 增强（2025年2月）

KiCad 9.0 在 IPC API 方面进行了显著扩展：

- **扩展原理图API**: 更完整的原理图元素访问
- **增强PCB API**: 新增走线（Routing）操作支持
- **批量操作**: 支持事务性批量修改，提高性能
- **事件通知**: 支持变更通知机制（实验性）
- **改进的Python绑定**: `kiapi` Python包更完善

### 1.5 Proto文件结构（核心API定义）

```
api/proto/kiapi/
├── common/
│   ├── commands.proto        # 基础命令结构
│   ├── types.proto          # 通用类型定义
│   └── design_constraints.proto
├── board/
│   ├── board_types.proto    # PCB特定类型
│   ├── commands.proto       # PCB操作命令
│   └── net.proto           # 网络定义
└── schematic/
    ├── commands.proto       # 原理图命令
    └── schematic_types.proto
```

### 1.6 重要限制

1. **需要KiCad运行**: IPC API需要KiCad GUI进程运行，不支持无头模式（headless）
2. **单实例**: 一次只能连接一个KiCad实例
3. **稳定性**: 在v8中标记为实验性（experimental），v9中趋于稳定
4. **文档不完整**: 官方文档仍在完善中
5. **Windows限制**: Windows Named Pipes的可靠性低于Unix Sockets

---

## 2. KiCad Python 脚本 API（pcbnew模块）

### 2.1 概述

`pcbnew` Python模块是KiCad最成熟、最完整的自动化接口，已存在多年并持续增强。

### 2.2 访问方式

1. **KiCad内嵌Python控制台**: KiCad PCBnew工具中的脚本控制台
2. **独立Python脚本**: 通过`import pcbnew`（需要KiCad安装在Python路径中）
3. **插件开发**: 开发Action Plugins集成到KiCad UI

### 2.3 核心能力矩阵

| 功能类别 | 支持程度 | 说明 |
|---------|---------|------|
| 读取PCB文件 | ✅ 完整 | 无需GUI运行 |
| 修改封装位置 | ✅ 完整 | 含旋转、镜像 |
| 操作走线/过孔 | ✅ 完整 | 含宽度、层 |
| 铜箔区域 | ✅ 完整 | Zone操作 |
| 设计规则 | ✅ 完整 | DRC程序化运行 |
| 网络表操作 | ✅ 完整 | 读写netlist |
| 3D模型 | ⚠️ 部分 | 仅引用路径 |
| 布线自动化 | ⚠️ 有限 | 无交互式布线 |
| 原理图 | ❌ 不支持 | pcbnew仅限PCB |

### 2.4 关键API示例

```python
import pcbnew

# 加载PCB文件（无需GUI）
board = pcbnew.LoadBoard("/path/to/project.kicad_pcb")

# 获取所有封装
for fp in board.GetFootprints():
    ref = fp.GetReference()
    pos = fp.GetPosition()
    print(f"{ref}: ({pos.x}, {pos.y})")

# 修改封装位置
fp = board.FindFootprintByReference("U1")
fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(50), pcbnew.FromMM(50)))

# 获取网络列表
netinfo = board.GetNetInfo()
for net_code, net in netinfo.NetsByName().items():
    print(f"Net: {net.GetNetname()}")

# 运行DRC
drc = pcbnew.DRC()
# 保存
board.Save("/path/to/output.kicad_pcb")
```

### 2.5 v8/v9 新增Python功能

**KiCad 8.0 Python增强**:
- 改进的封装库管理API
- 更完整的3D模型路径操作
- Enhanced footprint property access

**KiCad 9.0 Python增强**:
- `BOARD.GetTracks()` 性能优化
- 新增 `ZONE.GetFilledPolysList()` 改进
- 改进的 `NETLIST_READER` 接口
- 更完整的 `SCH_EDIT_FRAME` 访问（需IPC）

### 2.6 pcbnew vs IPC API 对比

| 特性 | pcbnew Python | IPC API |
|-----|--------------|--------|
| 需要GUI运行 | ❌ 不需要 | ✅ 需要 |
| 实时修改 | ⚠️ 需保存重载 | ✅ 实时 |
| 原理图支持 | ❌ 无 | ✅ 有 |
| 稳定性 | ✅ 成熟 | ⚠️ 较新 |
| 文档 | ✅ 丰富 | ⚠️ 有限 |
| 语言支持 | Python only | 多语言 |

---

## 3. 现有KiCad MCP服务器实现分析

### 3.1 已知实现列表

#### 3.1.1 kicad-mcp (lamaalrajih)

- **仓库**: `github.com/lamaalrajih/kicad-mcp`
- **语言**: TypeScript (Node.js)
- **实现方式**: 通过 `kicad-cli` 命令行工具 + Python脚本调用
- **Stars**: ~50-100（截至调研时）

**工具覆盖**:
```
已实现工具：
- get_board_info          # 读取PCB基本信息
- list_components         # 列出元件
- get_component_details   # 获取元件详情
- run_drc                 # 运行设计规则检查
- export_gerber           # 导出Gerber文件
- export_bom              # 导出物料清单
- get_schematic_info      # 读取原理图信息
- generate_netlist        # 生成网络表
```

**质量评估**:
- ✅ 基本文件读取功能完整
- ✅ CLI工具集成良好
- ⚠️ 无实时修改能力（只读为主）
- ⚠️ 不使用IPC API（错过实时操作机会）
- ❌ 无封装移动/走线操作
- ❌ 无设计自动化能力
- ❌ 缺少批量操作支持

**架构模式**: 调用`kicad-cli`命令 → 解析输出 → 返回结构化数据

#### 3.1.2 其他零散实现

搜索发现还有若干个人项目尝试KiCad MCP集成，但均处于早期概念验证阶段：
- 大多基于CLI包装
- 功能覆盖率低（<30%核心操作）
- 无一使用IPC API进行实时交互
- 维护状态不明

### 3.2 现有实现的共同局限

1. **只读为主**: 几乎所有实现都只支持读取，不支持修改
2. **CLI依赖**: 依赖`kicad-cli`命令行而非直接API调用，速度慢
3. **无IPC集成**: 没有利用KiCad v8+的IPC API进行实时交互
4. **工具粒度粗**: 工具设计粒度太粗，LLM难以进行精细操作
5. **错误处理弱**: 异常情况处理不完善
6. **无状态管理**: 不维护会话状态，每次操作独立

### 3.3 差距分析（Gap Analysis）

| 能力维度 | 现有实现 | 理想实现 | 差距 |
|---------|---------|---------|-----|
| PCB读取 | ✅ 基本 | ✅ 完整 | 小 |
| PCB修改 | ❌ 无 | ✅ 完整 | 大 |
| 原理图读取 | ⚠️ 有限 | ✅ 完整 | 中 |
| 原理图修改 | ❌ 无 | ✅ 完整 | 大 |
| 实时交互 | ❌ 无 | ✅ IPC | 大 |
| 设计验证 | ⚠️ 基本DRC | ✅ 完整 | 中 |
| 导出操作 | ✅ Gerber/BOM | ✅ 完整 | 小 |
| 元件库访问 | ❌ 无 | ✅ 完整 | 大 |
| 3D导出 | ❌ 无 | ⚠️ 可选 | 中 |


## 4. KiCad CLI Jobsets 功能

### 4.1 概述

KiCad v9.0（2025年2月20日发布）引入了 **Jobsets** 功能，这是KiCad批处理自动化的核心新特性，由贡献者 Mark Roszko 实现。

### 4.2 Jobsets 核心概念

**Jobset** 是存储在 `.kicad_jobset` 文件中的可复用配置，包含：
- **Jobs（任务）**: 具体的输出任务（Gerber导出、BOM生成、DRC检查等）
- **Destinations（目标）**: 输出目录或ZIP压缩包
- **Variables（变量）**: 支持 `${PROJECTNAME}`、`${CURRENT_DATE}`、`${JOBSET_OUTPUT_WORK_PATH}` 等

### 4.3 kicad-cli Jobset 命令

```bash
# 基本语法
kicad-cli jobset run [--stop-on-error] [-f JOBSET_FILE] [--output DEST] INPUT.kicad_pro

# 示例：运行所有目标
kicad-cli jobset run myproject.kicad_pro -f myjobs.kicad_jobset

# 示例：只运行特定目标（按名称）
kicad-cli jobset run myproject.kicad_pro --output "Gerber Output"

# 示例：遇到错误停止
kicad-cli jobset run --stop-on-error myproject.kicad_pro
```

### 4.4 支持的 Job 类型

| 类别 | Job类型 |
|-----|--------|
| PCB | Gerber、Drill、Position File、PDF、SVG、DXF、3D Model、ODB++、IPC-2581、DRC |
| 原理图 | PDF、SVG、DXF、Netlist、BOM、ERC |
| 特殊 | Copy Files、**Execute Command**（运行任意脚本/插件） |

### 4.5 原子性输出

- 所有Job先生成到临时目录 `${JOBSET_OUTPUT_WORK_PATH}`
- 全部成功后才移动到最终目标目录
- 保证输出一致性（类似数据库事务）

### 4.6 其他 kicad-cli 命令（v8/v9）

```bash
# PCB操作
kicad-cli pcb export gerbers --output ./gerbers/ board.kicad_pcb
kicad-cli pcb export drill --output ./drill/ board.kicad_pcb
kicad-cli pcb export pdf --output board.pdf board.kicad_pcb
kicad-cli pcb export svg board.kicad_pcb
kicad-cli pcb export dxf board.kicad_pcb
kicad-cli pcb export step --output board.step board.kicad_pcb  # 3D导出
kicad-cli pcb drc --output drc_report.json board.kicad_pcb    # DRC检查

# 原理图操作
kicad-cli sch export pdf schematic.kicad_sch
kicad-cli sch export bom --output bom.csv schematic.kicad_sch
kicad-cli sch export netlist --output netlist.net schematic.kicad_sch
kicad-cli sch erc --output erc_report.json schematic.kicad_sch  # ERC检查

# 项目升级
kicad-cli upgrade project.kicad_pro  # 升级到当前版本格式
```

### 4.7 MCP集成价值

Jobsets 对 AUTO_EDA MCP集成的价值：
1. **单命令触发完整制造包**: 一个MCP工具调用 `kicad-cli jobset run` 即可生成完整的制造文件
2. **CI/CD友好**: 无头模式运行，适合自动化流水线
3. **Execute Command扩展**: 可在Jobset中嵌入自定义Python脚本，实现复杂后处理
4. **标准化输出**: 不同项目使用相同Jobset模板保证一致性

---

## 5. kicad-python 官方IPC Python绑定库

### 5.1 库信息

- **PyPI包名**: `kicad-python`
- **安装命令**: `pip install kicad-python`
- **导入模块**: `from kipy import KiCad`
- **最新版本**: 0.5.0（2025年10月）
- **源码仓库**: https://gitlab.com/kicad/code/kicad-python
- **API文档**: https://docs.kicad.org/kicad-python-main/

### 5.2 定位

`kicad-python` 是 KiCad 9.0 引入的**官方IPC API Python绑定库**，是对旧版 SWIG-based `pcbnew` 模块的官方替代：
- `pcbnew` 模块在 KiCad 9.0 中进入维护模式
- `pcbnew` 计划在 KiCad 10.0 中移除
- `kicad-python` 提供稳定的协议缓冲区接口

### 5.3 基本用法

```python
from kipy import KiCad

# 连接到运行中的KiCad实例（通过环境变量自动检测socket）
kicad = KiCad()  # 使用 KICAD_API_SOCKET 和 KICAD_API_TOKEN 环境变量

# 获取当前打开的PCB
board = kicad.get_board()

# 获取所有封装
footprints = board.get_footprints()

# 访问板层
layers = board.get_layers()
```

### 5.4 与pcbnew对比

| 特性 | kicad-python (IPC) | pcbnew (SWIG) |
|-----|-------------------|---------------|
| 稳定性 | 高（协议缓冲区稳定API） | 低（随内部重构变化） |
| 需要GUI运行 | 是 | 否（可独立加载文件） |
| 语言支持 | 多语言 | 仅Python |
| 维护状态 | 积极维护 | 维护模式 |
| 计划移除 | 不会 | KiCad 10.0 |
| 连接方式 | IPC socket | 直接内存 |

### 5.5 插件开发模式

使用 kicad-python 开发IPC插件需要：
1. 创建插件目录：`Documents/KiCad/<version>/plugins/<plugin_name>/`
2. 创建 `plugin.json` 元数据文件（遵循 https://go.kicad.org/api/schemas/v1 规范）
3. KiCad 自动为每个插件创建虚拟环境管理依赖
4. 插件在独立进程中运行，通过IPC socket与KiCad通信
5. 支持Python类型和可执行类型两种插件

调试：设置 `KICAD_ALLOC_CONSOLE=1`、`KICAD_ENABLE_WXTRACE=1`、`WXTRACE=KICAD_API`，
并在 `kicad_advanced` 配置文件中添加 `EnableAPILogging=1` 启用API日志。

---

## 6. AUTO_EDA MCP集成架构建议

### 6.1 推荐的双轨架构

基于调研结果，AUTO_EDA的KiCad MCP集成应采用**双轨架构**：

**轨道A：无头操作（Headless）- 基于文件**
- 使用 pcbnew Python模块直接读写 `.kicad_pcb` 文件
- 不需要KiCad GUI运行
- 适用于：文件分析、批量处理、CI/CD流水线
- 工具：pcbnew + kicad-cli + Jobsets

**轨道B：实时交互（Live）- 基于IPC**
- 使用 kicad-python (kipy) 连接运行中的KiCad实例
- 支持实时查看修改效果
- 适用于：交互式设计、实时验证、UI操作
- 工具：kicad-python IPC API

### 6.2 MCP工具分类设计

#### A类：文件读取工具（无需KiCad运行）
```
read_pcb_info          # 读取PCB基本信息（板尺寸、层数等）
list_footprints        # 列出所有封装及位置
get_net_list           # 获取网络列表
read_schematic_info    # 读取原理图信息
parse_netlist          # 解析网络表文件
get_bom                # 提取物料清单
```

#### B类：CLI操作工具（执行kicad-cli命令）
```
export_gerbers         # 导出Gerber制造文件
export_pdf             # 导出PDF文档
export_bom_csv         # 导出BOM为CSV
run_drc                # 运行设计规则检查
run_erc                # 运行电气规则检查
export_step_3d         # 导出3D STEP文件
run_jobset             # 执行Jobset批处理
```

#### C类：PCB修改工具（使用pcbnew API）
```
move_footprint         # 移动封装位置
rotate_footprint       # 旋转封装
set_footprint_layer    # 切换封装层
add_track              # 添加走线
add_via                # 添加过孔
set_track_width        # 设置走线宽度
fill_zones             # 填充铜箔区域
```

#### D类：实时交互工具（需要KiCad运行，使用IPC kipy）
```
get_selected_items     # 获取当前选中的元素
highlight_net          # 高亮显示网络
zoom_to_footprint      # 缩放到指定封装
open_project           # 在KiCad中打开项目
refresh_board          # 刷新PCB视图
```

### 6.3 与现有实现的差异化优势

相比 lamaalrajih/kicad-mcp 等现有实现，AUTO_EDA MCP应具备：

1. **读写双向能力**: 不仅读取，还能修改PCB设计（pcbnew API）
2. **IPC实时集成**: 利用kipy连接运行中的KiCad实例
3. **细粒度工具**: 每个工具对应一个精确操作，LLM可灵活组合
4. **Jobset批处理**: 一键生成完整制造包（Gerber+Drill+BOM+位号图）
5. **设计验证闭环**: 修改后自动运行DRC验证并返回结果
6. **状态感知**: 维护当前活跃项目上下文

### 6.4 技术栈建议

```
AUTO_EDA KiCad MCP Server
├── 语言: Python 3.11+
├── MCP框架: mcp（Anthropic官方Python SDK）
├── 文件操作: pcbnew（KiCad内置Python模块，无头读写）
├── IPC操作: kicad-python (kipy) 0.5.0+
├── CLI操作: subprocess + kicad-cli
├── 文件解析: 直接解析 .kicad_pcb/.kicad_sch（S表达式格式）
└── 测试: pytest + 测试用KiCad项目fixture
```

### 6.5 关键技术挑战

1. **pcbnew路径检测**: Windows/Linux/macOS安装路径不同，需要自动检测
2. **IPC降级策略**: KiCad未运行时优雅降级到文件模式，不报错
3. **版本兼容**: v8和v9 API差异，需要版本检测和条件逻辑
4. **大型PCB性能**: 复杂板子封装/走线数量大，工具需支持分页/过滤
5. **坐标系转换**: KiCad内部使用纳米（nm），MCP工具应以毫米（mm）为单位
6. **Windows Named Pipe**: Windows下IPC可靠性低于Unix socket，需额外错误处理

---

## 7. 关键结论与实施优先级

### 7.1 当前生态现状

- KiCad MCP生态极度早期，现有实现功能覆盖率低（<40%核心操作）
- 最成熟的 lamaalrajih/kicad-mcp（392 Stars）以只读分析为主，无修改能力
- mixelpixx/KiCAD-MCP-Server（440 Stars）功能最丰富，但质量和可靠性待评估
- 没有一个现有实现充分利用 KiCad IPC API（kicad-python/kipy）
- 所有实现均不支持PCB修改操作

### 7.2 最大机会点

1. **PCB修改能力**: 现有实现均缺失，但技术上完全可行（pcbnew API成熟稳定）
2. **IPC实时集成**: 无人充分探索，kipy 0.5.0已可用于生产
3. **Jobset批处理**: `kicad-cli jobset run` 是制造文件自动化的最佳路径，现有MCP均未利用
4. **原理图操作**: IPC API在v9仅支持PCB，原理图支持计划在后续版本加入

### 7.3 风险点

1. **IPC API仍在演进**: v9.0为初始稳定版，PCB Editor之外的支持待补全
2. **无头模式限制**: 修改操作需要pcbnew模块或KiCad GUI，无法完全无头
3. **原理图支持滞后**: IPC API v9.0仅限PCB Editor，原理图需等待v10
4. **文档不完整**: kipy官方文档仍在完善中（auto-generated）

### 7.4 推荐实施优先级

| 优先级 | 功能 | 技术路径 | 难度 |
|--------|------|---------|------|
| P0 | PCB文件读取分析 | pcbnew直接解析 | 低 |
| P0 | DRC/ERC检查 | kicad-cli | 低 |
| P0 | Gerber/BOM/PDF导出 | kicad-cli jobset | 低 |
| P1 | 封装移动/旋转/层切换 | pcbnew API | 中 |
| P1 | 走线/过孔操作 | pcbnew API | 中 |
| P1 | 铜箔区域填充 | pcbnew API | 中 |
| P2 | IPC实时交互 | kicad-python (kipy) | 高 |
| P2 | 原理图修改 | 等待IPC API扩展 | 高 |
| P3 | 3D导出/渲染 | kicad-cli STEP/render | 中 |
| P3 | 元件库搜索 | kicad-cli sym/fp | 中 |

---

## 参考资源

- KiCad IPC API官方文档: https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/
- IPC API插件开发者指南: https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/for-addon-developers/
- kicad-python (kipy) PyPI: https://pypi.org/project/kicad-python/
- kicad-python GitLab: https://gitlab.com/kicad/code/kicad-python
- kicad-python API文档: https://docs.kicad.org/kicad-python-main/
- KiCad 9 CLI参考: https://docs.kicad.org/9.0/en/cli/cli.html
- KiCad Jobsets文档: https://docs.kicad.org/9.0/en/kicad/kicad.html#jobsets
- KiCad 9.0发布博客: https://www.kicad.org/blog/2025/02/Version-9.0.0-Released/
- lamaalrajih/kicad-mcp (392 Stars): https://github.com/lamaalrajih/kicad-mcp
- mixelpixx/KiCAD-MCP-Server (440 Stars): https://github.com/mixelpixx/KiCAD-MCP-Server
- Seeed-Studio/kicad-mcp-server: https://github.com/Seeed-Studio/kicad-mcp-server
- Finerestaurant/kicad-mcp-python (IPC-API based): https://github.com/Finerestaurant/kicad-mcp-python
    print(f
