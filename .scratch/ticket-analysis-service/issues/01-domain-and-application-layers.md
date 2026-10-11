# 01 Domain and application layers

Status: resolved
Type: task

## What
Business rules in pure Python, a use case, and a port, testable without a web server.

## Built (first version)
- Domain: `TicketText`, `Department`, `Probability`, `FrustrationScore`, `TicketAnalysis`; policies for escalation (threshold 0.5)
  and frustration level (calm below 0.5, annoyed below 1.5, furious from 1.5); errors `DomainError`, `InvalidTicket`, `ClassifierUnavailable`.
- Application: `TicketClassifier` `Protocol`, `AnalyzeTicket` use case, DTOs.
- Domain imports no FastAPI, Pydantic, OpenJev or httpx (checked by grep during the review).

## Superseded
The department/urgency/frustration types were removed when the service became a batch severity/category
service. The structure (ports, use case, domain errors) was kept. See batch-ticket-analysis/01.

## Verified by
Unit tests with a fake classifier (policies, value objects, use case).
