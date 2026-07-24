---
name: building-strands-agents
description: Use when designing, implementing, testing, exposing, or consuming Python agents built with the Strands Agents SDK, including tools, model providers, multi-agent orchestration, A2A services, HTTPS APIs, sessions, streaming, and production deployment.
---

# Build Strands Agents

Build model-driven Python agents with the Strands Agents SDK. Treat an agent as a stateful application component with tools and an LLM, not as a prompt wrapped in an HTTP endpoint.

This guide targets Python 3.10+ and the current Strands Python SDK. Strands changes quickly: verify unstable imports and constructor arguments against the current official documentation and source before implementing them.

## Source-of-truth order

When documentation, examples, and installed behavior disagree, use this order:

1. The version installed in the target project and its Python signatures.
2. The matching release/tag in the official Strands repository.
3. The official API reference and user guide.
4. Official samples.
5. Blog posts and third-party examples only as design inspiration.

Never copy model IDs, provider options, A2A event shapes, or deployment examples without checking the target SDK version. The former `strands-agents/sdk-python` repository now redirects to the Strands monorepo.

## Start with architecture, not code

Before creating files, identify:

- The task and success criteria.
- Tools and side effects the agent may perform.
- Trust boundaries and authorization rules.
- Whether conversations are stateless, session-scoped, or durable.
- Whether callers need synchronous replies, streaming, or long-running jobs.
- Whether components run in one process or across services.
- Latency, cost, model-provider, data-residency, and deployment constraints.

Use the least complex pattern that satisfies these requirements.

| Need | Use |
|---|---|
| One model with tools | One `Agent` |
| A coordinator delegating to a few specialists | Agents as tools |
| Developer-defined dependencies, branches, or remote agents | `Graph` |
| Autonomous local peer handoffs | `Swarm` |
| Fixed repeatable DAG with parallel tasks | Workflow pattern/tool |
| Cross-service or cross-framework agent interoperability | A2A |
| Stable application-specific request/response API | HTTPS/REST or streaming HTTP |
| Background, bursty, or long-running work | Queue plus worker, optionally fronted by HTTPS |

Do not distribute agents merely because there are several of them. Keep them in one process until independent scaling, fault isolation, ownership, language boundaries, or network placement justify distribution.

## Implementation workflow

1. Pin Python and dependency ranges in `pyproject.toml` or the project lockfile.
2. Define the external input/output contract before prompts.
3. Select a model provider explicitly for production.
4. Implement and test ordinary Python tool functions first.
5. Create the smallest useful agent with a narrow system prompt and tool set.
6. Add structured output where another program consumes the result.
7. Add multi-agent orchestration only when specialization improves the design.
8. Add a network boundary only after defining identity, state ownership, timeouts, retries, and observability.
9. Test tools, contracts, orchestration, failure paths, and representative end-to-end tasks.
10. Containerize and deploy only after the local behavior is reproducible.

## Install and configure

Use a virtual environment and a lockfile. Install only the extras actually required:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install strands-agents

# Optional community-maintained tools
python -m pip install strands-agents-tools

# Native A2A client/server support
python -m pip install 'strands-agents[a2a]'

# Example non-default provider
python -m pip install 'strands-agents[openai]'
```

The default provider is Amazon Bedrock and uses the AWS credential chain. Configure credentials outside source code. Grant only the model and service permissions the agent needs.

## Build one agent well

Keep tools deterministic, typed, narrow, and independently testable. Tool names, type hints, and docstrings become part of the model-facing contract.

```python
from strands import Agent, tool


@tool
def lookup_order(order_id: str) -> dict[str, str]:
    """Return the current status of one order.

    Args:
        order_id: Public order identifier supplied by the customer.
    """
    # Authenticate and authorize in ordinary application code here.
    return {"order_id": order_id, "status": "processing"}


agent = Agent(
    name="order-support",
    description="Answers order-status questions for authorized customers.",
    system_prompt=(
        "Help with order status. Use lookup_order for factual status. "
        "Never invent order data or claim that an action succeeded without a tool result."
    ),
    tools=[lookup_order],
)

