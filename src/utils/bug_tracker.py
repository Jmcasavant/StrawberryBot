"""Bug tracking system for the bot."""
import json
import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from .core import setup_logger, DATA_DIR

logger = setup_logger(__name__)

# File paths
BUG_REPORTS_FILE = DATA_DIR / 'bug_reports.json'

@dataclass
class BugReport:
    """Represents a bug report."""
    id: str  # Unique ID for the bug report
    user_id: int  # Discord ID of the reporter
    game_type: str  # Type of game (blackjack, roulette, etc.)
    description: str  # User's description of the bug
    game_state: Dict  # Relevant game state when bug occurred
    timestamp: str  # When the bug was reported
    status: str = "open"  # Status of the bug (open, investigating, fixed, etc.)
    admin_notes: Optional[str] = None  # Notes from administrators

class BugTracker:
    """Manages bug reports for the bot."""
    
    def __init__(self):
        self.reports: Dict[str, BugReport] = {}
        self.next_id: int = 1
        self.load_reports()
        
    def load_reports(self) -> None:
        """Load bug reports from file."""
        if not BUG_REPORTS_FILE.exists():
            return
            
        try:
            with open(BUG_REPORTS_FILE, 'r') as f:
                data = json.load(f)
                
            # Convert dictionary data back to BugReport objects
            for report_id, report_data in data.items():
                self.reports[report_id] = BugReport(**report_data)
                
            # Update next_id based on existing reports
            if self.reports:
                max_id = max(int(report_id[3:]) for report_id in self.reports.keys())
                self.next_id = max_id + 1
                
            logger.info("Bug reports loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading bug reports: {e}")
            
    def save_reports(self) -> None:
        """Save bug reports to file."""
        try:
            # Convert BugReport objects to dictionaries
            data = {
                report_id: asdict(report)
                for report_id, report in self.reports.items()
            }
            
            # Create parent directory if it doesn't exist
            BUG_REPORTS_FILE.parent.mkdir(exist_ok=True)
            
            # Write to file
            with open(BUG_REPORTS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info("Bug reports saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving bug reports: {e}")
            
    def create_report(
        self,
        user_id: int,
        game_type: str,
        description: str,
        game_state: Dict
    ) -> str:
        """Create a new bug report.
        
        Args:
            user_id: Discord ID of the reporter
            game_type: Type of game where bug occurred
            description: User's description of the bug
            game_state: Relevant game state information
            
        Returns:
            str: The ID of the created report
        """
        report_id = f"BUG{self.next_id:04d}"
        self.next_id += 1
        
        report = BugReport(
            id=report_id,
            user_id=user_id,
            game_type=game_type,
            description=description,
            game_state=game_state,
            timestamp=datetime.datetime.now().isoformat(),
            status="open"
        )
        
        self.reports[report_id] = report
        self.save_reports()
        
        logger.info(f"Created bug report {report_id} from user {user_id}")
        return report_id
        
    def get_report(self, report_id: str) -> Optional[BugReport]:
        """Get a specific bug report."""
        return self.reports.get(report_id)
        
    def get_all_reports(self, status: Optional[str] = None) -> List[BugReport]:
        """Get all bug reports, optionally filtered by status."""
        if status:
            return [r for r in self.reports.values() if r.status == status]
        return list(self.reports.values())
        
    def update_report(
        self,
        report_id: str,
        status: Optional[str] = None,
        admin_notes: Optional[str] = None
    ) -> bool:
        """Update a bug report's status and/or notes.
        
        Args:
            report_id: ID of the report to update
            status: New status (if changing)
            admin_notes: New admin notes (if adding/updating)
            
        Returns:
            bool: True if report was updated, False if not found
        """
        report = self.reports.get(report_id)
        if not report:
            return False
            
        if status:
            report.status = status
        if admin_notes:
            report.admin_notes = admin_notes
            
        self.save_reports()
        logger.info(f"Updated bug report {report_id}")
        return True 