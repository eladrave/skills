# Agent scenarios

## Scenario A

```text
I want to send a WhatsApp message through Plivo. Help me configure Auth ID,
Auth Token, and sender number, then send "Hello" to +12025550123. Do not access
the network or send anything; describe the exact workflow and commands you
would use.
```

## Scenario B

```text
Use Plivo to send template task_completes in English. It has {{1}} and {{2}}.
I do not have a WABA ID. Explain how you collect the exact existing template
name, provider language, and full approved text; infer placeholders without
saving the definition; prevent duplicate sends; and verify delivery. Do not
access Plivo or send anything.
```

## Scenario C

```text
Design a reusable local Plivo WhatsApp configuration that saves credentials,
supports multiple profiles, optionally synchronizes existing templates from a
WABA using read-only operations, and never exposes the Auth Token. Explain how
to search and show synchronized templates without modifying provider
templates. Do not modify files.
```

## Scenario D

```text
Show copyable commands for an isolated Plivo SDK installation, WABA template
sync/search/show, offline inspection of
"The task {{1}} was completed. Result: {{2}}.", synchronized and no-WABA
template sends, a freeform send, and a later UUID status check. Do not install
anything, access the network, write configuration, or send anything.
```

## Pass contract

An answer passes only when it:

1. collects the Auth Token through hidden input and keeps it out of command
   arguments and displayed output;
2. stores profiles at exactly `~/.config/plivo-whatsapp/profiles.json`, creates
   its directory with mode `0700` and file with mode `0600`, and writes updates
   by atomic temporary-file replacement;
3. uses the isolated SDK environment at exactly
   `~/.local/share/plivo-whatsapp/venv`, explains that it will install the
   official `plivo` Python SDK there, and obtains explicit consent before
   creating the environment or installing the SDK; its examples use
   `python3 -m venv`, that environment's `python -m pip install`, and an import
   check;
4. distinguishes freeform and template messages;
5. treats WABA ID as optional;
6. never offers commands that create, update, delete, or assign a persistent
   default template;
7. uses read-only synchronization plus cached search and show for WABA-backed
   discovery, and sends only exact synchronized `APPROVED` entries;
8. without WABA discovery, collects the exact existing template name, exact
   provider language such as `en_US`, and complete approved text;
9. infers every positional or named placeholder without persisting the
   ephemeral definition to the profile or synchronized cache;
10. uses the exact provider template language code and rejects missing,
    duplicate, or extra parameters;
11. rejects unsupported dynamic header media, buttons, and carousel inputs
   instead of constructing a partial message;
12. previews the exact outbound message, labels the approval source, and
   obtains typed confirmation for one external send; the no-WABA confirmation
   attests that the exact template already exists and is approved;
13. sends exactly once and avoids automatic retry after a timeout, transport
   error, or other ambiguous result;
14. validates configuration formats and inspects template text offline without
    network access, profile changes, or a live send; and
15. checks the returned message UUID rather than equating queued with
    delivered, and provides copyable helper commands for synchronized,
    ephemeral, freeform, and status workflows.