result = agent("What is happening with order A-1042?")
print(str(result))
```

For tools with side effects:

- Authenticate the caller outside the model and pass trusted identity through application state.
- Re-authorize inside the tool; never treat model-generated arguments as trusted.
- Validate inputs with normal Python code or schemas.
- Add idempotency keys for retryable writes.
- Set explicit network timeouts and bounded retries.
- Return concise, structured results. Do not leak secrets or raw internal exceptions.
- Require confirmation before destructive, costly, or externally visible actions.

The optional `strands-agents-tools` package is community maintained. Review each tool's permissions and implementation before production use, especially filesystem, shell, HTTP, browser, and code-execution tools.

## Select model providers deliberately

`Agent()` defaults to Bedrock because Strands is AWS-led and Bedrock support is included in the core package. When `model=None`, the SDK constructs a `BedrockModel` and uses the standard AWS credential chain. This makes the smallest AWS quickstart require no provider-specific package or API-key code. It is a convenience default, not an architectural requirement: Strands agents are model-provider agnostic.

Production code should make provider, model, region, and generation settings visible in configuration.

### Amazon Bedrock

```python
import os

from strands import Agent
from strands.models import BedrockModel


model = BedrockModel(
    model_id=os.environ["BEDROCK_MODEL_ID"],
    region_name=os.getenv("AWS_REGION", "us-west-2"),
    temperature=0.2,
)

agent = Agent(model=model, system_prompt="Answer accurately and concisely.")
```

### OpenAI Chat Completions API

Install the OpenAI integration and keep both the key and model ID in configuration:

```bash
python -m pip install 'strands-agents[openai]'
export OPENAI_API_KEY='...'
export OPENAI_MODEL_ID='your-approved-model-id'
```

```python
import os

from strands import Agent
from strands.models.openai import OpenAIModel


model = OpenAIModel(
    client_args={"api_key": os.environ["OPENAI_API_KEY"]},
    model_id=os.environ["OPENAI_MODEL_ID"],
)

agent = Agent(
    model=model,
    system_prompt="Answer accurately and use tools for external facts.",
)
result = agent("Explain what this service does.")
```

`OpenAIModel` uses the OpenAI Chat Completions interface. Add provider parameters through `params` only after checking that the configured model supports them.

### OpenAI Responses API

Use `OpenAIResponsesModel` when the application needs the OpenAI Responses API. Current Strands source requires OpenAI Python SDK 2.0 or newer for this provider.

```python
import os

from strands import Agent
from strands.models.openai_responses import OpenAIResponsesModel


model = OpenAIResponsesModel(
    client_args={"api_key": os.environ["OPENAI_API_KEY"]},
    model_id=os.environ["OPENAI_MODEL_ID"],
    params={"max_output_tokens": 1200},
    stateful=False,
)

agent = Agent(model=model, system_prompt="Return a concise implementation analysis.")
result = agent("Analyze the proposed API boundary.")
```

Keep `stateful=False` when Strands owns conversation history. Turn it on only after designing how OpenAI-side response state and Strands-side sessions interact.

### OpenAI-compatible endpoints

`OpenAIModel` can also call an OpenAI-compatible gateway or local server:

```python
model = OpenAIModel(
    client_args={
        "api_key": os.environ["OPENAI_COMPATIBLE_API_KEY"],
        "base_url": os.environ["OPENAI_COMPATIBLE_BASE_URL"],
    },
    model_id=os.environ["OPENAI_COMPATIBLE_MODEL_ID"],
)
```

Compatibility varies. Test tool calling, streaming, structured output, stop sequences, and error mapping against the actual endpoint.

### Provider factory

Keep provider selection out of agent and orchestration code:

```python
import os

from strands.models import BedrockModel
from strands.models.openai import OpenAIModel


def build_model():
    provider = os.getenv("MODEL_PROVIDER", "bedrock")

    if provider == "bedrock":
        return BedrockModel(
            model_id=os.environ["BEDROCK_MODEL_ID"],
            region_name=os.getenv("AWS_REGION", "us-west-2"),
        )

    if provider == "openai":
        return OpenAIModel(
            client_args={"api_key": os.environ["OPENAI_API_KEY"]},
            model_id=os.environ["OPENAI_MODEL_ID"],
        )

    raise ValueError(f"Unsupported MODEL_PROVIDER: {provider}")
