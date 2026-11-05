# MuseBridge — A2A Relationship Bridge\n\nLive demo: https://musebridge.onrender.com\n\nA portfolio-ready prototype for consent-first communication between two personal AI agents.

MuseBridge is a consent-based prototype that connects two independent personal AI agents without merging their private memories.

## Current milestone

This first vertical slice is a self-contained, deterministic demo of the core product boundary:

- two isolated agent profiles
- Tell Them / Help Them Understand / Work This Out interaction modes
- draft-before-transmit workflow
- explicit consent and revocation controls
- synthetic data only
- audit view showing what crossed the bridge and what was withheld
- provider settings that distinguish adapters from personal-account memory access

## Demo flow\n\n1. Open the live demo.\n2. Prepare a draft in Bridge.\n3. Review Consent and revoke permission.\n4. Open Agreements and approve as both participants.\n5. Open Audit log to inspect the recorded events.\n\nThe hosted portfolio uses a deterministic demo identity so the complete product flow is available without external account setup. Supabase Auth is the production-auth upgrade path.\n\n## Run locally

Open `index.html` in a browser, or serve the directory:

```bash
python3 -m http.server 4173
```

Then visit `http://localhost:4173`.

## Important limitation

This is the UI/protocol demonstration, not yet a production multi-user backend. The next implementation slice is a FastAPI service with authenticated identities, server-side consent enforcement, idempotent message delivery, revocation, and provider adapters behind environment-based secrets.
