#!/usr/bin/env python
"""
Patient Simulator Bot - Main entry point
Run: python run.py --mode test --calls 10
"""

import argparse
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description='Patient Simulator Bot')
    parser.add_argument('--mode', choices=['server', 'test', 'both'], 
                       default='server', help='Run mode')
    parser.add_argument('--calls', type=int, default=10,
                       help='Number of test calls to make')
    parser.add_argument('--scenario', type=str, default=None,
                       help='Specific scenario to test')
    
    args = parser.parse_args()
    
    # Validate environment variables
    required_vars = ['TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 
                    'TWILIO_PHONE_NUMBER', 'OPENAI_API_KEY', 
                    'ELEVENLABS_API_KEY', 'BASE_URL']
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"Error: Missing required environment variables: {', '.join(missing)}")
        print("Please check your .env file")
        sys.exit(1)
    
    if args.mode == 'server':
        print("Starting webhook server for incoming calls...")
        print(f"Make sure your Twilio webhook is set to: {os.getenv('BASE_URL')}/twiml")
        from app.webhook_server import app
        app.run(port=5000, debug=True)
        
    elif args.mode == 'test':
        print(f"Running test mode with {args.calls} calls...")
        from tests.test_runner import run_test_suite
        run_test_suite(num_calls=args.calls)
        
    elif args.mode == 'both':
        print("Starting server and test suite...")
        import threading
        from app.webhook_server import app
        from tests.test_runner import run_test_suite
        
        # Start server in background
        server_thread = threading.Thread(target=app.run, kwargs={'port': 5000, 'debug': False})
        server_thread.daemon = True
        server_thread.start()
        
        # Give server time to start
        import time
        time.sleep(3)
        
        # Run tests
        run_test_suite(num_calls=args.calls)
        
        print("Tests complete. Press Ctrl+C to stop server.")
        try:
            server_thread.join()
        except KeyboardInterrupt:
            print("\nShutting down...")

if __name__ == "__main__":
    main()