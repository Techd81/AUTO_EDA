# 商业EDA软件全景调研报告

**调研日期**: 2026-03-14
**调研范围**: Synopsys、Cadence、Siemens EDA (Mentor)、Ansys EDA
**重点**: 产品线全景、开源情况、MCP支持、Python API、AI集成现状

---

## 1. 商业EDA软件清单

### 1.1 Synopsys

| 工具名 | 类别 | 主要用途 | 开源情况 | 最新版本（2024-2025） |
|--------|------|---------|---------|--------------------|
| IC Compiler II (ICC2) | 布局布线 | 芯片物理实现 (Place & Route) | 闭源商业 | 2024.03+ |
| Design Compiler (DC) / Genus 竞品 | 综合 | RTL综合 (Synthesis) | 闭源商业 | 2024.03+ |
| PrimeTime (PT) | 时序分析 | 静态时序分析 (STA) | 闭源商业 | 2024.03+ |
| VCS | 仿真 | Verilog/SV/VHDL仿真 | 闭源商业 | 2024.03+ |
| Verdi | 调试 | 波形/代码调试分析 | 闭源商业 | 2024.03+ |
| Formality | 等价性检查 | 形式等价验证 (FEV) | 闭源商业 | 2024.03+ |
| VC SpyGlass | 静态分析 | 代码质量/CDC/RDC检查 | 闭源商业 | 2024.03+ |
| Fusion Compiler | 综合+布局布线 | RTL-to-GDS融合流程 | 闭源商业 | 2024.03+ |
| IC Validator (ICV) | 物理验证 | DRC/LVS验证 | 闭源商业 | 2024.03+ |
| StarRC | 寄生参数提取 | RC提取 | 闭源商业 | 2024.03+ |
| PrimeSim/HSPICE | 电路仿真 | SPICE/FastSPICE | 闭源商业 | 2024.03+ |
| DSO.ai | AI优化 | 设计空间优化AI | 闭源商业 | 集成于主平台 |
| VSO.ai | AI优化 | 验证空间优化AI | 闭源商业 | 集成于主平台 |
| TSO.ai | AI优化 | 测试空间优化AI | 闭源商业 | 集成于主平台 |

**Synopsys 产品平台**: Fusion Design Platform（融合了综合、布局布线、时序分析、物理验证）

**发布节奏**: 每年约2个主要版本，格式为 YYYY.MM（如 2024.03, 2024.09）

---

### 1.2 Cadence Design Systems

| 工具名 | 类别 | 主要用途 | 开源情况 | 最新版本（2024-2025） |
|--------|------|---------|---------|--------------------|
| Virtuoso Studio | 定制IC设计 | 模拟/定制电路设计 (Schematic + Layout) | 闭源商业 | ICADVM23.1 / IC23.1 |
| Genus Synthesis Solution | 综合 | RTL综合 | 闭源商业 | Genus23.1+ |
| Innovus Implementation System | 布局布线 | 数字IC物理实现 | 闭源商业 | Innovus23.1+ |
| Tempus Timing Signoff | 时序签核 | 静态时序分析 | 闭源商业 | Tempus23.1+ |
| Quantus | 寄生提取 | RC寄生参数提取 | 闭源商业 | Quantus23.1+ |
| Voltus | 功耗分析 | 电源完整性/功耗仿真 | 闭源商业 | Voltus23.1+ |
| Xcelium Logic Simulator | 仿真 | 数字仿真 (SV/UVM) | 闭源商业 | Xcelium23.1+ |
| Jasper Formal Verification | 形式验证 | 属性检查/形式验证 | 闭源商业 | JasperGold23.1+ |
| Modus DFT | 测试 | 可测试性设计 | 闭源商业 | 2024版 |
| Pegasus Physical Verification | 物理验证 | DRC/LVS (云端可扩展) | 闭源商业 | 2024版 |
| Spectre Circuit Simulator | 电路仿真 | AMS仿真 | 闭源商业 | Spectre23.1+ |
| Cerebrus AI | AI优化 | 机器学习驱动的流程优化 | 闭源商业 | 集成于流程 |
| JedAI | 生成式AI | 自然语言EDA助手 | 闭源商业 | 2024年发布 |
| Verisium | AI验证 | 基于AI的验证加速 | 闭源商业 | 2024版 |

