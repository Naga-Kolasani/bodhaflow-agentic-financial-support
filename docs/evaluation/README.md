# Evaluation

I will evaluate BodhaFlow as I build it because a system like this should not be judged only by whether it can produce a helpful-sounding response.

The evaluation work will focus on whether BodhaFlow follows the intended workflow safely and consistently. Every evaluation case will use fictional customers, transactions, transfers, merchants, policies, and support requests created specifically for this project.

## What I will evaluate

I plan to measure whether BodhaFlow:

- Identifies the correct support scenario
- Retrieves and cites relevant BodhaFlow policy guidance
- Uses the correct mock tool only when it is allowed
- Prevents a fictional customer from accessing another customer's fictional records
- Escalates unrecognized transactions every time
- Escalates or safely stops for sensitive, unsupported, unclear, or low-confidence requests
- Resists prompt-injection attempts that try to bypass policy, authorization, tool, or escalation rules
- Returns API responses within a reasonable local-development time

## Evaluation scenarios

The evaluation set will include examples of:

- Supported requests with enough information to continue
- Supported requests that need clarification
- Requests that fall outside the five V1 support scenarios
- Attempts to access another fictional customer's transaction or transfer
- Prompt-injection attempts
- Unrecognized transactions and other sensitive situations
- Requests with missing, conflicting, or incomplete evidence
- Retrieval failures, unavailable policy support, malformed tool input, and mock-tool failures

## How I will report results

I will keep the evaluation set versioned with the project and document how each scenario is expected to behave.

When I report results, I will include the method, the number and type of cases tested, the outcome for each evaluation category, and the known limitations. I will not invent scores, claim reliability that I have not tested, or hide failures that show where the system needs improvement.
