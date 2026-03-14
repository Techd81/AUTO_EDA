# EDA工具Python API深度调研报告

> 调研日期：2026-03-14
> 调研范围：10个主流EDA工具的Python API成熟度、使用示例、限制与MCP封装难点
> 数据来源：官方文档、GitHub仓库、学术论文、社区论坛（2024-2026）

---

## 1. 各工具Python API成熟度评分表（更新版）

| 工具 | Python API类型 | 成熟度(1-10) | 文档质量 | 社区活跃度 | MCP封装难度 | 主要用途 |
|------|---------------|-------------|----------|-----------|------------|----------|
| **KLayout pya** | 原生C++绑定 | **9/10** | 优秀 | 高 | 低 | 布局、DRC、LVS、截图 |
| **cocotb 2.x** | 纯Python框架 | **9/10** | 优秀 | 高 | 低-中 | HDL仿真验证 |
| **gdstk** | C++后端Python封装 | **8/10** | 良好 | 中-高 | 低 | GDSII/OASIS布局创建 |
| **LibreLane** | 纯Python框架 | **7/10** | 良好 | 中 | 中 | RTL-to-GDSII全流程 |
| **OpenROAD** | SWIG生成绑定 | **7/10** | 中等 | 中-高 | 高 | 物理设计全流程 |
| **KiCad IPC API** | Protobuf/NNG | **7/10** | 良好 | 中-高 | 中 | PCB设计自动化 |
| **PySpice/ngspice** | 进程包装+CFFI | **6/10** | 中等 | 中 | 中 | 电路仿真 |
| **pyverilog** | 纯Python解析器 | **6/10** | 中等 | 低-中 | 低 | Verilog RTL解析分析 |
| **Pyosys** | pybind11绑定 | **5/10** | 差 | 低 | 高 | RTL综合（实验性）|
| **Magic VLSI** | 无Python API | **2/10** | 差 | 低 | 极高 | VLSI版图（仅Tcl）|

---

## 2. 各工具详细分析

### 2.1 OpenROAD Python API

**状态**：生产就绪，用于600+次芯片流片
**版本**：持续开发中（2026年3月仍活跃）
**运行方式**：必须在`openroad -python script.py`环境内运行，不能独立import

#### API架构
```
openroad（ord）模块  → 高层orchestration，工具管理
odb模块             → OpenDB数据库，1800+个对象类
Timing类            → 时序分析
```

#### 关键API调用示例

```python
# 必须在openroad -python环境内运行
from openroad import Design, Tech
import odb

# 加载工艺文件
tech = Tech()
tech.readLef("sky130_fd_sc_hd.tlef")
tech.readLef("sky130_fd_sc_hd_merged.lef")
tech.readLiberty("sky130_fd_sc_hd__tt_025C_1v80.lib")

# 加载设计
design = Design(tech)
design.readVerilog("design.v")
design.link("top_module")
# 或直接读取已完成布局的数据库
# design.readDb("post_place.odb")

# 访问数据库对象
db = odb.get_db()
chip = db.getChip()
block = chip.getBlock()

# 遍历实例（netlist）
for inst in block.getInsts():
    print(f"Instance: {inst.getName()}, Master: {inst.getMaster().getName()}")
    loc = inst.getLocation()
    print(f"  Location: ({loc[0]/1000:.3f}um, {loc[1]/1000:.3f}um)")

# 遍历网
for net in block.getNets():
    print(f"Net: {net.getName()}, SigType: {net.getSigType()}")

# 执行物理设计步骤
design.floorplan()       # 等价Tcl: initialize_floorplan
design.globalPlacement() # 等价Tcl: global_placement

# 时序分析
from openroad import Timing
timing = Timing(design)
wns = design.getWorstNegativeSlack()
tns = design.getTotalNegativeSlack()
print(f"WNS: {wns:.3f}ns, TNS: {tns:.3f}ns")

# 混合调用Tcl（对于没有Python绑定的命令）
design.evalTclString("report_checks -path_delay max -format full_clock_expanded")

# 保存设计
design.writeDb("output.odb")
```

#### ASP-DAC 2024教程示例（完整流程）

```python
# 来源：https://github.com/ASU-VDA-Lab/ASP-DAC24-Tutorial
# demo1_flow.py - 完整RTL到GDSII Python流程
from openroad import Design, Tech
import odb

def run_full_flow(design_name, verilog_file):
    tech = Tech()
    # 读取工艺
    tech.readLef("platforms/nangate45/lef/NangateOpenCellLibrary.tech.lef")

    design = Design(tech)
    design.readVerilog(verilog_file)
    design.link(design_name)

    # Floorplan
    design.floorplan(utilization=0.45, aspect_ratio=1.0)

    # IO placement
    design.getIOPlacer().run()

    # Global placement
    gpl = design.getReplace()
    gpl.setTimingDrivenMode(True)
    gpl.doInitialPlace()

    # Clock Tree Synthesis
    cts = design.getTritonCts()
    cts.runTritonCts()

    # Global Routing
    grt = design.getGlobalRouter()
    grt.globalRoute(save_guides=True)

    # Detailed Routing
    design.getTritonRoute().run()

    # 提取寄生参数
    rcx = design.getRCX()
    rcx.extractRC()

    return design
```

#### 已知限制
- Python接口必须在`openroad -python`环境内运行，无法在普通Python环境`import openroad`
- 部分高级功能（如某些时序ECO操作）仅通过Tcl暴露，需用`evalTclString()`调用
- SWIG绑定文档极不完整（1800+对象无文档），需通过`dir()`探索API
- API在不同版本间稳定性差，大版本更新可能破坏脚本
- 调试困难：Python异常有时被内部C++层吞掉，错误信息不清晰
- 内存管理风险：修改设计对象后Python持有的引用可能失效

