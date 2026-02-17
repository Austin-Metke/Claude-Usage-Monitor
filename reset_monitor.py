#!/usr/bin/env python3
"""
API Reset Time Monitor
Monitors an API endpoint for reset times and sends email notifications when resets occur.
"""

import requests
import smtplib
import time
import json
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from typing import Dict, Optional
from pathlib import Path

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, will use system env vars

# ==================== CONFIGURATION ====================
# Load from environment variables
API_URL = os.getenv('API_URL')
NOTIFICATION_METHOD = os.getenv('NOTIFICATION_METHOD', 'email')  # 'email', 'webhook', or 'both'

# Email configuration (for SMTP method)
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')

# Webhook configuration (optional)
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# Monitoring settings
SLEEP_BUFFER = int(os.getenv('SLEEP_BUFFER', '5'))  # Seconds before reset time to wake up
MAX_RETRY_DELAY = int(os.getenv('MAX_RETRY_DELAY', '300'))  # Maximum retry delay in seconds

# ==================== LOGGING SETUP ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reset_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== NOTIFICATION FUNCTIONS ====================
def send_email(subject: str, body: str) -> bool:
    """
    Send email notification via SMTP.
    
    Args:
        subject: Email subject line
        body: Email body content
        
    Returns:
        True if email sent successfully, False otherwise
    """
    if not all([SMTP_USER, SMTP_PASSWORD, RECIPIENT_EMAIL]):
        logger.warning("Email credentials not configured, skipping email notification")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Email sent successfully: {subject}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False


def send_webhook(payload: Dict) -> bool:
    """
    Send notification via webhook (Discord, Slack, custom endpoint, etc.).
    
    Args:
        payload: Dictionary to send as JSON
        
    Returns:
        True if webhook sent successfully, False otherwise
    """
    if not WEBHOOK_URL:
        logger.warning("Webhook URL not configured, skipping webhook notification")
        return False
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Webhook sent successfully to {WEBHOOK_URL}")
        return True
    except Exception as e:
        logger.error(f"Failed to send webhook: {e}")
        return False


