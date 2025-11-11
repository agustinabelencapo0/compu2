import io

from PIL import Image

from processor.advanced import (
    analyze_accessibility,
    detect_technologies,
    evaluate_seo,
    extract_structured_data,
)
from processor.performance import analyze_performance
from processor.image_processor import generate_thumbnails


def test_analyze_performance_example():
    # Solo valida que devuelve el shape correcto; puede fallar sin red
    res = analyze_performance("https://example.com")
    assert set(res.keys()) == {"load_time_ms", "total_size_kb", "num_requests"}


def test_detect_technologies_identifies_react():
    html = """
    <html>
      <head>
        <script src="https://cdn.example.com/react.js"></script>
      </head>
      <body data-reactroot="">
        <div id="root"></div>
      </body>
    </html>
    """
    tech = detect_technologies(html)
    assert "React" in tech


def test_evaluate_seo_scores_basic_elements():
    html = """
    <html>
      <head>
        <title>Example title for SEO</title>
        <meta name="description" content="Descripción de prueba para SEO con longitud adecuada" />
        <link rel="canonical" href="https://example.com" />
        <meta property="og:title" content="Open Graph Title" />
      </head>
      <body><h1>Hola</h1></body>
    </html>
    """
    seo = evaluate_seo(html)
    assert seo["score"] > 0
    assert seo["h1_count"] == 1


def test_extract_structured_data_returns_entries():
    html = """
    <html>
      <head>
        <script type="application/ld+json">
        {"@context": "https://schema.org", "@type": "Person", "name": "Ada"}
        </script>
      </head>
    </html>
    """
    data = extract_structured_data(html)
    assert isinstance(data, list)
    assert data and data[0]["@type"] == "Person"


def test_analyze_accessibility_detects_missing_alt():
    html = """
    <html>
      <body>
        <img src="img.png" />
        <a href="/empty"></a>
        <button></button>
        <div style="color:#fff;background-color:#fff">Texto</div>
      </body>
    </html>
    """
    report = analyze_accessibility(html)
    assert "img.png" in report["images_missing_alt"]
    assert "/empty" in report["links_without_text"]
    assert report["buttons_without_text"]
    assert report["contrast_warnings"]


def test_generate_thumbnails_resizes(monkeypatch):
    def fake_download(url: str, timeout: int = 20) -> bytes:
        img = Image.new("RGB", (400, 200), color=(255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    monkeypatch.setattr("processor.image_processor._download_bytes", fake_download)
    thumbs = generate_thumbnails(["https://example.com/image.png"], size=100, max_images=1)
    assert len(thumbs) == 1
    thumb_img = Image.open(io.BytesIO(thumbs[0]))
    assert max(thumb_img.size) <= 100

