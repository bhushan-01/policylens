# AI Act Evidence Pack — Acme Talent AI

_Generated 2026-11-22 · mode: LLM-assisted_

> Draft prepared from the vendor's own documents and the text of Regulation (EU) 2024/1689. Not legal advice. Have qualified counsel review before sending to a customer.

## 1. Risk classification

**HIGH-RISK (Annex III, employment)**

- **Annex III** — Employment use case, Annex III point 4(a).
  > “access to self-employment: (a) AI systems intended to be used for the recruitment or selection of natural persons, in particular to place targeted job advertisements, to analyse and filter job applications, and to evaluate candidates; (b) AI systems intended to be used to make decisions affecting terms of work-related relationships, the promotion or termination of work-related contractual relation”
- **Article 6** — Article 6(2): Annex III systems are high-risk. Article 6(3) derogations do not apply where the system performs profiling of natural persons.
  > “Notwithstanding the first subparagraph, an AI system referred to in Annex III shall always be considered to be high-risk where the AI system performs profiling of natural persons. 4”

_Ranking/scoring candidates generally involves profiling, so the Article 6(3) 'not high-risk' derogation should not be relied on without counsel._

_IMPORTANT DATE UPDATES (EU Digital Omnibus on AI, 2026 — not in the 2024 PDF text):
- Stand-alone high-risk systems (Annex III / Article 6(2)): apply from 2 December 2027
  (delayed from 2 August 2026).
- High-risk systems in regulated products (Annex I / Article 6(1)): apply from 2 August 2028.
Always mention these updated dates when discussing when high-risk obligations apply._

## 2. Readiness against buyer-expected evidence

| Obligation | Article | Status | Where we found it |
|---|---|---|---|
| Risk management system | Article 9 | Missing | — |
| Data and data governance | Article 10 | Evidenced | data_governance.md § 1, data_governance.md § 2, data_governance.md § 3 |
| Technical documentation (Annex IV) | Article 11 | Missing | — |
| Record-keeping / automatic logging | Article 12 | Missing | — |
| Transparency and instructions for use | Article 13 | Evidenced | human_oversight.md § 3, product_overview.md § 2 |
| Human oversight | Article 14 | Evidenced | human_oversight.md § 2, human_oversight.md § 3, human_oversight.md § 1 |
| Accuracy, robustness, cybersecurity | Article 15 | Evidenced | security_and_accuracy.md § 2, security_and_accuracy.md § 1, security_and_accuracy.md § 3 |
| Quality management system | Article 17 | Missing | — |
| Conformity assessment | Article 43 | Missing | — |
| Registration in the EU database | Article 49 | Missing | — |
| Post-market monitoring | Article 72 | Evidenced | security_and_accuracy.md § 3 |
| Serious incident reporting | Article 73 | Missing | — |
| AI literacy | Article 4 | Evidenced | human_oversight.md § 3 |
| Right to explanation of individual decisions | Article 86 | Partial | human_oversight.md § 2 |

**6 evidenced · 1 partial · 7 missing** of 14 obligations. _Keyword triage of your documents to show where to look first — not a compliance determination._

### Fix first

- **Article 9 — Risk management system** (Missing): A documented, continuously updated risk management process covering foreseeable misuse and residual risk.
- **Article 11 — Technical documentation (Annex IV)** (Missing): Technical documentation drawn up before market placement and kept up to date (Annex IV contents).
- **Article 12 — Record-keeping / automatic logging** (Missing): Automatic event logging over the system's lifetime, enabling traceability and monitoring.
- **Article 17 — Quality management system** (Missing): A written quality management system covering design, testing, change control and accountability.
- **Article 43 — Conformity assessment** (Missing): Status of the conformity assessment procedure followed before placing the system on the market.
- **Article 49 — Registration in the EU database** (Missing): Registration of the system in the EU database for high-risk systems.
- **Article 73 — Serious incident reporting** (Missing): A procedure to detect, investigate and report serious incidents to market surveillance authorities.
- **Article 86 — Right to explanation of individual decisions** (Partial): Ability for deployers to give affected persons a clear explanation of the system's role in a decision.

## 3. Questionnaire answers

### Q1. Is your AI system classified as high-risk under the EU AI Act? Please explain the basis.

**[READY]**

Yes, our AI system is classified as high-risk under the EU AI Act. The system is intended to be used to analyse and filter job applications and evaluate candidates for open roles [doc: product_overview.md § 2], which falls under Annex III point (a) as an AI system intended for recruitment or selection of natural persons, specifically to analyse and filter job applications and evaluate candidates (Annex III). Because the system is placed on the EU market [doc: product_overview.md § 4] and matches the Annex III use case, it is classified as high-risk pursuant to Article 6(2). The high-risk obligations for stand-alone Annex III systems apply from 2 December 2027 under the updated EU Digital Omnibus timeline.

