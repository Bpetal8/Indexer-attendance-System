import streamlit as st
from attendance_system import AttendanceSystem
import pandas as pd 
from datetime import datetime, timedelta
from pdf_utils import generate_attendance_pdf

#Page configuration
st.set_page_config(
    page_title="Indexers Attendance System",
    page_icon="",
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
if "show_reset_password" not in st.session_state:
    st.session_state.show_reset_password = False


system = AttendanceSystem()

# Cache dashboard data for performance
@st.cache_data(ttl=30)
def get_dashboard_data():
    return {
        'today': system.get_today_attendance(),
        'employees': system.get_all_employees()
    }

if not st.session_state.logged_in:

    st.markdown('<div class="main-header">Admin Login</div>', unsafe_allow_html=True)

    # ---- ADMIN SETUP (FIRST TIME ONLY) ----
    if not system.admin_exists():
        st.info("👋 **Welcome!** No admin account exists yet. Please create one to get started.")

        with st.form("setup_form"):
            st.markdown("### Create Admin Account")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            confirm = st.text_input("Confirm Password", type="password")

            submitted = st.form_submit_button(" Create Admin")

            if submitted:
                if not username or not password:
                    st.error("Fill all fields")
                elif password != confirm:
                    st.error("Passwords do not match")
                else:
                    success, msg = system.register_admin(username, password)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    # ---- NORMAL LOGIN ----
    else:
        if st.session_state.show_reset_password:
            st.markdown("### Reset Password")

            with st.form("reset_form"):
                user = st.text_input("Username")
                new_pass = st.text_input("New Password", type="password")
                confirm = st.text_input("Confirm Password", type="password")

                submitted = st.form_submit_button("Reset")

                if submitted:
                    if new_pass != confirm:
                        st.error("Passwords do not match")
                    else:
                        success, msg = system.reset_admin_password(user, new_pass)
                        if success:
                            st.success(msg)
                            st.session_state.show_reset_password = False
                            st.rerun()
                        else:
                            st.error(msg)

            if st.button("← Back to Login"):
                st.session_state.show_reset_password = False
                st.rerun()

        else:
            with st.form("login_form"):
                st.markdown("### Login")
                user = st.text_input("Username")
                pwd = st.text_input("Password", type="password")

                submitted = st.form_submit_button("Login")

                if submitted:
                    success, msg = system.verify_admin(user, pwd)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.admin_username = user
                        st.rerun()
                    else:
                        st.error(msg)

            if st.button(" Forgot Password?"):
                st.session_state.show_reset_password = True
                st.rerun()

    # HARD STOP — NOTHING BELOW RUNS
    st.stop()

# ---- SIDEBAR ----
st.sidebar.title(" Navigation")
st.sidebar.markdown(f"**Logged in as:** {st.session_state.admin_username}")
st.sidebar.markdown("---")

menu_items = [
    (" Dashboard", "dashboard"),
    (" Register Employee", "register"),
    (" Mark Attendance", "attendance"),
    (" Reports", "reports"),
    (" View Employees", "employees"),
    (" Missed Days", "missed"),
    (" Deactivate Employee", "deactivate"),
    (" Employee Archive", "archive")
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

/*  RESPONSIVENESS */
/* =========================
   Stack columns on mobile/tablet
========================= */
@media (max-width: 768px) {
    [data-testid="column"] {
        width: 100% !important;
        min-width: 100% !important;
    }
}

/* ← NEW: RADIO BUTTONS - MOBILE */
@media (max-width: 768px) {
    div[role="radiogroup"] {
        flex-direction: column !important;
    }
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
        df = pd.DataFrame(today_records, columns=["Employee ID", "Name", "Shift", "Time", "Status"])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No attendance records for today yet.")


elif page == "register":

    st.markdown("### Register New Employee")
    


    with st.form("register_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Full Name *", placeholder="")

        with col2:
            department = st.text_input("Department", value="Data Entry", disabled=True)

        submitted = st.form_submit_button(" Register Employee", use_container_width=True)

        if submitted:
            if not name:  # ← SIMPLIFIED
                st.error(" Please enter employee name")
            else:
                success, msg = system.register_employee(name, department)  # ← ONLY 2 PARAMS
                if success:
                    st.success(f" {msg}")
                    get_dashboard_data.clear()
                else:
                    st.error(f" {msg}")


elif page == "attendance":

    st.markdown("###  Mark Attendance")
    st.caption("Select employee and shift to mark attendance")
    
    # Show shift timings info
    st.info("""
    **Shift Timings:**
    -  Morning: 7:00 AM - 1:00 PM (Grace period: 8:00 AM)
    -  Afternoon: 2:00 PM - 8:00 PM (Grace period: 2:00 PM)
    
    *Attendance marked after grace period will be flagged as LATE*
    """)

    # Get all employees for dropdown
    employees = system.get_all_employees()

    if not employees:
        st.warning(" No employees registered yet. Please register employees first.")
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

            arrival_date = st.date_input(
                "Arrival Date",
                value=datetime.now().date()
            )

            arrival_time = st.time_input(
                "Arrival Time",
                value=datetime.now().replace(second=0, microsecond=0).time(),
                step=timedelta(minutes=1)
            )

            submitted = st.form_submit_button(
                f" Mark {shift} Attendance",
                use_container_width=True
            )

            if submitted:
                if not selected_employee:
                    st.error(" Please select an employee")

                else:
                    arrival_datetime = datetime.combine(arrival_date, arrival_time)

                    if arrival_datetime > datetime.now():
                        st.error(" Arrival time cannot be in the future")

                    else:
                        employee_id = employee_options[selected_employee]
                        success, msg = system.mark_attendance(
                            employee_id,
                            shift,
                            arrival_datetime
                        )

                        if success:
                            if "Late" in msg:
                                st.warning(f" {msg}")
                            else:
                                st.success(f" {msg}")
                            get_dashboard_data.clear()
                        else:
                            st.error(f" {msg}")
        
        # Show today's attendance below form
        st.markdown("---")
        st.markdown("###  Recent Attendance")
        
        today_records = system.get_today_attendance()
        if today_records:
            df = pd.DataFrame(today_records[:10], columns=["Employee ID", "Name", "Shift", "Time", "Status"])
            st.dataframe(df, use_container_width=True, hide_index=True)

elif page == "reports":

    st.markdown("### Attendance Reports")

    report_type = st.radio("Select Report Type", ["Today's Report", "Date Range Report"], horizontal=True)

    st.markdown("---")

    if report_type == "Today's Report":
        today_records = system.get_today_attendance()
        
        if today_records:
            df = pd.DataFrame(today_records, columns=["Employee ID", "Name", "Shift", "Time", "Status"])
            
            st.markdown(f"**Total Records:** {len(today_records)}")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Download button
            pdf = generate_attendance_pdf(
                title="Today's Attendance Report",
                columns=df.columns.tolist(),
                data=df.values.tolist()
            )

            st.download_button(
                label=" Download PDF",
                data=pdf,
                file_name=f"attendance_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
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
                df = pd.DataFrame(records, columns=["Employee ID", "Name", "Date", "Shift", "Time", "Status"])
                
                st.markdown(f"**Total Records:** {len(records)}")
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Download button
                pdf = generate_attendance_pdf(
                    title=f"Attendance Report ({start_date} to {end_date})",
                    columns=df.columns.tolist(),
                    data=df.values.tolist()
                )

                st.download_button(
                    label=" Download PDF",
                    data=pdf,
                    file_name=f"attendance_{start_date}_{end_date}.pdf",
                    mime="application/pdf",
                    use_container_width=True
)
            else:
                st.info("No records found for this date range.")


elif page == "employees":

    st.markdown("###  All Registered Employees")

    employees = system.get_all_employees()
    
    if not employees:
        st.info("No employees registered yet.")
    else:
        df = pd.DataFrame(employees, columns=["Employee ID", "Name", "Department", "Registered Date"])
        
        st.markdown(f"**Total Employees:** {len(employees)}")
        
        # Search
        search = st.text_input("🔍 Search by Name or ID", placeholder="Type to search...")
        
        if search:
            df = df[
                df["Name"].str.contains(search, case=False) | 
                df["Employee ID"].str.contains(search, case=False)
            ]

        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("## Edit Employee")

        # Select employee to edit
        options = {f"{e[1]} ({e[0]})": e for e in employees}
        selected = st.selectbox("Select Employee to Edit", list(options.keys()))

        selected_emp = options[selected]
        emp_id = selected_emp[0]
        current_name = selected_emp[1]
        current_dept = selected_emp[2]

        new_name = st.text_input("Full Name", value=current_name)
        new_dept = st.text_input("Department", value=current_dept, disabled=True)

        if st.button(" Save", use_container_width=True):
            success, msg = system.update_employee(emp_id, new_name, new_dept)
            if success:
                st.success(msg)
                get_dashboard_data.clear()
                st.rerun()
            else:
                st.error(msg)

        st.markdown("---")

        # Download
        pdf = generate_attendance_pdf(
            title="Employee List",
            columns=df.columns.tolist(),
            data=df.values.tolist()
        )

        st.download_button(
            label=" Download Employee List",
            data=pdf,
            file_name="employees.pdf",
            mime="application/pdf",
            use_container_width=True
        )


elif page == "missed":

    st.markdown("###  Check Missed Days")
    with st.form("missed_days_form"):
        # Get all employees for dropdown
        employees = system.get_all_employees()
        
        if not employees:
            st.warning(" No employees registered yet.")
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
            
            submitted = st.form_submit_button(" Check Missed Days", use_container_width=True)
            
            if submitted:
                employee_id = employee_options[selected_employee]
                
                result, error = system.get_missed_days(
                    employee_id,
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d")
                )
                
                if error:
                    st.error(f" {error}")
                else:
                    name, missed_dates = result
                    
                    st.success(f" Report for **{name}** (ID: {employee_id})")
                    st.info(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
                    
                    if missed_dates:
                        st.warning(f" **Total Missed Days:** {len(missed_dates)}")
                        
                        df = pd.DataFrame(missed_dates, columns=["Date"])
                        df["Day"] = pd.to_datetime(df["Date"]).dt.day_name()
                        
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        st.success(" No missed days! Perfect attendance!")

elif page == "deactivate":

    st.markdown("### Deactivate Employee")
    st.warning(" Deactivated employees will not appear in lists and cannot mark attendance.")

    with st.form("deactivate_form"):
        # Get all employees for dropdown
        employees = system.get_all_employees()
        
        if not employees:
            st.warning(" No active employees.")
            st.form_submit_button("Deactivate", disabled=True)
        else:
            employee_options = {f"{emp[1]} ({emp[0]})": emp[0] for emp in employees}
            
            selected_employee = st.selectbox(
                "Select Employee to Deactivate",
                options=list(employee_options.keys())
            )
            
            confirm = st.checkbox("I understand this will deactivate the employee (not delete)")
            
            submitted = st.form_submit_button(" Deactivate Employee", use_container_width=True)
            
            if submitted:
                if not confirm:
                    st.error(" Please confirm the action")
                else:
                    employee_id = employee_options[selected_employee]
                    success, msg = system.deactivate_employee(employee_id)
                    
                    if success:
                        st.success(f" {msg}")
                        get_dashboard_data.clear()
                        st.rerun()
                    else:
                        st.error(f" {msg}")

elif page == "archive":

    st.markdown("### Employee Archive")
    st.info(" These employees have been deactivated. You can reactivate them at any time.")

    inactive_employees = system.get_inactive_employees()
    
    if inactive_employees:
        df = pd.DataFrame(inactive_employees, columns=["Employee ID", "Name", "Department", "Registered Date"])
        
        st.markdown(f"**Total Deactivated Employees:** {len(inactive_employees)}")
        
        # Search functionality
        search = st.text_input("🔍 Search by Name or ID", placeholder="Type to search...")
        
        if search:
            df_display = df[
                df["Name"].str.contains(search, case=False) | 
                df["Employee ID"].str.contains(search, case=False)
            ]
        else:
            df_display = df
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("### Reactivate Employee")
        
        with st.form("reactivate_form"):
            employee_options = {f"{emp[1]} ({emp[0]})": emp[0] for emp in inactive_employees}
            
            selected_employee = st.selectbox(
                "Select Employee to Reactivate",
                options=list(employee_options.keys())
            )
            
            confirm = st.checkbox("I want to reactivate this employee")
            
            submitted = st.form_submit_button(" Reactivate Employee", use_container_width=True)
            
            if submitted:
                if not confirm:
                    st.error(" Please confirm the action")
                else:
                    employee_id = employee_options[selected_employee]
                    success, msg = system.reactivate_employee(employee_id)
                    
                    if success:
                        st.success(f" {msg}")
                        get_dashboard_data.clear()
                        st.rerun()
                    else:
                        st.error(f" {msg}")
    else:
        st.success(" No deactivated employees. All employees are active!")
# Footer
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align: center; color: #6c757d; padding: 1rem;'>
        <small>Indexers Attendance System v2.0 | Logged in as: {st.session_state.admin_username} | Azul Tech © 2026</small>
    </div>
    """,
    unsafe_allow_html=True
)