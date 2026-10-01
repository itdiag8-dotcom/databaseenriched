#!/usr/bin/env python3
"""Offline self-test for step94: stubs WDQS + the Commons API and exercises
SPARQL-result parsing, brand-prefix stripping, attribution lookup and the
catalog merge. Mirrors real payloads captured from query.wikidata.org."""
import os
import tempfile

import sevenzap_lib as lib
import step94_fetch_wikidata_images as s94

SPARQL_JSON = {
    "head": {"vars": ["m", "mLabel", "img", "y1", "y2"]},
    "results": {"bindings": [
        {"m": {"value": "http://www.wikidata.org/entity/Q463627"},
         "mLabel": {"value": "Ferrari F40"},
         "img": {"value": "http://commons.wikimedia.org/wiki/Special:FilePath/Ferrari%20F40%207.jpg"},
         "y1": {"value": "1987"}, "y2": {"value": "1992"}},
        {"m": {"value": "http://www.wikidata.org/entity/Q117235"},
         "mLabel": {"value": "Ferrari 360"},
         "img": {"value": "http://commons.wikimedia.org/wiki/Special:FilePath/Ferrari360.JPG"},
         "y1": {"value": "1999"}},
        # duplicate entity (several P571 statements) - must collapse
        {"m": {"value": "http://www.wikidata.org/entity/Q117235"},
         "mLabel": {"value": "Ferrari 360"},
         "img": {"value": "http://commons.wikimedia.org/wiki/Special:FilePath/Ferrari360.JPG"}},
        # unlabelled entity - must be dropped
        {"m": {"value": "http://www.wikidata.org/entity/Q99999999"},
         "mLabel": {"value": "Q99999999"},
         "img": {"value": "http://commons.wikimedia.org/wiki/Special:FilePath/x.jpg"}},
        # no picture - must be dropped
        {"m": {"value": "http://www.wikidata.org/entity/Q1"}, "mLabel": {"value": "Ferrari 250"}},
    ]},
}

COMMONS_JSON = {"query": {"pages": {
    "1": {"title": "File:Ferrari F40 7.jpg", "imageinfo": [{"extmetadata": {
        "Artist": {"value": '<a href="//commons.wikimedia.org/wiki/User:X">Jane&nbsp;Doe</a>'},
        "LicenseShortName": {"value": "CC BY-SA 4.0"}}}]},
    "2": {"title": "File:Ferrari360.JPG", "imageinfo": [{"extmetadata": {
        "Artist": {"value": "John Doe"}, "LicenseShortName": {"value": "CC BY 2.0"}}}]},
}}}


class FakeResponse:
    def __init__(self, payload):
        self.status_code = 200
        self.headers = {}
        self._payload = payload

    def json(self):
        return self._payload


class FakeSession:
    """Answers WDQS with SPARQL_JSON and the Commons API with COMMONS_JSON."""

    def __init__(self):
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params))
        if url == s94.SPARQL_ENDPOINT:
            assert '"Ferrari"@en' in params["query"], params["query"]
            return FakeResponse(SPARQL_JSON)
        if url == s94.COMMONS_API:
            titles = params["titles"].split("|")
            assert "File:Ferrari F40 7.jpg" in titles, titles
            return FakeResponse(COMMONS_JSON)
        raise AssertionError(url)


def main() -> None:
    session = FakeSession()

    payload = s94.sparql(session, s94.MODELS_QUERY % {"label": s94.literal("Ferrari")})
    rows = s94.parse_models(payload, "Ferrari")
    assert len(rows) == 2, [r.model_name for r in rows]

    by_name = {r.model_name: r for r in rows}
    assert set(by_name) == {"F40", "360"}, set(by_name)  # brand prefix stripped
    f40 = by_name["F40"]
    assert (f40.year_from, f40.year_to) == (1987, 1992)
    assert f40.years_text == "(1987 - 1992)"
    assert f40.brand_slug == "ferrari" and f40.source == "wikidata"
    assert f40.image_url.startswith("https://commons.wikimedia.org/") and f40.image_url.endswith("?width=1024")
    assert f40.page_url == "http://www.wikidata.org/entity/Q463627" and f40.slug == "Q463627"
    assert by_name["360"].year_to is None  # still in production / unknown end

    assert s94.commons_filename(f40.image_url.split("?")[0]) == "Ferrari F40 7.jpg"

    assert s94.fetch_credits(session, rows) == 2
    assert f40.credit == "Jane Doe" and f40.license == "CC BY-SA 4.0", (f40.credit, f40.license)
    assert by_name["360"].credit == "John Doe"

    # alias handling for database spellings Wikidata does not know
    assert s94.ALIASES["Maruti"] == "Maruti Suzuki"
    assert s94.strip_brand("Maruti Suzuki Swift", "Maruti") == "Swift"

    tmp = os.path.join(tempfile.mkdtemp(), "wikidata.jsonl")
    assert lib.save_catalog(rows, tmp, merge=True) == 2
    reloaded = {r.model_name: r for r in lib.load_catalog(tmp)}
    assert reloaded["F40"].license == "CC BY-SA 4.0"  # attribution survives the round-trip
    assert lib.save_catalog(rows, tmp, merge=True) == 2  # idempotent

    print("step94 self-test OK (2 models parsed, credits attached, merge idempotent)")


if __name__ == "__main__":
    main()
