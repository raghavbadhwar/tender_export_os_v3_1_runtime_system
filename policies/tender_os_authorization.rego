package tenderos.authz

import rego.v1

# The caller resolves action metadata and verifies the local approval artifacts.
# OPA remains the final fail-closed decision point; model-provided approval text
# is never accepted as proof.

default decision := {
    "allow": false,
    "status": "blocked",
    "reason_code": "NO_MATCHING_POLICY",
    "reason": "No authorization rule matched; deny by default.",
}

decision := {
    "allow": false,
    "status": "blocked",
    "reason_code": "PROHIBITED_ACTION",
    "reason": "The requested action is prohibited and cannot be unlocked by approval.",
} if {
    input.prohibited == true
} else := {
    "allow": false,
    "status": "blocked",
    "reason_code": "CREDENTIAL_MATERIAL_REJECTED",
    "reason": "Credentials or secret material are not valid policy inputs.",
} if {
    input.credentials_present == true
} else := {
    "allow": true,
    "status": "allowed",
    "reason_code": "LOW_RISK_INTERNAL_ACTION",
    "reason": "T0-T2 internal, advisory, or public read-only action is allowed and logged.",
} if {
    input.tier <= 2
    input.external_effect == false
    input.approval_required == false
} else := {
    "allow": false,
    "status": "blocked",
    "reason_code": "UNDECLARED_EXTERNAL_EFFECT",
    "reason": "An external effect cannot run under a T0-T2 authorization.",
} if {
    input.tier <= 2
    input.external_effect == true
} else := {
    "allow": false,
    "status": "approval_required",
    "reason_code": "VALID_APPROVAL_REQUIRED",
    "reason": input.approval.reason,
} if {
    input.approval_required == true
    input.approval.valid == false
} else := {
    "allow": false,
    "status": "blocked",
    "reason_code": "REQUIRED_CONTROLS_MISSING",
    "reason": input.controls.reason,
} if {
    input.approval_required == true
    input.approval.valid == true
    input.controls.satisfied == false
} else := {
    "allow": true,
    "status": "allowed",
    "reason_code": "SCOPED_APPROVAL_VERIFIED",
    "reason": "A current owner decision receipt, exact scope, and required controls were verified.",
} if {
    input.tier >= 3
    input.approval_required == true
    input.approval.valid == true
    input.controls.satisfied == true
}