#### MCP封装难点
- **进程管理**：需要以`openroad -python script.py`模式运行脚本，通过临时文件传递输入输出
- **状态持久化**：设计数据库为内存对象，跨多次MCP调用需通过`.odb`文件序列化
- **推荐方案**：MCP工具生成Python脚本文件 → 调用`openroad -python script.py` → 解析stdout/文件结果

---

### 2.2 KLayout pya Python API

**状态**：最成熟的EDA Python API之一，生产就绪
**版本**：持续活跃开发
**文档**：https://www.klayout.de/doc-qt5/programming/python.html

#### API架构
- `pya`（旧命名空间）或`klayout.db`（现代推荐）
- 支持独立脚本：`klayout -b -r script.py`
- 支持GUI内嵌宏：通过Macro Development IDE

#### 关键API调用示例

```python
import klayout.db as db

# ===== 布局创建 =====
layout = db.Layout()
layout.dbu = 0.001  # 1nm精度

# 创建顶层单元
top_cell = layout.create_cell("TOP")

# 添加层
layer_m1 = layout.layer(1, 0)  # layer=1, datatype=0
layer_via = layout.layer(2, 0)

# 绘制矩形
top_cell.shapes(layer_m1).insert(db.Box(0, 0, 10000, 5000))  # 10um x 5um

# 创建子单元并实例化
sub_cell = layout.create_cell("SUBCELL")
sub_cell.shapes(layer_m1).insert(db.Box(0, 0, 2000, 2000))
top_cell.insert(db.CellInstArray(sub_cell.cell_index(), db.Trans(db.Point(1000, 1000))))

# ===== 读写GDS =====
layout = db.Layout()
layout.read("input_design.gds")

# 写出GDS
options = db.SaveLayoutOptions()
options.format = "GDS2"
layout.write("output.gds", options)

# ===== DRC（Design Rule Check）=====
# 注意：DRC脚本主体使用Ruby DSL，但可从Python调用
import pya

# 方法1：从Python执行.drc脚本文件
drc_macro = pya.Macro("path/to/rules.drc")
drc_report = drc_macro.run()

# 方法2：批处理模式（推荐用于自动化）
# klayout -b -r drc_check.drc -rd input=design.gds -rd report=results.lyrdb

# ===== 截图 =====
import pya

# 在GUI模式下截图
app = pya.Application.instance()
main_window = app.main_window()
view = main_window.current_view()

# 截图保存为PNG
view.save_image("screenshot.png", 1920, 1080)

# ===== LVS（Layout vs Schematic）=====
# LVS脚本也是Ruby# LVS从Python调用方式与DRC类似
lvs_macro = pya.Macro("path/to/lvs_rules.lvs")
lvs_macro.run()
```

#### DRC/LVS重要说明
- DRC和LVS脚本核心使用**Ruby DSL**编写（KLayout官方推荐语言）
- Python（pya）可**调用**这些Ruby脚本，但不能直接用Python写DRC规则
- Python擅长：布局创建、PCells、批处理自动化、结果后处理
- PDK示例：Sky130 PDK包含完整的KLayout DRC/LVS规则集

#### 已知限制
- DRC/LVS脚本本身必须用Ruby编写，Python仅能调用执行
- GUI截图功能需要在有GUI的模式下运行（非`-b`批处理模式）
- 批处理模式（`-b`）不支持GUI操作，某些功能不可用
- klayout Python包在PyPI上可用（`pip install klayout`），但功能是db子集

#### MCP封装难点
- 相对较低：API完善，可通过`klayout -b -r script.py`无头运行
- 截图功能需要GUI，建议用Xvfb虚拟显示或offscreen渲染
- DRC结果为`.lyrdb`格式，需解析XML提取违规信息

---

### 2.3 Pyosys（Yosys Python绑定）

**状态**：实验性/研究用，不推荐生产环境
**版本**：0.63（2026-03-04），PyPI可用
**文档**：https://yosyshq.readthedocs.io/projects/yosys/en/latest/using_yosys/pyosys.html
**安装**：`pip install pyosys`（有预编译wheel，无需编译）

#### 关键API调用示例

```python
from pyosys import libyosys as ys

# ===== 基础综合流程 =====
design = ys.Design()

# 读取Verilog
ys.run_pass("read_verilog tests/simple/fiedler-cooley.v", design)

# 准备/优化
ys.run_pass("prep", design)
ys.run_pass("opt -full", design)

# 标准综合
ys.run_pass("synth -top my_module", design)

# 技术映射（映射到标准单元库）
ys.run_pass("dfflibmap -liberty my_cells.lib", design)
ys.run_pass("abc -liberty my_cells.lib", design)

# 写出网表
ys.run_pass("write_verilog -noattr netlist.v", design)
ys.run_pass("write_rtlil output.il", design)  # RTLIL格式

# ===== 自定义Pass开发 =====
class CellStatsPass(ys.Pass):
    def __init__(self):
        super().__init__("cell_stats", "Print cell type statistics")

    def execute(self, args, design):
        stats = {}
        for module in design.selected_whole_modules_warn():
            for cell in module.selected_cells():
                typ = cell.type.str()
                stats[typ] = stats.get(typ, 0) + 1

        print("Cell Statistics:")
        for cell_type, count in sorted(stats.items()):
            print(f"  {cell_type}: {count}")

# 注册Pass（实例化即注册）
stats_pass = CellStatsPass()

# 执行
ys.run_pass("cell_stats", design)

# ===== 直接修改设计（高级用法）=====
# 在综合后为所有DFF添加使能信号
ys.run_pass("synth", design)
for module in design.selected_whole_modules_warn():
    for cell in list(module.selected_cells()):
        if cell.type.str() == "$dff":
            # 添加使能端口
            en_wire = module.addWire(module.uniquify("$en"), 1)
            # 修改cell类型
            cell.type = ys.IdString("$dffe")
            cell.setPort(ys.IdString("\EN"), ys.SigSpec(en_wire))
            cell.setParam(ys.IdString("\EN_POLARITY"), ys.Const(1, 1))
```

