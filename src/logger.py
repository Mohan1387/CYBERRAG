"""
Logging and Progress Tracking Module

This module provides a centralized logging configuration and a custom ProgressTracker class
to monitor the execution of long-running operations (like search and LLM generation).

It handles:
1.  **File & Console Logging:** Writes logs to both the console and timestamped files in the `logs/` directory.
2.  **Progress Tracking:** A `ProgressTracker` singleton to record the start, completion, and duration of processing stages.
"""

import logging
import os
from datetime import datetime
from pathlib import Path

# Create logs directory if it doesn't exist
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Configure logging
# Logs are saved with a timestamp to avoid overwriting previous sessions
log_filename = LOG_DIR / f"cyberrag_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)

def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance for a specific module.
    
    Args:
        name (str): The name of the module requesting the logger.
        
    Returns:
        logging.Logger: The logger instance.
    """
    return logging.getLogger(name)


class ProgressTracker:
    """
    Tracks the progress, status, and duration of multi-step operations.
    
    This class is useful for debugging performance bottlenecks and providing
    user feedback on long-running tasks.
    """
    
    def __init__(self):
        self.logger = get_logger("ProgressTracker")
        self.stages = {}
        self.current_stage = None
        
    def start_stage(self, stage_name: str, description: str = ""):
        """
        Begin tracking a new stage.
        
        Args:
            stage_name (str): Unique identifier for the stage.
            description (str): Human-readable description of what is happening.
        """
        self.current_stage = stage_name
        self.stages[stage_name] = {
            "start_time": datetime.now(),
            "description": description,
            "status": "IN_PROGRESS"
        }
        self.logger.info(f"▶️ START: {stage_name} - {description}")
        
    def complete_stage(self, stage_name: str, details: str = ""):
        """
        Mark a stage as successfully completed.
        
        Args:
            stage_name (str): The identifier of the stage to complete.
            details (str): Additional information about the completion (e.g., "Found 5 results").
        """
        if stage_name in self.stages:
            start_time = self.stages[stage_name]["start_time"]
            duration = (datetime.now() - start_time).total_seconds()
            self.stages[stage_name]["status"] = "COMPLETED"
            self.stages[stage_name]["duration"] = duration
            self.logger.info(f"✅ COMPLETE: {stage_name} ({duration:.2f}s) - {details}")
        
    def fail_stage(self, stage_name: str, error: str = ""):
        """
        Mark a stage as failed.
        
        Args:
            stage_name (str): The identifier of the stage that failed.
            error (str): The error message or reason for failure.
        """
        if stage_name in self.stages:
            start_time = self.stages[stage_name]["start_time"]
            duration = (datetime.now() - start_time).total_seconds()
            self.stages[stage_name]["status"] = "FAILED"
            self.stages[stage_name]["duration"] = duration
            self.logger.error(f"❌ FAILED: {stage_name} ({duration:.2f}s) - {error}")
            
    def get_summary(self) -> str:
        """
        Generate a text summary of all tracked stages.
        
        Returns:
            str: A formatted table of stages, statuses, and durations.
        """
        summary = "\n=== OPERATION SUMMARY ===\n"
        total_duration = 0
        for stage, info in self.stages.items():
            duration = info.get("duration", 0)
            total_duration += duration
            status = info["status"]
            summary += f"{status:12} | {stage:20} | {duration:6.2f}s\n"
        summary += f"\nTotal Duration: {total_duration:.2f}s"
        self.logger.info(summary)
        return summary


# Global progress tracker instance to be shared across modules
progress_tracker = ProgressTracker()
