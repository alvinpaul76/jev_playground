# Ticket analysis

Labels support tickets (severity, category, assigned team) with a language model, and measures how often those labels match what a person decided.

## Language

**Ticket**:
A support report with an id, a title and a description, and optionally an environment, a business impact and evidence.
_Avoid_: Issue, case

**Label**:
One of the three answers given for a ticket: its severity, its category, or its assigned team.
_Avoid_: Tag, class

**Assigned team**:
The team that can fix the cause of a ticket.
_Avoid_: Owner, department

**Expected label**:
The label a person decided is right for a ticket.
_Avoid_: Ground truth, gold label, correct answer

**Predicted label**:
The label the model gave for a ticket.
_Avoid_: Output, guess

**Labeled set**:
Tickets that have expected labels, used to measure accuracy.
_Avoid_: Dataset, test data

**Smoke set**:
The first 8 labeled tickets. Their descriptions were adjusted after seeing the results, so they only catch breakage and do not measure accuracy.

**Tuning set**:
Labeled tickets you may look at while editing label descriptions.
_Avoid_: Training set, dev set

**Held-out set**:
Labeled tickets never used while editing label descriptions, so their accuracy is a fair report.
_Avoid_: Test set, validation set

**Labeling guide**:
The written rules a person follows to decide expected labels, kept separate from the label descriptions the model sees.
_Avoid_: Rubric, annotation spec
