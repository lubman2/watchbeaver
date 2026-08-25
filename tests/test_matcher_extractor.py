import pytest
from src.matcher import KeywordMatcher
from src.extractors.pdf_extractor import PDFExtractor

def test_keyword_matcher_finds_zelenec():
    patterns = [r'(?i)\bzeleneč', r'(?i)\bmstětic\w*', r'792756']
    matcher = KeywordMatcher(patterns)

    # Positive match
    text1 = "Městský úřad Brandýs oznamuje zahájení řízení pro stavbu v k.ú. Zeleneč, pozemek č. 123/4."
    res = matcher.find_match(text1)
    assert res is not None
    kw, snippet = res
    assert "Zeleneč" in kw
    assert "pozemek č. 123/4" in snippet

    # Positive match Mstětice
    text2 = "Rekonstrukce železniční stanice Mstětice a napojení vlečky."
    res2 = matcher.find_match(text2)
    assert res2 is not None
    assert "Mstětice" in res2[0]

    # Positive match parcel code
    text3 = "Vymezení zájmového území katastrální území 792756 - část A."
    res3 = matcher.find_match(text3)
    assert res3 is not None
    assert "792756" in res3[0]

    # Negative match
    text_neg = "Městský úřad oznamuje záměr v k.ú. Brandýs nad Labem."
    assert matcher.find_match(text_neg) is None

def test_pdf_hash_computation():
    data = b"%PDF-1.4 dummy pdf content"
    h = PDFExtractor.compute_hash(data)
    assert len(h) == 64
