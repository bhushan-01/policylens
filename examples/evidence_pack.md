# AI Act Evidence Pack — Acme Talent AI

_Generated 2026-11-23 · mode: LLM-assisted_

> Draft prepared from the vendor's own documents and the text of Regulation (EU) 2024/1689. Not legal advice. Have qualified counsel review before sending to a customer.

## 1. Risk classification

**HIGH-RISK (Annex III point 4(a), 4(b))**

- **Annex III** — Annex III point 4(a): recruitment and selection.
  > “AI systems intended to be used for the recruitment or selection of natural persons, in particular to place targeted job advertisements, to analyse and filter job applications, and to evaluate candidates; (b) AI systems intended to be used to make decisions affecting terms of work-related relationships, the promotion or termination of work-related contractual relation”
- **Annex III** — Annex III point 4(b): decisions on work relationships, promotion, termination, monitoring.
  > “AI systems intended to be used to make decisions affecting terms of work-related relationships, the promotion or termination of work-related contractual relationships, to allocate tasks based on individual behaviour or personal traits or characteristics or to monitor and evaluate the performance and behaviour of persons in such relationships. 5. Access to and enjoyme”
- **Article 6** — Article 6(2): Annex III systems are high-risk. The Article 6(3) 'not high-risk' derogation does not apply where the system performs profiling of natural persons.
  > “Notwithstanding the first subparagraph, an AI system referred to in Annex III shall always be considered to be high-risk where the AI system performs profiling of natural persons. 4”

_Ranking, scoring or predicting things about people generally counts as profiling, so do not rely on the Article 6(3) derogation without counsel._

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

Yes, our AI system is classified as high-risk under the EU AI Act. The system is intended to analyse and filter job applications and evaluate candidates for open roles [doc: product_overview.md § 2], which falls directly under Annex III as an AI system intended "to analyse and filter job applications, and to evaluate candidates" (Annex III). Because it meets the conditions in Article 6(2) for stand-alone high-risk systems listed in Annex III, the full requirements of the Act apply to us. Under the EU Digital Omnibus amendments, these obligations take effect from 2 December 2027.

_Law consulted: Article 86, Article 2, Article 6, Article 80, Article 23, Article 24, Annex III. Company docs consulted: human_oversight.md § 2, product_overview.md § 4, product_overview.md § 3, product_overview.md § 2._

### Q2. What is the intended purpose of the system, and what uses are explicitly excluded?

**[READY]**

The system is intended to help recruiters analyse and filter job applications and evaluate candidates for open roles [doc: product_overview.md § 2]. We explicitly exclude use of the system for promotion decisions, termination decisions, or employee performance monitoring [doc: product_overview.md § 2]. This intended purpose and these exclusions are communicated to deployers during onboarding and in written user guides, in line with the transparency obligations under Article 13(3)(b)(i).

_Law consulted: Article 13. Company docs consulted: human_oversight.md § 3, product_overview.md § 2, security_and_accuracy.md § 2, product_overview.md § 3._

### Q3. How do you ensure effective human oversight of the system's outputs?

**[CHECK CITATIONS]**

We ensure effective human oversight by keeping recruiters in control at all decision points [doc: human_oversight.md § 1]. Our system never automatically rejects candidates; every rejection requires explicit recruiter confirmation, and the ranked list serves only as advisory input [doc: human_oversight.md § 1]. Recruiters can reorder rankings, restore low-ranked candidates, and add manual notes; each candidate card displays the top scoring factors and a confidence indicator to support informed interpretation and help identify potential model errors [doc: human_oversight.md § 2]. We provide a 45-minute onboarding session and a written user guide that explain score meaning, model limitations, automation bias risks, and override procedures [doc: human_oversight.md § 3].

⚠ negative claim (e.g. 'we do not…'): documents rarely prove absence — confirm it is true

_Law consulted: Article 14, Article 14. Company docs consulted: human_oversight.md § 2, human_oversight.md § 3, human_oversight.md § 1, security_and_accuracy.md § 2._

### Q4. Does the system automatically log events, and for how long are logs retained?

**[NEEDS INPUT]**

