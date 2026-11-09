"""Who may open what. Narrow roles see one branch only; the assistant also refuses questions about screens a role cannot open."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class Role:
    id: str
    title: str
    tabs: Tuple[str, ...]
    everything: bool
    description: str
    landing: str


ROLES = {r.id: r for r in (
    Role("chairman", "Chairman / Owner", (), True, "Every branch, every number, every setting.", "home"),
    Role("finance", "Finance Manager", ("overview", "history", "profit", "staff", "khata", "suppliers", "orders", "price", "forecast", "assistant"),
         False, "Money in all branches. Cannot change stock or offers.", "overview"),
    Role("branch", "Branch Manager", ("home", "talk", "overview", "staff", "stock", "orders", "expiry", "brands", "customers", "khata", "routine"),
         False, "Only their own branch. No profit and no supplier dues.", "overview"),
    Role("hod", "Head of Department", ("home", "talk", "stock", "expiry"), False, "Only their own department.", "home"),
    Role("purchase", "Purchase & Stock Manager", ("stock", "orders", "suppliers", "expiry", "brands", "price", "regions", "offers"),
         False, "Buying and stock only. No cash, no profit, no customer credit.", "stock"),
    Role("audit", "Auditor (view only)", ("overview", "staff", "suppliers", "expiry", "khata"), False,
         "Looks at what needs checking. Cannot change or approve anything.", "staff"),
    Role("cashier", "Cashier (Counter)", ("counter",), False, "Only their own counter.", "counter"),
)}

SINGLE_BRANCH_ROLES = ("branch", "hod", "cashier")
REFUSAL = "Your role cannot see this. Please ask the person who has access."


def get_role(role_id: str) -> Role:
    try:
        return ROLES[role_id]
    except KeyError:
        raise ValueError(f"unknown role {role_id}") from None


def can_see(role_id: str, tab: str) -> bool:
    r = get_role(role_id)
    return r.everything or tab in r.tabs


def can_approve(role_id: str) -> bool:
    """Only the owner approves purchase orders."""
    return role_id == "chairman"


def blocked_answer(role_id: str, question: str) -> Optional[str]:
    """If the question is about a screen the role cannot open, return the refusal text; otherwise None."""
    s = question.lower()
    tab = None
    if re.search(r"profit|earn", s):
        tab = "profit"
    elif re.search(r"credit|khata|owe", s):
        tab = "khata"
    elif "cash" in s:
        tab = "staff"
    elif "supplier" in s:
        tab = "suppliers"
    return REFUSAL if tab and not can_see(role_id, tab) else None