**Cadence 产品平台**: Cadence.ai（整合AI能力平台）+ Cadence Intelligent System Design
**SKILL语言**: Cadence专有的类LISP脚本语言，是Virtuoso的主要自动化接口

---

### 1.3 Siemens EDA (前身 Mentor Graphics)

| 工具名 | 类别 | 主要用途 | 开源情况 | 最新版本（2024-2025） |
|--------|------|---------|---------|--------------------|
| Calibre | 物理验证 | DRC/LVS/PEX，行业标准 | 闭源商业 | Calibre 2024.1+ |
| Questa | 仿真/验证 | 数字/混合信号仿真 (SystemVerilog/UVM) | 闭源商业 | Questa 2024.1+ |
| ModelSim | 仿真 | FPGA/ASIC仿真（入门级） | 闭源商业 | 2024版 |
| Eldo / ADMS | 电路仿真 | 模拟/混合信号SPICE仿真 | 闭源商业 | 2024版 |
| HyperLynx | 信号完整性 | PCB信号/电源完整性仿真 | 闭源商业 | 2024版 |
| Xpedition PCB | PCB设计 | 高速PCB布局布线 | 闭源商业 | 2024版 |
| Capital | 线束设计 | 电气线束系统设计 | 闭源商业 | 2024版 |
| Tessent | DFT/测试 | 可测试性设计、内置自测 | 闭源商业 | Tessent 2024.1+ |
| Aprisa | 布局布线 | 数字IC P&R（竞争产品） | 闭源商业 | 2024版 |
| Catapult HLS | 高层综合 | C/C++到RTL综合 | 闭源商业 | 2024版 |
| EDA Cloud (Xcelerator) | 云平台 | 云端EDA工具服务 | 闭源商业 | 2024版 |

**Siemens EDA 平台**: Xcelerator（西门子数字化工业云平台的EDA部分）
**脚本接口**: 主要使用Tcl，Calibre支持SVRF/TVF规则文件格式

---

### 1.4 Ansys EDA

| 工具名 | 类别 | 主要用途 | 开源情况 | 最新版本（2024-2025） |
|--------|------|---------|---------|--------------------|
| HFSS | 电磁仿真 | 三维电磁场仿真 | 高频器件/天线/封装仿真 | 闭源商业 | 2024 R2 |
| SIwave | 信号/电源完整性 | PCB/封装信号电源完整性 | 闭源商业 | 2024 R2 |
| RedHawk-SC | 电源完整性 | SoC电源签核（云原生） | 闭源商业 | 2024 R1.1+ |
| Totem | 电源分析 | 模拟/混合信号电源分析 | 闭源商业 | 2024版 |
| PathFinder | 电迁移/ESD | 电迁移和ESD分析 | 闭源商业 | 2024版 |
| Icepak | 热分析 | 芯片/PCB热仿真 | 闭源商业 | 2024 R2 |
| Q3D Extractor | 寄生提取 | 3D/2D寄生参数提取 | 闭源商业 | 2024 R2 |

**Ansys EDA 平台**: Ansys Electronics Desktop (AEDT) 统一环境
**发布节奏**: 每年2个主要版本，格式为 YYYY R1/R2（如 2024 R1, 2024 R2）
**注**: Ansys 于2024年被 Synopsys 收购（$35B），整合进行中

---

## 2. 开源情况与许可证

| 厂商 | 许可模式 | 价格估算 | 教育/学术 | 源代码 |
|------|---------|---------|---------|-------|
| Synopsys | 专有商业许可（FlexLM/RLAC） | $150K-$500K+/席/年 | 有限教育项目 | 完全闭源 |
| Cadence | 专有商业许可（TBL/eDAcard） | $150K-$300K+/席/年 | 有限教育版 | 完全闭源 |
| Siemens EDA | 专有商业许可 | $100K-$300K+/席/年 | 有限学术授权 | 完全闭源 |
| Ansys EDA | 专有商业许可（HPC Pack） | $50K-$200K+/席/年 | 学生版（功能限制） | 完全闭源 |

**结论**: 四大商业EDA厂商工具均为**完全闭源专有软件**，无任何开源版本。许可费用高昂，中小团队和学术界无法负担正式许可。

---

## 3. MCP（Model Context Protocol）支持现状