def send_reset_notification(reset_type: str, reset_time: str, utilization: float):
    """Send notification that a reset has occurred using configured method(s)."""
    
    # Email notification
    if NOTIFICATION_METHOD in ['email', 'both']:
        subject = f"🔄 API Reset: {reset_type}"
        body = f"""
API Reset Notification
======================

Reset Type: {reset_type}
Reset Time: {reset_time}
Previous Utilization: {utilization}%

The API has been reset and is ready for new requests.

---
Automated notification from Reset Monitor
    """
        send_email(subject, body.strip())
    
    # Webhook notification
    if NOTIFICATION_METHOD in ['webhook', 'both']:
        payload = {
            "reset_type": reset_type,
            "reset_time": reset_time,
            "utilization": utilization,
            "message": f"API reset: {reset_type}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        send_webhook(payload)


# ==================== API FUNCTIONS ====================
def fetch_reset_data() -> Optional[Dict]:
    """
    Fetch reset time data from API endpoint.
    
    Returns:
        JSON response as dictionary, or None if request fails
    """
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch data from API: {e}")
        return None


def parse_reset_times(data: Dict) -> Dict[str, datetime]:
    """
    Extract all 'resets_at' timestamps from JSON response.
    
    Args:
        data: JSON response dictionary
        
    Returns:
        Dictionary mapping reset type to datetime object
    """
    reset_times = {}
    
    for key, value in data.items():
        if isinstance(value, dict) and 'resets_at' in value:
            try:
                # Parse ISO 8601 timestamp with timezone
                reset_time = datetime.fromisoformat(value['resets_at'])
                reset_times[key] = {
                    'time': reset_time,
                    'utilization': value.get('utilization', 0)
                }
                logger.debug(f"Parsed {key}: resets at {reset_time}")
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse timestamp for {key}: {e}")
    
    return reset_times


# ==================== MONITORING LOGIC ====================
def monitor_resets():
    """
    Main monitoring loop.
    Intelligently sleeps until the next reset time, then sends notifications.
    """
    logger.info("Starting reset monitor...")
    logger.info(f"API URL: {API_URL}")
    logger.info(f"Sleep buffer: {SLEEP_BUFFER}s before reset time")
    
    retry_count = 0
    
    while True:
        try:
            # Fetch current data
            logger.info("Fetching reset time data from API...")
            data = fetch_reset_data()
            
            if data is None:
                retry_count += 1
                retry_delay = min(30 * retry_count, MAX_RETRY_DELAY)
                logger.warning(f"API fetch failed. Retrying in {retry_delay}s (attempt {retry_count})")
                time.sleep(retry_delay)
                continue
            
            # Reset retry counter on successful fetch
            retry_count = 0
            
            # Parse reset times
            reset_times = parse_reset_times(data)
            
            if not reset_times:
                logger.warning("No reset times found in API response. Retrying in 60s...")
                time.sleep(60)
                continue
            
            # Get current time
            now = datetime.now(timezone.utc)
            
            # Find the next upcoming reset
            upcoming_resets = []
            for reset_type, reset_info in reset_times.items():
                reset_time = reset_info['time']
                time_until = (reset_time - now).total_seconds()
                
                if time_until > 0:
                    upcoming_resets.append({
                        'type': reset_type,
                        'time': reset_time,
                        'utilization': reset_info['utilization'],
                        'seconds_until': time_until
                    })
                    logger.info(f"{reset_type}: {time_until / 3600:.2f} hours until reset ({reset_time.isoformat()})")
                else:
                    logger.info(f"{reset_type}: reset time already passed ({reset_time.isoformat()})")
            
            if not upcoming_resets:
                logger.warning("All reset times are in the past! Fetching fresh data in 30s...")
                time.sleep(30)
                continue
            
            # Sort by time and get the earliest reset
            upcoming_resets.sort(key=lambda x: x['seconds_until'])
            next_reset = upcoming_resets[0]
            
            # Calculate sleep time (wake up a few seconds before the reset)
            sleep_duration = max(0, next_reset['seconds_until'] - SLEEP_BUFFER)
            
            if sleep_duration > 0:
                wake_time = now + (next_reset['time'] - now) - (SLEEP_BUFFER * 1)
                logger.info(f"⏰ Sleeping for {sleep_duration / 3600:.2f} hours until {next_reset['type']} reset")
                logger.info(f"   Will wake at {wake_time.isoformat()} ({SLEEP_BUFFER}s before reset)")
                time.sleep(sleep_duration)
            
            # Re-check current time after sleeping
            now = datetime.now(timezone.utc)
            
            # Check if we've reached or passed the reset time
            time_until_reset = (next_reset['time'] - now).total_seconds()
            
            if time_until_reset <= SLEEP_BUFFER and time_until_reset >= -60:
                # We're at the reset time (within buffer window)
                logger.info(f"🔄 Reset time reached for {next_reset['type']}!")
                send_reset_notification(
                    next_reset['type'],
                    next_reset['time'].isoformat(),
                    next_reset['utilization']
                )
                
                # Wait a moment for the reset to complete
                logger.info("Waiting 5 seconds for reset to complete...")
                time.sleep(5)
                
                # Fetch fresh data immediately after reset
                logger.info("Fetching fresh data after reset...")
                fresh_data = fetch_reset_data()
                if fresh_data:
                    logger.info("Fresh data retrieved successfully!")
                    new_resets = parse_reset_times(fresh_data)
                    for reset_type, reset_info in new_resets.items():
                        logger.info(f"  {reset_type}: next reset at {reset_info['time'].isoformat()}")
                else:
                    logger.warning("Failed to fetch fresh data after reset")
                
                # Continue to next iteration to recalculate next reset
                continue
            elif time_until_reset < -60:
                # We somehow missed the reset window (clock drift or long sleep?)
                logger.warning(f"Missed reset window for {next_reset['type']} by {abs(time_until_reset)}s")
                continue
            else:
                # Still waiting for reset, sleep a bit more
                logger.info(f"Still {time_until_reset:.1f}s until reset, sleeping...")
                time.sleep(max(1, time_until_reset))
                continue
            
        except KeyboardInterrupt:
            logger.info("Monitor stopped by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error in monitoring loop: {e}", exc_info=True)
            logger.info("Retrying in 60 seconds...")
            time.sleep(60)


# ==================== MAIN ENTRY POINT ====================
if __name__ == "__main__":
    # Validate configuration
    if not API_URL:
        logger.error("API_URL environment variable is required!")
        logger.error("Please set it in your .env file or environment")
        exit(1)
    
    if NOTIFICATION_METHOD in ['email', 'both']:
        if not all([SMTP_USER, SMTP_PASSWORD, RECIPIENT_EMAIL]):
            logger.error("Email notification requires: SMTP_USER, SMTP_PASSWORD, RECIPIENT_EMAIL")
            logger.error("Either set these variables or change NOTIFICATION_METHOD to 'webhook'")
            exit(1)
    
    if NOTIFICATION_METHOD in ['webhook', 'both']:
        if not WEBHOOK_URL:
            logger.error("Webhook notification requires: WEBHOOK_URL")
            logger.error("Either set this variable or change NOTIFICATION_METHOD to 'email'")
            exit(1)
    
    logger.info(f"Configuration loaded:")
    logger.info(f"  API URL: {API_URL}")
    logger.info(f"  Notification method: {NOTIFICATION_METHOD}")
    if NOTIFICATION_METHOD in ['email', 'both']:
        logger.info(f"  Email: {SMTP_USER} → {RECIPIENT_EMAIL}")
    if NOTIFICATION_METHOD in ['webhook', 'both']:
        logger.info(f"  Webhook: {WEBHOOK_URL}")
    
    try:
        monitor_resets()
    except Exception as e:
        logger.critical(f"Monitor crashed: {e}", exc_info=True)
        exit(1)
