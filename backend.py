"""MuseBridge MVP backend core.

Dependency-free domain service used by the first testable backend slice.
It deliberately keeps provider calls outside the consent boundary.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Set
import json
import sqlite3

class BridgeError(Exception): pass
class PermissionDenied(BridgeError): pass
class InvalidState(BridgeError): pass

class MessageStatus(str, Enum): DRAFT="draft"; APPROVED="approved"; DELIVERED="delivered"; REJECTED="rejected"

@dataclass
class Message:
    id: str; sender: str; recipient: str; body: str; scope: str
    status: MessageStatus = MessageStatus.DRAFT
    approved_by: Set[str] = field(default_factory=set)
    delivered_once: bool = False

@dataclass
class Agreement:
    id: str; text: str; approvals: Set[str] = field(default_factory=set)
    status: str = "pending"

class MuseBridge:
    def __init__(self, db_path=":memory:"):
        self.users = {"alex", "jordan"}
        self.permissions: Dict[str, Set[str]] = {"alex": set(), "jordan": set()}
        self.messages: Dict[str, Message] = {}
        self.agreements: Dict[str, Agreement] = {}
        self.audit = []
        self.db_path = db_path
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.db.execute("CREATE TABLE IF NOT EXISTS bridge_state (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        self._load()

    def _save(self):
        state = {
            "permissions": {u: sorted(v) for u, v in self.permissions.items()},
            "messages": {k: {"id": v.id, "sender": v.sender, "recipient": v.recipient, "body": v.body, "scope": v.scope, "status": v.status.value, "approved_by": sorted(v.approved_by), "delivered_once": v.delivered_once} for k, v in self.messages.items()},
            "agreements": {k: {"id": v.id, "text": v.text, "approvals": sorted(v.approvals), "status": v.status} for k, v in self.agreements.items()},
            "audit": self.audit,
        }
        self.db.execute("INSERT OR REPLACE INTO bridge_state(key,value) VALUES('state',?)", (json.dumps(state),))
        self.db.commit()

    def _load(self):
        row = self.db.execute("SELECT value FROM bridge_state WHERE key='state'").fetchone()
        if not row: return
        state = json.loads(row[0])
        self.permissions = {u: set(v) for u, v in state["permissions"].items()}
        self.messages = {k: Message(v["id"], v["sender"], v["recipient"], v["body"], v["scope"], MessageStatus(v["status"]), set(v["approved_by"]), v["delivered_once"]) for k, v in state["messages"].items()}
        self.agreements = {k: Agreement(v["id"], v["text"], set(v["approvals"]), v["status"]) for k, v in state["agreements"].items()}
        self.audit = state["audit"]

    def _check_user(self, user):
        if user not in self.users: raise PermissionDenied("unknown user")

    def grant(self, owner, scope):
        self._check_user(owner); self.permissions[owner].add(scope)
        self._log(owner, "permission_granted", scope)
        self._save()

    def revoke(self, owner, scope):
        self._check_user(owner); self.permissions[owner].discard(scope)
        self._log(owner, "permission_revoked", scope)
        self._save()

    def prepare_message(self, message_id, sender, recipient, body, scope="message_content"):
        self._check_user(sender); self._check_user(recipient)
        if sender == recipient: raise InvalidState("sender and recipient must differ")
        if scope not in self.permissions[sender]: raise PermissionDenied("sender has not granted this scope")
        if message_id in self.messages: raise InvalidState("duplicate message id")
        msg = Message(message_id, sender, recipient, body, scope)
        self.messages[message_id] = msg; self._log(sender, "message_prepared", message_id)
        self._save()
        return msg

    def approve_message(self, message_id, user):
        msg = self.messages[message_id]; self._check_user(user)
        if user != msg.sender: raise PermissionDenied("only the sender may approve a draft")
        if msg.status != MessageStatus.DRAFT: raise InvalidState("message is not a draft")
        if msg.scope not in self.permissions[msg.sender]: raise PermissionDenied("permission was revoked")
        msg.approved_by.add(user); msg.status = MessageStatus.APPROVED
        self._log(user, "message_approved", message_id); self._save(); return msg

    def deliver_message(self, message_id):
        msg = self.messages[message_id]
        if msg.delivered_once: return msg
        if msg.status != MessageStatus.APPROVED: raise InvalidState("message requires approval")
        if msg.scope not in self.permissions[msg.sender]: raise PermissionDenied("permission was revoked")
        msg.delivered_once = True; msg.status = MessageStatus.DELIVERED
        self._log("bridge", "message_delivered", message_id); self._save(); return msg

    def create_agreement(self, agreement_id, text):
        if agreement_id in self.agreements: raise InvalidState("duplicate agreement id")
        self.agreements[agreement_id] = Agreement(agreement_id, text)
        self._log("bridge", "agreement_created", agreement_id); self._save(); return self.agreements[agreement_id]

    def approve_agreement(self, agreement_id, user):
        self._check_user(user); agreement = self.agreements[agreement_id]
        if agreement.status != "pending": raise InvalidState("agreement is not pending")
        agreement.approvals.add(user)
        if agreement.approvals == self.users: agreement.status = "approved"
        self._log(user, "agreement_approved", agreement_id); self._save(); return agreement

    def _log(self, actor, action, target):
        self.audit.append({"at": datetime.now(timezone.utc).isoformat(), "actor": actor, "action": action, "target": target})
