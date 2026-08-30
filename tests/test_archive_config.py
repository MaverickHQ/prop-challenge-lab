"""Pre-publication portability: nothing account-specific may be hardcoded.

`aws/research-template.yaml` names the bucket
`occams-research-${AWS::AccountId}`, so it belongs to whoever deployed it.
This module used to hardcode one account's name — which meant a reader could
deploy the infrastructure correctly and still have the code point at somebody
else's bucket, and it published an AWS account id in the process. The AWS
profile name was hardcoded too, and a new user has no profile called
"occams".

The fix that makes it safe to publish is the same fix that makes it usable.
"""

from __future__ import annotations

import re
from pathlib import Path

from occams import archive

ROOT = Path(__file__).resolve().parent.parent

# Built at runtime so the 12-digit LITERAL never appears in this file. The
# prepublish audit scans for exactly that shape, and the first version of
# this test tripped it — a scanner matching its own fixture, which is the
# third time that has happened here (the untracked-file gap, the sentinel
# term, and now this). Test fixtures must construct anything they are
# testing the detection of, or the detector has to be switched off to make
# its own tests pass.
FAKE_ACCOUNT = "9999" + "8888" + "7777"
OTHER_ACCOUNT = "1111" + "2222" + "3333"


def test_no_aws_account_id_is_hardcoded_anywhere_in_the_package():
    """A 12-digit literal in source is either an account id or a coincidence.
    occams/stats.py holds AS241 polynomial coefficients, which is the
    coincidence — it is excluded by name so the check stays meaningful."""
    bad = []
    for f in sorted((ROOT / "occams").glob("*.py")):
        if f.name == "stats.py":
            continue
        for n, line in enumerate(f.read_text().splitlines(), 1):
            if re.search(r"(?<![\d.eE-])\d{12}(?![\d.eE-])", line):
                bad.append(f"{f.name}:{n}")
    assert not bad, f"hardcoded 12-digit literal(s): {bad}"


def test_no_hardcoded_aws_profile_name():
    src = (ROOT / "occams" / "archive.py").read_text()
    assert 'profile_name="occams"' not in src
    assert "PROFILE_ENV" in src


def test_an_explicit_bucket_override_wins(monkeypatch):
    archive._reset_bucket_cache()
    monkeypatch.setenv(archive.BUCKET_ENV, "someone-elses-bucket")
    assert archive.bucket() == "someone-elses-bucket"
    archive._reset_bucket_cache()


def test_the_bucket_is_derived_from_the_account_actually_in_use(monkeypatch):
    """Mirrors the template's !Sub occams-research-${AWS::AccountId}."""
    archive._reset_bucket_cache()
    monkeypatch.delenv(archive.BUCKET_ENV, raising=False)

    class _STS:
        def get_caller_identity(self):
            return {"Account": FAKE_ACCOUNT}

    class _Sess:
        def client(self, name):
            assert name == "sts"
            return _STS()

    monkeypatch.setattr(archive, "_session", lambda: _Sess())
    assert archive.bucket() == f"occams-research-{FAKE_ACCOUNT}"
    archive._reset_bucket_cache()


def test_the_account_is_looked_up_at_most_once(monkeypatch):
    """Importing this module must not cost an STS call, and a Lambda cold
    start must not pay for one per operation."""
    archive._reset_bucket_cache()
    monkeypatch.delenv(archive.BUCKET_ENV, raising=False)
    calls = []

    class _STS:
        def get_caller_identity(self):
            calls.append(1)
            return {"Account": OTHER_ACCOUNT}

    monkeypatch.setattr(archive, "_session",
                        lambda: type("S", (), {"client": lambda s, n: _STS()})())
    archive.bucket()
    archive.bucket()
    archive.bucket()
    assert len(calls) == 1
    archive._reset_bucket_cache()


def test_the_template_still_derives_the_same_name():
    """If the template and the code ever disagree, the code points at a
    bucket the template never made."""
    tpl = (ROOT / "aws" / "research-template.yaml").read_text()
    assert f"{archive.BUCKET_PREFIX}-${{AWS::AccountId}}" in tpl


def test_no_template_ships_a_personal_identifier_as_a_default():
    """An IAM user name, an email address — a CloudFormation Default is
    shipped to every reader, and silently applies to every deployer who does
    not override it."""
    import re
    for name in ("research-template.yaml", "template.yaml"):
        tpl = (ROOT / "aws" / name).read_text()
        for param in ("AdminPrincipal", "AlarmEmail"):
            # split on the DECLARATION, not a bare mention: template.yaml
            # references AdminPrincipal in prose, which slipped past a
            # membership test that omitted the colon and then indexed a
            # one-element split.
            parts = tpl.split(f"\n  {param}:")
            if len(parts) < 2:
                continue
            block = parts[1].split("Description:")[0]
            assert "Default:" not in block, f"{name}: {param} has a default"
        assert not re.search(r"Default:\s*\S+@\S+\.\S+", tpl), \
            f"{name} ships an email address as a default"


def test_the_template_does_not_ship_a_real_iam_principal_as_a_default():
    """A default principal is both a disclosure and a footgun: it silently
    exempts an identity that does not exist in the deployer's account."""
    tpl = (ROOT / "aws" / "research-template.yaml").read_text()
    block = tpl.split("AdminPrincipal:")[1].split("Description:")[0]
    assert "Default:" not in block, "AdminPrincipal must be a required parameter"
