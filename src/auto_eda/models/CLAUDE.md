[根目录](../../../CLAUDE.md) > [src/auto_eda](../) > **models**

# models — 共享数据模型

## 模块职责

`models/` 存放跨 Server 共用的 Pydantic 数据模型。当前仅有 `verilog.py`，为未来 Yosys/VerilogUtils Server 预置 HDL 相关模型。easyeda 模块有自己专属的 `servers/easyeda/models.py`，不在此目录。

---

## 文件清单

```
src/auto_eda/models/
├── __init__.py    # 空（待填充导出）
└── verilog.py     # Verilog/HDL Pydantic 模型（Phase 1 使用）
```

---

## 当前状态

骨架完成，`verilog.py` 内容为 Phase 0 脚手架占位，Phase 1 开发 Yosys/VerilogUtils Server 时填充。

---

## 变更记录 (Changelog)

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-03-14 | 0.1.0 | 架构师扫描自动生成 |
