from datetime import datetime, timedelta, time
import os
import psycopg2
import bcrypt
from psycopg2 import errors, pool

SHIFT_CUTOFFS = {
    "Morning": time(8, 0),      
    "Afternoon": time(14, 0)    
}

# ENV Mode
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("❌ DATABASE_URL is not set")

# trigger streamlit restart
class AttendanceSystem:
    def __init__(self):
        try:
            self.connection_pool = pool.SimpleConnectionPool(
                1, 10,
                DATABASE_URL,
                sslmode="require"
            )
            print("✓ PostgreSQL connection pool created")
        except Exception as e:
            raise RuntimeError(f"❌ Failed to create PostgreSQL pool: {e}")

        self.init_database()

    # ---------------- DATABASE CONNECTION ----------------

    def get_connection(self):
        return self.connection_pool.getconn()

    def close_connection(self, conn):
        self.connection_pool.putconn(conn)

    # Placeholder helper
    def q(self):
        return "%s"

    def placeholders(self, n):
        return ", ".join(["%s"] * n)

    # ---------------- DATABASE INITIALIZATION ----------------

    def init_database(self):
        conn = self.get_connection()
        c = conn.cursor()

        try:
            c.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TEXT
                );
            """)

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
                    time TIME,
                    UNIQUE(employee_id, date, shift)
                );
            """)

            c.execute("""
                ALTER TABLE employees
                ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
            """)

            c.execute("""
                ALTER TABLE attendance
                ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'On Time';
            """)

            conn.commit()
            print("✓ Database initialized successfully")

        finally:
            self.close_connection(conn)
    # ---------------- ADMIN FUNCTIONS ----------------

    def register_admin(self, username, password):
        """Register a new admin"""
        if len(password) < 6:
            return False, "Password must be at least 6 characters"

        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

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
        except errors.UniqueViolation:
            conn.rollback()
            return False, f"✗ Username {username} already exists"
        except Exception as e:
            conn.rollback()
            return False, f"✗ Registration failed: {str(e)}"
        finally:
            self.close_connection(conn)

    def verify_admin(self, username, password):
        conn = self.get_connection()
        c = conn.cursor()

        try:
            c.execute("SELECT password_hash FROM admins WHERE username = %s", (username,))
            row = c.fetchone()

            if not row:
                return False, "Admin not found"

            stored_hash = row[0]

            if bcrypt.checkpw(password.encode(), stored_hash.encode()):
                return True, "Login successful"
            else:
                return False, "Wrong password"

        except Exception as e:
            return False, str(e)

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
            new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
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
            return True, f" Employee {name} registered with ID: {employee_id}"
        except Exception as e:
            conn.rollback()
            return False, f" Registration failed: {str(e)}"
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
        
    def update_employee(self, employee_id, new_name, new_department):
        """Update employee name and department"""
        if not new_name or not new_name.strip():
            return False, "Employee name cannot be empty"

        conn = self.get_connection()
        c = conn.cursor()

        try:
            # Check if employee exists and is active
            c.execute(
                "SELECT name FROM employees WHERE employee_id = %s AND is_active = TRUE",
                (employee_id,)
            )
            result = c.fetchone()

            if not result:
                return False, "Employee not found or inactive"

            # Update
            c.execute(
                """
                UPDATE employees
                SET name = %s, department = %s
                WHERE employee_id = %s
                """,
                (new_name.strip(), new_department.strip(), employee_id)
            )

            conn.commit()
            return True, f"✓ Employee updated successfully"

        except Exception as e:
            conn.rollback()
            return False, f"✗ Failed to update employee: {str(e)}"
        finally:
            self.close_connection(conn)

    def deactivate_employee(self, employee_id):
        conn = self.get_connection()
        c = conn.cursor()

        try:
            c.execute(
                "SELECT name FROM employees WHERE employee_id = %s AND is_active = TRUE",
                (employee_id,)
            )
            result = c.fetchone()

            if not result:
                return False, "Employee not found or already deactivated"

            name = result[0]

            c.execute(
                "UPDATE employees SET is_active = FALSE WHERE employee_id = %s",
                (employee_id,)
            )

            conn.commit()
            return True, f"✓ Employee {name} has been deactivated"

        except Exception as e:
            conn.rollback()
            return False, f"✗ Failed to deactivate employee: {str(e)}"
        finally:
            self.close_connection(conn)

    def get_inactive_employees(self):
        """Get all deactivated employees"""
        conn = self.get_connection()
        c = conn.cursor()

        try:
            c.execute("""
                SELECT employee_id, name, department, added_date 
                FROM employees 
                WHERE is_active = FALSE
                ORDER BY name
            """)
            rows = c.fetchall()
            return rows
        finally:
            self.close_connection(conn)

    def reactivate_employee(self, employee_id):
        """Reactivate a deactivated employee"""
        conn = self.get_connection()
        c = conn.cursor()

        try:
            c.execute(
                "SELECT name FROM employees WHERE employee_id = %s AND is_active = FALSE",
                (employee_id,)
            )
            result = c.fetchone()

            if not result:
                return False, "Employee not found or already active"

            name = result[0]

            c.execute(
                "UPDATE employees SET is_active = TRUE WHERE employee_id = %s",
                (employee_id,)
            )

            conn.commit()
            return True, f"✓ Employee {name} has been reactivated"

        except Exception as e:
            conn.rollback()
            return False, f"✗ Failed to reactivate employee: {str(e)}"
        finally:
            self.close_connection(conn)

    # ---------------- ATTENDANCE ----------------

    def mark_attendance(self, employee_id, shift, arrival_datetime):
        """
        Mark attendance using admin-provided arrival time
        """

        if shift not in SHIFT_CUTOFFS:
            return False, "Invalid shift selected"

        cutoff_time = SHIFT_CUTOFFS[shift]
        arrival_time_only = arrival_datetime.time()

        if shift == "Morning" and arrival_time_only >= time(13, 0):
            return False, "Invalid time for Morning shift"

        if shift == "Afternoon" and arrival_time_only < time(13, 0):
            return False, "Invalid time for Afternoon shift"

        status = "Late" if arrival_time_only > cutoff_time else "On Time"

        date_str = arrival_datetime.strftime("%Y-%m-%d")
        time_str = arrival_datetime.strftime("%H:%M:%S")

        conn = self.get_connection()
        c = conn.cursor()

        try:
            # Validate employee
            c.execute(
                "SELECT name FROM employees WHERE employee_id = %s AND is_active = TRUE",
                (employee_id,)
            )
            result = c.fetchone()

            if not result:
                return False, "Employee not found or inactive"

            employee_name = result[0]

            c.execute(
                """
                INSERT INTO attendance
                (employee_id, employee_name, date, shift, time, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (employee_id, employee_name, date_str, shift, time_str, status)
            )

            conn.commit()
            return True, f"✓ Attendance marked for {employee_name} ({status})"

        except errors.UniqueViolation:
            conn.rollback()
            return False, f"⚠️ Attendance already marked for {shift} shift on this date"

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
            c.execute("""
                SELECT employee_id, name, department, added_date 
                    FROM employees 
                    WHERE is_active = TRUE
                    ORDER BY name
            """)
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
                f"""SELECT employee_id, employee_name, shift, time, status
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
                f"""SELECT employee_id, employee_name, date, shift, time, status
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

