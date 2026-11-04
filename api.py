"""HTTP adapter for MuseBridge. Install requirements and run with uvicorn api:app."""
import os
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from backend import MuseBridge, BridgeError

app = FastAPI(title="MuseBridge API", version="0.1.0")
allowed_origins = [origin.strip() for origin in os.getenv("MUSEBRIDGE_ALLOWED_ORIGINS", "http://localhost:4173,http://127.0.0.1:4173").split(",") if origin.strip()]
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_methods=["*"], allow_headers=["*"], allow_credentials=False)
bridge = MuseBridge("musebridge.db")

@app.get("/", include_in_schema=False)
def frontend():
    from fastapi.responses import HTMLResponse
    index = Path(__file__).with_name("index.html").read_text(encoding="utf-8")
    client = Path(__file__).with_name("app.js").read_text(encoding="utf-8")
    email_auth = '<div id="email-auth" style="margin:10px 0"><input id="auth-email" type="email" value="imajeemale@gmail.com" style="padding:10px;border-radius:8px;border:1px solid #263348;background:#090f18;color:white"><button id="email-signin">Email me a secure sign-in link</button><span id="email-notice" class="muted"></span></div>'
    page = index.replace('<nav>', email_auth + '<nav>')
    return HTMLResponse(page.replace("</body>", f"<script>{client}</script></body>"))

@app.get("/app.js", include_in_schema=False)
def frontend_script():
    from fastapi.responses import FileResponse
    return FileResponse(Path(__file__).with_name("app.js"), media_type="application/javascript")

@app.get("/musebridge-client.js", include_in_schema=False)
def frontend_client_script():
    from fastapi.responses import FileResponse
    return FileResponse(Path(__file__).with_name("app.js"), media_type="application/javascript")
DEMO_TOKENS = {"alex": os.getenv("MUSEBRIDGE_ALEX_TOKEN", "alex-demo-token"), "jordan": os.getenv("MUSEBRIDGE_JORDAN_TOKEN", "jordan-demo-token")}
AUTH_MODE = os.getenv("MUSEBRIDGE_AUTH_MODE", "demo").lower()
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_PUBLISHABLE_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY", os.getenv("SUPABASE_ANON_KEY", ""))

def supabase_user(access_token: str):
    """Validate a bearer token through Supabase Auth instead of trusting client claims."""
    if not SUPABASE_URL or not SUPABASE_PUBLISHABLE_KEY or not access_token:
        raise HTTPException(503, "Supabase authentication is not configured")
    request = Request(f"{SUPABASE_URL}/auth/v1/user", headers={"apikey": SUPABASE_PUBLISHABLE_KEY, "Authorization": f"Bearer {access_token}"})
    try:
        with urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError):
        raise HTTPException(401, "valid Supabase access token required")
    if not payload.get("id"):
        raise HTTPException(401, "valid Supabase access token required")
    return payload["id"]

def current_user(authorization: str = Header(default=""), x_muse_user: str = Header(default=""), x_muse_token: str = Header(default="")):
    if AUTH_MODE == "supabase":
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer":
            raise HTTPException(401, "Bearer access token required")
        return supabase_user(token)
    if x_muse_user not in DEMO_TOKENS or x_muse_token != DEMO_TOKENS[x_muse_user]:
        raise HTTPException(401, "valid MuseBridge identity required")
    return x_muse_user

class PermissionRequest(BaseModel):
    owner: str; scope: str = Field(min_length=1)

class MessageRequest(BaseModel):
    sender: str; recipient: str; body: str = Field(min_length=1); scope: str = "message_content"

class AgreementRequest(BaseModel):
    text: str = Field(min_length=1)

def safe(call):
    try: return call()
    except KeyError: raise HTTPException(404, "resource not found")
    except BridgeError as exc: raise HTTPException(409, str(exc))

@app.get("/health")
def health(): return {"status": "ok", "service": "musebridge", "auth_mode": AUTH_MODE}

@app.post("/permissions/grant")
def grant(req: PermissionRequest, user=Depends(current_user)):
    if user != req.owner: raise HTTPException(403, "cannot change another user's permissions")
    safe(lambda: bridge.grant(req.owner, req.scope)); return {"owner": req.owner, "scope": req.scope, "active": True}

@app.post("/permissions/revoke")
def revoke(req: PermissionRequest, user=Depends(current_user)):
    if user != req.owner: raise HTTPException(403, "cannot change another user's permissions")
    safe(lambda: bridge.revoke(req.owner, req.scope)); return {"owner": req.owner, "scope": req.scope, "active": False}

@app.post("/messages/{message_id}/prepare")
def prepare(message_id: str, req: MessageRequest, user=Depends(current_user)):
    if user != req.sender: raise HTTPException(403, "cannot prepare as another user")
    msg = safe(lambda: bridge.prepare_message(message_id, **req.model_dump()))
    return {"id": msg.id, "status": msg.status, "transmitted": False}

@app.post("/messages/{message_id}/approve")
def approve(message_id: str, user=Depends(current_user)):
    msg = safe(lambda: bridge.approve_message(message_id, user)); return {"id": msg.id, "status": msg.status}

@app.post("/messages/{message_id}/deliver")
def deliver(message_id: str, user=Depends(current_user)):
    msg = safe(lambda: bridge.deliver_message(message_id)); return {"id": msg.id, "status": msg.status, "transmitted": True}

@app.post("/agreements/{agreement_id}")
def create_agreement(agreement_id: str, req: AgreementRequest, user=Depends(current_user)):
    agreement = safe(lambda: bridge.create_agreement(agreement_id, req.text)); return {"id": agreement.id, "status": agreement.status}

@app.post("/agreements/{agreement_id}/approve")
def approve_agreement(agreement_id: str, user=Depends(current_user)):
    agreement = safe(lambda: bridge.approve_agreement(agreement_id, user)); return {"id": agreement.id, "status": agreement.status, "approvals": sorted(agreement.approvals)}

@app.get("/audit")
def audit(user=Depends(current_user)): return {"events": bridge.audit}
