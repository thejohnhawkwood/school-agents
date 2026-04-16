# PRD-003: Science Lab Designer

## 1. Purpose
Generate realistic, curriculum-aligned lab options and expand chosen options into classroom-ready materials.

## 2. User
A high school science teacher planning labs for Science 30 or Bio 20.

## 3. Problem
AI often proposes labs that are flashy but unrealistic, overly expensive, or poorly aligned to the unit.

## 4. Inputs
- curriculum documents
- unit notes or slide decks
- class period length
- available equipment constraints
- desired level of complexity

## 5. Outputs
- candidate lab list
- feasibility matrix
- recommended options
- expanded lab package when chosen

## 6. Workflow
1. parse outcomes and constraints
2. generate lab candidates
3. score feasibility
4. present options
5. expand selected lab

## 7. Constraints
- realistic for ordinary school conditions
- explicit about safety and setup burden
- time-aware
- aligned to outcomes

## 8. Acceptance criteria
- labs are plausible and useful
- setup burden is honestly represented
- teacher can choose between options quickly

## 9. Failure modes
- fantasy equipment
- weak curricular linkage
- hidden setup burden
- unsafe simplifications

## 10. Test cases
- one-period Bio 20 lab
- two-period Science 30 lab
- limited-equipment scenario

## 11. Future improvements
- material cost estimator
- teacher vs student export modes
- substitute-teacher simplified version
