import streamlit as st
from attendance_system import AttendanceSystem
import pandas as pd 
from datetime import datetime, timedelta

#Page configuration
st.set_page_config(
    page_title="Indexers Attendance System",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
/* Hide Streamlit header */
header[data-testid="stHeader"] {
    display: none;
}

/* Hide Streamlit footer */
footer {
    display: none;
}

/* Remove top padding caused by header */
.block-container {
    padding-top: 1.5rem;
}
</style>
""", unsafe_allow_html=True)

# ---- SESSION STATE (INIT ONCE) ----
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "admin_username" not in st.session_state:
    st.session_state.admin_username = None
if "page" not in st.session_state:
    st.session_state.page = "dashboard"


system = AttendanceSystem()

# Cache dashboard data for performance
@st.cache_data(ttl=30)
def get_dashboard_data():
    return {
        'today': system.get_today_attendance(),
        'employees': system.get_all_employees()
    }

if not st.session_state.logged_in:
    st.markdown('<div class="main-header"> Admin Login</div>', unsafe_allow_html=True)
    
    # Check if admin exists
    if not system.admin_exists():
        st.info("👋 **Welcome!** No admin account exists yet. Please create one to get started.")
        
        with st.form("setup_form"):
            st.markdown("### Create Admin Account")
            username = st.text_input("Username", placeholder="Enter admin username")
            password = st.text_input("Password", type="password", placeholder="Minimum 6 characters")
            password_confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")
            
            submitted = st.form_submit_button("✅ Create Admin Account", use_container_width=True)
            
            if submitted:
                if not username or not password:
                    st.error("⚠️ Please fill in all fields")
                elif password != password_confirm:
                    st.error("⚠️ Passwords do not match")
                elif len(password) < 6:
                    st.error("⚠️ Password must be at least 6 characters")
                else:
                    success, msg = system.register_admin(username, password)
                    if success:
                        st.success(f"✅ {msg}")
                        st.info("Please login with your new credentials below.")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
    
    else:
        # Login form
        with st.form("login_form"):
            st.markdown("### Login to Continue")
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            submitted = st.form_submit_button(" Login", use_container_width=True)
            
            if submitted:
                if not username or not password:
                    st.error("⚠️ Please enter both username and password")
                else:
                    success, msg = system.verify_admin(username, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.admin_username = username
                        st.success(f"✅ Welcome back, {username}!")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    st.stop()


# ---- SIDEBAR ----
st.sidebar.title("📋 Navigation")
st.sidebar.markdown(f"**Logged in as:** {st.session_state.admin_username}")
st.sidebar.markdown("---")

menu_items = [
    (" Dashboard", "dashboard"),
    (" Register Employee", "register"),
    (" Mark Attendance", "attendance"),
    (" Reports", "reports"),
    (" View Employees", "employees"),
    (" Missed Days", "missed"),
    (" Delete Employee", "delete"),
]

for label, key in menu_items:
    if st.sidebar.button(label, key=f"nav_{key}", use_container_width=True):
        st.session_state.page = key
        st.rerun()

st.sidebar.markdown("---")

if st.sidebar.button(" Logout", use_container_width=True):  # ← CORRECT POSITION
    st.session_state.logged_in = False
    st.session_state.admin_username = None
    st.session_state.page = "dashboard"
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info(
    "**Indexers Attendance System**\n"
    "Data Entry Department\n"
    "Version 2.0"  # ← Also change to v2.0
)
page = st.session_state.page


st.markdown("""
<style>

/* =========================
   GLOBAL APP
========================= */
.stApp {
    background-color: #0F172A;
    color: #E5E7EB;
    font-family: "Inter", sans-serif;
}

/* =========================
   PAGE CONTAINER
========================= */
.block-container {
    background-color: #020617;
    padding: 2rem 2.2rem;
    border-radius: 22px;
    box-shadow: 0 25px 60px rgba(0,0,0,0.6);
}

/* =========================
   SIDEBAR
========================= */
section[data-testid="stSidebar"] {
    background-color: #020617;
    border-right: 1px solid #1E293B;
}

section[data-testid="stSidebar"] * {
    color: #E5E7EB !important;
}

/* Sidebar buttons */
section[data-testid="stSidebar"] button {
    background: transparent !important;
    border: none !important;
    text-align: left;
    padding: 0.75rem 1rem;
    margin-bottom: 0.35rem;
    border-radius: 14px;
    font-weight: 500;
    transition: background 0.2s ease, transform 0.2s ease;
}

/* FORCE SIDEBAR BUTTON TEXT COLOR */
section[data-testid="stSidebar"] div.stButton > button {
    color: #E5E7EB !important;
    background: transparent !important;
}

/* Hover text color */
section[data-testid="stSidebar"] div.stButton > button:hover {
    color: #FFFFFF !important;
}

/* Sidebar hover */
section[data-testid="stSidebar"] button:hover {
    background: rgba(37, 99, 235, 0.18) !important;
    transform: translateX(4px);
}

/* FORCE SIDEBAR VISIBLE */
section[data-testid="stSidebar"] {
    min-width: 260px !important;
    max-width: 260px !important;
    transform: translateX(0) !important;
    visibility: visible !important;
}

/* Prevent Streamlit from collapsing it */
section[data-testid="stSidebar"][aria-hidden="true"] {
    transform: translateX(0) !important;
    visibility: visible !important;
}

/* =========================
   MAIN HEADER
========================= */
.main-header {
    font-size: 2.4rem;
    font-weight: 800;
    background: linear-gradient(135deg, #60A5FA, #2563EB);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 2rem;
}

/* =========================
   STAT CARDS (INTERACTIVE SAFE)
========================= */
.stat-card {
    background-color: #020617;
    border: 1px solid #1E293B;
    padding: 1.5rem;
    border-radius: 18px;
    text-align: center;
    transition: all 0.25s ease;
}

.stat-card:hover {
    transform: translateY(-4px);
    border-color: #2563EB;
    box-shadow: 0 18px 45px rgba(37, 99, 235, 0.25);
}

/* =========================
   BUTTONS (PAGE CONTENT ONLY)
   SAFE — DOES NOT BREAK CARDS
========================= */
div.stButton > button {
    background: linear-gradient(135deg, #2563EB, #1D4ED8) !important;
    color: #FFFFFF !important;
    border-radius: 14px !important;
    border: none !important;
    font-weight: 600 !important;
    padding: 0.55rem 1.4rem !important;
    transition: all 0.25s ease !important;
}

div.stButton > button:hover {
    background: linear-gradient(135deg, #1D4ED8, #1E40AF) !important;
    box-shadow: 0 10px 28px rgba(37, 99, 235, 0.4);
}

/* =========================
   INPUTS & FORMS
========================= */
input, textarea, select {
    background-color: #020617 !important;
    color: #E5E7EB !important;
    border-radius: 12px !important;
    border: 1px solid #1E293B !important;
}

/* Input wrappers */
div[data-baseweb="input"],
div[data-baseweb="textarea"],
div[data-baseweb="select"] {
    background-color: #020617 !important;
}

/* Focus */
input:focus, textarea:focus {
    border-color: #2563EB !important;
}

/* Placeholder */
::placeholder {
    color: #64748B !important;
}

/* Labels */
label {
    color: #CBD5E1 !important;
    font-weight: 500;
}

/* =========================
   TABLES & DATAFRAMES
========================= */
div[data-testid="stDataFrame"] {
    background-color: #020617;
    border-radius: 16px;
    border: 1px solid #1E293B;
}

/* Header */
div[data-testid="stDataFrame"] thead th {
    background-color: #020617 !important;
    color: #93C5FD !important;
    border-bottom: 1px solid #1E293B !important;
    font-weight: 600;
}

/* Body */
div[data-testid="stDataFrame"] tbody td {
    background-color: #020617 !important;
    color: #E5E7EB !important;
    border-bottom: 1px solid #1E293B !important;
}

/* Row hover */
div[data-testid="stDataFrame"] tbody tr:hover td {
    background-color: #020617 !important;
}

/* =========================
   ALERTS / MESSAGES
========================= */
.stAlert {
    border-radius: 14px;
}

</style>
""", unsafe_allow_html=True)

# Main Header
st.markdown('<div class="main-header"> Indexers Attendance System</div>', unsafe_allow_html=True)

if page == "dashboard":

    st.markdown("## System Overview")
    st.caption("Real-time attendance statistics")

    st.markdown("---")
    st.markdown("###  Today's Overview")
    st.markdown(f"**Date:** {datetime.now().strftime('%A, %B %d, %Y')}")

    # Use cached data
    data = get_dashboard_data()
    today_records = data['today']
    all_employees = data['employees']

    morning_count = len([r for r in today_records if r[2] == "Morning"])
    afternoon_count = len([r for r in today_records if r[2] == "Afternoon"])
    total_employees = len(all_employees)
    present_today = len(set(r[0] for r in today_records))
    absent_today = total_employees - present_today

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"<div class='stat-card'><h3>{total_employees}</h3>Total Employees</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='stat-card'><h3 style='color: #10B981;'>{present_today}</h3>Present Today</div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='stat-card'><h3 style='color: #F59E0B;'>{morning_count}</h3>Morning Shift</div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='stat-card'><h3 style='color: #3B82F6;'>{afternoon_count}</h3>Afternoon Shift</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("###  Today's Attendance Records")

    if today_records:
        df = pd.DataFrame(today_records, columns=["Employee ID", "Name", "Shift", "Time"])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No attendance records for today yet.")


elif page == "register":

    st.markdown("### Register New Employee")
    st.caption("Employee ID will be auto-generated")  # ← ADD THIS


    with st.form("register_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Full Name *", placeholder="e.g., John Doe")

        with col2:
            department = st.text_input("Department", value="Data Entry")

        submitted = st.form_submit_button("✅ Register Employee", use_container_width=True)

        if submitted:
            if not name:  # ← SIMPLIFIED
                st.error("⚠️ Please enter employee name")
            else:
                success, msg = system.register_employee(name, department)  # ← ONLY 2 PARAMS
                if success:
                    st.success(f"✅ {msg}")
                    get_dashboard_data.clear()
                else:
                    st.error(f"❌ {msg}")


elif page == "attendance":

    st.markdown("### ✅ Mark Attendance")
    st.caption("Select employee and shift to mark attendance")

# Get all employees for dropdown
    employees = system.get_all_employees()

    if not employees:
        st.warning("⚠️ No employees registered yet. Please register employees first.")
    else:
        employee_options = {f"{emp[1]} ({emp[0]})": emp[0] for emp in employees}
        
        shift = st.radio("Select Shift", ["Morning", "Afternoon"], horizontal=True)

        st.markdown("---")

        with st.form("attendance_form"):
            selected_employee = st.selectbox(
                "Select Employee",
                options=list(employee_options.keys()),
                placeholder="Choose an employee..."
            )

            submitted = st.form_submit_button(f"✅ Mark {shift} Attendance", use_container_width=True)

            if submitted:
                if not selected_employee:
                    st.error("⚠️ Please select an employee")
                else:
                    employee_id = employee_options[selected_employee]
                    success, msg = system.mark_attendance(employee_id, shift)  # ← DIRECT CALL
                    
                    if success:
                        st.success(f"✅ {msg}")
                        get_dashboard_data.clear()
                    else:
                        st.warning(f"⚠️ {msg}")
        # Show today's attendance below form
        st.markdown("---")
        st.markdown("### Recent Attendance")
        
        today_records = system.get_today_attendance()
        if today_records:
            df = pd.DataFrame(today_records[:10], columns=["Employee ID", "Name", "Shift", "Time"])
            st.dataframe(df, use_container_width=True, hide_index=True)


elif page == "reports":

    st.markdown("### Attendance Reports")

    report_type = st.radio("Select Report Type", ["Today's Report", "Date Range Report"], horizontal=True)

    st.markdown("---")

    if report_type == "Today's Report":
        today_records = system.get_today_attendance()
        
        if today_records:
            df = pd.DataFrame(today_records, columns=["Employee ID", "Name", "Shift", "Time"])
            
            st.markdown(f"**Total Records:** {len(today_records)}")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"attendance_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("No attendance records for today.")

    else:  # Date Range Report
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=7))
        
        with col2:
            end_date = st.date_input("End Date", value=datetime.now())
        
        if st.button(" Generate Report", use_container_width=True):
            records = system.get_attendance_report(
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d")
            )
            
            if records:
                df = pd.DataFrame(records, columns=["Employee ID", "Name", "Date", "Shift", "Time"])
                
                st.markdown(f"**Total Records:** {len(records)}")
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Download button
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"attendance_{start_date}_{end_date}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.info("No records found for this date range.")


elif page == "employees":

    st.markdown("### All Registered Employees")

    employees = system.get_all_employees()
    
    if employees:
        df = pd.DataFrame(employees, columns=["Employee ID", "Name", "Department", "Registered Date"])
        
        st.markdown(f"**Total Employees:** {len(employees)}")
        
        # Search functionality
        search = st.text_input("🔍 Search by Name or ID", placeholder="Type to search...")
        
        if search:
            df = df[
                df["Name"].str.contains(search, case=False) | 
                df["Employee ID"].str.contains(search, case=False)
            ]
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Employee List",
            data=csv,
            file_name="employees.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("No employees registered yet.")


elif page == "missed":

    st.markdown("###  Check Missed Days")

    # REPLACE EVERYTHING BELOW WITH THIS ↓
    with st.form("missed_days_form"):
        # Get all employees for dropdown
        employees = system.get_all_employees()
        
        if not employees:
            st.warning("⚠️ No employees registered yet.")
            st.form_submit_button("Check", disabled=True)
        else:
            employee_options = {f"{emp[1]} ({emp[0]})": emp[0] for emp in employees}
            
            selected_employee = st.selectbox(
                "Select Employee",
                options=list(employee_options.keys())
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=7))
            
            with col2:
                end_date = st.date_input("End Date", value=datetime.now())
            
            submitted = st.form_submit_button("🔍 Check Missed Days", use_container_width=True)
            
            if submitted:
                employee_id = employee_options[selected_employee]
                
                result, error = system.get_missed_days(
                    employee_id,
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d")
                )
                
                if error:
                    st.error(f"❌ {error}")
                else:
                    name, missed_dates = result
                    
                    st.success(f"📊 Report for **{name}** (ID: {employee_id})")
                    st.info(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
                    
                    if missed_dates:
                        st.warning(f"⚠️ **Total Missed Days:** {len(missed_dates)}")
                        
                        df = pd.DataFrame(missed_dates, columns=["Date"])
                        df["Day"] = pd.to_datetime(df["Date"]).dt.day_name()
                        
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        st.success("✅ No missed days! Perfect attendance!")

elif page == "delete":

    st.markdown("### 🗑️ Delete Employee")
    st.warning("⚠️ **Warning:** This action will permanently delete the employee and all their attendance records!")

    with st.form("delete_form"):
        # Get all employees for dropdown
        employees = system.get_all_employees()
        
        if not employees:
            st.warning("⚠️ No employees to delete.")
            st.form_submit_button("Delete", disabled=True)
        else:
            employee_options = {f"{emp[1]} ({emp[0]})": emp[0] for emp in employees}
            
            selected_employee = st.selectbox(
                "Select Employee to Delete",
                options=list(employee_options.keys())
            )
            
            confirm = st.checkbox("I understand this action cannot be undone")
            
            submitted = st.form_submit_button("🗑️ Delete Employee", use_container_width=True)
            
            if submitted:
                if not confirm:
                    st.error("⚠️ Please confirm that you understand this action")
                else:
                    employee_id = employee_options[selected_employee]
                    success, msg = system.delete_employee(employee_id)
                    
                    if success:
                        st.success(f"✅ {msg}")
                        get_dashboard_data.clear()
                    else:
                        st.error(f"❌ {msg}")
# Footer
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align: center; color: #6c757d; padding: 1rem;'>
        <small>Indexers Attendance System v2.0 | Logged in as: {st.session_state.admin_username} | Azul Tech © 2025</small>
    </div>
    """,
    unsafe_allow_html=True
)