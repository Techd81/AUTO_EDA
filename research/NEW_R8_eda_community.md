# 开源EDA社区生态调研报告

> 调研日期：2026-03-14  
> 数据截止：2025年底 / 2026年初

---

## 1. 开源EDA社区规模数据表

### 1.1 主要工具 GitHub 数据（2026年初）

| 工具 | 主要仓库 | Stars | Forks | 定位 | 活跃度 |
|------|----------|-------|-------|------|--------|
| **Yosys** | YosysHQ/yosys | ~4,300 | ~1,100 | RTL综合 | 高（2026年3月发布v0.63）|
| **KiCad** | KiCad/kicad-source-mirror（镜像）| ~2,600 | ~599 | PCB设计 | 高（主库在GitLab）|
| **OpenROAD** | The-OpenROAD-Project/OpenROAD | ~2,500 | ~831 | RTL-to-GDSII | 高（持续更新）|
| **Magic** | RTimothyEdwards/magic | ~620 | ~136 | IC版图 | 高（v8.3.620）|
| **ngspice** | ngspice/ngspice | ~220 | — | SPICE仿真 | 低（GitHub为旧镜像）|
| **LibreLane** | librelane/librelane | 新项目 | — | OpenLane后继者 | 高（2025年由FOSSi发布）|

> 注：KiCad主要开发在 gitlab.com/kicad/code/kicad，GitHub为镜像。
> ngspice GitHub镜像2015年后未更新，主力在SourceForge。

### 1.2 KiCad 社区详细数据

| 指标 | 数据 | 来源/时间 |
|------|------|----------|
| GitHub镜像贡献者 | ~640人（累计）| GitHub, 2026初 |
| v9.0.0 commits | 4,870个独特提交 | kicad.org博客, 2025.02 |
| v9新增内容 | ~1,500符号, ~750封装, 132个3D模型 | kicad.org, 2025.02 |
| 年度捐款者 | 每年>2,500人 | 年度筹款活动 |
| 年度筹款 | ~$100k+/年 | 2024/2025筹款报告 |
| 核心开发团队 | ~14名主导开发者 + 18名库管理员 | v9发布说明 |
| 工厂使用占比 | Aisler上~42%（2023.12）；OSH Park上37% | 各平台统计 |
| 用户规模估计 | 无官方数字；历史累计下载>25万次 | 社区讨论 |
| 版本节奏 | v8: 2024.01；v9: 2025.02；v10: 预计2026.02 | 官方发布 |
| 重要活动 | KiCon Asia 2025（亚洲市场显著增长）| 社区 |

### 1.3 OpenROAD 生态数据

| 指标 | 数据 | 来源/时间 |
|------|------|----------|
| GitHub Stars | ~2,500 | 2026初 |
| 已支持tapeout数 | >600次（历史累计，多节点180nm-12nm）| 官方2024报告 |
| 2024年培训学生 | >5,000人（印度IITG/VTU项目）| 2024年报告 |
| TinyTapeout设计数 | 1,233+（2025年各批次合计）| tinytapeout.com |
| IHP MPW shuttle | 多批次（SG13G2），60+设计/批次 | IHP官方 |
| 主要工业采用者 | Ascenium（RISC-V CPU探索）、ChipFlow | 2024报告 |
| PPA改进 | CTS提升45%、天线修复等 | 2024年报告PDF |
| 可持续支持 | Precision Innovations（DARPA后续）| 2024年报告 |

### 1.4 TinyTapeout 2025 批次统计

| 批次 | 设计数 | 工艺 | 状态（截至2026.03）|
|------|--------|------|-------------------|
| TTIHP25a | 547 | IHP SG13G2 | 芯片预计2026.02交付 |
| TTSKY25a | 237 | SKY130 | 已关闭 |
| TTSKY25b | 316 | SKY130 | 已关闭 |
| TTIHP25b | 81 | IHP SG13G2 | 已关闭 |
| TTGF0p2（测试）| 52 | GF | 已关闭 |
| **合计2025** | **~1,233** | 3个工厂 | — |
| TTIHP26a | 开放中 | IHP | 已满额，2026.03关闭 |
| TTSKY26a | 开放中 | SKY130 | 招募中 |

### 1.5 efabless/ChipFoundry 动态

