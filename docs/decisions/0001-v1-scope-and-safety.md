# V1 Scope and Safety Decisions

This document explains the choices that set the boundaries for BodhaFlow V1. I want to build a realistic engineering project, but every customer, policy, merchant, transaction, transfer, and support case in BodhaFlow will be fictional and created specifically for this project.

## Why I am keeping the first version narrow

Financial-support questions can involve sensitive information, unclear evidence, and requests that should not be handled automatically. A broad system would be harder to test, easier to overreach, and more likely to give unsupported guidance.

For the first version, I am focusing on a small set of scenarios where I can clearly define the policy, authorization checks, available mock tools, and escalation behavior.

## What BodhaFlow V1 will handle

BodhaFlow V1 will support only these fictional customer-support scenarios:

1. Pending card payment
2. Declined card payment
3. Duplicate charge
4. Unrecognized transaction
5. Transfer pending or not received

Any request outside these scenarios is out of scope for V1. The system should explain that it cannot handle the request or send it to escalation when appropriate. It should not attempt to guess a new workflow or invent guidance.

## Escalation rules

An unrecognized transaction always requires escalation. BodhaFlow must not try to decide whether the transaction is valid, dismiss the concern, investigate it, reverse it, submit a dispute, freeze a card, or take any other action.

The system must also escalate or give a safe fallback response when:

- The request is sensitive or unsafe
- The request is unsupported
- The intent classification has low confidence
- Important information is missing
- The available information conflicts
- The fictional customer is not authorized to access the requested record
- The relevant project policy is missing or does not support the requested response
- The request includes a prompt-injection attempt or instructions that conflict with the defined workflow

These rules are deterministic. An LLM cannot override them.

## Data and action boundaries

BodhaFlow will use only fictional, synthetic data and project-authored materials. It will not use, connect to, or suggest that it has access to real customers, financial accounts, transaction data, bank systems, payment processors, card networks, employer systems, or proprietary materials.

BodhaFlow will not move money or perform real financial actions. It will not issue refunds, submit disputes, freeze cards, change account details, alter transactions, or take other irreversible actions.

## How the AI is constrained

The AI component can help classify a request and generate a response within the workflow, but it does not have unrestricted control.

It cannot:

- Choose an agent that is not defined in the application
- Call a tool that is not explicitly allowlisted
- Run arbitrary code
- Bypass input validation or authorization checks
- Skip policy retrieval when policy grounding is required
- Override escalation rules
- Invent a policy, transaction detail, citation, tool result, or completed action

All tool inputs will be validated with Pydantic models. Authorization and sensitive-case decisions will use deterministic checks rather than model judgment alone.

## What this means for future work

Every later implementation decision must stay within these boundaries unless I deliberately revise this document first. If I change the V1 scope, safety rules, or allowed behavior, I will record the reason and update the relevant documentation before changing the application.
