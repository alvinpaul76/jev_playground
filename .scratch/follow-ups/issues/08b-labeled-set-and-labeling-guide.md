# 08b Labeled set and labeling guide

Status: needs-info
Type: research
Parent: 08

## What
At least 30 new labeled tickets in `evals/data/`, with a written labeling guide, split into a tuning set (about 12) and a held-out set (at least 18), kept separate from the smoke set. Needs a person to decide the labels (grilling Q3), so it is `ready-for-human` once the rules below are settled.

## Waiting on the maintainer (grilling round 1)
- Q2 where the tickets come from (recommended: real tickets anonymized plus hand-written ones for rare cases; a person always decides the expected label)
- Q3 who labels (recommended: the owner alone, tickets they cannot decide are marked `ambiguous`)
- Q4 which team owns a post-deploy outage (recommended: the team that can fix the cause, so JEV-001 would be `backend`)
- Q5 when `unknown` is right (recommended: severity when impact cannot be judged; category only when no other fits; no unknown team)
- Q7 coverage (recommended: at least 2 per team, 1 per category, 2 per severity, about 5 hard cases)

Q1, Q6, Q8 and Q9 were taken as agreed when 08a was implemented.

## Done when
The labeling guide exists, 30+ tickets are labeled and split, the harness (08a) loads them, and the first held-out accuracy is reported.
