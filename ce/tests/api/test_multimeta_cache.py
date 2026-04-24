import json
from datetime import datetime, UTC

import ce.api
from werkzeug.wrappers import Response


def test_multimeta_get_uses_cached_response(
    test_client, app, populateddb_session, monkeypatch, tmp_path
):
    cache_dir = tmp_path / "multimeta-cache"
    app.config["MULTIMETA_CACHE_DIR"] = str(cache_dir)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("multimeta should not be called when cache exists")

    monkeypatch.setattr(ce.api, "multimeta", fail_if_called)
    monkeypatch.setitem(ce.api.methods, "multimeta", fail_if_called)

    cached_response = Response('{"cached": true}', content_type="application/json")
    cached_response.last_modified = datetime(2026, 4, 23, tzinfo=UTC)

    def return_cached_response(params):
        return cached_response

    monkeypatch.setattr(ce.api, "get_cached_multimeta_response", return_cached_response)

    response = test_client.get(
        "/api/multimeta",
        query_string={"ensemble_name": "ce_files", "extras": "filepath"},
    )

    assert response.status_code == 200
    assert response.get_json() == {"cached": True}
    assert response.last_modified is not None


def test_preload_multimeta_cache_warms_cache_on_boot(monkeypatch, tmp_path):
    cache_dir = tmp_path / "multimeta-cache"
    app = __import__("ce").get_app(
        {
            "MULTIMETA_CACHE_DIR": str(cache_dir),
            "PRELOAD_MULTIMETA_CACHE": False,
            "TESTING": True,
        }
    )

    def cacheable_multimeta(*args, **kwargs):
        return {
            "cached-id": {
                "institution": "PCIC",
                "model_id": "demo",
                "model_name": "",
                "experiment": "historical",
                "ensemble_member": "r1i1p1",
                "timescale": "monthly",
                "multi_year_mean": True,
                "start_date": datetime(2026, 1, 1, tzinfo=UTC),
                "end_date": datetime(2026, 12, 31, tzinfo=UTC),
                "modtime": datetime(2026, 4, 23, tzinfo=UTC),
                "variables": {"tasmax": "Daily Maximum Temperature"},
                "units": {"tasmax": "degC"},
            }
        }

    monkeypatch.setattr(ce.api, "multimeta", cacheable_multimeta)
    monkeypatch.setitem(ce.api.methods, "multimeta", cacheable_multimeta)

    app.config["TESTING"] = False
    app.config["PRELOAD_MULTIMETA_CACHE"] = True
    app.config["MULTIMETA_PRELOAD_PARAMS"] = [
        {"ensemble_name": "ce_files", "extras": "filepath"}
    ]

    from ce.api.multimeta_cache import preload_multimeta_cache

    preload_multimeta_cache(app)

    assert list(cache_dir.iterdir())


def test_multimeta_get_populates_cache(test_client, app, populateddb_session, tmp_path):
    cache_dir = tmp_path / "multimeta-cache"
    app.config["MULTIMETA_CACHE_DIR"] = str(cache_dir)

    response = test_client.get(
        "/api/multimeta",
        query_string={
            "ensemble_name": "ce",
            "extras": "filepath",
            "climatological_statistic": "standard_deviation",
        },
    )

    assert response.status_code == 200
    cache_files = list(cache_dir.iterdir())
    assert len(cache_files) == 1

    cached = json.loads(cache_files[0].read_text())
    assert json.loads(cached["body"]) == response.get_json()
    assert cached["last_modified"] is not None


def test_multimeta_post_does_not_use_cache(
    test_client, app, populateddb_session, monkeypatch, tmp_path
):
    cache_dir = tmp_path / "multimeta-cache"
    app.config["MULTIMETA_CACHE_DIR"] = str(cache_dir)

    calls = {"count": 0}
    original = ce.api.multimeta

    def wrapped(*args, **kwargs):
        calls["count"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(ce.api, "multimeta", wrapped)
    monkeypatch.setitem(ce.api.methods, "multimeta", wrapped)

    response = test_client.post(
        "/api/multimeta",
        data={
            "ensemble_name": "ce",
            "extras": "filepath",
            "climatological_statistic": "standard_deviation",
        },
    )

    assert response.status_code == 200
    assert calls["count"] == 1
    assert not cache_dir.exists()
