import sqlite3
from datetime import datetime, timedelta
import hashlib
import os
import psycopg2
from psycopg2 import errors, pool

# trigger streamlit restart
class AttendanceSystem:
    def __init__(self):
        # Detect cloud database (Postgres)
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
            if self.connection_pool:
                try:
                    return self.connection_pool.getconn()
                except Exception as e:
                    print(f"Pool connection failed, using direct: {e}")
                    return psycopg2.connect(
                        os.environ["DATABASE_URL"],
                        sslmode="require"
                    )
            else:
                return psycopg2.connect(
                    os.environ["DATABASE_URL"],
                    sslmode="require"
                )
        else:
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
                c.execute("""
                    CREATE TABLE IF NOT EXISTS employees (
                        id SERIAL PRIMARY KEY,
                        employee_id TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        pin_hash TEXT NOT NULL,
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
                c.execute("""
                    CREATE TABLE IF NOT EXISTS employees (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        employee_id TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        pin_hash TEXT NOT NULL,
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

    def hash_pin(self, pin):
        return hashlib.sha256(pin.encode()).hexdigest()

    # ---------------- EMPLOYEES ----------------

    def register_employee(self, employee_id, name, pin, department="Data Entry"):
        if len(pin) < 4:
            return False, "PIN must be at least 4 digits"

        pin_hash = self.hash_pin(pin)
        conn = self.get_connection()
        c = conn.cursor()

        try:
            c.execute(
                f"""INSERT INTO employees
                    (employee_id, name, pin_hash, department, added_date)
                    VALUES ({self.placeholders(5)})""",
                (
                    employee_id,
                    name,
                    pin_hash,
                    department,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
            )
            conn.commit()
            return True, f"✓ Employee {name} (ID: {employee_id}) registered successfully"
        except (sqlite3.IntegrityError, errors.UniqueViolation):
            conn.rollback()
            return False, f"✗ Employee ID {employee_id} already exists"
        except Exception as e:
            conn.rollback()
            return False, f"✗ Registration failed: {str(e)}"
        finally:
            self.close_connection(conn)
    
    def verify_employee(self, employee_id, pin):
        conn = self.get_connection()
        c = conn.cursor()

        try:
            c.execute(
                f"SELECT name, pin_hash FROM employees WHERE employee_id = {self.q()}",
                (employee_id,)
            )
            result = c.fetchone()

            if not result:
                return False, None, "Employee ID not found"

            name, stored_hash = result
            return (
                True,
                name,
                "Verified"
            ) if self.hash_pin(pin) == stored_hash else (
                False,
                None,
                "Incorrect PIN"
            )
        finally:
            self.close_connection(conn)

    # ---------------- ATTENDANCE ----------------

    def mark_attendance(self, employee_id, shift):
        today = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")

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

            employee_name = result[0]

            c.execute(
                f"""INSERT INTO attendance
                    (employee_id, employee_name, date, shift, time)
                    VALUES ({self.placeholders(5)})""",
                (
                    employee_id,
                    employee_name,
                    today,
                    shift,
                    current_time
                )
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


def main_menu():
    """Main menu interface"""
    system = AttendanceSystem()
    
    while True:
        print("\n" + "="*60)
        print("           SMART ATTENDANCE SYSTEM (PIN/ID)")
        print("="*60)
        print("1. Register New Employee")
        print("2. Mark Attendance (Morning Shift)")
        print("3. Mark Attendance (Afternoon Shift)")
        print("4. View Today's Attendance")
        print("5. View Attendance Report (Date Range)")
        print("6. Check Missed Days")
        print("7. View All Employees")
        print("8. Delete Employee")
        print("9. Exit")
        print("="*60)

        choice = input("\nEnter choice (1-9): ").strip()

        if choice == '1':
            print("\n--- Register New Employee ---")
            employee_id = input("Enter Employee ID (e.g., EMP001): ").strip().upper()
            name = input("Enter Full Name: ").strip()
            department = input("Enter Department (or press Enter for 'General'): ").strip() or "General"
            pin = input("Enter 4-digit PIN: ").strip()
            pin_confirm = input("Confirm PIN: ").strip()

            if pin != pin_confirm:
                print("✗ PINs do not match!")
                continue
            
            success, msg = system.register_employee(employee_id, name, pin, department)
            print(msg)

        elif choice == '2' or choice == '3':
            shift = "Morning" if choice == '2' else "Afternoon"
            print(f"\n--- {shift} Shift Attendance ---")

            employee_id = input("Enter Employee ID: ").strip().upper()
            pin = input("Enter PIN: ").strip()

            verified, name, msg = system.verify_employee(employee_id, pin)
            
            if verified:
                print(f"✓ Welcome, {name}!")
                success, msg = system.mark_attendance(employee_id, shift)
                print(msg)
            else:
                print(f"✗ {msg}")

        elif choice == '4':
            print("\n--- Today's Attendance ---")
            records = system.get_today_attendance()

            if records:
                print("\n" + "="*70)
                print(f"{'ID':<12} {'Name':<20} {'Shift':<12} {'Time':<12}")
                print("="*70)
                for record in records:
                    print(f"{record[0]:<12} {record[1]:<20} {record[2]:<12} {record[3]:<12}")
                print("="*70)
                print(f"Total: {len(records)} attendance records today")
            else:
                print("No attendance records for today")

        elif choice == '5':
            print("\n--- Attendance Report ---")
            start = input("Start date (YYYY-MM-DD): ").strip()
            end = input("End date (YYYY-MM-DD): ").strip()

            records = system.get_attendance_report(start, end)

            if records:
                print("\n" + "="*80)
                print(f"{'ID':<12} {'Name':<20} {'Date':<12} {'Shift':<12} {'Time':<12}")
                print("="*80)
                for record in records:
                    print(f"{record[0]:<12} {record[1]:<20} {record[2]:<12} {record[3]:<12} {record[4]:<12}")
                print("="*80)
                print(f"Total: {len(records)} records")
            else:
                print("No records found for this date range")

        elif choice == '6':
            print("\n--- Check Missed Days ---")
            employee_id = input("Enter Employee ID: ").strip().upper()
            start = input("Start date (YYYY-MM-DD): ").strip()
            end = input("End date (YYYY-MM-DD): ").strip()

            result, error = system.get_missed_days(employee_id, start, end)

            if error:
                print(f"✗ {error}")
            else:
                name, missed = result
                print(f"\nMissed days for {name} (ID: {employee_id}):")
                print(f"Period: {start} to {end}")

                if missed:
                    print(f"\n{'Date':<15} {'Day':<10}")
                    print("-" * 25)
                    for date in missed:
                        day_name = datetime.strptime(date, "%Y-%m-%d").strftime("%A")
                        print(f"{date:<15} {day_name:<10}")
                    print(f"\nTotal missed days: {len(missed)}")      
                else:
                    print("✓ No missed days! Perfect attendance!")

        elif choice == '7':
            print("\n--- All Employees ---")
            employees = system.get_all_employees()

            if employees:
                print("\n" + "="*80)
                print(f"{'ID':<12} {'Name':<25} {'Department':<20} {'Registered':<20}")
                print("="*80)
                for emp in employees:
                    print(f"{emp[0]:<12} {emp[1]:<25} {emp[2]:<20} {emp[3]:<20}")
                print("="*80)
                print(f"Total employees: {len(employees)}")
            else:
                print("No employees registered yet")

        elif choice == '8':
            print("\n--- Delete Employee ---")
            employee_id = input("Enter Employee ID to delete: ").strip().upper()
            confirm = input(f"Are you sure you want to delete {employee_id}? (yes/no): ").strip().lower()

            if confirm == 'yes':
                success, msg = system.delete_employee(employee_id)
                print(msg)
            else:
                print("Deletion cancelled")

        elif choice == '9':
            print("\n✓ Thank you for using the Attendance System!")
            print("Goodbye!\n")
            break
        
        else:
            print("✗ Invalid choice. Please try again.")


if __name__ == "__main__":
    print("\nStarting Attendance System...")
    main_menu()