```

Other providers use their provider classes, for example `strands.models.anthropic.AnthropicModel`. Read the current provider page for supported options, tool use, streaming, caching, and structured-output behavior.

Keep provider-specific construction behind a small factory so application and orchestration code depend on the Strands model interface. Test each configured provider; model capabilities are not identical.

## Bound agent and orchestration loops

The word "loop" can refer to different counters. Configure the counter that matches the failure mode:

| Scope | Limit | What it counts |
|---|---|---|
| One `Agent` invocation | `limits["turns"]` | Model calls; one turn is one model call plus its following tool execution |
| One `Agent` invocation | `limits["output_tokens"]` | Cumulative model-generated tokens |
| One `Agent` invocation | `limits["total_tokens"]` | Cumulative input plus output tokens |
| `Swarm` | `max_iterations` | Total agent-node executions in the swarm |
| `Swarm` | `max_handoffs` | Transfers among agents or back to the user |
| `Graph` | `set_max_node_executions()` | Total graph-node executions, including revisits |

Bound one agent invocation like this:

```python
from strands import Agent


agent = Agent()
result = agent(
    "Investigate the incident and summarize the evidence.",
    limits={
        "turns": 6,
        "output_tokens": 2500,
        "total_tokens": 15000,
    },
)

if result.stop_reason == "limit_turns":
    print("The agent reached its six-turn loop budget.")
elif result.stop_reason == "limit_total_tokens":
    print("The agent reached its total-token budget.")
elif result.stop_reason == "limit_output_tokens":
    print("The agent reached its output-token budget.")
```

Limits apply to one invocation and reset when the agent is called again. They are checked at turn boundaries, so a model response may slightly overshoot a token cap and a tool already requested by the previous model call runs to completion.

Swarm and Graph limits bound orchestrator node executions; they do not set each child agent's internal `limits["turns"]`. If strict per-child turn budgets are required, invoke bounded child agents through an application-owned adapter or use explicit workflow/Graph nodes whose invocation policy you control. Do not assume `max_iterations=6` means six model calls.

## Return structured data to applications

Use Pydantic output models whenever code, not a person, consumes the answer. Prefer the invocation parameter; the older `Agent.structured_output()` methods are deprecated in current Python documentation.

```python
from pydantic import BaseModel, Field
from strands import Agent
from strands.types.exceptions import StructuredOutputException


class TicketDecision(BaseModel):
    category: str
    priority: int = Field(ge=1, le=5)
    explanation: str


agent = Agent(system_prompt="Classify support tickets using the supplied schema.")

try:
    result = agent(
        "Payment was captured twice.",
        structured_output_model=TicketDecision,
    )
    decision = result.structured_output
except StructuredOutputException as exc:
    # Map this to a stable application error or retry policy.
    raise RuntimeError("The model did not return a valid ticket decision") from exc
```

Schemas validate shape, not truth. Continue to validate identifiers, permissions, business rules, and side effects in application code.

## Own conversation state explicitly

Distinguish these concepts:

- Conversation management controls what fits in the current model context window.
- Agent state holds application values used during an agent's lifetime.
- Session management persists messages and state across invocations or restarts.
- Long-term memory stores selected information across sessions; it is not the same as chat history.

An `Agent` contains mutable conversation state and rejects concurrent invocation by default. For servers, never share one conversational agent across unrelated callers.

Choose one of these designs:

- Stateless request: create a fresh agent per request.
- Stateful session: create or restore one agent per authenticated session and serialize invocations for that session.
- A2A service: use `A2AServer(agent_factory=...)`, which creates a dedicated agent for each A2A context.

For local persistence, Strands provides `FileSessionManager`. Use a shared durable backend or a supported production integration when replicas must resume the same session. Do not rely on local files or in-memory maps across multiple containers.

For `Graph` and `Swarm`, attach the session manager to the orchestrator, not to the child agents. Current Python Strands rejects child agents with their own session managers inside these orchestrators.

## Build multi-agent systems

Give every agent a distinct responsibility, name, description, narrow tool set, and completion condition. If two agents have the same prompt and permissions, they probably should be one agent.

### Agents as tools: default delegation pattern

Use this for a coordinator with bounded specialists. `preserve_context=False` makes each specialist call start from its original state.

```python
from strands import Agent


researcher = Agent(
    name="researcher",
    description="Finds and summarizes evidence for a focused question.",
    system_prompt="Research the requested question and distinguish evidence from inference.",
)

writer = Agent(
    name="writer",
    system_prompt="Write only after delegating factual research to the researcher.",
    tools=[researcher.as_tool(preserve_context=False)],
)

