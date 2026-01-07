import sqlite3
from datetime import datetime, timedelta
import hashlib
import os
import psycopg2
from psycopg2 import errors, pool

# ENV Mode
IS_PRODUCTION = os.environ.get("ENV") == "production"

# trigger streamlit restart
class AttendanceSystem:
    def __init__(self):
        # Detect cloud database (Postgres)
        if IS_PRODUCTION:
            if "DATABASE_URL" not in os.environ:
                raise RuntimeError("❌ DATABASE_URL is missing in production!")
            self.use_postgres = True
        else:
            self.use_postgres = "DATABASE_URL" in os.environ

        # DEBUG
        print("USING POSTGRES:", self.use_postgres)

        # SQLite path (local only)
        self.db_path = "attendance.db"

        self.connection_pool = None
        if self.use_postgres:
            try:
                self.connection_pool = pool.SimpleConnectionPool(
                   1, 10,  # min and max connections
                os.environ["DATABASE_URL"],
                sslmode="require"  
                )
                print("✓ PostgreSQL connection pool created")
            except Exception as e:
                print(f"✗ Failed to create connection pool: {e}")
        self.init_database()

    # ---------------- DATABASE CONNECTION ----------------

    def get_connection(self):
        if self.use_postgres:
            ...
        else:
            if IS_PRODUCTION:
                raise RuntimeError("❌ SQLite is forbidden in production")
            return sqlite3.connect(self.db_path, check_same_thread=False)
    
    def close_connection(self, conn):
        """Properly close or return connection to pool"""
        if self.use_postgres and self.connection_pool:
            self.connection_pool.putconn(conn)
        else:
            conn.close()

    # Placeholder helper
    def q(self):
        return "%s" if self.use_postgres else "?"

    def placeholders(self, n):
        return ", ".join([self.q()] * n)

    # ---------------- DATABASE INIT ----------------

    def init_database(self):
        conn = self.get_connection()
        c = conn.cursor()

        try:
            if self.use_postgres:
                # ADD THIS ADMINS TABLE FIRST ↓
                c.execute("""
                    CREATE TABLE IF NOT EXISTS admins (
                        id SERIAL PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        created_at TEXT
                    );
                """)
                
                # THEN MODIFY EMPLOYEES TABLE (remove pin_hash) ↓
                c.execute("""
                    CREATE TABLE IF NOT EXISTS employees (
                        id SERIAL PRIMARY KEY,
                        employee_id TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        department TEXT,
                        added_date TEXT
                    );
                """)

                c.execute("""
                    CREATE TABLE IF NOT EXISTS attendance (
                        id SERIAL PRIMARY KEY,
                        employee_id TEXT,
                        employee_name TEXT,
                        date TEXT,
                        shift TEXT,
                        time TEXT,
                        UNIQUE(employee_id, date, shift)
                    );
                """)
            else:
                # ADD THIS ADMINS TABLE FIRST ↓
                c.execute("""
                    CREATE TABLE IF NOT EXISTS admins (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        created_at TEXT
                    );
                """)
                
                # THEN MODIFY EMPLOYEES TABLE (remove pin_hash) ↓
                c.execute("""
                    CREATE TABLE IF NOT EXISTS employees (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        employee_id TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        department TEXT,
                        added_date TEXT
                    );
                """)

                c.execute("""
                    CREATE TABLE IF NOT EXISTS attendance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        employee_id TEXT,
                        employee_name TEXT,
                        date TEXT,
                        shift TEXT,
                        time TEXT,
                        UNIQUE(employee_id, date, shift)
                    );
                """)

            conn.commit()
            print("✓ Database initialized successfully")
        except Exception as e:
            print(f"✗ Database initialization failed: {e}")
            raise
        finally:
            self.close_connection(conn)

    # ---------------- SECURITY ----------------

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    # ---------------- ADMIN FUNCTIONS ----------------

    def register_admin(self, username, password):
        """Register a new admin"""
        if len(password) < 6:
            return False, "Password must be at least 6 characters"

        password_hash = self.hash_password(password)
        conn = self.get_connection()
        c = conn.cursor()

        try:
            c.execute(
                f"""INSERT INTO admins (username, password_hash, created_at)
                    VALUES ({self.placeholders(3)})""",
                (username, password_hash, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            conn.commit()
            return True, f"✓ Admin {username} registered successfully"
        except (sqlite3.IntegrityError, errors.UniqueViolation):
            conn.rollback()
            return False, f"✗ Username {username} already exists"
        except Exception as e:
            conn.rollback()
            return False, f"✗ Registration failed: {str(e)}"
        finally:
            self.close_connection(conn)

    def verify_admin(self, username, password):
        """Verify admin credentials"""
        conn = self.get_connection()
        c = conn.cursor()

        try:
            c.execute(
                f"SELECT password_hash FROM admins WHERE username = {self.q()}",
                (username,)
            )
            result = c.fetchone()

            if not result:
                return False, "Invalid username or password"

            stored_hash = result[0]
            if self.hash_password(password) == stored_hash:
                return True, "Login successful"
            else:
                return False, "Invalid username or password"
        finally:
            self.close_connection(conn)

    def reset_admin_password(self, username, new_password):
        """Reset admin password"""
        if len(new_password) < 6:
            return False, "Password must be at least 6 characters"
        
        conn = self.get_connection()
        c = conn.cursor()
        
        try:
            # Check if admin exists
            c.execute(
                f"SELECT username FROM admins WHERE username = {self.q()}",
                (username,)
            )
            result = c.fetchone()
            
            if not result:
                return False, f"✗ Admin '{username}' not found"
            
            # Update password
            new_hash = self.hash_password(new_password)
            c.execute(
                f"UPDATE admins SET password_hash = {self.q()} WHERE username = {self.q()}",
                (new_hash, username)
            )
            conn.commit()
            return True, f"✓ Password reset successfully for {username}"
        
        except Exception as e:
            conn.rollback()
            return False, f"✗ Password reset failed: {str(e)}"
        finally:
            self.close_connection(conn)


    def list_all_admins(self):
        """List all admin usernames (helpful for password reset)"""
        conn = self.get_connection()
        c = conn.cursor()
        
        try:
            c.execute("SELECT username, created_at FROM admins ORDER BY created_at")
            rows = c.fetchall()
            return rows
        finally:
            self.close_connection(conn)

    def admin_exists(self):
        """Check if any admin exists"""
        conn = self.get_connection()
        c = conn.cursor()

        try:
            c.execute("SELECT COUNT(*) FROM admins")
            count = c.fetchone()[0]
            return count > 0
        finally:
            self.close_connection(conn)

    # ---------------- EMPLOYEES ----------------

    def get_next_employee_id(self):
        """Auto-generate next employee ID"""
        conn = self.get_connection()
        c = conn.cursor()

        try:
            c.execute("SELECT employee_id FROM employees ORDER BY id DESC LIMIT 1")
            result = c.fetchone()

            if not result:
                return "EMP001"
            
            # Extract number from last ID (e.g., EMP001 -> 1)
            last_id = result[0]
            try:
                number = int(last_id.replace("EMP", ""))
                next_number = number + 1
                return f"EMP{next_number:03d}"
            except:
                return "EMP001"
        finally:
            self.close_connection(conn)

    def register_employee(self, name, department="Data Entry"):
        """Register employee with auto-generated ID (no PIN)"""
        if not name or not name.strip():
            return False, "Employee name is required"

        employee_id = self.get_next_employee_id()  # ← AUTO-GENERATE ID
        conn = self.get_connection()
        c = conn.cursor()

        try:
            c.execute(
                f"""INSERT INTO employees (employee_id, name, department, added_date)
                    VALUES ({self.placeholders(4)})""",  # ← Changed from 5 to 4
                (employee_id, name.strip(), department, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            conn.commit()
            return True, f"✓ Employee {name} registered with ID: {employee_id}"
        except Exception as e:
            conn.rollback()
            return False, f"✗ Registration failed: {str(e)}"
        finally:
            self.close_connection(conn)
    
    def get_employee_by_id(self, employee_id):
        """Get employee details by ID"""
        conn = self.get_connection()
        c = conn.cursor()

        try:
            c.execute(
                f"SELECT employee_id, name, department FROM employees WHERE employee_id = {self.q()}",
                (employee_id,)
            )
            result = c.fetchone()
            return result
        finally:
            self.close_connection(conn)

    # ---------------- ATTENDANCE ----------------

    def mark_attendance(self, employee_id, shift):
        """Mark attendance (no PIN verification needed)"""
        today = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")

        conn = self.get_connection()
        c = conn.cursor()

        try:  # ← Add try block
            c.execute(
                f"SELECT name FROM employees WHERE employee_id = {self.q()}",
                (employee_id,)
            )
            result = c.fetchone()

            if not result:
                return False, "Employee not found"  # ← No conn.close()

            employee_name = result[0]

            c.execute(
                f"""INSERT INTO attendance
                    (employee_id, employee_name, date, shift, time)
                    VALUES ({self.placeholders(5)})""",
                (employee_id, employee_name, today, shift, current_time)
            )
            conn.commit()
            return True, f"✓ Attendance marked for {employee_name} - {shift} shift"
        except (sqlite3.IntegrityError, errors.UniqueViolation):
            conn.rollback()
            return False, f"✗ Attendance already marked for {shift} shift today"
        except Exception as e:
            conn.rollback()
            return False, f"✗ Failed to mark attendance: {str(e)}"
        finally:
            self.close_connection(conn)

    # ---------------- REPORTS ----------------

    def get_all_employees(self):
        conn = self.get_connection()
        c = conn.cursor()

        try:
            c.execute(
                "SELECT employee_id, name, department, added_date FROM employees ORDER BY name"
            )
            rows = c.fetchall()
            return rows
        finally:
            self.close_connection(conn)

    def get_today_attendance(self):
        today = datetime.now().strftime("%Y-%m-%d")

        conn = self.get_connection()
        c = conn.cursor()

        try:
            c.execute(
                f"""SELECT employee_id, employee_name, shift, time
                    FROM attendance
                    WHERE date = {self.q()}
                    ORDER BY time DESC""",
                (today,)
            )
            rows = c.fetchall()
            return rows
        finally:
            self.close_connection(conn)

    def get_attendance_report(self, start_date, end_date):
        conn = self.get_connection()
        c = conn.cursor()

        try:
            c.execute(
                f"""SELECT employee_id, employee_name, date, shift, time
                    FROM attendance
                    WHERE date BETWEEN {self.q()} AND {self.q()}
                    ORDER BY date DESC, time DESC""",
                (start_date, end_date)
            )
            rows = c.fetchall()
            return rows
        finally:
            self.close_connection(conn)

    def get_missed_days(self, employee_id, start_date, end_date):
        conn = self.get_connection()
        c = conn.cursor()

        try:
            c.execute(
                f"SELECT name FROM employees WHERE employee_id = {self.q()}",
                (employee_id,)
            )
            result = c.fetchone()

            if not result:
                return None, "Employee not found"

            employee_name = result[0]

            c.execute(
                f"""SELECT DISTINCT date FROM attendance
                    WHERE employee_id = {self.q()}
                    AND date BETWEEN {self.q()} AND {self.q()}""",
                (employee_id, start_date, end_date)
            )

            present_days = {row[0] for row in c.fetchall()}

            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")

            all_days = set()
            current = start
            while current <= end:
                if current.weekday() < 5:
                    all_days.add(current.strftime("%Y-%m-%d"))
                current += timedelta(days=1)

            missed = sorted(all_days - present_days)
            return (employee_name, missed), None
        finally:
            self.close_connection(conn)

    def delete_employee(self, employee_id):
        conn = self.get_connection()
        c = conn.cursor()

        try:
            c.execute(
                f"SELECT name FROM employees WHERE employee_id = {self.q()}",
                (employee_id,)
            )
            result = c.fetchone()

            if not result:
                return False, "Employee not found"

            name = result[0]

            c.execute(
                f"DELETE FROM attendance WHERE employee_id = {self.q()}",
                (employee_id,)
            )
            c.execute(
                f"DELETE FROM employees WHERE employee_id = {self.q()}",
                (employee_id,)
            )

            conn.commit()
            return True, f"✓ Employee {name} and all records deleted"
        except Exception as e:
            conn.rollback()
            return False, f"✗ Deletion failed: {str(e)}"
        finally:
            self.close_connection(conn)

    def __del__(self):
        """Cleanup connection pool on deletion"""
        if self.connection_pool:
            self.connection_pool.closeall()