| 事件 | 时间 | 影响 |
|------|------|------|
| Efabless宣布关停 | 2025年3月初 | TT08/TT09等设计受阻 |
| 失败原因 | B轮融资失败 | 数百开源项目进入不确定期 |
| ChipFoundry收购资产 | 2025年9月（GlobeNewswire）| IP、专利、chipIgnite平台续存 |
| ChipFoundry chipIgnite定价 | $14,950/项目（含100颗封装芯片）| 相比原$9,750涨价 |
| LibreLane发布 | 2025年7月/8月 | OpenLane的FOSSi官方继承者 |
| TinyTapeout恢复 | 2025年中（转向IHP等合作方）| 社区适应能力强 |

### 1.6 PDK 版本状态

| PDK | 仓库 | 当前版本 | 状态 | 最近更新 |
|-----|------|----------|------|----------|
| SkyWater SKY130 | google/skywater-pdk | 0.0.0-369-g7198cf6 | 实验性/Alpha | 核心: 2023.05；工具链持续更新 |
| GlobalFoundries GF180MCU | google/gf180mcu-pdk | 0.0.0-111-gde3240d | 实验性/Alpha | 核心: ~2023 |
| open_pdks（集成安装）| RTimothyEdwards/open_pdks | — | 活跃 | 2026.03.04 |
| IHP SG13G2 | IHP-Open-PDK | 活跃开发 | 生产可用 | 持续更新 |

> 注：SKY130和GF180MCU核心库自2023年中后无重大新版本，但open_pdks集成层持续更新至今。
> Cadence于2025年在SKY130上推出付费聚合MPW服务（提交截止2026.01.16，交付预计2026.07）。
> Google原版OpenMPW免费梭航计划已于2024年初结束，PDK治理已移交CHIPS Alliance。

---

## 2. 用户痛点汇总（直接影响AUTO_EDA功能优先级）

> 来源：Reddit（r/KiCad、r/PrintedCircuitBoard、r/ElectricalEngineering）、KiCad官方论坛、社区讨论，2024-2025年。

### 2.1 高频痛点（P0级，直接影响AUTO_EDA优先级）

#### 痛点1：库管理地狱（Library Management Hell）
- **描述**：用户称之为「Library Management HeLL」。跨项目、跨团队维护自定义库极其繁琐；从旧版本迁移（v7→v8→v9）时库路径/格式问题频发；外部库集成（如SnapEDA）体验割裂。
- **典型抱怨**：「Every update breaks my library paths」「Adding symbols/footprints is a royal pain」
- **AUTO_EDA机会**：
  - 智能库搜索与自动匹配（元件→封装→3D模型一键关联）
  - AI辅助库导入与版本迁移
  - 跨项目库同步工具

#### 痛点2：Wayland/Linux 稳定性问题
- **描述**：KiCad在Wayland（Linux）下闪烁、复制粘贴失效、崩溃。随Linux发行版逐步放弃X11，该问题影响日益严重。有用户发帖称「KiCad会因Wayland问题失去所有用户」。
- **AUTO_EDA机会**：Web端或平台无关的AI辅助层可绕过此问题。

#### 痛点3：新版本稳定性回归
- **描述**：KiCad 8/9发布时频繁崩溃（PCB编辑器粘贴操作、DRC、原理图更新同步）；v9引入丝印层变化和焊盘显示bug；部分用户选择降级。
- **典型抱怨**：「KiCad 9 broke my workflow」「Crashed during DRC again」
- **AUTO_EDA机会**：
  - 提供版本无关的AI分析层
  - DRC结果解读与修复建议自动化

#### 痛点4：原理图工作流摩擦
- **描述**：拖拽元件时自动生成不需要的连接点；导线无法自动清理；原理图与PCB同步时报错不直观。
- **AUTO_EDA机会**：原理图AI审查与自动修正建议。

#### 痛点5：性能问题（复杂设计）
- **描述**：在复杂PCB上放大时渲染帧率骤降（即使硬件为现代Ryzen+独立显卡）；大型设计操作卡顿。
- **AUTO_EDA机会**：离线AI批处理分析，避免实时GUI瓶颈。

### 2.2 中频痛点（P1级）

