"""
Lambda Authorizer entry point (TOKEN type).

Validates a static API key sent in the Authorization header.
Simple token auth: no user identity, no expiry, no rotation logic.
"""

import os

VALID_KEYS = set(os.environ.get("API_KEYS", "").split(","))


def api_handler(event, context):
    """
    API Gateway TOKEN authorizer.

    Checks if the Authorization header token is in VALID_KEYS.
    Returns IAM policy allowing or denying access to the entire API/stage.
    """
    token = (event.get("authorizationToken") or "").strip()
    method_arn = event.get("methodArn", "")

    is_valid = token in VALID_KEYS and token != ""

    effect = "Allow" if is_valid else "Deny"
    principal_id = "user" if is_valid else "anonymous"

    # Build resource ARN for whole stage: arn:aws:execute-api:region:account:api_id/stage/*/*
    # This allows API Gateway to cache the decision across all routes for 300s per token
    parts = method_arn.split("/")
    resource = f"{parts[0]}/{parts[1]}/*/*" if len(parts) >= 2 else "*"

    return {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": effect,
                    "Resource": resource,
                }
            ],
        },
    }