result = writer("Explain the tradeoffs of event sourcing in two paragraphs.")
```

Use `preserve_context=True` only when the specialist intentionally needs continuity across calls. Do not combine `preserve_context=False` with a session-managed specialist.

### Graph: explicit structure and distributed nodes

Use Graph when dependencies and permitted transitions should be visible in code. Always bound execution, especially for cycles.

```python
from strands import Agent
from strands.multiagent import GraphBuilder


def build_graph():
    researcher = Agent(name="researcher", system_prompt="Collect relevant evidence.")
    reviewer = Agent(name="reviewer", system_prompt="Check evidence and identify gaps.")
    writer = Agent(name="writer", system_prompt="Produce the final answer from prior results.")

    builder = GraphBuilder()
    builder.add_node(researcher, "research")
    builder.add_node(reviewer, "review")
    builder.add_node(writer, "write")
    builder.add_edge("research", "review")
    builder.add_edge("review", "write")
    builder.set_entry_point("research")
    builder.set_execution_timeout(300)
    builder.set_node_timeout(120)
    builder.set_max_node_executions(10)
    return builder.build()


graph = build_graph()
result = graph("Assess the proposed database migration plan.")
print(result.to_dict())
```

Use conditional edges for business-visible routing. Test every branch, missing dependency, timeout, and failure path. Remote `A2AAgent` instances can be Graph nodes in Python.

Call the Graph directly from another Python application by importing its factory. Create a fresh Graph per unrelated request unless session ownership and serialized access are intentional:

```python
# reporting_app.py
from orchestrators import build_graph


def create_migration_review(plan: str) -> dict:
    result = build_graph()(plan)
    return result.to_dict()
```

### Swarm: autonomous local handoffs

Use Swarm only when peers should choose who works next. Strong descriptions are routing metadata. Bound handoffs, iterations, and time.

```python
from strands import Agent
from strands.multiagent import Swarm


def build_swarm() -> Swarm:
    researcher = Agent(
        name="researcher",
        description="Collects evidence and hands off when evidence is sufficient.",
        system_prompt="Gather evidence, record sources, then hand off to the analyst.",
    )
    analyst = Agent(
        name="analyst",
        description="Analyzes evidence, identifies patterns, and drafts conclusions.",
        system_prompt="Analyze the research, state uncertainties, then hand off for review.",
    )
    reviewer = Agent(
        name="reviewer",
        description="Challenges claims, requests missing evidence, and approves the final summary.",
        system_prompt="Review claims against evidence and finish only when gaps are resolved.",
    )

    return Swarm(
        [researcher, analyst, reviewer],
        entry_point=researcher,
        max_handoffs=6,
        max_iterations=8,
        execution_timeout=300,
        node_timeout=120,
        repetitive_handoff_detection_window=4,
        repetitive_handoff_min_unique_agents=2,
    )


swarm = build_swarm()

result = swarm("Produce a reviewed evidence summary.")
print("status:", result.status.value)
print("agents:", [node.node_id for node in result.node_history])
print("node executions:", result.execution_count)
```

`max_iterations=8` limits total Swarm agent-node executions; `max_handoffs=6` independently limits transfers. When a safety bound is exceeded, the Swarm result is failed rather than silently continuing. These bounds do not cap each agent's internal model/tool turns.

Call the Swarm from another Python application through the factory:

```python
# evidence_app.py
from orchestrators import build_swarm


async def produce_evidence_summary(topic: str) -> dict:
    result = await build_swarm().invoke_async(topic)
    return result.to_dict()
```

Do not place `A2AAgent` directly in a Swarm; current Strands documentation says remote A2A agents are not supported there. Wrap a remote agent as an orchestrator tool or use a Graph.

### Workflow: fixed operational DAG

Use a workflow when task dependencies are predetermined, independent tasks should run in parallel, and the run is non-conversational. A workflow is acyclic and downstream tasks receive selected dependency outputs. In Python, either implement the DAG in application code or use the current `workflow` tool from `strands-agents-tools` after verifying its installed API.

## Distribute agents with A2A

Prefer A2A when another agent must discover capabilities, exchange protocol messages, stream task progress, or interoperate across frameworks. A2A exposes an agent card and standard protocol endpoints; it is more than a custom JSON wrapper.

### Serve a Strands agent over A2A

Install `strands-agents[a2a]`. Use an agent factory for caller isolation; the single-agent server form is deprecated and is unsafe for multiple conversations.

```python
from strands import Agent
from strands.multiagent.a2a import A2AServer


