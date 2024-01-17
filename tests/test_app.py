import pytest
import requests
from unittest.mock import Mock, patch

from utils.utils import *

from config.config import Config

cfg = Config.instance()

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


def test_get_pdf_endpoint_with_valid_author_name(client):
    with patch("headless_pdfkit.generate_pdf", return_value=b"mocked_pdf_data"):
        response = client.get("/report.pdf", json={"author_name": "John Doe"})

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/pdf"
    assert response.headers["Content-Disposition"] == "inline; filename=report.pdf"
    assert response.data == b"mocked_pdf_data"

def test_get_pdf_endpoint_with_missing_author_name(client):
    response = client.get("/report.pdf", json={})

    assert response.status_code == 200
    assert response.get_json() == {"error": "No JSON data provided"}


def test_get_pdf_endpoint_with_exception(client):
    with patch("utils.utils.webManager.retrieve_request", side_effect=Exception("Test Exception")):
        response = client.get("/report.pdf", json={"author_name": "John Doe"})

    assert response.status_code == 200
    assert response.get_json() == {"error": "Error: Test Exception"}

def test_generate_author_info_pdf_with_invalid_data(client):
    response = client.post("/generate-pdf", json={"invalid_key": "John Doe"})

    assert response.status_code == 404

if __name__ == "__main__":
    pytest.main()