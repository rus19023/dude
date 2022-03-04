import json
from typing import Any, Dict, List
from unittest import mock

import httpx
import pytest
import yaml

from dude import Scraper, storage
from dude.storage import save_csv, save_json, save_yaml


def test_full_flow(
    scraper_application: Scraper,
    playwright_select: None,
    playwright_setup: None,
    playwright_navigate: None,
    expected_data: List[Dict],
    test_url: str,
) -> None:
    assert scraper_application.has_async is False
    assert len(scraper_application.rules) == 5
    mock_save = mock.MagicMock()
    scraper_application.save(format="custom")(mock_save)
    scraper_application.run(urls=[test_url], pages=2, format="custom", parser="playwright")
    mock_save.assert_called_with(expected_data, None)


def test_full_flow_bs4(
    scraper_application: Scraper,
    bs4_select: None,
    expected_data: List[Dict],
    test_url: str,
) -> None:
    assert scraper_application.has_async is False
    assert len(scraper_application.rules) == 3
    mock_save = mock.MagicMock()
    scraper_application.save(format="custom")(mock_save)
    scraper_application.run(urls=[test_url], pages=2, format="custom", parser="bs4")
    mock_save.assert_called_with(expected_data, None)


@mock.patch.object(httpx, "Client")
def test_full_flow_bs4_httpx(
    mock_client: mock.MagicMock,
    scraper_application: Scraper,
    bs4_select: None,
    expected_data: List[Dict],
    test_url: str,
) -> None:
    assert scraper_application.has_async is False
    assert len(scraper_application.rules) == 3
    mock_save = mock.MagicMock()

    with open(test_url[7:]) as f:
        mock_client.return_value.__enter__.return_value.get.return_value.text = f.read()

    test_url = "https://dude.ron.sh"
    expected_data = [{**d, "_page_url": test_url} for d in expected_data]

    scraper_application.save(format="custom")(mock_save)
    scraper_application.run(urls=[test_url], pages=2, format="custom", parser="bs4")
    mock_save.assert_called_with(expected_data, None)


@mock.patch.object(httpx, "Client")
def test_bs4_httpx_exception(
    mock_client: mock.MagicMock,
    scraper_application: Scraper,
    bs4_select: None,
    expected_data: List[Dict],
) -> None:
    assert scraper_application.has_async is False
    assert len(scraper_application.rules) == 3
    mock_save = mock.MagicMock()

    response = mock_client.return_value.__enter__.return_value.get.return_value
    response.raise_for_status.side_effect = httpx.HTTPStatusError(
        message="Mock exception",
        request=mock.MagicMock(),
        response=mock.MagicMock(),
    )

    test_url = "https://dude.ron.sh"

    scraper_application.save(format="custom")(mock_save)
    scraper_application.run(urls=[test_url], pages=2, format="custom", parser="bs4")
    mock_save.assert_called_with([], None)


def test_custom_save(
    scraper_application: Scraper, playwright_select: None, expected_data: List[Dict], test_url: str
) -> None:
    assert scraper_application.has_async is False
    assert len(scraper_application.rules) == 3
    mock_save = mock.MagicMock()
    mock_save.return_value = True
    scraper_application.save(format="custom")(mock_save)
    scraper_application.run(urls=[test_url], pages=2, format="custom", parser="playwright")
    mock_save.assert_called_with(expected_data, None)


def test_scraper_with_parser(
    scraper_application_with_parser: Scraper,
    playwright_select_with_parser: None,
    expected_data: List[Dict],
    test_url: str,
) -> None:
    assert scraper_application_with_parser.has_async is False
    assert scraper_application_with_parser.scraper is not None
    assert len(scraper_application_with_parser.scraper.rules) == 3
    mock_save = mock.MagicMock()
    mock_save.return_value = True
    scraper_application_with_parser.save(format="custom")(mock_save)
    scraper_application_with_parser.run(urls=[test_url], pages=2, format="custom", parser="playwright")
    mock_save.assert_called_with(expected_data, None)


