# MuseBridge — A2A Relationship Bridge

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

## Run locally

Open `index.html` in a browser, or serve the directory:

```bash
python3 -m http.server 4173
```

Then visit `http://localhost:4173`.

## Important limitation

This is the UI/protocol demonstration, not yet a production multi-user backend. The next implementation slice is a FastAPI service with authenticated identities, server-side consent enforcement, idempotent message delivery, revocation, and provider adapters behind environment-based secrets.