#### 已知限制
- Python API是C++接口的**有限子集**，非所有功能可用
- 修改设计对象后，Python持有的引用可能**失效**（无自动保护）
- 无法直接将RTLIL获取为Python字符串（必须写文件再读取）
- 性能低于C++ Pass，仅适合原型开发
- 文档极少，需查看C++源码理解API
- Windows支持需手动编译（wheel主要针对Linux/macOS）

#### MCP封装难点
- 可通过`pip install pyosys`安装，相对独立
- 问题在于API文档缺乏，LLM难以生成正确调用
- 建议封装为预定义工作流（如synth_sky130）而非暴露底层API

---

### 2.4 cocotb 2.x

**状态**：生产就绪，2.0.0于2025-09-12发布，2.0.1于2025-11-15发布
**文档**：https://docs.cocotb.org/en/stable/
**安装**：`pip install cocotb`

#### 关键API调用示例

```python
# test_my_module.py - 测试文件
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from cocotb.types import LogicArray

@cocotb.test()
async def test_adder_basic(dut):
    """测试简单加法器"""
    # 启动时钟（10ns周期）
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # 复位
    dut.reset.value = 1
    dut.a.value = 0
    dut.b.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.reset.value = 0

    # 测试用例
    test_cases = [(5, 3, 8), (255, 1, 256), (0, 0, 0)]
    for a, b, expected in test_cases:
        dut.a.value = a
        dut.b.value = b
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)

        result = dut.sum.value.integer
        assert result == expected, f"Expected {expected}, got {result} for {a}+{b}"
        dut._log.info(f"{a} + {b} = {result} ✓")

@cocotb.test()
async def test_adder_overflow(dut):
    """测试溢出行为"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await RisingEdge(dut.clk)

    # 使用LogicArray处理复杂信号（2.0新特性）
    dut.a.value = LogicArray("11111111")
    dut.b.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    # 检查结果...
```

```python
# test_runner.py - Verilator集成运行器
import os
from cocotb_tools.runner import get_runner

def test_adder():
    sim = get_runner(os.getenv("SIM", "verilator"))

    # 编译DUT
    sim.build(
        sources=["src/adder.sv"],
        hdl_toplevel="adder",
        build_args=["--trace", "--trace-fst"],  # 波形输出
        waves=True,  # Verilator必须在build时开启
    )

    # 运行测试
    sim.test(
        hdl_toplevel="adder",
        test_module="test_my_module",
    )

if __name__ == "__main__":
    test_adder()
```

#### cocotb 2.0重要变更（从1.x迁移）
| 旧语法（1.x） | 新语法（2.x） |
|-------------|-------------|
| `yield RisingEdge(dut.clk)` | `await RisingEdge(dut.clk)` |
| `dut.sig.value.integer` | `dut.sig.value.integer`（不变）|
| `BinaryValue` | `LogicArray`（新推荐）|
| `raise TestFailure("msg")` | `assert condition, "msg"` |
| Makefile流程 | `cocotb_tools.runner`（推荐）|

#### 支持的仿真器
| 仿真器 | 状态 | 接口 | 最低版本 |
|--------|------|------|----------|
| Verilator | 完全支持 | VPI | ≥5.036 |
| GHDL | 完全支持 | VPI | ≥2.0 |
| Icarus Verilog | 完全支持 | VPI | ≥10.3 |
| Questa/ModelSim | 完全支持 | VPI | - |
| Xcelium | 完全支持 | VPI/VHPI | - |
| VCS | 支持 | VPI | - |
| XSim（Vivado） | **不支持** | 无VPI | - |

#### 已知限制
- XSim（Xilinx/AMD Vivado）**没有**原生支持，需第三方`cocotb-vivado`包（功能有限）
- Verilator的VPI force/release操作不完整支持
- 波形输出需在`build()`时设置，不能事后添加
- 不能实例化HDL模块（DUT必须完整）

#### MCP封装难点
- 中等：需要管理仿真器安装和HDL文件
- 最佳方案：MCP工具接受Verilog/VHDL + Python测试文件，调用runner执行，返回测试结果XML

---

### 2.5 KiCad IPC API（v9/v10）

**状态**：KiCad 9.0（2025-02发布）稳定，v10 RC（2026-03）进一步成熟
**协议**：Protocol Buffers over NNG
（非REST/JSON）
**安装**：`pip install kicad-python`
**文档**：https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/

#### API架构
- KiCad 9+引入IPC API，通过Protobuf消息在NNG socket（Unix domain socket/named pipe）上通信
- 取代旧的SWIG pcbnew绑定（v10中计划移除旧绑定）
- 需要KiCad进程正在运行（无headless模式）

#### 关键API调用示例