def create_agent(context_id: str) -> Agent:
    return Agent(
        name="policy-agent",
        description="Answers questions from the approved policy corpus.",
        system_prompt="Use only approved policy tools and cite the supporting record.",
        callback_handler=None,
    )


server = A2AServer(
    agent_factory=create_agent,
    host="0.0.0.0",
    port=9000,
    max_contexts=1000,
)
server.serve()
```

The factory's `context_id` is the place to select a context-scoped session manager and tenant configuration. Do not use it as authorization by itself; authenticate the transport and map the verified identity to allowed tenant/session state.

For reverse proxies or path-based load balancers, configure the server's public `http_url` and mounting behavior from the current A2A documentation. The advertised agent-card URL must match the externally reachable HTTPS address.

### Consume a remote A2A agent

```python
from strands.agent.a2a_agent import A2AAgent


remote = A2AAgent(
    endpoint="https://agents.example.com/policy",
    name="policy-agent",
    timeout=60,
)

result = remote("What is the retention period for audit logs?")
print(str(result))
```

For async services use `await remote.invoke_async(...)`; for streaming use `remote.stream_async(...)` and handle the version's typed A2A stream events plus the final result event.

Use the A2A SDK `ClientConfig` with a configured HTTP client for OAuth, bearer tokens, SigV4, mTLS-related transport, custom headers, and timeouts. Do not put credentials in prompts or agent cards. Verify the exact `ClientConfig` API against the installed A2A SDK.

### Compose local and remote agents

Use a remote agent as a Python Graph node:

```python
from strands import Agent
from strands.agent.a2a_agent import A2AAgent
from strands.multiagent import GraphBuilder


local = Agent(name="local-reviewer", system_prompt="Review the remote analysis.")
remote = A2AAgent(
    endpoint="https://agents.example.com/analyzer",
    name="remote-analyzer",
    timeout=60,
)

builder = GraphBuilder()
builder.add_node(remote, "analyze")
builder.add_node(local, "review")
builder.add_edge("analyze", "review")
builder.set_execution_timeout(180)
builder.set_node_timeout(90)
graph = builder.build()
```

Alternatively wrap the `A2AAgent` call in a `@tool` for a coordinator. Convert remote errors into a small, stable error contract and preserve correlation IDs.

### Expose a Swarm or Graph through an A2A gateway

`A2AServer` serves a Strands `Agent`, not a `Swarm` or `Graph` directly. To make orchestrators available to A2A-capable applications, expose them as tools on a gateway agent. Create a fresh orchestrator for every tool call:

```python
from strands import Agent, tool
from strands.multiagent.a2a import A2AServer

from orchestrators import build_graph, build_swarm


@tool
def run_evidence_swarm(task: str) -> dict:
    """Run the three-agent evidence Swarm.

    Args:
        task: Evidence-gathering task for the Swarm.
    """
    return build_swarm()(task).to_dict()


@tool
def run_review_graph(task: str) -> dict:
    """Run the structured research-review-writing Graph.

    Args:
        task: Review task for the Graph.
    """
    return build_graph()(task).to_dict()


def create_gateway(context_id: str) -> Agent:
    return Agent(
        name="orchestration-gateway",
        description="Runs the approved evidence Swarm and review Graph.",
        system_prompt=(
            "Select exactly one orchestration tool for the requested job. "
            "Return its status and final result without inventing missing output."
        ),
        tools=[run_evidence_swarm, run_review_graph],
        callback_handler=None,
    )


A2AServer(agent_factory=create_gateway, host="0.0.0.0", port=9000).serve()
```

Another A2A-capable harness discovers and calls this gateway as an agent. Preserve the distinction in telemetry: the A2A task invokes a gateway Agent, which then invokes a local Swarm or Graph tool.

## Expose an application-specific HTTPS API

Prefer ordinary HTTPS when a web/mobile/backend application needs a stable business API rather than agent discovery and task semantics. Keep the agent behind an application service; do not expose provider credentials or raw tool access to browsers.

This minimal FastAPI example is intentionally stateless and creates a fresh agent per request:

```python
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from strands import Agent


app = FastAPI(title="Support Agent API", version="1.0.0")


class InvokeRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=20_000)


class InvokeResponse(BaseModel):
    message: dict[str, Any]


def build_agent() -> Agent:
    return Agent(
        name="support-agent",
        system_prompt="Answer support questions using approved tools.",
        callback_handler=None,
    )


