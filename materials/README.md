# Materials Folder Guide

Use this folder as the single source location for course and lesson assets that agents should reference.

## Folder structure

- `slides/` - teacher slide decks (`.pptx`, `.pdf`)
- `lesson-docs/` - lesson notes, handouts, chapter docs
- `assessments/` - tests, quizzes, homework sets, worksheets
- `keys/` - existing answer keys from teacher or department
- `curriculum/` - curriculum outcomes and standards docs
- `external-sources/` - imported third-party content (web/docs)
- `rosters-and-meta/` - class lists, course metadata, schedule notes
- `archive/` - older versions kept for reference only

## Naming convention

Use predictable file names:

`<course>-<unit>-<lesson>-<topic>-v<version>.<ext>`

Example:

`bio20-unitC-lesson03-blood-vessels-v1.pptx`

## Workflow notes

- Prefer copying files into this repo rather than referencing files from Downloads/Desktop.
- Keep source files unchanged; store transformed files under `data/processed/` or `outputs/`.
- When a source is uncertain quality, keep it but note uncertainty in audits.
