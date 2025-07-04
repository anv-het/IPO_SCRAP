#!/usr/bin/env python3
"""
Database viewer for IPO Summary data
"""

import sqlite3
import json
from datetime import datetime

def view_ipo_data():
    """View and analyze IPO summary data in the database"""
    
    # Connect to database
    conn = sqlite3.connect('ipo_data_investorgain.db')
    cursor = conn.cursor()
    
    try:
        # Get basic statistics
        print("IPO SUMMARY DATABASE ANALYSIS")
        print("=" * 60)
        
        # Total records
        cursor.execute("SELECT COUNT(*) FROM ipo_summary_data")
        total_records = cursor.fetchone()[0]
        print(f"Total records: {total_records}")
        
        # Records by year
        cursor.execute("""
            SELECT year, COUNT(*) as count 
            FROM ipo_summary_data 
            GROUP BY year 
            ORDER BY year DESC
        """)
        
        print("\nRecords by year:")
        print("-" * 30)
        for year, count in cursor.fetchall():
            print(f"Year {year}: {count} records")
        
        # Status distribution
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM ipo_summary_data 
            GROUP BY status 
            ORDER BY count DESC
        """)
        
        print("\nStatus distribution:")
        print("-" * 30)
        for status, count in cursor.fetchall():
            status_display = status if status else "NULL"
            print(f"{status_display}: {count} records")
        
        # IPO categories
        cursor.execute("""
            SELECT ipo_category, COUNT(*) as count 
            FROM ipo_summary_data 
            GROUP BY ipo_category 
            ORDER BY count DESC
        """)
        
        print("\nIPO Categories:")
        print("-" * 30)
        for category, count in cursor.fetchall():
            category_display = category if category else "NULL"
            print(f"{category_display}: {count} records")
        
        # Listed IPOs with gains
        cursor.execute("""
            SELECT ipo_name, list_price, list_gain, ipo_price 
            FROM ipo_summary_data 
            WHERE status = 'Listed' AND list_price IS NOT NULL 
            ORDER BY CAST(REPLACE(list_gain, '%', '') AS REAL) DESC 
            LIMIT 10
        """)
        
        print("\nTop 10 Listed IPOs by Gain:")
        print("-" * 60)
        listed_ipos = cursor.fetchall()
        if listed_ipos:
            for ipo_name, list_price, list_gain, ipo_price in listed_ipos:
                print(f"{ipo_name[:40]:40} | List: ₹{list_price:>8} | Gain: {list_gain:>8} | IPO: ₹{ipo_price}")
        else:
            print("No listed IPOs found with gain data")
        
        # Recent entries
        cursor.execute("""
            SELECT ipo_name, status, ipo_category, year, created_at 
            FROM ipo_summary_data 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        print("\nRecent entries:")
        print("-" * 60)
        for ipo_name, status, category, year, created_at in cursor.fetchall():
            print(f"{ipo_name[:30]:30} | {status:15} | {category:8} | {year} | {created_at}")
        
        # Sample raw data
        cursor.execute("""
            SELECT ipo_name, raw_data 
            FROM ipo_summary_data 
            WHERE year = 2025 
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        if result:
            ipo_name, raw_data = result
            print(f"\nSample raw data for '{ipo_name}':")
            print("-" * 60)
            try:
                parsed_data = json.loads(raw_data)
                print(json.dumps(parsed_data, indent=2)[:500] + "...")
            except:
                print(raw_data[:500] + "...")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    view_ipo_data()