```python
# 需要KiCad 9+正在运行并启用API服务器
# KiCad设置：Preferences -> Plugins -> Enable IPC API server
from kipy import KiCad
from kipy.geometry import Vector2

# 连接到运行中的KiCad
kicad = KiCad()

# 获取版本信息
print(kicad.get_version())

# 获取当前PCB板
board = kicad.get_board()

# 遍历焊盘
for footprint in board.get_footprints():
    print(f"Footprint: {footprint.reference}, at {footprint.position}")
    for pad in footprint.pads:
        print(f"  Pad {pad.number}: net={pad.net_name}")

# 获取网络
nets = board.get_nets()
for net in nets:
    print(f"Net: {net.name}")

# 移动元器件
fp = board.get_footprint("U1")
new_pos = Vector2.from_mm(10.0, 20.0)
fp.position = new_pos
board.update_footprint(fp)
```

```python
# 插件开发示例（plugin.json + Python文件）
# plugin.json 位于 ~/Documents/KiCad/9.0/plugins/my_plugin/
# {
#   "name": "My Automation Plugin",
#   "identifier": "com.example.my_plugin",
#   "description": "Automates PCB tasks",
#   "entry": "plugin.py"
# }

# plugin.py
from kipy import KiCad

def run_plugin():
    kicad = KiCad()
    board = kicad.get_board()
    # 自动化操作...
    board.refresh()

run_plugin()
```

#### KiCad 8.x旧API（SWIG，已废弃）

```python
# 旧方式（KiCad 8及以前，v10将移除）
import pcbnew

# 从文件加载（无需运行KiCad GUI）
board = pcbnew.LoadBoard("my_board.kicad_pcb")

# 遍历footprints
for fp in board.GetFootprints():
    print(fp.GetReference(), fp.GetX(), fp.GetY())

# 保存
pcbnew.Refresh()
board.Save("output.kicad_pcb")
```

#### 版本对比
| 特性 | KiCad 8 (SWIG) | KiCad 9+ (IPC API) |
|------|---------------|--------------------|
| 接口类型 | 嵌入式Python | 外部进程通信 |
| 协议 | 直接调用 | Protobuf/NNG |
| headless支持 | 部分支持 | **不支持** |
| Python版本 | KiCad内置 | 任意Python |
| 稳定性 | 较低 | 较高 |
| 文档 | 较差 | 良好 |
| v10状态 | **将移除** | 主流 |

#### 已知限制
- IPC API需要KiCad GUI**正在运行**（无headless模式）
- v9主要支持PCB编辑器，原理图支持有限/待完善
- headless导出操作需用`kicad-cli`命令行工具
- 连接时需要知道socket路径（通常在临时目录）

#### MCP封装难点
- 中等：需要管理KiCad进程生命周期
- headless操作（如导出Gerber、DRC报告）建议用`kicad-cli`而非IPC API
- IPC API最适合交互式自动化场景

---

### 2.6 PySpice / ngspice Python接口

**状态**：PySpice v1.5（2021）+ 2024年维护性更新，可用于生产
**安装**：`pip install PySpice`（还需单独安装ngspice二进制）
**文档**：https://pyspice.fabrice-salvaire.fr/releases/v1.6/
**GitHub**：https://github.com/PySpice-org/PySpice

#### 关键API调用示例

```python
import PySpice.Logging.Logging as Logging
logger = Logging.setup_logging()

from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import numpy as np
import matplotlib.pyplot as plt

# ===== DC工作点分析 =====
circuit = Circuit('Voltage Divider')
circuit.V('input', 'in', circuit.gnd, 10@u_V)
circuit.R(1, 'in', 'out', 2@u_kΩ)
circuit.R(2, 'out', circuit.gnd, 1@u_kΩ)

simulator = circuit.simulator(temperature=25, nominal_temperature=25)
analysis = simulator.operating_point()

for node in analysis.nodes.values():
    print(f'Node {node}: {float(node):.4f} V')
# 输出: Node out: 3.3333 V

# ===== RC电路瞬态仿真 =====
circuit = Circuit('RC Transient')
# 阶跃电压源
circuit.PulseVoltageSource('input', 'in', circuit.gnd,
    initial_value=0@u_V,
    pulsed_value=5@u_V,
    delay_time=1@u_us,
    rise_time=0.1@u_us,
    fall_time=0.1@u_us,
    pulse_width=10@u_us,
    period=20@u_us
)
circuit.R(1, 'in', 'out', 1@u_kΩ)
circuit.C(1, 'out', circuit.gnd, 100@u_nF)

simulator = circuit.simulator(temperature=25, nominal_temperature=25)
analysis = simulator.transient(step_time=0.1@u_us, end_time=30@u_us)

# 结果为numpy数组
time = np.array(analysis.time)
vout = np.array(analysis['out'])

plt.plot(time * 1e6, vout)
plt.xlabel('Time (us)')
plt.ylabel('Voltage (V)')
plt.title('RC Transient Response')
plt.savefig('rc_transient.png')

# ===== AC频率扫描 =====
circuit = Circuit('RC Low Pass Filter')
circuit.SinusoidalVoltageSource('input', 'in', circuit.gnd, amplitude=1@u_V)
circuit.R(1, 'in', 'out', 1@u_kΩ)
circuit.C(1, 'out', circuit.gnd, 1@u_uF)

simulator = circuit.simulator()
analysis = simulator.ac(
    variation='dec',
    number_of_points=100,
    start_frequency=1@u_Hz,
    stop_frequency=1@u_MHz
)

frequency = np.array(analysis.frequency)
magnitude = 20 * np.log10(np.abs(np.array(analysis['out'])))

# ===== ngspice共享库模式（高级）=====
# 允许Python在仿真过程中动态提供电压/电流源
from PySpice.Spice.NgSpice.Shared import NgSpiceShared

class MySimulation(NgSpiceShared):
    def external_voltage(self, vector_name, actual_vector_values, time):
        # Python控制的动态电压源
        return 5.0 * np.sin(2 * np.pi * 1000 * time)
```

