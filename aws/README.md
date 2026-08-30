# Workstream B — AWS stack

One arm64 Python 3.12 Lambda, dispatched by job name, on EventBridge
Scheduler. It emits cards to Telegram; **a human places every order**
(B-C2). No order routing exists in this stack or anywhere downstream.

Backlog and constraints: `../docs/TASKS.md` § Workstream B.
Spike findings and the decisions they forced: `../docs/AWS-RECON.md`.

## Layout

| File | Role |
|---|---|
| `template.yaml` | SAM template — function, state bucket, log group |
| `handler.py` | Entry point; `morning \| poll \| evening \| command` |
| `samconfig.toml` | Stack name, region, `project=occams` tag |
| `deploy-user-policy.json` | Scoped IAM policy for the deploy identity |

## Packaging is an allow-list, deliberately

`CodeUri` is the repo root, because the Lambda imports the **unforked**
`occams` package (B1.4). SAM's default Python builder would sweep the
*whole* repo in — a first build produced a **533 MB** artifact carrying
purchased market data, the Databento key, the Telegram token and the
venue name (B-C5). **`.samignore` does not bind that builder.**

So `BuildMethod: makefile` runs `build-CampaignFunction` in the root
`Makefile`, which copies only `occams/` + `aws/` + numpy, then runs
`scripts/check_artifact.py`, which **fails the build** on secrets, vendor
data, `*.local.md`, forbidden terms, or breaching Lambda's 250 MB limit.
Current artifact: **48.6 MB, clean**.

Note `occams.privacy` scans *tracked* files, so it is structurally blind
to precisely the git-ignored files at issue here. The artifact guard is
not redundant with it.

## First-time setup

**1. Deploy identity — DONE 2026-07-31.** IAM user `occams-deploy`
exists, tagged `project=occams`, with the customer-managed policy
`occams-deploy` (this directory's `deploy-user-policy.json`) attached.

Why a new user rather than the existing one: the account also holds two
retired projects awaiting teardown, and that project plans to delete
unused IAM users. Deploying as `Tromso-Aura-Hunter-dev` would couple the
two — exactly what keeping them separate was meant to prevent.

Scoping was verified with `iam simulate-principal-policy`, not assumed —
allowed on `/occams/*` parameters, the SAM bucket and
`occams-campaign-*` roles; denied on `/other/*`, foreign buckets and the
retired projects' roles; explicit deny on ECS/RDS/ECR-delete.

**2. Create its access key and local profile.** The user was created
with **no access keys**. Run this yourself — it pipes the secret straight
into your AWS config so it is never printed to a terminal or a
transcript, and echoes only the (non-secret) key id:

```bash
aws iam create-access-key --user-name occams-deploy --output json | python3 -c "import json,subprocess,sys; k=json.load(sys.stdin)['AccessKey']; [subprocess.run(['aws','configure','set',f,v,'--profile','occams'],check=True) for f,v in (('aws_access_key_id',k['AccessKeyId']),('aws_secret_access_key',k['SecretAccessKey']),('region','eu-north-1'))]; print('profile occams ready, key id:', k['AccessKeyId'])"
```

Region `eu-north-1` (inherited from the machine's default; `samconfig.toml`
is the single place to change it, and it is reversible until first deploy).

This is a long-lived credential — the class of thing the teardown brief
calls out as its biggest security item. Rotate it periodically, and
delete it if this stack is ever retired.

**3. Build and deploy:**

```bash
sam build --template aws/template.yaml
sam deploy --config-file aws/samconfig.toml --profile occams
```

`confirm_changeset` is on, so nothing applies without you reading the
diff first.

## Secrets

SSM SecureString under `/occams/` only (B-C4) — never in the repo, never
in plaintext env vars, never in logs. The Lambda's IAM grant is scoped to
that path plus `kms:Decrypt` via SSM. The local `.env` remains Workstream
A's source; neither reads the other's.

```bash
aws ssm put-parameter --profile occams --type SecureString \
  --name /occams/telegram/token --value "<token>"
```

## Cost

The account carries ~$10.51/month belonging to the retired projects, so
the $5 budget alarm (B4.4) **must** filter on `project=occams` or it fires
on their spend forever. Every resource here is tagged accordingly. This
stack's own expected cost is under $1/month, and $0 for market data —
the poller reads a 10-minute-delayed public source validated tick-exact
against CME (B0.5).