### 3.1 各厂商官方MCP支持

| 厂商 | 官方MCP服务器 | MCP集成程度 | 接口类型 | 集成难度 |
|------|-------------|------------|---------|--------|
| **Synopsys** | 无官方MCP服务器发布 | 部分工具内部支持MCP协议（Verdi Assistant） | Verdi可作为MCP Server提供调试服务 | 高（需许可证+内部API访问） |
| **Cadence** | 无官方独立MCP服务器 | JedAI/ChipStack内部使用MCP架构 | MCP用于Agent间通信（内部） | 高（闭源，仅企业客户） |
| **Siemens EDA** | 无官方MCP服务器 | DAC 2025宣布EDA AI系统，明确讨论MCP | 增强型API层（MCP概念） | 高（需Xcelerator企业授权） |
| **Ansys EDA** | 无官方MCP服务器 | PyAEDT Python API为主要接口 | Python API（非MCP） | 中（有Python API但非MCP） |

### 3.2 关键发现

1. **Synopsys Verdi + MCP（已确认）**
   - Verdi可作为MCP Server向外部AI应用提供调试服务（波形分析、源码关联、原理图视图）
   - 参考：Synopsys博客《Using AI to Debug More Quickly and Accurately》
   - 需要企业许可证才能访问此功能

2. **Cadence JedAI + MCP（内部架构）**
   - ChipStack AI Super Agent内部使用MCP+A2A（Agent-to-Agent）协议
   - 无公开MCP服务器供第三方连接
   - 社区中有用户自建MCP服务器封装Cadence TCL/SKILL命令的案例

3. **Siemens EDA（概念层面）**
   - DAC 2025明确讨论MCP作为AI-EDA集成的API层
   - 尚未发布可连接的MCP服务器端点

4. **商业EDA MCP集成整体评估**
   - 商业EDA对MCP的支持处于**内部探索/早期采用**阶段
   - 均无面向外部开发者的公开MCP服务器
   - 访问需要高昂许可证费用

---

## 4. Python/脚本自动化接口

### 4.1 各工具脚本接口对比

| 工具/厂商 | 原生脚本语言 | Python支持 | Python接口类型 | 开放程度 |
|----------|-----------|----------|--------------|--------|
| **Synopsys PrimeTime** | Tcl | 是（官方） | `py_eval` + `set_app_var sh_language python` | 商业许可内可用 |
| **Synopsys Fusion Compiler** | Tcl | 部分 | 外部Python调用Tcl | 商业许可内 |
| **Synopsys VCS** | Tcl/SV | 部分 | 外部脚本封装 | 商业许可内 |
| **Cadence Virtuoso** | SKILL（类LISP） | 无官方API | skillbridge（第三方开源桥接） | 第三方开源 |
| **Cadence Innovus/Tempus** | Tcl（Stylus UI） | 部分 | 外部Python+Tcl混合 | 商业许可内 |
| **Cadence Sigrity** | Python | 是（官方） | 直接Python脚本 | 商业许可内 |
| **Siemens Calibre** | Tcl（TVF/SVRF） | 无官方API | Python调用Tcl批处理（间接） | 间接 |
| **Siemens Questa** | Tcl | 部分 | 外部封装 | 商业许可内 |
| **Siemens HyperLynx** | Python | 是（官方） | Python脚本API | 商业许可内 |
| **Ansys HFSS/SIwave** | Python | 是（官方） | PyAEDT（官方开源库） | **开源！** |
| **Ansys RedHawk-SC** | Python | 是（官方） | Python API | 商业许可内 |

### 4.2 重要发现：PyAEDT（Ansys官方开源Python库）

```
GitHub: https://github.com/ansys/pyaedt
许可证: MIT License
功能: 封装HFSS, SIwave, Q3D等所有Ansys EDA工具的Python API
特点: 官方维护、文档完善、支持自动化仿真流程
```

PyAEDT是四大商业EDA厂商中**唯一的官方开源Python API**，是连接商业EDA与AI/MCP的最佳切入点之一。

---

## 5. AI自动化能力对比

### 5.1 AI产品全景

