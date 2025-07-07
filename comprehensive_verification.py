#!/usr/bin/env python3
"""
Comprehensive verification script for new IPO scraper features
"""
import sqlite3
import re

def verify_new_features():
    """Verify all new features are working correctly"""
    
    # Connect to database
    conn = sqlite3.connect('ipo_data_investorgain.db')
    cursor = conn.cursor()
    
    print("🔍 COMPREHENSIVE VERIFICATION OF NEW IPO SCRAPER FEATURES")
    print("=" * 65)
    
    # Check schema changes
    print("\n📋 Schema Verification:")
    cursor.execute("PRAGMA table_info(ipo_master_data)")
    columns = [row[1] for row in cursor.fetchall()]
    
    new_columns = ['allotment_status_url', 'bse_code', 'nse_code', 'post_listing_details_table_html']
    for col in new_columns:
        status = "✅" if col in columns else "❌"
        print(f"  {col}: {status}")
    
    print(f"\n📊 Total columns: {len(columns)}")
    
    # Check data for recent IPOs
    print("\n🎯 Data Quality Verification:")
    cursor.execute("""
        SELECT ipo_id, allotment_status_url, bse_code, nse_code, 
               CASE WHEN post_listing_details_table_html != 'N/A' THEN 'YES' ELSE 'NO' END as has_post_listing,
               issue_price_band, face_value, gmp_latest, listing_at
        FROM ipo_master_data 
        WHERE ipo_id IN ('1279', '1280', '1317')
        ORDER BY ipo_id DESC
    """)
    
    results = cursor.fetchall()
    for row in results:
        ipo_id, allot_url, bse, nse, has_post, price_band, face_val, gmp, listing = row
        
        print(f"\n  📈 IPO {ipo_id}:")
        print(f"    Allotment URL: {allot_url[:50]}{'...' if len(allot_url) > 50 else ''}")
        print(f"    BSE Code: {bse} {'✅' if is_valid_code(bse) else '❌'}")
        print(f"    NSE Code: {nse} {'✅' if is_valid_code(nse) else '❌'}")
        print(f"    Post-listing Table: {has_post}")
        print(f"    Price Band: {price_band}")
        print(f"    Face Value: {face_val}")
        print(f"    GMP Latest: {gmp}")
        print(f"    Listing At: {listing}")
    
    # Check text cleaning quality
    print("\n🧹 Text Cleaning Verification:")
    cursor.execute("""
        SELECT ipo_id, issue_price_band, face_value, retail_quota
        FROM ipo_master_data 
        WHERE ipo_id IN ('1279', '1280', '1317')
        ORDER BY ipo_id DESC
    """)
    
    for row in cursor.fetchall():
        ipo_id, price_band, face_val, retail_quota = row
        print(f"\n  IPO {ipo_id}:")
        
        # Check for HTML tags
        has_html_tags = any('<' in str(field) and '>' in str(field) 
                           for field in [price_band, face_val, retail_quota])
        print(f"    HTML Tags Removed: {'✅' if not has_html_tags else '❌'}")
        
        # Check for proper formatting
        spacing_ok = not any('Per' in str(field) and not ' Per' in str(field) 
                            for field in [price_band, face_val] if field != 'N/A')
        print(f"    Proper Spacing: {'✅' if spacing_ok else '❌'}")
    
    # Statistics
    print("\n📈 Feature Usage Statistics:")
    
    # Allotment URLs
    cursor.execute("SELECT COUNT(*) FROM ipo_master_data WHERE allotment_status_url != 'N/A'")
    allot_count = cursor.fetchone()[0]
    
    # BSE/NSE codes
    cursor.execute("SELECT COUNT(*) FROM ipo_master_data WHERE bse_code != 'N/A' AND bse_code NOT IN ('Cd', 'Retail')")
    bse_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM ipo_master_data WHERE nse_code != 'N/A' AND nse_code NOT IN ('Cd', 'Retail')")
    nse_count = cursor.fetchone()[0]
    
    # Post-listing tables
    cursor.execute("SELECT COUNT(*) FROM ipo_master_data WHERE post_listing_details_table_html != 'N/A'")
    post_count = cursor.fetchone()[0]
    
    # Total IPOs
    cursor.execute("SELECT COUNT(*) FROM ipo_master_data")
    total_count = cursor.fetchone()[0]
    
    print(f"  Allotment URLs found: {allot_count}/{total_count} ({allot_count/total_count*100:.1f}%)")
    print(f"  Valid BSE codes: {bse_count}/{total_count} ({bse_count/total_count*100:.1f}%)")
    print(f"  Valid NSE codes: {nse_count}/{total_count} ({nse_count/total_count*100:.1f}%)")
    print(f"  Post-listing tables: {post_count}/{total_count} ({post_count/total_count*100:.1f}%)")
    
    conn.close()
    
    print("\n✅ VERIFICATION COMPLETED!")
    print("=" * 65)

def is_valid_code(code):
    """Check if a BSE/NSE code looks valid"""
    if not code or code == 'N/A':
        return False
    
    # Invalid codes we've seen
    invalid_codes = ['Cd', 'Retail', 'N/A']
    if code in invalid_codes:
        return False
    
    # Valid codes are usually alphanumeric, 3-10 characters
    return len(code) >= 3 and len(code) <= 10 and code.replace('_', '').isalnum()

if __name__ == "__main__":
    verify_new_features()
