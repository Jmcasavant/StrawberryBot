"""
Database models for StrawberryBot.

This module defines the SQLAlchemy ORM models for:
- Users and their economy data
- Server configurations
- Game statistics
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    ForeignKey, BigInteger, Float, Text, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    """
    Represents a Discord user in the bot's economy system.
    Tracks user's strawberries, statistics, and other relevant data.
    """
    __tablename__ = "users"
    
    # Primary Key - Discord User ID
    id = Column(BigInteger, primary_key=True)
    
    # User Data
    name = Column(String(32), nullable=False)
    discriminator = Column(String(4))
    
    # Economy Data
    strawberries = Column(Integer, default=0)
    lifetime_strawberries = Column(Integer, default=0)
    last_daily = Column(DateTime, nullable=True)
    
    # Statistics
    games_played = Column(Integer, default=0)
    games_won = Column(Integer, default=0)
    total_bets = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    game_stats = relationship("GameStats", back_populates="user")

class GameStats(Base):
    """
    Detailed statistics for each game type.
    Tracks wins, losses, and other relevant metrics per game.
    """
    __tablename__ = "game_stats"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    game_type = Column(String(32), nullable=False)
    
    # Game Statistics
    games_played = Column(Integer, default=0)
    games_won = Column(Integer, default=0)
    total_bets = Column(Integer, default=0)
    highest_win = Column(Integer, default=0)
    biggest_loss = Column(Integer, default=0)
    
    # Timestamps
    last_played = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="game_stats")

class ServerConfig(Base):
    """
    Server-specific configurations and settings.
    Stores customizable options for each Discord server.
    """
    __tablename__ = "server_configs"
    
    # Primary Key - Discord Server ID
    id = Column(BigInteger, primary_key=True)
    
    # Basic Settings
    name = Column(String(100), nullable=False)
    prefix = Column(String(10), default="!")
    
    # Feature Toggles
    economy_enabled = Column(Boolean, default=True)
    games_enabled = Column(Boolean, default=True)
    voice_enabled = Column(Boolean, default=True)
    
    # Custom Settings
    welcome_channel_id = Column(BigInteger, nullable=True)
    admin_role_id = Column(BigInteger, nullable=True)
    custom_settings = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class AuditLog(Base):
    """
    Audit log for tracking important bot actions and changes.
    Helps with debugging and monitoring bot usage.
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=func.now())
    
    # Action Information
    action_type = Column(String(50), nullable=False)
    user_id = Column(BigInteger, nullable=True)
    server_id = Column(BigInteger, nullable=True)
    
    # Details
    details = Column(Text, nullable=True)
    metadata = Column(JSON, default=dict) 