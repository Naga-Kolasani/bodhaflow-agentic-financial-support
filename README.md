# BodhaFlow: Agentic Financial Support

I am building BodhaFlow to explore a practical question: how can an AI support system handle common financial-support questions while staying within clear safety and authorization boundaries?

BodhaFlow is a fictional financial-support platform. It is designed to route a small set of customer requests, find relevant guidance from project-authored policy documents, use limited mock tools when allowed, and escalate cases that should not be handled automatically.

Everything in this project is fictional. The policies, customers, merchants, transactions, transfers, and support cases are created only for BodhaFlow.

## Why I am building this

Financial-support requests can look simple on the surface, but they often depend on the right policy, the right transaction information, and careful handling of sensitive situations.

I want this project to demonstrate more than a chatbot response. The goal is to build a system that can follow a defined workflow, check whether a fictional customer is allowed to view a fictional record, use only approved mock tools, cite the guidance it used, and stop when a case needs escalation.

## Current status

BodhaFlow is in the foundation stage. I have defined the initial scope, safety boundaries, and the workflow that will guide the implementation.

The repository currently contains project documentation. I will add the application in small, tested stages, beginning with the Python project structure and core data models.

## V1 support scope

The first version of BodhaFlow will handle only these fictional support scenarios:

1. A card payment is pending
2. A card payment is declined
3. A customer sees a duplicate charge
4. A customer does not recognize a transaction
5. A transfer is pending or has not been received

A request about an unrecognized transaction always goes to escalation. The system will also escalate when the request is sensitive, unsafe, unsupported, unclear, missing needed information, inconsistent with available evidence, or not covered by policy.

## How BodhaFlow should work

For a supported request, BodhaFlow is designed to follow this path:

1. Validate the request and create a traceable request context.
2. Check for unsupported requests, unsafe content, and prompt-injection attempts.
3. Identify the support scenario or ask for clarification when the request is unclear.
4. Apply mandatory escalation rules before trying to provide an answer.
5. Confirm that the fictional customer is authorized to access the requested fictional record.
6. Retrieve the relevant BodhaFlow policy guidance.
7. Use an approved mock tool only when the policy and authorization checks allow it.
8. Validate the mock-tool result.
9. Respond with cited guidance, a clarification question, a safe refusal, or an escalation outcome.

The system should not guess transaction details, invent policy, or take an action that has not been explicitly allowed.

## Safety boundaries

BodhaFlow uses only fictional, synthetic data and mock tools. It does not connect to or represent a real bank, payment processor, card network, financial account, customer system, or employer system.

It does not move money, issue refunds, submit disputes, freeze cards, change accounts, or take other real financial actions.

The AI component will operate within a defined workflow. It will not be able to choose arbitrary tools, run arbitrary code, bypass authorization checks, or override required escalation rules.

## What I plan to build

The implementation will be developed in small stages:

1. A Python application structure with typed data models and configuration.
2. Synthetic customer, transaction, transfer, and support-case data with restricted mock tools.
3. Local policy retrieval with citations.
4. An explicit agent workflow with controlled routing and escalation.
5. A FastAPI interface with authorization and guardrails.
6. Unit tests, integration tests, and an evaluation set for safe behavior.
7. Docker, GitHub Actions, project documentation, and a short demo.

## Project documentation

- [V1 scope and safety decision](docs/decisions/0001-v1-scope-and-safety.md)
- [Architecture overview](docs/architecture/overview.md)
- [Fictional policy authoring guide](docs/policies/README.md)
- [Evaluation plan](docs/evaluation/README.md)
