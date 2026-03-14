# R4: 现有MCP Server在设计/工程工具中的应用调研

> 调研日期: 2026-03-14
> 调研范围: EDA、CAD、工程仿真、硬件开发领域的MCP Server生态

---

## 目录

1. [MCP协议概述](#1-mcp协议概述)
2. [EDA领域MCP Server](#2-eda领域mcp-server)
3. [CAD/设计工具类MCP Server](#3-cad设计工具类mcp-server)
4. [工程仿真类MCP Server](#4-工程仿真类mcp-server)
5. [硬件开发类MCP Server](#5-硬件开发类mcp-server)
6. [MCP Server生态总体情况](#6-mcp-server生态总体情况)
7. [对AUTO_EDA项目的启示](#7-对auto_eda项目的启示)

---

## 1. MCP协议概述

### 什么是MCP (Model Context Protocol)

- **发布时间**: 2024年11月由Anthropic开源发布
- **治理**: 2025年12月捐赠给Linux基金会下属的Agentic AI Foundation
- **协议规范**: 基于JSON-RPC 2.0的开放标准，2025-11-25版本为最新正式规范
- **核心功能**: 标准化AI模型（如Claude、ChatGPT、Copilot）与外部工具/数据源之间的安全双向连接
- **类比**: 被称为"AI的USB-C接口"——任何兼容的AI客户端都可以通过统一协议连接到任何MCP服务器

### MCP架构模型

```
AI客户端 (Claude Desktop/Cursor/VS Code)
    ↕ MCP协议 (JSON-RPC 2.0)
MCP Server (暴露tools/resources/prompts)
    ↕ 本地API/CLI
目标应用 (KiCad/Blender/MATLAB等)
```

### 支持MCP的主要客户端

| 客户端 | 类型 | 备注 |
|--------|------|------|
| Claude Desktop | AI助手 | Anthropic官方客户端 |
| Claude Code | CLI工具 | 开发者CLI |
| Cursor | IDE | AI代码编辑器 |
| VS Code + Copilot | IDE | GitHub Copilot集成 |
| Zed | IDE | 原生MCP支持 |
| Windsurf | IDE | Codeium产品 |
| OpenAI ChatGPT | AI助手 | 2025年后支持 |

---

## 2. EDA领域MCP Server

### 2.1 MCP4EDA — VLSI/ASIC设计自动化

**最成熟的EDA领域MCP Server**

- **GitHub**: https://github.com/NellyW8/MCP4EDA
- **网站**: https://www.agent4eda.com/
- **论文**: arXiv 2507.19570 (2025年7月)
- **功能范围**: 完整的RTL-to-GDSII流程自动化

#### 集成的EDA工具

| 工具 | 功能 | 在MCP4EDA中的角色 |
|------|------|-------------------|
| Yosys | 逻辑综合 | RTL综合（支持ice40、Xilinx、通用FPGA目标） |
| Icarus Verilog | 仿真 | Verilog功能验证和仿真 |
| Verilator | 仿真 | 高性能C++仿真 |
| OpenLane | 物理设计 | 完整Place & Route流程 |
| KLayout | 版图查看 | GDSII版图可视化 |
| GTKWave | 波形查看 | 仿真波形分析 |

#### 核心特性

- **自然语言驱动**: AI可执行如"为ice40 FPGA综合这个Verilog设计并优化时序"的指令
- **闭环优化**: LLM基于后端布局后的指标（PPA）自动优化TCL脚本
- **性能提升**: 论文报告10-30%的PPA（功耗/性能/面积）改善
- **后端感知综合**: 利用布局后时序信息指导综合优化

#### 安装示例

```bash
git clone https://github.com/NellyW8/MCP4EDA
cd MCP4EDA && npm install && npm run build
node build/index.js
# 在Claude Desktop配置中添加MCP server URL
```

### 2.2 KiCad MCP Server — PCB设计自动化

**多个独立实现，覆盖PCB设计全流程**

| 项目 | GitHub | 特点 |
|------|--------|------|
| KiCAD-MCP-Server | mixelpixx/KiCAD-MCP-Server | 暴露KiCad Python API |
| kicad-mcp | lamaalrajih/kicad-mcp | AI辅助原理图/PCB编辑 |
| kicad-mcp-server | Seeed-Studio/kicad-mcp-server | Seeed Studio维护 |
| kicad-mcp-python | Finerestaurant/kicad-mcp-python | Python实现 |

#### 共同功能

- 读取和分析原理图（SCH）和PCB布局
- 运行DRC（设计规则检查）和ERC（电气规则检查）
- AI建议元器件放置和布线
- 追踪引脚级网络连接
- 生成设备树和测试代码
- 兼容KiCad 9.0（2025）和v10 RC（2026）

### 2.3 DVT MCP Server — HDL开发

- **供应商**: AMIQ
- **功能**: Verilog/VHDL代码分析、lint检查、IDE集成
- **定位**: 面向RTL设计验证的AI辅助

### 2.4 EDA领域MCP Server小结

| 项目 | 领域 | 成熟度 | 开源 | 活跃度 |
|------|------|--------|------|--------|
| MCP4EDA | VLSI/ASIC (RTL-to-GDSII) | 高 | 是 | 活跃 |
| KiCad MCP (多个) | PCB设计 | 中-高 | 是 | 活跃 |
| DVT MCP | HDL验证 | 中 | 部分 | 活跃 |

**关键发现**: EDA领域的MCP Server已具备完整的RTL-to-GDSII和PCB设计流程覆盖能力，且都是2025年后出现的新项目。

---

## 3. CAD/设计工具类MCP Server

### 3.1 Blender MCP Server — 3D建模

**MCP生态中最成功的设计工具集成之一**

#### 主要项目

| 项目 | GitHub | Stars | 特点 |
|------|--------|-------|------|
| blender-mcp | ahujasid/blender-mcp | ~17,700 | 最流行，支持多种AI 3D生成 |
| Blender-MCP-Server | poly-mcp/Blender-MCP-Server | - | 51+工具，HTTP端点 |
| blender-open-mcp | dhakalnirajan/blender-open-mcp | - | 本地Ollama LLM支持 |

#### ahujasid/blender-mcp 功能（v1.5.5，2026年1月更新）

- 创建/修改3D对象、材质、场景
- Poly Haven和Sketchfab资产下载
- Hyper3D/Rodin/Hunyuan3D AI 3D模型生成
- Blender内Python代码执行
- 视口截图供AI理解场景
- 相机和灯光控制

#### 官方认可

- **2025年11月**: Blender Foundation发布Blender Lab，明确列出"AI和ML技术，从Blender MCP服务器开始"为2026年首批探索项目

### 3.2 Figma MCP Server — UI设计

**官方支持，设计到代码的桥梁**

- **发布**: 2025年6月（Beta），2026年初GA
- **官方服务器**: https://mcp.figma.com/mcp
- **类型**: Figma官方在Dev Mode中集成

#### 核心功能

- 从设计文件提取结构化上下文（组件层级、变量、自动布局、样式）
- 支持Code Connect映射到真实设计系统组件
- AI生成精确匹配设计的React/Tailwind/Vue代码
- **2026年新增**: 双向工作流 — 代码可推送回Figma画布生成可编辑图层

#### 支持的AI客户端

Cursor, Claude Code, VS Code Copilot, Codex, Windsurf, Warp, Factory等15+客户端

#### 社区扩展

- GLips/Figma-Context-MCP: 更深层的读写自动化

### 3.3 FreeCAD MCP Server — 开源参数化CAD

| 项目 | 特点 |
|------|------|
| spkane/freecad-mcp | "Robust MCP Server w/ Bridge"，80+工具 |
| neka-nat/freecad-mcp | 完整PartDesign、布尔运算、Python执行 |

- 支持参数化建模、文档控制、全部通过Claude Desktop操作
- 2026年社区活跃度高，工具数量持续增长

### 3.4 OpenSCAD MCP Server — 脚本化CSG建模

| 项目 | 特点 |
|------|------|
| jhacksman/openscad-mcp | AI生成OpenSCAD代码、PNG预览、STL渲染 |
| jkoets/openscad-mcp | 文本/图像到参数化模型 |
| fboldo/openscad-mcp | 类似功能变体 |

- 特别适合算法化/3D打印导向的生成式设计

### 3.5 AutoCAD / Fusion 360 MCP Server

**Autodesk企业级MCP生态**

- **AutoCAD**: 社区MCP Server支持自然语言制图、AutoLISP自动化
- **Fusion 360**: 多个开源MCP Server + Autodesk官方公共MCP Server
  - 完整API访问、Python脚本执行
  - 支持云协作、仿真驱动设计
  - Autodesk在2026年将MCP推广至整个"Design and Make"产品线

#### Autodesk MCP战略

- 发布官方Fusion Data Explorer MCP Server
- 集成到Autodesk Assistant
- 支持OAuth等企业安全特性
- 计划覆盖AutoCAD、Revit、Civil 3D等

### 3.6 CAD/设计工具MCP Server小结

| 工具 | 官方MCP | 社区MCP | Stars/热度 | 成熟度 |
|------|---------|---------|------------|--------|
| Blender | 计划中(2026) | 多个实现 | ~17.7k | 高 |
| Figma | 官方支持 | 有扩展 | N/A(官方) | 高 |
| FreeCAD | 无 | 多个(80+工具) | 中 | 中-高 |
| OpenSCAD | 无 | 多个 | 低 | 中 |
| Fusion 360 | 官方支持 | 多个 | 中 | 高 |
| AutoCAD | 计划中 | 社区 | 低-中 | 中 |

---

## 4. 工程仿真类MCP Server

### 4.1 MATLAB MCP Core Server — 官方最成熟

**MathWorks官方产品级支持**

- **发布时间**: 2025年10月
- **GitHub**: https://github.com/matlab/matlab-mcp-core-server
- **产品页**: https://www.mathworks.com/products/matlab-mcp-core-server.html
- **类型**: 官方发布，可执行文件分发

#### 核心功能

- AI代理可启动/退出MATLAB会话
- 编写、运行、调试MATLAB代码
- 执行完整Simulink模型仿真
- 控制硬件（Data Acquisition Toolbox）
- 评估代码风格和正确性
- **2026年2月博客**: Claude Code自主构建和运行Simscape多物理场模型

#### 安装配置

```bash
# 下载exe从GitHub
# 配置AI客户端
claude mcp add --transport stdio matlab
# 指向MATLAB安装路径 (R2025b/R2026a)
```

### 4.2 COMSOL Multiphysics MCP Server — 社区驱动

- **来源**: LobeHub / MCP Marketplace（2026年初可用）
- **功能**: AI自动化多物理场仿真全流程
  - 创建几何体
  - 设置物理场
  - 求解
  - 后处理结果分析
- **要求**: 需安装COMSOL 5.x/6.x
- **状态**: 社区驱动，功能完整但非官方

### 4.3 ANSYS MCP Server — 定向工具

| MCP Server | 目标工具 | 功能 |
|------------|----------|------|
| STK-MCP | Ansys STK | 卫星任务仿真（桌面和Engine模式） |
| Fluent MCP | Ansys Fluent | 文档导航 + 仿真触发 |

- **GitHub**: https://github.com/alti3/stk-mcp (STK)
- **状态**: 针对特定工具，ANSYS全面集成仍在发展中
- ANSYS也有自己的AI工具SimAI

### 4.4 工程仿真MCP Server小结

| 工具 | 官方MCP | 成熟度 | 覆盖度 |
|------|---------|--------|--------|
| MATLAB/Simulink | 官方支持 | 高 | 完整 |
| COMSOL | 社区 | 中 | 基本完整 |
| ANSYS STK | 社区 | 中 | 特定工具 |
| ANSYS Fluent | 社区 | 低-中 | 文档+基本仿真 |

---

## 5. 硬件开发类MCP Server

### 5.1 Arduino MCP Server

**多个实现，从简单控制到完整开发流程**

| 项目 | 特点 |
|------|------|
| amahpour/arduino-mcp-server-simple | 简单Python示例，快速入门 |
| AimanMadan/Arduino_MCP_Server | pyfirmata协议控制 |
| Octopart教程 | 详细构建指南 |

#### 暴露的工具

- `list_boards`: 检测已连接Arduino板
- `compile_sketch(sketch_path, fqbn)`: 编译草图
- `upload_sketch`: 上传到板卡
- `serial_write`: 实时引脚/LED/Firmata控制

#### 使用场景

AI可以执行如"将blink草图上传到Nano，每500ms闪烁LED 13"这样的自然语言指令。

### 5.2 FPGA/Verilog MCP Server

#### MCP4EDA（同EDA部分）

- 支持FPGA目标综合（ice40、Xilinx等）
- AI可执行"为Xilinx FPGA综合此Verilog"、运行仿真、分析波形

#### 专用FPGA MCP

| 项目 | 特点 |
|------|------|
| fpgaZeroMCP | 专注FPGA零配置自动化 |
| DE10-Nano MCP | Quartus自动化（Reddit社区） |
| DVT MCP Server | Verilog/VHDL lint和分析 |

#### Reddit社区案例

- 用户用Claude Code生成MCP Server自动化DE10-Nano/ADI板卡的FPGA构建/部署/测试循环

### 5.3 硬件开发MCP Server小结

| 领域 | 可用MCP Server | 成熟度 |
|------|---------------|--------|
| Arduino控制 | 多个Python实现 | 中-高 |
| FPGA综合/仿真 | MCP4EDA + 专用 | 中 |
| Verilog/VHDL分析 | DVT MCP | 中 |
| PCB设计 | KiCad MCP (多个) | 中-高 |

---

## 6. MCP Server生态总体情况

### 6.1 生态规模（截至2026年3月）

| 指标 | 数据 |
|------|------|
| 总MCP Server数量 | 7,000-18,000+（不同统计口径） |
| 官方Registry条目 | 数百个且快速增长 |
| SDK月下载量 | 9700万+ |
| GitHub awesome列表Star数 | punkpeye/awesome-mcp-servers最高 |

### 6.2 核心注册和目录

| 资源 | URL | 描述 |
|------|-----|------|
| 官方MCP Registry | https://registry.modelcontextprotocol.io/ | 权威注册中心，支持搜索和发布 |
| 官方参考实现 | https://github.com/modelcontextprotocol/servers | Anthropic维护的参考Server |
| mcpservers.org | https://mcpservers.org/ | 分类精选目录 |
| mcp.so | https://mcp.so | 社区目录，18,000+收录 |
| awesome-mcp-servers | https://github.com/punkpeye/awesome-mcp-servers | 最活跃的GitHub awesome列表 |

### 6.3 GitHub热门awesome列表

| 仓库 | 特点 |
|------|------|
| punkpeye/awesome-mcp-servers | 最全面，4000+提交，持续更新至2026年3月 |
| MobinX/awesome-mcp-list | 精简版 |
| patriksimek/awesome-mcp-servers-2 | 含客户端支持矩阵 |
| win4r/Awesome-Claude-MCP-Servers | Claude专属优化 |
| raoufchebri/awesome-mcp | 分类清晰 |

### 6.4 主要MCP Server分类

| 类别 | 典型Server |
|------|-----------|
| 搜索/Web | Exa, Firecrawl, Bright Data |
| 开发/云 | GitHub官方MCP, Cloudflare, Playwright |
| 数据库 | PostgreSQL, MongoDB, Redis |
| 浏览器自动化 | Playwright, Browserbase, Puppeteer |
| 生产力 | Slack, Notion, Google Workspace |
| 文件系统 | Filesystem (官方参考实现) |
| 金融/DeFi | DeFiLlama, Pyth Hermes |
| 设计/CAD | Blender, Figma, FreeCAD |
| 工程 | MATLAB, KiCad, MCP4EDA |

### 6.5 MCP协议时间线

| 时间 | 事件 |
|------|------|
| 2024年11月 | Anthropic开源发布MCP |
| 2025年上半年 | 社区快速增长，GitHub awesome列表爆发 |
| 2025年6月 | Figma发布官方MCP Server |
| 2025年7月 | MCP4EDA论文发表 |
| 2025年9月 | 官方MCP Registry预览版 |
| 2025年10月 | MATLAB MCP Core Server发布 |
| 2025年11月 | MCP规范2025-11-25版本；Blender Lab宣布 |
| 2025年12月 | MCP捐赠给Linux基金会Agentic AI Foundation |
| 2026年初 | 生态爆发，18,000+ Server，全面企业采用 |

---

## 7. 对AUTO_EDA项目的启示

### 7.1 EDA MCP的现状与机会

**已有覆盖**:
- VLSI/ASIC: MCP4EDA覆盖RTL-to-GDSII（Yosys + OpenLane）
- PCB: 多个KiCad MCP Server
- HDL验证: DVT MCP Server
- FPGA: 部分覆盖（通过MCP4EDA的Yosys目标）

**明显空白**:
- **电路仿真**: 无SPICE/LTSpice/ngspice的MCP Server
- **信号完整性**: 无SI/PI分析工具MCP
- **热仿真**: 无EDA热分析MCP
- **DFM/DFT**: 无可制造性/可测试性分析MCP
- **多工具协同**: 无统一的EDA工作流编排MCP
- **商业EDA**: Cadence/Synopsys/Siemens无公开MCP Server

### 7.2 架构参考模式

从成功的MCP Server中可以总结以下模式:

1. **工具封装模式** (MCP4EDA): 封装多个CLI工具，通过MCP暴露统一接口
2. **API桥接模式** (KiCad MCP): 桥接应用的Python API到MCP协议
3. **官方集成模式** (Figma/MATLAB): 应用厂商直接实现MCP支持
4. **插件+服务器模式** (Blender MCP): 应用内插件(addon) + 外部MCP Server通信

### 7.3 技术栈选择参考

| 技术选择 | 常见方案 | 备注 |
|----------|----------|------|
| 实现语言 | Python (FastMCP/uvx) 或 TypeScript (Node) | Python在EDA领域更常见 |
| 通信方式 | stdio (本地) 或 SSE (远程) | 本地开发建议stdio |
| 包管理 | npm (TS) 或 pip/uvx (Python) | |
| 配置 | JSON配置文件 | 兼容Claude Desktop标准 |

### 7.4 关键成功因素

基于生态调研，MCP Server成功的关键因素:

1. **解决真实痛点**: 设计到代码（Figma）、自然语言3D建模（Blender）
2. **降低门槛**: 一键安装，最少配置
3. **工具丰富度**: 覆盖完整工作流而非单点功能
4. **社区活跃**: GitHub Stars和持续更新
5. **文档质量**: 清晰的安装和使用指南
6. **兼容性**: 支持多个AI客户端（不仅限于Claude）

### 7.5 建议方向

AUTO_EDA项目可以考虑:

1. **补充空白**: 构建电路仿真（SPICE）MCP Server是最大机会
2. **工作流编排**: 构建多EDA工具协同的编排层MCP
3. **统一接口**: 为KiCad + ngspice + OpenLane提供统一MCP入口
4. **差异化**: 关注信号完整性、热仿真等专业领域
5. **集成现有**: 可以构建在MCP4EDA和KiCad MCP之上，而非重复造轮子

---

## 附录: 主要项目链接汇总

### EDA
- MCP4EDA: https://github.com/NellyW8/MCP4EDA
- Agent4EDA: https://www.agent4eda.com/
- KiCad MCP: https://github.com/lamaalrajih/kicad-mcp

### CAD/设计
- Blender MCP: https://github.com/ahujasid/blender-mcp
- Figma MCP: https://mcp.figma.com/mcp
- FreeCAD MCP: https://github.com/neka-nat/freecad-mcp

### 仿真
- MATLAB MCP: https://github.com/matlab/matlab-mcp-core-server
- STK-MCP: https://github.com/alti3/stk-mcp

### 硬件
- Arduino MCP: https://github.com/amahpour/arduino-mcp-server-simple

### 生态
- MCP官方规范: https://modelcontextprotocol.io/
- MCP Registry: https://registry.modelcontextprotocol.io/
- MCP官方Servers: https://github.com/modelcontextprotocol/servers
- Awesome MCP: https://github.com/punkpeye/awesome-mcp-servers
- mcpservers.org: https://mcpservers.org/
- mcp.so: https://mcp.so
