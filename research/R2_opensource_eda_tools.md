# R2: 开源EDA工具全景调研报告

> 调研日期: 2026-03-14
> 调研范围: PCB设计、数字IC设计、模拟/仿真、HDL及编译器基础设施、开源PDK

---

## 目录

1. [PCB设计工具](#1-pcb设计工具)
2. [数字IC设计工具](#2-数字ic设计工具)
3. [模拟/仿真工具](#3-模拟仿真工具)
4. [其他开源EDA项目](#4-其他开源eda项目)
5. [工具对比总表](#5-工具对比总表)
6. [关键发现与建议](#6-关键发现与建议)

---

## 1. PCB设计工具

### 1.1 KiCad

| 属性 | 详情 |
|------|------|
| **官方网站** | https://www.kicad.org/ |
| **代码仓库** | GitLab (主): gitlab.com/kicad/code/kicad; GitHub (镜像): KiCad/kicad-source-mirror |
| **GitHub Stars** | ~2,600 (镜像仓库) |
| **最新版本** | 9.0.7 (2026年1月稳定版); 10.0.0 RC2 (2026年3月7日) |
| **许可证** | GPL v3+ |
| **活跃贡献者** | 数百名 (GitLab主仓库) |
| **Python支持** | 有 - IPC API (v10新增Pythonic接口替代旧SWIG绑定) |
| **CLI接口** | 有 - Jobsets支持批量CLI操作 (v9+) |

**核心功能:**
- 完整的原理图捕获 + PCB布局设计 + 3D查看器
- Zone Manager (铜箔管理)、Design Blocks (可复用设计块)
- 嵌入式文件 (自包含项目)、Bezier曲线
- 多通道设计、组件类和网络类规则区域
- Pad Stacks (层级焊盘形状)
- ODB++ 导出支持

**v10新特性 (2026年即将发布):**
- 新导入器: Cadence Allegro (.brd), Mentor PADS, gEDA/Lepton EDA
- 装配变体系统 (Assembly Variants) - 管理多BOM/装配选项
- 成熟的IPC API + 原理图编辑器API
- Windows原生暗色模式、可自定义工具栏

**插件生态:**
- Plugin and Content Manager (PCM) - 内置插件管理器
- Interactive HTML BOM (iBOM)、KiCost、KiKit (拼板自动化)、FreeRouting (自动布线)
- SparkFun、Digi-Key、SnapMagic、LCSC 库集成

**社区活跃度:**
- forum.kicad.info (每日数千帖)
- Discord (~7k+ 成员)
- KiCon年度会议 (欧洲/亚洲/北美)
- CERN、Raspberry Pi Foundation、Digi-Key 支持

**与商业工具对比:**
KiCad是Altium Designer和Eagle的最强开源替代品。v9/v10的功能已覆盖大部分专业PCB设计需求,但在超复杂多层板(32层以上)和高速信号完整性分析方面仍有差距。

---

### 1.2 LibrePCB

| 属性 | 详情 |
|------|------|
| **官方网站** | https://librepcb.org/ |
| **GitHub仓库** | https://github.com/LibrePCB/LibrePCB |
| **GitHub Stars** | ~2,800 |
| **最新版本** | 2.0.1 (2026年2月) |
| **许可证** | GPL v3 |
| **Python支持** | 无原生API |
| **CLI接口** | 有 - CLI自动化支持 |

**核心功能:**
- 集成原理图 + PCB编辑器
- 优秀的库管理系统 (层次化、自包含项目)
- 实时DRC、制造服务集成
- HTML BOM、KiCad库兼容
- 版本控制友好的文件格式
- 跨平台 (Windows, macOS, Linux)

**2025-2026亮点:**
- v2.0.0 (2026年1月) - 全新现代UI (标签页、分割窗口)
- 原理图总线、原理图图片支持
- 对初学者极其友好

---

### 1.3 FreePCB

| 属性 | 详情 |
|------|------|
| **官方网站** | http://www.freepcb.com/ |
| **GitHub仓库** | https://github.com/Duxah/FreePCB-2 (活跃分支) |
| **最新版本** | 原版停更于2010; FreePCB-2 v2.4计划中 |
| **许可证** | GPL |
| **Python支持** | 无 |
| **CLI接口** | 无 |

**状态:** 原版已停止开发。FreePCB-2分支仍有少量维护,仅支持Windows,适合极简单的PCB布局。不推荐用于新项目。

---

### 1.4 gEDA

| 属性 | 详情 |
|------|------|
| **官方网站** | http://www.geda-project.org/ |
| **状态** | 已停滞/废弃 (2025年无新发布) |
| **许可证** | GPL v2 |
| **Python支持** | 无 (Guile脚本) |

**状态:** gEDA套件 (gschem + PCB) 自2025年已基本停止开发,GTK2兼容性问题导致在现代系统上难以运行。推荐迁移到:
- **pcb-rnd / Ringdove EDA** - 活跃的PCB布局分支
- **Lepton EDA** - gschem的活跃分支
- **KiCad** - v10已支持gEDA文件导入

---

## 2. 数字IC设计工具

### 2.1 OpenROAD (RTL-to-GDSII全流程)

| 属性 | 详情 |
|------|------|
| **官方网站** | https://theopenroadproject.org/ |
| **GitHub仓库** | https://github.com/The-OpenROAD-Project/OpenROAD |
| **GitHub Stars** | ~1,800+ (主仓库) |
| **许可证** | BSD 3-Clause |
| **Python支持** | 有 - Python绑定和TCL接口 |
| **CLI接口** | 有 - 完整CLI工具链 |
| **最近更新** | 2026年3月 (持续活跃) |
| **活跃贡献者** | 37,980+ commits |

**核心功能:**
- 完整的无人参与RTL-to-GDSII流程 (24小时设计周转)
- 综合 (通过Yosys)、布局规划、放置、时钟树综合、布线、签核
- 分层物理设计支持
- 3DIC支持 (3Dblox数据模型)
- AI/LLM辅助设计

**2025年里程碑:**
- 分层物理设计用于3DIC
- AI/LLM设计协助 (Design Copilot)
- 改进的时序收敛
- 超过600个流片验证 (180nm到12nm)
- 支持PDK: SkyWater 130nm, ASAP7, GlobalFoundries

**关联项目:**
- **OpenROAD-flow-scripts**: https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts
- **文档**: https://openroad.readthedocs.io/

---

### 2.2 Yosys (综合工具)

| 属性 | 详情 |
|------|------|
| **官方网站** | https://yosyshq.net/yosys/ |
| **GitHub仓库** | https://github.com/YosysHQ/yosys |
| **GitHub Stars** | ~4,300 |
| **Forks** | ~1,100 |
| **贡献者** | 290 |
| **最新版本** | 0.63 (2026年3月) |
| **许可证** | ISC |
| **Python支持** | 有 - Pyosys (pybind11重写) |
| **CLI接口** | 有 - 完整TCL/命令行接口 |

**核心功能:**
- RTL综合框架 (Verilog/SystemVerilog到网表)
- 广泛的Verilog-2005支持
- ABC集成用于逻辑优化
- 支持多种FPGA目标: Xilinx, Lattice (ECP5, Nexus), Gowin, QuickLogic
- ASIC综合流程支持

**2025年关键更新:**
- DSP推断: Gowin GW1N/GW2A、Xilinx预加器减法
- 统一synth_lattice pass (合并synth_ecp5/synth_nexus)
- SDC pass: 读取SDC时序约束文件
- 实验性OpenSTA集成
- Pyosys用pybind11完全重写
- RTLIL解析器重建
- 新pass: opt_balance_tree、opt_hier、design_equal、lut2bmux
- 并行ABC和opt_merge执行
- SystemVerilog支持扩展 (SV2017, unique/priority if)

**定位:** "硬件的GCC" - 最广泛使用的开源RTL综合工具。

---

### 2.3 OpenSTA (静态时序分析)

| 属性 | 详情 |
|------|------|
| **GitHub仓库(上游)** | https://github.com/parallaxsw/OpenSTA |
| **GitHub仓库(OpenROAD)** | https://github.com/The-OpenROAD-Project/OpenSTA |
| **GitHub Stars** | 104 (上游) / ~555 (OpenROAD分支) |
| **Forks** | 57 / 240 |
| **主要作者** | James Cherry (Parallax Software) |
| **许可证** | GPL v3 / 商业双许可 |
| **Python支持** | 有限 - TCL接口为主 |
| **CLI接口** | 有 - TCL命令行接口 |

**核心功能:**
- 门级静态时序分析
- 支持格式: Verilog网表、Liberty (.lib)、SDC、SDF、SPEF、VCD/SAIF
- 完整时钟处理 (生成时钟、延迟、不确定性)
- 高级路径例外 (false path、multicycle)
- 有效电容延迟计算 (Dartu/Menezes/Pileggi + Arnoldi)
- 可嵌入定时引擎 (API集成)

**2025年关键更新:**
- **Release 3.0.0 (2025年11月)**: 重大MCMM (多角多模) 支持 - 通过"scenes"组合模式/角落
  - 新命令: define_scene, set_mode, read_sdc -mode, report_checks -scenes
- **Release 2.7.0 (2025年5月)**: 构建改进、路径报告增强
- **2025年9月**: 集成VPR用于FPGA后布线STA

---

### 2.4 Magic VLSI (版图工具)

| 属性 | 详情 |
|------|------|
| **官方网站** | http://opencircuitdesign.com/magic/ |
| **GitHub仓库** | https://github.com/RTimothyEdwards/magic |
| **GitHub Stars** | ~620 |
| **Forks** | 136 |
| **最新版本** | 8.3.620 (2026年3月) |
| **许可证** | BSD |
| **Python支持** | 无 (Tcl/Tk脚本) |
| **CLI接口** | 有 - Tcl命令行 |

**核心功能:**
- 分层版图编辑器
- 连续/增量DRC
- 电路提取 (SPICE)、LVS
- 迷宫布线
- 支持CIF/GDS/LEF/DEF
- "Plowing"操作 (压缩/拉伸)
- 技术文件支持 (SCMOS, Sky130等)

**定位:** 1980年代Berkeley经典工具,深度集成DRC/提取,特别适合模拟版图和教学。

---

### 2.5 KLayout (版图查看/编辑)

| 属性 | 详情 |
|------|------|
| **官方网站** | https://www.klayout.de/ |
| **GitHub仓库** | https://github.com/KLayout/klayout |
| **GitHub Stars** | ~1,100 |
| **Forks** | 265 |
| **最新版本** | 0.30.7 (2026年3月) |
| **许可证** | GPL v2 |
| **Python支持** | 有 - Python + Ruby脚本 (强大的宏/PCell) |
| **CLI接口** | 有 |

**核心功能:**
- 高速GDS/OASIS文件查看和编辑
- 分层编辑和变换
- 强大的Python和Ruby脚本 (自动化、PCell)
- DRC/LVS能力 (通过Ruby脚本)
- XOR/diff工具、标记浏览器
- 技术包支持

**定位:** 现代化的版图查看/编辑器,脚本自动化能力极强,是开源PDK (Sky130, GF180)工作流的标配工具。

---

## 3. 模拟/仿真工具

### 3.1 ngspice (电路仿真)

| 属性 | 详情 |
|------|------|
| **官方网站** | https://ngspice.sourceforge.io/ |
| **GitHub仓库** | https://github.com/ngspice/ngspice (镜像) |
| **最新版本** | 45.2 (2025年9月) |
| **许可证** | BSD 3-Clause |
| **Python支持** | 有限 - 通过PySpice等外部库 |
| **CLI接口** | 有 - 交互式命令行 |

**核心功能:**
- 完整SPICE仿真器 (DC, AC, 瞬态, 噪声等)
- XSPICE混合信号仿真
- Verilog-A支持 (通过OpenVAF/OSDI)
- KiCad深度集成

**2025年关键更新 (v45):**
- d_cosim支持VHDL协仿真 (通过GHDL)
- BSIM4更新至4.8.3
- VBIC双极性晶体管改进
- 新命令: save nointernals
- XSPICE事件节点iplot
- Icarus Verilog协仿真 (v44延续)

**定位:** 最广泛使用的桌面级开源SPICE仿真器,混合信号能力强。

---

### 3.2 Xyce (电路仿真)

| 属性 | 详情 |
|------|------|
| **官方网站** | https://xyce.sandia.gov/ |
| **GitHub仓库** | https://github.com/Xyce/Xyce |
| **最新版本** | 7.10 (2025年8月) |
| **许可证** | GPL v3 |
| **Python支持** | 有 - Python/MATLAB/Simulink集成示例 (v7.10) |
| **CLI接口** | 有 |

**核心功能:**
- 高性能并行电路仿真 (MPI)
- 适合超大规模电路 (100k+器件)
- SPICE兼容
- Sandia国家实验室开发

**2025年关键更新:**
- **v7.9 (2025年1月)**: 新增BSIM-CMG v111.2.1; BSIMSOI修复; DTEMP参数; .PARAM函数定义; M乘法器扩展
- **v7.10 (2025年8月)**: TABLE表达式容忍乱序数据; 弃用autotools转CMake; MKL内存泄漏修复; Python/MATLAB/Simulink集成示例

**定位:** 超大规模并行仿真专家,适合电力系统、辐射效应等HPC场景。

**ngspice vs Xyce:**
| 对比 | ngspice | Xyce |
|------|---------|------|
| 最佳场景 | 桌面混合信号仿真 | 大规模并行仿真 |
| 并行能力 | 有限 | MPI全面并行 |
| KiCad集成 | 深度集成 | 无直接集成 |
| 学习曲线 | 低 | 中等 |

---

### 3.3 Verilator (Verilog仿真)

| 属性 | 详情 |
|------|------|
| **官方网站** | https://www.veripool.org/verilator/ |
| **GitHub仓库** | https://github.com/verilator/verilator |
| **GitHub Stars** | ~3,400 |
| **Forks** | 771 |
| **最新版本** | 5.038+ (2025年持续发布) |
| **许可证** | LGPL v3 / Artistic License 2.0 |
| **Python支持** | 通过cocotb集成 |
| **CLI接口** | 有 |

**核心功能:**
- 最快的开源Verilog/SystemVerilog仿真器
- 将HDL编译为多线程C++/SystemC
- Lint检查
- 性能可达传统解释型仿真器的1000倍

**2025年亮点:**
- 多个点版本发布 (5.038 2025年7月等)
- Coverage/Linter增强
- CHIPS Alliance项目成员

**定位:** 性能王者,适合需要高速仿真的场景。

---

### 3.4 cocotb (Python验证框架)

| 属性 | 详情 |
|------|------|
| **官方网站** | https://www.cocotb.org/ |
| **GitHub仓库** | https://github.com/cocotb/cocotb |
| **GitHub Stars** | ~2,300 |
| **Forks** | 618 |
| **最新版本** | 2.0.1 (2025年11月) |
| **许可证** | BSD |
| **Python支持** | 核心 - 纯Python验证框架 |
| **CLI接口** | 通过Makefile/pytest集成 |

**核心功能:**
- Python协程驱动RTL验证
- 支持多种仿真器: Verilator (>=5.036), Icarus Verilog, ModelSim, VCS等
- 利用Python生态 (pytest, numpy, asyncio)
- 替代传统SystemVerilog/UVM测试平台

**2025年重大更新 (v2.0):**
- 2.0.0 (2025年9月) + 2.0.1 (2025年11月)
- 性能改进、更好的Verilator支持
- 提升最低Verilator版本要求至5.036

**Verilator + cocotb组合:** 开源硬件验证的最佳实践 - Verilator提供极速仿真引擎,cocotb提供Python生产力。

---

### 3.5 QUCS / Qucs-S (RF仿真)

| 属性 | 详情 |
|------|------|
| **官方网站** | https://ra3xdh.github.io/ |
| **GitHub仓库** | https://github.com/ra3xdh/qucs_s (活跃版) |
| **最新版本** | 25.2.0 (2025年9月) |
| **许可证** | GPL |
| **Python支持** | 无原生API (可通过CLI外部调用) |
| **CLI接口** | 有限 - 仿真内核CLI |

**核心功能:**
- Qt6 GUI电路仿真器
- 多仿真内核: Ngspice, Xyce, QucsatorRF
- RF/微波: S参数分析、谐波平衡、微带线
- Smith图和极坐标图

**2025年更新:**
- 25.1.0: 组件属性对话框重设计、CDL网表导出
- 25.2.0: Ngspice微带线支持、Jiles-Atherton磁芯模型、噪声贡献绘图

**注意:** 原始QUCS (Qucs/qucs) 活跃度极低,Qucs-S是实际的活跃继承者。无原生Python API是主要局限。

---

## 4. 其他开源EDA项目

### 4.1 OpenLane / LibreLane (自动化数字后端流程)

| 属性 | 详情 |
|------|------|
| **GitHub仓库** | https://github.com/The-OpenROAD-Project/OpenLane (维护模式) |
| **继任者** | https://github.com/librelane/librelane |
| **GitHub Stars** | ~1,700 (原版) / ~326 (LibreLane) |
| **许可证** | Apache 2.0 |
| **Python支持** | 有 - LibreLane基于Python模块化架构 |
| **CLI接口** | 有 |

**核心功能:**
- 全自动RTL-to-GDSII流程
- 集成工具: Yosys (综合) + OpenROAD (布局布线) + Magic/Netgen/KLayout (DRC/LVS)
- 支持PDK: SkyWater SKY130 (默认), GlobalFoundries GF180MCU

**2025年重要变化:**
- 原OpenLane进入维护模式 (最后提交2025年9月)
- LibreLane (原OpenLane 2) 于2025年8月由FOSSi Foundation发布为社区继任者
- 向后兼容,相同PDK支持

---

### 4.2 SkyWater PDK

| 属性 | 详情 |
|------|------|
| **GitHub仓库** | https://github.com/google/skywater-pdk |
| **工艺节点** | 130nm |
| **许可证** | Apache 2.0 |
| **Python支持** | 通过open_pdks工具链 |

**说明:** Google与SkyWater Technology合作的首个完全开源的生产级PDK。包含标准单元库、IO库、原始器件模型。是开源芯片设计的基石,多次MPW (Multi-Project Wafer) 流片验证。

---

### 4.3 GlobalFoundries PDK

| 属性 | 详情 |
|------|------|
| **GitHub仓库** | https://github.com/google/gf180mcu-pdk |
| **工艺节点** | 180nm MCU |
| **许可证** | Apache 2.0 |
| **变体** | gf180mcuC, gf180mcuD (不同金属层堆叠) |

**说明:** Google与GlobalFoundries合作的开源PDK,适合MCU级别的芯片设计。与OpenLane/LibreLane完全集成。

---

### 4.4 CIRCT (MLIR-based编译器基础设施)

| 属性 | 详情 |
|------|------|
| **官方网站** | https://circt.llvm.org/ |
| **GitHub仓库** | https://github.com/llvm/circt |
| **GitHub Stars** | ~2,100 |
| **最新版本** | firtool-1.142.0 (2026年3月) |
| **许可证** | Apache 2.0 (LLVM) |
| **Python支持** | 有 - Python绑定 |
| **CLI接口** | 有 - firtool等命令行工具 |

**核心功能:**
- LLVM孵化项目 - 将MLIR方法论应用于硬件工具链
- 多层次方言: FIRRTL, HW, Comb, SV, Calyx, ESI, Handshake, Moore/LLHD
- firtool: FIRRTL到SystemVerilog的高质量编译
- SAT求解器集成、波形追踪
- SystemVerilog前端 (通过slang v10.0)

**2025年里程碑:**
- 稳定API标记 (~2025年3月)
- Chisel 7.0 Layer API支持 (2025年4月)
- 持续方言扩展

**定位:** 硬件的LLVM - 共享编译器基础设施,Chisel的默认后端。

---

### 4.5 Chisel (硬件描述语言)

| 属性 | 详情 |
|------|------|
| **官方网站** | https://www.chisel-lang.org/ |
| **GitHub仓库** | https://github.com/chipsalliance/chisel |
| **最新版本** | 7.9.0 (2026年) |
| **许可证** | Apache 2.0 |
| **语言基础** | Scala嵌入式DSL |

**核心功能:**
- 参数化硬件生成器
- 类型安全、函数式编程风格
- 通过FIRRTL -> CIRCT (firtool) -> SystemVerilog
- CHIPS Alliance项目成员

**与CIRCT关系:** Chisel现代版本通过CIRCT的firtool作为默认后端,替代旧FIRRTL编译器。

---

### 4.6 SpinalHDL (硬件描述语言)

| 属性 | 详情 |
|------|------|
| **GitHub仓库** | https://github.com/SpinalHDL/SpinalHDL |
| **最新版本** | 1.14.0 (2026年) |
| **许可证** | MIT / LGPL |
| **语言基础** | Scala嵌入式DSL |

**核心功能:**
- 强类型位宽系统
- 显式时钟域管理 (ClockDomain)
- 直接生成VHDL/Verilog (不依赖CIRCT)
- 强大的元编程能力
- 仿真支持

**与Chisel对比:**
| 对比 | Chisel | SpinalHDL |
|------|--------|-----------|
| CIRCT集成 | 默认后端 | 无 |
| 输出 | 通过firtool到SystemVerilog | 直接生成VHDL/Verilog |
| 时钟域 | 隐式 | 显式 (更安全) |
| 社区规模 | 更大 (CHIPS Alliance) | 较小但活跃 |
| 最佳场景 | ASIC流程 | FPGA/爱好者项目 |

---

## 5. 工具对比总表

### 5.1 按类别汇总

| 工具 | 类别 | Stars | 最近更新 | Python | CLI | 许可证 |
|------|------|-------|---------|--------|-----|--------|
| **KiCad** | PCB设计 | ~2,600 | 2026-03 | IPC API | Yes | GPL v3 |
| **LibrePCB** | PCB设计 | ~2,800 | 2026-02 | No | Yes | GPL v3 |
| **FreePCB** | PCB设计 | 少量 | 停滞 | No | No | GPL |
| **gEDA** | PCB设计 | - | 停滞 | No | 有限 | GPL v2 |
| **OpenROAD** | 数字IC | ~1,800 | 2026-03 | Yes | Yes | BSD |
| **Yosys** | 综合 | ~4,300 | 2026-03 | Pyosys | Yes | ISC |
| **OpenSTA** | STA | ~555 | 2026 | TCL | Yes | GPL/商业 |
| **Magic** | 版图 | ~620 | 2026-03 | No(Tcl) | Yes | BSD |
| **KLayout** | 版图 | ~1,100 | 2026-03 | Yes | Yes | GPL v2 |
| **ngspice** | 仿真 | - | 2025-09 | PySpice | Yes | BSD |
| **Xyce** | 仿真 | - | 2025-08 | Yes | Yes | GPL v3 |
| **Verilator** | 仿真 | ~3,400 | 2026-03 | cocotb | Yes | LGPL |
| **cocotb** | 验证 | ~2,300 | 2025-11 | 核心 | Yes | BSD |
| **Qucs-S** | RF仿真 | - | 2025-09 | No | 有限 | GPL |
| **OpenLane** | 后端流程 | ~1,700 | 维护 | Yes | Yes | Apache |
| **LibreLane** | 后端流程 | ~326 | 2026 | Yes | Yes | Apache |
| **CIRCT** | 编译器 | ~2,100 | 2026-03 | Yes | Yes | Apache |
| **Chisel** | HDL | - | 2026 | N/A | sbt | Apache |
| **SpinalHDL** | HDL | - | 2026 | N/A | sbt | MIT/LGPL |

### 5.2 API/可编程性评估

对AUTO_EDA项目最关键的维度 - 工具的可编程性和自动化能力:

| 工具 | Python API | CLI | TCL | 脚本能力评级 |
|------|-----------|-----|-----|-------------|
| KiCad | IPC API (新) | v9+ Jobsets | 有 | ★★★★☆ |
| Yosys | Pyosys (pybind11) | 完整 | 核心 | ★★★★★ |
| OpenROAD | Python绑定 | 完整 | 核心 | ★★★★★ |
| KLayout | Python + Ruby | 有 | 无 | ★★★★★ |
| OpenSTA | 有限 | 完整 | 核心 | ★★★★☆ |
| Magic | 无 | 有 | 核心 | ★★★☆☆ |
| ngspice | PySpice外部 | 交互式 | 无 | ★★★☆☆ |
| Xyce | v7.10示例 | 有 | 无 | ★★★☆☆ |
| Verilator | 通过cocotb | 有 | 无 | ★★★★☆ |
| cocotb | 核心Python | pytest | 无 | ★★★★★ |
| CIRCT | Python绑定 | firtool | 无 | ★★★★☆ |
| OpenLane/LibreLane | Python架构 | 有 | 无 | ★★★★★ |

---

## 6. 关键发现与建议

### 6.1 开源EDA生态成熟度

1. **数字IC设计流程已完全开源可行**: OpenROAD + Yosys + OpenSTA + Magic + KLayout + OpenLane/LibreLane + SkyWater/GF PDK 构成完整的RTL-to-GDSII流程,已有600+流片验证。

2. **PCB设计KiCad主导**: KiCad v9/v10功能接近商业级,生态最完整,是唯一值得重点关注的开源PCB工具。

3. **仿真/验证Python化趋势明显**: cocotb + Verilator组合代表了Python驱动硬件验证的主流方向。

4. **编译器基础设施统一**: CIRCT正在成为硬件编译的LLVM,Chisel已完全依赖CIRCT后端。

### 6.2 对AUTO_EDA MCP项目的建议

**优先集成的工具 (具备良好API/CLI):**
1. **KiCad** - IPC API + Jobsets CLI (PCB设计)
2. **Yosys** - Pyosys + TCL CLI (综合)
3. **OpenROAD** - Python/TCL (数字后端)
4. **KLayout** - Python/Ruby脚本 (版图)
5. **cocotb** - 纯Python (验证)
6. **OpenLane/LibreLane** - Python模块化 (自动化流程)

**次优先集成 (CLI为主):**
7. **ngspice** - CLI + PySpice
8. **Verilator** - CLI
9. **OpenSTA** - TCL CLI
10. **Magic** - Tcl CLI

**不建议集成:**
- FreePCB, gEDA (已停滞)
- Qucs-S (无Python API, 受众小)

### 6.3 许可证兼容性

所有主要开源EDA工具使用的许可证 (GPL, BSD, Apache, ISC, LGPL) 均允许集成和二次开发,但需注意:
- GPL工具在分发时需要开源衍生作品
- MCP Server作为工具调用层,一般不构成衍生作品
- BSD/Apache/ISC许可最为宽松

---

*报告结束*
