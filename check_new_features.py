#!/usr/bin/env python3
"""
Quick database check script to verify new features
"""
import sqlite3
import json

# Connect to database
conn = sqlite3.connect('ipo_data_investorgain.db')
cursor = conn.cursor()

# Check the new columns for both IPO IDs
for ipo_id in ['1280', '1317']:
    cursor.execute("""
        SELECT 
            ipo_id, 
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
        FROM ipo_master_data 
        WHERE ipo_id = ?
    """, (ipo_id,))

    result = cursor.fetchone()
    if result:
        print(f"✅ New features verification for IPO ID {ipo_id}:")
        print(f"  IPO ID: {result[0]}")
        print(f"  Allotment Status URL: {result[1]}")
        print(f"  BSE Code: {result[2]}")
        print(f"  NSE Code: {result[3]}")
        print(f"  Post-listing Table: {result[4]}")
        print(f"  Issue Price Band: {result[5]}")
        print(f"  Face Value: {result[6]}")
        print(f"  GMP Latest: {result[7]}")
        print(f"  Listing At: {result[8]}")
        print()
    else:
        print(f"❌ No data found for IPO ID {ipo_id}")

# Check schema
cursor.execute("PRAGMA table_info(ipo_master_data)")
columns = cursor.fetchall()
print(f"✅ Total columns in table: {len(columns)}")
new_columns = ['allotment_status_url', 'bse_code', 'nse_code', 'post_listing_details_table_html']
for col in new_columns:
    found = any(col in row[1] for row in columns)
    print(f"  {col}: {'✅' if found else '❌'}")

# Check validation for IPO codes
print(f"\n✅ Data validation:")
cursor.execute("SELECT ipo_id, bse_code, nse_code FROM ipo_master_data WHERE ipo_id IN ('1280', '1317')")
for row in cursor.fetchall():
    ipo_id, bse_code, nse_code = row
    bse_valid = bse_code != 'N/A' and len(bse_code) >= 3 and bse_code.isalnum()
    nse_valid = nse_code != 'N/A' and len(nse_code) >= 3 and nse_code.isalnum()
    print(f"  IPO {ipo_id}: BSE={bse_code} {'✅' if bse_valid else '❌'}, NSE={nse_code} {'✅' if nse_valid else '❌'}")

conn.close()
print("\n✅ Database check completed!")
