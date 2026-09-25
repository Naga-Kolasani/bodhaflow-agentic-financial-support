# Declined card payment

## Purpose

This is an original fictional BodhaFlow policy for synthetic-data demonstrations. It does not describe real financial services or authorize real financial actions. It explains how BodhaFlow responds when a customer reports that a card payment was declined in the synthetic environment.

## When it applies

This policy applies when a customer reports that a card payment attempt did not go through and was declined. It applies only to the synthetic card transaction records used in this project.

## Required information

To respond safely, BodhaFlow should have:

- A transaction ID for the declined payment, if one exists.
- A short description of what the customer was trying to do, such as the merchant or purpose of the payment.

## Safe guidance

BodhaFlow cannot determine or claim a specific cause for a decline in the synthetic environment. BodhaFlow can acknowledge the decline and note that the customer may try the payment again later or use another available payment method, without promising that a retry will succeed or that any specific outcome will happen.

## Approved future mock lookup

The future approved mock lookup may retrieve a synthetic card transaction only after the request includes a transaction ID and the caller is authorized for that transaction.

## Mandatory escalation conditions

Escalate this request when any of the following are true:

- The customer reports repeated declines for the same or related payments.
- The details provided are unclear.
- Required information is missing.
- The request is not supported by this policy.
- Any safety concern is present.
