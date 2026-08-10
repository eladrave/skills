# Designing reliable LACP agents

## Contents

1. Start from an operating contract
2. Write complete instructions
3. Select LACP capabilities deliberately
4. Design schedules and state
5. Apply the quality gate
6. Run acceptance cases

## Start from an operating contract

Ask only for missing facts that change the design. Resolve these before agent
creation:

| Contract part | Required decision |
|---|---|
| Outcome | Exact artifact, decision, or external result the agent must produce |
| Inputs | Where authoritative data comes from and how freshness is determined |
| Scope | Accounts, repositories, folders, channels, records, dates, and users it may touch |
| Output | Format, destination, audience, citations/evidence, and required fields |
| Completion | Observable conditions that make the task done |
| Boundaries | Actions that are forbidden, read-only, or require approval |
| Failure | Retry limit, fallback, escalation, and what must remain unchanged |
| Operation | Interactive versus scheduled, timezone, runtime limit, and expected volume |

Do not convert an ambiguous aspiration such as “manage my support” directly
into an agent. First make the operating boundary concrete: which queue, which
sources, whether it may draft or send, when it must escalate, and how quality
will be judged.

## Write complete instructions

Write the `system` value as a standalone operating manual. The initial user
prompt may be short, a scheduled routine may supply only one sentence, and a
sub-agent receives only the prompt its parent sends. Do not rely on this Codex
conversation being available at run time.

Use this compact structure:

```markdown
Role
You are <role> responsible for <bounded outcome>.

Authoritative inputs
- Use <sources> for <facts>.
- Treat <source> as authoritative when sources disagree.
- If required input is missing or stale, <stop/escalate behavior>.

Workflow
1. Inspect and validate the inputs.
2. Perform <specific steps and tool calls>.
3. Cross-check <important claims or side effects>.
4. Produce <output contract>.

Tool policy
- Use <tool/server> only for <purpose>.
- Prefer read/list/search before create/update/send/delete.
- Never infer a successful tool result; inspect the returned status and payload.

Boundaries and approvals
- Do not <forbidden actions>.
- Before <external effect>, present <exact preview> and obtain approval through <mechanism>.

Completion and failure
- Complete only when <observable checks> pass.
- On <failure>, retry at most <n> times, preserve <state>, and report <evidence>.

Output
- Return <schema/sections> with <citations, IDs, links, counts, or caveats>.
```

Instruction rules:

- State positive actions and prohibitions precisely. “Be careful” is not a
  control; “do not send until `request_human_approval` returns accepted” is.
- Name the expected tool purpose, not only the tool. An attached MCP server
  does not tell the model when it should call it.
- Specify source precedence and freshness for fact-sensitive work.
- Separate drafting from delivery. A drafting agent normally needs read tools;
  a delivery agent needs write tools plus an approval contract.
- Define uncertainty behavior. Require the agent to distinguish verified fact,
  inference, and missing evidence.
- Define a stopping condition. Avoid open-ended “continue researching” loops.
- Keep reusable domain procedure in an attached skill, cross-agent policy in an
  attached rule, and the agent-specific mission in `system`.
- Do not duplicate or contradict attached skills and rules. LACP appends the
  selected skill bodies and rules to the agent system prompt.

### Weak and strong examples

Weak:

```text
You are a research agent. Search the web and write a good report.
```

Stronger:

```text
You are a market-evidence researcher. Produce a decision brief answering the
request with evidence current as of the run date. Search primary sources first;
use secondary sources only to locate or compare primary evidence. For every
material claim, preserve the source URL and publication date. If two sources
conflict, report the conflict and do not choose silently. Do not contact people,
submit forms, or publish content. Complete only after each requested question is
answered or explicitly marked unsupported. Return: answer first, evidence table,
uncertainties, and recommended next checks.
```

## Select LACP capabilities deliberately

### Runtime and model

