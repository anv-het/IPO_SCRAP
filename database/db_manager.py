# database/db_manager.py

import sqlite3
import json
import pyodbc # Import pyodbc for SQL Server connectivity
from datetime import datetime
try:
    import pymongo
    from pymongo import MongoClient
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False
    
from config import (
    DATABASE_TYPE, USE_SQL_SERVER, USE_MONGODB, SQLITE_DATABASE_PATH, 
    SQL_SERVER_DB_CONFIG, MONGODB_CONFIG, IPO_SUMMARY_TABLE_NAME, 
    IPO_MASTER_TABLE_NAME
)

class DatabaseManager:
    """
    Manages database operations for storing IPO data, supporting SQLite, SQL Server, and MongoDB.
    """
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.db = None  # For MongoDB database object
        self.database_type = DATABASE_TYPE.lower()
        
        # Legacy support
        self.use_sql_server = USE_SQL_SERVER
        self.use_mongodb = USE_MONGODB
        
        # Table/Collection names
        self.summary_table_name = IPO_SUMMARY_TABLE_NAME
        self.master_table_name = IPO_MASTER_TABLE_NAME
        
        if self.database_type == 'sqlserver':
            self.db_name = SQL_SERVER_DB_CONFIG['database']
        elif self.database_type == 'mongodb':
            self.db_name = MONGODB_CONFIG['database']
        else:
            self.db_name = SQLITE_DATABASE_PATH

    def connect(self):
        """Establishes a connection to the configured database."""
        try:
            if self.database_type == 'sqlserver':
                conn_str = (
                    f"DRIVER={SQL_SERVER_DB_CONFIG['driver']};"
                    f"SERVER={SQL_SERVER_DB_CONFIG['server']};"
                    f"DATABASE={SQL_SERVER_DB_CONFIG['database']};"
                    f"UID={SQL_SERVER_DB_CONFIG['username']};"
                    f"PWD={SQL_SERVER_DB_CONFIG['password']}"
                )
                self.conn = pyodbc.connect(conn_str)
                self.cursor = self.conn.cursor()
                print(f"Connected to SQL Server database: {SQL_SERVER_DB_CONFIG['database']}")
                
            elif self.database_type == 'mongodb':
                if not PYMONGO_AVAILABLE:
                    raise ImportError("pymongo is required for MongoDB support. Install it with: pip install pymongo")
                
                # Connect to MongoDB
                self.conn = MongoClient(MONGODB_CONFIG['connection_string'])
                self.db = self.conn[MONGODB_CONFIG['database']]
                
                # Test connection
                self.conn.admin.command('ping')
                print(f"Connected to MongoDB database: {MONGODB_CONFIG['database']}")
                
            else:  # SQLite (default)
                self.conn = sqlite3.connect(SQLITE_DATABASE_PATH)
                self.cursor = self.conn.cursor()
                print(f"Connected to SQLite database: {SQLITE_DATABASE_PATH}")
                
        except Exception as e:
            print(f"Error connecting to {self.database_type} database: {e}")
            self.conn = None
            self.cursor = None
            self.db = None

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            print(f"Database connection closed.")
        self.conn = None
        self.cursor = None
        self.db = None

    def create_table(self):
        """
        Creates the IPO master table/collection, adapting for the chosen database.
        """
        if not self.conn and not self.db:
            print("Database not connected. Cannot create table.")
            return

        # MongoDB doesn't require explicit table creation, collections are created automatically
        if self.database_type == 'mongodb':
            print(f"MongoDB collections '{self.master_table_name}' will be created automatically when data is inserted.")
            return

        # Common column definitions for SQL databases
        columns = [
            "ipo_id TEXT PRIMARY KEY",
            "company_short_name_api TEXT",
            "company_full_name_scraped TEXT",
            "ipo_category TEXT",
            "detail_url TEXT",
            "scraping_date TEXT",
            "ipo_open_date TEXT",
            "ipo_close_date TEXT",
            "listing_date TEXT",
            "basis_of_allotment_date TEXT",
            "refunds_initiation_date TEXT",
            "credit_shares_demat_date TEXT",
            "ipo_open_date_status TEXT",
            "ipo_close_date_status TEXT",
            "listing_date_status TEXT",
            "about_company_text TEXT",
            "issue_price_band TEXT",
            "issue_size_cr TEXT",
            "shares_per_lot TEXT",
            "min_order_quantity TEXT",
            "min_hni_lots TEXT",
            "min_small_hni_lots TEXT",
            "min_big_hni_lots TEXT",
            "gmp_latest TEXT",
            "estimated_listing_price TEXT",
            "ipo_strengths_json TEXT",    # Stored as JSON string
            "ipo_objectives_json TEXT",   # Stored as JSON string
            "company_financials_json TEXT", # Stored as JSON string
            "peer_comparison_json TEXT",  # Stored as JSON string
            "contact_company_address_json TEXT", # Stored as JSON string
            "contact_ipo_registrar_json TEXT", # Stored as JSON string
            "contact_ipo_lead_manager_json TEXT", # Stored as JSON string
            "last_updated_on_page TEXT",
            "company_logo_url TEXT",
            "local_logo_path TEXT",
            "drhp_url TEXT",
            "rhp_url TEXT",
            "anchor_list_url TEXT",
            "retail_quota TEXT",
            "issue_type TEXT",
            "fresh_issue_amount TEXT",
            "face_value TEXT",
            "promoter_holding_pre_ipo TEXT",
            "promoter_holding_post_ipo TEXT",
            "listing_at TEXT",
            "gmp_comments TEXT",
            "subject_to_sauda TEXT",
            "allotment_status_url TEXT",
            "bse_code TEXT",
            "nse_code TEXT",
            "post_listing_details_table_html TEXT"
        ]

        # Specific JSON fields that might be larger, using NVARCHAR(MAX) for SQL Server
        json_columns = [
            "gmp_trend_history_json",
            "subscription_bidding_history_json",
            "subscription_share_allocation_json",
            "subscription_daywise_table_json",
            "subscription_shares_bid_amount_table_json",
            "gmp_latest_details_json"
        ]

        if self.database_type == 'sqlserver':
            # SQL Server specific column definitions
            sql_server_columns = []
            for col_def in columns:
                if "TEXT PRIMARY KEY" in col_def:
                    sql_server_columns.append(col_def.replace("TEXT PRIMARY KEY", "NVARCHAR(50) PRIMARY KEY"))
                elif "TEXT" in col_def:
                    if any(json_col in col_def for json_col in json_columns):
                        sql_server_columns.append(col_def.replace("TEXT", "NVARCHAR(MAX)"))
                    else:
                        sql_server_columns.append(col_def.replace("TEXT", "NVARCHAR(255)")) # Default string length
            
            create_table_sql = f"""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='{self.master_table_name}' and xtype='U')
            CREATE TABLE {self.master_table_name} (
                {", ".join(sql_server_columns)}
            );
            """
        else:
            # SQLite specific column definitions (already TEXT)
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {self.master_table_name} (
                {", ".join(columns)}
            );
            """

        try:
            self.cursor.execute(create_table_sql)
            self.conn.commit()
            print(f"Table '{self.master_table_name}' created or already exists.")
        except (sqlite3.Error, pyodbc.Error) as e:
            print(f"Error creating table: {e}")

    def insert_or_update_ipo_data(self, ipo_data):
        """
        Inserts new IPO data or updates existing data if ipo_id already exists.
        Args:
            ipo_data (dict): A dictionary containing all IPO details.
                             Keys must match table column names.
        """
        if not self.conn and not self.db:
            print("Database not connected. Cannot insert/update data.")
            return False

        # Get ipo_id for identification
        ipo_id_value = ipo_data.get('ipo_id')
        if ipo_id_value is None:
            print("Error: IPO ID is missing for data insertion/update.")
            return False

        # MongoDB implementation
        if self.database_type == 'mongodb':
            try:
                collection = self.db[self.master_table_name]
                
                # Prepare data for MongoDB
                mongo_data = dict(ipo_data)
                
                # Convert JSON strings to actual objects for MongoDB (optional)
                json_fields = [
                    'gmp_trend_history_json', 'ipo_strengths_json', 'ipo_objectives_json',
                    'subscription_bidding_history_json', 'subscription_share_allocation_json',
                    'subscription_daywise_table_json', 'subscription_shares_bid_amount_table_json',
                    'company_financials_json', 'peer_comparison_json',
                    'contact_company_address_json', 'contact_ipo_registrar_json',
                    'contact_ipo_lead_manager_json', 'gmp_latest_details_json'
                ]
                
                for field in json_fields:
                    if field in mongo_data and isinstance(mongo_data[field], str):
                        try:
                            mongo_data[field] = json.loads(mongo_data[field])
                        except (json.JSONDecodeError, TypeError):
                            pass  # Keep as string if not valid JSON
                
                # Add metadata
                mongo_data['updated_at'] = datetime.utcnow()
                
                # Upsert operation (update if exists, insert if not)
                result = collection.replace_one(
                    {"ipo_id": ipo_id_value}, 
                    mongo_data, 
                    upsert=True
                )
                
                if result.upserted_id:
                    print(f"Inserted new IPO ID: {ipo_id_value}")
                elif result.modified_count > 0:
                    print(f"Updated IPO ID: {ipo_id_value}")
                else:
                    print(f"No changes for IPO ID: {ipo_id_value}")
                
                return True
                
            except Exception as e:
                print(f"Error inserting/updating MongoDB data for IPO ID {ipo_id_value}: {e}")
                return False

        # SQL Database implementation (SQLite/SQL Server)
        # Prepare data for insertion/update
        # Convert lists/dicts to JSON strings and handle other data types
        json_fields = [
            'gmp_trend_history_json', 
            'ipo_strengths_json', 
            'ipo_objectives_json',
            'subscription_bidding_history_json', 
            'subscription_share_allocation_json',
            'subscription_daywise_table_json', 
            'subscription_shares_bid_amount_table_json',
            'company_financials_json', 
            'peer_comparison_json',
            'contact_company_address_json', 
            'contact_ipo_registrar_json',
            'contact_ipo_lead_manager_json',
            'gmp_latest_details_json',
        ]
        
        # Convert all data to appropriate types
        for key, value in ipo_data.items():
            if key in json_fields:
                if isinstance(value, (list, dict)):
                    ipo_data[key] = json.dumps(value, ensure_ascii=False)
                elif value is None:
                    ipo_data[key] = None
                elif isinstance(value, str):
                    ipo_data[key] = value
                else:
                    ipo_data[key] = str(value)
            elif isinstance(value, (list, dict)):
                # Convert any other list/dict to JSON string
                ipo_data[key] = json.dumps(value, ensure_ascii=False)
            elif value is None:
                ipo_data[key] = None
            elif isinstance(value, (int, float, str)):
                ipo_data[key] = value
            else:
                # Convert other types to string
                ipo_data[key] = str(value)

        # Get column names from the table for robust insertion
        # This is important because the actual columns might differ from the initial dict
        if self.database_type == 'sqlserver':
            # For SQL Server, fetch column names from INFORMATION_SCHEMA
            self.cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{self.master_table_name}' AND TABLE_SCHEMA = '{SQL_SERVER_DB_CONFIG['database']}'")
            column_names = [row[0] for row in self.cursor.fetchall()]
        else:
            # For SQLite, use PRAGMA
            self.cursor.execute(f"PRAGMA table_info({self.master_table_name});")
            column_names = [col[1] for col in self.cursor.fetchall()]

        # Filter ipo_data to only include keys that are actual columns
        filtered_ipo_data = {k: v for k, v in ipo_data.items() if k in column_names}

        # Construct SQL for insertion/update
        cols = ', '.join(filtered_ipo_data.keys())
        placeholders = ', '.join(['?' for _ in filtered_ipo_data.keys()])
        
        # Build UPDATE SET clause, excluding 'ipo_id' from the SET part
        update_set_parts = []
        update_values = []
        for k, v in filtered_ipo_data.items():
            if k != 'ipo_id':
                update_set_parts.append(f"{k} = ?")
                update_values.append(v)
        update_set = ', '.join(update_set_parts)
        update_values.append(ipo_id_value) # Add ipo_id for WHERE clause

        try:
            # Check if record exists
            self.cursor.execute(f"SELECT ipo_id FROM {self.master_table_name} WHERE ipo_id = ?", (ipo_id_value,))
            existing_record = self.cursor.fetchone()

            if existing_record:
                # Update existing record
                if update_set: # Only update if there are fields other than ipo_id
                    self.cursor.execute(f"UPDATE {self.master_table_name} SET {update_set} WHERE ipo_id = ?", update_values)
                    print(f"Updated IPO ID: {ipo_id_value}")
                else:
                    print(f"No updatable fields for IPO ID: {ipo_id_value}. Skipping update.")
            else:
                # Insert new record
                insert_values = list(filtered_ipo_data.values())
                self.cursor.execute(f"INSERT INTO {self.master_table_name} ({cols}) VALUES ({placeholders})", insert_values)
                print(f"Inserted new IPO ID: {ipo_id_value}")
            
            self.conn.commit()
            return True
        except (sqlite3.Error, pyodbc.Error) as e:
            print(f"Error inserting/updating data for IPO ID {ipo_id_value}: {e}")
            self.conn.rollback()
            return False

    def get_ipo_by_id(self, ipo_id):
        """Fetches an IPO record by its ID."""
        if not self.conn and not self.db:
            print("Database not connected. Cannot fetch data.")
            return None
            
        if self.database_type == 'mongodb':
            try:
                collection = self.db[self.master_table_name]
                result = collection.find_one({"ipo_id": ipo_id})
                return result
            except Exception as e:
                print(f"Error fetching MongoDB data for IPO ID {ipo_id}: {e}")
                return None
                
        try:
            self.cursor.execute(f"SELECT * FROM {self.master_table_name} WHERE ipo_id = ?", (ipo_id,))
            row = self.cursor.fetchone()
            if row:
                col_names = [description[0] for description in self.cursor.description]
                ipo_data = dict(zip(col_names, row))
                # Convert JSON strings back to lists/dicts
                for key in ipo_data:
                    if key.endswith('_json') and ipo_data[key] is not None and isinstance(ipo_data[key], str):
                        try:
                            ipo_data[key] = json.loads(ipo_data[key])
                        except json.JSONDecodeError:
                            pass # Keep as string if not valid JSON
                return ipo_data
            return None
        except (sqlite3.Error, pyodbc.Error) as e:
            print(f"Error fetching data for IPO ID {ipo_id}: {e}")
            return None

    def get_all_ipos(self, limit=None):
        """Fetches all IPO records, with an optional limit."""
        if not self.conn:
            print("Database not connected. Cannot fetch data.")
            return []
        try:
            if DATABASE_TYPE == 'mongodb':
                # MongoDB query
                cursor = self.db[IPO_MASTER_TABLE_NAME].find({})
                if limit:
                    cursor = cursor.limit(limit)
                
                all_ipos = []
                for doc in cursor:
                    # Remove MongoDB's _id field
                    doc.pop('_id', None)
                    all_ipos.append(doc)
                return all_ipos
            else:
                query = f"SELECT * FROM {IPO_MASTER_TABLE_NAME}"
                if limit:
                    # Syntax for LIMIT differs between SQLite and SQL Server
                    if self.use_sql_server:
                        query = f"SELECT TOP {limit} * FROM {IPO_MASTER_TABLE_NAME}"
                    else:
                        query += f" LIMIT {limit}"
                self.cursor.execute(query)
                rows = self.cursor.fetchall()
                if rows:
                    col_names = [description[0] for description in self.cursor.description]
                    all_ipos = []
                    for row in rows:
                        ipo_data = dict(zip(col_names, row))
                        for key in ipo_data:
                            if key.endswith('_json') and ipo_data[key] is not None and isinstance(ipo_data[key], str):
                                try:
                                    ipo_data[key] = json.loads(ipo_data[key])
                                except json.JSONDecodeError:
                                    pass
                        all_ipos.append(ipo_data)
                    return all_ipos
                return []
        except (sqlite3.Error, pyodbc.Error) as e:
            print(f"Error fetching all IPOs: {e}")
            return []

    def add_new_columns_if_not_exist(self):
        """
        Add new columns to the existing table if they don't exist.
        This handles schema evolution without losing existing data.
        """
        if not self.conn:
            print("Database not connected. Cannot add columns.")
            return

        # Skip for MongoDB as it doesn't have fixed schema
        if DATABASE_TYPE == 'mongodb':
            return

        # Define new columns to add
        new_columns = [
            "allotment_status_url TEXT",
            "bse_code TEXT", 
            "nse_code TEXT",
            "post_listing_details_table_html TEXT"
        ]

        try:
            # Check existing columns
            if self.use_sql_server:
                # SQL Server approach
                self.cursor.execute(f"""
                    SELECT COLUMN_NAME 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = '{IPO_MASTER_TABLE_NAME}'
                """)
            else:
                # SQLite approach
                self.cursor.execute(f"PRAGMA table_info({IPO_MASTER_TABLE_NAME})")
                
            existing_columns = [row[1] if not self.use_sql_server else row[0] for row in self.cursor.fetchall()]
            
            # Add missing columns
            for column_def in new_columns:
                column_name = column_def.split()[0]
                if column_name not in existing_columns:
                    try:
                        if self.use_sql_server:
                            # SQL Server syntax
                            alter_sql = f"ALTER TABLE {IPO_MASTER_TABLE_NAME} ADD {column_def.replace('TEXT', 'NVARCHAR(255)')}"
                        else:
                            # SQLite syntax
                            alter_sql = f"ALTER TABLE {IPO_MASTER_TABLE_NAME} ADD COLUMN {column_def}"
                        
                        self.cursor.execute(alter_sql)
                        self.conn.commit()
                        print(f"Added column: {column_name}")
                    except Exception as e:
                        print(f"Error adding column {column_name}: {e}")
                        
        except Exception as e:
            print(f"Error checking/adding columns: {e}")

