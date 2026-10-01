#!/usr/bin/env python3
"""Offline self-test for step93: stubs the network and exercises
sitemap parsing -> model-page parsing -> catalog merge."""
import os
import tempfile

import sevenzap_lib as lib
import step93_fetch_7zap_all_regions as s93

SITEMAP = """<?xml version="1.0"?><sitemapindex>
<sitemap><loc>https://7zap.com/sitemaps/cats/7zap_com/bmw/generation_1-series-f20.xml</loc></sitemap>
<sitemap><loc>https://7zap.com/sitemaps/cats/7zap_com/bmw/generation_5-series-g60.xml</loc></sitemap>
<sitemap><loc>https://7zap.com/sitemaps/cats/7zap_com/opel/generation_astra-k.xml</loc></sitemap>
<sitemap><loc>https://7zap.com/sitemaps/cats/7zap_com/bmw/landings.xml</loc></sitemap>
</sitemapindex>"""

PAGES = {
    "https://7zap.com/en/catalog/cars/bmw/1-series-f20-parts-catalog/":
        "<title>BMW 1' F20 (2011 - 2015) OEM Parts Catalogue | 7zap</title>"
        '<img src="https://img.7zap.com/images/oem/models/BMW_1-series_F20.webp">'
        '<img src="/images/common/region.png">Europe',
    "https://7zap.com/en/catalog/cars/bmw/5-series-g60-parts-catalog/":
        '<meta property="og:title" content="BMW 5\' G60 (2023 - ...)">'
        '<meta property="og:image" content="https://img.7zap.com/images/oem/models/BMW_5-Series_G60.webp">',
    "https://7zap.com/en/catalog/cars/opel/astra-k-parts-catalog/":
        "<title>Opel Astra K 2015 - 2021 Parts Catalogue | 7zap</title>"
        '<img src="https://img.7zap.com/images/oem/models/Opel_Astra_K.webp">',
}


def fake_get(session, url, retries=3, pause=1.0):
    if url == s93.SITEMAP_INDEX:
        return SITEMAP
    return PAGES.get(url)


def main() -> None:
    s93.get = fake_get
    s93.make_session = lambda: None

    pairs = s93.list_generations(None, None)
    assert pairs == [("bmw", "1-series-f20"), ("bmw", "5-series-g60"), ("opel", "astra-k")], pairs
    assert s93.list_generations(None, {"opel"}) == [("opel", "astra-k")]

    tmp = os.path.join(tempfile.mkdtemp(), "catalog.jsonl")
    found = s93.crawl(pairs, workers=2, delay=0, out_path=tmp)
    assert found == 3, found
    rows = {r.model_name: r for r in lib.load_catalog(tmp)}
    assert set(rows) == {"1' F20", "5' G60", "Astra K"}, set(rows)
    f20 = rows["1' F20"]
    assert (f20.year_from, f20.year_to) == (2011, 2015)
    assert f20.brand_label == "BMW" and f20.source == "7zap:europe"
    assert f20.image_url.endswith("BMW_1-series_F20.webp")
    assert f20.page_url.endswith("/bmw/1-series-f20-parts-catalog/")
    g60 = rows["5' G60"]
    assert (g60.year_from, g60.year_to) == (2023, None), (g60.year_from, g60.year_to)
    astra = rows["Astra K"]
    assert (astra.year_from, astra.year_to) == (2015, 2021)

    # merge is idempotent
    s93.crawl(pairs, workers=1, delay=0, out_path=tmp)
    assert len(lib.load_catalog(tmp)) == 3
    print("step93 self-test OK (3 generations parsed, merge idempotent)")


if __name__ == "__main__":
    main()
