import pytest

from main import ping


def test_always_passes():
    return True


def test_ping():
    res = ping()
    assert res["status"] == "ok"
    assert "message" in res
