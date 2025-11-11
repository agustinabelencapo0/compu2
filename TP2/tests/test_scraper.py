from scraper.html_parser import parse_basic_structure
from scraper.metadata_extractor import extract_meta_tags


def test_parse_basic_structure_minimal():
    html = """
    <html><head><title>Hola</title></head>
    <body>
      <h1>Header</h1>
      <a href="/contact">link</a>
      <img src="x.png" />
    </body></html>
    """
    data = parse_basic_structure(html, base_url="https://example.com")
    assert data["title"] == "Hola"
    assert data["structure"]["h1"] == 1
    assert data["images_count"] == 1
    assert data["links"] == ["https://example.com/contact"]
    assert data["image_urls"] == ["https://example.com/x.png"]


def test_extract_meta_tags():
    html = """
    <html><head>
      <meta name="description" content="desc" />
      <meta name="keywords" content="k1,k2" />
      <meta property="og:title" content="ogt" />
    </head></html>
    """
    meta = extract_meta_tags(html)
    assert meta["description"] == "desc"
    assert meta["keywords"] == "k1,k2"
    assert meta["og:title"] == "ogt"

