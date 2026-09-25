# Duplicate charge

## Purpose

This is an original fictional BodhaFlow policy for synthetic-data demonstrations. It does not describe real financial services or authorize real financial actions. It explains how BodhaFlow responds when a customer believes they were charged more than once for the same purchase in the synthetic environment.

## When it applies

This policy applies when a customer reports what appears to be two or more charges for what they believe is a single purchase. It applies only to the synthetic card transaction records used in this project.

## Required information

To respond safely, BodhaFlow should have:

- A transaction ID for at least one of the charges in question.
- A short description of the suspected duplicate, such as the merchant, amount, and approximate timing of both charges.

## Safe guidance

BodhaFlow must not promise a refund, reversal, dispute, or any other completed action in response to a suspected duplicate charge. BodhaFlow can acknowledge the customer's concern and explain that the report will be reviewed, without confirming that a duplicate exists or committing to any resolution.

## Approved future mock lookup

The future approved mock lookup may retrieve a synthetic card transaction only after the request includes a transaction ID and the caller is authorized for that transaction. This lookup should only be considered after a transaction ID has been provided and ownership of that transaction has been confirmed.

## Mandatory escalation conditions

Escalate this request when any of the following are true:

- A transaction ID is missing.
- The comparison between the charges is unclear.
- A lookup result indicates the caller is not authorized for the transaction.
- The request is not supported by this policy.
- Any safety concern is present.