def test_format_not_supported(scraper_application: Scraper, playwright_select: None, test_url: str) -> None:
    assert scraper_application.has_async is False
    assert len(scraper_application.rules) == 3
    with pytest.raises(KeyError):
        scraper_application.run(urls=[test_url], pages=2, format="custom", parser="playwright")


def test_failed_to_save(
    scraper_application: Scraper, playwright_select: None, expected_data: List[Dict], test_url: str
) -> None:
    assert scraper_application.has_async is False
    assert len(scraper_application.rules) == 3
    mock_save = mock.MagicMock()
    mock_save.return_value = False
    scraper_application.save(format="fail_db")(mock_save)
    with pytest.raises(Exception):
        scraper_application.run(urls=[test_url], pages=2, output="failing.fail_db", parser="playwright")


@mock.patch.object(json, "dump")
def test_save_json(
    mock_dump: mock.MagicMock,
    scraper_application: Scraper,
    playwright_select: None,
    expected_data: List[Dict],
    test_url: str,
) -> None:
    assert scraper_application.has_async is False
    assert len(scraper_application.rules) == 3
    scraper_application.save(format="json")(save_json)
    scraper_application.run(urls=[test_url], format="json")
    mock_dump.assert_called()


@mock.patch.object(json, "dump")
def test_save_csv(
    mock_dump: mock.MagicMock,
    scraper_application: Scraper,
    playwright_select: None,
    expected_data: List[Dict],
    test_url: str,
) -> None:
    assert scraper_application.has_async is False
    assert len(scraper_application.rules) == 3
    scraper_application.save(format="csv")(save_csv)
    scraper_application.run(urls=[test_url], format="csv")
    mock_dump.assert_called()


@mock.patch.object(yaml, "safe_dump")
def test_save_yaml(
    mock_safe_dump: mock.MagicMock,
    scraper_application: Scraper,
    playwright_select: None,
    expected_data: List[Dict],
    test_url: str,
) -> None:
    assert scraper_application.has_async is False
    assert len(scraper_application.rules) == 3
    scraper_application.save(format="yaml")(save_yaml)
    scraper_application.run(urls=[test_url], format="yaml")
    mock_safe_dump.assert_called()


@mock.patch.object(storage, "_save_json")
def test_save_json_file(
    mock_save: mock.MagicMock,
    scraper_application: Scraper,
    playwright_select: None,
    expected_data: List[Dict],
    test_url: str,
) -> None:
    assert scraper_application.has_async is False
    assert len(scraper_application.rules) == 3
    scraper_application.run(urls=[test_url], output="output.json")
    mock_save.assert_called_with(expected_data, "output.json")


@mock.patch.object(storage, "_save_csv")
def test_save_csv_file(
    mock_save: mock.MagicMock,
    scraper_application: Scraper,
    playwright_select: None,
    expected_data: List[Dict],
    test_url: str,
) -> None:
    assert scraper_application.has_async is False
    assert len(scraper_application.rules) == 3
    scraper_application.save(format="csv")(save_csv)
    scraper_application.run(urls=[test_url], output="output.csv")
    mock_save.assert_called_with(expected_data, "output.csv")


@mock.patch.object(storage, "_save_yaml")
def test_save_yaml_file(
    mock_save: mock.MagicMock,
    scraper_application: Scraper,
    playwright_select: None,
    expected_data: List[Dict],
    test_url: str,
) -> None:
    assert scraper_application.has_async is False
    assert len(scraper_application.rules) == 3
    scraper_application.save(format="yaml")(save_yaml)
    scraper_application.run(urls=[test_url], output="output.yaml")
    mock_save.assert_called_with(expected_data, "output.yaml")


def test_playwright_invalid_group(scraper_application: Scraper) -> None:
    assert scraper_application.has_async is False
    assert len(scraper_application.rules) == 0
    with pytest.raises(Exception):

        @scraper_application.group()
        @scraper_application.select(selector=".title")
        def title(element: Any) -> Dict:
            return {}