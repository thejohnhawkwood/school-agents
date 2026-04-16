# PRD-001: Lesson Homework Engine

## 1. Purpose
Generate trustable homework from tightly bounded lesson materials.

## 2. User
A classroom teacher preparing daily or weekly homework from a slide deck, lesson PDF, or teacher notes.

## 3. Problem
General-purpose AI tends to drift beyond the actual lesson, generate vague questions, or invent details from nearby topics.

## 4. Inputs
- Slide deck or lesson PDF
- Explicit allowed range, such as slides 6-14
- Question format requirements
- Optional reading level or class notes

## 5. Outputs
- 5 short-answer questions
- 1 diagram question
- teacher key
- audit section
- uncertainty flags

## 6. Workflow
1. Read source files
2. Verify readable pages or slides
3. Restrict to allowed range
4. Extract relevant lesson content
5. Generate questions
6. Generate teacher key
7. Run QA audit

## 7. Constraints
- No use of unverified source content
- No use of nearby lesson content
- Must flag unreadable slides
- Questions must be specific and answerable

## 8. Acceptance criteria
- All questions map to source content
- Key is supported by source
- Audit identifies used source segments
- Unreadable content is not guessed

## 9. Failure modes
- Slide drift
- generic filler questions
- unsupported answer key claims
- unflagged unreadable source

## 10. Test cases
- clean PPTX with 10 slides
- mixed PDF with image-heavy diagrams
- one slide range containing unreadable text

## 11. Future improvements
- direct docx export
- diagram extraction support
- multiple question set variants