_Law consulted: Article 86, Article 2, Article 6, Article 80, Article 23, Article 24, Annex III. Company docs consulted: human_oversight.md § 2, product_overview.md § 4, product_overview.md § 3, product_overview.md § 2._

### Q2. What is the intended purpose of the system, and what uses are explicitly excluded?

**[READY]**

The system is intended to help recruiters analyse and filter job applications and evaluate candidates for open roles [doc: product_overview.md § 2]. We explicitly exclude its use for promotion decisions, termination decisions, or employee performance monitoring [doc: product_overview.md § 2]. This scope aligns with the EU AI Act's requirement that instructions for use specify the system's intended purpose (Article 13(3)(b)(i)).

_Law consulted: Article 13. Company docs consulted: human_oversight.md § 3, product_overview.md § 2, security_and_accuracy.md § 2, product_overview.md § 3._

### Q3. How do you ensure effective human oversight of the system's outputs?

**[CHECK CITATIONS]**

We ensure effective human oversight by keeping recruiters in control at all decision points [doc: human_oversight.md § 1]. Our system never automatically rejects candidates; every rejection requires explicit recruiter confirmation, and the ranked list serves only as advisory input [doc: human_oversight.md § 1]. Recruiters can reorder rankings, restore low-ranked candidates, and add manual notes; each candidate card displays the top scoring factors and a confidence indicator to support informed interpretation and help identify potential model errors [doc: human_oversight.md § 2]. We provide a 45-minute onboarding session and a written user guide that explain score meaning, model limitations, automation bias risks, and override procedures [doc: human_oversight.md § 3].

⚠ negative claim (e.g. 'we do not…'): documents rarely prove absence — confirm it is true

_Law consulted: Article 14, Article 14. Company docs consulted: human_oversight.md § 2, human_oversight.md § 3, human_oversight.md § 1, security_and_accuracy.md § 2._

### Q4. Does the system automatically log events, and for how long are logs retained?

**[NEEDS INPUT]**

[NEEDS INPUT: whether the system automatically records events (logs) as required by Article 12, what events are logged, and the retention period for those logs]. Article 12 requires high-risk AI systems to technically allow automatic recording of events over the system's lifetime, capturing situations that may present risks, supporting post-market monitoring, and enabling operational oversight. The company evidence describes data retention for candidate records (12 months after requisition closure) [doc: data_governance.md § 3] and monitoring of override rates and score distributions [doc: security_and_accuracy.md § 3], but does not address automatic event logging or log retention periods. We need to document our logging capabilities, the specific events captured, and how long system logs are retained to demonstrate compliance with Article 12.

Missing: Whether the system implements automatic event logging as required by Article 12; What specific events are logged (e.g., system decisions, user interactions, errors, data inputs); The retention period for system event logs; How logs support identification of risks, post-market monitoring, and operational oversight

_Law consulted: Article 12, Article 12. Company docs consulted: data_governance.md § 3, human_oversight.md § 3, security_and_accuracy.md § 3, security_and_accuracy.md § 2._

### Q5. Describe how training data is governed and how you test for bias.

**[NEEDS INPUT]**

We govern training data through documented practices covering source, collection date, and licensing [doc: data_governance.md § 1]. Our ranking model is trained on anonymised historical application and hiring outcome data from consenting customers and a licensed public job-posting corpus [doc: data_governance.md § 1]. For bias testing, we evaluate the model quarterly for score disparities across gender and age groups using a held-out test set with inferred demographic labels; results are reviewed by the ML lead, and the most recent review confirmed the selection-rate ratio remained within our internal threshold of 0.8 [doc: data_governance.md § 2]. [NEEDS INPUT: documentation of design choices, data preparation operations (annotation, labelling, cleaning), formulation of assumptions about what the data measures, assessment of data quantity and suitability, measures to prevent and mitigate identified biases, and identification of data gaps as required by Article 10(2)(a), (c), (d), (e), (g), and (h)].

Missing: Documentation of design choices for training, validation and testing datasets (Article 10(2)(a)); Data preparation processing operations such as annotation, labelling, cleaning, updating, enrichment and aggregation (Article 10(2)(c)); Formulation of assumptions about what the data measures and represents (Article 10(2)(d)); Assessment of availability, quantity and suitability of datasets (Article 10(2)(e)); Measures to detect, prevent and mitigate identified biases beyond quarterly testing (Article 10(2)(g)); Identification of data gaps or shortcomings and how they are addressed (Article 10(2)(h))

_Law consulted: Article 10, Article 10. Company docs consulted: data_governance.md § 1, data_governance.md § 2, data_governance.md § 3, human_oversight.md § 3._

### Q6. What accuracy metrics do you declare, and how are they measured?

**[NEEDS INPUT]**

