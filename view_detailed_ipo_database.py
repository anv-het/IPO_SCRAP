#!/usr/bin/env python3
"""
View Detailed IPO Database
Script to view and analyze the detailed IPO data from the master table
"""

import sys
import os
import json
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager

class DetailedIPOViewer:
    """Viewer for detailed IPO data"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def connect_database(self):
        """Connect to the database"""
        self.db_manager.connect()
        return self.db_manager.conn is not None
    
    def close_database(self):
        """Close database connection"""
        if self.db_manager:
            self.db_manager.close()
    
    def get_database_stats(self):
        """Get basic statistics about the detailed IPO database"""
        try:
            # Total records
            self.db_manager.cursor.execute("SELECT COUNT(*) FROM ipo_master_data")
            total_records = self.db_manager.cursor.fetchone()[0]
            
            # Records by category
            self.db_manager.cursor.execute("""
                SELECT ipo_category, COUNT(*) as count 
                FROM ipo_master_data 
                WHERE ipo_category IS NOT NULL 
                GROUP BY ipo_category 
                ORDER BY count DESC
            """)
            category_stats = self.db_manager.cursor.fetchall()
            
            # Recent entries
            self.db_manager.cursor.execute("""
                SELECT ipo_id, company_full_name_scraped, ipo_category, scraping_date
                FROM ipo_master_data 
                ORDER BY scraping_date DESC 
                LIMIT 10
            """)
            recent_entries = self.db_manager.cursor.fetchall()
            
            return {
                'total_records': total_records,
                'category_stats': category_stats,
                'recent_entries': recent_entries
            }
            
        except Exception as e:
            print(f"Error getting database stats: {e}")
            return None
    
    def search_ipo_by_name(self, search_term: str):
        """Search for IPOs by company name"""
        try:
            query = """
                SELECT ipo_id, company_full_name_scraped, ipo_category, 
                       issue_price_band, issue_size_cr, listing_date
                FROM ipo_master_data 
                WHERE company_full_name_scraped LIKE ? 
                ORDER BY company_full_name_scraped
            """
            
            self.db_manager.cursor.execute(query, (f"%{search_term}%",))
            results = self.db_manager.cursor.fetchall()
            
            return results
            
        except Exception as e:
            print(f"Error searching IPOs: {e}")
            return []
    
    def get_ipo_details(self, ipo_id: str):
        """Get detailed information for a specific IPO"""
        try:
            query = "SELECT * FROM ipo_master_data WHERE ipo_id = ?"
            self.db_manager.cursor.execute(query, (ipo_id,))
            result = self.db_manager.cursor.fetchone()
            
            if result:
                # Get column names
                columns = [description[0] for description in self.db_manager.cursor.description]
                # Create dictionary
                ipo_data = dict(zip(columns, result))
                return ipo_data
            
            return None
            
        except Exception as e:
            print(f"Error getting IPO details: {e}")
            return None
    
    def display_stats(self):
        """Display database statistics"""
        stats = self.get_database_stats()
        
        if not stats:
            print("❌ Failed to get database statistics")
            return
        
        print("=" * 60)
        print("DETAILED IPO DATABASE STATISTICS")
        print("=" * 60)
        
        print(f"📊 Total detailed records: {stats['total_records']}")
        
        if stats['category_stats']:
            print("\n📈 Records by category:")
            print("-" * 30)
            for category, count in stats['category_stats']:
                print(f"{category}: {count} records")
        
        if stats['recent_entries']:
            print("\n🕐 Recent entries:")
            print("-" * 60)
            for entry in stats['recent_entries']:
                ipo_id, company_name, category, scraping_date = entry
                print(f"ID: {ipo_id} | {company_name} | {category} | {scraping_date}")
        
        print("=" * 60)
    
    def display_ipo_details(self, ipo_id: str):
        """Display detailed information for a specific IPO"""
        ipo_data = self.get_ipo_details(ipo_id)
        
        if not ipo_data:
            print(f"❌ No detailed data found for IPO ID: {ipo_id}")
            return
        
        print("=" * 80)
        print(f"DETAILED IPO INFORMATION - {ipo_data.get('company_full_name_scraped', 'N/A')}")
        print("=" * 80)
        
        # Basic Information
        print("🏢 BASIC INFORMATION:")
        print(f"   IPO ID: {ipo_data.get('ipo_id', 'N/A')}")
        print(f"   Company Name: {ipo_data.get('company_full_name_scraped', 'N/A')}")
        print(f"   Category: {ipo_data.get('ipo_category', 'N/A')}")
        print(f"   Issue Price: {ipo_data.get('issue_price_band', 'N/A')}")
        print(f"   Issue Size: {ipo_data.get('issue_size_cr', 'N/A')}")
        print(f"   Lot Size: {ipo_data.get('shares_per_lot', 'N/A')}")
        
        # Dates
        print("\n📅 IMPORTANT DATES:")
        print(f"   Open Date: {ipo_data.get('ipo_open_date', 'N/A')}")
        print(f"   Close Date: {ipo_data.get('ipo_close_date', 'N/A')}")
        print(f"   Listing Date: {ipo_data.get('listing_date', 'N/A')}")
        print(f"   Basis of Allotment: {ipo_data.get('basis_of_allotment_date', 'N/A')}")
        
        # GMP Information
        print("\n💰 GMP INFORMATION:")
        print(f"   Latest GMP: {ipo_data.get('gmp_latest', 'N/A')}")
        print(f"   Estimated Listing Price: {ipo_data.get('estimated_listing_price', 'N/A')}")
        
        # About Company
        if ipo_data.get('about_company_text') and ipo_data['about_company_text'] != 'N/A':
            print("\n📋 ABOUT COMPANY:")
            about_text = ipo_data['about_company_text']
            if len(about_text) > 300:
                about_text = about_text[:300] + "..."
            print(f"   {about_text}")
        
        # Contact Information
        print("\n📞 CONTACT INFORMATION:")
        try:
            if ipo_data.get('contact_company_address_json'):
                contact_data = json.loads(ipo_data['contact_company_address_json'])
                if isinstance(contact_data, dict):
                    for key, value in contact_data.items():
                        if value:
                            print(f"   {key}: {value}")
        except:
            pass
        
        # Additional Information
        print("\n🔗 ADDITIONAL INFORMATION:")
        print(f"   Detail URL: {ipo_data.get('detail_url', 'N/A')}")
        print(f"   Logo URL: {ipo_data.get('company_logo_url', 'N/A')}")
        print(f"   Scraped Date: {ipo_data.get('scraping_date', 'N/A')}")
        
        print("=" * 80)


def main():
    """Main interactive function"""
    viewer = DetailedIPOViewer()
    
    try:
        # Connect to database
        if not viewer.connect_database():
            print("❌ Failed to connect to database. Exiting.")
            return
        
        print("✅ Database connected successfully")
        
        while True:
            print("\n" + "=" * 50)
            print("DETAILED IPO DATABASE VIEWER")
            print("=" * 50)
            print("1. View database statistics")
            print("2. Search IPO by company name")
            print("3. View specific IPO details")
            print("4. Exit")
            
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == "1":
                viewer.display_stats()
            
            elif choice == "2":
                search_term = input("Enter company name to search: ").strip()
                if search_term:
                    results = viewer.search_ipo_by_name(search_term)
                    if results:
                        print(f"\n🔍 Found {len(results)} results:")
                        print("-" * 80)
                        for result in results:
                            ipo_id, company_name, category, price_band, size, listing_date = result
                            print(f"ID: {ipo_id} | {company_name} | {category} | {price_band} | {size}")
                    else:
                        print("❌ No results found")
                else:
                    print("❌ Please enter a search term")
            
            elif choice == "3":
                ipo_id = input("Enter IPO ID: ").strip()
                if ipo_id:
                    viewer.display_ipo_details(ipo_id)
                else:
                    print("❌ Please enter an IPO ID")
            
            elif choice == "4":
                print("👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice")
    
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        viewer.close_database()


if __name__ == "__main__":
    main()