#### 已知限制
- PySpice本身**不仿真**，它生成SPICE网表并调用ngspice进程执行
- 需要单独安装ngspice（`conda install ngspice`或系统包管理器）
- ngspice版本兼容性问题：不同版本输出格式略有差异
- PySpice v1.5是2021年发布，部分新ngspice特性未支持
- Windows上ngspice安装和路径配置较复杂
- 复杂电路（如含有压控开关）的Python表示语法不直观

#### MCP封装难点
- 中等：需要管理ngspice二进制的安装和调用
- 结果解析相对简单（numpy数组）
- 建议提供预定义仿真类型（DC、AC、transient）的模板

---

### 2.7 gdstk vs gdspy 对比

**状态**：gdstk是gdspy的官方继任者，生产就绪
**版本**：gdstk v1.0.0（2026-02），gdspy已停止维护
**安装**：`pip install gdstk`
**文档**：https://heitzmann.github.io/gdstk/

#### 性能对比（官方基准测试）

| 操作 | gdspy时间 | gdstk时间 | 加速比 |
|------|----------|----------|--------|
| 10k个矩形创建 | 80.3 ms | 4.87 ms | **16.5x** |
| 读取GDS文件 | 1.48 s | 52.3 ms | **28.3x** |
| Bounding Box | 21.7 ms | 0.10 ms | **216x** |
| FlexPath创建 | 3.91 s | 21.9 ms | **178x** |
| 内存占用 | 基准 | 减少29-71% | - |

#### 关键API调用示例

```python
import gdstk
import numpy as np

# ===== 基础布局 =====
lib = gdstk.Library()
lib.unit = 1e-6      # 1 micron
lib.precision = 1e-9  # 1 nm精度

# 创建单元
cell = lib.new_cell("MY_CELL")

# 基本图形
cell.add(gdstk.rectangle((0, 0), (10, 5), layer=1))
cell.add(gdstk.ellipse((5, 2.5), 3, layer=2))  # 椭圆/圆

# 任意多边形
poly = gdstk.Polygon([(0,0), (5,0), (7.5,5), (0,5)], layer=3)
cell.add(poly)

# 写出GDS
lib.write_gds("design.gds")

# ===== 光子学应用：光栅耦合器 =====
def grating_coupler(period=0.74, fill_frac=0.5, num_teeth=20,
                    width=12.0, layer=1, cell_name="GratingCoupler"):
    """参数化光栅耦合器"""
    cell = gdstk.Cell(cell_name)
    x = width / 2
    w = period * fill_frac
    # 添加光栅齿
    for i in range(num_teeth):
        y = i * period
        cell.add(gdstk.rectangle((-x, y), (x, y + w), layer=layer))
    return cell

# =====


# ===== 波导路径（FlexPath / RobustPath）=====
wg = gdstk.FlexPath([(0, 0)], width=0.5, bend_radius=5.0, layer=1)
wg.horizontal(10)
wg.turn(3.14159/2, "r")  # 右转 90 度
wg.vertical(10)
cell.add(wg)

# RobustPath: 定向耦合器（双波导）
dc = gdstk.RobustPath((0, 0), [0.5, 0.5], 2.0, simple_path=True, layer=1)
dc.segment((10, 0))
cell.add(dc)

# ===== 层次化引用 =====
top = lib.new_cell("TOP")
gc = grating_coupler()
lib.add(gc)
top.add(gdstk.Reference(gc, (0, 0)))
top.add(gdstk.Reference(gc, (100, 0), rotation=3.14159))

# ===== 布尔运算 =====
poly_a = gdstk.rectangle((0, 0), (10, 10))
poly_b = gdstk.ellipse((5, 5), 4)
result = gdstk.boolean(poly_a, poly_b, "and", layer=5)
```

#### gdstk vs gdspy 迁移指南

```python
# gdspy（旧，已停止维护）
import gdspy
lib = gdspy.GdsLibrary()
cell = lib.new_cell("CELL")
cell.add(gdspy.Rectangle((0, 0), (10, 5), layer=1))
lib.write_gds("old.gds")

# gdstk（新，API 类似但快 16-216x）
import gdstk
lib = gdstk.Library()
cell = lib.new_cell("CELL")
cell.add(gdstk.rectangle((0, 0), (10, 5), layer=1))  # 小写函数名
lib.write_gds("new.gds")
lib.write_oas("new.oas")  # gdspy 不支持 OASIS
```

**主要 API 差异**：
- `gdspy.Rectangle` → `gdstk.rectangle`（工厂函数，非类）
- `gdspy.Path` → `gdstk.FlexPath`（自动弯曲）或 `gdstk.RobustPath`（精确控制）
- `gdspy.CellArray` → `gdstk.Reference` with `repetition` 参数
- gdstk 额外支持 OASIS 格式（`write_oas()`）

#### 已知限制
- gdstk 仅处理**几何数据**，不做 DRC/LVS（需配合 KLayout）
- GDSII 格式不支持曲线，自动离散化为多边形折线
- 层次深度过深时性能下降，flat 化后速度更快
- gdspy 已停止维护，不建议用于新项目

#### MCP 封装难点
- **低**：纯 Python，`pip install gdstk` 即可，无系统依赖
- 主要挑战：GDS 文件可能达 GB 级，不能直接传入 LLM 上下文
- 建议提供预定义操作（提取层列表、布尔运算、层统计、缩略图）

---

### 2.8 pyverilog

**状态**：学术/研究用途，最后版本 1.3.0（2020-12），被多篇 EDA 论文引用
**安装**：`pip install pyverilog`（需要 Icarus Verilog 作为预处理器后端）
**GitHub**：https://github.com/PyHDI/Pyverilog

