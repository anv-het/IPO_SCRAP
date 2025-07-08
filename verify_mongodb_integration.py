#!/usr/bin/env python3
"""
Comprehensive verification script for MongoDB integration
"""
import json
from datetime import datetime
from database.db_manager import DatabaseManager
from config import DATABASE_TYPE, IPO_SUMMARY_TABLE_NAME, IPO_MASTER_TABLE_NAME

def verify_mongodb_integration():
    """Verify MongoDB integration is working correctly"""
    
    print("🔍 COMPREHENSIVE VERIFICATION OF MONGODB INTEGRATION")
    print("=" * 65)
    
    # Initialize database manager
    db_manager = DatabaseManager()
    db_manager.connect()
    
    if not db_manager.conn and not db_manager.db:
        print("❌ Failed to connect to database")
        return
    
    print(f"✅ Connected to {DATABASE_TYPE} database")
    
    # Verify collections/tables exist and have data
    print(f"\n📊 Data Verification:")
    
    try:
        if DATABASE_TYPE == 'mongodb':
            # Check MongoDB collections
            collections = db_manager.db.list_collection_names()
            print(f"  Available collections: {collections}")
            
            # Check summary data
            if IPO_SUMMARY_TABLE_NAME in collections:
                summary_count = db_manager.db[IPO_SUMMARY_TABLE_NAME].count_documents({})
                print(f"  {IPO_SUMMARY_TABLE_NAME}: {summary_count} documents")
                
                # Sample document
                sample_doc = db_manager.db[IPO_SUMMARY_TABLE_NAME].find_one()
                if sample_doc:
                    print(f"  Sample summary document keys: {list(sample_doc.keys())}")
            
            # Check master data
            if IPO_MASTER_TABLE_NAME in collections:
                master_count = db_manager.db[IPO_MASTER_TABLE_NAME].count_documents({})
                print(f"  {IPO_MASTER_TABLE_NAME}: {master_count} documents")
                
                # Sample document
                sample_doc = db_manager.db[IPO_MASTER_TABLE_NAME].find_one()
                if sample_doc:
                    print(f"  Sample master document keys: {list(sample_doc.keys())}")
            
        else:
            # Check SQLite/SQL Server tables
            if DATABASE_TYPE == 'sqlite':
                cursor = db_manager.cursor
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                print(f"  Available tables: {tables}")
                
                # Check record counts
                for table in [IPO_SUMMARY_TABLE_NAME, IPO_MASTER_TABLE_NAME]:
                    if table in tables:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        print(f"  {table}: {count} records")
            
            elif DATABASE_TYPE == 'sqlserver':
                cursor = db_manager.cursor
                cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'")
                tables = [row[0] for row in cursor.fetchall()]
                print(f"  Available tables: {tables}")
                
                # Check record counts
                for table in [IPO_SUMMARY_TABLE_NAME, IPO_MASTER_TABLE_NAME]:
                    if table in tables:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        print(f"  {table}: {count} records")
    
    except Exception as e:
        print(f"❌ Error during data verification: {e}")
    
    # Test data retrieval functionality
    print(f"\n🔍 Testing Data Retrieval:")
    
    try:
        # Test get_all_ipos
        all_ipos = db_manager.get_all_ipos(limit=5)
        if all_ipos:
            print(f"  ✅ Retrieved {len(all_ipos)} IPO records")
            
            # Show sample data
            if len(all_ipos) > 0:
                sample = all_ipos[0]
                print(f"  Sample IPO record: {sample.get('company_short_name_api', 'N/A')} (ID: {sample.get('ipo_id', 'N/A')})")
        else:
            print("  ❌ No IPO records retrieved")
    
    except Exception as e:
        print(f"❌ Error during data retrieval test: {e}")
    
    # Test specific IPO data retrieval
    print(f"\n🎯 Testing Specific IPO Data Retrieval:")
    
    try:
        # Get a few IPO IDs from master data
        if DATABASE_TYPE == 'mongodb':
            sample_ipos = list(db_manager.db[IPO_MASTER_TABLE_NAME].find({}, {'ipo_id': 1}).limit(3))
            ipo_ids = [str(ipo['ipo_id']) for ipo in sample_ipos]
        else:
            cursor = db_manager.cursor
            cursor.execute(f"SELECT ipo_id FROM {IPO_MASTER_TABLE_NAME} LIMIT 3")
            ipo_ids = [str(row[0]) for row in cursor.fetchall()]
        
        print(f"  Testing with IPO IDs: {ipo_ids}")
        
        for ipo_id in ipo_ids:
            # Test get_ipo_by_id
            ipo_data = db_manager.get_ipo_by_id(ipo_id)
            if ipo_data:
                print(f"  ✅ Retrieved data for IPO {ipo_id}: {ipo_data.get('company_short_name_api', 'N/A')}")
            else:
                print(f"  ❌ No data found for IPO {ipo_id}")
    
    except Exception as e:
        print(f"❌ Error during specific IPO data retrieval: {e}")
    
    # Test database write operations
    print(f"\n✍️ Testing Database Write Operations:")
    
    try:
        # Create test data
        test_data = {
            'ipo_id': '9999',
            'company_short_name_api': 'Test Company Ltd',
            'ipo_category': 'Test Category',
            'issue_price_band': '₹100-120',
            'listing_date': '2024-01-01',
            'scraped_at': datetime.now().isoformat()
        }
        
        # Test insert operations
        db_manager.insert_or_update_ipo_data(test_data)
        print(f"  ✅ Successfully inserted/updated test data")
        
        # Verify test data was inserted
        test_record = db_manager.get_ipo_by_id('9999')
        if test_record:
            print(f"  ✅ Test data verified in database: {test_record.get('company_short_name_api', 'N/A')}")
        else:
            print(f"  ❌ Test data not found in database")
        
        # Clean up test data
        if DATABASE_TYPE == 'mongodb':
            db_manager.db[IPO_MASTER_TABLE_NAME].delete_one({'ipo_id': '9999'})
        else:
            cursor = db_manager.cursor
            cursor.execute(f"DELETE FROM {IPO_MASTER_TABLE_NAME} WHERE ipo_id = '9999'")
            db_manager.conn.commit()
        
        print(f"  ✅ Test data cleaned up")
    
    except Exception as e:
        print(f"❌ Error during write operations test: {e}")
    
    # Close database connection
    db_manager.close()
    
    print(f"\n🎉 MongoDB Integration Verification Complete!")
    print(f"Database Type: {DATABASE_TYPE}")
    print(f"Summary Table/Collection: {IPO_SUMMARY_TABLE_NAME}")
    print(f"Master Table/Collection: {IPO_MASTER_TABLE_NAME}")

if __name__ == "__main__":
    verify_mongodb_integration()
