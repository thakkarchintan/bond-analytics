import mysql.connector
import logging
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

db_host = os.getenv("HOST")
db_user = os.getenv("USER")
db_password = os.getenv("PASSWORD")
db_name = os.getenv("DATABASE_NAME")

def create_database():
    """Create the database if it does not exist."""
    logging.info("Attempting to create/check database...")
    try:
        with mysql.connector.connect(host=db_host, user=db_user, password=db_password) as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
                logging.info(f"Database `{db_name}` is ready.")
    except mysql.connector.Error as err:
        logging.error(f"Error creating database: {err}")

def create_tables():
    """Create necessary tables inside the database."""
    logging.info("Checking/creating `User_Data` table...")
    try:
        with mysql.connector.connect(host=db_host, user=db_user, password=db_password, database=db_name) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS User_Data (
                        Email VARCHAR(255) PRIMARY KEY,
                        Formula_Table VARCHAR(255) UNIQUE
                    )
                """)
                logging.info("Table `User_Data` is ready.")
    except mysql.connector.Error as err:
        logging.error(f"Error creating tables: {err}")

def create_formula_table(table_name):
    """Create a table for storing user formulas if it does not exist."""
    logging.info(f"Checking/creating formula table `{table_name}`...")
    try:
        with mysql.connector.connect(host=db_host, user=db_user, password=db_password, database=db_name) as conn:
            with conn.cursor() as cursor:
                query = f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        Id INT AUTO_INCREMENT PRIMARY KEY,
                        Formula_Name VARCHAR(255) UNIQUE,
                        Formula VARCHAR(255)
                    )
                """
                cursor.execute(query)
                logging.info(f"Formula table `{table_name}` is ready.")
    except mysql.connector.Error as err:
        logging.error(f"Error creating formula table `{table_name}`: {err}")

def insert_user(email, table_name):
    """Insert a new user into the User_Data table if not exists."""
    logging.info(f"Attempting to insert user `{email}` with table `{table_name}`...")
    try:
        with mysql.connector.connect(host=db_host, user=db_user, password=db_password, database=db_name) as conn:
            with conn.cursor() as cursor:
                cursor.execute("USE {}".format(db_name))

                cursor.execute(
                    "INSERT IGNORE INTO User_Data (Email, Formula_Table) VALUES (%s, %s)",
                    (email, table_name),
                )

                if cursor.rowcount > 0:
                    logging.info(f"User `{email}` inserted successfully.")
                    conn.commit()
                    create_formula_table(table_name)
                else:
                    logging.info(f"User `{email}` already exists, skipping insertion.")

    except mysql.connector.Error as err:
        logging.error(f"Error inserting user `{email}`: {err}")

def insert_formula(table_name, formula_name, formula):
    """Insert a new formula into the user's formula table."""
    logging.info(f"Attempting to insert formula `{formula_name}` into `{table_name}`...")
    try:
        with mysql.connector.connect(host=db_host, user=db_user, password=db_password, database=db_name) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"INSERT INTO {table_name} (Formula_Name, Formula) VALUES (%s, %s)",
                    (formula_name, formula),
                )
                conn.commit()
                logging.info(f"Formula `{formula_name}` inserted into `{table_name}` successfully.")
    except mysql.connector.Error as err:
        logging.error(f"Error inserting formula `{formula_name}`: {err}")

def delete_user(email):
    """Delete a user and their associated formula table."""
    logging.info(f"Attempting to delete user `{email}` and their associated data...")
    try:
        with mysql.connector.connect(host=db_host, user=db_user, password=db_password, database=db_name) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT Formula_Table FROM User_Data WHERE Email = %s", (email,))
                result = cursor.fetchone()

                if result:
                    table_name = result[0]
                    cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                    logging.info(f"Deleted table `{table_name}`.")

                    cursor.execute("DELETE FROM User_Data WHERE Email = %s", (email,))
                    conn.commit()
                    logging.info(f"User `{email}` deleted successfully.")
                else:
                    logging.info(f"User `{email}` not found, nothing to delete.")
    except mysql.connector.Error as err:
        logging.error(f"Error deleting user `{email}`: {err}")

def check_email_exists(email):
    """Check if a user email exists in the database."""
    logging.info(f"Checking if email `{email}` exists in database...")
    try:
        with mysql.connector.connect(host=db_host, user=db_user, password=db_password, database=db_name) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(1) FROM User_Data WHERE Email = %s", (email,))
                result = cursor.fetchone()
                exists = result[0] > 0
                logging.info(f"Email `{email}` existence check: {exists}")
                return exists
    except mysql.connector.Error as err:
        logging.error(f"Error checking email `{email}` existence: {err}")
        return False

def fetch_all_data(table_name):
    """Fetch all data from the specified table in the database."""
    logging.info(f"Fetching all data from table `{table_name}`...")
    try:
        with mysql.connector.connect(host=db_host, user=db_user, password=db_password, database=db_name) as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(f"SELECT * FROM {table_name}")
                data = cursor.fetchall()
                logging.info(f"Fetched {len(data)} records from `{table_name}`.")
                return data
    except mysql.connector.Error as err:
        logging.error(f"Error fetching data from `{table_name}`: {err}")
        return None
    
def check_formula_exists(table_name,formula_name):
    """Check if a formula name exists in the database."""
    logging.info(f"Checking if email `{formula_name}` exists in database...")
    try:
        with mysql.connector.connect(host=db_host, user=db_user, password=db_password, database=db_name) as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(1) FROM {table_name} WHERE Formula_Name = %s", (formula_name,))
                result = cursor.fetchone()
                exists = result[0] > 0
                logging.info(f"Email `{formula_name}` existence check: {exists}")
                return exists
    except mysql.connector.Error as err:
        logging.error(f"Error checking email `{formula_name}` existence: {err}")
        return False