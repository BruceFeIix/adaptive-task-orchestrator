# Adaptive Task Orchestrator

[English](README.md) | 简体中文

[![CI](https://github.com/BruceFeIix/adaptive-task-orchestrator/actions/workflows/ci.yml/badge.svg)](https://github.com/BruceFeIix/adaptive-task-orchestrator/actions/workflows/ci.yml)

一个面向 Codex 的仓库本地编排 Skill：通过明确的任务合同、依赖感知执行、资源归属、证据门槛和根任务审查，协调边界清晰的子任务。

> **状态：实验性。** 当前实现已经在一个边界明确、仅使用标准库、单主机的软件开发 fixture 中完成有证据支持的本地验证。它不是生产级调度器，也不是分布式代理运行时。

## 为什么需要它

如果任务拆解、权限、路由、写入归属和审查都保持隐式，复杂代理工作很容易变得不可验证。Adaptive Task Orchestrator 把这些问题转化为明确的工件和门槛，同时让当前 Codex 对话继续担任最终根协调者。

这个 Skill 帮助根任务：

- 判断委派是否真的有收益；
- 将每个委派节点表示为边界明确的 `TaskContract`；
- 按拓扑波次执行无环依赖图；
- 分配互不冲突的读取范围、写入范围和资源锁；
- 按能力要求和风险下限路由，而不是只看模型品牌；
- 区分请求的、已观测的和未获运行时证明的路由；
- 要求带有证据的 `WorkerReceipt`；
- 选择确定性、根任务、独立或 frontier 审查门槛；
- 在范围、证据、权限或依赖失效时停止或重新规划。

## 它是什么——以及不是什么

| 它提供 | 它不提供 |
|---|---|
| 仓库本地 Codex Skill 和政策集合 | 持久化队列、服务、数据库或调度器 |
| 任务合同、路由决策、回执和审查门槛 | 对 Codex 工具、权限或沙箱的替代 |
| 依赖感知编排和写入归属规则 | 自动扩大权限或无边界自主委派 |
| 带故障关闭风险下限的能力路由 | 对模型可用性或路由证明的保证 |
| 标准库 fixture、结构验证和便携完整性工具 | 生产、吞吐、延迟或跨主机保证 |
| 单主机插桩重叠证据 | 跨主机时钟正确性或分布式追踪 |

Codex 仍然是执行环境。当前对话模型仍然负责范围、授权、冲突解决、外部操作、集成和最终交付。

## 什么时候使用

至少有一项收益足够明显时使用这个 Skill：

- 多个独立的只读工作可以并行；
- 不同子任务需要不同能力或上下文包；
- 一个宽泛任务可以拆成有依赖关系的明确产物；
- 共享写入需要清楚的所有者和顺序；
- 风险或弱验证性需要新的独立审查者；
- 结果需要可审计的证据链。

当工作很小、严格串行、高度耦合或由根任务直接验证更便宜时，应保留在根任务中。这个 Skill 明确反对为了“用了多代理”而委派。

## 在仓库中使用

### 前置条件

- 支持仓库本地 Skills 的 Codex 环境。
- 需要委派时具有多代理工具。如果委派不可用，Skill 仍可指导低风险的根任务内工作。
- 只有在运行随附验证 fixture 时才需要 Python 3 和 Git。

fixture 没有第三方 Python 依赖。

### 在仓库本地安装

把以下目录复制到 Codex 将要工作的仓库中：

```text
.agents/skills/adaptive-task-orchestrator/
```

该目录必须包含 `SKILL.md`、`agents/openai.yaml` 及其引用的政策文件。不要仅仅为了使用该 Skill 而安装外部运行时或扩大仓库权限。

### 调用方式

显式调用：

```text
$adaptive-task-orchestrator
```

示例：

```text
使用 $adaptive-task-orchestrator 规划这次 API 迁移。
共享合同只能有一个所有者；合同通过后才能并行处理相互独立的消费者；
最终必须提供有证据的回执，并由新的审查者完成集成审查。
```

对于明显受益于依赖感知委派的工作，该 Skill 也允许隐式触发。

## 编排如何工作

```text
分类任务
    ↓
判断委派是否值得
    ↓
创建边界明确的 TaskContracts
    ↓
验证依赖、范围、资源锁和权限
    ↓
预检路由，并记录“请求”与“已观测”的区别
    ↓
按拓扑波次派发，保证写入归属不重叠
    ↓
验证 WorkerReceipts 和确定性检查
    ↓
根任务集成，并在需要时进行新的独立审查
    ↓
接受、修订、重新规划或停止
```

### 任务合同

任务定义与模型路由、执行回执相互独立。完整合同结构见 [TaskContract 参考](.agents/skills/adaptive-task-orchestrator/references/task-contract.md)。

说明性片段：

```yaml
id: contract-migration
revision: 1
objective: Add a compatibility field while preserving legacy input.
task_type: implementation
mode: write
dependencies: []
read_scope:
  - contract/openapi.json
  - tests/test_migration.py
write_scope:
  - contract/openapi.json
resource_locks:
  - compatibility-contract
acceptance_checks:
  - contract tests pass
evidence_required:
  - scoped diff
  - test result
assurance_requirement: independent
```

这是政策工件，不是外部调度器配置文件或公共服务 API。如果验收命令会导入其他项目资源，这些传递读取必须显式声明或被隔离。

### 路由

计划使用 `fast_reader`、`general_worker`、`deep_reasoner` 和 `frontier_reviewer` 等稳定能力别名。在把能力别名绑定到真实模型和 reasoning effort 前，必须先预检运行时。

未获运行时证明的路由不能被描述为已观测。高风险能力下限约束分析质量，但不会授予额外权限。详见[路由政策](.agents/skills/adaptive-task-orchestrator/references/routing-policy.md)。

### 证据与审查

工作者返回结构化声明、证据、检查、未确定项、访问资源、外部调用和建议的下一步。根任务必须验证这些回执，而不是看到“成功”叙述就自动接受。

审查强度与影响和验证手段相匹配：

- `deterministic`：可靠的可执行或结构化检查；
- `root_check`：根任务可以直接检查的有界证据；
- `independent`：新的上下文进行规格与质量审查；
- `frontier`：用于高影响弱验证、安全、密码学或未解决冲突的对抗性保障。

详见[审查与升级规则](.agents/skills/adaptive-task-orchestrator/references/review-and-escalation.md)。

## 仓库结构

```text
.agents/skills/adaptive-task-orchestrator/  当前 Skill 与政策参考
fixtures/adaptive-task-orchestrator-write-dag/
                                            本地验证工具和测试
docs/decisions/                             架构决策记录
docs/specs/                                 已批准的验证范围
docs/context/                               不可变的版本化证据包
```

当前 Skill 是现行行为的权威来源。版本化 context 是验证证据，不是现行指令。参见[证据包说明](docs/context/README.md)。

## 本地验证

以下命令都从仓库根目录运行。

### 完整 fixture 工具测试

```bash
python -B -m unittest discover \
  -s fixtures/adaptive-task-orchestrator-write-dag/tests -v
```

使用 Windows Python Launcher：

```powershell
py -3 -B -m unittest discover `
  -s fixtures/adaptive-task-orchestrator-write-dag/tests -v
```

当前测试套件包含 110 项测试，覆盖原子化 materialization、结构化证据验证、
工作者独占事件流、便携 manifest 完整性、运行时路由一致性、注册表示例和受控
测试判据变异。本地 Windows Python 3.10／3.11 各通过 107 项，并跳过相同的 3 项
真实符号链接权限测试。跳过不计为通过。

后续针对 `96ba830` 的[四单元 CI 证据](docs/validation/v0.5-ci-platform.json)记录：
**Windows／Linux × Python 3.10／3.11 每个单元均为 110/110 通过、零跳过**，
包含全部三项真实符号链接断言和测试之后的九项证据／路由／完整性校验。
首轮 Windows 故障注入测试的路径匹配问题及仅涉及测试的修正，记录于
[ADR-0012](docs/decisions/0012-canonicalize-fault-injection-targets.md)。
这些观测补充已封存的本地回执，不改写历史记录。

### 验证已发布证据包的结构

```bash
python -B fixtures/adaptive-task-orchestrator-write-dag/tools/validate_evidence.py \
  --context-root docs/context/adaptive-task-orchestrator-v0.2

python -B fixtures/adaptive-task-orchestrator-write-dag/tools/validate_evidence.py \
  --context-root docs/context/adaptive-task-orchestrator-v0.3
```

退出码 `0` 表示所选 TaskContract、路由、不可变 revision 和回执记录全部通过。该验证器不证明签名、工件真实性、任意领域 JSON 的正确性、OpenAPI 语义或运行时模型可用性。

### 验证已发布证据包的文件清单和字节

便携校验器把自排除的 `integrity.sha256` 当作信任输入，核对包内普通文件的
精确清单与 SHA-256 字节：

```bash
python -B fixtures/adaptive-task-orchestrator-write-dag/tools/verify_integrity.py \
  --context-root docs/context/adaptive-task-orchestrator-v0.2

python -B fixtures/adaptive-task-orchestrator-write-dag/tools/verify_integrity.py \
  --context-root docs/context/adaptive-task-orchestrator-v0.3
```

该命令只读且仅使用 Python 标准库。没有 finding 时退出 `0` 且不输出；校验
失败时退出 `1` 并输出确定性的 JSON Lines finding；参数用法错误由参数解析器
返回 `2`。成功结果只表示相对于可信 manifest 的包变更检测，不代表签名、
来源、可信时间戳或真实性。校验假设所选证据包在调用期间保持静止，也不是
防御并发恶意替换的文件系统沙箱。

### 检查运行时模型路由

v0.5 的可选校验器仅使用 Python 标准库，只读取显式指定的两个 JSON 文件。
仅复制 Skill 不会安装这个源代码仓库附带的 CLI：

```bash
python -B fixtures/adaptive-task-orchestrator-write-dag/tools/validate_runtime_routes.py \
  --registry .agents/skills/adaptive-task-orchestrator/references/model-registry.json \
  --bundle docs/context/adaptive-task-orchestrator-v0.5/candidates/planned-astra-bundle.json
```

示例描述的是计划，而非已完成运行。退出 `0` 只表示所提供的记录相互一致；
`1` 输出确定性的 JSONL finding；`2` 表示参数用法错误。检查涵盖模型／effort
交集、能力下限、精确锁定、回退链、上下文与覆盖参数兼容性、实际身份绑定、
审查关系、并发批次和声明记录的覆盖情况。

校验器不执行代理、不访问来源引用、不认证输入，也不证明完整 run 成功。
主机返回任务 ID 并不证明实际模型／effort；缺少实际配置证据的高风险
accepted／completed 记录会被拒绝，仅把示例改成 `completed` 不能使其通过。
参见[运行时路由参考](.agents/skills/adaptive-task-orchestrator/references/runtime-routing.md)
和 [v0.5 规格](docs/specs/adaptive-task-orchestrator-v0.5-runtime-routing.md)。

版本化[模型注册表](.agents/skills/adaptive-task-orchestrator/references/model-registry.json)
把 Astra 加入最高审查候选，同时保留 Luna／Terra／Sol 的职责。这些是暂定的
项目策略，不是已测量的模型排名。候选资格取决于注册表与主机在确切工具接口上
的支持交集；用户锁定同时约束模型和 effort，不允许静默回退。

### 创建新的 fixture run

下面的命令会写入一个自包含的嵌套 Git fixture。必须使用唯一 run ID，且绝不能把项目根目录作为目标：

```bash
python -B fixtures/adaptive-task-orchestrator-write-dag/tools/materialize.py \
  --run-id my-local-run
```

公开仓库会忽略生成的 runs。materializer 会拒绝覆盖已有 run 或 baseline receipt。

## 验证状态

| 里程碑 | 有证据支持的结果 | 边界 |
|---|---|---|
| v0.1 | 初始 Codex-native 政策基线 | v0.1 没有完成真实写入型多代理 DAG |
| v0.2 | 一个有界的本地 nested-Git 写入型软件开发 DAG | 不证明持久调度器、生产负载、跨主机协调或所有路由 |
| v0.3 | 原子化 fixture 发布、故障关闭证据验证、工作者独占事件流，以及一次真实双代理重叠探针 | 仅限单主机本地证据；不证明吞吐、崩溃恢复、签名或跨主机能力 |
| v0.4（已封存本地候选） | 相对于可信 manifest 的便携只读精确清单与 SHA-256 校验；v0.4 的 Windows Python 3.10／3.11 基线发现 63 项测试：60 项通过，3 项跳过 | 后续四单元 CI 与真实符号链接观测另行保存；不证明真实性或并发对抗安全 |
| v0.5（本地候选） | 版本化 Astra 注册表、运行时策略和离线路由校验器；当前本地套件在两套 Python 各发现 110 项：107 项通过，3 项跳过 | 合成记录和有界原生审查不代表实际模型认证、模型基准测试、完整 run 闭合或跨平台发布验收 |

已发布的 v0.3 回执记录了本地 Python 3.10 和 3.11 环境下 44/44 fixture 测试、有效的 v0.2/v0.3 证据包，以及没有未解决 Critical/Required 发现的独立审查。整体结果仍然是 `ACCEPT_WITH_CAVEATS`，不是生产认证。

v0.5 试跑中，请求使用 Astra 和 Terra 的两组配置分别首次答对了三个固定的
确定性任务。这一小规模、仅确认请求配置的观察没有改变暂定注册表默认值，
也不构成模型质量、延迟或成本基准测试。

详细证据：

- [v0.2 写入型 DAG 规格](docs/specs/adaptive-task-orchestrator-v0.2-write-dag.md)
- [v0.2 证据包](docs/context/adaptive-task-orchestrator-v0.2/README.md)
- [v0.3 硬化规格](docs/specs/adaptive-task-orchestrator-v0.3-hardening.md)
- [v0.3 证据包](docs/context/adaptive-task-orchestrator-v0.3/README.md)
- [v0.4 便携完整性规格](docs/specs/adaptive-task-orchestrator-v0.4-portable-integrity.md)
- [ADR-0009：便携校验证据 manifest](docs/decisions/0009-verify-evidence-manifests-portably.md)
- [v0.5 运行时路由规格](docs/specs/adaptive-task-orchestrator-v0.5-runtime-routing.md)
- [v0.5 本地候选证据](docs/context/adaptive-task-orchestrator-v0.5/README.md)
- [ADR-0011：校验运行时模型路由](docs/decisions/0011-validate-runtime-specific-model-routes.md)
- [架构决策](docs/decisions/README.md)

## 已知限制

以下能力仍然被明确排除、延期或没有得到证明：

- 持久调度、队列、数据库、服务、仪表盘或 Web API；
- 生产负载就绪或性能保证；
- 跨主机执行和跨主机时钟正确性；
- 进程崩溃恢复、陈旧锁检测和陈旧锁回收；
- 超出所选结构记录校验器与可信 manifest 清单范围的全部传递证据读取严格闭合；
- 密码学签名、可信时间戳或工件真实性；
- 第三方 OpenAPI 语义验证；
- 所有运行时模型、effort、能力等级或领域拓扑都可工作；
- 在未提供所需运行时结果的主机上证明实际模型／effort；注册表等级和 profile
  默认值仍为暂定策略，没有模型成本、延迟或质量基准测试声明；
- 第二个端到端领域 fixture，包括逆向工程；
- 精确重建当时没有保存的 11 个早期 v0.2 TaskContract 正文。
- 超出已观测四个 CI 单元的平台和 Python 版本；后续平台回执不会将本地的权限
  跳过追溯改为通过，也不代表合并、打 tag、发布或实际模型认证。

## 贡献与安全

欢迎贡献。在修改当前 Skill、证据结构、fixture 或双语能力声明前，请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

请按照 [SECURITY.md](SECURITY.md) 私下报告漏洞。不要在公开 issue 中放入凭据、私有仓库数据或未经脱敏的代理证据。

社区参与遵循 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。

## 许可证

本项目采用 [Apache License 2.0](LICENSE)。
