#!/usr/bin/env python3
"""
Test script to verify database connections and table/collection operations
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DATABASE_TYPE, IPO_SUMMARY_TABLE_NAME, IPO_MASTER_TABLE_NAME
from database.db_manager import DatabaseManager

def test_database_operations():
    """Test basic database operations"""
    print("=" * 60)
    print("DATABASE CONNECTION AND OPERATIONS TEST")
    print("=" * 60)
    print(f"Database Type: {DATABASE_TYPE}")
    print(f"Summary Table/Collection: {IPO_SUMMARY_TABLE_NAME}")
    print(f"Master Table/Collection: {IPO_MASTER_TABLE_NAME}")
    print("-" * 60)
    
    # Test database connection
    db_manager = DatabaseManager()
    try:
        print("Testing database connection...")
        db_manager.connect()
        
        if DATABASE_TYPE == 'mongodb':
            if db_manager.db is not None:
                print("✅ MongoDB connection successful")
                
                # Test collections
                collections = db_manager.db.list_collection_names()
                print(f"📊 Available collections: {collections}")
                
                # Test summary collection
                summary_count = db_manager.db[IPO_SUMMARY_TABLE_NAME].count_documents({})
                print(f"📈 Summary collection '{IPO_SUMMARY_TABLE_NAME}' records: {summary_count}")
                
                # Test master collection
                master_count = db_manager.db[IPO_MASTER_TABLE_NAME].count_documents({})
                print(f"📋 Master collection '{IPO_MASTER_TABLE_NAME}' records: {master_count}")
                
            else:
                print("❌ MongoDB connection failed")
        else:
            if db_manager.conn is not None:
                print(f"✅ {DATABASE_TYPE.upper()} connection successful")
                
                # Test tables
                if DATABASE_TYPE == 'sqlite':
                    db_manager.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in db_manager.cursor.fetchall()]
                elif DATABASE_TYPE == 'sqlserver':
                    db_manager.cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
                    tables = [row[0] for row in db_manager.cursor.fetchall()]
                
                print(f"📊 Available tables: {tables}")
                
                # Test summary table
                if IPO_SUMMARY_TABLE_NAME in tables:
                    db_manager.cursor.execute(f"SELECT COUNT(*) FROM {IPO_SUMMARY_TABLE_NAME}")
                    summary_count = db_manager.cursor.fetchone()[0]
                    print(f"📈 Summary table '{IPO_SUMMARY_TABLE_NAME}' records: {summary_count}")
                else:
                    print(f"⚠️  Summary table '{IPO_SUMMARY_TABLE_NAME}' not found")
                
                # Test master table
                if IPO_MASTER_TABLE_NAME in tables:
                    db_manager.cursor.execute(f"SELECT COUNT(*) FROM {IPO_MASTER_TABLE_NAME}")
                    master_count = db_manager.cursor.fetchone()[0]
                    print(f"📋 Master table '{IPO_MASTER_TABLE_NAME}' records: {master_count}")
                else:
                    print(f"⚠️  Master table '{IPO_MASTER_TABLE_NAME}' not found")
                    
            else:
                print(f"❌ {DATABASE_TYPE.upper()} connection failed")
        
        # Test table/collection creation
        print("-" * 60)
        print("Testing table/collection creation...")
        db_manager.create_table()
        print("✅ Table/collection creation test completed")
        
    except Exception as e:
        print(f"❌ Error during database operations: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db_manager.close()
        print("🔒 Database connection closed")
    
    print("=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    test_database_operations()
