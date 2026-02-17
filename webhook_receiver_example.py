#!/usr/bin/env python3
"""
Example Webhook Receiver
A simple Flask server that receives and logs reset notifications.
This is useful if you want to run your own webhook endpoint.

Usage:
    pip install flask
    python webhook_receiver.py

Then set WEBHOOK_URL=http://your-server:5000/webhook in your .env file
"""

from flask import Flask, request, jsonify
from datetime import datetime
import logging

app = Flask(__name__)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webhook_notifications.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
    """Receive and log reset notifications"""
    try:
        data = request.get_json()
        
        logger.info("=" * 60)
        logger.info("RESET NOTIFICATION RECEIVED")
        logger.info(f"Reset Type: {data.get('reset_type')}")
        logger.info(f"Reset Time: {data.get('reset_time')}")
        logger.info(f"Utilization: {data.get('utilization')}%")
        logger.info(f"Message: {data.get('message')}")
        logger.info(f"Timestamp: {data.get('timestamp')}")
        logger.info("=" * 60)
        
        # Here you could add custom logic:
        # - Send a Telegram message
        # - Update a database
        # - Trigger another API call
        # - Send a desktop notification
        # etc.
        
        return jsonify({"status": "success", "received": datetime.utcnow().isoformat()}), 200
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()}), 200


if __name__ == '__main__':
    logger.info("Starting webhook receiver on http://0.0.0.0:5000")
    logger.info("Webhook endpoint: http://0.0.0.0:5000/webhook")
    logger.info("Health check: http://0.0.0.0:5000/health")
    app.run(host='0.0.0.0', port=5000, debug=False)
