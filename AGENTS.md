# AGENTS.md

You are working in a school workflow repository used to build teacher-facing tools and educational content pipelines.

## Core operating rules

1. Never invent source content that is not present in provided files.
2. When file quality is poor, explicitly flag uncertainty instead of guessing.
3. Prefer auditability over fluency.
4. Every workflow must produce both a human-readable output and a machine-readable audit artifact.
5. Keep generation separate from checking whenever practical.
6. Do not silently cross lesson boundaries, slide boundaries, or curriculum boundaries.
7. For student-related scans, do not silently normalize uncertain names or dates. Mark low-confidence fields.
8. Preserve teacher trust: surface ambiguity, unreadable pages, missing files, and unsupported claims.
9. Keep outputs practical for real classrooms: realistic timing, realistic setup burden, realistic marking burden.
10. Do not over-engineer. Build the smallest reliable version first.

## Output expectations

For each workflow, produce:
- output file or draft content
- audit log
- unresolved issues list
- suggested next action

## Coding expectations

- Write clear, boring, maintainable code.
- Use small functions.
- Add docstrings where useful.
- Add tests for parsing and transformation logic.
- Avoid hidden behavior.
- Prefer explicit config and templates.

## Educational expectations

- Align tightly to the provided source material.
- Do not drift into generic filler.
- Keep assignments concrete and copy-pastable.
- Keep teacher keys concise and supportable.

## Workflow patterns

Supported workflow patterns in this repository include:
- lesson homework generation
- scan collation and review
- science lab design
- CTS module build
- teacher keying and solution support

For teacher keying workflows:
- Treat teacher-provided material as authoritative.
- External knowledge may be used only to resolve ambiguity and must be flagged when used.
- Final keyed answers must preserve appropriate significant figures for calculated values.
- Provide both teacher-facing clarity and student-facing steps/explanations.

## Standard agent contract

All workflow prompts in this repository must include and enforce this communication contract.

Required end-of-run reporting sections:
1. In scope
2. Out of scope
3. Completed (what was done)
4. Not completed (what was not done)
5. Assumptions and decisions
6. Risks or uncertainty
7. Suggested next action

Contract rules:
- Do not claim work as completed if it was only proposed.
- Distinguish clearly between generated outputs and verified outputs.
- If scope changed during execution, explicitly record the change and reason.
- If blocked, list the exact blocker and the minimum teacher input needed to proceed.
