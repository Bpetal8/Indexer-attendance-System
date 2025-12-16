import sqlite3
from datetime import datetime, timedelta
import hashlib
import getpass

class AttendanceSystem:
    def __init__(self):
        self.db_path = "attendance.db"
        self.init_database()

    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Employees table
        c.execute('''CREATE TABLE IF NOT EXISTS employees
        (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
                  employee_id TEXT UNIQUE NOT NULL,
                  name TEXT NOT NULL,
                  pin_hash TEXT NOT NULL,
                  department TEXT,
                  added_date TEXT
        )''')

        # Attendance Table
        c.execute('''CREATE TABLE IF NOT EXISTS attendance
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  employee_id TEXT,
                  employee_name TEXT,
                  date TEXT,
                  shift TEXT,
                  time TEXT,
                  UNIQUE(employee_id, date, shift))''')
        
        conn.commit()
        conn.close()
        print("✓ Database initialized successfully")

    def hash_pin(self, pin):
        """Hash PIN for secure storage"""
        return hashlib.sha256(pin.encode()).hexdigest()

    def register_employee(self, employee_id, name, pin, department="Data Entry"):
        """Register a new employee"""
        if len(pin) < 4:
            return False, "PIN must be at least 4 digits"
        
        pin_hash = self.hash_pin(pin)

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        try:
            c.execute("""INSERT INTO employees (employee_id, name, pin_hash, department, added_date)
                    VALUES (?, ?, ?, ?, ?)""",
                 (employee_id, name, pin_hash, department, 
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            return True, f"✓ Employee {name} (ID: {employee_id}) registered successfully"
        except sqlite3.IntegrityError:  #This catches the duplicate
            return False, f"✗ Employee ID {employee_id} already exists"
        finally:
            conn.close()

    def verify_employee(self, employee_id, pin):
        """Verify employee ID and PIN"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("SELECT name, pin_hash FROM employees WHERE employee_id = ?", 
             (employee_id,))
        result = c.fetchone()
        conn.close()

        if result is None:
            return False, None, "Employee ID not found"
        
        name, stored_hash = result

        if self.hash_pin(pin) == stored_hash:
            return True, name, "Verified"
        else:
            return False, None, "Incorrect PIN"
    
    def mark_attendance(self, employee_id, shift):
        """Mark attendance for an employee"""
        today = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")

        # Get employee name
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("SELECT name FROM employees WHERE employee_id = ?", (employee_id,))
        result = c.fetchone()

        if result is None:
            conn.close()
            return False, "Employee not found"
        
        employee_name = result[0]

        try:
            c.execute("""INSERT INTO attendance (employee_id, employee_name, date, shift, time)
                    VALUES (?, ?, ?, ?, ?)""",
                 (employee_id, employee_name, today, shift, current_time))
            conn.commit()
            conn.close()
            return True, f"✓ Attendance marked for {employee_name} - {shift} shift at {current_time}"
        except sqlite3.IntegrityError:
            conn.close()
            return False, f"✗ {employee_name} already marked for {shift} shift today"
        
    def get_all_employees(self):
        """Get list of all employees"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("SELECT employee_id, name, department, added_date FROM employees ORDER BY name")
        employees = c.fetchall()
        conn.close()

        return employees
    
    def get_attendance_report(self, start_date=None, end_date=None):
        """Get attendance report for date range"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        if start_date and end_date:
            c.execute("""SELECT employee_id, employee_name, date, shift, time 
                    FROM attendance 
                    WHERE date BETWEEN ? AND ?
                    ORDER BY date DESC, time DESC""",
                 (start_date, end_date))
        else:
            c.execute("""SELECT employee_id, employee_name, date, shift, time 
                    FROM attendance 
                    ORDER BY date DESC, time DESC
                    LIMIT 50""")
        
        records = c.fetchall()
        conn.close()
        return records
        
    def get_today_attendance(self):
        """Get today's attendance"""
        today = datetime.now().strftime("%Y-%m-%d")

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("""SELECT employee_id, employee_name, shift, time 
                FROM attendance 
                WHERE date = ?
                ORDER BY time DESC""", (today,))
        
        records = c.fetchall()
        conn.close()
        return records
    
    def get_missed_days(self, employee_id, start_date, end_date):
        """Get days when employee was absent"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Get employee name
        c.execute("SELECT name FROM employees WHERE employee_id = ?", (employee_id,))
        result = c.fetchone()
        if result is None:
            conn.close()
            return None, "Employee not found"
        
        employee_name = result[0]

        # Get present dates
        c.execute("""SELECT DISTINCT date FROM attendance 
                WHERE employee_id = ? AND date BETWEEN ? AND ?""",
             (employee_id, start_date, end_date))
        
        present_dates = set(row[0] for row in c.fetchall())
        conn.close()

        # Generate all weekdays in range
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        all_dates = set()

        current = start
        while current <= end:
            # Skip weekends (Saturday=5, Sunday=6)
            if current.weekday() < 5:
                all_dates.add(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)

        missed_dates = sorted(all_dates - present_dates, reverse=True)
        return (employee_name, missed_dates), None

    def delete_employee(self, employee_id):
        """Delete an employee and their attendance records"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Check if employee exists
        c.execute("SELECT name FROM employees WHERE employee_id = ?", (employee_id,))
        result = c.fetchone()

        if result is None:
            conn.close()
            return False, "Employee not found"

        name = result[0]

        # Delete attendance records
        c.execute("DELETE FROM attendance WHERE employee_id = ?", (employee_id,))

        # Delete employee
        c.execute("DELETE FROM employees WHERE employee_id = ?", (employee_id,))

        conn.commit()
        conn.close()

        return True, f"✓ Employee {name} and all records deleted"


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