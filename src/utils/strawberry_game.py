"""Strawberry game management module."""
import json
import datetime
import asyncio
from pathlib import Path
import os
from typing import Dict, Optional, Tuple, List, Set
from collections import defaultdict
from .core import (
    setup_logger,
    STARTING_STRAWBERRIES,
    DAILY_REWARD,
    DAILY_STREAK_BONUS,
    MAX_STREAK_BONUS,
    DATA_DIR
)

logger = setup_logger(__name__)

# File paths
DATA_FILE = DATA_DIR / 'strawberry_data.json'
BACKUP_FILE = DATA_DIR / 'strawberry_data.backup.json'

class StrawberryGame:
    """Manages the strawberry economy game state."""
    
    def __init__(self):
        # Game state
        self.players: Dict[int, int] = defaultdict(lambda: STARTING_STRAWBERRIES)
        self.last_daily: Dict[int, datetime.datetime] = {}
        self.streaks: Dict[int, int] = defaultdict(int)
        
        # Cache management
        self._dirty: bool = False
        self._last_save: datetime.datetime = datetime.datetime.min
        self._save_lock: asyncio.Lock = asyncio.Lock()
        self._cached_leaderboard: Optional[List[Tuple[int, int]]] = None
        self._leaderboard_expires: datetime.datetime = datetime.datetime.min
        self._auto_save_task: Optional[asyncio.Task] = None
        
        # Load initial data
        self.load_data()
        
    async def start(self) -> None:
        """Start the auto-save loop."""
        if self._auto_save_task is None:
            self._auto_save_task = asyncio.create_task(self._auto_save_loop())
            logger.info("Started auto-save loop")
            
    async def stop(self) -> None:
        """Stop the auto-save loop and save any pending changes."""
        if self._auto_save_task is not None:
            self._auto_save_task.cancel()
            try:
                await self._auto_save_task
            except asyncio.CancelledError:
                pass
            self._auto_save_task = None
            
            # Save any pending changes
            await self.save_data_if_dirty()
            logger.info("Stopped auto-save loop")
        
    async def _auto_save_loop(self) -> None:
        """Background task to automatically save data periodically."""
        while True:
            try:
                await asyncio.sleep(300)  # Save every 5 minutes if needed
                await self.save_data_if_dirty()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in auto-save loop: {e}")
                
    async def save_data_if_dirty(self) -> None:
        """Save data only if changes have been made."""
        if not self._dirty:
            return
            
        async with self._save_lock:
            try:
                # Create backup of current file if it exists
                if DATA_FILE.exists():
                    DATA_FILE.rename(BACKUP_FILE)
                
                # Save new data
                data = {
                    'players': self.players,
                    'last_daily': {
                        str(user_id): time.isoformat()
                        for user_id, time in self.last_daily.items()
                    },
                    'streaks': self.streaks
                }
                
                # Write to temporary file first
                temp_file = DATA_FILE.with_suffix('.tmp')
                with open(temp_file, 'w') as f:
                    json.dump(data, f, indent=2)
                    
                # Rename temporary file to actual file
                temp_file.rename(DATA_FILE)
                
                # Remove old backup if save was successful
                if BACKUP_FILE.exists():
                    BACKUP_FILE.unlink()
                    
                self._dirty = False
                self._last_save = datetime.datetime.now()
                logger.info("Game data saved successfully")
                
            except Exception as e:
                logger.error(f"Error saving game data: {e}")
                # Restore backup if save failed
                if BACKUP_FILE.exists():
                    BACKUP_FILE.rename(DATA_FILE)
                    
    def load_data(self) -> None:
        """Load game data from file."""
        if not DATA_FILE.exists():
            return
            
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                
            # Load and validate player data
            for user_id, amount in data.get('players', {}).items():
                if amount >= 0:  # Validate non-negative amounts
                    self.players[int(user_id)] = amount
                    
            # Load and validate daily claims
            now = datetime.datetime.now()
            for user_id, time_str in data.get('last_daily', {}).items():
                try:
                    claim_time = datetime.datetime.fromisoformat(time_str)
                    if claim_time <= now:  # Validate timestamps
                        self.last_daily[int(user_id)] = claim_time
                except ValueError:
                    continue
                    
            # Load and validate streaks
            for user_id, streak in data.get('streaks', {}).items():
                if streak >= 0:  # Validate non-negative streaks
                    self.streaks[int(user_id)] = streak
                    
            logger.info("Game data loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading game data: {e}")
            # Try to load backup if main file is corrupted
            if BACKUP_FILE.exists():
                logger.info("Attempting to load backup file...")
                BACKUP_FILE.rename(DATA_FILE)
                self.load_data()
                
    def _mark_dirty(self) -> None:
        """Mark the data as needing to be saved."""
        self._dirty = True
        self._cached_leaderboard = None  # Invalidate leaderboard cache
        
    def get_strawberries(self, user_id: int) -> int:
        """Get user's strawberry count."""
        return self.players[user_id]  # defaultdict handles default value
        
    async def add_strawberries(self, user_id: int, amount: int) -> int:
        """Add strawberries to user's account."""
        if amount < 0:
            raise ValueError("Amount must be positive")
            
        self.players[user_id] += amount
        self._mark_dirty()
        logger.info(f"Added {amount} strawberries to user {user_id}")
        return self.players[user_id]
        
    async def remove_strawberries(self, user_id: int, amount: int) -> bool:
        """Remove strawberries from user's account."""
        if amount < 0:
            raise ValueError("Amount must be positive")
            
        current = self.players[user_id]
        if current < amount:
            return False
            
        self.players[user_id] = current - amount
        self._mark_dirty()
        logger.info(f"Removed {amount} strawberries from user {user_id}")
        return True
        
    async def set_strawberries(self, user_id: int, amount: int) -> None:
        """Set a user's strawberry balance."""
        if amount < 0:
            raise ValueError("Amount cannot be negative")
            
        self.players[user_id] = amount
        self._mark_dirty()
        logger.info(f"Set user {user_id}'s strawberries to {amount}")
        
    async def transfer_strawberries(
        self,
        from_user_id: int,
        to_user_id: int,
        amount: int
    ) -> bool:
        """Transfer strawberries between users.
        
        Args:
            from_user_id: The sender's Discord ID
            to_user_id: The receiver's Discord ID
            amount: Amount of strawberries to transfer
            
        Returns:
            bool: True if transfer was successful, False if insufficient funds
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
            
        # Check if sender has enough strawberries
        if self.players[from_user_id] < amount:
            return False
            
        # Remove from sender
        if not await self.remove_strawberries(from_user_id, amount):
            return False
            
        # Add to receiver
        await self.add_strawberries(to_user_id, amount)
        
        logger.info(f"Transferred {amount} strawberries from {from_user_id} to {to_user_id}")
        return True
        
    def get_streak(self, user_id: int) -> int:
        """Get user's current daily streak."""
        return self.streaks[user_id]
        
    def get_player_data(self, user_id: int) -> Dict[str, int]:
        """Get a player's complete data.
        
        Args:
            user_id: The user's Discord ID
            
        Returns:
            Dict containing the player's strawberries and streak
        """
        return {
            'strawberries': self.players[user_id],
            'streak': self.streaks[user_id]
        }
        
    def can_claim_daily(self, user_id: int) -> Tuple[bool, Optional[datetime.timedelta]]:
        """Check if user can claim daily reward."""
        if user_id not in self.last_daily:
            return True, None
            
        last_claim = self.last_daily[user_id]
        now = datetime.datetime.now()
        time_passed = now - last_claim
        
        if time_passed.total_seconds() >= 24 * 3600:  # 24 hours
            return True, None
            
        time_until_next = datetime.timedelta(days=1) - time_passed
        return False, time_until_next
        
    async def claim_daily(self, user_id: int) -> int:
        """Claim daily reward and update streak.
        
        Args:
            user_id: The user's Discord ID
            
        Returns:
            int: The amount of strawberries rewarded, or 0 if already claimed
        """
        can_claim, _ = self.can_claim_daily(user_id)
        if not can_claim:
            return 0
            
        now = datetime.datetime.now()
        streak = self.streaks[user_id]
        
        # Check streak continuity
        if user_id in self.last_daily:
            hours_passed = (now - self.last_daily[user_id]).total_seconds() / 3600
            if hours_passed > 48:  # Reset streak if more than 48 hours passed
                streak = 0
                
        # Update streak
        streak += 1
        self.streaks[user_id] = streak
        
        # Calculate reward with capped streak bonus
        bonus = min((streak - 1) * DAILY_STREAK_BONUS, MAX_STREAK_BONUS)
        reward = DAILY_REWARD + bonus
        
        # Update user data
        await self.add_strawberries(user_id, reward)
        self.last_daily[user_id] = now
        self._mark_dirty()
        
        logger.info(f"User {user_id} claimed daily reward: {reward} strawberries (streak: {streak})")
        return reward
        
    async def get_leaderboard(self, limit: int = 10) -> List[Tuple[int, int]]:
        """Get the top players by strawberry count.
        
        Args:
            limit: Maximum number of players to return
            
        Returns:
            List of (user_id, strawberry_count) tuples
        """
        now = datetime.datetime.now()
        
        # Return cached leaderboard if valid
        if (self._cached_leaderboard is not None and 
            now < self._leaderboard_expires):
            return self._cached_leaderboard[:limit]
            
        # Calculate new leaderboard
        leaderboard = sorted(
            self.players.items(),
            key=lambda x: (-x[1], x[0])  # Sort by count desc, then ID asc
        )[:limit]
        
        # Cache for 5 minutes
        self._cached_leaderboard = leaderboard
        self._leaderboard_expires = now + datetime.timedelta(minutes=5)
        
        return leaderboard
        
    async def get_rank(self, user_id: int) -> Optional[int]:
        """Get user's rank on the leaderboard.
        
        Args:
            user_id: The user's Discord ID
            
        Returns:
            Optional[int]: User's rank (1-based) or None if not ranked
        """
        if user_id not in self.players:
            return None
            
        user_strawberries = self.players[user_id]
        return sum(1 for count in self.players.values() if count > user_strawberries) + 1
        
    async def cleanup_inactive_users(self, days: int = 30) -> int:
        """Remove data for users inactive for the specified number of days.
        
        Args:
            days: Number of days of inactivity before removal
            
        Returns:
            int: Number of users removed
        """
        now = datetime.datetime.now()
        cutoff = now - datetime.timedelta(days=days)
        
        to_remove: Set[int] = set()
        
        # Find inactive users
        for user_id, last_claim in self.last_daily.items():
            if last_claim < cutoff and self.players[user_id] <= STARTING_STRAWBERRIES:
                to_remove.add(user_id)
                
        # Remove their data
        for user_id in to_remove:
            self.players.pop(user_id, None)
            self.last_daily.pop(user_id, None)
            self.streaks.pop(user_id, None)
            
        if to_remove:
            self._mark_dirty()
            logger.info(f"Cleaned up {len(to_remove)} inactive users")
            
        return len(to_remove) 