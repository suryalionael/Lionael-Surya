# AI Customer Support Agent

**Status:** 🔜 Planned

## Business Problem

A growing e-commerce business gets hundreds of repetitive support tickets daily ("where's my order," "how do I return this") that consume agent time better spent on genuinely complex cases. They need automatic triage: resolve the simple cases directly and escalate the rest with full context attached.

## Objective

Build a tool-calling AI agent that can look up order status, check return eligibility against policy, and answer FAQ-style questions — escalating to a human with a structured summary when it can't confidently resolve the ticket itself.

## Planned Tech Stack

- LangChain (or LlamaIndex) agent framework with tool-calling
- Claude/OpenAI API
- Mock tools: `get_order_status(order_id)`, `check_return_eligibility(order_id)`, `search_faq(query)`
- FastAPI backend simulating a ticketing system webhook

## Planned Deliverables

- [ ] Tool definitions with mock backend data (orders, policies, FAQ)
- [ ] Agent loop with explicit escalation logic (confidence threshold / unknown-tool fallback)
- [ ] Structured escalation summary format for human handoff
- [ ] Test suite of ~15 sample tickets covering resolvable and must-escalate cases
- [ ] Write-up on prompt/agent design and failure modes observed during testing

---
Back to [AI Engineering](../README.md) · [main portfolio](../../README.md).