| 痛点 | 描述 | AUTO_EDA机会 |
|------|------|-------------|
| **专业功能缺口** | 相比Altium缺少高速设计约束管理器、柔性PCB叠层、DFM检查 | AI辅助高速规则检查 |
| **自动布线质量差** | Freerouting布线结果常有artifacts需手动修复 | AI布线质量评估 |
| **差分对调谐bug** | 差分对等长调谐偶发bug | AI辅助验证 |
| **版本控制复杂** | KiCad项目文件Git管理非直观；文件diff不可读 | 智能项目归档 |
| **网络类管理UI差** | Netclass搜索/分配界面设计差 | AI辅助规则设置 |
| **初学者入门门槛高** | 学习曲线陡峭；文档散乱 | AI导师/向导功能 |

### 2.3 开源IC设计专项痛点

| 痛点 | 描述 |
|------|------|
| **工具链安装复杂** | OpenROAD/OpenLane/LibreLane安装配置门槛高，Docker是常见解法 |
| **PDK状态不透明** | SKY130/GF180长期Alpha，用户不知道是否「生产可用」 |
| **调试困难** | RTL-to-GDSII流程中间错误定位困难，日志晦涩 |
| **资源稀缺** | 高质量中文教程极少；商业EDA培训资源与开源工具脱节 |

---

## 3. 推广渠道评估

### 3.1 社区平台概览

| 平台 | 频道/社区 | 规模 | 适合内容 | 评分 |
|------|----------|------|----------|------|
| **Discord** | TinyTapeout Discord | >3,000成员 | 开源IC/ASIC设计、新手友好 | ⭐⭐⭐⭐⭐ |
| **Discord** | KiCad官方Discord | ~8,800成员 | PCB设计工具 | ⭐⭐⭐⭐⭐ |
| **Matrix** | fossi-chat.org（element.fossi-chat.org）|
 FOSSi核心社区 | 开源EDA/芯片综合讨论 | ⭐⭐⭐⭐ |
| **Reddit** | r/KiCad | 活跃 | PCB/KiCad | ⭐⭐⭐⭐ |
| **Reddit** | r/chipdesign, r/ECE, r/FPGA | 中等 | IC设计、FPGA | ⭐⭐⭐ |
| **论坛** | forum.kicad.info | 高质量技术讨论 | KiCad深度问题 | ⭐⭐⭐⭐ |
| **论坛** | EDAboard.com | 综合EDA | 广泛EDA问题 | ⭐⭐⭐ |
| **GitHub** | 项目主页、Discussions | 开发者 | 功能展示、集成 | ⭐⭐⭐⭐ |
| **YouTube** | FOSSi Foundation频道 | 会议录播 | 技术演讲 | ⭐⭐⭐ |

### 3.2 FOSSi Foundation 关键活动（推广入口）

| 活动 | 2025情况 | 意义 |
|------|----------|------|
| **ORConf** | 2025年9月，西班牙瓦伦西亚 | 最重要的开源EDA/硬件年会 |
| **Latch-Up** | 2025年5月，美国圣巴巴拉 | 北美开源芯片设计聚会 |
| **FSiC** | 2025年7月，德国 | 欧洲开源硅大会 |
| **FOSDEM** | 每年2月，比利时布鲁塞尔 | 有开源硅/EDA专项分会场 |
| **El Correo Libre** | FOSSi双周通讯 | 精准触达核心社区用户 |

### 3.3 推广策略建议（针对AUTO_EDA）

**短期（0-3个月）：**
1. 在 TinyTapeout Discord 和 fossi-chat.org Matrix 发布工具介绍，聚焦解决工具链配置痛点
2. 向 El Correo Libre 通讯投稿
3. 在 r/KiCad 发布「AI辅助KiCad工作流」演示帖
4. 在 forum.kicad.info 发布技术集成方案

**中期（3-6个月）：**
1. 提交 ORConf 2026 演讲提案（展示与开源EDA工具的MCP集成）
2. 与 TinyTapeout 合作，为其用户提供AI辅助设计流程
3. 向 KiCad 官方 GitLab 提交插件/集成方案
4. 与 FOSSi Foundation 探讨官方认可或合作

**长期（6个月+）：**
1. 成为 awesome-opensource-asic-resources 收录工具
2. 与 LibreLane（FOSSi官方维护）集成
3. 探索 CHIPS Alliance 工作组参与

---

## 4. 潜在合作机会

### 4.1 高优先级合作目标

