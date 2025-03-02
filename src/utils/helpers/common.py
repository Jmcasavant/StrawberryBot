"""
Common helper functions for StrawberryBot.

This module provides utility functions for:
- Text formatting
- Time handling
- Discord-specific helpers
- Data validation
- Error handling
"""

import re
import random
from typing import Optional, Union, List, Dict, Any
from datetime import datetime, timedelta
import discord
from discord.ext import commands

def format_number(num: Union[int, float]) -> str:
    """
    Format a number with commas and optional decimal places.
    
    Args:
        num: Number to format
        
    Returns:
        Formatted string
    """
    if isinstance(num, int):
        return f"{num:,}"
    return f"{num:,.2f}"

def format_duration(seconds: Union[int, float]) -> str:
    """
    Format seconds into human-readable duration.
    
    Args:
        seconds: Number of seconds
        
    Returns:
        Formatted duration string
    """
    intervals = [
        ('year', 31536000),
        ('month', 2592000),
        ('week', 604800),
        ('day', 86400),
        ('hour', 3600),
        ('minute', 60),
        ('second', 1)
    ]
    
    parts = []
    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                parts.append(f"{value} {name}")
            else:
                parts.append(f"{value} {name}s")
    return ', '.join(parts[:2]) if parts else "0 seconds"

def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length.
    
    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: String to append if truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def sanitize_text(text: str) -> str:
    """
    Remove unwanted characters and normalize text.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text
    """
    # Remove Discord markdown
    text = re.sub(r'[*_~`|]', '', text)
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Remove control characters
    text = ''.join(char for char in text if ord(char) >= 32)
    
    return text

def parse_duration(duration_str: str) -> Optional[timedelta]:
    """
    Parse a duration string into a timedelta.
    
    Args:
        duration_str: Duration string (e.g., "1h30m", "2d", "5w")
        
    Returns:
        Timedelta or None if invalid
    """
    pattern = re.compile(r'(\d+)([wdhms])')
    matches = pattern.findall(duration_str.lower())
    
    if not matches:
        return None
    
    total_seconds = 0
    for amount, unit in matches:
        amount = int(amount)
        if unit == 'w':
            total_seconds += amount * 7 * 24 * 3600
        elif unit == 'd':
            total_seconds += amount * 24 * 3600
        elif unit == 'h':
            total_seconds += amount * 3600
        elif unit == 'm':
            total_seconds += amount * 60
        elif unit == 's':
            total_seconds += amount
    
    return timedelta(seconds=total_seconds)

def format_relative_time(dt: datetime) -> str:
    """
    Format a datetime as a relative time string.
    
    Args:
        dt: Datetime to format
        
    Returns:
        Relative time string
    """
    now = datetime.utcnow()
    diff = now - dt
    
    if diff < timedelta(minutes=1):
        return "just now"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes}m ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours}h ago"
    elif diff < timedelta(days=7):
        days = diff.days
        return f"{days}d ago"
    elif diff < timedelta(days=30):
        weeks = int(diff.days / 7)
        return f"{weeks}w ago"
    else:
        return dt.strftime("%Y-%m-%d")

def get_random_color() -> discord.Color:
    """
    Get a random Discord color.
    
    Returns:
        Random Discord color
    """
    return discord.Color.from_rgb(
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255)
    )

def chunk_text(text: str, chunk_size: int = 1900) -> List[str]:
    """
    Split text into chunks that fit in Discord messages.
    
    Args:
        text: Text to split
        chunk_size: Maximum chunk size
        
    Returns:
        List of text chunks
    """
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

def format_dict(data: Dict[str, Any], indent: int = 0) -> str:
    """
    Format a dictionary as a readable string.
    
    Args:
        data: Dictionary to format
        indent: Indentation level
        
    Returns:
        Formatted string
    """
    lines = []
    prefix = " " * indent
    
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(format_dict(value, indent + 2))
        else:
            lines.append(f"{prefix}{key}: {value}")
    
    return "\n".join(lines)

def is_url(text: str) -> bool:
    """
    Check if text is a valid URL.
    
    Args:
        text: Text to check
        
    Returns:
        True if text is a URL
    """
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return bool(url_pattern.match(text))

def parse_bool(value: Union[str, bool]) -> bool:
    """
    Parse a string into a boolean value.
    
    Args:
        value: String or boolean to parse
        
    Returns:
        Boolean value
    """
    if isinstance(value, bool):
        return value
    
    return value.lower() in ('yes', 'true', '1', 'on', 'y', 't') 