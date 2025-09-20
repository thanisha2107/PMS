import streamlit as st
import pandas as pd
from backend_pms import (
    connect_db, create_tables, authenticate_user, create_goal, get_goals, update_goal_status,
    add_task, get_tasks_for_goal, get_employees_by_manager, provide_feedback, get_feedback_for_goal,
    update_task_status, update_task_progress, get_manager_for_employee
)
from datetime import date

# --- Page Configuration ---
st.set_page_config(
    page_title="Performance Management System",
    page_icon="📈",
    layout="wide"
)

# --- Session State Management ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None

# --- Main App Logic ---
conn = connect_db()
if conn:
    create_tables(conn)

def show_login_page():
    st.title("Performance Management System 📈")
    st.header("Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")

    if login_button:
        user = authenticate_user(conn, username, password)
        if user:
            st.session_state.authenticated = True
            st.session_state.user = user
            st.success("Login successful!")
            st.experimental_rerun()
        else:
            st.error("Invalid username or password.")

def show_manager_dashboard():
    st.sidebar.header(f"Welcome, {st.session_state.user['username']}!")
    st.sidebar.button("Logout", on_click=logout)
    
    st.title("Manager Dashboard 📊")
    st.write("View and manage goals for your employees.")

    tab1, tab2 = st.tabs(["Set Goals", "Track Progress & Feedback"])
    
    with tab1:
        st.header("Set a New Goal")
        employees = get_employees_by_manager(conn, st.session_state.user['user_id'])
        employee_map = {emp[1]: emp[0] for emp in employees}
        employee_names = list(employee_map.keys())

        if not employees:
            st.warning("You do not have any employees assigned to you.")
        else:
            with st.form("goal_form", clear_on_submit=True):
                selected_employee = st.selectbox("Select Employee", options=employee_names)
                goal_title = st.text_input("Goal Title")
                goal_desc = st.text_area("Goal Description")
                due_date = st.date_input("Due Date", date.today())
                submit_goal = st.form_submit_button("Set Goal")

                if submit_goal and conn:
                    if create_goal(conn, employee_map[selected_employee], st.session_state.user['user_id'], goal_title, goal_desc, due_date):
                        st.success(f"Goal for {selected_employee} has been set successfully!")

    with tab2:
        st.header("Track Employee Progress")
        goals_data = get_goals(conn, st.session_state.user['user_id'], 'manager')
        if goals_data:
            df = pd.DataFrame(goals_data, columns=["goal_id", "employee_id", "manager_id", "title", "description", "due_date", "status", "created_at"])
            df['employee_name'] = df['employee_id'].apply(lambda emp_id: [emp[1] for emp in employees if emp[0] == emp_id][0])
            
            for employee_id, group in df.groupby('employee_id'):
                st.subheader(f"Goals for: {group.iloc[0]['employee_name']}")
                for index, row in group.iterrows():
                    with st.expander(f"**{row['title']}** (Status: {row['status']})"):
                        st.write(f"**Description:** {row['description']}")
                        st.write(f"**Due Date:** {row['due_date']}")
                        
                        st.subheader("Manage Goal Status")
                        new_status = st.selectbox("Update Status", options=['draft', 'in progress', 'completed', 'cancelled'], key=f"status_{row['goal_id']}", index=['draft', 'in progress', 'completed', 'cancelled'].index(row['status']))
                        if st.button("Update Status", key=f"btn_status_{row['goal_id']}"):
                            if update_goal_status(conn, row['goal_id'], new_status):
                                st.success(f"Goal status updated to '{new_status}'.")
                                st.experimental_rerun()
                                
                        st.subheader("Provide Feedback")
                        feedback_text = st.text_area("Your Feedback", key=f"feedback_{row['goal_id']}")
                        if st.button("Submit Feedback", key=f"btn_feedback_{row['goal_id']}"):
                            if provide_feedback(conn, row['goal_id'], st.session_state.user['user_id'], feedback_text):
                                st.success("Feedback submitted successfully.")
                                st.experimental_rerun()

                        st.subheader("Tasks & Feedback History")
                        tasks_data = get_tasks_for_goal(conn, row['goal_id'])
                        if tasks_data:
                            task_df = pd.DataFrame(tasks_data, columns=["task_id", "goal_id", "description", "status", "progress", "created_at"])
                            st.write("**Tasks**")
                            st.dataframe(task_df[['description', 'status', 'progress']], use_container_width=True)
                            
                            st.write("**Task Approval**")
                            task_to_approve = st.selectbox("Select a task to approve", options=[t[2] for t in tasks_data if t[3] == 'pending'], key=f"approve_{row['goal_id']}")
                            if task_to_approve:
                                task_id = [t[0] for t in tasks_data if t[2] == task_to_approve][0]
                                if st.button("Approve Task", key=f"btn_approve_{task_id}"):
                                    update_task_status(conn, task_id, 'approved')
                                    st.success("Task approved!")
                                    st.experimental_rerun()

                        feedback_data = get_feedback_for_goal(conn, row['goal_id'])
                        if feedback_data:
                            feedback_df = pd.DataFrame(feedback_data, columns=["feedback_id", "goal_id", "manager_id", "feedback_text", "feedback_date"])
                            st.write("**Feedback**")
                            st.dataframe(feedback_df[['feedback_date', 'feedback_text']], use_container_width=True)
        else:
            st.info("You have not set any goals for your employees yet.")

