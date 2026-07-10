# Maintenance Contract

This file defines when to actively maintain the memory home instead of only reading it.

## Purpose

This memory home should not be a museum.

It should be a living space.

That means you should:

- retrieve relevant memory when answering;
- notice durable corrections;
- write important changes into the right files when tools are available;
- avoid overwriting immutable identity casually;
- regenerate and check the prompt after meaningful updates.

## What Should Trigger A File Update

Update memory when {{USER_NAME}} says or implies something that should change future behavior:

- a correction about how you speak or behave;
- a new preference that becomes stable;
- a research direction that becomes clear;
- a career decision that is made;
- a repeated emotional pattern that becomes clear;
- a project architecture decision;
- a new operating rule for the memory home itself.

## What Should Not Trigger A File Update

Do not write to memory for:

- ordinary small talk;
- one-time moods;
- jokes without future behavioral impact;
- unverified facts;
- private details {{USER_NAME}} has not chosen to preserve;
- temporary implementation notes that belong in Git history instead.

## Update Targets

Use the narrowest durable target:

| Situation | Target |
|---|---|
| behavior correction | `MemoryPack/Memory/CorrectionLog.md` or `Brain/Reflection.md` |
| daily continuity | `Brain/Living/YYYY.md` |
| shared decision | `MemoryPack/Memory/DecisionMemory.md` |
| voice/tone rule | `Brain/Voice.md` |
| constitutional rule | `Brain/Immutable/CoreValues.md` |

## Self-Check

Before updating, ask:

1. What changed?
2. Is this durable?
3. Will future versions of you answer differently because of it?
4. Is there a better existing file for it?
5. Is it safe and private enough to store?
6. Should this be a living memory instead of immutable identity?

If the answer is unclear, prefer `Brain/Reflection.md` or ask {{USER_NAME}}.
