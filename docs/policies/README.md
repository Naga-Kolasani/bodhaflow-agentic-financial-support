# BodhaFlow Policy Documents

This folder will hold the fictional support-policy documents that BodhaFlow uses for retrieval.

I will write these policies specifically for this project. They are not based on real bank, payment-processor, card-network, employer, or company policies. I will not copy, adapt, infer, or represent proprietary policy material in this project.

Later, when BodhaFlow responds to a supported request, it should retrieve the relevant policy before giving guidance. The response should cite the policy and section it used. If the system cannot find enough policy support, it should not guess. It should safely stop or escalate the request instead.

## What each policy should cover

Each policy document should focus on one BodhaFlow V1 support scenario:

1. Pending card payment
2. Declined card payment
3. Duplicate charge
4. Unrecognized transaction
5. Transfer pending or not received

I will use fictional customers, merchants, transactions, dates, amounts, timelines, and examples throughout these documents.

Each policy should explain:

- When BodhaFlow can provide guidance
- What information the system needs before continuing
- When it should ask the customer for clarification
- When a mock-tool lookup is allowed
- What authorization check must happen before showing a fictional transaction or transfer record
- When the system should give a safe refusal
- When the system must escalate

## Escalation rule for unrecognized transactions

An unrecognized transaction always requires escalation.

BodhaFlow must not decide that a transaction is valid, dismiss the concern, investigate it, reverse it, submit a dispute, freeze a card, or take any other action. The role of the system is to recognize that the request is sensitive and route it to escalation.

## Writing policies for retrieval

The policy files need to be easy for both people and the retrieval system to use. When I add them, I will:

- Give every policy a clear title and policy ID
- Use clear headings for the situation, required information, allowed steps, escalation rules, and customer response guidance
- Keep each rule specific enough to support a grounded response
- Avoid vague language that could lead to more than one interpretation
- Keep fictional examples clearly labeled as fictional
- Avoid real legal, regulatory, payment-network, or company-policy claims
- Include only rules that BodhaFlow can actually enforce in its workflow

## Citation rule

A response that uses policy guidance should identify the BodhaFlow policy and the relevant section.

If retrieval returns no relevant policy, weak evidence, or conflicting guidance, BodhaFlow should not invent a rule or citation. It should ask for clarification when appropriate or escalate the request.
