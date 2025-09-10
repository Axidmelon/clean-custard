#!/usr/bin/env python3
import time
import requests
from db.dependencies import get_db
from db.models import Connection
from sqlalchemy.orm import Session

def check_schema_status():
    """Check if schema is saved for the new connection"""
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        connection = db.query(Connection).filter(Connection.agent_id == 'agent-og-test-02-1757479817').first()
        
        if connection:
            has_schema = connection.db_schema_cache is not None
            print(f"[{time.strftime('%H:%M:%S')}] Connection: {connection.name}")
            print(f"[{time.strftime('%H:%M:%S')}] Agent ID: {connection.agent_id}")
            print(f"[{time.strftime('%H:%M:%S')}] Has schema: {has_schema}")
            if has_schema:
                print(f"[{time.strftime('%H:%M:%S')}] Schema length: {len(str(connection.db_schema_cache))} chars")
                print(f"[{time.strftime('%H:%M:%S')}] Schema preview: {str(connection.db_schema_cache)[:100]}...")
            return has_schema
        else:
            print(f"[{time.strftime('%H:%M:%S')}] Connection not found")
            return False
    finally:
        db.close()

if __name__ == "__main__":
    print("Monitoring schema discovery for OG TEST 02...")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            check_schema_status()
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nMonitoring stopped")