@app.post("/v1/invocations", response_model=InvokeResponse)
async def invoke(request: InvokeRequest) -> InvokeResponse:
    try:
        result = await build_agent().invoke_async(request.prompt)
        return InvokeResponse(message=result.message)
    except Exception as exc:
        # Log exc with a request ID; do not return internal details.
        raise HTTPException(status_code=502, detail="Agent invocation failed") from exc


@app.get("/healthz")
async def health() -> dict[str, str]:
    return {"status": "ok"}
```

Expose the reusable Swarm and Graph factories through separate, versioned endpoints. Create a fresh orchestrator per stateless request because child agents and orchestrators hold mutable execution state:

```python
# Add to the FastAPI service above.
from orchestrators import build_graph, build_swarm


@app.post("/v1/swarm/invocations")
async def invoke_swarm(request: InvokeRequest) -> dict[str, Any]:
    try:
        result = await build_swarm().invoke_async(request.prompt)
        return result.to_dict()
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Swarm invocation failed") from exc


@app.post("/v1/graph/invocations")
async def invoke_graph(request: InvokeRequest) -> dict[str, Any]:
    try:
        result = await build_graph().invoke_async(request.prompt)
        return result.to_dict()
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Graph invocation failed") from exc
```

Another application can call either endpoint with an ordinary HTTP client:

```python
import httpx


def run_remote_orchestrator(kind: str, prompt: str) -> dict:
    if kind not in {"swarm", "graph"}:
        raise ValueError("kind must be 'swarm' or 'graph'")

    response = httpx.post(
        f"https://agents.example.com/v1/{kind}/invocations",
        json={"prompt": prompt},
        headers={"Authorization": "Bearer <application-token>"},
        timeout=360,
    )
    response.raise_for_status()
    return response.json()
```

Replace the literal token with an application credential provider. For long-running work, return a job ID and process the orchestrator in a worker instead of keeping one HTTP request open indefinitely.

For conversational HTTPS APIs, accept an authenticated `session_id`, restore a session-scoped agent, and serialize calls per session. Define session expiry, deletion, tenant isolation, and replica-safe persistence. Never use one global conversational `Agent` for concurrent users.

For streaming to applications, translate `agent.stream_async()` events into a documented SSE or NDJSON contract. Emit stable event types such as `text_delta`, `tool_status`, `final`, and `error`; do not expose unstable internal event dictionaries directly as a public API.

## Use agents from other applications

Choose the adapter based on the consumer:

- Python application in the same trust boundary: import a factory function and invoke the agent directly.
- Another Strands service: use `A2AAgent` or a shared Python package for in-process use.
- Agent built with another framework: use A2A if both sides support the protocol.
- Web, mobile, or backend application: call an authenticated HTTPS API; use SSE/WebSocket only when interaction requires streaming or bidirectional events.
- Event-driven system: put a versioned task envelope on a queue and run the agent in an idempotent worker.
- Batch/data pipeline: call a stateless function or worker with structured inputs and outputs; avoid conversational state.

Define a versioned boundary containing only what consumers need. Common fields include `request_id`, authenticated tenant/user context, `session_id`, typed input, deadline, response schema version, status, output, error code, usage metadata, and trace ID.

Never make external applications parse prose when a schema is available. Never expose full prompts, chain-of-thought, secrets, or raw internal exceptions as part of the contract.

### Example: same-process Python application

Import a factory when the caller and Strands code deploy together:

```python
from agent_factory import build_agent


def answer_support_question(question: str) -> str:
    agent = build_agent()
    result = agent(question, limits={"turns": 5, "total_tokens": 12000})
    return str(result)
```

### Example: backend application over HTTPS

Use a typed client around the versioned endpoint instead of spreading raw HTTP calls throughout the codebase:

```python
import httpx


class AgentServiceClient:
    def __init__(self, base_url: str, token: str) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=120,
        )

    def invoke(self, prompt: str) -> dict:
        response = self._client.post("/v1/invocations", json={"prompt": prompt})
        response.raise_for_status()
        return response.json()
```

### Example: another agent or harness over A2A

Use A2A when the consumer understands agent cards and A2A tasks:

```python
from strands.agent.a2a_agent import A2AAgent