| 机构/项目 | 合作方向 | 理由 |
|----------|----------|------|
| **TinyTapeout** | AI辅助设计检查、教学工具 | 活跃社区（>3000人），注重教育，与AI工具高度契合 |
| **FOSSi Foundation** | 工具推荐、ORConf演讲 | 是开源EDA社区的权威背书机构 |
| **LibreLane** | MCP工具集成 | OpenLane的官方继承者，是2025年后开源IC流程的核心 |
| **KiCad官方** | 插件/脚本集成 | 用户基数最大的开源PCB工具 |
| **Matt Venn（zerotoasiccourse.com）** | 课程配套工具、教学内容 | 最活跃的开源芯片设计教育者，有大量学员 |

### 4.2 中优先级合作目标

| 机构/项目 | 合作方向 | 理由 |
|----------|----------|------|
| **IHP开放PDK项目** | EDA流程自动化 | 欧洲最活跃的免费MPW提供者 |
| **ChipFoundry** | 设计提交前验证工具 | 继承efabless，管理大量开源项目 |
| **CHIPS Alliance** | PDK兼容性、标准化 | Linux Foundation旗下，治理SKY130和GF180 |
| **iEDA项目（中国）** | 本地化支持、合作研究 | 中国开源EDA主力项目，有学术背景 |

### 4.3 教学资源生态

| 资源 | 提供者 | 内容 | AUTO_EDA机会 |
|------|--------|------|-------------|
| **Zero to ASIC Course** | Matt Venn | OpenLane/Sky130完整流程 | 成为课程推荐工具 |
| **KiCad官方文档** | KiCad团队 | PCB设计权威教程 | 补充AI交互式学习 |
| **Phil's Lab（YouTube）** | Phil | KiCad视频教程，百万订阅 | 合作推广 |
| **TinyTapeout Workshop材料** | TinyTapeout | 面向学生的芯片设计 | 配套AI助手 |
| **IIC-OSIC-TOOLS Docker** | JKU Linz | 预装全套开源IC工具 | 集成AUTO_EDA到Docker镜像 |
| **Udemy/Coursera KiCad课程** | 第三方讲师 | PCB设计入门 | 课程伴侣工具 |

---

## 5. 关键洞察与结论

### 5.1 社区总体判断

- **开源EDA社区2025年经历重大动荡但总体向上**：efabless关停（3月）引发短期震荡，但社区通过LibreLane、ChipFoundry、IHP等迅速填补空白，展现出强韧性。
- **教育场景是最大增量市场**：TinyTapeout 2025年超1,233个设计、印度5,000+学生培训，证明入门级工具需求巨大。
- **亚洲市场快速崛起**：KiCon Asia 2025召开，中国KiCad用户显著增长，印度政府推动ESDM自主化，这是AUTO_EDA的战略机会。
- **AI+EDA是明确趋势**：Awesome-LLM4EDA（~266 stars）、ChipNeMo（NVIDIA）、Intel GenAI与OpenROAD集成，表明社区对AI辅助工具接受度高。

### 5.2 对AUTO_EDA功能优先级的直接建议

| 优先级 | 功能 | 对应痛点 |
|--------|------|----------|
| P0 | 智能库搜索与元件自动匹配 | 库管理地狱 |
| P0 | DRC结果AI解读与修复建议 | 新版本稳定性/DRC体验差 |
| P0 | 开源IC工具链安装引导 | 工具链配置门槛高 |
| P1 | 原理图AI审查（连接点、网络命名）| 原理图工作流摩擦 |
| P1 | 高速设计规则AI检查 | 专业功能缺口 |
| P2 | 多版本项目迁移助手 | 版本控制复杂性 |
| P2 | 中文本地化与教学资源对接 | 亚洲市场机会 |

### 5.3 重要资源链接

- FOSSi Foundation: https://fossi-foundation.org/
- fossi-chat Matrix: https://fossi-chat.org
- TinyTapeout Discord: https://tinytapeout.com/discord
- KiCad官方: https://www.kicad.org/
- OpenROAD项目: https://theopenroadproject.org/
- LibreLane: https://github.com/librelane/librelane
- awesome-opensource-asic-resources: https://github.com/mattvenn/awesome-opensource-asic-resources
- Awesome-LLM4EDA: https://github.com/Thinklab-SJTU/Awesome-LLM4EDA
- ChipFoundry: https://chipfoundry.io/
- Zero to ASIC Course: https://www.zerotoasiccourse.com/

---

*报告生成时间：2026-03-14*
*数据来源：grok-search深度调研，涵盖官方博客、GitHub、Reddit、FOSSi官网、TinyTapeout官网等一手资料*
