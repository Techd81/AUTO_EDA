[根目录](../CLAUDE.md) > **tests**

# tests — 测试套件

## 模块职责

本目录包含 AUTO_EDA 的全部自动化测试，使用 pytest + pytest-asyncio。当前覆盖 core 错误体系、EDABridge WebSocket 通信、STM32 全自动流程三个方向，共 **24 个测试用例，全部通过**。所有测试均使用 mock，不依赖真实 EDA 客户端。

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
        └── test_stm32_flow.py           # 8个测试：组件表4个+流程4个
```

---

## 测试清单

### test_errors.py（10个）
| 测试 | 验证内容 |
|------|----------|
| `test_tool_not_found_error_code` | 错误码为 TOOL_NOT_FOUND (2001) |
| `test_tool_not_found_error_message_contains_tool_name` | 消息含工具名 |
| `test_tool_not_found_error_has_detail` | 含 detail 字段（PATH 安装指引）|
| `test_tool_execution_error_code` | 错误码为 UNKNOWN (1000) |
| `test_tool_execution_error_returncode` | returncode 属性正确 |
| `test_timeout_error_code` | 错误码为 TIMEOUT (1005) |
| `test_timeout_error_message_contains_duration` | 消息含超时秒数 |
| `test_error_to_mcp_error_text_contains_code` | MCP 错误文本含错误码 |
| `test_error_to_mcp_error_text_contains_message` | MCP 错误文本含工具名 |
| `test_eda_error_is_exception` | EDAError 继承 Exception |

### test_bridge.py（6个）

使用 `_MockConn` 模拟 WS ServerConnection，注入到 `bridge._conn`，匹配当前 WS 服务端架构。

| 测试 | 验证内容 |
|------|----------|
| `test_send_command_success` | 正常响应返回 result 字段 |
| `test_send_command_rpc_error` | EDA 返回 error 时抛出 EDAError |
| `test_ping_success` | ping 返回 True |
| `test_ping_failure_when_not_connected` | 无连接时返回 False 不抛异常 |
| `test_disconnect_clears_conn` | disconnect 后 `_conn` 为 None |
| `test_request_ids_increment` | 请求 ID 自增 "1", "2" |

### test_stm32_flow.py（8个）

使用 `_HappyBridge` (成功路径) 和 `_DeadBridge` (失败路径) mock。

| 测试 | 验证内容 |
|------|----------|
| `test_stm32_component_count` | STM32_MIN_SYS 共 19 个元件 |
| `test_all_lcsc_numbers_valid` | 所有 LCSC 料号格式 C+数字 |
| `test_lookup_by_ref` | STM32_BY_REF["U1"] 查找正确 |
| `test_no_duplicate_refs` | 无重复 ref |
| `test_happy_path_flow` | 14步全流程成功完成 |
| `test_flow_aborts_on_ping_failure` | ping 失败时流程中止 |
| `test_step_callback_called_for_all_14_steps` | on_step 回调覆盖 1-14 |
| `test_flow_summary_contains_all_steps` | summary() 含全部步骤号 |

---

## 运行方式

```bash
pytest tests/ -v                          # 全部测试（24个，~3s）
pytest tests/test_core/ -v                # 仅 core 测试（10个）
pytest tests/test_servers/ -v             # 仅 server 测试（14个）
pytest tests/ -v -m "not integration"     # 排除集成测试
pytest tests/ --cov=src/auto_eda --cov-report=term-missing  # 含覆盖率
```

---

## conftest.py 共享 Fixtures

| Fixture | 说明 | 状态 |
|---------|------|------|
| `tmp_dir` | 临时目录（pytest tmp_path 别名）| 正常 |
| `sample_verilog` | 8位计数器 .v 文件（写入 tmp_path）| 正常 |
| `mock_process_result` | ProcessResult stub（returncode=0）| 有 `timed_out` 字段错误，未被使用 |
| `mock_run_tool` | monkeypatch run_tool 为 AsyncMock | 正常 |

---

## 待补充项

1. conftest.py `mock_process_result` 传入 `timed_out=False`，但 `ProcessResult` 无此字段 — 当前未被使用，Phase 1 需修复
2. 无 `draw_stm32_minimum_system` MCP 工具层的端到端测试
3. 无 `core/base_server.py` (`create_server`, `@eda_tool`) 的单元测试
4. 无 `core/result.py` (`ToolSuccess`, `ToolFailure`, `format_mcp_error`) 的单元测试
5. 无 `core/process.py` (`run_tool`, `find_tool`) 的单元测试（需 mock subprocess）

---

## 变更记录 (Changelog)

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-03-14 | 0.1.0 | 架构师扫描自动生成 |
| 2026-03-15 | 0.2.0 | 深度扫描更新：修正测试计数(24)、修正bridge测试状态、补充完整测试清单 |
