import psycopg2
import streamlit as st
import uuid
from datetime import date

def connect_db():
    """Establishes a connection to the PostgreSQL database with hard-coded details."""
    # IMPORTANT: Replace with your actual PostgreSQL connection details.
    db_params = {
        "host": "localhost",
        "database": "PMS",
        "user": "postgres",
        "password": "Asdfghjkl@2107"
    }
    try:
        conn = psycopg2.connect(**db_params)
        return conn
    except psycopg2.OperationalError as e:
        st.error(f"Error: Could not connect to the database. {e}")
        return None

def create_tables(conn):
    """Creates the projects and members tables if they don't exist."""
    with conn.cursor() as cur:
        # Projects Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                project_id VARCHAR(255) PRIMARY KEY,
                project_name VARCHAR(255) UNIQUE NOT NULL,
                start_date DATE,
                due_date DATE
            );
        """)
        # Members Table (including department and salary)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS members (
                member_id VARCHAR(255) PRIMARY KEY,
                member_name VARCHAR(255) NOT NULL,
                last_name VARCHAR(255) NOT NULL,
                role VARCHAR(255),
                department VARCHAR(255),
                start_date DATE,
                salary DECIMAL(10, 2)
            );
        """)
        # Project_Members Table (linking projects and members)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS project_members (
                project_id VARCHAR(255) REFERENCES projects(project_id) ON DELETE CASCADE,
                member_id VARCHAR(255) REFERENCES members(member_id) ON DELETE CASCADE,
                PRIMARY KEY (project_id, member_id)
            );
        """)
    conn.commit()

def create_project(conn, project_name, start_date, due_date):
    """Adds a new project to the database."""
    with conn.cursor() as cur:
        project_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO projects (project_id, project_name, start_date, due_date) VALUES (%s, %s, %s, %s)",
            (project_id, project_name, start_date, due_date)
        )
    conn.commit()

def add_team_member(conn, member_name, last_name, role, department, start_date, salary):
    """Adds a new team member to the database."""
    with conn.cursor() as cur:
        member_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO members (member_id, member_name, last_name, role, department, start_date, salary) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (member_id, member_name, last_name, role, department, start_date, salary)
        )
    conn.commit()

def get_all_projects(conn):
    """Fetches all project names from the database."""
    with conn.cursor() as cur:
        cur.execute("SELECT project_name FROM projects ORDER BY project_name")
        return [row[0] for row in cur.fetchall()]

def get_project_members(conn, project_name):
    """Fetches all members associated with a given project."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT m.member_id, m.member_name, m.last_name, m.department, m.start_date, m.salary
            FROM members m
            JOIN project_members pm ON m.member_id = pm.member_id
            JOIN projects p ON pm.project_id = p.project_id
            WHERE p.project_name = %s
            ORDER BY m.member_name
        """, (project_name,))
        return cur.fetchall()
