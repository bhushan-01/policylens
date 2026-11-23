# Data Governance and Fairness

## Training data
The ranking model is trained on anonymised historical application and hiring outcome data contributed by consenting customers, plus a licensed public job-posting corpus. Each dataset has a recorded source, collection date, and licence.

## Bias testing
We evaluate the model each quarter for score disparities across gender and age groups using a held-out test set with inferred demographic labels. Results are reviewed by the ML lead; the last review found the selection-rate ratio within our internal threshold of 0.8.

## Data minimisation and retention
Candidate data is kept for 12 months after a requisition closes, then deleted. Only the fields needed for ranking are processed.
