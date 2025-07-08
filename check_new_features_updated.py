#!/usr/bin/env python3
"""
Quick database check script to verify new features
"""
import json
from database.db_manager import DatabaseManager
from config import DATABASE_TYPE, IPO_MASTER_TABLE_NAME

def check_new_features():
    """Check new features in the database"""
    
    # Connect to database
    db_manager = DatabaseManager()
    db_manager.connect()
    
    if not db_manager.conn and not db_manager.db:
        print("❌ Failed to connect to database")
        return
    
    print(f"🔍 Checking new features in {DATABASE_TYPE} database")
    print(f"Collection/Table: {IPO_MASTER_TABLE_NAME}")
    print("=" * 50)
    
    # Check the new columns for both IPO IDs
    test_ipo_ids = ['1280', '1317']
    
    for ipo_id in test_ipo_ids:
        try:
            if DATABASE_TYPE == 'mongodb':
                doc = db_manager.db[IPO_MASTER_TABLE_NAME].find_one({'ipo_id': ipo_id})
                if doc:
                    print(f"✅ New features verification for IPO ID {ipo_id}:")
                    print(f"  IPO ID: {doc.get('ipo_id', 'N/A')}")
                    print(f"  Company: {doc.get('company_name', 'N/A')}")
                    print(f"  Allotment Status URL: {doc.get('allotment_status_url', 'N/A')}")
                    print(f"  BSE Code: {doc.get('bse_code', 'N/A')}")
                    print(f"  NSE Code: {doc.get('nse_code', 'N/A')}")
                    print(f"  Post-listing Table: {'HTML_CONTENT_FOUND' if doc.get('post_listing_details_table_html', 'N/A') != 'N/A' else 'N/A'}")
                    print(f"  Issue Price Band: {doc.get('issue_price_band', 'N/A')}")
                    print(f"  Face Value: {doc.get('face_value', 'N/A')}")
                    print(f"  GMP Latest: {doc.get('gmp_latest', 'N/A')}")
                    print(f"  Listing At: {doc.get('listing_at', 'N/A')}")
                    print()
                else:
                    print(f"❌ No data found for IPO ID {ipo_id}")
            
            else:
                cursor = db_manager.cursor
                cursor.execute(f"""
                    SELECT 
                        ipo_id, 
                        company_name,
                        allotment_status_url, 
                        bse_code, 
                        nse_code, 
                        CASE 
                            WHEN post_listing_details_table_html = 'N/A' THEN 'N/A'
                            ELSE 'HTML_CONTENT_FOUND'
                        END as post_listing_status,
                        issue_price_band,
                        face_value,
                        gmp_latest,
                        listing_at
                    FROM {IPO_MASTER_TABLE_NAME} 
                    WHERE ipo_id = ?
                """, (ipo_id,))

                result = cursor.fetchone()
                if result:
                    print(f"✅ New features verification for IPO ID {ipo_id}:")
                    print(f"  IPO ID: {result[0]}")
                    print(f"  Company: {result[1]}")
                    print(f"  Allotment Status URL: {result[2]}")
                    print(f"  BSE Code: {result[3]}")
                    print(f"  NSE Code: {result[4]}")
                    print(f"  Post-listing Table: {result[5]}")
                    print(f"  Issue Price Band: {result[6]}")
                    print(f"  Face Value: {result[7]}")
                    print(f"  GMP Latest: {result[8]}")
                    print(f"  Listing At: {result[9]}")
                    print()
                else:
                    print(f"❌ No data found for IPO ID {ipo_id}")
        
        except Exception as e:
            print(f"❌ Error checking IPO ID {ipo_id}: {e}")
    
    # Check schema/fields
    print("📋 Schema/Field Information:")
    
    try:
        if DATABASE_TYPE == 'mongodb':
            if IPO_MASTER_TABLE_NAME in db_manager.db.list_collection_names():
                sample_doc = db_manager.db[IPO_MASTER_TABLE_NAME].find_one()
                if sample_doc:
                    fields = list(sample_doc.keys())
                    print(f"  Total fields: {len(fields)}")
                    
                    new_fields = ['allotment_status_url', 'bse_code', 'nse_code', 'post_listing_details_table_html']
                    print("  New fields status:")
                    for field in new_fields:
                        status = "✅" if field in fields else "❌"
                        print(f"    {field}: {status}")
                else:
                    print("  ❌ No documents found")
            else:
                print(f"  ❌ Collection {IPO_MASTER_TABLE_NAME} not found")
        
        elif DATABASE_TYPE == 'sqlite':
            cursor = db_manager.cursor
            cursor.execute(f"PRAGMA table_info({IPO_MASTER_TABLE_NAME})")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            print(f"  Total columns: {len(column_names)}")
            
            new_columns = ['allotment_status_url', 'bse_code', 'nse_code', 'post_listing_details_table_html']
            print("  New columns status:")
            for col in new_columns:
                status = "✅" if col in column_names else "❌"
                print(f"    {col}: {status}")
        
        elif DATABASE_TYPE == 'sqlserver':
            cursor = db_manager.cursor
            cursor.execute(f"""
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = '{IPO_MASTER_TABLE_NAME}'
            """)
            columns = [row[0] for row in cursor.fetchall()]
            
            print(f"  Total columns: {len(columns)}")
            
            new_columns = ['allotment_status_url', 'bse_code', 'nse_code', 'post_listing_details_table_html']
            print("  New columns status:")
            for col in new_columns:
                status = "✅" if col in columns else "❌"
                print(f"    {col}: {status}")
    
    except Exception as e:
        print(f"❌ Error checking schema: {e}")
    
    # Close database connection
    db_manager.close()
    
    print("\n✅ New features check complete!")

if __name__ == "__main__":
    check_new_features()
