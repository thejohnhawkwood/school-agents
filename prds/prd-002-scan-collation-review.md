# PRD-002: Scan Collation and Review

## 1. Purpose
Collate low-quality student worksheet scans by student and date for faster completion checking and light assessment.

## 2. User
A teacher with a large batch of scanned daily check-in sheets.

## 3. Problem
Manual sorting wastes time, and low-quality scans create ambiguity around names, dates, and completeness.

## 4. Inputs
- batch PDF scans or image folders
- class roster if available
- expected date range
- optional form template

## 5. Outputs
- grouped pages by probable student and date
- confidence scores
- ambiguous pages queue
- completion-check summary
- optional quality-pass notes

## 6. Workflow
1. split and preprocess pages
2. OCR text fields
3. extract likely name and date
4. compare against roster if available
5. group by student and date
6. generate manual review queue
7. export summary table

## 7. Constraints
- low confidence must be surfaced
- uncertain pages must not be silently merged
- output should support fast teacher review

## 8. Acceptance criteria
- most pages grouped correctly
- ambiguous pages isolated clearly
- teacher can review unresolved pages quickly

## 9. Failure modes
- name confusion
- date confusion
- duplicate grouping
- false certainty

## 10. Test cases
- clean scans
- skewed scans
- hole-punched scans
- faint handwriting

## 11. Future improvements
- roster-assisted name correction
- dashboard review UI
- checkbox detection
