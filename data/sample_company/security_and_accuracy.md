# Security and Accuracy

## Accuracy evaluation
We measure ranking quality (NDCG@10) against recruiter shortlists on a held-out test set. The current model scores 0.81 NDCG@10. We re-run the evaluation before every model release.

## Security controls
Data is encrypted in transit and at rest. Access is role-based with single sign-on. An external penetration test is performed once a year. A SOC 2 Type II report is available to customers under NDA.

## Monitoring
We track the recruiter override rate and score distribution monthly to detect performance drift, and the ML lead reviews the dashboard.
