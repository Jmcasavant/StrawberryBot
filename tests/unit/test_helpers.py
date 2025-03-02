"""
Unit tests for helper functions.

Tests the functionality of common helper functions in:
- Text formatting
- Time handling
- Data validation
- URL checking
"""

import pytest
from datetime import datetime, timedelta
import discord
from src.utils.helpers.common import (
    format_number,
    format_duration,
    truncate_string,
    sanitize_text,
    parse_duration,
    format_relative_time,
    get_random_color,
    chunk_text,
    format_dict,
    is_url,
    parse_bool
)

class TestFormatNumber:
    """Tests for format_number function."""
    
    @pytest.mark.parametrize("number,expected", [
        (1000, "1,000"),
        (1000000, "1,000,000"),
        (1234.5678, "1,234.57"),
        (0.1, "0.10"),
        (-1234.56, "-1,234.56"),
    ])
    def test_format_number(self, number, expected):
        """Test number formatting with various inputs."""
        assert format_number(number) == expected

class TestFormatDuration:
    """Tests for format_duration function."""
    
    @pytest.mark.parametrize("seconds,expected", [
        (30, "30 seconds"),
        (60, "1 minute"),
        (3600, "1 hour"),
        (3661, "1 hour, 1 minute"),
        (86400, "1 day"),
        (90000, "1 day, 1 hour"),
    ])
    def test_format_duration(self, seconds, expected):
        """Test duration formatting with various inputs."""
        assert format_duration(seconds) == expected

class TestTruncateString:
    """Tests for truncate_string function."""
    
    @pytest.mark.parametrize("text,max_length,suffix,expected", [
        ("Hello World", 5, "...", "He..."),
        ("Hello", 10, "...", "Hello"),
        ("Very Long Text", 8, "...", "Very..."),
        ("Test", 4, "...", "Test"),
    ])
    def test_truncate_string(self, text, max_length, suffix, expected):
        """Test string truncation with various inputs."""
        assert truncate_string(text, max_length, suffix) == expected

class TestSanitizeText:
    """Tests for sanitize_text function."""
    
    @pytest.mark.parametrize("text,expected", [
        ("**bold**", "bold"),
        ("__underline__", "underline"),
        ("~~strikethrough~~", "strikethrough"),
        ("multiple  spaces", "multiple spaces"),
        ("*mixed* _formatting_", "mixed formatting"),
    ])
    def test_sanitize_text(self, text, expected):
        """Test text sanitization with various inputs."""
        assert sanitize_text(text) == expected

class TestParseDuration:
    """Tests for parse_duration function."""
    
    @pytest.mark.parametrize("duration_str,expected_seconds", [
        ("1h", 3600),
        ("30m", 1800),
        ("1d", 86400),
        ("1w", 604800),
        ("1h30m", 5400),
        ("invalid", None),
    ])
    def test_parse_duration(self, duration_str, expected_seconds):
        """Test duration parsing with various inputs."""
        result = parse_duration(duration_str)
        if expected_seconds is None:
            assert result is None
        else:
            assert result == timedelta(seconds=expected_seconds)

class TestFormatRelativeTime:
    """Tests for format_relative_time function."""
    
    def test_just_now(self):
        """Test formatting of very recent times."""
        now = datetime.utcnow()
        assert format_relative_time(now) == "just now"
    
    def test_minutes_ago(self):
        """Test formatting of times minutes ago."""
        time = datetime.utcnow() - timedelta(minutes=5)
        assert format_relative_time(time) == "5m ago"
    
    def test_hours_ago(self):
        """Test formatting of times hours ago."""
        time = datetime.utcnow() - timedelta(hours=2)
        assert format_relative_time(time) == "2h ago"
    
    def test_days_ago(self):
        """Test formatting of times days ago."""
        time = datetime.utcnow() - timedelta(days=3)
        assert format_relative_time(time) == "3d ago"

class TestGetRandomColor:
    """Tests for get_random_color function."""
    
    def test_returns_discord_color(self):
        """Test that function returns a Discord Color object."""
        color = get_random_color()
        assert isinstance(color, discord.Color)
    
    def test_random_values(self):
        """Test that multiple calls return different colors."""
        colors = [get_random_color() for _ in range(10)]
        # Check that at least some colors are different
        assert len(set(color.value for color in colors)) > 1

class TestChunkText:
    """Tests for chunk_text function."""
    
    @pytest.mark.parametrize("text,chunk_size,expected_chunks", [
        ("12345", 2, ["12", "34", "5"]),
        ("Hello World", 5, ["Hello", " Worl", "d"]),
        ("Short", 10, ["Short"]),
    ])
    def test_chunk_text(self, text, chunk_size, expected_chunks):
        """Test text chunking with various inputs."""
        assert chunk_text(text, chunk_size) == expected_chunks

class TestFormatDict:
    """Tests for format_dict function."""
    
    def test_simple_dict(self):
        """Test formatting of simple dictionary."""
        data = {"key1": "value1", "key2": "value2"}
        expected = "key1: value1\nkey2: value2"
        assert format_dict(data) == expected
    
    def test_nested_dict(self):
        """Test formatting of nested dictionary."""
        data = {"outer": {"inner": "value"}}
        expected = "outer:\n  inner: value"
        assert format_dict(data) == expected

class TestIsUrl:
    """Tests for is_url function."""
    
    @pytest.mark.parametrize("url,expected", [
        ("https://example.com", True),
        ("http://localhost:8080", True),
        ("not a url", False),
        ("ftp://invalid", False),
    ])
    def test_is_url(self, url, expected):
        """Test URL validation with various inputs."""
        assert is_url(url) == expected

class TestParseBool:
    """Tests for parse_bool function."""
    
    @pytest.mark.parametrize("value,expected", [
        ("yes", True),
        ("no", False),
        ("true", True),
        ("false", False),
        ("1", True),
        ("0", False),
        (True, True),
        (False, False),
    ])
    def test_parse_bool(self, value, expected):
        """Test boolean parsing with various inputs."""
        assert parse_bool(value) == expected 