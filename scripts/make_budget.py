"""B4.4 — the $5 monthly budget, filtered on the cost-allocation tag.

Not in the SAM template: `AWS::Budgets::Budget` is a global resource that
does not exist in eu-north-1, and standing up a second us-east-1 stack to
carry one alarm is more machinery than the alarm is worth.

**The tag filter is the whole point.** The account carries ~$10.51/month
belonging to two retired projects, so an unfiltered $5 budget would sit in
ALARM permanently and teach everyone to ignore it — which is worse than
having no alarm at all.

Usage:  python3 scripts/make_budget.py --profile occams --email you@example
"""

from __future__ import annotations

import argparse
import sys

LIMIT_USD = "5"
TAG = "user:project$occams"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="occams")
    ap.add_argument("--email", required=True)
    a = ap.parse_args()

    import boto3
    session = boto3.Session(profile_name=a.profile)
    account = session.client("sts").get_caller_identity()["Account"]
    # Budgets is global, reached through us-east-1 regardless of where the
    # stack lives.
    client = session.client("budgets", region_name="us-east-1")

    budget = {
        "BudgetName": "occams-monthly",
        "BudgetType": "COST",
        "TimeUnit": "MONTHLY",
        "BudgetLimit": {"Amount": LIMIT_USD, "Unit": "USD"},
        "CostFilters": {"TagKeyValue": [TAG]},
    }
    notifications = [{
        "Notification": {"NotificationType": "ACTUAL",
                         "ComparisonOperator": "GREATER_THAN",
                         "Threshold": 80.0,
                         "ThresholdType": "PERCENTAGE"},
        "Subscribers": [{"SubscriptionType": "EMAIL", "Address": a.email}],
    }]
    try:
        client.create_budget(AccountId=account, Budget=budget,
                             NotificationsWithSubscribers=notifications)
        print(f"created budget occams-monthly (${LIMIT_USD}/mo, {TAG})")
    except client.exceptions.DuplicateRecordException:
        client.update_budget(AccountId=account, NewBudget=budget)
        print(f"updated existing budget occams-monthly (${LIMIT_USD}/mo)")

    print("\nNOTE: `project` must be ACTIVATED as a cost-allocation tag in\n"
          "Billing > Cost allocation tags before this filter matches\n"
          "anything, and activation can take ~24h. Until then the budget\n"
          "reports $0 — which is under-reporting, never over.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
