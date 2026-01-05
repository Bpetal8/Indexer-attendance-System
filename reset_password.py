from attendance_system import AttendanceSystem  # Change 'attendance_system' to your actual file name

system = AttendanceSystem()

# First, see what admins exist
admins = system.list_all_admins()
print("Existing admins:")
for username, created_at in admins:
    print(f"  - {username} (created: {created_at})")

# Then reset the password
username = input("\nEnter username to reset: ")
new_password = input("Enter new password: ")

success, message = system.reset_admin_password(username, new_password)
print(message)