[NEEDS INPUT: whether the system automatically records events (logs) as required by Article 12, what events are logged, and the retention period for those logs]. Article 12 requires high-risk AI systems to technically allow automatic recording of events over the system's lifetime, capturing situations that may present risks, supporting post-market monitoring, and enabling operational oversight. The company evidence describes data retention for candidate records (12 months after requisition closure) [doc: data_governance.md § 3] and monitoring of override rates and score distributions [doc: security_and_accuracy.md § 3], but does not address system event logging or log retention periods. We need to document our logging capabilities, the specific events captured, and how long those logs are retained to demonstrate compliance with Article 12.

Missing: Whether the system automatically records events (logs) as required by Article 12; What specific events are logged (e.g., inputs, outputs, decisions, overrides, errors); Log retention period and policy; Technical logging capabilities and infrastructure

_Law consulted: Article 12, Article 12. Company docs consulted: data_governance.md § 3, human_oversight.md § 3, security_and_accuracy.md § 3, security_and_accuracy.md § 2._

### Q5. Describe how training data is governed and how you test for bias.

**[NEEDS INPUT]**

We govern training data through documented practices covering source, collection date, and licensing for all datasets—anonymised customer hiring records and a public job-posting corpus [doc: data_governance.md § 1]. Data preparation, retention (12 months post-requisition), and field minimisation are controlled [doc: data_governance.md § 3]. For bias testing, we run quarterly evaluations measuring score disparities across gender and age groups on a held-out test set with inferred demographic labels; the ML lead reviews results against an internal 0.8 selection-rate-ratio threshold [doc: data_governance.md § 2]. These practices address the data governance (Article 10(2)(a)–(e)) and bias examination and mitigation requirements (Article 10(2)(f)–(g)) that apply to high-risk AI systems from 2 December 2027.

Missing: Documented design choices and assumptions about what the data measure and represent (Article 10(2)(a), (d)); Specific data-preparation operations: annotation, labelling, cleaning, updating, enrichment, aggregation processes (Article 10(2)(c)); Assessment of data quantity and suitability for compliance (Article 10(2)(e)); Identification of data gaps or shortcomings and remediation plan (Article 10(2)(h)); Measures to detect and prevent (not only test for) biases, and mitigation actions taken when disparities are found (Article 10(2)(g))

_Law consulted: Article 10, Article 10. Company docs consulted: data_governance.md § 1, data_governance.md § 2, data_governance.md § 3, human_oversight.md § 3._

### Q6. What accuracy metrics do you declare, and how are they measured?

**[NEEDS INPUT]**

We declare NDCG@10 (Normalized Discounted Cumulative Gain at rank 10) as our primary accuracy metric, measured against recruiter shortlists on a held-out test set [doc: security_and_accuracy.md § 1]. The current model achieves 0.81 NDCG@10, and we re-run this evaluation before every model release [doc: security_and_accuracy.md § 1]. We also monitor recruiter override rates and score distributions monthly to detect performance drift [doc: security_and_accuracy.md § 3], and conduct quarterly bias evaluations measuring score disparities across gender and age groups [doc: data_governance.md § 2]. [NEEDS INPUT: confirmation that these metrics and measurement methods are formally declared in the instructions of use as required by Article 15(3)].

Missing: Confirmation that NDCG@10 and the measurement methodology are formally declared in the instructions of use accompanying the system, as required by Article 15(3)

_Law consulted: Article 15, Article 15. Company docs consulted: security_and_accuracy.md § 2, security_and_accuracy.md § 1, security_and_accuracy.md § 3, data_governance.md § 2._

### Q7. What cybersecurity measures protect the system?

**[NEEDS INPUT]**

We encrypt data in transit and at rest, enforce role-based access control with single sign-on, and conduct an external penetration test annually [doc: security_and_accuracy.md § 2]. A SOC 2 Type II report is available to customers under NDA [doc: security_and_accuracy.md § 2]. We monitor recruiter override rates and score distributions monthly to detect performance drift [doc: security_and_accuracy.md § 3]. [NEEDS INPUT: technical measures to prevent, detect, respond to, or control AI-specific attacks such as data poisoning, model poisoning, adversarial examples, model evasion, confidentiality attacks, or model flaws, as required by Article 15(5)].

