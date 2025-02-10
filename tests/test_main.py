import pytest
from unittest.mock import MagicMock, patch
import logging
from cleaner_onedrive.main import (
    get_access_token,
    get_files_recursive,
    detect_duplicates,
    delete_duplicates,
)


def test_get_access_token(mocker):
    """Test access token retrieval"""
    mock_app = mocker.patch("cleaner_onedrive.main.app")
    mock_app.get_accounts.return_value = [MagicMock()]
    mock_app.acquire_token_silent.return_value = {"access_token": "fake_token"}

    token = get_access_token()
    assert token == "fake_token"
    mock_app.get_accounts.assert_called_once()


class MockResponse:
    """Mock class for simulating API responses"""

    def __init__(self, json_data=None, status_code=200):
        self.json_data = json_data or {}
        self.status_code = status_code
        self.text = "fake response"

    def json(self):
        return self.json_data


def mocked_get_request(*args, **kwargs):
    """Mock GET request for OneDrive files"""
    return MockResponse(
        {
            "value": [
                {
                    "id": "file1",
                    "name": "test.txt",
                    "size": 100,
                    "file": {"hashes": {"quickXorHash": "hash1"}},
                    "webUrl": "https://test.txt",
                },
                {
                    "id": "file2",
                    "name": "photo.jpg",
                    "size": 200,
                    "file": {"hashes": {"quickXorHash": "hash2"}},
                    "webUrl": "https://photo.jpg",
                },
                {
                    "id": "file3",
                    "name": "photo2.jpg",
                    "size": 200,
                    "file": {"hashes": {"quickXorHash": "hash2"}},
                    "webUrl": "https://photo2.jpg",
                },
            ]
        }
    )


def mocked_delete_request(*args, **kwargs):
    """Mock DELETE request (successful deletion)"""
    return MockResponse(status_code=204)


@patch("cleaner_onedrive.main.requests.get", side_effect=mocked_get_request)
@patch("cleaner_onedrive.main.get_access_token", return_value="fake_token")
def test_get_files_recursive(mock_get, mock_token):
    """Test fetching files recursively from OneDrive"""
    files = get_files_recursive("root")

    assert len(files) == 3
    assert files[0]["name"] == "test.txt"
    assert files[1]["name"] == "photo.jpg"
    assert files[2]["name"] == "photo2.jpg"


def test_detect_duplicates():
    """Test duplicate detection logic"""
    files = [
        {
            "id": "file1",
            "name": "test.txt",
            "size": 100,
            "hash": "hash1",
            "webUrl": "https://test.txt",
        },
        {
            "id": "file2",
            "name": "photo1.jpg",
            "size": 200,
            "hash": "hash2",
            "webUrl": "https://photo1.jpg",
        },
        {
            "id": "file3",
            "name": "photo2.jpg",
            "size": 200,
            "hash": "hash2",
            "webUrl": "https://photo2.jpg",
        },
        {
            "id": "file4",
            "name": "photo3.jpg",
            "size": 200,
            "hash": "hash2",
            "webUrl": "https://photo3.jpg",
        },
        {
            "id": "file5",
            "name": "test4.txt",
            "size": 300,
            "hash": "hash3",
            "webUrl": "https://test4.txt",
        },
        {
            "id": "file6",
            "name": "test3.txt",
            "size": 300,
            "hash": "hash3",
            "webUrl": "https://test5.txt",
        },
    ]

    duplicates = detect_duplicates(files)

    assert isinstance(duplicates, dict)
    assert len(duplicates) == 2  # assert two groups of duplicates

    # Verify the keys and values
    key1 = (200, "hash2")
    assert key1 in duplicates
    assert len(duplicates[key1]) == 3  # 3 files are duplicated

    key2 = (300, "hash3")
    assert key2 in duplicates
    assert len(duplicates[key2]) == 2


@patch("cleaner_onedrive.main.requests.delete", side_effect=mocked_delete_request)
@patch("builtins.input", side_effect=["yes", "no", "yes"])  # Delete selected duplicates
@patch("cleaner_onedrive.main.get_access_token", return_value="fake_token")
def test_delete_duplicates(mock_delete, mock_input, mock_token):
    """Test deletion process with user confirmation"""
    with patch("builtins.print") as mock_print:
        duplicates = {
            (200, "hash2"): [
                {"id": "file2", "name": "photo.jpg", "webUrl": "https://photo.jpg"},
                {"id": "file3", "name": "photo2.jpg", "webUrl": "https://photo2.jpg"},
            ],    
            (300, "hash3"): [
                {"id": "file5", "name": "test4.txt", "webUrl": "https://test4.txt"},
                {"id": "file6", "name": "test3.txt", "webUrl": "https://test5.txt"},
                {"id": "file7", "name": "test7.txt", "webUrl": "https://test7.txt"},
            ]
        }

        result = delete_duplicates(duplicates)
        assert len(result) == 2  # Ensure two files were kept
        mock_print.assert_any_call("Deleted: photo2.jpg")
        mock_print.assert_any_call("Deleted: test7.txt")


@patch("cleaner_onedrive.main.requests.delete", side_effect=mocked_delete_request)
@patch("builtins.input", side_effect=["all"])  # Automatic deletion of all duplicates
@patch("cleaner_onedrive.main.get_access_token", return_value="fake_token")
def test_delete_duplicates_all(mock_delete,mock_input, mock_token):
    """Test automatic deletion of all duplicates"""
    with patch("builtins.print") as mock_print:
        duplicates = {
            (200, "hash2"): [
                {"id": "file2", "name": "photo.jpg", "webUrl": "https://photo.jpg"},
                {"id": "file3", "name": "photo2.jpg", "webUrl": "https://photo2.jpg"},
            ]
        }

        result = delete_duplicates(duplicates)
        assert len(result) == 1
        # Verify that deletion was attempted for all duplicates
        assert mock_delete.call_count == 1
        
        # Verify deletion messages
        mock_print.assert_any_call("Deleted: photo2.jpg")
