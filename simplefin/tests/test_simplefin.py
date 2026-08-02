from __future__ import annotations

import base64
import importlib.util
import json
import os
import stat
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock
from urllib.error import HTTPError


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "simplefin.py"
)
SPEC = importlib.util.spec_from_file_location("simplefin_skill_client", SCRIPT_PATH)
assert SPEC and SPEC.loader
simplefin = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = simplefin
SPEC.loader.exec_module(simplefin)


class FakeResponse:
    def __init__(self, body: bytes, *, headers: dict[str, str] | None = None):
        self._body = body
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, limit: int = -1) -> bytes:
        return self._body if limit < 0 else self._body[:limit]


class SimpleFINClientTests(unittest.TestCase):
    def setUp(self):
        self.environment = mock.patch.dict(
            os.environ,
            {
                "SIMPLEFIN_ALLOWED_HOST_SUFFIXES": ".simplefin.org",
            },
            clear=True,
        )
        self.environment.start()

    def tearDown(self):
        self.environment.stop()

    def test_parse_access_url_removes_credentials(self):
        details = simplefin.parse_access_url(
            "https://user%40example.com:p%3Ass@bridge.simplefin.org/simplefin"
        )
        self.assertEqual(details.username, "user@example.com")
        self.assertEqual(details.password, "p:ss")
        self.assertEqual(
            details.accounts_url,
            "https://bridge.simplefin.org/simplefin/accounts",
        )
        self.assertNotIn("user", details.accounts_url)

    def test_rejects_non_https_and_untrusted_hosts(self):
        with self.assertRaisesRegex(simplefin.SimpleFINError, "HTTPS"):
            simplefin.parse_access_url("http://u:p@bridge.simplefin.org/simplefin")
        with self.assertRaisesRegex(simplefin.SimpleFINError, "not allowed"):
            simplefin.parse_access_url("https://u:p@example.com/simplefin")

    def test_setup_token_decoding_accepts_missing_padding(self):
        claim_url = "https://bridge.simplefin.org/simplefin/claim/test"
        token = base64.b64encode(claim_url.encode()).decode().rstrip("=")
        self.assertEqual(simplefin._decode_setup_token(token), claim_url)

    def test_query_window_is_exclusive_and_dst_aware(self):
        start_date, end_date, start_ts, end_ts = simplefin._parse_query_window(
            "2026-03-08",
            "2026-03-09",
            "America/New_York",
        )
        self.assertEqual(start_date.isoformat(), "2026-03-08")
        self.assertEqual(end_date.isoformat(), "2026-03-09")
        self.assertEqual(end_ts - start_ts, 23 * 60 * 60)

    def test_rejects_more_than_90_days(self):
        with self.assertRaisesRegex(simplefin.SimpleFINError, "90 days"):
            simplefin._parse_query_window(
                "2026-01-01",
                "2026-04-02",
                "America/New_York",
            )

    def test_secret_file_is_written_with_mode_0600(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".simplefin" / "access-url"
            access_url = "https://u:p@bridge.simplefin.org/simplefin"
            simplefin._write_secret_file(path, access_url, replace=False)
            self.assertEqual(path.read_text().strip(), access_url)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_load_rejects_world_readable_secret(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "access-url"
            path.write_text("https://u:p@bridge.simplefin.org/simplefin\n")
            path.chmod(0o644)
            with mock.patch.dict(
                os.environ,
                {
                    "SIMPLEFIN_ALLOWED_HOST_SUFFIXES": ".simplefin.org",
                    "SIMPLEFIN_ACCESS_URL_FILE": str(path),
                },
                clear=True,
            ):
                with self.assertRaisesRegex(simplefin.SimpleFINError, "permissions"):
                    simplefin.load_access_url()

    def test_access_url_file_cli_option_sets_explicit_state_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "access-url"
            path.write_text("https://u:p@bridge.simplefin.org/simplefin\n")
            path.chmod(0o600)
            with mock.patch.object(
                simplefin,
                "fetch_accounts",
                return_value={"accounts": [], "connections": [], "errors": []},
            ) as fetch:
                exit_code = simplefin.main(
                    ["--access-url-file", str(path), "accounts"]
                )
            self.assertEqual(exit_code, 0)
            self.assertEqual(os.environ["SIMPLEFIN_ACCESS_URL_FILE"], str(path))
            fetch.assert_called_once_with(balances_only=True, timeout=30.0)

    def test_fetch_accounts_uses_basic_auth_and_normalizes_data(self):
        payload = {
            "errlist": [],
            "connections": [
                {
                    "conn_id": "c1",
                    "name": "Example Bank",
                    "org_id": "o1",
                    "sfin_url": "https://bank.example",
                }
            ],
            "accounts": [
                {
                    "id": "a1",
                    "conn_id": "c1",
                    "name": "Checking",
                    "currency": "USD",
                    "balance": "100.00",
                    "balance-date": 1785369600,
                    "transactions": [
                        {
                            "id": "t1",
                            "posted": 1785369600,
                            "amount": "-12.34",
                            "description": "Coffee",
                        }
                    ],
                }
            ],
        }
        captured = {}

        def fake_urlopen(request, **kwargs):
            captured["url"] = request.full_url
            captured["authorization"] = request.get_header("Authorization")
            return FakeResponse(json.dumps(payload).encode())

        with mock.patch.dict(
            os.environ,
            {
                "SIMPLEFIN_ALLOWED_HOST_SUFFIXES": ".simplefin.org",
                "SIMPLEFIN_ACCESS_URL": "https://user:pass@bridge.simplefin.org/simplefin",
            },
            clear=True,
        ), mock.patch.object(simplefin, "_urlopen", fake_urlopen):
            result = simplefin.fetch_accounts(
                start_timestamp=100,
                end_timestamp=200,
                account_ids=["a1"],
            )

        self.assertNotIn("user", captured["url"])
        self.assertEqual(
            captured["authorization"],
            "Basic " + base64.b64encode(b"user:pass").decode(),
        )
        self.assertIn("start-date=100", captured["url"])
        self.assertIn("end-date=200", captured["url"])
        self.assertIn("account=a1", captured["url"])
        transaction = result["accounts"][0]["transactions"][0]
        self.assertEqual(transaction["amount"], "-12.34")
        self.assertEqual(transaction["direction"], "outflow")

    def test_structured_errors_are_sanitized(self):
        payload = {
            "errlist": [
                {
                    "code": "act.missingdata",
                    "msg": "Incomplete\x00 transaction listing",
                    "account_id": "a1",
                }
            ],
            "connections": [],
            "accounts": [],
        }
        normalized = simplefin._normalize_payload(payload)
        self.assertEqual(normalized["errors"][0]["code"], "act.missingdata")
        self.assertNotIn("\x00", normalized["errors"][0]["msg"])

    def test_claim_403_message_warns_about_possible_compromise(self):
        error = HTTPError(
            url="https://bridge.simplefin.org/simplefin/claim/test",
            code=403,
            msg="Forbidden",
            hdrs=None,
            fp=None,
        )
        with mock.patch.object(simplefin, "_urlopen", side_effect=error):
            token = base64.b64encode(
                b"https://bridge.simplefin.org/simplefin/claim/test"
            ).decode()
            with self.assertRaisesRegex(simplefin.SimpleFINError, "may already have been claimed"):
                simplefin.claim_setup_token(token, timeout=1)


if __name__ == "__main__":
    unittest.main()