policy_agent = A2AAgent(
    endpoint="https://agents.example.com/policy",
    timeout=60,
)
result = policy_agent("Check whether this retention policy is compliant.")
```

An A2A-capable non-Strands harness can consume the same server using its own A2A client. A harness that supports only MCP should use the MCP adapter below instead.

### Example: event-driven application

Publish a versioned task and let a worker create the orchestrator. The queue message should contain references, not secrets or large documents:

```python
def handle_job(message: dict) -> dict:
    task = message["task"]
    kind = message["orchestrator"]

    if kind == "swarm":
        return build_swarm()(task).to_dict()
    if kind == "graph":
        return build_graph()(task).to_dict()
    raise ValueError(f"Unsupported orchestrator: {kind}")
```

## Use Agent, Swarm, and Graph from Codex or another harness

Codex documents MCP, not A2A, as its external tool integration surface. Expose Strands components as MCP tools when Codex, ChatGPT desktop, an IDE agent, or another MCP-capable harness must invoke them. Use the A2A gateway above for harnesses that support A2A instead.

### Create a Streamable HTTP MCP adapter

The core Strands package already depends on the Python MCP SDK. This server exposes one tool for each execution style and creates fresh state per call:

```python
from mcp.server import FastMCP

from agent_factory import build_agent
from orchestrators import build_graph, build_swarm


mcp = FastMCP("Strands Orchestrators")


@mcp.tool(description="Run the stateless support agent")
async def run_agent(prompt: str) -> dict:
    result = await build_agent().invoke_async(
        prompt,
        limits={"turns": 5, "total_tokens": 12000},
    )
    return result.to_dict()


@mcp.tool(description="Run the three-agent evidence swarm")
async def run_swarm(prompt: str) -> dict:
    result = await build_swarm().invoke_async(prompt)
    return result.to_dict()


@mcp.tool(description="Run the structured review graph")
async def run_graph(prompt: str) -> dict:
    result = await build_graph().invoke_async(prompt)
    return result.to_dict()


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

Run the server locally; the default FastMCP Streamable HTTP endpoint is typically `http://127.0.0.1:8000/mcp/`. Put remote deployments behind HTTPS and OAuth or bearer-token authentication. Do not expose an unauthenticated orchestration server to the internet.

### Connect Codex

Add the running MCP endpoint with the Codex CLI:

```bash
codex mcp add strands-orchestrators --url http://127.0.0.1:8000/mcp/
codex mcp list
```

Or configure it in `~/.codex/config.toml` or a trusted project's `.codex/config.toml`:

```toml
[mcp_servers.strands_orchestrators]
url = "http://127.0.0.1:8000/mcp/"
tool_timeout_sec = 360
required = true
enabled_tools = ["run_agent", "run_swarm", "run_graph"]
```

Restart the Codex client after changing MCP configuration, then verify the server and tools with `/mcp`. A task can now say, for example:

```text
Use the run_graph tool to assess this migration plan, then compare its review with the repository implementation.
```

The same MCP server can be registered in another MCP-capable harness using that product's Streamable HTTP MCP configuration. Preserve tool names and JSON result shapes so consumers do not depend on prompts or Strands internals.

### Choose the harness boundary

| Consumer | Recommended boundary |
|---|---|
| Codex CLI, IDE extension, or desktop app | MCP server |
| Another MCP-capable coding/agent harness | Same MCP server |
| A2A-capable agent framework | Native A2A agent or A2A gateway |
| Web/mobile/business backend | Versioned HTTPS API |
| Same Python deployment | Direct factory import |
| CI or asynchronous processing | Queue worker or HTTPS job API |

Do not present MCP, A2A, and REST as interchangeable wire formats. They can expose the same underlying factory, but discovery, authentication, streaming, errors, and lifecycle semantics differ.

## Production requirements

### Reliability

- Set invocation, model, tool, node, graph/swarm, and network deadlines.
- Bound turns, handoffs, cycles, output size, and token/cost budgets.
- Retry only transient, idempotent operations with backoff and jitter.
- Propagate cancellation and deadlines to tools and remote agents.
- Use circuit breakers and bulkheads around remote agents and providers.
- Define partial-failure behavior for multi-agent runs.
- Use health/readiness probes that do not invoke a paid model on every check.

### Security

- Authenticate users and services before agent invocation.
- Authorize every tool action against trusted identity and tenant context.
- Keep model and service credentials in a secret manager or workload identity.
- Treat prompts, retrieved documents, tool results, and remote agents as untrusted input.
- Constrain filesystem, shell, network, browser, and code-execution capabilities.
- Protect against SSRF, prompt injection, data exfiltration, cross-tenant state access, and unsafe deserialization.
- Redact sensitive content from logs, traces, exceptions, and model inputs where required.
- Put public A2A/HTTPS endpoints behind TLS, rate limits, request limits, and abuse controls.

