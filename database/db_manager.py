# database/db_manager.py

import sqlite3
import json
import pyodbc # Import pyodbc for SQL Server connectivity
from config import USE_SQL_SERVER, SQLITE_DB_NAME, SQL_SERVER_DB_CONFIG

class DatabaseManager:
    """
    Manages database operations for storing IPO data, supporting both SQLite and SQL Server.
    """
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.use_sql_server = USE_SQL_SERVER
        self.db_name = SQLITE_DB_NAME if not self.use_sql_server else SQL_SERVER_DB_CONFIG['database']

    def connect(self):
        """Establishes a connection to the configured database."""
        try:
            if self.use_sql_server:
                conn_str = (
                    f"DRIVER={SQL_SERVER_DB_CONFIG['driver']};"
                    f"SERVER={SQL_SERVER_DB_CONFIG['server']};"
                    f"DATABASE={SQL_SERVER_DB_CONFIG['database']};"
                    f"UID={SQL_SERVER_DB_CONFIG['username']};"
                    f"PWD={SQL_SERVER_DB_CONFIG['password']}"
                )
                self.conn = pyodbc.connect(conn_str)
                print(f"Connected to SQL Server database: {SQL_SERVER_DB_CONFIG['database']}")
            else:
                self.conn = sqlite3.connect(SQLITE_DB_NAME)
                print(f"Connected to SQLite database: {SQLITE_DB_NAME}")
            self.cursor = self.conn.cursor()
        except (sqlite3.Error, pyodbc.Error) as e:
            print(f"Error connecting to database: {e}")
            self.conn = None
            self.cursor = None

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            print("Database connection closed.")

    def create_table(self):
        """
        Creates the 'ipo_master_data' table if it doesn't exist, adapting for the chosen database.
        """
        if not self.conn:
            print("Database not connected. Cannot create table.")
            return

        # Common column definitions
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
            "subject_to_sauda TEXT"
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

        if self.use_sql_server:
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
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='ipo_master_data' and xtype='U')
            CREATE TABLE ipo_master_data (
                {", ".join(sql_server_columns)}
            );
            """
        else:
            # SQLite specific column definitions (already TEXT)
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS ipo_master_data (
                {", ".join(columns)}
            );
            """

        try:
            self.cursor.execute(create_table_sql)
            self.conn.commit()
            print("Table 'ipo_master_data' created or already exists.")
        except (sqlite3.Error, pyodbc.Error) as e:
            print(f"Error creating table: {e}")

    def insert_or_update_ipo_data(self, ipo_data):
        """
        Inserts new IPO data or updates existing data if ipo_id already exists.
        Args:
            ipo_data (dict): A dictionary containing all IPO details.
                             Keys must match table column names.
        """
        if not self.conn:
            print("Database not connected. Cannot insert/update data.")
            return False

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
        if self.use_sql_server:
            # For SQL Server, fetch column names from INFORMATION_SCHEMA
            self.cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ipo_master_data' AND TABLE_SCHEMA = '{SQL_SERVER_DB_CONFIG['database']}'")
            column_names = [row[0] for row in self.cursor.fetchall()]
        else:
            # For SQLite, use PRAGMA
            self.cursor.execute("PRAGMA table_info(ipo_master_data);")
            column_names = [col[1] for col in self.cursor.fetchall()]

        # Filter ipo_data to only include keys that are actual columns
        filtered_ipo_data = {k: v for k, v in ipo_data.items() if k in column_names}

        # Handle 'ipo_id' separately for the WHERE clause
        ipo_id_value = filtered_ipo_data.get('ipo_id')
        if ipo_id_value is None:
            print("Error: IPO ID is missing for data insertion/update.")
            return False

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
            self.cursor.execute("SELECT ipo_id FROM ipo_master_data WHERE ipo_id = ?", (ipo_id_value,))
            existing_record = self.cursor.fetchone()

            if existing_record:
                # Update existing record
                if update_set: # Only update if there are fields other than ipo_id
                    self.cursor.execute(f"UPDATE ipo_master_data SET {update_set} WHERE ipo_id = ?", update_values)
                    print(f"Updated IPO ID: {ipo_id_value}")
                else:
                    print(f"No updatable fields for IPO ID: {ipo_id_value}. Skipping update.")
            else:
                # Insert new record
                insert_values = list(filtered_ipo_data.values())
                self.cursor.execute(f"INSERT INTO ipo_master_data ({cols}) VALUES ({placeholders})", insert_values)
                print(f"Inserted new IPO ID: {ipo_id_value}")
            
            self.conn.commit()
            return True
        except (sqlite3.Error, pyodbc.Error) as e:
            print(f"Error inserting/updating data for IPO ID {ipo_id_value}: {e}")
            self.conn.rollback()
            return False

    def get_ipo_by_id(self, ipo_id):
        """Fetches an IPO record by its ID."""
        if not self.conn:
            print("Database not connected. Cannot fetch data.")
            return None
        try:
            self.cursor.execute("SELECT * FROM ipo_master_data WHERE ipo_id = ?", (ipo_id,))
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
            query = "SELECT * FROM ipo_master_data"
            if limit:
                # Syntax for LIMIT differs between SQLite and SQL Server
                if self.use_sql_server:
                    query = f"SELECT TOP {limit} * FROM ipo_master_data"
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