- Use only a connected runtime alias and a model returned for that runtime.
- Match the runtime to required execution: repository/file work, code
  execution, web research, or external MCP access.
- Prefer a cheaper/faster model for narrow deterministic specialists and a
  stronger model for orchestration, ambiguous synthesis, or safety-critical
  judgment. Do not assume a model is available from its marketing name.

### Native runtime tools

- Start from the runtime's returned tool catalog.
- Attach read/search tools when the agent must observe. Attach write/edit/shell
  only when the contract requires them.
- Shell access is broad authority. Do not give it to an agent that only needs a
  registry MCP tool.
- Treat tool availability and tool competence separately: the system prompt
  must say when, why, and under what limits to use each capability.

### Skills and rules

- Use `skill_ids` for reusable procedures or domain knowledge.
- Use `rule_ids` for policy that should apply consistently across agents.
- Attach only IDs returned by inventory. Review the full attached content for
  contradictions and stale assumptions before creation.

### Vault keys

- `vault_keys` names values that LACP resolves into the runtime environment for
  the agent owner, with fallback to the local owner and then global scope.
- Attach only keys the selected tools actually require. A named key is not
  proof that a value exists or that the upstream credential is authorized.
- Test the least-privileged credential against the intended read/write action.
  Never place the value in `system`, files, skills, rules, or a blueprint.

### Integration and platform MCP tools

- Use `mcp_server_ids` for registered external integrations.
- Use `platform_mcp_ids` for LACP built-ins such as approvals or agent memory.
- Read `mcp.md` before configuring either surface.

### Runtime limits and failure

- Set `max_runtime_minutes` to the shortest realistic end-to-end duration,
  including upstream tools and sub-agent work.
- Use a bounded retry policy in the instructions. Never let retries repeat an
  external side effect without idempotency evidence.
- Keep `on_failure` conservative; `pause_and_notify` is the safe default for an
  unattended workflow.

## Design schedules and state

- Use a schedule only when the goal is truly time-driven. Record an explicit
  IANA timezone and describe the data window, late-run behavior, and duplicate
  prevention.
- Keep the agent paused until a manual test has exercised the same inputs and
  permissions as the scheduled run.
- Treat DB-backed memory as agent state, not as a replacement for authoritative
  records. Store stable preferences or checkpoints, not secrets or unchecked
  facts. Give the agent the `agent_memory` platform tool only when it must
  manage that state itself.
- Use agent files for durable working material that belongs with the agent.
  State how freshness, format, and conflicting versions are handled.

## Apply the quality gate

Reject or revise the design if any answer is “no”:

1. Can another operator state exactly what success looks like?
2. Are authoritative inputs, freshness, and conflict handling explicit?
3. Are every runtime, model, native tool, MCP ID, skill ID, and rule ID present
   in current inventory?
4. Does each permission have a necessary step in the workflow?
5. Does the instruction say when and how to use each attached external tool?
6. Are side effects separated from research/drafting and approval-protected?
7. Are missing input, tool failure, partial result, retry, and escalation defined?
8. Is the output contract concrete enough to test without subjective judgment?
9. For scheduled work, are timezone, duplicate prevention, and paused rollout defined?
10. For multi-agent work, does every boundary satisfy `multi-agent.md`?

## Run acceptance cases

Use synthetic or isolated inputs before production activation:

| Case | Expected evidence |
|---|---|
| Happy path | Required artifact and every completion check |
| Missing input | No guessing; explicit request or escalation |
| Out-of-scope request | Refusal without side effects |
| MCP unavailable | Bounded failure with server/tool error preserved |
| Empty result | Valid empty output, not fabricated content |
| Conflicting sources | Conflict surfaced according to source policy |
| External action | Preview and approval before the action; result verified afterward |
| Repeat invocation | No duplicate send/create/purchase/delete |

For mutable operations, verify the target system's state independently. An HTTP
success response is not enough when the requested outcome is externally
observable.
