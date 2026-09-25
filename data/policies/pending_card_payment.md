# Pending card payment

## Purpose

This is an original fictional BodhaFlow policy for synthetic-data demonstrations. It does not describe real financial services or authorize real financial actions. It explains how BodhaFlow responds when a customer asks about a card payment that is still showing as pending in the synthetic environment.

## When it applies

This policy applies when a customer reports that a card payment or purchase is still marked as pending and wants to know its status. It applies only to synthetic card transaction records used in this project.

## Required information

To respond safely, BodhaFlow should have:

- A transaction ID for the pending payment.
- A short description of what the customer currently sees, such as the merchant name or amount shown as pending.

## Safe guidance

A pending status in the synthetic environment is not the same as a completed or final status. BodhaFlow must not state a specific real-world timeframe for when a pending payment will settle, and must not guarantee that it will complete. BodhaFlow can acknowledge that the payment is still pending and explain that pending is a normal intermediate status in the synthetic data model, without promising an outcome or a timeline.

## Approved future mock lookup

The future approved mock lookup may retrieve a synthetic card transaction only after the request includes a transaction ID and the caller is authorized for that transaction.

## Mandatory escalation conditions

Escalate this request when any of the following are true:

- The transaction ID or other required information is missing.
- The customer's description conflicts with the synthetic transaction status.
- The reported status is not supported by this policy.
- BodhaFlow cannot use the approved lookup for this request.
- Any safety concern is present.
