# Backend Forge Controller Protocol

Backend Forge follows the shared forge controller discipline, then adds backend-specific architecture, data, security, and test-closure gates.

## Shared Controller Surface

- Trigger recognition: `bf-`, `bf-fast`, `bf-a`, `bf a`, `/backend-forge`.
- Project detection: `scripts/detect_project_root_state.py`.
- Task classification: `scripts/classify_task.sh`.
- Session state: `scripts/bf_session.sh`.
- Write gates: `scripts/gate_check.py`.
- Output protocol: `scripts/validate_output.sh`.
- Release validation: `scripts/validate_release.sh`.

## Backend Adapter Extensions

Backend Forge keeps these domain-specific requirements outside the shared layer:

- Architecture leadership A0-A7.
- Data model and migration impact analysis.
- Authentication, authorization, and resource ownership checks.
- Transaction, cache, async, queue, and consistency decisions.
- Test closure as the primary acceptance mechanism.
- Architecture sign-off for enterprise or organization-level decisions.

## Minimum State Mapping

| Shared concept | Backend Forge field |
|---|---|
| `phase` | `当前阶段` |
| `mode` | `当前模式` |
| `policy` | `执行策略` |
| `confirmation_status` | `确认状态` |
| `work_unit` | `当前子单元` |
| `verification_status` | `验证状态` |
| backend-specific core definition | `目标状态` / `架构状态` / `数据影响状态` / `安全边界状态` / `测试闭环状态` |

## Release Rule

Any new P0/P1 backend rule must either be covered by `scripts/validate_release.sh` or explicitly recorded as a known gap before release.

release_binding: RB-BACKEND-ROUTE-001
release_binding: RB-BACKEND-GATE-001
release_binding: RB-BACKEND-OUTPUT-001
