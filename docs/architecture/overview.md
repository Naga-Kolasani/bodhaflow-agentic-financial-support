# Architecture Overview

This document describes how I plan to structure BodhaFlow as I build it. The goal is to create a clear, local-first system for fictional financial-support scenarios, with policy grounding, authorization checks, restricted mock tools, and safe escalation built into the workflow.

BodhaFlow is not designed to take real financial actions. Every customer, transaction, transfer, merchant, policy, and support case used by the application will be fictional and created specifically for this project.

## Main parts of the system

I plan to build BodhaFlow with the following components:

- FastAPI for the API that receives support requests and returns structured responses
- Pydantic for request and response models, workflow state, validation, and mock-tool input checks
- LangGraph for the explicit workflow that controls how a request moves through the system
- One LLM provider for limited tasks such as intent classification and response generation
- sentence-transformers for local text embeddings
- ChromaDB or FAISS for local policy retrieval
- Markdown files for BodhaFlow's fictional support policies
- JSON or SQLite for synthetic customer, transaction, transfer, and support-case data
- pytest for unit and integration tests
- Ruff for code quality checks
- Docker, Docker Compose, and GitHub Actions after the local application is working reliably

I will choose between ChromaDB and FAISS, and between JSON and SQLite, before building the related parts of the application. The choice will be based on keeping the project simple, local, and easy to test.

## How a request will move through BodhaFlow

A fictional customer will send a support request through the API. The workflow will then follow a controlled set of steps:

1. Validate the API request and create a request ID for tracing.
2. Check for unsupported requests, unsafe instructions, and prompt-injection attempts.
3. Classify the request into one of the five supported scenarios, or identify that clarification or escalation is needed.
4. Apply mandatory escalation rules before looking up any record or generating a resolution.
5. Check whether the request includes the information needed to continue.
6. Confirm that the fictional customer is allowed to access the requested fictional transaction or transfer.
7. Retrieve the relevant BodhaFlow policy guidance.
8. Choose an allowlisted mock tool only when the policy and authorization checks allow it.
9. Validate the tool input, run the mock tool, and validate the returned result.
10. Return a response with cited guidance, a clarification question, a safe refusal, or an escalation outcome.

The workflow should stop safely if required information is missing, authorization fails, the policy does not support a response, a tool result is inconsistent, or an error occurs.

## Where safety controls apply

I want the safety controls to be part of the system design, not an afterthought added to the final response.

- API requests are untrusted and must be validated before entering the workflow.
- LLM output is untrusted and must be structured and validated before it affects routing or response content.
- Authorization checks happen before a synthetic transaction or transfer record is returned.
- The LLM cannot choose arbitrary agents, tools, code, or workflow transitions.
- Mock tools will be explicitly allowlisted and protected by Pydantic schemas.
- Policy retrieval will provide the grounding for policy-based responses and their citations.
- Missing policy support, retrieval failures, invalid tool inputs, malformed LLM output, unavailable dependencies, and conflicting information must lead to a safe fallback or escalation.
- Deterministic rules will handle sensitive cases and required escalations.

## Escalation path

BodhaFlow will always escalate an unrecognized transaction. It will also escalate or safely stop when a request is sensitive, unsafe, unsupported, low confidence, missing important information, inconsistent with available evidence, unauthorized, or not covered by the available policy.

The LLM will not be able to override these rules.

## What this architecture does not include

BodhaFlow will not include:

- Real financial accounts, customers, transaction data, or payment systems
- Real money movement, refunds, disputes, card freezes, account changes, or other irreversible actions
- Unrestricted agent selection, tool use, or code execution
- Support for financial topics outside the five V1 scenarios
- Multiple LLM providers
- Managed vector databases, AWS, Kubernetes, or a React frontend

## Current stage

I have documented the initial design and safety boundaries for BodhaFlow. I will build the application in small, tested stages.