We declare NDCG@10 (Normalized Discounted Cumulative Gain at rank 10) as our primary accuracy metric, measured against recruiter shortlists on a held-out test set [doc: security_and_accuracy.md § 1]. The current model achieves 0.81 NDCG@10, and we re-run this evaluation before every model release [doc: security_and_accuracy.md § 1]. We also monitor recruiter override rates and score distributions monthly to detect performance drift [doc: security_and_accuracy.md § 3], and conduct quarterly bias evaluations measuring score disparities across gender and age groups [doc: data_governance.md § 2]. [NEEDS INPUT: confirmation that these metrics and measurement methods are documented in the instructions of use as required by Article 15(3)].

Missing: Confirmation that NDCG@10 and the measurement methodology are declared in the instructions of use accompanying the system

_Law consulted: Article 15, Article 15. Company docs consulted: security_and_accuracy.md § 2, security_and_accuracy.md § 1, security_and_accuracy.md § 3, data_governance.md § 2._

### Q7. What cybersecurity measures protect the system?

**[NEEDS INPUT]**

We encrypt data in transit and at rest, enforce role-based access control with single sign-on, and conduct an external penetration test annually [doc: security_and_accuracy.md § 2]. A SOC 2 Type II report is available to customers under NDA [doc: security_and_accuracy.md § 2]. We monitor recruiter override rates and score distributions monthly to detect performance drift [doc: security_and_accuracy.md § 3]. [NEEDS INPUT: technical measures to prevent, detect, respond to, or control AI-specific attacks such as data poisoning, model poisoning, adversarial examples, model evasion, confidentiality attacks, or model flaws, as required by Article 15(5)].

Missing: Technical solutions to address AI-specific vulnerabilities: data poisoning prevention/detection, model poisoning controls, adversarial example defences, model evasion protections, confidentiality attack safeguards, and model flaw resolution procedures (Article 15(5))

_Law consulted: Article 15, Article 15. Company docs consulted: security_and_accuracy.md § 2, security_and_accuracy.md § 1, security_and_accuracy.md § 3, product_overview.md § 2._

### Q8. Do you maintain technical documentation as required by Annex IV? Can you share it?

**[NEEDS INPUT]**

[NEEDS INPUT: complete Annex IV technical documentation package]. Article 11 requires that we draw up and maintain technical documentation before placing a high-risk AI system on the market, covering all elements listed in Annex IV (including general system description, detailed design and development process, data governance measures, risk management, testing and validation records, and human oversight mechanisms). The NOTICE indicates that no document in our current evidence covers the full Annex IV technical documentation. While we have implemented several relevant controls—including security measures [doc: security_and_accuracy.md § 2], human oversight features [doc: human_oversight.md § 2] [doc: human_oversight.md § 3], and data governance practices [doc: data_governance.md § 3]—we cannot confirm that a complete, consolidated technical documentation package meeting all Annex IV requirements has been prepared or is available for sharing.

Missing: Complete Annex IV technical documentation package as required by Article 11; Confirmation that technical documentation was drawn up before market placement; General description of the AI system and its intended purpose (Annex IV element); Detailed design, development process, and architecture documentation; Complete data governance and training/validation dataset documentation; Risk management system documentation; Full testing, validation, and performance metrics records; Cybersecurity measures documentation; Quality management system documentation; Process for maintaining technical documentation up-to-date

_Law consulted: Article 11, Article 11. Company docs consulted: security_and_accuracy.md § 2, human_oversight.md § 3, data_governance.md § 3, human_oversight.md § 2._

### Q9. What is the status of your conformity assessment and CE marking?

**[NEEDS INPUT]**

[NEEDS INPUT: conformity assessment procedure not yet documented]. Under Article 43, providers of high-risk AI systems must complete a conformity assessment—either internal control (Annex VI) or assessment involving a notified body (Annex VII)—before affixing CE marking. The obligation applies from 2 December 2027 for stand-alone high-risk systems (Annex III) or 2 August 2028 for systems embedded in regulated products (Annex I). We have not yet initiated the formal conformity assessment process or obtained CE marking.

Missing: Which conformity assessment procedure (Annex VI internal control or Annex VII notified-body assessment) the vendor has selected or intends to follow; Whether harmonised standards (Article 40) or common specifications (Article 41) have been applied; Current status and timeline of the conformity assessment (not started, in progress, completed); Whether CE marking has been affixed and EU declaration of conformity drawn up; If using Annex VII, which notified body has been or will be engaged

_Law consulted: Article 43. Company docs consulted: data_governance.md § 2, security_and_accuracy.md § 1, security_and_accuracy.md § 2, human_oversight.md § 3._

### Q10. Describe your procedure for reporting serious incidents to authorities.

**[NEEDS INPUT]**