def show_employee_dashboard():
    st.sidebar.header(f"Welcome, {st.session_state.user['username']}!")
    st.sidebar.button("Logout", on_click=logout)

    st.title("Employee Dashboard 🚀")
    st.write("View your goals and log your progress.")
    
    manager_data = get_manager_for_employee(conn, st.session_state.user['user_id'])
    if manager_data:
        st.write(f"Your Manager: **{manager_data[1]}**")

    goals_data = get_goals(conn, st.session_state.user['user_id'], 'employee')
    if goals_data:
        for goal in goals_data:
            goal_id, _, _, title, description, due_date, status, created_at = goal
            with st.expander(f"**{title}** (Status: {status})"):
                st.write(f"**Description:** {description}")
                st.write(f"**Due Date:** {due_date}")
                st.write(f"**Status:** {status}")

                st.subheader("Log a New Task")
                with st.form(f"task_form_{goal_id}", clear_on_submit=True):
                    task_desc = st.text_area("What are you going to do to achieve this goal?")
                    submit_task = st.form_submit_button("Submit Task for Approval")
                    if submit_task and conn:
                        add_task(conn, goal_id, task_desc)
                        st.success("Task submitted for manager approval!")
                
                st.subheader("Your Tasks")
                tasks_data = get_tasks_for_goal(conn, goal_id)
                if tasks_data:
                    tasks_df = pd.DataFrame(tasks_data, columns=["task_id", "goal_id", "description", "status", "progress", "created_at"])
                    st.dataframe(tasks_df[['description', 'status', 'progress']], use_container_width=True)

                    st.subheader("Update Task Progress")
                    task_to_update = st.selectbox("Select a task to update", options=[t[2] for t in tasks_data if t[3] == 'approved'], key=f"progress_select_{goal_id}")
                    if task_to_update:
                        task_id_to_update = [t[0] for t in tasks_data if t[2] == task_to_update][0]
                        new_progress = st.selectbox("Update Progress", options=['not started', 'in progress', 'completed'], key=f"progress_update_{goal_id}")
                        if st.button("Update Progress", key=f"btn_progress_{task_id_to_update}"):
                            update_task_progress(conn, task_id_to_update, new_progress)
                            st.success("Task progress updated!")
                            st.experimental_rerun()
                
                st.subheader("Manager Feedback")
                feedback_data = get_feedback_for_goal(conn, goal_id)
                if feedback_data:
                    feedback_df = pd.DataFrame(feedback_data, columns=["feedback_id", "goal_id", "manager_id", "feedback_text", "feedback_date"])
                    st.dataframe(feedback_df[['feedback_date', 'feedback_text']], use_container_width=True)
                else:
                    st.info("No feedback has been provided for this goal yet.")
    else:
        st.info("You have no goals assigned at the moment.")

def logout():
    st.session_state.authenticated = False
    st.session_state.user = None
    st.experimental_rerun()

if st.session_state.authenticated:
    if st.session_state.user['role'] == 'manager':
        show_manager_dashboard()
    else:
        show_employee_dashboard()
else:
    show_login_page()