| 厂商 | AI产品名 | 技术类型 | 成熟度 | 开放性 |
|------|---------|---------|-------|-------|
| **Synopsys** | DSO.ai | 强化学习（设计空间优化） | 生产级（数百次tapeout） | 闭源 |
| **Synopsys** | VSO.ai | 机器学习（验证覆盖优化） | 生产级 | 闭源 |
| **Synopsys** | TSO.ai | 机器学习（测试模式优化） | 生产级 | 闭源 |
| **Synopsys** | Synopsys.ai Copilot | 生成式AI（LLM辅助） | 早期采用（2025） | 闭源 |
| **Synopsys** | AgentEngineer | 多Agent自主设计 | 原型/早期（DAC 2025展示） | 闭源 |
| **Cadence** | Cerebrus AI Studio | 强化学习+ML（PPA优化） | 生产级（750+ tapeout） | 闭源 |
| **Cadence** | Verisium | 大数据+AI（验证加速） | 生产级 | 闭源 |
| **Cadence** | JedAI Platform | 数据平台+GenAI基础 | 生产级 | 闭源 |
| **Cadence** | ChipStack AI Super Agent | 多Agent全自动前端设计 | 发布（2026年初） | 闭源 |
| **Siemens EDA** | Solido AI | 机器学习（模拟变异分析） | 生产级 | 闭源 |
| **Siemens EDA** | Calibre Vision AI | AI（DRC违例分类修复） | 生产级 | 闭源 |
| **Siemens EDA** | Questa One Agentic | Agentic AI（验证） | 早期发布（2025） | 闭源 |
| **Siemens EDA** | EDA AI System (DAC 2025) | GenAI+Agentic（全栈） | 早期发布 | 闭源 |
| **Ansys** | AI/ML集成（AEDT） | ML（仿真时间预测） | 集成于工具 | 闭源 |

### 5.2 自主度等级对比（L1-L5）

```
L1 - 辅助建议：AI提供优化建议，人工确认执行
L2 - 参数优化：AI自动调整流程参数（DSO.ai、Cerebrus）
L3 - 任务自动化：AI自动完成单个设计任务
L4 - 子流程自主：AI自主完成多步骤设计子流程（AgentEngineer目标、ChipStack已实现）
L5 - 全自主设计：AI端到端自主完成芯片设计（未实现）
```

| 厂商 | AI产品 | 自主度等级 | 覆盖阶段 |
|------|-------|----------|--------|
| Synopsys | DSO.ai | L2 | 综合+布局布线PPA优化 |
| Synopsys | VSO.ai | L2 | 验证覆盖优化 |
| Synopsys | AgentEngineer | L3-L4（原型） | 多步骤设计任务 |
| Cadence | Cerebrus | L2 | 数字全流程PPA优化 |
| Cadence | ChipStack Super Agent | L4 | 前端设计+验证全流程 |
| Siemens | Solido AI | L2 | 模拟变异/良率分析 |
| Siemens | Questa One Agentic | L3 | 验证规划+执行 |

---

## 6. 第三方MCP服务器案例

### 6.1 已知开源MCP-EDA项目

| 项目 | GitHub | 覆盖工具 | 语言 | 状态 |
|------|--------|---------|------|------|
| **MCP4EDA** | github.com/NellyW8/MCP4EDA | Yosys+OpenLane+Icarus+GTKWave+KLayout | TypeScript/CLI | 活跃（2025） |
| **mcp4eda集合** | github.com/ssql2014/mcp4eda | 多工具EDA MCP服务器集合 | Python/TS | 活跃 |
| **MCP-EDA-Server** | github.com/Euler-Zhu/MCP-EDA-Server | Synopsys DC + Cadence Innovus封装 | Python | 实验性 |
| **kicad-mcp-server** | github.com/Seeed-Studio/kicad-mcp-server | KiCad PCB设计 | Python/TS | 活跃 |
| **DVT MCP Server** | AMIQ EDA官方 | 完整设计数据库访问 | — | 商业产品 |

### 6.2 MCP4EDA核心能力（最成熟开源方案）

```
论文: "MCP4EDA: LLM-Powered MCP RTL-to-GDSII Automation"
arXiv: 2507.19570
功能:
  - 自然语言控制完整RTL-to-GDSII流程
  - 支持Claude Desktop / Cursor IDE作为MCP客户端
  - 后端感知综合优化（backend-aware synthesis）
  - 覆盖: 综合→仿真→布局布线→物理验证→版图查看
局限:
  - 仅覆盖开源工具（无商业工具集成）
  - 无PCB设计支持
  - 无模拟/混合信号支持
  - 无可视化反馈闭环
```