Missing: Technical solutions to address AI-specific vulnerabilities: data poisoning prevention/detection, model poisoning controls, adversarial example defenses, model evasion protections, confidentiality attack safeguards, and model flaw resolution procedures (Article 15(5))

_Law consulted: Article 15, Article 15. Company docs consulted: security_and_accuracy.md § 2, security_and_accuracy.md § 1, security_and_accuracy.md § 3, product_overview.md § 2._

### Q8. Do you maintain technical documentation as required by Annex IV? Can you share it?

**[NEEDS INPUT]**

[NEEDS INPUT: technical documentation package as specified in Annex IV]. Under Article 11, providers of high-risk AI systems must draw up and maintain technical documentation before placing the system on the market, covering all elements listed in Annex IV to demonstrate compliance with the Act's requirements. The automated review indicates we do not currently have a consolidated technical documentation file meeting Annex IV's structure. We do maintain certain underlying records—security controls and SOC 2 reporting [doc: security_and_accuracy.md § 2], human oversight mechanisms and training materials [doc: human_oversight.md § 2] [doc: human_oversight.md § 3], and data governance policies [doc: data_governance.md § 3]—but these have not been assembled into the formal Annex IV package required by Article 11. If our system is classified as high-risk, we will need to complete and be able to share that documentation in accordance with the applicable timeline (2 December 2027 for stand-alone systems under Annex III, or 2 August 2028 for systems in regulated products under Annex I).

Missing: Complete technical documentation package structured according to Annex IV requirements; Confirmation of AI system's risk classification and applicable compliance timeline; Policy on sharing technical documentation with customers and authorities

⚠ negative claim (e.g. 'we do not…'): documents rarely prove absence — confirm it is true

⚠ forward commitment: confirm you actually intend to promise this

_Law consulted: Article 11, Article 11. Company docs consulted: security_and_accuracy.md § 2, human_oversight.md § 3, data_governance.md § 3, human_oversight.md § 2._

### Q9. What is the status of your conformity assessment and CE marking?

**[NEEDS INPUT]**

[NEEDS INPUT: conformity assessment procedure not yet documented]. Under Article 43, high-risk AI systems must complete a conformity assessment—either internal control (Annex VI) or third-party assessment with a notified body (Annex VII)—before affixing CE marking. The procedure depends on whether harmonised standards or common specifications have been applied. For stand-alone high-risk systems listed in Annex III, these obligations apply from 2 December 2027; for systems embedded in regulated products (Annex I), from 2 August 2028. We have not yet initiated the formal conformity assessment process or obtained CE marking.

Missing: Which conformity assessment procedure (Annex VI internal control or Annex VII notified-body assessment) has been selected or completed; Whether harmonised standards (Article 40) or common specifications (Article 41) have been applied; Current status of technical documentation compilation for conformity assessment; Whether a notified body has been engaged (if Annex VII route chosen); Timeline for completing conformity assessment and affixing CE marking; CE marking status and declaration of conformity

_Law consulted: Article 43. Company docs consulted: data_governance.md § 2, security_and_accuracy.md § 1, security_and_accuracy.md § 2, human_oversight.md § 3._

### Q10. Describe your procedure for reporting serious incidents to authorities.

**[NEEDS INPUT]**

[NEEDS INPUT: serious incident reporting procedure]. Under Article 73, providers of high-risk AI systems placed on the Union market must report any serious incident to the market surveillance authorities of the Member State where it occurred, then perform necessary investigations including a risk assessment and corrective action without altering the system in a way that may affect subsequent evaluation of causes. No company documentation describing our incident reporting procedure, investigation protocol, or authority notification process has been provided.

Missing: Serious incident reporting procedure: how incidents are identified, documented, and reported to market surveillance authorities; Definition of what constitutes a 'serious incident' in our context; Investigation protocol following a serious incident, including risk assessment and corrective action steps; Process for cooperating with competent authorities and notified bodies during investigations; Safeguards to preserve the AI system state for subsequent evaluation before any alterations

