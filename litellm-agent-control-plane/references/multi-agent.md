# Reliable multi-agent design on LACP

## Contents

1. Decide whether to split
2. Define specialist contracts
3. Define the orchestrator contract
4. Model data flow and failure
5. Configure LACP relationships
6. Validate the complete topology

## Decide whether to split

Keep one agent when the task shares one context, one permission set, and one
output, or when orchestration would only relay prose between identical roles.

Split when at least one boundary is real:

- Different expertise or evaluation criteria.
- Different integrations, credentials, or safety permissions.
- Independent work that can be reused or verified separately.
- Context isolation materially improves accuracy.
- One role gathers evidence while another makes a bounded judgment.

Add an orchestrator only when LACP must coordinate the specialists after the
current Codex task ends. Avoid decorative roles, duplicate “reviewers,” and
deep hierarchies. Prefer one parent with a small set of leaf specialists.

## Define specialist contracts

Each child must be useful when invoked with a complete task prompt and no
parent conversation. Give it:

- One bounded capability and explicit non-goals.
- Its own authoritative sources and necessary tools.
- A machine-reviewable output contract.
- Completion, timeout, and failure behavior.
- No authority to delegate unless another hierarchy is genuinely required.

Example output contract:

```json
{
  "status": "complete|partial|blocked",
  "answer": "bounded result",
  "evidence": [{"claim": "...", "source": "..."}],
  "assumptions": ["..."],
  "errors": ["..."],
  "recommended_next_step": "..."
}
```

Use the same field names across specialists when the parent must merge results.
Do not ask a specialist to produce the final user answer unless that is its
only job.

## Define the orchestrator contract

The parent is a coordinator, not a vague “smartest agent.” Its instructions
must require this loop:

1. Parse the request and identify required deliverables.
2. Call `list_sub_agents` when IDs or capabilities are not already certain.
3. Choose only the specialists needed for this request.
4. Call `run_sub_agent` with a complete prompt containing objective, relevant
   context, scope, input locations, constraints, expected schema, and deadline.
5. Inspect `status`, `output`, and any error evidence returned for each child.
6. Retry only when safe and with a corrected prompt or transient-failure reason.
7. Reconcile contradictions and missing coverage; never silently choose one
   child's claim.
8. Synthesize the final output and disclose partial/failed child work.

Include an explicit prohibition against claiming success merely because the
parent session completed. The current platform tool returns a child session ID,
status, and text; the parent must evaluate those values.

## Model data flow and failure

For every edge, record:

| Field | Decision |
|---|---|
| Sender | Parent or named specialist |
| Receiver | Named specialist or parent |
| Input | Exact facts/files/IDs included in the prompt |
| Output | Required schema and evidence |
| Dependency | Whether another child must finish first |
| Failure | Retry, fallback, partial result, or stop |
| Sensitivity | Data the receiver may and may not receive |

Do not assume child agents share the parent's prompt, memory, tools,
credentials, workspace, or attached skills. Configure each child independently
and send all task-specific context in `run_sub_agent.prompt`.

Use sequential calls when one result changes the next task. Independent calls
may be issued concurrently only when the selected runtime supports safe
parallel tool calls and the tasks do not mutate shared state. Never parallelize
competing edits or non-idempotent external actions.

Keep the graph acyclic. Do not attach the parent back to a child or create
mutual delegation. Bound attempts globally; a child retry plus a parent retry
must not create an accidental multiplicative loop.

## Configure LACP relationships

- Put symbolic child refs in blueprint `sub_agents`; the helper creates agents,
  obtains real IDs, and patches parent `config.sub_agents` afterward.
- LACP automatically exposes `list_sub_agents` and `run_sub_agent` when a
  parent has attached children. Do not register these as external MCP servers.
- A parent may also request platform approvals through `platform_mcp_ids`.
- Give external integration MCP servers to the specialist that uses them. Do
  not attach every integration to the parent by default.
- Create all agents paused. Activate leaf tests before parent tests, then enable
  the parent, and only then enable a schedule or delivery capability.

## Validate the complete topology

Test more than the final prose:

1. Invoke every child directly with a representative task.
2. Verify every child uses its intended tools and respects denied actions.
3. Invoke the parent on a task requiring one child, then multiple children.
4. Force one child to return partial, blocked, malformed, and contradictory
   output; confirm the parent reports or repairs the condition.
5. Inspect the `run_sub_agent` tool result and child session, not only the
   parent's terminal status.
6. Confirm sensitive context reaches only the intended child.
7. Repeat a mutable workflow and confirm there is no duplicate side effect.

LACP does not currently provide a durable parent-child foreign key for every
session. Preserve returned child session IDs in diagnostic output and correlate
by child agent ID and time when deeper investigation is required.
