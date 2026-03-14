# DA2: AUTO_EDA 可视化反馈闭环完整技术方案

> 分析日期: 2026-03-14
> 分析师: Agent DA2 (视觉AI分析师)
> 依赖分析: A5_differentiation_strategy.md (USP-3), A7_tech_stack_decision.md
> 状态: 完成

---

## 目录

1. [各EDA工具截图/导出方案](#1-各eda工具截图导出方案)
2. [图像编码和MCP传输](#2-图像编码和mcp传输)
3. [Claude视觉分析能力边界](#3-claude视觉分析能力边界)
4. [反馈循环控制逻辑](#4-反馈循环控制逻辑)
5. [完整实现代码框架](#5-完整实现代码框架)

---

## 1. 各EDA工具截图/导出方案

### 1.1 KiCad 截图：IPC API 导出 PNG/SVG

#### 技术路径

KiCad v9/v10 提供两种截图导出路径：

**路径 A：IPC API（推荐，适用于 KiCad 运行中）**

KiCad v10 的 IPC API 基于 Protobuf over Unix/TCP Socket，支持直接导出当前视图：

```python
# kicad_screenshot.py
import subprocess
import tempfile
from pathlib import Path
from kipy import KiCad  # KiCad Python IPC 客户端库


class KiCadScreenshotCapture:
    """通过 KiCad IPC API 捕获原理图/PCB 截图。"""

    def __init__(self, host: str = "localhost", port: int = 5000) -> None:
        self.kicad = KiCad(host=host, port=port)

    def capture_schematic(self, output_path: str, dpi: int = 150) -> str:
        """导出当前原理图为 PNG。

        KiCad IPC API 调用链:
        1. GetSchematic() → 获取当前原理图对象
        2. ExportSVG() → 导出 SVG
        3. cairosvg 渲染 SVG → PNG
        """
        with self.kicad.connect() as conn:
            sch = conn.schematic.get_schematic()
            svg_data = sch.export_svg()  # 返回 SVG 字节串

        # SVG → PNG（解决 KiCad SVG 字体嵌入问题）
        import cairosvg
        cairosvg.svg2png(
            bytestring=svg_data,
            write_to=output_path,
            dpi=dpi
        )
        return output_path

    def capture_pcb(self, output_path: str,
                    layers: list[str] | None = None,
                    bbox: tuple[float, float, float, float] | None = None,
                    dpi: int = 150) -> str:
        """导出 PCB 布局为 PNG，支持指定图层和区域。

        Args:
            layers: 要渲染的图层列表，如 ["F.Cu", "B.Cu", "F.SilkS"]
            bbox: 裁剪区域 (x_min, y_min, x_max, y_max)，单位 mm
            dpi: 输出分辨率
        """
        with self.kicad.connect() as conn:
            pcb = conn.pcb.get_board()

            export_cfg = {
                "format": "PNG",
                "dpi": dpi,
                "layers": layers or ["F.Cu", "B.Cu", "F.SilkS", "B.SilkS",
                                      "Edge.Cuts"],
            }
            if bbox:
                export_cfg["bbox"] = {
                    "x_min": bbox[0], "y_min": bbox[1],
                    "x_max": bbox[2], "y_max": bbox[3]
                }

            png_data = pcb.export_image(**export_cfg)

        Path(output_path).write_bytes(png_data)
        return output_path
```

**路径 B：CLI Jobsets（无头批处理，KiCad 不必运行）**

```python
import asyncio
import json
import tempfile
from pathlib import Path


async def kicad_export_pcb_png_headless(
    kicad_pcb_path: str,
    output_path: str,
    layers: list[str] | None = None,
    dpi: int = 150
) -> str:
    """无头模式导出 PCB PNG（KiCad 不需运行）。

    使用 kicad-cli pcb export image 命令。
    KiCad 7.0+ 支持，KiCad 8.0+ 完善。
    """
    layers = layers or ["F.Cu", "B.Cu", "Edge.Cuts"]

    cmd = [
        "kicad-cli", "pcb", "export", "image",
        "--output", output_path,
        "--format", "png",
        "--layers", ",".join(layers),
        "--width", "2048",  # 像素宽度
        "--black-and-white",  # 可选：减小文件大小
        kicad_pcb_path,
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30.0)

    if proc.returncode != 0:
        raise RuntimeError(
            f"kicad-cli failed (rc={proc.returncode}): {stderr.decode()}"
        )
    return output_path


async def kicad_export_schematic_svg_headless(
    kicad_sch_path: str,
    output_path: str,
) -> str:
    """无头模式导出原理图 SVG，再转 PNG。"""
    svg_path = output_path.replace(".png", ".svg")

    cmd = [
        "kicad-cli", "sch", "export", "svg",
        "--output", svg_path,
        kicad_sch_path,
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await asyncio.wait_for(proc.communicate(), timeout=30.0)

    # SVG → PNG
    import cairosvg
    cairosvg.svg2png(url=svg_path, write_to=output_path, dpi=150)
    Path(svg_path).unlink(missing_ok=True)  # 清理中间文件
    return output_path
```

**方案选择建议**:
- KiCad 正在运行（GUI 场景）→ IPC API (路径 A)
- 批处理/CI 场景 → CLI Jobsets (路径 B)
- KiCad v7 以下 → pcbnew Python 模块直接调用

---

### 1.2 KLayout 截图：pya.LayoutView API

KLayout 的 Python 绑定 `pya` 提供完整的截图 API，支持无头模式（通过 `klayout -b` 批处理标志）。

```python
# klayout_screenshot.py
from __future__ import annotations

import base64
from pathlib import Path
from typing import NamedTuple


class LayerSpec(NamedTuple):
    layer: int
    datatype: int
    color: str  # 十六进制颜色，如 "#FF0000"
    dither_pattern: int = 0  # KLayout 填充图案 ID


class KLayoutScreenshotCapture:
    """KLayout 版图截图，支持无头模式和 GUI 模式。"""

    def capture_gds_region(
        self,
        gds_path: str,
        output_path: str,
        cell_name: str | None = None,
        bbox: tuple[float, float, float, float] | None = None,
        width_px: int = 1920,
        height_px: int = 1080,
        layer_specs: list[LayerSpec] | None = None,
        dbu: float = 0.001,  # 数据库单位，单位 um（SkyWater130 标准）
    ) -> str:
        """
        使用 KLayout pya API 截取 GDSII 版图区域。

        关键 API 调用链:
        1. pya.Layout() → 加载 GDS 文件
        2. pya.LayoutView() → 创建视图（无头模式）
        3. view.load_layout() → 加载到视图
        4. view.zoom_box() / view.zoom_fit() → 定位视角
        5. view.save_image() → 输出 PNG

        Args:
            bbox: 截图区域 (x1, y1, x2, y2)，单位 um
        """
        try:
            import pya
        except ImportError:
            return self._capture_via_klayout_subprocess(
                gds_path, output_path, cell_name, bbox, width_px, height_px
            )

        # 创建无头 LayoutView
        # pya.Application.instance() 在批处理模式下返回 None
        # 必须使用 pya.LayoutView(True) 创建独立视图（True=无 UI）
        view = pya.LayoutView(True)

        try:
            # 加载 GDS
            layout_index = view.load_layout(gds_path, True)
            view.max_hier()  # 展开所有层次

            # 设置 cell
            if cell_name:
                layout = view.cellview(layout_index).layout()
                cell = layout.cell(cell_name)
                if cell is None:
                    raise ValueError(f"Cell '{cell_name}' not found in {gds_path}")
                view.select_cell(cell.cell_index(), layout_index)

            # 配置图层颜色（可选）
            if layer_specs:
                self._apply_layer_styles(view, layer_specs)

            # 设置视角
            if bbox:
                x1, y1, x2, y2 = bbox
                # KLayout 坐标单位为 dbu，转换: um / dbu
                box = pya.DBox(x1, y1, x2, y2)  # DBox 使用 um 单位
                view.zoom_box(box)
            else:
                view.zoom_fit()  # 自动适配

            # 输出截图
            # save_image(path, width, height)
            view.save_image(output_path, width_px, height_px)

        finally:
            view._destroy()  # 显式释放 C++ 对象，防止内存泄漏

        return output_path

    def _apply_layer_styles(
        self, view: "pya.LayoutView", layer_specs: list[LayerSpec]
    ) -> None:
        """应用自定义图层颜色和填充样式。"""
        import pya
        for li in view.each_layer():
            lp = li.layer_info()
            for spec in layer_specs:
                if lp.layer == spec.layer and lp.datatype == spec.datatype:
                    lnp = li.dup()
                    color = int(spec.color.lstrip("#"), 16)
                    lnp.fill_color = color
                    lnp.frame_color = color
                    lnp.dither_pattern = spec.dither_pattern
                    view.set_layer_properties(li, lnp)
                    break

    def _capture_via_klayout_subprocess(
        self,
        gds_path: str,
        output_path: str,
        cell_name: str | None,
        bbox: tuple[float, float, float, float] | None,
        width_px: int,
        height_px: int,
    ) -> str:
        """回退方案：通过 klayout -b 子进程截图（pya 不可用时）。"""
        import asyncio
        import textwrap
        import tempfile

        script = textwrap.dedent(f"""
            import pya
            view = pya.LayoutView(True)
            view.load_layout("{gds_path}", True)
            view.max_hier()
            {f'view.zoom_box(pya.DBox{bbox})' if bbox else 'view.zoom_fit()'}
            view.save_image("{output_path}", {width_px}, {height_px})
            view._destroy()
        """)

        with tempfile.NamedTemporaryFile(suffix=".py", mode="w",
                                         delete=False) as f:
            f.write(script)
            script_path = f.name

        import subprocess
        subprocess.run(
            ["klayout", "-b", "-r", script_path],
            check=True, timeout=60
        )
        Path(script_path).unlink(missing_ok=True)
        return output_path
```

**大图处理策略**（版图截图可能 >10MB）:

```python
from PIL import Image
from io import BytesIO


def compress_layout_image(
    image_path: str,
    max_bytes: int = 4 * 1024 * 1024,  # 4MB：Claude API 单图上限
    min_dimension: int = 800,
) -> tuple[bytes, str]:
    """压缩版图截图至 Claude API 可接受大小。

    Returns:
        (compressed_bytes, mime_type)
    """
    img = Image.open(image_path)
    original_size = img.size

    # 策略1: 先尝试 JPEG 压缩（版图适合 JPEG，色块大）
    for quality in [85, 70, 55, 40]:
        buf = BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=quality,
                                 optimize=True)
        data = buf.getvalue()
        if len(data) <= max_bytes:
            return data, "image/jpeg"

    # 策略2: 降采样（保持比例，最小边不低于 min_dimension）
    w, h = img.size
    scale = min(max_bytes / len(Path(image_path).read_bytes()), 1.0) ** 0.5
    new_w = max(int(w * scale), min_dimension)
    new_h = max(int(h * scale), min_dimension)
    img_resized = img.resize((new_w, new_h), Image.LANCZOS)

    buf = BytesIO()
    img_resized.convert("RGB").save(buf, format="JPEG", quality=70)
    return buf.getvalue(), "image/jpeg"


---

### 1.3 ngspice 仿真结果：matplotlib 绘图 Pipeline

ngspice 无原生截图 API，通过 PySpice 控制仿真，matplotlib Agg 后端渲染结果图像，无需 X11 显示器。

```python
# ngspice_plot.py
import matplotlib
matplotlib.use("Agg")  # 必须在 import pyplot 之前
import matplotlib.pyplot as plt
import numpy as np
from PySpice.Spice.Netlist import Circuit


class NgspiceVisualizer:
    def run_and_plot_transient(
        self,
        circuit: Circuit,
        step_time: str,
        end_time: str,
        signals: list[str],
        output_path: str,
        title: str = "Transient Analysis",
    ) -> str:
        """
        Pipeline:
          1. PySpice 生成 SPICE 网表
          2. simulator("ngspice-shared") 调用共享库（非子进程，零启动延迟）
          3. analysis.time / analysis[signal] 获取 numpy 数组
          4. matplotlib 多子图 sharex=True 对齐时间轴
          5. savefig(dpi=150) 输出 PNG
        """
        simulator = circuit.simulator(
            simulator="ngspice-shared", temperature=27, nominal_temperature=27
        )
        analysis = simulator.transient(step_time=step_time, end_time=end_time)

        fig, axes = plt.subplots(
            len(signals), 1,
            figsize=(12, max(4, len(signals) * 2)),
            sharex=True,
            gridspec_kw={"hspace": 0.05},
        )
        if len(signals) == 1:
            axes = [axes]

        time_ns = np.array(analysis.time) * 1e9
        for ax, sig_name in zip(axes, signals):
            try:
                values = np.array(analysis[sig_name])
            except KeyError:
                ax.text(0.5, 0.5, f"{sig_name}: not found",
                        ha="center", transform=ax.transAxes, color="red")
                continue
            ax.plot(time_ns, values, linewidth=1.2, color="#2196F3")
            ax.set_ylabel(sig_name, fontsize=9)
            ax.grid(True, alpha=0.3, linestyle="--")

        axes[-1].set_xlabel("Time (ns)", fontsize=10)
        fig.suptitle(title, fontsize=12, fontweight="bold")
        plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return output_path

    def run_and_plot_ac(
        self,
        circuit: Circuit,
        start_frequency: str,
        stop_frequency: str,
        number_of_points: int,
        output_nodes: list[str],
        output_path: str,
    ) -> str:
        """生成 Bode 图（幅频 + 相频双子图）。"""
        simulator = circuit.simulator(simulator="ngspice-shared")
        analysis = simulator.ac(
            variation="dec",
            number_of_points=number_of_points,
            start_frequency=start_frequency,
            stop_frequency=stop_frequency,
        )
        freq = np.array(analysis.frequency)
        fig, (ax_mag, ax_phase) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
        for node in output_nodes:
            v = np.array(analysis[node])
            ax_mag.semilogx(freq, 20 * np.log10(np.abs(v) + 1e-15),
                            label=node, linewidth=1.5)
            ax_phase.semilogx(freq, np.angle(v, deg=True),
                              label=node, linewidth=1.5)
        ax_mag.set_ylabel("Magnitude (dB)")
        ax_mag.grid(True, which="both", alpha=0.3)
        ax_mag.legend()
        ax_phase.set_ylabel("Phase (deg)")
        ax_phase.set_xlabel("Frequency (Hz)")
        ax_phase.grid(True, which="both", alpha=0.3)
        fig.suptitle("AC Analysis - Bode Plot", fontsize=12, fontweight="bold")
        plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return output_path
```

**关键设计决策**:
- `matplotlib.use("Agg")` 必须在首次 `import matplotlib.pyplot` 前调用
- 优先 `ngspice-shared`（共享库）而非子进程，避免每次仿真的进程启动开销
- DPI=150 在 Claude 视觉分析中可清晰识别信号跳变边沿和毛刺

---

### 1.4 Verilator/GTKWave 波形：VCD → 图像转换

**推荐方案：轻量级 VCDParser + matplotlib（零外部 GUI 依赖）**

```python
# vcd_to_image.py
from __future__ import annotations
import re
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


@dataclass
class VCDSignal:
    name: str
    width: int
    symbol: str
    times: list[int] = field(default_factory=list)
    values: list[str] = field(default_factory=list)


class VCDParser:
    """轻量级 VCD 解析器，无外部依赖。"""

    def parse(self, vcd_path: str) -> tuple[int, dict[str, VCDSignal]]:
        """
        VCD 格式关键结构:
          $timescale 1ns $end     <- 时间单位
          $var wire 1 ! clk $end  <- 信号定义: type width symbol name
          #100                    <- 时间戳
          0!                      <- 1bit 值变化: value+symbol
          b1010 @                 <- 多bit 值变化: b+value space+symbol
        """
        signals: dict[str, VCDSignal] = {}
        sym_to_sig: dict[str, VCDSignal] = {}
        timescale_ps = 1000  # 默认 1ns
        current_time = 0

        content = Path(vcd_path).read_text(errors="replace")
        ts_match = re.search(r"(\d+)\s*(fs|ps|ns|us|ms)", content)
        if ts_match:
            val, unit = int(ts_match.group(1)), ts_match.group(2)
            timescale_ps = val * {"fs": 0.001, "ps": 1, "ns": 1000,
                                   "us": 1_000_000, "ms": 1_000_000_000}[unit]

        for line in content.splitlines():
            line = line.strip()
            if line.startswith("$var"):
                parts = line.split()
                if len(parts) >= 5:
                    sig = VCDSignal(name=parts[4], width=int(parts[2]),
                                    symbol=parts[3])
                    signals[parts[4]] = sig
                    sym_to_sig[parts[3]] = sig
            elif line.startswith("#"):
                try:
                    current_time = int(line[1:])
                except ValueError:
                    pass
            elif line and not line.startswith("$"):
                if line[0] in ("0", "1", "x", "z") and len(line) > 1:
                    sym = line[1:]
                    if sym in sym_to_sig:
                        sym_to_sig[sym].times.append(current_time)
                        sym_to_sig[sym].values.append(line[0])
                elif line.startswith("b"):
                    parts = line.split()
                    if len(parts) == 2 and parts[1] in sym_to_sig:
                        sym_to_sig[parts[1]].times.append(current_time)
                        sym_to_sig[parts[1]].values.append(parts[0][1:])

        return int(timescale_ps), signals


def vcd_to_waveform_png(
    vcd_path: str,
    output_path: str,
    signals_to_show: list[str] | None = None,
    time_range: tuple[int, int] | None = None,
    max_signals: int = 16,
) -> str:
    """
    VCD 波形 -> PNG，供 Claude 视觉分析。

    Args:
        signals_to_show: 要显示的信号名，None 则自动选前 max_signals 个
        time_range: 显示时间范围 (start, end)，VCD 时间戳单位
        max_signals: 防止图像过高的信号数上限
    """
    _, all_signals = VCDParser().parse(vcd_path)
    sigs = (
        [all_signals[s] for s in signals_to_show if s in all_signals]
        if signals_to_show else list(all_signals.values())[:max_signals]
    )
    if not sigs:
        raise ValueError("No signals found in VCD file")

    fig, axes = plt.subplots(
        len(sigs), 1,
        figsize=(14, max(4, len(sigs) * 0.8 + 1)),
        sharex=True,
    )
    if len(sigs) == 1:
        axes = [axes]

    for ax, sig in zip(axes, sigs):
        if not sig.times:
            ax.text(0.5, 0.5, "no data", ha="center", transform=ax.transAxes)
        elif sig.width == 1:
            val_map = {"1": 1.0, "0": 0.0}
            vals = [val_map.get(v, 0.5) for v in sig.values]
            ax.step(sig.times, vals, where="post", linewidth=1.5, color="#1976D2")
            ax.set_ylim(-0.2, 1.4)
            ax.set_yticks([0, 1])
            ax.set_yticklabels(["0", "1"], fontsize=7)
        else:
            # 多位总线：彩色色块 + 数值标注
            times = sig.times
            for i, (t0, val) in enumerate(zip(times, sig.values)):
                t1 = times[i + 1] if i + 1 < len(times) else t0 * 1.05
                ax.axvspan(t0, t1, alpha=0.3, color="#4CAF50")
                if (t1 - t0) > (times[-1] - times[0]) * 0.02:
                    ax.text((t0 + t1) / 2, 0.5, val,
                            ha="center", va="center", fontsize=7)
            ax.set_ylim(0, 1)
            ax.set_yticks([])

        ax.set_ylabel(sig.name, fontsize=8, rotation=0, labelpad=55)
        ax.grid(True, axis="x", alpha=0.3, linestyle=":")
        ax.spines[["top", "right"]].set_visible(False)

    axes[-1].set_xlabel("Time (VCD units)", fontsize=9)
    fig.suptitle(f"Waveform: {Path(vcd_path).name}", fontsize=11, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output_path
```

**备用方案：GTKWave TCL 脚本驱动（需 Xvfb）**

```python
async def gtkwave_export_png(
    vcd_path: str, output_path: str, signals: list[str]
) -> str:
    """通过 GTKWave TCL 接口导出波形图（需要 Xvfb 虚拟显示器）。"""
    import asyncio, tempfile
    tcl = (
        f'gtkwave::loadFile "{vcd_path}"\n'
        + "".join(f'gtkwave::addSignalsFromList {{{s}}}\n' for s in signals)
        + f'gtkwave::setZoomFactor -8\ngtkwave::hardcopy png "{output_path}"\n'
    )
    with tempfile.NamedTemporaryFile(suffix=".tcl", mode="w", delete=False) as f:
        f.write(tcl)
        script = f.name
    proc = await asyncio.create_subprocess_exec(
        "xvfb-run", "-a", "gtkwave", "--script", script,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    await asyncio.wait_for(proc.communicate(), timeout=30.0)
    Path(script).unlink(missing_ok=True)
    return output_path
```

**方案选择建议**: 优先 VCDParser+matplotlib（无头服务器零依赖）；仅在需要还原 GTKWave 原生外观时使用 GTKWave 路径。

---

### 1.5 Yosys 电路图：show 命令 → dot → PNG

```python
# yosys_schematic.py
from __future__ import annotations
import asyncio
import tempfile
from pathlib import Path


async def yosys_export_schematic(
    verilog_path: str,
    output_path: str,
    top_module: str | None = None,
    max_nodes: int = 200,
) -> str:
    """
    Yosys show -> dot -> PNG pipeline.

    Steps:
      1. yosys -p "read_verilog; proc; opt; clean; show -format dot -prefix ..."
      2. dot -Tpng -Gdpi=150 schematic.dot -o output.png

    max_nodes: 超过此边数自动降级为层次框图，防止 Graphviz 渲染挂死。
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        dot_prefix = str(Path(tmpdir) / "sch")
        top_flag = f"-top {top_module}" if top_module else ""
        show_target = top_module or ""

        yosys_cmds = ";".join([
            f"read_verilog {verilog_path}",
            f"hierarchy -check {top_flag}",
            "proc; opt; clean",
            f"show -format dot -prefix {dot_prefix} {show_target}",
        ])

        proc = await asyncio.create_subprocess_exec(
            "yosys", "-p", yosys_cmds,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=120.0)
        if proc.returncode != 0:
            raise RuntimeError(f"Yosys failed: {stderr.decode()[:500]}")

        dot_file = f"{dot_prefix}.dot"
        if not Path(dot_file).exists():
            raise FileNotFoundError(f"Yosys did not produce DOT at {dot_file}")

        # 节点数检查（防止超大图 Graphviz 挂死）
        dot_content = Path(dot_file).read_text()
        edge_count = dot_content.count("->")
        if edge_count > max_nodes:
            # 降级：只显示模块层次，不展开门级
            return await _yosys_hierarchy_only(verilog_path, output_path, top_module)

        render = await asyncio.create_subprocess_exec(
            "dot", "-Tpng", "-Gdpi=150", "-o", output_path, dot_file,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        _, render_err = await asyncio.wait_for(render.communicate(), timeout=60.0)
        if render.returncode != 0:
            raise RuntimeError(f"dot failed: {render_err.decode()[:300]}")

    return output_path


async def _yosys_hierarchy_only(
    verilog_path: str, output_path: str, top_module: str | None
) -> str:
    """降级方案：仅输出模块层次框图（不展开内部门级连接）。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        dot_prefix = str(Path(tmpdir) / "hier")
        top_flag = f"-top {top_module}" if top_module else ""
        cmds = ";".join([
            f"read_verilog {verilog_path}",
            f"hierarchy -check {top_flag}",
            f"show -format dot -prefix {dot_prefix} -notitle",
        ])
        proc = await asyncio.create_subprocess_exec(
            "yosys", "-p", cmds,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.wait_for(proc.communicate(), timeout=60.0)
        render = await asyncio.create_subprocess_exec(
            "dot", "-Tpng", "-Gdpi=120", "-o", output_path,
            f"{dot_prefix}.dot",
        )
        await asyncio.wait_for(render.communicate(), timeout=30.0)
    return output_path
```

---

## 2. 图像编码和 MCP 传输

### 2.1 base64 编码效率分析

base64 将二进制数据转 ASCII，**体积膨胀约 33%**（每 3 字节 → 4 字符）。

| 原始图像大小 | base64 后 | Claude 处理方式 | 建议 |
|------------|-----------|----------------|------|
| <512 KB | <683 KB | 直接处理 | 原始 PNG 传输 |
| 512KB–3MB | 683KB–4MB | 接近上限 | JPEG 压缩后传输 |
| 3MB–10MB | >4MB | 超出单图上限 | 必须降采样+JPEG |
| >10MB | 远超限制 | 拒绝接受 | 分块截图策略 |

**Claude API 图像规格限制（2026）**:
- 单张图像 base64 上限：约 5MB
- Claude 内部将长边超过 1568px 的图像自动降采样
- 实际有效像素：约 1568×1568（超出部分信息损失）
- **结论**：截图分辨率设为 1920×1080 即可，不必更高

### 2.2 MCP image content type 使用方式

MCP 协议通过 `ImageContent` 类型传递图像，FastMCP 完整支持：

```python
# mcp_image_transport.py
from __future__ import annotations
import base64
from io import BytesIO
from pathlib import Path
from mcp.types import ImageContent, TextContent
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("auto-eda-visual")


def image_to_mcp_content(
    image_path: str,
    max_long_edge: int = 1568,
    jpeg_quality: int = 82,
) -> ImageContent:
    """
    本地图像 -> MCP ImageContent，自动处理尺寸和格式。

    自动降采样到 max_long_edge（Claude 内部处理上限），
    超过阈值自动转 JPEG 节省传输体积。
    """
    from PIL import Image

    img = Image.open(image_path)
    w, h = img.size

    # 降采样到 Claude 有效分辨率上限
    if max(w, h) > max_long_edge:
        scale = max_long_edge / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    # 格式决策：PNG 用于小图（保留细节），JPEG 用于版图（色块大，压缩率高）
    buf = BytesIO()
    file_size = Path(image_path).stat().st_size
    if file_size > 500_000:  # >500KB 转 JPEG
        img.convert("RGB").save(buf, format="JPEG", quality=jpeg_quality,
                                 optimize=True)
        mime = "image/jpeg"
    else:
        img.save(buf, format="PNG", optimize=True)
        mime = "image/png"

    encoded = base64.standard_b64encode(buf.getvalue()).decode("ascii")
    return ImageContent(type="image", data=encoded, mimeType=mime)


@mcp.tool()
async def capture_layout_screenshot(
    gds_path: str,
    cell_name: str | None = None,
    region_um: list[float] | None = None,
) -> list[TextContent | ImageContent]:
    """
    截取 GDSII 版图区域，返回图像供 Claude 直接分析。

    Args:
        gds_path: GDSII 文件路径
        cell_name: Cell 名称，None 则截顶层
        region_um: [x1,y1,x2,y2] 截图区域（微米），None 则自动适配
    """
    import tempfile
    from auto_eda.visual.klayout_screenshot import KLayoutScreenshotCapture

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp_path = f.name

    bbox = tuple(region_um) if region_um and len(region_um) == 4 else None  # type: ignore
    KLayoutScreenshotCapture().capture_gds_region(
        gds_path=gds_path, output_path=tmp_path,
        cell_name=cell_name, bbox=bbox,
        width_px=1920, height_px=1080,
    )
    img_content = image_to_mcp_content(tmp_path)
    Path(tmp_path).unlink(missing_ok=True)

    final_size_kb = len(img_content.data) * 3 // 4 // 1024
    return [
        TextContent(type="text", text=(
            f"Layout captured: cell='{cell_name or 'top'}', "
            f"region={region_um or 'full'}, "
            f"encoded_size={final_size_kb}KB"
        )),
        img_content,
    ]
```

### 2.3 大图像分块截图策略

对超大版图（全芯片 100MB+），单次截图不可行，需要按需分块：

```python
def plan_layout_tiles(
    gds_path: str,
    cell_name: str,
    tile_size_um: float = 500.0,
    overlap_um: float = 10.0,
) -> list[dict]:
    """
    规划版图分块截图网格，返回元数据列表。
    Claude 可根据分析需要请求特定坐标的图块，而非一次截取整图。

    Returns:
        [{'bbox_um': (x1,y1,x2,y2), 'grid_x': int, 'grid_y': int}, ...]
    """
    import pya
    layout = pya.Layout()
    layout.read(gds_path)
    cell = layout.cell(cell_name)
    if cell is None:
        raise ValueError(f"Cell '{cell_name}' not found")
    bb = cell.dbbox()  # pya.DBox，单位 um

    tiles = []
    x = bb.left
    while x < bb.right:
        y = bb.bottom
        while y < bb.top:
            tiles.append({
                "bbox_um": (
                    x - overlap_um, y - overlap_um,
                    min(x + tile_size_um + overlap_um, bb.right),
                    min(y + tile_size_um + overlap_um, bb.top),
                ),
                "grid_x": int((x - bb.left) / tile_size_um),
                "grid_y": int((y - bb.bottom) / tile_size_um),
            })
            y += tile_size_um
        x += tile_size_um
    return tiles
```

---

## 3. Claude 视觉分析能力边界

### 3.1 Claude 多模态能力对 EDA 图形的理解深度

| EDA 图形类型 | 理解可靠度 | 原因分析 |
|-------------|-----------|----------|
| PCB 布局俯视图 | ★★★★☆ | 结构清晰，元件轮廓/铜箔颜色对比明显 |
| 电路原理图 | ★★★★☆ | 标准符号与通用技术图纸接近 |
| 数字波形图（方波） | ★★★★★ | 高对比度方波边沿极易识别 |
| Bode 图/频响曲线 | ★★★★☆ | 与标准工程图表相似 |
| RTL 层次框图 | ★★★☆☆ | 框图+箭头通用，但 EDA 语义需提示 |
| GDSII 版图（彩色层） | ★★★☆☆ | 几何形状可识别，层含义需上下文 |
| 门级网表图（DOT渲染）| ★★★☆☆ | 节点/边结构可识别，但门符号需提示 |
| DRC 错误标记 | ★★★★☆ | 高亮红色框在浅色背景对比度高 |
| 布线拥塞热图 | ★★★★☆ | 热力图颜色梯度是通用视觉语言 |
| 时序路径图 | ★★☆☆☆ | EDA 专有，依赖大量领域知识 |

### 3.2 可靠识别的视觉特征

**异常标记类**: 红色/橙色高亮区域（DRC violation markers）、叉号/感叹号图标、颜色异常区域

**布局密度类**: 拥塞热图颜色梯度（深红=高拥塞）、空白 vs 密集区域分布、布线方向规律性

**波形特征类**: 方波上升/下降沿时刻、脉冲宽度比较、信号稳定 vs 振荡区域、多信号相位关系

**电路结构类**: 元件对称性、连接密度差异、层次框图子模块边界

### 3.3 需要结构化数据辅助的场景

| 场景 | 纯视觉局限 | 必需的辅助数据 |
|------|-----------|---------------|
| 精确时序违规量化 | 无法读取 slack 精确值 | OpenSTA 文本报告 |
| DRC 违规类型分类 | 只能定位区域，无法判断规则类型 | DRC 错误列表（rule+location）|
| 网表连接正确性 | 无法追踪信号路径 | Verilog 网表或连接矩阵 |
| 版图 LVS 状态 | 无法比较原理图与版图 | LVS 报告文本 |
| 信号精确电压值 | 波形图中精度受限 | ngspice 数值仿真数据 |
| 时钟域交叉问题 | 视觉上难以区分 | 时钟域划分标注 |

**实现原则**: 视觉图像与结构化数据互补传递，不互相替代。

### 3.4 Prompt 工程：引导 Claude 分析 EDA 图形

```python
# eda_visual_prompts.py
from string import Template

LAYOUT_ANALYSIS_PROMPT = Template("""
You are analyzing a chip layout image from KLayout.
Technology: $technology | Cell: $cell_name | Region: $region_description
Layer colors: $layer_colors (e.g. Metal1=blue, Metal2=red, Poly=green)

Analyze and report each finding as: location | severity(info/warning/error) | action
1. CONGESTION: Dense overlapping routing lines. Rate: low/medium/high/critical.
2. DRC_MARKERS: Highlighted regions, red boxes, violation indicators.
3. SYMMETRY: Layout symmetry assessment (for analog cells).
4. EMPTY_AREAS: Significant empty regions that could be compacted.
5. ANOMALIES: Any unusual patterns that appear incorrect.
""")

WAVEFORM_ANALYSIS_PROMPT = Template("""
You are analyzing a digital waveform from simulation.
Module: $module_name | Clock period: $clock_period | Tool: $sim_tool
Signals (top to bottom): $signal_list
Expected behavior: $expected_behavior

Analyze:
1. TIMING_VIOLATIONS: Signals changing too close to clock edges.
2. GLITCHES: Narrow pulses shorter than minimum pulse width.
3. FUNCTIONAL_ERRORS: Transitions not matching expected behavior.
4. METASTABILITY: Signals oscillating or stabilizing slowly.
5. CLOCK_INTEGRITY: Clock regularity and frequency consistency.
""")

PCB_LAYOUT_ANALYSIS_PROMPT = Template("""
You are analyzing a PCB layout from KiCad.
Board: $board_size | Layers: $layers
Design rules: trace_min=$trace_min, clearance_min=$clearance_min

Analyze:
1. COMPONENT_PLACEMENT: Decoupling caps near power pins of ICs.
2. ROUTING_DENSITY: Congested routing areas.
3. THERMAL: Power components needing thermal relief.
4. EMI_RISKS: Long parallel traces, loop antenna formation.
5. MANUFACTURABILITY: Components too close to board edges.
""")
```

**关键 prompt 工程原则**:
1. 提供层颜色映射：告知 Claude 每种颜色对应的层，是版图分析的前提
2. 明确预期行为：波形分析时说明预期时序，Claude 才能判断异常
3. 分点结构化输出：固定格式（位置/严重度/建议），便于后续自动解析
4. 限制分析范围：针对具体关注点，避免过于宽泛的问题

---

## 4. 反馈循环控制逻辑

### 4.1 循环终止条件设计

```python
# feedback_loop_controller.py
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Awaitable
import time


class TerminationReason(Enum):
    SUCCESS = "success"           # 目标达成
    MAX_ITERATIONS = "max_iter"   # 超过最大迭代次数
    TIMEOUT = "timeout"           # 超过总时间限制
    NO_PROGRESS = "no_progress"   # 连续多次无改善
    TOOL_ERROR = "tool_error"     # EDA 工具返回不可恢复错误
    DIVERGING = "diverging"       # 指标持续恶化


@dataclass
class IterationResult:
    iteration: int
    image_path: str
    analysis_text: str           # Claude 分析文本
    metrics: dict[str, float]    # 量化指标（如 DRC 违规数、时序 slack）
    actions_taken: list[str]     # 本轮执行的修改动作
    improvement: float           # 相对上轮的改善量（正数=改善）


@dataclass
class FeedbackLoopConfig:
    max_iterations: int = 10          # 绝对迭代上限
    timeout_seconds: float = 600.0   # 总超时（10分钟）
    no_progress_patience: int = 3     # 连续无改善轮次后终止
    min_improvement_threshold: float = 0.01  # 最小有效改善量（1%）
    divergence_threshold: float = 0.2        # 恶化超过20%视为发散


class VisualFeedbackLoop:
    """
    可视化反馈闭环控制器。

    Loop 结构:
        while not terminated:
            1. capture() -> image
            2. analyze(image) -> metrics + actions
            3. check_termination(metrics)
            4. execute(actions) -> tool results
            5. record(iteration_result)
    """

    def __init__(self, config: FeedbackLoopConfig | None = None) -> None:
        self.config = config or FeedbackLoopConfig()
        self.history: list[IterationResult] = []
        self._start_time: float = 0.0
        self._no_progress_count: int = 0

    async def run(
        self,
        capture_fn: Callable[[], Awaitable[str]],
        analyze_fn: Callable[[str], Awaitable[tuple[str, dict[str, float], list[str]]]],
        execute_fn: Callable[[list[str]], Awaitable[bool]],
        success_fn: Callable[[dict[str, float]], bool],
    ) -> tuple[TerminationReason, list[IterationResult]]:
        """
        运行反馈闭环。

        Args:
            capture_fn: 截图函数，返回图像路径
            analyze_fn: 分析函数，输入图像路径，返回 (分析文本, 指标字典, 动作列表)
            execute_fn: 执行函数，输入动作列表，返回是否成功
            success_fn: 成功判定函数，输入当前指标，返回是否达成目标

        Returns:
            (终止原因, 迭代历史)
        """
        self._start_time = time.monotonic()
        prev_score: float | None = None

        for iteration in range(1, self.config.max_iterations + 1):
            # 超时检查
            elapsed = time.monotonic() - self._start_time
            if elapsed > self.config.timeout_seconds:
                return TerminationReason.TIMEOUT, self.history

            # 截图
            image_path = await capture_fn()

            # Claude 视觉分析
            analysis_text, metrics, actions = await analyze_fn(image_path)

            # 计算改善量（以第一个指标为主要评分）
            primary_metric = next(iter(metrics.values()), 0.0)
            improvement = (
                (prev_score - primary_metric) / (abs(prev_score) + 1e-9)
                if prev_score is not None else 0.0
            )

            result = IterationResult(
                iteration=iteration,
                image_path=image_path,
                analysis_text=analysis_text,
                metrics=metrics,
                actions_taken=actions,
                improvement=improvement,
            )
            self.history.append(result)

            # 成功判定
            if success_fn(metrics):
                return TerminationReason.SUCCESS, self.history

            # 进展检测
            if prev_score is not None:
                if improvement < self.config.min_improvement_threshold:
                    self._no_progress_count += 1
                else:
                    self._no_progress_count = 0

                if self._no_progress_count >= self.config.no_progress_patience:
                    return TerminationReason.NO_PROGRESS, self.history

                # 发散检测：指标持续恶化超过阈值
                if improvement < -self.config.divergence_threshold:
                    return TerminationReason.DIVERGING, self.history

            prev_score = primary_metric

            # 无可执行动作时跳出（Claude 认为无需修改）
            if not actions:
                return TerminationReason.SUCCESS, self.history

            # 执行修改
            success = await execute_fn(actions)
            if not success:
                return TerminationReason.TOOL_ERROR, self.history

        return TerminationReason.MAX_ITERATIONS, self.history
```

### 4.2 进展检测：防止无效循环

```python
class ProgressDetector:
    """
    多维度进展检测，防止 Claude 陷入无效修改循环。

    策略:
    1. 指标变化检测（主要）
    2. 动作去重检测（防止重复同一操作）
    3. 图像相似度检测（防止截图无变化）
    """

    def __init__(self, similarity_threshold: float = 0.98) -> None:
        self.action_history: list[frozenset[str]] = []
        self.similarity_threshold = similarity_threshold

    def is_action_repeated(self, new_actions: list[str]) -> bool:
        """检测本轮动作是否与最近两轮完全相同（无限循环征兆）。"""
        new_set = frozenset(new_actions)
        if len(self.action_history) >= 2:
            if new_set in self.action_history[-2:]:
                return True
        self.action_history.append(new_set)
        return False

    def images_are_identical(
        self, image_path_a: str, image_path_b: str
    ) -> bool:
        """
        图像相似度检测：若两张截图几乎相同，说明执行动作未生效。
        使用像素哈希而非全像素比较，速度快。
        """
        from PIL import Image
        import hashlib

        def img_hash(path: str) -> str:
            img = Image.open(path).resize((64, 64)).convert("L")
            return hashlib.md5(img.tobytes()).hexdigest()

        return img_hash(image_path_a) == img_hash(image_path_b)
```

### 4.3 循环终止后的处理

```python
def summarize_loop_result(
    reason: TerminationReason,
    history: list[IterationResult],
) -> dict:
    """
    将反馈循环结果整理为结构化摘要，供 Claude 最终报告使用。
    """
    if not history:
        return {"status": "no_iterations", "reason": reason.value}

    first = history[0]
    last = history[-1]
    total_improvement = (
        (first.metrics.get("primary", 0) - last.metrics.get("primary", 0))
        / (abs(first.metrics.get("primary", 1)) + 1e-9)
    )

    return {
        "status": reason.value,
        "iterations_completed": len(history),
        "total_improvement_pct": round(total_improvement * 100, 1),
        "initial_metrics": first.metrics,
        "final_metrics": last.metrics,
        "all_actions": [a for r in history for a in r.actions_taken],
        "convergence_trend": [
            {"iter": r.iteration, "improvement": round(r.improvement, 4)}
            for r in history
        ],
    }
```

---

## 5. 完整实现代码框架

### 5.1 视觉反馈 MCP 工具的 Python 实现框架

模块结构:

```
auto_eda/visual/
    __init__.py
    feedback_engine.py        # FastMCP 工具入口（MCP tool 定义）
    feedback_loop_controller.py  # 循环控制逻辑
    klayout_screenshot.py     # KLayout pya 截图
    kicad_screenshot.py       # KiCad IPC API / CLI 截图
    ngspice_plot.py           # PySpice + matplotlib 仿真图
    vcd_to_image.py           # VCD 波形渲染
    yosys_schematic.py        # Yosys show -> dot -> PNG
    tool_executors.py         # 各工具执行器抽象层
    eda_visual_prompts.py     # Claude 分析 prompt 模板
```

```python
# auto_eda/visual/feedback_engine.py
from __future__ import annotations
import asyncio, base64, tempfile
from io import BytesIO
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from mcp.types import ImageContent, TextContent
from pydantic import BaseModel, Field

mcp = FastMCP("auto-eda-visual",
              description="Visual feedback engine for EDA tools")


def _encode_image(image_path: str, max_long_edge: int = 1568,
                  jpeg_quality: int = 82) -> ImageContent:
    """统一图像编码：自动降采样到 Claude 有效分辨率上限，超大图转 JPEG。"""
    from PIL import Image
    img = Image.open(image_path)
    w, h = img.size
    if max(w, h) > max_long_edge:
        scale = max_long_edge / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    buf = BytesIO()
    if Path(image_path).stat().st_size > 500_000:
        img.convert("RGB").save(buf, "JPEG", quality=jpeg_quality, optimize=True)
        mime = "image/jpeg"
    else:
        img.save(buf, "PNG", optimize=True)
        mime = "image/png"
    data = base64.standard_b64encode(buf.getvalue()).decode("ascii")
    return ImageContent(type="image", data=data, mimeType=mime)


# --- Tool 1: KLayout layout screenshot ---

class LayoutScreenshotArgs(BaseModel):
    gds_path: str = Field(description="Path to GDSII/OASIS file")
    cell_name: str | None = Field(None, description="Cell name; None = top cell")
    region_um: list[float] | None = Field(
        None, description="[x1,y1,x2,y2] in micrometers")
    width_px: int = Field(1920)
    height_px: int = Field(1080)


@mcp.tool()
async def capture_layout_screenshot(
    args: LayoutScreenshotArgs,
) -> list[TextContent | ImageContent]:
    """Capture GDSII layout screenshot via KLayout Python API."""
    from auto_eda.visual.klayout_screenshot import KLayoutScreenshotCapture
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp = f.name
    bbox = tuple(args.region_um) if args.region_um else None  # type: ignore
    try:
        KLayoutScreenshotCapture().capture_gds_region(
            gds_path=args.gds_path, output_path=tmp,
            cell_name=args.cell_name, bbox=bbox,
            width_px=args.width_px, height_px=args.height_px,
        )
        img = _encode_image(tmp)
    finally:
        Path(tmp).unlink(missing_ok=True)
    kb = len(img.data) * 3 // 4 // 1024
    return [
        TextContent(type="text", text=(
            f"Layout: cell={args.cell_name or 'top'}, "
            f"region={args.region_um or 'full'}, {kb}KB")),
        img,
    ]


# --- Tool 2: VCD waveform image ---

@mcp.tool()
async def capture_waveform_image(
    vcd_path: str,
    signals: list[str] | None = None,
    max_signals: int = 16,
) -> list[TextContent | ImageContent]:
    """Render VCD waveform as PNG for visual analysis."""
    from auto_eda.visual.vcd_to_image import vcd_to_waveform_png
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp = f.name
    try:
        vcd_to_waveform_png(vcd_path=vcd_path, output_path=tmp,
                            signals_to_show=signals, max_signals=max_signals)
        img = _encode_image(tmp)
    finally:
        Path(tmp).unlink(missing_ok=True)
    return [TextContent(type="text",
                        text=f"Waveform: {Path(vcd_path).name}"), img]


# --- Tool 3: ngspice simulation plot ---

@mcp.tool()
async def capture_ngspice_plot(
    netlist_path: str,
    analysis_type: str,
    signals: list[str],
    params: dict[str, str] | None = None,
) -> list[TextContent | ImageContent]:
    """Run ngspice and return simulation plot image."""
    from auto_eda.visual.ngspice_plot import run_spice_and_plot
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp = f.name
    try:
        run_spice_and_plot(netlist_path=netlist_path,
                           analysis_type=analysis_type,
                           signals=signals, output_path=tmp,
                           **(params or {}))
        img = _encode_image(tmp)
    finally:
        Path(tmp).unlink(missing_ok=True)
    return [TextContent(type="text",
                        text=f"ngspice {analysis_type} plot"), img]


# --- Tool 4: Yosys gate-level schematic ---

@mcp.tool()
async def capture_yosys_schematic(
    verilog_path: str,
    top_module: str | None = None,
    max_nodes: int = 200,
) -> list[TextContent | ImageContent]:
    """Export Yosys schematic: show -> dot -> PNG."""
    from auto_eda.visual.yosys_schematic import yosys_export_schematic
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp = f.name
    try:
        await yosys_export_schematic(
            verilog_path=verilog_path, output_path=tmp,
            top_module=top_module, max_nodes=max_nodes)
        img = _encode_image(tmp)
    finally:
        Path(tmp).unlink(missing_ok=True)
    return [TextContent(type="text",
                        text=f"Yosys: {top_module or 'top'}"), img]


# --- Tool 5: Full visual feedback loop ---

class FeedbackLoopArgs(BaseModel):
    task: str = Field(description="Optimization goal description")
    tool: str = Field(description="EDA tool: klayout|kicad_pcb|ngspice|yosys")
    target_file: str = Field(description="Primary design file path")
    success_criteria: dict[str, float] = Field(
        description="Metric thresholds, e.g. {drc_violations: 0}")
    max_iterations: int = Field(8)
    timeout_seconds: float = Field(300.0)


@mcp.tool()
async def run_visual_feedback_loop(
    args: FeedbackLoopArgs,
) -> list[TextContent]:
    """
    Run complete visual feedback loop for automated EDA optimization.

    Loop:
      capture screenshot -> Claude analyzes -> extract actions
      -> execute via EDA API -> repeat until success or termination
    """
    from auto_eda.visual.feedback_loop_controller import (
        FeedbackLoopConfig, VisualFeedbackLoop, summarize_loop_result)
    from auto_eda.visual.tool_executors import get_executor
    from auto_eda.visual.eda_visual_prompts import get_analysis_prompt
    import json

    config = FeedbackLoopConfig(
        max_iterations=args.max_iterations,
        timeout_seconds=args.timeout_seconds,
    )
    executor = get_executor(args.tool, args.target_file)
    loop = VisualFeedbackLoop(config)
    prompt = get_analysis_prompt(args.tool, args.task)

    reason, history = await loop.run(
        capture_fn=executor.capture_screenshot,
        analyze_fn=lambda p: executor.analyze_with_claude(p, prompt),
        execute_fn=executor.execute_actions,
        success_fn=lambda m: all(
            m.get(k, float("inf")) <= v
            for k, v in args.success_criteria.items()),
    )
    summary = summarize_loop_result(reason, history)
    return [TextContent(type="text", text=(
        f"Loop completed: {reason.value}\n"
        f"Iterations: {summary['iterations_completed']}\n"
        f"Improvement: {summary['total_improvement_pct']}%\n"
        f"Final metrics: {json.dumps(summary['final_metrics'], indent=2)}"
    ))]
```

### 5.2 与各 EDA Server 的集成接口

```python
# auto_eda/visual/tool_executors.py
from __future__ import annotations
from abc import ABC, abstractmethod
import re
import asyncio
import tempfile
from pathlib import Path


class BaseEDAExecutor(ABC):
    def __init__(self, target_file: str) -> None:
        self.target_file = target_file

    @abstractmethod
    async def capture_screenshot(self) -> str: ...

    @abstractmethod
    def extract_metrics(self, analysis_text: str) -> dict[str, float]: ...

    @abstractmethod
    def extract_actions(self, analysis_text: str) -> list[str]: ...

    @abstractmethod
    async def execute_actions(self, actions: list[str]) -> bool: ...

    async def analyze_with_claude(self, image_path: str, prompt: str) -> str:
        """
        MCP sampling API 调用点（生产实现）。
        通过 FastMCP context.sample() 将图像发回 LLM 进行分析。

        示例（在 FastMCP context 内）:
            result = await ctx.sample(
                messages=[{"role": "user", "content": [
                    {"type": "image", "source": {"type": "base64",
                     "media_type": "image/jpeg", "data": encoded}},
                    {"type": "text", "text": prompt}
                ]}]
            )
            return result.content[0].text
        """
        raise NotImplementedError


class KLayoutExecutor(BaseEDAExecutor):
    """KLayout DRC/版图修复执行器。"""

    async def capture_screenshot(self) -> str:
        from auto_eda.visual.klayout_screenshot import KLayoutScreenshotCapture
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp = f.name
        KLayoutScreenshotCapture().capture_gds_region(
            gds_path=self.target_file, output_path=tmp,
            width_px=1920, height_px=1080)
        return tmp

    def extract_metrics(self, analysis_text: str) -> dict[str, float]:
        # 约定: Claude 输出格式 "DRC_MARKERS: N violations found"
        m = re.search(r"DRC_MARKERS[^\n]*?(\d+)\s*violation",
                      analysis_text, re.IGNORECASE)
        return {"drc_violations": float(m.group(1)) if m else 0.0}

    def extract_actions(self, analysis_text: str) -> list[str]:
        # 约定: Claude 输出格式 "action: <klayout_python_expr>"
        return [a.strip() for a in re.findall(
            r"(?:action|fix|cmd):\s*(.+)", analysis_text, re.IGNORECASE)]

    async def execute_actions(self, actions: list[str]) -> bool:
        if not actions:
            return True
        script_lines = [
            "import pya",
            f'lv = pya.LayoutView(True); lv.load_layout("{self.target_file}", True)',
        ] + actions + [f'lv._destroy()']
        with tempfile.NamedTemporaryFile(
                suffix=".py", mode="w", delete=False) as f:
            f.write("\n".join(script_lines))
            script_path = f.name
        proc = await asyncio.create_subprocess_exec(
            "klayout", "-b", "-r", script_path,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await asyncio.wait_for(proc.communicate(), timeout=120.0)
        Path(script_path).unlink(missing_ok=True)
        return proc.returncode == 0


class KiCadPCBExecutor(BaseEDAExecutor):
    """KiCad PCB 执行器（通过 IPC API 或 kicad-cli）。"""

    async def capture_screenshot(self) -> str:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp = f.name
        from auto_eda.visual.kicad_screenshot import kicad_export_pcb_png_headless
        await kicad_export_pcb_png_headless(
            kicad_pcb_path=self.target_file, output_path=tmp)
        return tmp

    def extract_metrics(self, analysis_text: str) -> dict[str, float]:
        m = re.search(r"ROUTING_DENSITY[^\n]*?(\d+(?:\.\d+)?)%",
                      analysis_text, re.IGNORECASE)
        density = float(m.group(1)) if m else 0.0
        err = re.search(r"(\d+)\s*error", analysis_text, re.IGNORECASE)
        return {"routing_density_pct": density,
                "errors": float(err.group(1)) if err else 0.0}

    def extract_actions(self, analysis_text: str) -> list[str]:
        return [a.strip() for a in re.findall(
            r"action:\s*(.+)", analysis_text, re.IGNORECASE)]

    async def execute_actions(self, actions: list[str]) -> bool:
        # KiCad IPC API 执行（占位，实际通过 kipy 客户端）
        return True


class NgSpiceExecutor(BaseEDAExecutor):
    """ngspice 仿真执行器。"""

    async def capture_screenshot(self) -> str:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp = f.name
        from auto_eda.visual.ngspice_plot import run_spice_and_plot
        run_spice_and_plot(self.target_file, "transient", [], tmp)
        return tmp

    def extract_metrics(self, analysis_text: str) -> dict[str, float]:
        m = re.search(r"GLITCHES[^\n]*?(\d+)", analysis_text, re.IGNORECASE)
        return {"glitches": float(m.group(1)) if m else 0.0}

    def extract_actions(self, analysis_text: str) -> list[str]:
        return [a.strip() for a in re.findall(
            r"action:\s*(.+)", analysis_text, re.IGNORECASE)]

    async def execute_actions(self, actions: list[str]) -> bool:
        return True


def get_executor(tool: str, target_file: str) -> BaseEDAExecutor:
    """工厂函数：根据工具名返回对应执行器。"""
    mapping: dict[str, type[BaseEDAExecutor]] = {
        "klayout": KLayoutExecutor,
        "kicad_pcb": KiCadPCBExecutor,
        "ngspice": NgSpiceExecutor,
    }
    cls = mapping.get(tool)
    if cls is None:
        raise ValueError(f"Unknown tool: {tool!r}. Available: {list(mapping)}")
    return cls(target_file)
```

---

## 总结：关键技术决策矩阵

| 技术问题 | 决策 | 理由 |
|---------|------|------|
| KiCad 截图方案 | IPC API（运行中）+ kicad-cli（批处理）双轨 | IPC API 实时性强，CLI 无头服务器友好 |
| KLayout 截图 | pya.LayoutView(True) 无头模式，klayout -b 子进程回退 | 原生 Python，无 GUI 依赖，支持批处理 |
| ngspice 可视化 | PySpice ngspice-shared + matplotlib Agg | 共享库零进程开销，Agg 无需 X11 |
| VCD 波形渲染 | 自研 VCDParser + matplotlib（GTKWave 备用） | 零外部 GUI 依赖，服务器环境直接运行 |
| Yosys 电路图 | show -format dot + Graphviz dot -Tpng | 原生支持，超大图自动降级为层次框图 |
| 图像尺寸上限 | 长边 1568px + JPEG 质量 82 | Claude 内部处理上限，JPEG 压缩率高 |
| 大版图处理 | 分块截图（500um/块，10um 重叠） | 按需请求图块，避免单次超大图传输 |
| MCP 传输格式 | ImageContent(base64, mimeType) | MCP 协议原生支持，FastMCP 完整集成 |
| 循环终止 | 6 条件：成功/超次/超时/无进展/工具错误/发散 | 多重保护防止无效循环消耗资源 |
| 进展检测 | 指标变化 + 动作去重 + 图像哈希三重检测 | 防止 Claude 陷入重复相同动作的循环 |
| Prompt 结构 | 分点结构化输出（位置/严重度/action 行） | 便于正则提取 metrics 和 actions |

---

## 实施优先级

| 优先级 | 组件 | 依赖 | 预估工期 |
|--------|------|------|----------|
| P0 | KLayout 截图 + MCP ImageContent 传输 | pya, Pillow | 1 周 |
| P0 | VCD → matplotlib 波形图 | matplotlib, numpy | 3 天 |
| P0 | ngspice 瞬态/AC 绘图 | PySpice, matplotlib | 3 天 |
| P1 | KiCad PCB/原理图截图（CLI 路径） | kicad-cli, cairosvg | 1 周 |
| P1 | Yosys show → dot → PNG | yosys, graphviz | 3 天 |
| P1 | 反馈循环控制器（FeedbackLoopController） | asyncio | 1 周 |
| P2 | KiCad IPC API 截图（实时路径） | kipy | 1-2 周 |
| P2 | 分块截图策略（超大版图） | pya | 1 周 |
| P2 | EDA Visual Prompt 模板库 | — | 3 天 |