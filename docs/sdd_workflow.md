# Spec-Driven Development (SDD) with AI Agents

> **Purpose of this document:** A didactic guide to the development workflow followed in this project, written for students learning software development in an era of AI coding assistants. It explains *why* we work this way, *what* the key concepts mean, and *how* tools like GitHub Copilot fit into the picture.

---

## Table of Contents

1. [What is Spec-Driven Development?](#1-what-is-spec-driven-development)
2. [Key Industry Concepts](#2-key-industry-concepts)
3. [The SDD Lifecycle](#3-the-sdd-lifecycle)
4. [Why SDD and AI Agents Are a Natural Fit](#4-why-sdd-and-ai-agents-are-a-natural-fit)
5. [Applied to This Project](#5-applied-to-this-project)
6. [Related Methodologies](#6-related-methodologies)
7. [Tooling: GitHub Copilot in VS Code](#7-tooling-github-copilot-in-vs-code)
8. [Common Pitfalls](#8-common-pitfalls)
9. [Summary](#9-summary)

---

## 1. What is Spec-Driven Development?

**Spec-Driven Development (SDD)** is a software development approach where a formal specification document is the primary driver of every decision: what to build, in what order, and how to verify it is complete.

The central idea is simple:

> *Write the spec first. Then build exactly what the spec says. Then verify against the spec.*

This sounds obvious, but in practice many projects skip or rush the specification phase, letting the implementation define the product instead of the requirements. SDD inverts that: the spec is the source of truth, and the code is the artifact that satisfies it.

### What a spec contains

A good specification document (like this project's [`specs.md`](../specs.md)) includes:

| Section | Purpose |
|---------|---------|
| **Product Overview** | One paragraph describing what and for whom |
| **Goals / Non-Goals** | Explicit boundary: what is *in* and what is *out* |
| **Actors** | Who uses the system and in what role |
| **Functional Requirements** | Numbered, traceable requirements (FR-1, FR-2, …) |
| **Business Rules** | Domain constraints that must always hold |
| **Quality Attributes** | Non-functional requirements (performance, security, portability) |
| **Data Model** | Structure of the data to be persisted |
| **Acceptance Criteria** | The conditions that prove the system works correctly |

The spec is a living document — it changes as the product evolves — but it always precedes the code that implements it.

---

## 2. Key Industry Concepts

### Proof of Concept (PoC)

A **Proof of Concept** is a minimal, often throwaway implementation built to answer a specific technical or product question: *"Can this actually be done? Does the core idea work?"*

A PoC is **not** meant for production. It trades quality, architecture, and completeness for speed. The goal is to reduce uncertainty and validate assumptions before committing to a full build.

**In this project:** The first iteration was a PoC that answered: *"Can we build a desktop stats tracker with Python + Tkinter + SQLite that a hockey team manager could realistically use?"* It was shown to the client (the team) to verify the concept made sense.

**Key distinction:** A PoC proves an idea is feasible. An MVP delivers actual value to actual users.

---

### Minimum Viable Product (MVP)

A **Minimum Viable Product** is the simplest version of a product that delivers real value to real users and generates feedback. Every feature in an MVP is there for a reason; nothing extra is built.

Eric Ries, who popularized the term in *The Lean Startup*, defines it as: *"That version of a new product which allows a team to collect the maximum amount of validated learning about customers with the least effort."*

The word "viable" is important — a PoC is often not viable (a user couldn't actually use it day to day), but an MVP is. It is usable, even if limited.

**In this project:** The current version (v0.2) is the MVP. It implements all the requirements from [`specs.md`](../specs.md): roster management, game entry, season stats dashboard, game corrections, and email notifications. A team staff member could use it today to manage a real season.

**Key distinction:** MVP ≠ "bad quality". MVP means minimum *scope*. Quality attributes (correctness, reliability, architecture) still matter.

---

### Iteration

An **iteration** is a time-boxed cycle of: plan → build → demo → gather feedback → plan again.

Each iteration produces a working increment of the product and ends with a meeting with the stakeholder (client, user representative, or product owner) to:

1. Demonstrate what was built.
2. Validate it against the spec.
3. Collect new requirements, corrections, or priority changes.
4. Update the spec for the next iteration.

In this project, iterations are not strict sprints with fixed duration. Instead, they are driven by spec versions: a new major iteration begins when the client provides feedback significant enough to require a revised spec.

---

### Technical Debt

**Technical debt** is the accumulated cost of shortcuts taken to deliver faster. Like financial debt, it accrues interest: the longer it stays, the harder it becomes to work with the codebase.

SDD helps control technical debt by keeping scope explicit. When you have a clear spec, you can distinguish between *"this shortcut is deliberate and bounded"* (a PoC decision you plan to revisit) and *"this was never a good idea"* (unintentional debt).

In this project, the [open questions](../open_questions.md) document explicitly tracks decisions that were intentionally deferred — that is a form of honest, tracked technical debt.

---

## 3. The SDD Lifecycle

```
┌─────────────────────────────────────────────────────────────────────┐
│                           SDD LIFECYCLE                             │
│                                                                     │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    │
│   │  GATHER  │───▶│  WRITE   │───▶│  BUILD   │───▶│  DEMO &  │    │
│   │ REQUIREM.│    │  SPECS   │    │ (impl.)  │    │  VERIFY  │    │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘    │
│         ▲                                               │           │
│         └──────── client feedback ────────────────────┘           │
└─────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Gather Requirements

Meet with the client (a real person, not a document). The goal is to understand:
- What problem are they solving?
- Who does what today, and what is painful?
- What would "success" look like?

Output: raw notes, sketches, examples of existing artifacts (in this project, the score sheet PDF).

### Phase 2: Write or Update the Spec

Turn raw notes into a structured specification. This is the most important phase, and it is often the most neglected. Key practices:

- **Separate Out-of-Scope explicitly.** Listing Non-Goals prevents scope creep and is as important as the Goals list.
- **Number requirements.** FR-1, FR-2 etc. allow requirements to be referenced in code, tests, and conversations.
- **Write Acceptance Criteria before writing code.** These become your test cases.
- **Track open questions.** Not every decision can be made immediately. Document the unknowns rather than guessing.

### Phase 3: Design (if significant architecture changes)

For non-trivial features, produce an architecture or design artifact before coding. In this project, the class diagram ([`docs/class_diagram.md`](class_diagram.md)) and the architecture document ([`docs/architecture.md`](architecture.md)) are produced before the corresponding code is written.

Design artifacts do not need to be exhaustive. A diagram that captures the key relationships is enough.

### Phase 4: Build

Implement *only what the spec says*. The spec is your most important tool against scope creep, gold-plating (adding unrequested features), and premature optimization.

With AI agents (see §4), the spec also serves as the primary context for every prompt.

### Phase 5: Demo and Verify

Show the working software to the stakeholder. Walk through each acceptance criterion explicitly. This is not a sales presentation — it is a *verification session*:

- Does it do what the spec said?
- Does it do it in a way that works for actual users?

Collect feedback in structured notes. These become the input for the next iteration's requirements.

### Phase 6: Update the Spec, Repeat

Client feedback either:
1. **Confirms the spec was correct** → mark acceptance criteria as passed, close requirements.
2. **Reveals gaps or misunderstandings** → update the spec before writing more code.
3. **Introduces new requirements** → add to the spec with new FR numbers for the next iteration.

Track this history. See [`docs/iteration_log.md`](iteration_log.md) for this project's iteration history.

---

## 4. Why SDD and AI Agents Are a Natural Fit

AI coding assistants like GitHub Copilot can generate code, suggest implementations, and accelerate many routine tasks. But they have a fundamental limitation: **they do not know what you want to build unless you tell them.**

This is where SDD creates a structural advantage.

### Specs as Context

When you ask Copilot to implement a feature, the quality of the output depends entirely on the context you provide. A vague prompt produces vague code. A structured specification produces focused, traceable code.

Compare:

```
❌ "Add a way to enter game stats"

✅ "Implement FR-2 from specs.md: game input must capture date, opponent,
   season, game_type (regular|playoff), result (win|loss), optional notes.
   Per skater: optional jersey_number, goals, assists, pim, shg, ppg.
   Per goalie: optional jersey_number, saves, goals_against.
   shots_received is always computed as saves + goals_against.
   Validation: reject negative stats, unknown players, duplicate games
   (same season + date + opponent)."
```

The second prompt produces a testable, requirement-traceable implementation. The specification text *is* the prompt.

### Bounded Scope

One risk of AI-assisted development is that the agent adds features, refactors code, or makes "improvements" beyond what was requested. A clear spec gives you the authority to say: *"This is not in scope for this iteration."*

Acceptance criteria are particularly powerful here: you can verify the output point-by-point against the spec, and reject anything that goes beyond it.

### Verifiable Output

Because the spec contains acceptance criteria, you can immediately test whether the AI-generated code satisfies them. This creates a tight feedback loop:

```
Spec (AC) → Agent generates code → Run tests against AC → Adjust prompt → Repeat
```

This is very similar to Test-Driven Development (see §6), and the two approaches combine well.

### Traceability

With a numbered spec, every piece of code can be traced back to a requirement. This is valuable for:

- **Code review**: "Does this change satisfy FR-5?"
- **Debugging**: "This bug violates FR-4 (SV% calculation). The spec says exactly how it should work."
- **Handover**: A new developer (or a new AI session) can get up to speed by reading the spec.

### The Human Remains in Control

AI agents are tools, not architects. They can generate implementations efficiently, but they cannot:
- Understand the client's actual intent from a 10-minute conversation.
- Make trade-off decisions that involve product strategy.
- Know when to say "this is out of scope for this iteration."
- Detect when a requirement is contradictory or underspecified.

SDD keeps the developer in the architectural and requirements-driving seat. The AI accelerates the implementation phase; the developer owns the spec.

---

## 5. Applied to This Project

### Project structure reflects the spec

Every layer in the code maps to a section of the spec:

| Spec section | Code location |
|-------------|--------------|
| §4 Functional Requirements | `app/application/use_cases.py` (one method per use case) |
| §7 Clean Architecture / Domain | `app/domain/` (entities, value objects, services) |
| §7 Infrastructure | `app/infrastructure/` (SQLite repos, SMTP sender) |
| §7 Presentation | `app/ui/` (Tkinter GUI calls use cases only) |
| §8 Data Model | `app/infrastructure/sqlite_db.py` (schema creation) |
| §9 Acceptance Criteria | `tests/` (unit tests, one test class per AC) |

### The spec drives decisions explicitly

Consider FR-2's rule: *"ShotsReceived is always computed as Saves + GoalsAgainst... not a free-entry field."*

This single sentence explains:
- Why the UI shows a read-only computed label, not an input field.
- Why `GoalieGameStatInput` has no `shots_received` field.
- Why the DB stores `shots_received` (§8: "stored for query perf") — a deliberate, spec-justified decision.

Without the spec, each of those choices would be a mystery or an accident.

### Open questions as iteration fuel

The [`open_questions.md`](../open_questions.md) file is not a list of things that went wrong. It is the **input to the next iteration**. After the client demo, each open question becomes either:
- A confirmed requirement added to `specs.md`.
- A confirmed out-of-scope item added to Non-Goals.
- A deferred item that stays in open questions.

This is the SDD feedback loop in practice.

### The PoC → MVP progression

| Version | Type | What was validated |
|---------|------|-------------------|
| v0.1 | PoC | Core concept: Python desktop stats tracker is feasible and usable |
| v0.2 | MVP | Full requirements from client meeting: corrections, game types, playoff splits, email notifications, jersey numbers |

See [`docs/iteration_log.md`](iteration_log.md) for the full iteration history.

---

## 6. Related Methodologies

### Test-Driven Development (TDD)

**TDD** inverts the usual coding order: write a failing test first, then write the minimal code to pass it, then refactor.

SDD and TDD are complementary: in SDD, acceptance criteria from the spec become the test cases for TDD. The spec tells you *what* to test; TDD tells you *how* to write the tests and the code together.

In this project, the acceptance criteria in §9 of `specs.md` are the direct source for unit tests.

### Behavior-Driven Development (BDD)

**BDD** extends TDD by writing tests in natural language (often `Given / When / Then` syntax), making them readable by non-technical stakeholders.

BDD is essentially SDD + TDD with a shared language layer. The spec plays an even more central role: BDD specifications are literally executable tests written in business language.

### Agile / Scrum

Agile is an umbrella of iterative methodologies. SDD is not in conflict with Agile — they work at different levels. Agile defines the *process* (sprints, retrospectives, ceremonies); SDD defines the *artifact* that drives each sprint (the spec).

In practice: each sprint or iteration in an Agile process should start with a spec update, making SDD the documentation discipline *inside* the Agile process.

### Domain-Driven Design (DDD)

**DDD** focuses on modeling the business domain accurately in the code, using a "ubiquitous language" shared by developers and domain experts.

This project applies several DDD ideas:
- Domain entities (`Player`, `Game`, `SkaterGameStat`) map directly to concepts from the client's world.
- The domain layer is independent of infrastructure (no SQL in `domain/`).
- The spec *is* the ubiquitous language document — the terminology in `specs.md` matches the code.

---

## 7. Tooling: GitHub Copilot in VS Code

GitHub Copilot offers several interaction modes for AI-assisted development. The choice of mode matters for SDD workflows.

### Chat modes

| Mode | When to use with SDD |
|------|---------------------|
| **Ask** | Explain a spec requirement, ask for design options, explore trade-offs before writing code |
| **Agent** | Multi-file implementation tasks that reference the full spec context; also handles single-file changes |

### Effective prompting from a spec

When providing a spec as context to Copilot:

1. **Attach `specs.md` explicitly.** Do not assume the model remembers a previous message.
2. **Reference requirement numbers.** `"Implement FR-7 (Correct Game Stats)"` is more precise than a paraphrase.
3. **Paste the acceptance criteria.** They are the definition of done for the prompt.
4. **State Non-Goals.** *"Do not implement FR-8 (AI Ingestion) in this prompt."*
5. **Reference the architecture.** *"Follow the layering in `docs/architecture.md` — use cases in `application/`, no DB calls in `domain/`."*

### Custom instructions

VS Code Copilot supports workspace-level instruction files (`.github/copilot-instructions.md`, `.instructions.md` files, `.prompt.md` prompt files) that are automatically included in Copilot sessions. In a SDD project, the main instructions file can contain:

```markdown
This project follows Spec-Driven Development. The specification is in specs.md.
Architecture rules: domain/ has no infrastructure dependencies. 
Use cases in application/use_cases.py call repositories via Protocol interfaces.
UI in ui/ calls use cases only — no direct DB or domain access.
All changes must satisfy acceptance criteria in specs.md §9.
```

This makes every Copilot interaction automatically spec-aware.

> **This project does not yet have instruction files configured.** Adding them is planned for iteration 0.3 — see [`docs/iteration_log.md`](iteration_log.md).

### Agent mode and multi-file tasks

Agent mode is particularly powerful for implementing a complete requirement across multiple layers (domain model → use case → repository → UI). A good Agent mode prompt for SDD looks like:

```
Implement FR-6 (Manage Mailing List) from specs.md:
- Add/remove/list mail recipients
- MailRecipient entity: id, name, email
- SqliteMailingListRepository following the pattern in sqlite_db.py
- Add use cases add_mail_recipient, remove_mail_recipient, list_mail_recipients 
  to HockeyService in use_cases.py
- Add a Mailing tab to the Tkinter UI following the pattern in tk_app.py
- No authentication; mailing list is independent from players
```

---

## 8. Common Pitfalls

### Spec too vague → AI output too vague

If a spec says *"the system should display stats"*, neither a developer nor an AI agent knows what fields to show, in what format, split by what dimensions, read-only or editable, etc.

Good specs are specific enough that a developer could implement a requirement without asking follow-up questions. If you find yourself guessing during implementation, the spec needs more detail.

### Spec too rigid → no room for learning

A spec is not a contract carved in stone. If a client sees the PoC and realizes they actually want something different, the right response is to update the spec, not to defend the old one.

Open questions exist precisely because some decisions cannot be made without seeing working software. The spec should be honest about what is known versus what is deferred.

### Implementing beyond the spec

AI agents (and eager developers) may add features that seem useful but were not specified. This is called **gold-plating**, and it creates problems:
- It has not been validated with the client — it may not be what they want.
- It adds code that has no acceptance criteria — it will not be tested.
- It increases the surface area for bugs and maintenance burden.

The Non-Goals section of the spec is your most powerful tool against gold-plating.

### Confusing PoC quality with production quality

A PoC is allowed to have shortcuts: no error handling, no tests, hardcoded values, no migrations. But those shortcuts must be tracked and deliberately removed in the MVP and subsequent iterations.

A common failure mode is shipping PoC-quality code as the MVP because "it works". Use the spec's Quality Attributes section (§6 in `specs.md`) to enforce production-quality standards for the MVP.

---

## 9. Summary

Spec-Driven Development is a discipline, not a tool. It requires that you:

1. **Write the spec before writing the code.** Requirements first, implementation second.
2. **Be explicit about scope.** Goals and Non-Goals are equally important.
3. **Iterate with the client.** The spec reflects the current state of a conversation, not the final truth.
4. **Track uncertainty.** Open questions are not failures — they are honest acknowledgment of what is not yet decided.
5. **Verify against the spec.** Acceptance criteria exist to be checked, not filed away.

When combined with AI coding agents, SDD provides the structured context that makes AI assistance reliable, traceable, and bounded. The developer owns the spec; the AI accelerates the implementation.

---

*This document is part of the [hockey-stats](../README.md) project, used as a teaching reference for Software Development courses.*
