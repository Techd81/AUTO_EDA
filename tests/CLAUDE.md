[根目录](../CLAUDE.md) > **tests**

# tests — 测试套件

## 模块职责

本目录包含 AUTO_EDA 的全部自动化测试，使用 pytest + pytest-asyncio。当前覆盖 core 错误体系、EDABridge WebSocket 通信、STM32 全自动流程三个方向，共 22 个测试用例。所有测试均使用 mock，不依赖真实 EDA 客户端。

---

## 测试结构

```
tests/
├── conftest.py                          # 共享 fixtures
├── __init__.py
├── test_core/
│   ├── __init__.py
│   └── test_errors.py                   # 10个测试：错误码/消息/继承
└── test_servers/
    ├── __init__.py
    └── test_easyeda/
        ├── __init__.py
        ├── test_bridge.py               # 6个测试：WS通信/ping/断开/ID递增
        └── test_stm32_flow.py           # 6个测试：流程+组件表验证
```

---

## 测试清单

### test_errors.py（10个）
| 测试 | 验证内容 |
|------|----------|
| `test_tool_not_found_error_code` | 错误码为 TOOL_NOT_FOUND |
| `test_tool_not_found_error_message_contains_tool_name` | 消息含工具名 |
| `test_tool_not_found_error_has_suggested_fix` | 含 suggested_fix 字段 |
| `test_tool_execution_error_code` | 错误码为 TOOL_EXECUTION_FAILED |
| `test_tool_execution_error_returncode` | returncode 属性正确 |
| `test_timeout_error_code` | 错误码为 TIMEOUT |
| `test_timeout_error_message_contains_duration` | 消息含超时秒数 |
| `test_error_to_dict_*` | `to_dict()` 结构验证 |
| `test_eda_error_is_exception` | 继承关系验证 |

> 注意：test_errors.py 导入 `TimeoutError` 和 `TOOL_EXECUTION_FAILED`，与 errors.py 中实际的 `ToolTimeoutError` / `EDAErrorCode.UNKNOWN` 存在命名不一致，需修复后才能通过。

### test_bridge.py（6个）
| 测试 | 验证内容 |
|------|----------|
| `test_send_command_success` | 正常响应返回 result 字段 |
| `test_send_command_rpc_error` | EDA 返回 error 时抛出 EDAError |
| `test_ping_success` | ping 返回 True |
| `test_ping_failure_on_connection_error` | 无服务器时返回 False 不抛异常 |
| `test_disconnect_clears_ws` | disconnect 后 _ws 为 None |
| `test_request_ids_increment` | 请求 ID 自增 "1", "2" |

> 注意：test_bridge.py 使用旧协议格式（`_ws` 属性、`url=` 构造）与当前 bridge.py 的 WS 服务端架构不匹配，需适配。

### test_stm32_flow.py（6个）
| 测试 | 验证内容 |
|------|----------|
| `test_stm32_component_count` | STM32_MIN_SYS 共 19 个元件 |
| `test_all_lcsc_numbers_valid` | 所有 LCSC 料号格式正确 |
| `test_lookup_by_ref` | STM32_BY_REF["U1"] 查找正确 |
| `test_no_duplicate_refs` | 无重复 ref |
| `test_happy_path_flow` | 14步全流程成功完成 |
| `test_flow_aborts_on_ping_failure` | ping失败时流程中止 |

---

## 运行方式

```bash
pytest tests/ -v                          # 全部测试
pytest tests/test_core/ -v                # 仅 core 测试
pytest tests/test_servers/ -v             # 仅 server 测试
pytest tests/ -v -m "not integration"     # 排除集成测试
pytest tests/ --cov=src/auto_eda --cov-report=term-missing  # 含覆盖率
```

---

## conftest.py 共享 Fixtures

| Fixture | 说明 |
|---------|------|
| `tmp_dir` | 临时目录（pytest tmp_path 别名）|
| `sample_verilog` | 8位计数器 .v 文件（写入 tmp_path）|
| `mock_process_result` | ProcessResult stub（returncode=0）|
| `mock_run_tool` | monkeypatch run_tool 为 AsyncMock |

---

## 已知缺口与待修复项

1. `test_errors.py`：导入 `TimeoutError`（应为 `ToolTimeoutError`/`EDATimeoutError`）和 `TOOL_EXECUTION_FAILED`（应为 `UNKNOWN`）— 需对齐命名
2. `test_bridge.py`：基于旧 WS 客户端架构（`EDABridge(url=...)`，`bridge._ws`）— 需重写以适配当前 WS 服务端架构（`EDABridge(host, port)`，`bridge._conn`）
3. 缺少 `test_stm32_flow.py` 中 ERC 错误中止和14步回调的完整测试（`test_flow_aborts_on_erc_errors`、`test_step_callback_called_for_all_14_steps` 已定义但依赖 `sch.runERC` 协议格式）
4. 无 `draw_stm32_minimum_system` MCP 工具层的端到端测试

---

## 变更记录 (Changelog)

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-03-14 | 0.1.0 | 架构师扫描自动生成，基于全量代码阅读 |
