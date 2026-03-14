# R1: 主流商业EDA设计软件全景调研报告

> 调研日期: 2026-03-14
> 数据时效: 2024-2025年度 (部分2026 Q1数据)

---

## 目录

1. [行业概览与市场格局](#1-行业概览与市场格局)
2. [三大EDA厂商详细分析](#2-三大eda厂商详细分析)
   - 2.1 [Synopsys (新思科技)](#21-synopsys-新思科技)
   - 2.2 [Cadence (楷登电子)](#22-cadence-楷登电子)
   - 2.3 [Siemens EDA (西门子EDA / 原Mentor Graphics)](#23-siemens-eda-西门子eda--原mentor-graphics)
3. [新兴与中型EDA厂商](#3-新兴与中型eda厂商)
   - 3.1 [Ansys (被Synopsys收购)](#31-ansys-被synopsys收购)
   - 3.2 [Altium](#32-altium)
   - 3.3 [Zuken (图研)](#33-zuken-图研)
   - 3.4 [Keysight (是德科技)](#34-keysight-是德科技)
   - 3.5 [Silvaco](#35-silvaco)
   - 3.6 [AI原生EDA初创公司](#36-ai原生eda初创公司)
4. [国产EDA厂商](#4-国产eda厂商)
   - 4.1 [华大九天 (Empyrean)](#41-华大九天-empyrean)
   - 4.2 [概伦电子 (Primarius)](#42-概伦电子-primarius)
   - 4.3 [芯华章 (X-Epic)](#43-芯华章-x-epic)
   - 4.4 [其他国产厂商](#44-其他国产厂商)
5. [自动化能力对比](#5-自动化能力对比)
   - 5.1 [脚本语言支持](#51-脚本语言支持)
   - 5.2 [API/SDK能力](#52-apisdk能力)
   - 5.3 [命令行接口(CLI)](#53-命令行接口cli)
   - 5.4 [自动化能力综合对比表](#54-自动化能力综合对比表)
6. [价格模式分析](#6-价格模式分析)
7. [对AUTO_EDA项目的启示](#7-对auto_eda项目的启示)

---

## 1. 行业概览与市场格局

### 市场规模

| 指标 | 2024年 | 2025年(预估) |
|------|--------|-------------|
| 全球EDA市场规模 | ~$19.2B | ~$20-21B |
| 年增长率(CAGR) | 8-10% | 8-10% |
| 中国EDA市场规模 | ~105-136亿元RMB | ~150-185亿元RMB |

### 市场份额分布 (2024)

| 厂商 | 全球份额 | 年收入 | 核心优势领域 |
|------|---------|--------|-------------|
| **Synopsys** | ~31-46% | $6.13B (FY2024) / $7B+ (FY2025含Ansys) | 数字综合/实现、IP |
| **Cadence** | ~30-35% | $4.64B (2024) / $5.3B (FY2025) | 模拟/定制IC、PCB、硬件仿真 |
| **Siemens EDA** | ~13% | ~$2.2B (~EUR2B FY2025) | 物理验证、PCB企业级 |
| **三巨头合计** | **>85%** | | |
| Altium | ~2-3% | ~$300M+ (被Renesas收购) | PCB中端市场 |
| Keysight EDA | ~2% | (EDA部门) | RF/高速设计-测试一体化 |
| Zuken | ~1-2% | ~$270M (FY2025) | 汽车/企业级E/E |
| Silvaco | <1% | $63.1M (2025) | TCAD、模拟SIP |
| 国产EDA合计 | ~3-5% (中国市场12-15%) | | 模拟全流程、仿真、验证 |

> 注: 不同分析机构(TrendForce、Griffin Securities、VLSIresearch)对市场份额定义和统计口径不同，Synopsys份额在31%-46%之间浮动，取决于是否包含IP/服务收入。

### 增长驱动因素 (2024-2025)

1. **AI芯片复杂度激增**: AI/HPC芯片设计推动高端EDA工具需求
2. **先进制程推进**: 3nm/2nm FinFET/GAA工艺对EDA工具精度要求提升
3. **3D-IC与先进封装**: Chiplet架构推动多物理域联合仿真
4. **云化与AI集成**: EDA工具自身的AI化(DSO.ai, Cerebrus等)
5. **中国国产替代**: 出口管制加速国产EDA研发投入

---

## 2. 三大EDA厂商详细分析

### 2.1 Synopsys (新思科技)

**总部**: 美国加利福尼亚州Mountain View
**2024收入**: $6.13B | **FY2025收入**: ~$7B+ (含Ansys)
**全球市场份额**: ~31-46%
**员工**: ~19,000+

#### 核心产品线

| 产品 | 类别 | 功能描述 | 市场地位 |
|------|------|---------|---------|
| **Design Compiler (DC)** | 逻辑综合 | RTL到门级网表综合，优化时序/功耗/面积 | 综合领域行业标准，>20年历史 |
| **Design Compiler NXT** | 逻辑综合(增强) | 面向<5nm节点的增强综合，与ICC2更好关联 | DC升级版，先进节点首选 |
| **IC Compiler II (ICC2)** | 物理实现 | 布局布线(P&R)、时钟树综合、优化 | 传统P&R标杆工具 |
| **Fusion Compiler** | 统一RTL-to-GDSII | 综合+物理实现统一平台，单一数据模型 | 旗舰产品，500+tapeout(2021)，持续增长 |
| **PrimeTime** | 静态时序分析(STA) | 签核级时序分析 | STA行业金标准 |
| **PrimeSim** | 电路仿真 | SPICE/FastSPICE仿真 | 强竞争力 |
| **StarRC** | 寄生参数提取 | 互连寄生提取 | 签核级标准 |
| **VCS** | 功能仿真 | RTL/门级仿真验证 | 仿真器第一梯队 |
| **Verdi** | 调试平台 | 可视化调试 | 验证调试事实标准 |
| **SpyGlass** | Lint/CDC/RDC | 设计质量检查 | 广泛采用 |
| **VC Formal** | 形式验证 | 属性/等价检查 | 形式验证领先 |
| **DSO.ai** | AI优化 | ML驱动的设计空间探索 | EDA AI先驱 |
| **3DIC Compiler** | 3D-IC设计 | 多芯片集成设计 | 先进封装领先 |
| **DesignWare IP** | IP核库 | 接口IP、处理器IP、安全IP | 全球#1 IP供应商 |

#### 产品演进 (2024-2025)

- **Fusion Compiler** 成为旗舰，逐步替代DC+ICC2分离流程
- **DSO.ai** AI优化引擎深度集成到各工具中，~20%收入提升
- **FlexEDA** 云按分钟计费模式，突破传统授权限制
- 收购Ansys(2025.07完成)，扩展多物理域仿真能力

#### 定价模式

- **传统模式**: 多年期订阅/Seat License，高度定制化谈判
- **企业级**: 大客户"全包"协议，年费$M级别(如Intel曾签>$1B合约)
- **FlexEDA云模式**: 按分钟/小时计费，无限License，灵活扩展
- **无公开标价**: 所有价格需直接联系销售

---

### 2.2 Cadence (楷登电子)

**总部**: 美国加利福尼亚州San Jose
**2024收入**: $4.64B | **FY2025收入**: $5.297B (+14% YoY)
**全球市场份额**: ~30-35%
**核心EDA增长**: FY2025 Core EDA +13%
**积压订单**: $7.8B (创纪录)

#### 核心产品线

| 产品 | 类别 | 功能描述 | 市场地位 |
|------|------|---------|---------|
| **Virtuoso Studio** | 模拟/定制IC设计 | 全定制模拟/RF/混合信号/光子IC设计平台 | 模拟IC设计行业标准(30+年) |
| **Virtuoso Layout Suite** | 版图设计 | 自动化版图(XL/EXL/MXL)、生成式AI版图 | 定制IC版图标杆 |
| **Allegro X** | PCB设计平台 | 企业级多板/高速PCB设计与分析 | 高端PCB设计领先 |
| **Allegro X AI** | AI驱动PCB | 生成式自动布局/布线/铺铜 | PCB AI创新引领 |
| **Innovus** | 数字实现 | 布局布线(GigaPlace/NanoRoute)、优化 | 数字P&R强竞争力 |
| **Innovus+** | 综合+实现 | 集成综合的统一数字实现 | 对标Fusion Compiler |
| **Genus** | 逻辑综合 | RTL综合 | 综合第二梯队 |
| **Tempus** | 静态时序分析 | 签核级STA | 挑战PrimeTime |
| **Voltus** | 功耗分析 | IR-drop、功耗签核 | 功耗分析强竞争力 |
| **Quantus** | 寄生提取 | 互连寄生提取 | 与StarRC竞争 |
| **Pegasus** | 物理验证 | DRC/LVS | 挑战Calibre |
| **Xcelium** | 功能仿真 | 多核并行仿真 | 仿真器第一梯队 |
| **JasperGold** | 形式验证 | 属性验证 | 形式验证领先之一 |
| **Palladium Z2/Z3** | 硬件仿真 | 大规模硬件仿真加速 | 硬件仿真市场领先 |
| **Protium X2/X3** | FPGA原型验证 | 快速原型验证 | 原型验证领先 |
| **Cerebrus** | AI优化 | ML驱动自动化调优 | AI EDA战略核心 |
| **Sigrity X** | 信号/电源完整性 | SI/PI/热分析 | SI/PI分析领先 |
| **Celsius** | 热仿真 | 系统级热分析 | 热管理扩展 |

#### 产品演进 (2024-2025)

- **Virtuoso Studio**: 生成式AI版图自动化(MXL)，支持光子IC/3D-IC异构集成
- **Allegro X AI**: 生成式自动布局/布线，将"天"级任务缩短至"分钟"级
- **Innovus+**: 集成综合能力，对标Fusion Compiler统一流程
- **Cadence.AI平台**: Cerebrus、InsightAI、ChipStack AI Super Agent
- **IC 25.1版本**: 2025年全线更新，AI增强各工具

#### 定价模式

- **IC设计套件**: $150,000-$300,000+/seat/年 (估计，高度定制谈判)
- **Allegro X PCB**: ~$4,000/年租赁(基础) 至 ~$12,000永久授权(基础)，企业级更高
- **OrCAD**: 入门级产品，价格较低
- **授权方式**: 时间制(1-3年)、批量折扣、捆绑套餐
- **学术版**: 显著折扣

---

### 2.3 Siemens EDA (西门子EDA / 原Mentor Graphics)

**母公司**: Siemens Digital Industries Software (2017年收购Mentor Graphics)
**FY2025 EDA收入**: ~EUR2B (~$2.2B)，占DI Software ~1/3
**全球市场份额**: ~13%
**增长**: FY2025 +3% YoY (增速放缓)

#### 核心产品线

| 产品 | 类别 | 功能描述 | 市场地位 |
|------|------|---------|---------|
| **Calibre** | 物理验证 | DRC/LVS/OPC签核验证 | **行业金标准，>90%半导体公司使用** |
| **Calibre nmDRC** | 设计规则检查 | 纳米级DRC | 物理验证绝对领导者 |
| **Calibre nmLVS** | 版图vs原理图 | 电气一致性检查 | 签核LVS标准 |
| **Calibre OPC** | 光学邻近校正 | 掩模制造优化 | OPC市场领先 |
| **Xpedition** | 企业级PCB设计 | 高复杂度多板系统设计 | 汽车/航空/国防企业级领先 |
| **Xpedition Standard** | PCB设计(标准版) | 2025年推出，降低门槛 | 扩展中端市场 |
| **PADS** | PCB设计(入门) | 中小规模PCB设计 | 中端PCB市场 |
| **HyperLynx** | 信号/电源完整性 | SI/PI/EMI/EMC分析 | SI/PI分析领先工具之一 |
| **Questa** | 功能验证 | 仿真/形式/CDC验证 | 验证第一梯队 |
| **ModelSim** | HDL仿真 | Verilog/VHDL仿真 | 入门级仿真标准 |
| **Veloce** | 硬件仿真 | 硬件仿真加速器 | 硬件仿真主要选手 |
| **Catapult** | HLS高层次综合 | C/C++/SystemC到RTL | HLS市场强竞争力 |
| **Tessent** | DFT/测试 | 可测试性设计、BIST | DFT市场领先 |

#### 产品特色

- **Calibre**: 物理验证(DRC/LVS)领域近乎垄断地位
  - >90%半导体设计公司签核采用
  - 中国市场份额>70%
  - 物理验证子市场(~$3-5B)中明确领导者
  - 各大Foundry认证(TSMC/Samsung/Intel)
  - 2025年新增Vision AI、3D-IC支持

- **Xpedition**: 汽车/航空/国防等高可靠性领域首选
  - 支持超复杂多板系统设计
  - ECAD-MCAD协同
  - 2025年推出Standard版扩展市场

- **Tessent**: DFT(可测试性设计)领域领先
  - 芯片制造测试必备
  - 与Calibre形成"制造侧"完整方案

---

## 3. 新兴与中型EDA厂商

### 3.1 Ansys (被Synopsys收购)

**收购状态**: Synopsys于2025年7月17日完成收购($35B)
**现为Synopsys全资子公司**

#### 核心半导体产品(收购后持续运营)

| 产品 | 类别 | 功能描述 |
|------|------|---------|
| **HFSS** | 3D电磁场仿真 | 高频结构仿真(天线/封装/互连EM分析) |
| **HFSS-IC** | IC级EM仿真 | 芯片级电磁提取(2024 R2推出) |
| **HFSS-PI** | 电源完整性 | 宽带3D PDN分析(2026 R1新增) |
| **RedHawk-SC** | 功耗完整性签核 | 全芯片IR-drop/电迁移/动态电压降 |
| **RedHawk-SC Electrothermal** | 3D-IC热-电联合 | 多芯片封装热-应力-电联合分析 |
| **Totem-SC** | 模拟功耗分析 | 模拟/混合信号电路功耗 |
| **PathFinder-SC** | ESD分析 | 静电放电保护验证 |

**关键影响**:
- RedHawk-SC: 门级功耗完整性签核**行业金标准**，市占率55-60%
- HFSS: EM仿真市占率45-50%
- 收购后与Synopsys 3DIC Compiler/Fusion Compiler深度集成
- 2026 R1: 多物理域联合签核流程成熟

---

### 3.2 Altium

**状态**: 2024年8月被Renesas(瑞萨电子)以~$5.9B收购

| 产品 | 描述 |
|------|------|
| **Altium Designer** | 桌面级PCB设计工具，以易用性著称 |
| **Altium 365** | 云协作平台(版本管理/供应链集成) |
| **CircuitMaker** | 社区版免费PCB设计工具 |

**市场定位**: PCB设计中端市场领导者，面向中小企业和初创公司
**全球PCB软件市场份额**: ~20-25%

---

### 3.3 Zuken (图研)

**总部**: 日本横滨 | **FY2025收入**: 约$270M (JPY40.7B)

| 产品 | 描述 |
|------|------|
| **CR-8000** | 原生3D多板系统级PCB/IC封装设计平台，AI驱动 |
| **E3.series** | 电气/流体工程设计(线束/机柜/控制系统) |

**市场定位**: 汽车/工业/航空企业级E/E(电气/电子)系统设计

---

### 3.4 Keysight (是德科技)

**EDA定位**: RF/高速数字设计-测试一体化

| 产品 | 描述 |
|------|------|
| **ADS (Advanced Design System)** | RF/微波/高速数字设计行业标准 |
| **PathWave Design** | 统一设计软件套件 |
| **SystemVue** | 系统级仿真(5G/雷达) |

**市场定位**: RF/微波EDA领域#1，设计-测量闭环独特优势
**2025年新增**: PowerArtist (从Synopsys收购，RTL功耗分析)

---

### 3.5 Silvaco

**2025收入**: $63.1M (+6% YoY) | **EDA部分+60%增长**

| 产品 | 描述 |
|------|------|
| **Victory TCAD** | 器件/工艺级物理仿真(AI/ML增强) |
| **SmartSpice** | SPICE电路仿真器 |
| **SIP (Silicon IP)** | 安全认证IP核 |

**市场定位**: TCAD物理仿真细分市场领先

---

### 3.6 AI原生EDA初创公司 (2024-2025)

| 公司 | 方向 | 状态 |
|------|------|------|
| **Quilter** | AI自动PCB布局布线 | 融资中，产品早期 |
| **PrimisAI** | AI驱动RTL生成 | 种子轮 |
| **Alpha Design** | AI辅助芯片设计 | 初创 |
| **Silimate** | AI设计空间探索 | 融资中 |
| **Rise Design Automation** | AI优化P&R | 初创 |
| **Suitera** | AI验证加速 | 初创 |

> 以上初创公司商业收入<1%，但代表EDA AI化趋势方向。

---

## 4. 国产EDA厂商

### 国产EDA市场概览

| 指标 | 2024年 | 2025年(预估) |
|------|--------|-------------|
| 中国EDA市场规模 | ~105-136亿元RMB | ~150-185亿元RMB |
| 国产化率 | 12-15% | 19-23% |
| 三巨头在中国份额 | 68-80% | 60-75% (逐步下降) |

### 4.1 华大九天 (Empyrean)

**上市**: 深交所(301269) | **2024营收**: 12.22亿元 (EDA占89%)
**市场份额**: 中国市场6-9%，国产EDA龙头(国产>50%)
**客户**: 700+家，含海思、京东方等

#### 产品线(国产最全)

| 产品系列 | 类别 | 描述 |
|----------|------|------|
| **Aether系列** | 模拟/全定制IC全流程 | 原理图/版图/仿真(ALPS)/验证(Argus)，支持4-5nm |
| **FPD EDA** | 平板显示设计 | 全流程FPD IC设计，全球领先(国内90%+覆盖) |
| **数字SoC工具** | 数字前后端 | HimaSim仿真、HimaTime时序分析，覆盖率~80% |
| **存储/射频EDA** | 专项流程 | Flash/DRAM量产方案(2025年国内唯一) |
| **晶圆制造EDA** | 制造工艺 | 器件建模、掩模数据处理 |

**核心优势**: 唯一国产模拟IC全流程覆盖，2025年并购芯和半导体补齐系统级能力

---

### 4.2 概伦电子 (Primarius)

**上市**: 科创板(688206) | **2024营收**: 4.19亿元
**市场份额**: 中国市场~3-4%，制造类EDA领先

#### 产品线

| 产品 | 类别 | 描述 |
|------|------|------|
| **NanoSpice** | 电路仿真 | 高精度SPICE仿真(全球唯三通过三星3nm认证) |
| **器件建模工具** | SPICE模型/PDK | 全流程器件建模 |
| **标准单元库** | 库开发 | 数字标准单元库 |
| **WAT测试系统** | 半导体测试 | 晶圆验收测试 |

**核心优势**: NanoSpice仿真精度/速度国际领先；2025年6项并购构建"EDA+IP"生态

---

### 4.3 芯华章 (X-Epic)

**状态**: 私营(估值~70亿元) | 专注数字验证

#### 产品线

| 产品 | 类别 | 描述 |
|------|------|------|
| **GalaxSim** | 逻辑仿真器 | 数字逻辑仿真 |
| **GalaxFV** | 形式验证 | 属性/等价验证 |
| **HuaPro** | 硬件仿真 | 双模硬件仿真(支持数十亿门) |
| **FPGA原型** | 原型验证 | FPGA原型验证系统 |
| **VLAB** | 云验证平台 | 云原生验证 |

**核心优势**: 专注验证细分(芯片设计成本60-70%在验证)，全栈国产适配

---

### 4.4 其他国产厂商

| 厂商 | 聚焦领域 |
|------|---------|
| **芯和半导体 (Xpeedic)** | 高速仿真/EDA(2025被华大收购) |
| **国微思尔芯 (S2C)** | FPGA原型验证 |
| **合见工软 (UniVista)** | 数字前端EDA |
| **奥卡思微 (Arcas)** | 数字后端EDA |
| **行芯科技 (Xingxin)** | 时序/功耗签核 |
| **鸿芯微纳 (Hongxin)** | 布局布线 |

---

## 5. 自动化能力对比

### 5.1 脚本语言支持

#### TCL (Tool Command Language) - EDA通用标准

TCL是EDA工具的**事实标准嵌入式脚本语言**，几乎所有主流工具都以TCL作为主要命令接口:

- **Synopsys**: 所有数字工具(DC/PT/ICC2/Fusion Compiler)原生TCL驱动
- **Cadence**: 数字工具(Innovus/Genus/Tempus)使用TCL
- **Siemens EDA**: Calibre/Questa/Xpedition核心使用TCL
- **特点**: 每个GUI操作都记录为TCL命令，可回放自动化

#### SKILL - Cadence专有语言

- **来源**: Cadence专有，基于Lisp的扩展语言
- **适用**: Virtuoso(模拟/定制IC)、Allegro PCB
- **能力**: ~5000+内置函数，深度访问设计数据库(CDB/OpenAccess)
- **用途**: PCells参数化单元、版图自动化、自定义检查、UI扩展
- **版本**: SKILL (经典) / SKILL++ (面向对象增强)

#### Python - 快速增长的新力量

| 厂商 | Python支持状态 |
|------|---------------|
| **Synopsys** | PrimeTime `py_eval`命令 + `snps`模块，可TCL/Python混合编程 |
| **Cadence** | Sigrity原生Python; Virtuoso通过SkillBridge(开源)桥接Python调用SKILL |
| **Siemens** | L-Edit原生Python; Calibre/Questa部分支持 |
| **Keysight** | ADS/PathWave强Python API/SDK |
| **趋势** | Python用于ML/数据分析/跨工具编排，TCL保持工具内部命令核心地位 |

---

### 5.2 API/SDK能力

| 厂商 | API暴露方式 | SDK形态 | 外部集成 |
|------|-----------|--------|---------|
| **Synopsys** | TCL命令集 + Python模块 | 内嵌脚本环境 | C++包装器可用 |
| **Cadence** | SKILL API(Virtuoso) + TCL(数字) | SKILL IDE + SkillBridge | OpenAccess数据库接口 |
| **Siemens** | TCL接口 + C++ UPI宏 | TCL/Python绑定 | Calibre SVRF/TVF |
| **Keysight** | 原生Python API/SDK | 完整Python SDK | REST API(部分工具) |
| **国产** | 各自私有接口 | 有限SDK | 逐步开放中 |

---

### 5.3 命令行接口(CLI)

所有主流EDA工具都支持**无GUI批处理模式**:

| 工具 | CLI入口 | 批处理示例 |
|------|--------|-----------|
| Design Compiler | `dc_shell` | `dc_shell -f script.tcl` |
| PrimeTime | `pt_shell` | `pt_shell -file run.tcl` |
| Fusion Compiler | `fc_shell` | `fc_shell -f flow.tcl` |
| Innovus | `innovus` | `innovus -no_gui -files run.tcl` |
| Genus | `genus` | `genus -files synth.tcl` |
| Virtuoso | `virtuoso` | `virtuoso -nograph -replay script.il` |
| Calibre | `calibre` | `calibre -drc rulefile` |
| Questa | `vsim` | `vsim -batch -do sim.do` |
| VCS | `vcs` | `vcs -f filelist.f && ./simv` |
| Xcelium | `xrun` | `xrun -f filelist.f` |

**CLI自动化要点**:
- 支持HPC集群/云端Farm批量提交
- 支持CI/CD流水线集成
- 支持回归测试自动化
- 日志输出可解析用于自动化判断

---

### 5.4 自动化能力综合对比表

| 能力维度 | Synopsys | Cadence | Siemens EDA | Keysight | 国产EDA |
|---------|----------|---------|-------------|----------|--------|
| **TCL支持** | 原生全线 | 数字工具全线 | 全线 | 部分 | 部分 |
| **Python支持** | py_eval + snps | SkillBridge桥接 | 部分原生 | 原生SDK | 有限 |
| **SKILL** | 不支持 | Virtuoso/Allegro | 不支持 | 不支持 | 不支持 |
| **CLI/批处理** | 全线支持 | 全线支持 | 全线支持 | 支持 | 部分支持 |
| **AI/ML集成** | DSO.ai | Cerebrus | Vision AI | 有限 | 起步阶段 |
| **云原生** | FlexEDA | Cadence Cloud | 部分 | PathWave Cloud | 有限 |
| **API成熟度** | 高 | 高 | 高 | 中高 | 中低 |
| **第三方集成** | 广泛 | 广泛 | 广泛 | 中等 | 有限 |

---

## 6. 价格模式分析

### 定价模式概览

| 模式 | 描述 | 代表 |
|------|------|------|
| **时间订阅制** | 1-3年期License，按Seat/Core计费 | 三巨头主流模式 |
| **永久授权** | 一次性购买+年维护费 | 逐渐减少 |
| **企业全包协议** | 年度全工具访问，$M级别 | 大客户 |
| **按使用量付费** | 按分钟/小时计费，弹性扩展 | Synopsys FlexEDA |
| **学术/教育** | 大幅折扣或免费 | 所有厂商 |

### 典型价格范围(估计)

| 产品类别 | 年费估计(per seat) | 备注 |
|---------|-------------------|------|
| IC全流程套件(Synopsys/Cadence) | $150,000 - $300,000+ | 含综合+P&R+签核 |
| 物理验证(Calibre) | $50,000 - $100,000+ | 按工艺节点/功能模块 |
| PCB设计(高端Allegro/Xpedition) | $10,000 - $50,000+ | 企业级完整套件 |
| PCB设计(中端Altium) | $3,000 - $10,000 | 年订阅 |
| 仿真器(VCS/Xcelium) | $50,000 - $150,000 | 含调试器 |
| 硬件仿真(Palladium/Veloce) | $1M+ | 硬件+软件 |
| FPGA原型验证 | $100,000 - $500,000 | 含FPGA板卡 |

> 注: 以上均为行业讨论/论坛中的估计值，实际价格因客户规模、工艺节点、模块选择差异极大，均需直接联系厂商获取报价。

---

## 7. 对AUTO_EDA项目的启示

### 7.1 可切入的自动化空间

基于以上调研，AUTO_EDA项目可关注以下方向:

1. **TCL/Python脚本自动生成与管理**
   - 所有工具都支持TCL脚本，可构建跨工具的脚本生成框架
   - Python桥接能力正在增强，可作为统一编排层

2. **CLI批处理流程编排**
   - 利用各工具的CLI接口，构建端到端自动化流水线
   - 日志解析与自动化决策

3. **跨工具数据流管理**
   - 不同工具间的数据格式转换与流转
   - OpenAccess/LEF/DEF等标准格式的处理

4. **AI辅助设计决策**
   - 参数空间探索自动化
   - 设计质量预测与优化建议

### 7.2 技术路线建议

- **脚本层**: 以Python为统一外层，TCL/SKILL作为工具内部接口
- **接口层**: 利用CLI/批处理模式实现工具控制
- **数据层**: 基于标准格式(OpenAccess/GDSII/LEF/DEF)实现互操作
- **智能层**: LLM辅助脚本生成、错误诊断、设计建议

### 7.3 竞争格局观察

- 三巨头(Synopsys/Cadence/Siemens)已在内部集成AI(DSO.ai/Cerebrus)
- 但**跨工具、跨厂商的统一自动化**仍是空白
- 国产EDA生态碎片化，统一自动化需求强烈
- AI初创公司聚焦单点优化，缺乏全流程整合

---

## 数据来源

- Griffin Securities (DAC 2024) / Embedded.com (2025.06)
- TrendForce EDA Market Reports (2024-2025)
- MatrixBCG Synopsys Competitor Analysis (2025.12)
- Cadence Investor Relations FY2025 Financial Results (2026.02)
- Synopsys Ansys 2026 R1 Press Release (2026.03.11)
- Siemens Digital Industries FY2025 Reports
- 赛迪智库 / 中原证券 / 东方证券研报 (2024-2025)
- 华大九天/概伦电子 年报及半年报 (2024-2025)
- 各厂商官方产品页面及技术博客
- Reddit r/chipdesign、SemiWiki等行业社区讨论

---

*本报告为AUTO_EDA项目Phase 1调研输出，数据截止2026年3月。*
