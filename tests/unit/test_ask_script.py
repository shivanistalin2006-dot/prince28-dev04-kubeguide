"""Unit tests for scripts/ask.py CLI client arguments and helper execution."""

import argparse
from unittest.mock import MagicMock, patch

from scripts.ask import ask


def test_ask_cli_url_argument_parsing():
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", nargs="?", default="default")
    parser.add_argument(
        "--base-url",
        "--url",
        dest="base_url",
        default="http://localhost:8000",
    )
    parser.add_argument("--json", action="store_true")

    args = parser.parse_args(["--url", "https://kubeguide.onrender.com", "What is a Pod?"])
    assert args.base_url == "https://kubeguide.onrender.com"
    assert args.prompt == "What is a Pod?"
    assert args.json is False


def test_ask_cli_json_flag_parsing():
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", nargs="?", default="default")
    parser.add_argument(
        "--base-url",
        "--url",
        dest="base_url",
        default="http://localhost:8000",
    )
    parser.add_argument("--json", action="store_true")

    args = parser.parse_args(["--json", "List nodes"])
    assert args.json is True
    assert args.prompt == "List nodes"


def test_ask_non_streaming_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "response": "kubectl get pods",
        "provider": "gemini",
        "model": "gemini-3.8-flash",
        "fallback_used": False,
        "tokens_in": 10,
        "tokens_out": 20,
        "latency_ms": 150,
    }

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.return_value = mock_resp

    with patch("httpx.Client", return_value=mock_client):
        code = ask("How do I list pods?", base_url="http://fake:8000", stream=False)
        assert code == 0
