#!/usr/bin/env python3
"""
Database viewer for IPO Summary data
"""

import sqlite3
import json
from datetime import datetime
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DATABASE_TYPE, SQLITE_DATABASE_PATH, SQLSERVER_CONFIG, MONGODB_CONFIG, IPO_SUMMARY_TABLE_NAME
from database.db_manager import DatabaseManager

def view_ipo_data():
    """View and analyze IPO summary data in the database"""
    
    # Use the database manager for consistent connection handling
    db_manager = DatabaseManager()
    db_manager.connect()
    
    if not db_manager.conn:
        print("Failed to connect to database. Exiting.")
        return
    
    try:
        # Get basic statistics
        print("IPO SUMMARY DATABASE ANALYSIS")
        print("=" * 60)
        print(f"Database Type: {DATABASE_TYPE}")
        print(f"Table/Collection: {IPO_SUMMARY_TABLE_NAME}")
        print("-" * 60)
        
        # Total records
        if DATABASE_TYPE == 'mongodb':
            total_records = db_manager.db[IPO_SUMMARY_TABLE_NAME].count_documents({})
        else:
            db_manager.cursor.execute(f"SELECT COUNT(*) FROM {IPO_SUMMARY_TABLE_NAME}")
            total_records = db_manager.cursor.fetchone()[0]
        print(f"Total records: {total_records}")
        
        # Records by year
        if DATABASE_TYPE == 'mongodb':
            pipeline = [
                {"$group": {"_id": "$year", "count": {"$sum": 1}}},
                {"$sort": {"_id": -1}}
            ]
            year_results = list(db_manager.db[IPO_SUMMARY_TABLE_NAME].aggregate(pipeline))
        else:
            db_manager.cursor.execute(f"""
                SELECT year, COUNT(*) as count 
                FROM {IPO_SUMMARY_TABLE_NAME} 
                GROUP BY year 
                ORDER BY year DESC
            """)
            year_results = db_manager.cursor.fetchall()
        
        print("\nRecords by year:")
        print("-" * 30)
        if DATABASE_TYPE == 'mongodb':
            for result in year_results:
                print(f"Year {result['_id']}: {result['count']} records")
        else:
            for year, count in year_results:
                print(f"Year {year}: {count} records")
        
        # Status distribution
        if DATABASE_TYPE == 'mongodb':
            pipeline = [
                {"$group": {"_id": "$status", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            status_results = list(db_manager.db[IPO_SUMMARY_TABLE_NAME].aggregate(pipeline))
        else:
            db_manager.cursor.execute(f"""
                SELECT status, COUNT(*) as count 
                FROM {IPO_SUMMARY_TABLE_NAME} 
                GROUP BY status 
                ORDER BY count DESC
            """)
            status_results = db_manager.cursor.fetchall()
        
        print("\nStatus distribution:")
        print("-" * 30)
        if DATABASE_TYPE == 'mongodb':
            for result in status_results:
                status_display = result['_id'] if result['_id'] else "NULL"
                print(f"{status_display}: {result['count']} records")
        else:
            for status, count in status_results:
            status_display = status if status else "NULL"
            print(f"{status_display}: {count} records")
        
        # IPO categories
        if DATABASE_TYPE == 'mongodb':
            pipeline = [
                {"$group": {"_id": "$ipo_category", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            category_results = list(db_manager.db[IPO_SUMMARY_TABLE_NAME].aggregate(pipeline))
        else:
            db_manager.cursor.execute(f"""
                SELECT ipo_category, COUNT(*) as count 
                FROM {IPO_SUMMARY_TABLE_NAME} 
                GROUP BY ipo_category 
                ORDER BY count DESC
            """)
            category_results = db_manager.cursor.fetchall()
        
        print("\nIPO Categories:")
        print("-" * 30)
        if DATABASE_TYPE == 'mongodb':
            for result in category_results:
                category_display = result['_id'] if result['_id'] else "NULL"
                print(f"{category_display}: {result['count']} records")
        else:
            for category, count in category_results:
                category_display = category if category else "NULL"
                print(f"{category_display}: {count} records")
        
        # Listed IPOs with gains
        if DATABASE_TYPE == 'mongodb':
            # For MongoDB, we need to handle the data differently
            listed_ipos = list(db_manager.db[IPO_SUMMARY_TABLE_NAME].find(
                {"status": "Listed", "list_price": {"$ne": None}},
                {"ipo_name": 1, "list_price": 1, "list_gain": 1, "ipo_price": 1}
            ).limit(10))
        else:
            db_manager.cursor.execute(f"""
                SELECT ipo_name, list_price, list_gain, ipo_price 
                FROM {IPO_SUMMARY_TABLE_NAME} 
                WHERE status = 'Listed' AND list_price IS NOT NULL 
                ORDER BY CAST(REPLACE(list_gain, '%', '') AS REAL) DESC 
                LIMIT 10
            """)
            listed_ipos = db_manager.cursor.fetchall()
        
        print("\nTop 10 Listed IPOs by Gain:")
        print("-" * 60)
        if listed_ipos:
            if DATABASE_TYPE == 'mongodb':
                for ipo in listed_ipos:
                    ipo_name = ipo.get('ipo_name', 'N/A')
                    list_price = ipo.get('list_price', 'N/A')
                    list_gain = ipo.get('list_gain', 'N/A')
                    ipo_price = ipo.get('ipo_price', 'N/A')
                    print(f"{ipo_name[:40]:40} | List: ₹{list_price:>8} | Gain: {list_gain:>8} | IPO: ₹{ipo_price}")
            else:
                for ipo_name, list_price, list_gain, ipo_price in listed_ipos:
                    print(f"{ipo_name[:40]:40} | List: ₹{list_price:>8} | Gain: {list_gain:>8} | IPO: ₹{ipo_price}")
        else:
            print("No listed IPOs found with gain data")
        
        # Recent entries
        if DATABASE_TYPE == 'mongodb':
            recent_entries = list(db_manager.db[IPO_SUMMARY_TABLE_NAME].find(
                {},
                {"ipo_name": 1, "status": 1, "ipo_category": 1, "year": 1, "created_at": 1}
            ).sort("created_at", -1).limit(5))
        else:
            db_manager.cursor.execute(f"""
                SELECT ipo_name, status, ipo_category, year, created_at 
                FROM {IPO_SUMMARY_TABLE_NAME} 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            recent_entries = db_manager.cursor.fetchall()
        
        print("\nRecent entries:")
        print("-" * 60)
        if DATABASE_TYPE == 'mongodb':
            for entry in recent_entries:
                ipo_name = entry.get('ipo_name', 'N/A')
                status = entry.get('status', 'N/A')
                category = entry.get('ipo_category', 'N/A')
                year = entry.get('year', 'N/A')
                created_at = entry.get('created_at', 'N/A')
                print(f"{ipo_name[:30]:30} | {status:15} | {category:8} | {year} | {created_at}")
        else:
            for ipo_name, status, category, year, created_at in recent_entries:
                print(f"{ipo_name[:30]:30} | {status:15} | {category:8} | {year} | {created_at}")
        
        # Sample raw data
        if DATABASE_TYPE == 'mongodb':
            result = db_manager.db[IPO_SUMMARY_TABLE_NAME].find_one(
                {"year": 2025},
                {"ipo_name": 1, "raw_data": 1}
            )
        else:
            db_manager.cursor.execute(f"""
                SELECT ipo_name, raw_data 
                FROM {IPO_SUMMARY_TABLE_NAME} 
                WHERE year = 2025 
                LIMIT 1
            """)
            result = db_manager.cursor.fetchone()
        
        if result:
            if DATABASE_TYPE == 'mongodb':
                ipo_name = result.get('ipo_name', 'N/A')
                raw_data = result.get('raw_data', '')
            else:
                ipo_name, raw_data = result
                
            print(f"\nSample raw data for '{ipo_name}':")
            print("-" * 60)
            try:
                if isinstance(raw_data, str):
                    parsed_data = json.loads(raw_data)
                    print(json.dumps(parsed_data, indent=2)[:500] + "...")
                else:
                    print(str(raw_data)[:500] + "...")
            except:
                print(str(raw_data)[:500] + "...")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db_manager.close()

if __name__ == "__main__":
    view_ipo_data()