#### API 架构
```
pyverilog.vparser              → Verilog 解析器（生成 AST）
pyverilog.dataflow             → 数据流分析器（信号依赖图）
pyverilog.controlflow          → 控制流/FSM 提取器
pyverilog.ast_code_generator   → AST → Verilog 代码生成
```

#### 关键 API 调用示例

```python
# ===== 解析 Verilog 生成 AST =====
from pyverilog.vparser.parser import parse

ast, directives = parse(
    ["my_design.v"],
    preprocess_include=["include/"],
    preprocess_define=["DEFINE_A=1"]
)
print(ast.toCodegen())  # 重新生成 Verilog 代码

for item in ast.description.definitions:
    print(f"Module: {item.name}")
    for port in item.portlist.ports:
        print(f"  Port: {port.first.name}")

# ===== 数据流分析（信号驱动关系）=====
from pyverilog.dataflow.dataflow_analyzer import VerilogDataflowAnalyzer
from pyverilog.dataflow.optimizer import VerilogDataflowOptimizer

analyzer = VerilogDataflowAnalyzer(["design.v"], "top_module")
analyzer.generate()
binddict = analyzer.getBinddict()
termdict = analyzer.getTermdict()

for termname, bind in binddict.items():
    print(f"{termname}: {bind}")

optimizer = VerilogDataflowOptimizer(binddict, termdict)
optimizer.resolveConstant()
resolved = optimizer.getResolvedTermdict()

# ===== 控制流/FSM 分析 =====
from pyverilog.controlflow.controlflow_analyzer import VerilogControlflowAnalyzer

cfa = VerilogControlflowAnalyzer(["fsm_design.v"], "fsm_module")
cfa.generate()
fsm_vars, fsm_table, fsm_transitions = cfa.analyzeFsm()
for state, transitions in fsm_table.items():
    print(f"State {state}: {transitions}")

# ===== 代码生成（AST → Verilog）=====
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator

codegen = ASTCodeGenerator()
verilog_code = codegen.visit(ast)
print(verilog_code)
```

#### 实际使用案例
- **硬件安全分析**：信息流追踪、时序侧信道检测
- **LLM 生成 Verilog 验证**：评估 LLM 输出语法正确性的评测工具
- **形式验证预处理**：rtl2model 工具的 AST 前端
- **flipSyrup**：基于 pyverilog 的 FPGA 原型验证框架（~2700 行 Python）

#### 已知限制
- `generate`/`genvar` 块支持**不完整**（GitHub Issue #43，长期未修复）
- 不支持用户定义原语（UDP）
- SystemVerilog 支持有限（主要针对 Verilog-2001 标准）
- 依赖 Icarus Verilog 做 `` `include ``、`` `define `` 预处理
- 最后正式版本 2020 年，主代码库维护不活跃
- 大型设计（百万行以上）解析性能差

#### MCP 封装难点
- **低**：纯 Python，安装简单，无重量级系统依赖
- API 文档缺失，LLM 难以直接生成正确调用
- 建议封装为具体操作：模块接口提取、端口列表查询、基础数据流分析
- 对复杂设计，推荐使用 Yosys `read_verilog` 替代

---

### 2.9 LibreLane（OpenLane 2 的继任者）

**状态**：生产就绪，2025-08 从 OpenLane 2 正式更名，由 FOSSi Foundation 维护
**历史**：2022 Efabless 开发 → 2024-02 软发布为 OpenLane 2 → 2025-08 Efabless 倒闭后更名 LibreLane
**安装**：Nix（推荐，含完整工具链）或 `pip install librelane`
**文档**：https://librelane.readthedocs.io/en/latest/

#### API 架构
```
librelane.config   → 不可变配置对象（JSON/YAML/Tcl 向后兼容）
librelane.state    → 类型化设计状态（文件路径映射，Step 间传递）
librelane.steps    → 原子化步骤基类（继承实现自定义步骤）
librelane.flows    → 步骤编排基类（继承定制流程顺序）
```

#### 关键 API 调用示例

```python
# ===== 运行标准 RTL-to-GDSII 流程 =====
from librelane.flows.classic import Classic

flow = Classic(
    config={
        "DESIGN_NAME": "spm",
        "VERILOG_FILES": ["src/spm.v"],
        "CLOCK_PORT": "clk",
        "CLOCK_PERIOD": 10.0,
        "PDK": "sky130A",
        "STD_CELL_LIBRARY": "sky130_fd_sc_hd",
    },
    design_dir=".",
    pdk_root="/path/to/pdk",
)
flow.start()
```

```python
# ===== 自定义 Step =====
from librelane.steps import Step
from librelane.state import State
from librelane.config import Variable
import subprocess

class CustomDRC(Step):
    id = "Custom.DRC"
    name = "Custom DRC Check"
    inputs = ["GDS"]
    outputs = ["DRC_RESULTS"]
    config_vars = [
        Variable("CUSTOM_DRC_RULES", str, "Path to DRC rules", default="./rules.drc")
    ]
    def run(self, state_in: State, **kwargs):
        gds_path = state_in["GDS"]
        rules = self.config["CUSTOM_DRC_RULES"]
        subprocess.run(["klayout", "-b", "-r", rules,
                        "-rd", f"input={gds_path}",
                        "-rd", "report=drc_out.lyrdb"], check=True)
        state_out = state_in.copy()
        state_out["DRC_RESULTS"] = "drc_out.lyrdb"
        return state_out, {}

class MyFlow(Classic):
    Steps = Classic.Steps + [CustomDRC]

state = State.from_run_dir("./runs/RUN_2025_01_01")
print(state["GDS"])
```