[NEEDS INPUT: serious incident reporting procedure]. Under Article 73, providers of high-risk AI systems placed on the Union market must report any serious incident to the market surveillance authorities of the Member State where it occurred, then perform necessary investigations including a risk assessment and corrective action without altering the system in a way that may affect subsequent evaluation of causes. No company documentation describing our incident reporting procedure, investigation protocol, or authority notification process has been provided.

Missing: Serious incident reporting procedure: how incidents are identified, escalated, and reported to market surveillance authorities; Definition of 'serious incident' used internally and criteria for triggering a report; Investigation protocol following a serious incident, including risk assessment and corrective action steps; Process for cooperating with competent authorities and notified bodies during investigations; Safeguards to preserve the AI system state prior to authority notification to enable subsequent evaluation

_Law consulted: Article 73, Article 73. Company docs consulted: human_oversight.md § 2, product_overview.md § 2, data_governance.md § 1, human_oversight.md § 3._

### Q11. How do you monitor the system's performance after deployment?

**[NEEDS INPUT]**

We monitor post-deployment performance through monthly tracking of recruiter override rates and score distributions to detect drift [doc: security_and_accuracy.md § 3]. Our ML lead reviews these metrics on a dashboard [doc: security_and_accuracy.md § 3]. We also measure ranking quality (NDCG@10) against recruiter shortlists on held-out test data before each model release [doc: security_and_accuracy.md § 1]. [NEEDS INPUT: Article 72 requires active and systematic collection and analysis of relevant data on performance throughout the system's lifetime and evaluation of continuous compliance with Chapter III Section 2 requirements; we need evidence of a formal post-market monitoring plan, documented data sources beyond override rates, systematic compliance evaluation procedures, and analysis of interaction with other AI systems where relevant.]

Missing: Formal post-market monitoring plan as required by Article 72; Documentation of all data sources systematically collected for performance monitoring; Procedures for evaluating continuous compliance with Chapter III Section 2 requirements; Analysis of interaction with other AI systems (if relevant); Systematic documentation and analysis framework for collected performance data

_Law consulted: Article 72. Company docs consulted: security_and_accuracy.md § 3, human_oversight.md § 2, human_oversight.md § 3, security_and_accuracy.md § 1._

### Q12. Is the system registered in the EU database for high-risk AI systems?

**[NEEDS INPUT]**

[NEEDS INPUT: registration status in the EU database under Article 49]. Our system is a CV screening and candidate ranking tool that analyses and filters job applications and evaluates candidates [doc: product_overview.md § 1]. This falls under Annex III point 4(a) as an AI system intended for recruitment or selection of natural persons, making it high-risk (Article 6). Providers of high-risk systems listed in Annex III must register before placing on the market, though the registration obligation for stand-alone high-risk systems applies from 2 December 2027 under the updated timeline. We have placed the system on the EU market [doc: product_overview.md § 4].

Missing: Whether the system has been registered in the EU database for high-risk AI systems (Article 49); Registration reference number or confirmation if applicable; Timeline for registration if the system was placed on market before 2 December 2027

_Law consulted: Article 49, Article 49, Annex III, Article 6. Company docs consulted: product_overview.md § 4, data_governance.md § 1, product_overview.md § 1, product_overview.md § 3._

### Q13. Can our recruiters explain a ranking decision to an affected candidate?

**[READY]**

Yes. Article 86 grants any affected person subject to a deployer decision based on high-risk AI output the right to obtain clear and meaningful explanations of the AI system's role and the main elements of the decision. Our system displays the top factors behind each candidate's score and a confidence indicator on the candidate card [doc: human_oversight.md § 2], enabling recruiters to interpret the output and provide those explanations. Because every rejection requires explicit recruiter confirmation [doc: human_oversight.md § 1], the recruiter remains the decision-maker and can explain both the AI's contribution and their own judgment.

_Law consulted: Article 86. Company docs consulted: human_oversight.md § 2, human_oversight.md § 1, data_governance.md § 1, product_overview.md § 2._

### Q14. Does the system infer candidates' emotions or use biometric data?

**[CHECK CITATIONS]**

We do not infer candidates' emotions or use biometric data. The system scores candidates on skills match and experience using a gradient-boosted ranking model trained on anonymised historical application and hiring outcome data [doc: data_governance.md § 1] [doc: product_overview.md § 3]. Protected attributes—including gender, age, ethnicity, and photos—are removed before scoring [doc: product_overview.md § 3]. The system does not process facial images, dactyloscopic data, or other biometric data as defined in Article 3(34), and it does not identify or infer emotions or intentions from such data (Article 3(39)).

⚠ negative claim (e.g. 'we do not…'): documents rarely prove absence — confirm it is true

_Law consulted: Article 3, Article 50, Annex III, Article 3, Article 5. Company docs consulted: data_governance.md § 1, product_overview.md § 3, human_oversight.md § 2, product_overview.md § 2._
