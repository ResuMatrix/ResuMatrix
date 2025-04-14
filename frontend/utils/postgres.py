import psycopg2
import csv
import os

# Postgres Upload
def upload_csv_to_postgres(csv_file_path, db_params):
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    with open(csv_file_path, 'r', encoding='utf-8') as f:
        next(f)  # Skip header
        reader = csv.reader(f)
        for row in reader:
            cursor.execute("INSERT INTO resumes_data (header) VALUES (%s)", (row[0],))
    conn.commit()
    cursor.close()
    conn.close()