#### 与 OpenLane 1.x 对比

| 特性 | OpenLane 1.x | LibreLane |
|------|-------------|----------|
| 语言 | Tcl + Makefile | 纯 Python |
| 步骤定制 | 困难（修改 Tcl 脚本）| 简单（继承 Step 类）|
| 流程定制 | 困难 | 简单（重写 Steps 列表）|
| 配置格式 | JSON/Tcl | JSON/YAML/Tcl（向后兼容）|
| 安装 | 依赖 Docker | Nix 或 pip |
| Python API | 无 | 完整 |
| 中间结果 | 散落文件 | State 对象（类型化）|

#### 已知限制
- Nix 安装需要约 30GB 磁盘空间（包含所有 EDA 工具）
- `pip install librelane` 仅安装 Python 框架，OpenROAD/Magic/KLayout 等需单独安装
- 目前主要支持 sky130 和 gf180mcu PDK
- Efabless 平台倒闭（2025-08）影响部分云端流片文档和社区资源
- Windows 不支持（需 Linux/macOS 或 WSL2）

#### MCP 封装难点
- **中等**：Python API 设计清晰，但依赖整个 EDA 工具链
- 推荐方案：预定义流程模板 + Docker/Nix 容器封装
- MCP 工具可暴露：启动流程、查询步骤状态、读取 timing/DRC 报告

---

### 2.10 Magic VLSI

**状态**：无官方 Python API，仅支持 Tcl 脚本（成熟度 2/10）
**版本**：8.3.x（2024 年持续维护，Tim Edwards 主导）
**Python 集成方式**：subprocess 调用 + 解析文本输出

#### 架构说明

Magic 是 1983 年诞生的经典 VLSI 版图编辑器，核心交互语言为 Tcl。没有官方 Python 绑定，也无计划添加。Python 集成唯一可靠方式：
1. 生成 Tcl 脚本文件
2. subprocess 调用 `magic -noconsole -dnull < script.tcl`
3. 解析 Magic 的 stdout/stderr 文本输出
4. 读取 Magic 写出的中间文件（GDS、LEF、SPICE netlist）

#### 关键调用示例（Python + subprocess）

```python
import subprocess, tempfile, os

def magic_run_tcl(tcl_script: str, tech: str = "sky130A") -> tuple:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".tcl",
                                     delete=False, encoding="utf-8") as f:
        f.write(tcl_script)
        tcl_file = f.name
    try:
        result = subprocess.run(
            ["magic", "-noconsole", "-dnull", "-T", tech],
            stdin=open(tcl_file, "r"),
            capture_output=True, text=True, timeout=300
        )
        return result.stdout, result.stderr
    finally:
        os.unlink(tcl_file)

# GDS 转 SPICE（LVS 用）
TCL_GDS_TO_SPICE = """
gds read /path/to/design.gds
load design
extract all
ext2spice hierarchy on
ext2spice format ngspice
ext2spice /path/to/output.spice
quit
"""
stdout, stderr = magic_run_tcl(TCL_GDS_TO_SPICE)

# DRC 检查
TCL_DRC = """
gds read /path/to/design.gds
load design
drc check
drc count
quit
"""
stdout, stderr = magic_run_tcl(TCL_DRC)
for line in stdout.splitlines():
    if "Total DRC errors" in line:
        print(f"DRC: {line}")

# 生成 LEF
TCL_LEF = """
gds read /path/to/design.gds
load design
lef write /path/to/output.lef
quit
"""
magic_run_tcl(TCL_LEF)
```

#### 已知限制
- **无 Python API**：所有操作必须通过 Tcl 脚本或 subprocess
- 批处理模式输出不结构化，解析困难
- DRC/提取结果格式非标准，需自定义解析器
- GUI 功能（截图、交互式编辑）无法在无头模式下使用
- KLayout 在版图查看/DRC 方面已基本取代 Magic，新项目优先选 KLayout
- Windows 不支持，需 Linux 或 WSL2

#### MCP 封装难点
- **极高**：无 Python API，全靠 Tcl 脚本生成 + 文本输出解析
- AUTO_EDA 建议：**不直接封装 Magic**，改用 KLayout 处理同类操作
- 若必须使用（sky130 PDK DRC），封装为黑盒：接受 GDS，返回 DRC 计数和 SPICE


---

## 3. MCP 封装难点综合分析

### 3.1 难度分级汇总

| 工具 | MCP 封装难度 | 核心挑战 | AUTO_EDA 推荐优先级 |
|------|------------|---------|-------------------|
| KLayout pya | 低 | 截图需 GUI/Xvfb，DRC 用 Ruby DSL | ★★★★★ 最高优先 |
| gdstk | 低 | GDS 大文件，需流式摘要 | ★★★★☆ |
| cocotb 2.x | 低-中 | 需管理仿真器安装 | ★★★★☆ |
| pyverilog | 低 | API 文档缺失，功能有限 | ★★★☆☆ |
| KiCad IPC API | 中 | 需 KiCad GUI 进程常驻 | ★★★★★ PCB 最高优先 |
| LibreLane | 中 | 依赖完整工具链 | ★★★★☆ |
| PySpice/ngspice | 中 | 需安装 ngspice 二进制 | ★★★☆☆ |
| OpenROAD | 高 | 必须在 openroad -python 环境运行 | ★★★★☆ |
| Pyosys | 高 | API 文档极少，稳定性差 | ★★☆☆☆ |
| Magic VLSI | 极高 | 无 Python API，纯 Tcl | ★☆☆☆☆ 跳过 |

### 3.2 通用 MCP 封装模式

#### 模式1：脚本生成 + 进程调用（Script-and-Execute）
适用于：OpenROAD、Magic、KLayout（批处理）