_Law consulted: Article 73, Article 73. Company docs consulted: human_oversight.md § 2, product_overview.md § 2, data_governance.md § 1, human_oversight.md § 3._

### Q11. How do you monitor the system's performance after deployment?

**[NEEDS INPUT]**

We monitor post-deployment performance through monthly tracking of recruiter override rates and score distributions to detect drift [doc: security_and_accuracy.md § 3]. Our ML lead reviews these metrics on a dashboard [doc: security_and_accuracy.md § 3]. We also measure ranking quality (NDCG@10) against recruiter shortlists on held-out test data before each model release [doc: security_and_accuracy.md § 1]. [NEEDS INPUT: Article 72(2) requires active and systematic collection and analysis of relevant data on performance throughout the system's lifetime and evaluation of continuous compliance with Chapter III Section 2 requirements; we need evidence of a formal post-market monitoring plan, documented data sources beyond override rates, systematic compliance evaluation procedures, and any analysis of interaction with other AI systems.]

Missing: Formal post-market monitoring plan as required by Article 72; Documentation of all data sources systematically collected for performance monitoring; Procedures for evaluating continuous compliance with Chapter III Section 2 requirements; Analysis of interaction with other AI systems (if relevant); Frequency and scope of systematic performance data analysis beyond monthly override tracking

_Law consulted: Article 72. Company docs consulted: security_and_accuracy.md § 3, human_oversight.md § 2, human_oversight.md § 3, security_and_accuracy.md § 1._

### Q12. Is the system registered in the EU database for high-risk AI systems?

**[NEEDS INPUT]**

[NEEDS INPUT: registration status in the EU database for high-risk AI systems]. Under Article 49, providers of high-risk AI systems listed in Annex III must register before placing the system on the market. Our system is a CV screening and candidate ranking tool used for recruitment and selection of natural persons [doc: product_overview.md § 1], which falls under Annex III as a high-risk use case. The registration obligation for stand-alone high-risk systems applies from 2 December 2027. We require confirmation of whether registration has been completed or is planned before that deadline.

Missing: Whether the system has been registered in the EU database for high-risk AI systems (Article 49); Registration timeline and planned compliance date relative to the 2 December 2027 deadline; Registration reference number or confirmation of submission, if already completed

_Law consulted: Article 49, Article 49, Annex III, Annex III, Article 6. Company docs consulted: product_overview.md § 4, data_governance.md § 1, product_overview.md § 1, product_overview.md § 3._

### Q13. Can our recruiters explain a ranking decision to an affected candidate?

**[READY]**

Yes. Article 86 grants any affected person subject to a deployer decision based on high-risk AI output the right to obtain clear and meaningful explanations of the AI system's role and the main elements of the decision. Our system displays the top factors behind each candidate's score and a confidence indicator on the candidate card [doc: human_oversight.md § 2], enabling recruiters to explain both the model's contribution and their own judgment. Because every rejection requires explicit recruiter confirmation [doc: human_oversight.md § 1], the recruiter remains the decision-maker and can provide the explanation Article 86 requires.

_Law consulted: Article 86. Company docs consulted: human_oversight.md § 2, human_oversight.md § 1, data_governance.md § 1, product_overview.md § 2._

### Q14. Does the system infer candidates' emotions or use biometric data?

**[CHECK CITATIONS]**

We do not infer candidates' emotions or use biometric data. The system scores candidates on skills match and experience using a gradient-boosted ranking model trained on anonymised historical application and hiring outcome data [doc: data_governance.md § 1] [doc: product_overview.md § 3]. Protected attributes—including gender, age, ethnicity, and photos—are removed before scoring [doc: product_overview.md § 3]. The system does not process facial images, dactyloscopic data, or other biometric data as defined in Article 3(34), and it does not identify or infer emotions or intentions from such data (Article 3(39)).

⚠ negative claim (e.g. 'we do not…'): documents rarely prove absence — confirm it is true

_Law consulted: Article 3, Article 50, Annex III, Article 3, Article 5. Company docs consulted: data_governance.md § 1, product_overview.md § 3, human_oversight.md § 2, product_overview.md § 2._