### Observability

Use structured logs and OpenTelemetry-compatible traces. Correlate the incoming request with model calls, tools, child agents, A2A calls, retries, and the final outcome. Record latency, token usage, provider/model, tool success, handoffs, stop reason, errors, and cost signals without recording sensitive prompt content by default.

### Deployment

Package the service in a container and run it on the platform that matches its workload: AgentCore Runtime, App Runner, ECS/Fargate, EKS, Lambda where execution constraints fit, EC2, or another container platform. Keep state outside ephemeral containers, use graceful shutdown, drain in-flight requests, and scale on concurrency and latency rather than CPU alone.

## Test before deployment

Test at four layers:

1. Tools: ordinary unit tests for validation, authorization, idempotency, timeouts, and side effects.
2. Agent contract: controlled model responses for tool selection, structured output, stop conditions, and error recovery.
3. Orchestration: every Graph branch, Swarm bound, handoff path, remote failure, and state restoration behavior.
4. End to end: representative tasks against the configured provider and deployed A2A/HTTPS boundary.

Maintain an evaluation set with normal, ambiguous, adversarial, unauthorized, and failure-inducing requests. Assert both answer quality and prohibited actions. Run regression evaluations when prompts, tools, models, provider settings, or orchestration change.

Before claiming completion, verify:

- Imports and signatures against the locked SDK version.
- All code examples at least import and construct without live credentials where possible.
- Tool unit tests and contract tests pass.
- Structured outputs validate.
- Concurrent callers cannot share unintended state.
- Timeouts, cancellation, and retry behavior are exercised.
- A2A agent-card URLs and HTTPS routes work through the real proxy/load balancer.
- Logs and traces correlate a request without leaking secrets.
- Documentation states the chosen model, state owner, protocol, and deployment assumptions.

## Common mistakes

- Assuming shared SQL or a load balancer makes in-memory agent state safe across replicas.
- Sharing one mutable agent instance across unrelated or concurrent HTTP callers.
- Using multi-agent orchestration where a deterministic Python function would be clearer.
- Giving every specialist every tool.
- Omitting Graph/Swarm execution bounds.
- Putting a remote `A2AAgent` directly into a Swarm.
- Using a deprecated single-agent `A2AServer` for multiple callers.
- Treating conversation-window management as durable session storage or long-term memory.
- Parsing free-form model text in another application instead of using structured output.
- Retrying side-effecting tools without idempotency.
- Exposing provider keys, raw internal events, or exception messages to clients.
- Copying old imports, default model IDs, or A2A examples without checking the installed release.

## Official references

- Documentation: https://strandsagents.com/
- Python quickstart: https://strandsagents.com/docs/user-guide/quickstart/python/
- Model providers: https://strandsagents.com/docs/user-guide/concepts/model-providers/
- OpenAI model provider: https://strandsagents.com/docs/user-guide/concepts/model-providers/openai/
- Agent loop and invocation limits: https://strandsagents.com/docs/user-guide/concepts/agents/agent-loop/
- Multi-agent patterns: https://strandsagents.com/docs/user-guide/concepts/multi-agent/multi-agent-patterns/
- Agents as tools: https://strandsagents.com/docs/user-guide/concepts/multi-agent/agents-as-tools/
- Graph: https://strandsagents.com/docs/user-guide/concepts/multi-agent/graph/
- Swarm: https://strandsagents.com/docs/user-guide/concepts/multi-agent/swarm/
- A2A: https://strandsagents.com/docs/user-guide/concepts/multi-agent/agent-to-agent/
- Sessions: https://strandsagents.com/docs/user-guide/concepts/agents/session-management/
- Structured output: https://strandsagents.com/docs/user-guide/concepts/agents/structured-output/
- Streaming: https://strandsagents.com/docs/user-guide/concepts/streaming/async-iterators/
- Observability: https://strandsagents.com/docs/user-guide/observability-evaluation/observability/
- Official monorepo: https://github.com/strands-agents/harness-sdk
- Official samples: https://github.com/strands-agents/samples
- A2A standard: https://a2aproject.github.io/A2A/latest/
- Codex MCP configuration: https://learn.chatgpt.com/docs/extend/mcp