MCP Tool 接收参数 → 生成工具脚本（Python/Tcl）→ subprocess 调用 → 解析输出文件/stdout → 返回结构化结果

#### 模式2：进程托管（Persistent Process）
适用于：KiCad IPC API（需要 GUI 进程常驻）

MCP Server 启动时初始化 KiCad 进程，保持连接，Tool 调用通过 NNG socket 通信。

#### 模式3：直接 Python 调用（Native Python）
适用于：gdstk、pyverilog、PySpice、cocotb runner

MCP Tool 直接在同一 Python 进程中 import 并调用，最简单，无进程开销。

#### 模式4：工作流编排（Flow Orchestration）
适用于：LibreLane、复合 OpenROAD 流程

MCP Tool 触发 LibreLane Flow，异步监控进度，分阶段返回结果。

### 3.3 大文件处理策略

EDA 文件（GDS、ODB、网表）可能达 GB 级，不能直接传入 LLM 上下文：

| 文件类型 | 大小范围 | MCP 策略 |
|---------|---------|---------|
| GDSII/OASIS | 100MB-10GB | 提取摘要（层列表、单元数、面积统计）+ 截图缩略图 |
| ODB 数据库 | 10MB-1GB | 通过 OpenROAD Python API 查询，返回摘要 JSON |
| Verilog netlist | 1KB-10MB | 小文件直接传，大文件提取模块接口列表 |
| SPICE netlist | 1KB-10MB | 文本格式，LLM 可读，超过 100KB 则摘要 |
| KiCad .kicad_pcb | 100KB-10MB | S-expression 解析，提取元器件/网络摘要 |

### 3.4 错误处理最佳实践

MCP Tool 返回的错误信息需包含足够上下文帮助 LLM 自我纠错：

```python
# 推荐的 MCP Tool 错误返回格式
def klayout_drc(gds_path: str, rules_file: str) -> dict:
    try:
        result = subprocess.run([...], capture_output=True, timeout=120)
        if result.returncode != 0:
            return {
                "success": False,
                "error": "KLayout DRC failed",
                "details": result.stderr[-2000:],  # 最后 2000 字符
                "command": " ".join(result.args),
                "suggestion": "Check GDS file path and DRC rules file format"
            }
        return {"success": True, "violations": parse_drc_report(...)}
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "DRC timeout after 120s",
            "suggestion": "Design may be too large, try flattening first"
        }
```

---

## 4. 推荐优先级和实施路线图

### 4.1 AUTO_EDA MCP Server 第一阶段（核心功能）

**目标**：覆盖最高价值场景，3 个月内可交付

| 优先级 | MCP Server | 封装工具 | 核心 Tools（5-8个）|
|--------|-----------|---------|-------------------|
| P0 | klayout-mcp | KLayout pya | drc_check, gds_screenshot, layer_stats, boolean_op, gds_to_png |
| P0 | kicad-mcp | KiCad IPC API | list_components, move_footprint, run_drc, export_gerber, get_netlist |
| P1 | openroad-mcp | OpenROAD Python | floorplan, place, route, timing_report, write_gds |
| P1 | cocotb-mcp | cocotb 2.x + Verilator | run_simulation, get_waveform, check_coverage |
| P2 | spice-mcp | PySpice + ngspice | dc_analysis, ac_sweep, transient_sim, plot_result |

### 4.2 第二阶段（扩展功能）

| 优先级 | MCP Server | 封装工具 | 说明 |
|--------|-----------|---------|------|
| P3 | librelane-mcp | LibreLane | RTL-to-GDSII 全流程自动化 |
| P3 | gdstk-mcp | gdstk | 光子学版图生成、参数化单元库 |
| P4 | verilog-mcp | pyverilog + Yosys | RTL 解析、接口提取、综合 |

### 4.3 关键差异化优势

AUTO_EDA 相对现有方案（MCP4EDA）的核心差异：

1. **可视化反馈闭环**：KLayout pya 截图 → LLM 分析 → 修改工具调用 → 再截图验证
2. **PCB 支持**：KiCad IPC API（MCP4EDA 无 PCB）
3. **模拟电路支持**：PySpice/ngspice（MCP4EDA 无 SPICE）
4. **全 Python 实现**：FastMCP + 纯 Python EDA 库，无 TypeScript/CLI 中间层
5. **工作流模板**：可导出/导入/社区共享的 DAG 流程模板

---

## 5. 参考资料

### 官方文档
- KLayout Python API: https://www.klayout.de/doc-qt5/programming/python.html
- cocotb 2.x: https://docs.cocotb.org/en/stable/
- OpenROAD: https://openroad.readthedocs.io/en/latest/
- KiCad IPC API: https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/
- gdstk: https://heitzmann.github.io/gdstk/
- LibreLane: https://librelane.readthedocs.io/en/latest/
- PySpice: https://pyspice.fabrice-salvaire.fr/releases/v1.6/
- pyverilog: https://github.com/PyHDI/Pyverilog
- Pyosys: https://yosyshq.readthedocs.io/projects/yosys/en/latest/using_yosys/pyosys.html

### 学术论文
- Takamaeda-Yamazaki, "Pyverilog: A Python-Based Hardware Design Processing Toolkit", ARC 2015
- ASP-DAC 2024 Tutorial: OpenROAD Python API, https://github.com/ASU-VDA-Lab/ASP-DAC24-Tutorial
- ChipBench: A Benchmark for AI-Assisted Hardware Design, 2025

---

*报告生成时间：2026-03-14 | 调研范围：2024-2026 官方文档、GitHub、学术论文、社区论坛*