### 6.3 商业EDA的第三方MCP封装模式

社区中出现了封装商业EDA工具的MCP服务器模式：

```python
# 典型模式：Python MCP服务器封装Cadence Tcl命令
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="cadence_innovus_server")

@mcp.tool()
def run_innovus_script(script_content: str) -> str:
    """在Cadence Innovus中执行Tcl脚本"""
    import subprocess
    # 写入临时Tcl文件并调用Innovus批处理
    result = subprocess.run(
        ["innovus", "-batch", "-files", script_path],
        capture_output=True, text=True
    )
    return result.stdout
```

此模式同样适用于Synopsys（Tcl）和Siemens Calibre（TVF/Tcl），但需要本地安装有效许可证。

---

## 7. 关键发现与结论

### 7.1 MCP支持现状总结

| 维度 | 结论 |
|------|------|
| 官方MCP服务器 | 四大厂商均无面向外部开发者的公开MCP服务器 |
| 内部MCP使用 | Synopsys(Verdi)、Cadence(JedAI/ChipStack)已内部使用MCP协议 |
| 第三方MCP | 开源工具链有成熟MCP服务器(MCP4EDA)；商业工具有实验性封装 |
| 访问门槛 | 商业EDA MCP功能需$100K-$500K+/年许可证，普通开发者无法获取 |

### 7.2 AUTO_EDA项目的战略意义

1. **市场空白确认**: 商业EDA AI全部闭源且价格高昂，开源MCP-EDA方案仅覆盖数字IC子集
2. **技术路径可行**: PyAEDT(MIT)、skillbridge(开源)、OpenROAD Python API提供了连接开源/商业工具的桥梁
3. **差异化机会**:
   - 全栈覆盖（PCB + 数字IC + 模拟 + 电磁仿真）
   - 可视化反馈闭环（截图→LLM分析→修改→验证）
   - 开源+社区生态
   - 面向中小团队和学术界的可负担方案

### 7.3 各厂商脚本接口可利用性评估

| 工具 | AUTO_EDA可利用性 | 方式 | 优先级 |
|------|----------------|------|-------|
| Ansys HFSS/SIwave | **高** | PyAEDT开源库，MIT许可 | P1 |
| Cadence Virtuoso | **中** | skillbridge开源桥接 | P2 |
| Synopsys PrimeTime | **低** | 需企业许可+Python接口 | P3 |
| Siemens Calibre | **低** | 仅Tcl间接封装 | P3 |

### 7.4 建议优先集成路径

```
阶段1（开源工具，无许可证需求）:
  KiCad IPC API → PCB设计MCP
  OpenROAD Python → 数字IC布局布线MCP
  Yosys Python → RTL综合MCP
  cocotb → 验证MCP
  PySpice/ngspice → 模拟仿真MCP

阶段2（半开放工具）:
  PyAEDT(MIT) → 电磁仿真MCP（需Ansys许可但API开源）
  KLayout Python API → 版图分析MCP

阶段3（商业工具封装，可选）:
  skillbridge → Cadence Virtuoso桥接
  Tcl封装 → Synopsys/Siemens批处理调用
```

---

## 8. 参考来源

- Synopsys官方产品页面及投资者新闻（synopsys.com, investor.synopsys.com）
- Synopsys博客《Using AI to Debug More Quickly》（Verdi+MCP集成证据）
- Cadence官方产品页面（cadence.com）
- Cadence ChipStack AI Super Agent发布公告（2026年2月）
- Siemens EDA DAC 2025公告（news.siemens.com, 2025年6月）
- Ansys Electronics Desktop产品文档
- PyAEDT GitHub: https://github.com/ansys/pyaedt
- skillbridge GitHub: https://github.com/unihd-cag/skillbridge
- MCP4EDA: https://github.com/NellyW8/MCP4EDA
- arXiv:2507.19570《MCP4EDA》论文
- Anthropic MCP协议规范（modelcontextprotocol.io）

---

*本报告基于2026-03-14公开信息整理，商业EDA工具版本和功能随时间持续更新。*
