# DA7: EDA领域知识体系构建

> 分析师: EDA领域专家 (DA7)
> 分析日期: 2026-03-14
> 数据来源: R6_ai_eda_trends.md, R7_eda_file_formats.md, A1_technical_feasibility.md
> 输出版本: v1.0

---

## 目录

1. [EDA核心知识图谱](#1-eda核心知识图谱)
2. [Claude EDA理解能力评估](#2-claude-eda理解能力评估)
3. [EDA System Prompt工程](#3-eda-system-prompt工程)
4. [错误诊断知识库设计](#4-错误诊断知识库设计)
5. [EDA决策规则库](#5-eda决策规则库)
6. [领域知识飞轮实现方案](#6-领域知识飞轮实现方案)

---

## 1. EDA核心知识图谱

### 1.1 PCB设计知识体系

```
PCB设计知识树
│
├── 原理图设计
│   ├── 元件符号库管理
│   │   ├── KiCad Symbol格式 (.kicad_sym)
│   │   ├── 引脚定义 (输入/输出/双向/电源/开集)
│   │   └── 元件属性 (值/封装关联/数据手册URL)
│   ├── 层次化设计
│   │   ├── 层次图纸 (hierarchical sheets)
│   │   ├── 总线与网络标签
│   │   └── 全局标签 (PWR_FLAG, GND)
│   └── 电气规则检查 (ERC)
│       ├── 引脚类型冲突检测
│       ├── 未连接引脚警告
│       └── 电源网络完整性
│
├── 封装库 (Footprint)
│   ├── SMD封装 (0402/0603/0805/SOT-23/QFP/BGA)
│   ├── THT封装 (DIP/TO-220/连接器)
│   ├── 焊盘定义 (铜层/阻焊/丝印/钢网)
│   ├── 3D模型关联 (.step/.wrl)
│   └── 封装规则 (IPC-7351标准)
│
├── PCB布局 (Layout)
│   ├── 高速信号布局原则
│   │   ├── 差分对等长匹配 (±5mil)
│   │   ├── 去耦电容靠近IC电源引脚
│   │   ├── 晶振远离高速信号线
│   │   └── DDR/PCIe等长分组
│   ├── 电源布局
│   │   ├── 电源平面分割
│   │   ├── 滤波电容放置策略
│   │   └── 热插拔保护电路位置
│   ├── 散热布局
│   │   ├── 发热器件间距 (>5mm)
│   │   ├── 散热焊盘 (thermal pad) 连接
│   │   └── 过孔散热阵列设计
│   └── 可制造性 (DFM)
│       ├── 最小元件间距 (0402间距>0.2mm)
│       ├── 拼板设计规则
│       └── 测试点放置
│
├── PCB布线 (Routing)
│   ├── 信号完整性规则
│   │   ├── 阻抗控制 (微带线/带状线)
│   │   ├── 蛇形走线等长
│   │   └── 避免锐角和直角
│   ├── EMC规则
│   │   ├── 回流路径最小化
│   │   ├── 地平面完整性
│   │   ├── 敏感信号包地
│   │   └── 跨分割平面禁止
│   ├── 电源布线
│   │   ├── 宽度计算 (IPC-2152: W=I/k/ΔT^0.44/厚度^0.725)
│   │   └── 多过孔并联降阻抗
│   └── DRC规则
│       ├── 最小线宽 (通常4mil)
│       ├── 最小间距 (通常4mil)
│       ├── 最小过孔尺寸 (0.3mm钻孔/0.6mm焊盘)
│       └── 孔环 (annular ring ≥0.15mm)
│
├── EMC设计知识
│   ├── 辐射发射控制
│   │   ├── 时钟频率及谐波抑制
│   │   ├── 屏蔽罩设计
│   │   └── 共模滤波器放置
│   ├── 传导发射控制
│   │   ├── EMI滤波器设计
│   │   └── 输入电源滤波
│   └── ESD/EFT防护
│       ├── TVS/Zener选型
│       └── 防护器件靠近接口
│
└── 制造输出
    ├── Gerber文件 (RS-274X)
    ├── 钻孔文件 (Excellon)
    ├── BOM (Bill of Materials)
    ├── 装配图 (Assembly Drawing)
    └── ODB++/IPC-2581 (高级格式)
```

**知识节点依赖关系:**
```
元件库 → 原理图 → ERC → PCB布局 → 布线 → DRC → 制造输出
    ↑                              ↑
封装库 ─────────────────────────────┘
    ↑
EMC规则 (贯穿布局和布线)
```

---

### 1.2 数字IC设计知识体系 (RTL→综合→P&R→时序→DRC/LVS)

```
数字IC设计流程知识树
│
├── RTL设计 (Register Transfer Level)
│   ├── Verilog/SystemVerilog语法
│   │   ├── 模块定义 (module/endmodule)
│   │   ├── 时序逻辑 (always @posedge clk)
│   │   ├── 组合逻辑 (always @(*))
│   │   ├── 参数化设计 (parameter/localparam)
│   │   └── 接口 (interface/modport)
│   ├── 可综合RTL规范
│   │   ├── 避免initial块(非可综合)
│   │   ├── 时钟域明确(无门控时钟)
│   │   ├── 复位策略(同步/异步)
│   │   └── 状态机编码(Binary/One-Hot/Gray)
│   └── VHDL知识体系
│       ├── entity/architecture结构
│       ├── process/signal/variable
│       └── 类型系统(强类型)
│
├── 逻辑综合 (Logic Synthesis)
│   ├── 综合工具
│   │   ├── Yosys (开源: synth命令族)
│   │   ├── Synopsys Design Compiler (dc_shell)
│   │   └── Cadence Genus
│   ├── 综合约束 (SDC格式)
│   │   ├── create_clock (时钟定义)
│   │   ├── set_input_delay / set_output_delay
│   │   ├── set_false_path / set_multicycle_path
│   │   └── set_max_fanout / set_max_transition
│   ├── 综合流程
│   │   ├── RTL解析 → 通用逻辑网表 → 工艺映射
│   │   ├── 优化Pass: 面积/时序/功耗
│   │   └── Liberty库 (.lib) 映射标准单元
│   └── 网表格式
│       ├── 门级Verilog (.v)
│       ├── BLIF/EDIF
│       └── JSON (Yosys内部格式)
│
├── 物理设计 (Place & Route)
│   ├── 布局规划 (Floorplanning)
│   │   ├── 芯片面积估算
│   │   ├── 宏单元 (Macro) 放置
│   │   ├── IO引脚分配
│   │   └── 电源规划 (Power Planning)
│   ├── 放置 (Placement)
│   │   ├── 全局放置 (Global Placement)
│   │   ├── 合法化 (Legalization)
│   │   └── 详细放置 (Detailed Placement)
│   ├── 时钟树综合 (CTS)
│   │   ├── H-Tree结构
│   │   ├── 时钟偏斜控制 (Skew <100ps)
│   │   └── 时钟缓冲器插入
│   ├── 全局布线 (Global Routing)
│   │   ├── 拥塞分析
│   │   └── 资源分配
│   ├── 详细布线 (Detailed Routing)
│   │   ├── 层分配
│   │   ├── 轨道分配
│   │   └── DRC清洁布线
│   └── 文件格式
│       ├── LEF (工艺/库定义)
│       ├── DEF (设计实例数据)
│       ├── SPEF (寄生参数提取)
│       └── GDSII/OASIS (最终版图)
│
├── 时序分析 (Timing Analysis)
│   ├── 静态时序分析 (STA)
│   │   ├── 建立时间 (Setup Time) 分析
│   │   ├── 保持时间 (Hold Time) 分析
│   │   ├── 关键路径识别
│   │   └── 时序裕量 (Slack = Required - Arrival)
│   ├── 时序约束 (SDC)
│   │   ├── 时钟不确定性 (set_clock_uncertainty)
│   │   ├── 输入/输出延迟
│   │   └── 例外路径 (false path/multicycle)
│   ├── 时序报告解读
│   │   ├── report_timing (关键路径报告)
│   │   ├── report_constraint (约束违规)
│   │   └── WNS/TNS/FEP指标
│   └── 工具: OpenSTA, Synopsys PrimeTime
│
└── 物理验证 (DRC/LVS)
    ├── 设计规则检查 (DRC)
    │   ├── 间距规则 (Spacing)
    │   ├── 宽度规则 (Width)
    │   ├── 封闭规则 (Enclosure)
    │   ├── 面积规则 (Minimum Area)
    │   └── 工具: KLayout, Cadence Assura, Synopsys Hercules
    ├── 版图vs原理图 (LVS)
    │   ├── 器件匹配
    │   ├──    │   ├── 连接性检查
    │   └── 工具: KLayout LVS, Calibre
    └── 电学规则检查 (ERC)
        ├── 浮空输入节点
        ├── 驱动强度不足
        └── 天线规则违规
```

**知识节点依赖关系 (数字IC):**
```
RTL → [Lint检查] → 综合 → 门级仿真 → 布局规划 → 放置 → CTS → 布线 → STA → DRC/LVS → GDSII
           ↑              ↑                                              ↑
        CDC检查         功能仿真                                      寄生提取(SPEF)
           ↑
        形式验证 (Formality)
```

---

### 1.3 模拟电路仿真知识体系

```
模拟仿真知识树
│
├── SPICE网表
│   ├── 基本元件语法
│   │   ├── R (电阻): R1 n1 n2 10k
│   │   ├── C (电容): C1 n1 n2 100n
│   │   ├── L (电感): L1 n1 n2 1u
│   │   ├── V/I (电源): V1 n1 0 DC 5 AC 1
│   │   ├── D/Q/M (二极管/BJT/MOSFET)
│   │   └── X (子电路调用)
│   ├── 子电路定义 (.subckt/.ends)
│   └── 模型文件 (.model, BSIM/EKV)
│
├── 直流分析 (DC Analysis)
│   ├── .op (工作点分析)
│   │   ├── 确定偏置点
│   │   └── 线性化小信号参数
│   ├── .dc (DC扫描)
│   │   ├── 转移特性曲线
│   │   └── 温度扫描 (.TEMP)
│   └── 收敛技巧
│       ├── .nodeset (初始节点电压)
│       ├── .ic (初始条件)
│       └── GMIN步进法
│
├── 交流分析 (AC Analysis)
│   ├── .ac 频率扫描 (线性/对数)
│   ├── 波特图: 增益(dB)和相位(°)vs频率
│   ├── 关键指标
│   │   ├── 单位增益带宽 (GBW)
│   │   ├── 相位裕度 (>45°)
│   │   ├── 增益裕度 (>6dB)
│   │   └── 极点/零点频率
│   └── 噪声分析 (.noise)
│       ├── 热噪声/散粒噪声/闪烁噪声
│       └── 输入参考噪声 (V/√Hz)
│
├── 瞬态分析 (Transient Analysis)
│   ├── .tran 时间步长与终止时间
│   ├── 时间步长自适应控制
│   │   ├── RELTOL (默认0.001)
│   │   ├── ABSTOL (默认1pA)
│   │   └── VNTOL (默认1μV)
│   ├── 混合信号仿真 (数字激励+模拟电路)
│   └── 收敛失败处理
│       ├── 减小TSTEP
│       ├── 增大ITL4 (迭代次数)
│       └── 分段仿真
│
└── 蒙特卡洛/工艺角分析
    ├── .mc (蒙特卡洛统计仿真)
    ├── .corners (工艺角: TT/FF/SS/SF/FS)
    └── Mismatch分析 (器件失配)
```

---

### 1.4 验证知识体系

```
验证知识树
│
├── 功能验证
│   ├── 仿真验证
│   │   ├── Verilog Testbench结构
│   │   │   ├── 激励生成 (initial块)
│   │   │   ├── 响应检查 ($monitor/$display)
│   │   │   └── 自动比较 ($finish)
│   │   ├── cocotb (Python协程仿真)
│   │   │   ├── @cocotb.test() 装饰器
│   │   │   ├── await Timer(10, units='ns')
│   │   │   └── assert dut.output.value == expected
│   │   └── SystemVerilog断言 (SVA)
│   │       ├── assert property (@posedge clk)
│   │       ├── assume/cover
│   │       └── 序列 (sequence)
│   ├── 覆盖率驱动验证 (CDV)
│   │   ├── 代码覆盖率 (行/分支/条件/翻转)
│   │   ├── 功能覆盖率 (covergroup/coverpoint)
│   │   └── 覆盖率收敛标准 (通常95%+)
│   └── 约束随机验证 (CRV)
│       ├── randomize() with {约束}
│       └── 权重随机分布
│
├── 形式验证
│   ├── 等价性检查 (EC)
│   │   ├── RTL vs 门级网表
│   │   └── 工具: Synopsys Formality, Cadence Conformal
│   ├── 属性验证 (Property Checking)
│   │   ├── BMC (有界模型检验)
│   │   ├── k-归纳
│   │   └── 工具: JasperGold, SymbiFlow-SymbiYosys
│   └── CDC/RDC形式检查
│       ├── 异步跨时钟域检查
│       └── 复位域一致性
│
└── 时序验证 (STA)
    ├── 多角时序 (Multi-corner Multi-mode)
    │   ├── 最差情况慢角 (SS + 低温 + 低电压)
    │   └── 最佳情况快角 (FF + 高温 + 高电压)
    ├── 串扰时序 (SI-aware STA)
    │   ├── 耦合噪声对延迟的影响
    │   └── 噪声裕量分析
    └── 签收 (Signoff)
        ├── 物理验证DRC/LVS通过
        ├── 多角STA时序收敛
        └── 功耗签收 (Power Signoff)
```

---

### 1.5 跨域知识节点依赖图

```
┌─────────────────────────────────────────────────────────────┐
│                    EDA知识依赖关系全图                        │
├───────────┬─────────────┬──────────────┬───────────────────┤
│  PCB域    │  数字IC域   │   模拟仿真域  │    验证域          │
├───────────┼─────────────┼──────────────┼───────────────────┤
│ 原理图    │ RTL设计     │ SPICE网表    │ Testbench开发     │
│    ↓      │    ↓        │    ↓         │    ↓              │
│ ERC检查   │ 综合约束    │ DC分析       │ 功能覆盖率         │
│    ↓      │    ↓        │    ↓         │    ↓              │
│ 封装设计  │ 综合流程    │ AC分析       │ 形式验证           │
│    ↓      │    ↓        │    ↓         │    ↓              │
│ 布局规则  │ P&R流程     │ 瞬态分析     │ 时序签收           │
│    ↓      │    ↓        │    ↓         │                   │
│ 布线规则  │ 时序分析    │ 工艺角分析   │                   │
│    ↓      │    ↓        │              │                   │
│ 制造输出  │ DRC/LVS     │              │                   │
├───────────┴─────────────┴──────────────┴───────────────────┤
│            共享底层知识                                       │
│  • 文件格式 (Gerber/GDSII/LEF/DEF/Liberty/SPICE)            │
│  • 电气基础 (阻抗/延迟/功耗/信号完整性)                       │
│  • 工艺知识 (PDK/工艺节点/制造限制)                           │
│  • EDA工具链 (Yosys/OpenROAD/KiCad/ngspice)                 │
└─────────────────────────────────────────────────────────────┘
```


---

## 2. Claude EDA理解能力评估

### 2.1 Claude对Verilog/VHDL的理解深度

**强项 (置信度高):**

| 能力领域 | 评估 | 说明 |
|----------|------|------|
| Verilog基础语法 | ★★★★★ | module/always/assign/if/case等标准结构 |
| SystemVerilog语法扩展 | ★★★★☆ | interface/typedef/enum/logic类型 |
| RTL设计模式 | ★★★★☆ | FSM/FIFO/流水线/仲裁器等常用模式 |
| VHDL基础语法 | ★★★★☆ | entity/architecture/process结构 |
| 可综合RTL判断 | ★★★★☆ | 识别非可综合结构 |
| Testbench编写 | ★★★★☆ | 基础testbench, $monitor/$display |
| SDC约束语法 | ★★★★☆ | create_clock/set_input_delay等标准约束 |
| cocotb Python验证 | ★★★★☆ | Python协程验证框架 |

**中等 (需谨慎验证):**

| 能力领域 | 评估 | 说明 |
|----------|------|------|
| 复杂SVA断言 | ★★★☆☆ | 复杂sequence/property可能有错误 |
| 高级SystemVerilog (UVM) | ★★★☆☆ | UVM框架结构理解有限 |
| 工艺相关时序优化 | ★★★☆☆ | 缺乏PDK具体数据 |
| Yosys综合脚本 | ★★★☆☆ | 基础pass命令知道, 复杂组合可能出错 |

---

### 2.2 Claude对EDA工具命令的知识储备

**工具命令掌握度评估:**

```
Yosys命令知识:
  synth_ice40 / synth_xilinx / synth_ecp5     ★★★★☆  (综合目标命令)
  read_verilog / read_rtlil / write_json       ★★★★★  (基础IO)
  opt / opt_clean / opt_expr                   ★★★☆☆  (优化pass)
  abc / abc9                                   ★★★☆☆  (ABC优化)
  show (可视化)                                ★★★★☆
  自定义pass链组合                              ★★★☆☆  (容易顺序出错)

OpenROAD命令知识:
  基础流程命令 (floorplan/place/route)          ★★★☆☆
  具体参数值 (层数/间距)                        ★★☆☆☆  (工艺依赖)
  OpenSTA时序命令                              ★★★☆☆

KiCad CLI:
  kicad-cli pcb export-gerbers                 ★★★★☆
  kicad-cli pcb run-drc                        ★★★★☆
  IPC API (v9+新接口)                          ★★★☆☆  (知识可能偏旧)

ngspice命令:
  基础仿真命令 (.op/.dc/.ac/.tran)              ★★★★★
  SPICE模型参数 (BSIM4等)                      ★★★☆☆
  收敛参数调优                                  ★★★☆☆
```

---

### 2.3 Claude对PCB设计规范的理解

**强项:**
- 通用布局原则 (去耦电容位置, 晶振隔离)
- IPC标准编号知识 (IPC-2221, IPC-7351, IPC-2152)
- 信号完整性基础概念 (阻抗, 反射, 串扰)
- EMC基本规则 (回流路径, 地平面完整性)
- 差分对布线原则

**弱项 (需RAG增强):**
- 特定制造商的DFM规则 (PCBWay/JLCPCB具体参数)
- 高速接口特定规范 (USB3.2/PCIe5.0/DDR5具体走线规则)
- RF/微波设计规则 (波导, 匹配网络)
- 具体工艺参数 (特定PCB厂商的最小线宽/间距)

---

### 2.4 幻觉高发区域 (Claude容易出错的EDA知识)

**幻觉风险分级矩阵:**

| 风险等级 | 领域 | 典型错误模式 | 缓解策略 |
|----------|------|------------|----------|
| **极高 (红区)** | PDK工艺参数 | 编造不存在的标准单元名称/尺寸 | 强制RAG查询PDK文件 |
| **极高 (红区)** | 商业工具命令参数 | Synopsys DC/Cadence Innovus具体参数名错误 | 提示词注明不确定性 |
| **极高 (红区)** | Liberty文件具体数值 | 编造延迟/电容数值 | 禁止无来源数值输出 |
| **高 (橙区)** | 特定版本API | KiCad v9 IPC API新接口混淆旧接口 | 标注版本, RAG查文档 |
| **高 (橙区)** | OpenROAD具体参数 | 布线层名/PDK相关参数错误 | 要求用户提供PDK上下文 |
| **高 (橙区)** | Yosys复杂pass组合 | pass顺序错误导致优化失效 | 提供经验证的pass模板 |
| **中 (黄区)** | SDC时序约束 | set_multicycle_path路径指定错误 | 输出后提示验证 |
| **中 (黄区)** | SPICE收敛参数 | 错误的TRTOL/ITL参数组合 | 提供标准调试流程 |
| **低 (绿区)** | Verilog基础语法 | 极少语法错误 | 仍建议仿真验证 |
| **低 (绿区)** | SPICE基本命令 | .op/.dc/.ac/.tran用法正确率高 | 标准流程即可 |

**幻觉高发的根本原因分析:**
1. **工艺依赖性**: PDK参数因代工厂/节点/版本而异, Claude无法获知具体环境
2. **版本漂移**: EDA工具API频繁更新(KiCad v9→v10变化大), 训练数据可能过时
3. **闭源工具稀缺**: Synopsys/Cadence商业工具文档不公开, 训练数据严重不足
4. **精确数值依赖**: EDA严重依赖精确数值(延迟/电容/坐标), Claude擅长模糊推理而非精确记忆

---

### 2.5 需要RAG增强的知识盲点

| 知识类型 | RAG数据源 | 优先级 |
|----------|-----------|--------|
| KiCad IPC API文档 | KiCad官方文档/源码 | P0 |
| OpenROAD Python绑定API | OpenROAD readthedocs | P0 |
| Yosys pass参考手册 | Yosys官方文档 | P0 |
| 开源PDK规则 (Sky130/GF180) | PDK文件本身 | P0 |
| ngspice SPICE参考手册 | ngspice手册 | P1 |
| Liberty格式规范 | Liberty技术参考 | P1 |
| IPC PCB设计标准 (IPC-2221等) | IPC标准文档 | P1 |
| cocotb API文档 | cocotb.readthedocs | P1 |
| EDA错误代码数据库 | 社区整理/工具日志 | P2 |
| 常见DRC规则映射表 | PDK DRC文档 | P2 |


---

## 3. EDA System Prompt工程

### 3.1 通用EDA Assistant系统提示词

```
SYSTEM_PROMPT_EDA_GENERAL = """
You are AUTO_EDA, an expert AI assistant for Electronic Design Automation.
You have deep knowledge across PCB design, digital IC design, analog simulation,
and formal/functional verification.

## Core Principles

1. ACCURACY OVER COMPLETENESS: When uncertain about tool-specific parameters,
   PDK values, or version-specific APIs, explicitly state uncertainty rather
   than guessing. Prefer "I need more context about your PDK/tool version" over
   fabricating plausible-sounding values.

2. TOOL-AWARE RESPONSES: Always clarify which EDA tool context you are operating
   in. The same concept (e.g., "DRC") has different commands in KiCad vs KLayout
   vs Calibre.

3. VERIFICATION REMINDER: All generated code (Verilog, SPICE, TCL, Python EDA
   scripts) must be treated as a starting point. Remind users to simulate/run
   DRC before treating output as production-ready.

4. CONTEXT HIERARCHY: Prioritize information from:
   (1) Tool output/logs provided by user
   (2) Design files provided by user  
   (3) RAG-retrieved documentation
   (4) General EDA knowledge
   Never invent values when context is missing — ask instead.

5. UNIT DISCIPLINE: Always state units explicitly. EDA is rife with unit
   ambiguity (ns vs ps, um vs nm, dBm vs dBV). When interpreting user input,
   confirm units before proceeding.

## Response Format for EDA Tasks

- Code blocks: Use language tags (verilog, python, spice, tcl, json)
- File references: State exact file format and version when relevant
- Error explanations: Root cause first, then fix steps
- Design suggestions: State the trade-off (timing vs area vs power)
"""
```

---

### 3.2 PCB专用提示词模板

```
SYSTEM_PROMPT_PCB = """
{GENERAL_EDA_RULES}

## PCB Design Context

Active Tool: KiCad {kicad_version}
Design File: {pcb_file_path}
Board Stackup: {layer_count}-layer, {copper_weight}oz copper
Design Rules: Min trace {min_trace}mil, Min space {min_space}mil, Min via drill {min_drill}mm

## PCB-Specific Behavior

1. DESIGN RULE AWARENESS: Always apply the board's specific DRC rules. Do not
   suggest trace widths or spacings below the board's manufacturing limits.

2. SIGNAL INTEGRITY GUIDANCE:
   - High-speed signals (>100MHz): Always recommend controlled impedance
   - Differential pairs: Enforce length matching within ±5mil default
   - Power decoupling: 100nF ceramic within 2mm of each VCC pin

3. EMC CHECKLIST (auto-apply to layout reviews):
   □ Return path continuity under high-speed traces
   □ No signal crossing plane splits  
   □ Crystal/oscillator isolated from digital switching noise
   □ Ferrite beads on power entry points

4. MANUFACTURABILITY:
   - Reference IPC-7351 for SMD land patterns
   - Flag components below 0402 as high-risk for hand assembly
   - Minimum annular ring: 0.15mm (standard), 0.1mm (advanced)

5. KICAD API NOTES:
   - Use IPC API (v9+) for programmatic access, not legacy SWIG bindings
   - kicad-cli for batch operations: DRC, Gerber export, BOM generation
   - S-Expression format (.kicad_pcb) is human-readable and diff-friendly

## KiCad IPC API Quick Reference
```python
# Connection example
import kicad_utils  # AUTO_EDA wrapper
board = kicad_utils.load_board("{pcb_file_path}")

# DRC execution
drc_results = board.run_drc()
violations = [v for v in drc_results if v.severity == 'error']

# Export Gerbers
kicad_utils.export_gerbers(board, output_dir="./gerbers/")
```
"""
```

---

### 3.3 数字IC专用提示词模板

```
SYSTEM_PROMPT_DIGITAL_IC = """
{GENERAL_EDA_RULES}

## Digital IC Design Context

PDK: {pdk_name} ({process_node})
Target: {target_frequency}MHz @ {voltage}V, {temperature}°C
Tool Flow: {tool_flow}  # e.g., Yosys + OpenROAD, or DC + Innovus
Design Stage: {stage}  # RTL / Post-Synthesis / Post-Layout

## Stage-Aware Guidance

### RTL Stage Rules:
- Flag non-synthesizable constructs: initial blocks with delays, real types,
  system tasks in always blocks
- Recommend synchronous reset unless async reset explicitly required
- State machine: prefer One-Hot encoding for FPGAs, Binary for ASICs
- Clock domain crossing: identify and flag all async domain crossings

### Synthesis Stage Rules:
- SDC constraints are REQUIRED for meaningful synthesis results
- Always specify operating conditions: set_operating_conditions
- Report synthesis QoR: area, timing, power triad
- Yosys flow example:
  ```tcl
  yosys -p "read_verilog design.v; synth -top {top_module};
            dfflibmap -liberty {lib_file};
            abc -liberty {lib_file};
            write_verilog netlist.v"
  ```

### Post-Layout Stage Rules:
- Timing analysis MUST use extracted parasitics (SPEF)
- Report WNS (Worst Negative Slack), TNS (Total Negative Slack), FEP (Failing
  Endpoint count)
- Hold violations are more dangerous than setup (unfixable in mask)
- DRC clean is a hard requirement before tapeout

## Timing Violation Classification

| Violation Type | Urgency | Primary Fix |
|----------------|---------|-------------|
| Setup (WNS < 0) | High | Buffer insertion, logic restructuring, floorplan |
| Hold (WNS < 0, hold) | Critical | Delay cell insertion |
| Max transition | Medium | Buffer/driver upsizing |
| Max fanout | Medium | Buffer tree insertion |
| Clock skew | High | CTS parameter tuning |

## CRITICAL: Never Invent PDK Values
For {pdk_name}, do not fabricate:
- Standard cell names or drive strengths
- Metal layer names or pitch values  
- Via resistance or capacitance values
Always retrieve from actual PDK files or ask user to provide.
"""
```

---

### 3.4 仿真分析专用提示词模板

```
SYSTEM_PROMPT_SIMULATION = """
{GENERAL_EDA_RULES}

## Simulation Context

Simulator: {simulator}  # ngspice / Xyce / Verilator / Icarus / cocotb
Analysis Type: {analysis_type}  # DC / AC / Transient / Mixed-Signal
Design: {design_description}

## SPICE Simulation Rules (ngspice/Xyce)

### Convergence Protocol (ordered escalation):
1. Check netlist: unconnected nodes, floating gates, missing ground
2. Add .ic or .nodeset if operating point known
3. Tighten/loosen RELTOL (try 0.01 before 0.001)
4. For transient: reduce initial TSTEP by 10x
5. For DC sweep: use .options GMIN=1e-10
6. Break circuit into subcircuits and simulate independently
7. Check device models: correct temperature, process corner

### Analysis Template Library:
```spice
* Operating Point
.op

* DC Transfer Characteristic  
.dc Vin 0 5 0.01

* AC Frequency Sweep (1Hz to 1GHz, 100 pts/decade)
.ac dec 100 1 1G

* Transient (100ns total, 1ps step)
.tran 1p 100n

* Monte Carlo (100 runs)
.mc 100 transient

* Process Corners
.corners {pdk_corner_file}
```

### Output Interpretation:
- AC phase margin: measure at 0dB gain crossing
- Transient: check rise/fall time, overshoot (<10%), settling time
- Noise: input-referred noise at critical frequency point
- DC: verify all node voltages are physically reasonable

## Digital Simulation Rules (Verilator/cocotb)

### cocotb Test Structure:
```python
import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock

@cocotb.test()
async def test_{design_name}(dut):
    """Auto-generated test skeleton."""
    # Start clock
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    
    # Reset sequence
    dut.rst_n.value = 0
    await Timer(100, units="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    
    # Test body: fill in stimulus and assertions
    # assert dut.output.value == expected, f"Got {dut.output.value}"
```

### Waveform Analysis:
- VCD files: parseable with Python vcd library
- Key signals to monitor: clocks, resets, data valid, error flags
- Recommend saving only necessary signals to reduce VCD size
"""
```

---

### 3.5 MCP Prompts暴露方式

MCP协议支持通过 `prompts/list` 和 `prompts/get`

---

### 3.5 MCP Prompts暴露方式

MCP协议支持通过 `prompts/list` 和 `prompts/get` 端点将提示词模板暴露给Claude客户端。

**MCP Prompts注册结构 (auto_eda/mcp_server/prompts.py):**

```python
from fastmcp import FastMCP

mcp = FastMCP("auto-eda-prompts")

@mcp.prompt()
def eda_pcb_assistant(kicad_version: str = "9.0", layer_count: int = 4) -> str:
    # PCB设计助手 - 提供KiCad专项设计指导
    return SYSTEM_PROMPT_PCB.format(kicad_version=kicad_version, layer_count=layer_count)

@mcp.prompt()
def eda_digital_ic_assistant(pdk_name: str, process_node: str, target_frequency: str) -> str:
    # 数字IC设计助手 - RTL到GDSII流程指导
    return SYSTEM_PROMPT_DIGITAL_IC.format(**locals())

@mcp.prompt()
def eda_simulation_assistant(simulator: str = "ngspice", analysis_type: str = "Transient") -> str:
    # 仿真分析助手 - SPICE/数字仿真调试指导
    return SYSTEM_PROMPT_SIMULATION.format(**locals())
```

**Claude Desktop配置示例:**

```json
{
  "mcpServers": {
    "auto-eda": { "command": "uvx", "args": ["auto-eda"] }
  }
}
```

用户触发方式: "使用PCB助手模式" → Claude调用 `eda_pcb_assistant` prompt并填充专业系统上下文。

---

## 4. 错误诊断知识库设计

### 4.1 常见EDA错误代码→自然语言解释映射

知识库采用Python字典结构，支持正则模式匹配，存储于 `auto_eda/knowledge/error_database.py`。

**数据模式 (Schema):**

```python
ERROR_ENTRY = {
    "pattern": str,          # 正则表达式匹配错误信息
    "explanation": str,      # 自然语言解释（面向工程师）
    "root_cause": str,       # 根本原因分析
    "fix_steps": list[str],  # 有序修复步骤
    "severity": str,         # ERROR / WARNING / FATAL / INFO
    "related_docs": list[str] # 相关文档链接
}
```

**核心错误映射表 (按工具分类):**

| 工具 | 错误模式 | 自然语言解释 | 严重度 |
|------|---------|------------|--------|
| Yosys | `Module .* not found` | 模块定义缺失：文件未加载或模块名拼写错误 | ERROR |
| Yosys | `multiple conflicting drivers` | 多驱动冲突：同一信号有多个赋值来源 | WARNING |
| Yosys | `Assert failed` | 内部断言失败：RTL包含不支持的构造 | FATAL |
| OpenROAD | `No floorplan found` | 未初始化布局规划：缺少initialize_floorplan步骤 | ERROR |
| OpenROAD | `No routing tracks` | 无布线轨道：LEF层定义与tech文件不一致 | WARNING |
| KiCad DRC | `Clearance violation` | 铜导体间距不足：小于设计规则最小值 | ERROR |
| KiCad DRC | `Footprint courtyard overlap` | 封装禁止区重叠：元件物理实体可能碰撞 | ERROR |
| KiCad DRC | `Missing connection` | 未连接网络：原理图网络无对应PCB走线 | ERROR |
| ngspice | `Convergence problem` | DC收敛失败：浮空节点、正反馈或模型异常 | ERROR |
| ngspice | `Timestep too small` | 时间步长过小：信号跳变过快超出步长控制 | ERROR |
| OpenSTA | `setup violation` | 建立时间违规：数据路径延迟超过时钟周期 | ERROR |
| OpenSTA | `hold violation` | 保持时间违规：数据变化过快（路径过短） | CRITICAL |

**Yosys关键错误修复流程:**

```
[Module not found]
  ├── 检查文件列表: yosys -p "read_verilog -sv *.v"
  ├── 确认模块名大小写
  └── 检查子模块是否在单独文件中

[Multiple conflicting drivers]
  ├── 搜索所有对该信号的赋值: grep -n "assign.*{signal}\|{signal}\s*<=" *.v
  ├── 合并为单一驱动源
  └── 或改用tri/wor类型（特殊场景）
```

**ngspice收敛失败调试序列 (有序):**

```
1. 检查浮空节点: ngspice -b -a circuit.sp 2>&1 | grep "dangling"
2. 添加初始条件: .nodeset V(sensitive_node)=estimated_value
3. 放宽容差: .options RELTOL=0.01 (默认0.001)
4. GMIN步进: .options GMIN=1e-9
5. Source stepping: .options METHOD=GEAR
6. 分段仿真: 将电路分解为子电路独立验证
```

---

### 4.2 DRC违规类型→修复建议映射

| DRC违规类型 | 域 | 严重度 | 自动修复 | 推荐修复策略 |
|------------|-----|--------|---------|-------------|
| Min Width | IC/PCB | ERROR | 半自动 | 加宽导体/走线 |
| Min Spacing | IC/PCB | ERROR | 半自动 | 增大间距/重新布线 |
| Min Enclosure | IC | ERROR | 手动 | 调整上层金属覆盖 |
| Min Area | IC | WARNING | 自动 | 插入虚填充(metal fill) |
| Via Coverage | IC | ERROR | 半自动 | 增加via数量 |
| Antenna Rule | IC | WARNING | 半自动 | 插入antenna diode |
| Courtyard Overlap | PCB | ERROR | 手动 | 重新布局元件 |
| Silkscreen Overlap | PCB | INFO | 自动 | 移动/缩小丝印 |
| Missing Teardrops | PCB | WARNING | 自动 | KiCad自动添加泪滴 |
| Impedance Mismatch | PCB | WARNING | 手动 | 调整线宽匹配目标阻抗 |

---

### 4.3 时序违规→优化策略映射

| 违规类型 | WNS范围 | 推荐策略 | 实施工具 |
|---------|---------|---------|----------|
| Setup (轻微) | -0.1ns~0 | 单元upsizing + buffer插入 | OpenROAD ECO |
| Setup (中等) | -0.5ns~-0.1ns | 逻辑重构 + 布局优化 | 重新P&R |
| Setup (严重) | <-0.5ns | 流水线重设计 + RTL修改 | 重新综合 |
| Hold | 任意负值 | 延迟单元插入 | OpenROAD hold fix |
| Max Transition | 违规 | buffer树插入 / driver upsizing | OpenROAD |
| Max Fanout | 违规 | buffer树分割高扇出网络 | Yosys / OpenROAD |
| Clock Skew | >100ps | CTS参数调整 / skew group | OpenROAD CTS |

**Setup时序修复优先级决策树:**

```
 Setup Violation 检测
    |
    ├── WNS > -50ps? → 尝试 set_dont_touch 解除约束 + ECO buffer
    |
    ├── 关键路径扇出>20? → 优先修复高扇出 (buffer tree)
    |
    ├── 关键路径单元已最大尺寸? → 布局优化 (move cells closer)
    |
    ├── 路径跨越多个时钟域? → 检查multicycle_path设置
    |
    └── WNS < -500ps? → RTL重设计 (流水线分割)
```

---

### 4.4 仿真收敛失败→调试步骤映射

**SPICE仿真诊断决策树:**

```
仿真失败
   |
   ├── [DC/OP失败]
   │   ├── 步骤1: 检查浮空节点 (每个节点有DC路径到GND?)
   │   ├── 步骤2: 检查模型文件是否正确加载
   │   ├── 步骤3: 添加 .nodeset 提供初始猜测
   │   ├── 步骤4: 尝试 .options GMIN stepping
   │   └── 步骤5: 使用source stepping (.options SRC_STEP)
   |
   ├── [Transient失败 - 时间步过小]
   │   ├── 步骤1: 检查激励信号的上升时间 (tr >= 1ps)
   │   ├── 步骤2: 增大 TRTOL (7→3→1)
   │   ├── 步骤3: 检查寄生振荡 (在可疑节点加RC阻尼)
   │   └── 步骤4: 使用 METHOD=GEAR 积分方法
   |
   └── [收敛但结果异常]
       ├── 检查单位: 电压/电流/时间单位是否正确
       ├── 检查模型工作区间: MOSFET是否在亚阈值区?
       └── 对比手算估算值验证量级
```

---

## 5. EDA决策规则库

### 5.1 PCB布局规则

**高速信号布局规则 (结构化决策表):**

```python
# auto_eda/knowledge/pcb_rules.py
PCB_LAYOUT_RULES = {
    "high_speed_signals": [
        {
            "rule_id": "PCB-HS-001",
            "condition": "signal_frequency > 100e6",  # >100MHz
            "action": "require_controlled_impedance",
            "params": {"target_ohms": 50, "tolerance": 0.1},
            "rationale": "防止信号反射，维护信号完整性"
        },
        {
            "rule_id": "PCB-HS-002",
            "condition": "is_differential_pair",
            "action": "enforce_length_matching",
            "params": {"max_skew_mil": 5},
            "rationale": "差分对等长保证共模抑制比"
        },
        {
            "rule_id": "PCB-HS-003",
            "condition": "signal_type in ['DDR', 'PCIe', 'USB3']",
            "action": "apply_length_matching_group",
            "params": {"group_tolerance_ps": 20},
            "rationale": "总线等长保证建立/保持时序窗口"
        },
        {
            "rule_id": "PCB-HS-004",
            "condition": "trace_crosses_plane_split",
            "action": "BLOCK",
            "severity": "ERROR",
            "rationale": "跨参考平面切割会产生强烈EMI辐射"
        }
    ],
    "power_layout": [
        {
            "rule_id": "PCB-PWR-001",
            "condition": "ic_has_power_pin",
            "action": "place_decoupling_cap",
            "params": {"max_distance_mm": 2.0, "value": "100nF", "type": "ceramic"},
            "rationale": "减少电源平面的瞬态阻抗"
        },
        {
            "rule_id": "PCB-PWR-002",
            "condition": "current_path_ampere > 1.0",
            "action": "calculate_trace_width",
            "formula": "IPC-2152: W = I / (k * dT^0.44 * thickness^0.725)",
            "rationale": "防止铜导体过热"
        }
    ],
    "thermal_layout": [
        {
            "rule_id": "PCB-THERM-001",
            "condition": "component_power_dissipation_W > 0.5",
            "action": "maintain_spacing",
            "params": {"min_spacing_mm": 5.0},
            "rationale": "避免热耦合影响相邻器件"
        },
        {
            "rule_id": "PCB-THERM-002",
            "condition": "has_thermal_pad",
            "action": "add_thermal_vias",
            "params": {"via_count": "grid_pattern", "via_drill_mm": 0.3},
            "rationale": "热通孔将热量传导至内层散热"
        }
    ]
}
```

**MCP工具返回格式示例:**

```json
{
  "tool": "check_pcb_layout_rules",
  "violations": [
    {
      "rule_id": "PCB-HS-004",
      "severity": "ERROR",
      "location": {"x": 45.2, "y": 32.1, "layer": "F.Cu"},
      "description": "High-speed signal CLK_100M crosses plane split at (45.2, 32.1)",
      "fix_suggestion": "Reroute to avoid crossing the GND/PWR plane boundary, or add stitching capacitor at crossing point"
    }
  ]
}
```

---

### 5.2 综合约束典型模式

**SDC约束模板库:**

```tcl
# 模板1: 单时钟同步设计
create_clock -name clk_sys -period 10.0 [get_ports clk]
set_clock_uncertainty -setup 0.2 [get_clocks clk_sys]
set_clock_uncertainty -hold 0.1 [get_clocks clk_sys]
set_input_delay -clock clk_sys -max 2.0 [all_inputs]
set_input_delay -clock clk_sys -min 0.5 [all_inputs]
set_output_delay -clock clk_sys -max 2.0 [all_outputs]
set_output_delay -clock clk_sys -min 0.0 [all_outputs]

# 模板2: 多时钟设计 (异步域)
create_clock -name clk_a -period 10.0 [get_ports clk_a]
create_clock -name clk_b -period 7.0  [get_ports clk_b]
set_clock_groups -asynchronous -group clk_a -group clk_b
# 注意: 跨域路径需要CDC同步器

# 模板3: 例外路径
# False path: 复位路径不需要时序检查
set_false_path -from [get_ports rst_n]
# Multicycle path: 多拍路径
set_multicycle_path 2 -setup -from [get_cells slow_data_reg*] -to [get_cells capture_reg*]
set_multicycle_path 1 -hold  -from [get_cells slow_data_reg*] -to [get_cells capture_reg*]
```

**Yosys综合Recipe决策矩阵:**

| 目标 | 推荐Recipe | 关键Pass |
|------|-----------|----------|
| 最小面积 | `synth -run begin:fine; opt -full; abc -g aig` | opt_expr, opt_clean |
| 最高时序 | `synth; abc -D {period_ps}` | abc with timing |
| FPGA (Xilinx) | `synth_xilinx -top {top} -edif out.edif` | xilinx_dffopt |
| FPGA (iCE40) | `synth_ice40 -top {top} -json out.json` | ice40_opt |
| 形式验证准备 | `prep -top {top}; flatten` | flatten, clean |

---

### 5.3 时序收敛常用策略

**时序收敛决策树 (OpenROAD流程):**

```
时序收敛流程
│
├── 阶段1: 综合后检查 (pre-layout)
│   ├── 报告: report_timing -path_type full -delay max
│   ├── 目标: WNS > -0.5ns (预留布线裕量)
│   └── 修复: 调整综合约束 / 修改RTL
│
├── 阶段2: 布局后检查 (post-placement)
│   ├── 报告: estimate_parasitics -spef_file
│   ├── 目标: WNS > -0.2ns
│   └── 修复: 移动高负载单元 / 调整布局约束
│
├── 阶段3: CTS后检查
│   ├── 目标: 时钟偏斜 < 100ps, 延迟 < 500ps
│   └── 修复: 调整cts_target_skew参数
│
└── 阶段4: 布线后签收 (post-route)
    ├── 使用真实SPEF寄生参数
    ├── 目标: WNS >= 0, TNS = 0
    └── 修复策略优先级:
        1. ECO buffer insertion (最快)
        2. Cell resizing (无线变更)
        3. Local rerouting (小范围)
        4. 重新放置关键单元 (较大影响)
```

---

### 5.4 DRC修复优先级规则

**DRC修复优先级矩阵 (IC设计):**

| 优先级 | DRC类型 | 原因 | 修复难度 |
|--------|---------|------|----------|
| P0 - 必修 | Short (短路) | 直接导致功能失效 | 中 |
| P0 - 必修 | Metal not connected (断路) | 直接导致功能失效 | 中 |
| P0 - 必修 | LVS mismatch | 版图与原理图不一致 | 高 |
| P1 - 必修 | Min spacing | 制造良率风险 | 低 |
| P1 - 必修 | Min width | 制造良率风险 | 低 |
| P1 - 必修 | Via enclosure | 接触可靠性风险 | 低 |
| P2 - 建议修 | Min area | 蚀刻问题风险 | 低 |
| P2 - 建议修 | Antenna | 栅极氧化层损伤风险 | 低 |
| P3 - 可接受 | Metal density | 化学机械平坦化均匀性 | 低 |

**规则嵌入MCP工具返回的实现:**

```python
# auto_eda/tools/drc_advisor.py
def prioritize_drc_violations(violations: list[DRCViolation]) -> list[DRCViolation]:
    PRIORITY_MAP = {
        "short": 0, "open": 0, "lvs_mismatch": 0,
        "min_spacing": 1, "min_width": 1, "via_enclosure": 1,
        "min_area": 2, "antenna": 2,
        "metal_density": 3
    }
    for v in violations:
        v.priority = PRIORITY_MAP.get(v.rule_type, 2)
        v.fix_suggestion = RULE_FIX_SUGGESTIONS[v.rule_type]
    return sorted(violations, key=lambda x: x.priority)
```

---

## 6. 领域知识飞轮实现方案

### 6.1 用户操作→知识积累机制

**知识飞轮架构:**

```
用户操作流
    │
    ├── [工具调用] MCP Tool执行
    │       │
    │       ├── 记录: 调用参数 + 结果 + 耗时
    │       ├── 提取: 错误模式 (失败调用)
    │       └── 提取: 成功配置 (成功调用)
    │
    ├── [错误修复] 用户确认修复有效
    │       │
    │       └── 写入: error_solutions_db
    │           {error_pattern → fix_steps (用户验证)}
    │
    ├── [设计完成] 项目达到里程碑
    │       │
    │       ├── 提取: 成功的SDC约束模式
    │       ├── 提取: 有效的布局布线参数
    │       └── 提取: 仿真收敛参数组合
    │
    └── [反馈评分] 用户对建议评分 (1-5星)
            │
            └── 更新: 知识条目的置信度权重
```

**知识条目数据模型:**

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class KnowledgeEntry:
    entry_id: str
    domain: str           # pcb / digital_ic / simulation / verification
    category: str         # error_fix / design_rule / tool_param / workflow
    content: dict         # 知识内容（结构化）
    source: str           # user_feedback / tool_log / community / manual
    confidence: float     # 0.0-1.0，基于验证次数和用户评分
    usage_count: int      # 被检索/应用次数
    success_rate: float   # 应用后用户标记成功的比率
    created_at: datetime
    updated_at: datetime
    tags: list[str]
    pdk_context: str      # 适用PDK（sky130/gf180/generic）
    tool_version: str     # 适用工具版本

**知识积累触发点实现 (auto_eda/knowledge/accumulator.py):**

```python
class KnowledgeAccumulator:
    def on_tool_call_success(self, tool_name: str, params: dict, result: dict):
        if tool_name in KNOWLEDGE_EXTRACTORS:
            entry = KNOWLEDGE_EXTRACTORS[tool_name](params, result)
            self.db.upsert(entry)

    def on_tool_call_failure(self, tool_name: str, params: dict, error: str):
        self.pending_errors.append({
            "tool": tool_name,
            "error_pattern": extract_error_pattern(error),
            "context": params
        })

    def on_user_confirms_fix(self, error_id: str, fix_steps: list[str], rating: int):
        entry = self.pending_errors[error_id]
        entry["fix_steps"] = fix_steps
        entry["confidence"] = rating / 5.0
        self.db.insert(KnowledgeEntry(**entry))
```

---

### 6.2 知识库版本管理

**目录结构:**

```
auto_eda/knowledge/
  db/
    core_knowledge_v1.0.json      # 发布时内置基础知识库
    community_knowledge.json       # 社区贡献（可选加载）
    user_local.json                # 用户本地积累（不上传）
  migrations/
    001_add_openroad_rules.py
    002_add_sky130_pdk_rules.py
```

**版本控制规则:**

| 变更类型 | 版本号 | 迁移要求 |
|---------|--------|----------|
| 新增知识条目 | PATCH | 无需迁移 |
| 修改条目结构 | MINOR | 需迁移脚本 |
| 重构分类体系 | MAJOR | 完整迁移 |
| 删除废弃条目 | MINOR | 标记deprecated |

**Schema版本化示例:**

```json
{
  "schema_version": "1.2.0",
  "generated_at": "2026-03-14T00:00:00Z",
  "tool_compatibility": {
    "kicad": ">=9.0",
    "yosys": ">=0.40",
    "openroad": ">=3.0"
  },
  "entries": [
    {
      "entry_id": "ERR-YOSYS-001",
      "domain": "digital_ic",
      "category": "error_fix",
      "confidence": 0.95,
      "usage_count": 1423
    }
  ]
}
```

### 6.3 社区知识贡献流程

**贡献工作流:**

```
用户发现新知识点
    │
    ├── [CLI命令] auto-eda knowledge contribute
    │       │
    │       ├── 填写模板: domain/category/content/evidence
    │       └── 本地验证: schema检查 + 重复检测
    │
    ├── [自动提交] 生成PR到 auto-eda-knowledge 仓库
    │       │
    │       ├── CI自动测试: 格式验证 + 冲突检测
    │       └── 社区审核: 2名维护者approve
    │
    └── [合并发布] 随下一个PATCH版本分发
            │
            └── 贡献者获得: CONTRIBUTORS.md署名 + 积分
```

**知识贡献CLI接口:**

```bash
# 贡献新错误解决方案
auto-eda knowledge contribute \
  --domain digital_ic \
  --category error_fix \
  --tool yosys \
  --error-pattern "ERROR: .*not found" \
  --fix "1. 检查文件列表 2. 确认模块名" \
  --evidence "personal_experience"

# 查看本地知识库统计
auto-eda knowledge stats
# Output:
# Core knowledge: 847 entries (v1.2.0)
# Community: 234 entries
# Local: 12 entries
# Total confidence avg: 0.82
```

**社区知识质量保障机制:**

| 机制 | 实现方式 | 目的 |
|------|---------|------|
| 验证计数 | 每次成功应用+1 | 淘汰低质量条目 |
| 置信度衰减 | 工具版本升级后降低0.1 | 保持知识时效性 |
| 冲突检测 | 相似度>0.9时标记 | 避免重复条目 |
| PDK绑定 | 标注适用PDK | 避免跨PDK误用 |
| 专家审核标记 | EDA专家标注verified | 权重提升 |

---

## 附录A: 知识库JSON Schema定义

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "AUTO_EDA KnowledgeEntry",
  "type": "object",
  "required": ["entry_id", "domain", "category", "content", "confidence"],
  "properties": {
    "entry_id": {"type": "string", "pattern": "^[A-Z]+-[A-Z]+-[0-9]{3}$"},
    "domain": {"enum": ["pcb", "digital_ic", "analog_sim", "verification", "cross_domain"]},
    "category": {"enum": ["error_fix", "design_rule", "tool_param", "workflow", "prompt_template"]},
    "content": {
      "type": "object",
      "properties": {
        "error_pattern": {"type": "string"},
        "explanation": {"type": "string"},
        "fix_steps": {"type": "array", "items": {"type": "string"}},
        "severity": {"enum": ["INFO", "WARNING", "ERROR", "FATAL", "CRITICAL"]}
      }
    },
    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    "pdk_context": {"type": "string", "default": "generic"},
    "tool_version": {"type": "string"}
  }
}
```

---

## 附录B: 提示词模板速查索引

| 场景 | MCP Prompt名称 | 关键参数 |
|------|---------------|----------|
| PCB设计审查 | `eda_pcb_assistant` | kicad_version, layer_count, design_rules |
| 数字IC综合 | `eda_digital_ic_assistant` | pdk_name, process_node, target_freq |
| SPICE仿真调试 | `eda_simulation_assistant` | simulator, analysis_type |
| DRC违规分析 | 内嵌于工具响应 | violation_list, pdk_context |
| 时序违规修复 | 内嵌于工具响应 | wns, tns, critical_path |
| RTL代码审查 | `eda_digital_ic_assistant` + stage=RTL | top_module, clock_constraints |
| Testbench生成 | `eda_simulation_assistant` + simulator=cocotb | design_name, interface_description |

---

## 附录C: RAG增强优先级清单

| 优先级 | 知识类型 | 数据源 | 估计条目数 | 更新频率 |
|--------|---------|--------|-----------|----------|
| P0 | KiCad IPC API参考 | KiCad官方文档 | ~500 | 每版本 |
| P0 | OpenROAD Python API | readthedocs | ~800 | 每月 |
| P0 | Yosys Pass参考手册 | Yosys文档 | ~300 | 每季度 |
| P0 | Sky130 PDK设计规则 | PDK文件 | ~200 | 稳定 |
| P0 | GF180 PDK设计规则 | PDK文件 | ~200 | 稳定 |
| P1 | ngspice参考手册 | ngspice手册 | ~400 | 年度 |
| P1 | Liberty格式规范 | IEEE-ISTO | ~150 | 稳定 |
| P1 | IPC-2221 PCB标准摘要 | IPC文档 | ~100 | 稳定 |
| P1 | cocotb API参考 | readthedocs | ~300 | 每版本 |
| P2 | EDA错误社区数据库 | 社区整理 | ~1000 | 持续 |
| P2 | 常见DRC规则说明 | PDK DRC文档 | ~500 | 稳定 |

**RAG检索触发条件:**
- 用户提到具体工具版本 → 检索版本相关文档
- 检测到PDK名称 → 检索对应PDK规则
- 错误代码识别 → 检索错误数据库
- 幻觉风险词汇检测 (具体数值/参数名) → 强制RAG验证

---

## 变更记录 (Changelog)

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-03-14 | 1.0.0 | 初始版本：EDA知识图谱、Claude能力评估、System Prompt模板、错误诊断库、决策规则库、知识飞轮方案 |
