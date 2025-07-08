#!/usr/bin/env python3
"""
Comprehensive verification script for new IPO scraper features
"""
import re
from database.db_manager import DatabaseManager
from config import DATABASE_TYPE, IPO_MASTER_TABLE_NAME

def verify_new_features():
    """Verify all new features are working correctly"""
    
    # Connect to database
    db_manager = DatabaseManager()
    db_manager.connect()
    
    if not db_manager.conn and not db_manager.db:
        print("❌ Failed to connect to database")
        return
    
    print("🔍 COMPREHENSIVE VERIFICATION OF NEW IPO SCRAPER FEATURES")
    print("=" * 65)
    print(f"Database Type: {DATABASE_TYPE}")
    print(f"Master Table/Collection: {IPO_MASTER_TABLE_NAME}")
    
    # Check schema changes
    print("\n📋 Schema Verification:")
    
    try:
        if DATABASE_TYPE == 'mongodb':
            # Check if collection exists and get sample document
            if IPO_MASTER_TABLE_NAME in db_manager.db.list_collection_names():
                sample_doc = db_manager.db[IPO_MASTER_TABLE_NAME].find_one()
                if sample_doc:
                    columns = list(sample_doc.keys())
                    print(f"  Available fields: {len(columns)}")
                    
                    new_fields = ['allotment_status_url', 'bse_code', 'nse_code', 'post_listing_details_table_html']
                    for field in new_fields:
                        status = "✅" if field in columns else "❌"
                        print(f"  {field}: {status}")
                else:
                    print("  ❌ No documents found in collection")
            else:
                print(f"  ❌ Collection {IPO_MASTER_TABLE_NAME} not found")
        
        elif DATABASE_TYPE == 'sqlite':
            cursor = db_manager.cursor
            cursor.execute(f"PRAGMA table_info({IPO_MASTER_TABLE_NAME})")
            columns = [row[1] for row in cursor.fetchall()]
            
            new_columns = ['allotment_status_url', 'bse_code', 'nse_code', 'post_listing_details_table_html']
            for col in new_columns:
                status = "✅" if col in columns else "❌"
                print(f"  {col}: {status}")
            
            print(f"\n📊 Total columns: {len(columns)}")
        
        elif DATABASE_TYPE == 'sqlserver':
            cursor = db_manager.cursor
            cursor.execute(f"""
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = '{IPO_MASTER_TABLE_NAME}'
            """)
            columns = [row[0] for row in cursor.fetchall()]
            
            new_columns = ['allotment_status_url', 'bse_code', 'nse_code', 'post_listing_details_table_html']
            for col in new_columns:
                status = "✅" if col in columns else "❌"
                print(f"  {col}: {status}")
            
            print(f"\n📊 Total columns: {len(columns)}")
    
    except Exception as e:
        print(f"❌ Error during schema verification: {e}")
    
    # Check data for recent IPOs
    print("\n🎯 Data Quality Verification:")
    
    try:
        test_ipo_ids = ['1279', '1280', '1317']
        
        if DATABASE_TYPE == 'mongodb':
            for ipo_id in test_ipo_ids:
                doc = db_manager.db[IPO_MASTER_TABLE_NAME].find_one({'ipo_id': ipo_id})
                if doc:
                    print(f"\n  📈 IPO {ipo_id}:")
                    print(f"    Company: {doc.get('company_name', 'N/A')}")
                    print(f"    Allotment URL: {doc.get('allotment_status_url', 'N/A')[:50]}...")
                    print(f"    BSE Code: {doc.get('bse_code', 'N/A')}")
                    print(f"    NSE Code: {doc.get('nse_code', 'N/A')}")
                    print(f"    Post-listing: {'YES' if doc.get('post_listing_details_table_html', 'N/A') != 'N/A' else 'NO'}")
                else:
                    print(f"  ❌ No data found for IPO {ipo_id}")
        
        else:
            cursor = db_manager.cursor
            for ipo_id in test_ipo_ids:
                cursor.execute(f"""
                    SELECT ipo_id, company_name, allotment_status_url, bse_code, nse_code, 
                           CASE WHEN post_listing_details_table_html != 'N/A' THEN 'YES' ELSE 'NO' END as has_post_listing,
                           issue_price_band, face_value, gmp_latest, listing_at
                    FROM {IPO_MASTER_TABLE_NAME} 
                    WHERE ipo_id = ?
                """, (ipo_id,))
                
                result = cursor.fetchone()
                if result:
                    print(f"\n  📈 IPO {ipo_id}:")
                    print(f"    Company: {result[1]}")
                    print(f"    Allotment URL: {result[2][:50]}...")
                    print(f"    BSE Code: {result[3]}")
                    print(f"    NSE Code: {result[4]}")
                    print(f"    Post-listing: {result[5]}")
                else:
                    print(f"  ❌ No data found for IPO {ipo_id}")
    
    except Exception as e:
        print(f"❌ Error during data quality verification: {e}")
    
    # Summary statistics
    print("\n📊 Summary Statistics:")
    
    try:
        if DATABASE_TYPE == 'mongodb':
            total_count = db_manager.db[IPO_MASTER_TABLE_NAME].count_documents({})
            allot_count = db_manager.db[IPO_MASTER_TABLE_NAME].count_documents({
                'allotment_status_url': {'$ne': 'N/A'}
            })
            bse_count = db_manager.db[IPO_MASTER_TABLE_NAME].count_documents({
                'bse_code': {'$ne': 'N/A', '$nin': ['Cd', 'Retail']}
            })
            nse_count = db_manager.db[IPO_MASTER_TABLE_NAME].count_documents({
                'nse_code': {'$ne': 'N/A', '$nin': ['Cd', 'Retail']}
            })
            post_count = db_manager.db[IPO_MASTER_TABLE_NAME].count_documents({
                'post_listing_details_table_html': {'$ne': 'N/A'}
            })
        
        else:
            cursor = db_manager.cursor
            
            cursor.execute(f"SELECT COUNT(*) FROM {IPO_MASTER_TABLE_NAME}")
            total_count = cursor.fetchone()[0]
            
            cursor.execute(f"SELECT COUNT(*) FROM {IPO_MASTER_TABLE_NAME} WHERE allotment_status_url != 'N/A'")
            allot_count = cursor.fetchone()[0]
            
            cursor.execute(f"SELECT COUNT(*) FROM {IPO_MASTER_TABLE_NAME} WHERE bse_code != 'N/A' AND bse_code NOT IN ('Cd', 'Retail')")
            bse_count = cursor.fetchone()[0]
            
            cursor.execute(f"SELECT COUNT(*) FROM {IPO_MASTER_TABLE_NAME} WHERE nse_code != 'N/A' AND nse_code NOT IN ('Cd', 'Retail')")
            nse_count = cursor.fetchone()[0]
            
            cursor.execute(f"SELECT COUNT(*) FROM {IPO_MASTER_TABLE_NAME} WHERE post_listing_details_table_html != 'N/A'")
            post_count = cursor.fetchone()[0]
        
        print(f"  Total IPOs: {total_count}")
        print(f"  With Allotment URLs: {allot_count} ({allot_count/total_count*100:.1f}%)")
        print(f"  With BSE Codes: {bse_count} ({bse_count/total_count*100:.1f}%)")
        print(f"  With NSE Codes: {nse_count} ({nse_count/total_count*100:.1f}%)")
        print(f"  With Post-listing Data: {post_count} ({post_count/total_count*100:.1f}%)")
    
    except Exception as e:
        print(f"❌ Error during summary statistics: {e}")
    
    # Close database connection
    db_manager.close()
    
    print("\n✅ Verification Complete!")

def is_valid_code(code):
    """Check if a code looks valid (not empty, N/A, or common placeholders)"""
    return code and code not in ['N/A', 'Cd', 'Retail', '', 'None'] and len(code) > 2

if __name__ == "__main__":
    verify_new_features()
