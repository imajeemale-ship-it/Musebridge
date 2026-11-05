# MuseBridge Portfolio Case Study

## The problem

Personal AI assistants are becoming more useful, but they are still isolated from the people around us. Sharing an entire memory system is too invasive; sharing nothing makes coordination frustrating.

## The idea

MuseBridge creates a controlled bridge between two independent agents. It supports private communication without merging private memories.

## Product principle

Nothing crosses without approval.

Every exchange follows:

1. A draft is prepared.
2. A permission is checked.
3. The exchange is approved.
4. Delivery is recorded.
5. Permission can be revoked.

## What this prototype demonstrates

- Consent-aware agent coordination
- Draft-before-transmit messaging
- Mutual agreement approval
- Revocation controls
- Idempotent delivery
- Persistent audit history
- A production-authentication path through Supabase
- A deterministic demo mode for reliable portfolio presentation

## Technical decisions

The domain rules are isolated in a Python service so the safety model can be tested independently from the browser and HTTP transport. FastAPI exposes the service, SQLite preserves demo state, and the frontend remains intentionally lightweight. Supabase Auth and Postgres/RLS are documented as the next production layer.

## Why it matters

The interesting product boundary is not simply agent-to-agent messaging. It is negotiated coordination: two personal systems can help people understand each other while preserving privacy, consent, and the ability to say no.

Live demo: https://musebridge.onrender.com
