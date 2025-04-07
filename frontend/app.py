import streamlit as st
from authentication import authenticate_user, register_user
from text_extraction import extract_text_from_file, extract_resumes_from_zip
from resume_ranker import process_resumes
from io import BytesIO
import time
import json
# from jd_to_json import jobPosting_pre_processing
from jd_to_text import jobPosting_pre_processing
import os

# Streamlit UI
st.set_page_config(page_title="ResuMatrix", page_icon=":briefcase:", layout="wide")
st.title("Welcome to :green[ResuMatrix] :books:")

# HTML CSS for styling
st.markdown("""
    <style>
        .stButton > button {
            background-color: #28a745;
            color: white;
            border-radius: 12px;
            padding: 10px 20px;
            font-size: 16px;
        }
        .stButton > button:hover {
            background-color: #fafabb ;
        }
        .stTextArea {
            font-family: 'Arial', sans-serif;
        }
        body {
            background: linear-gradient(to right, #00c6ff, #0072ff);
        }
        .stFileUploader {
            border: 2px dashed #28a745;
            padding: 20px;
            border-radius: 8px;
        }
    </style>
""", unsafe_allow_html=True)


if "username" not in st.session_state:
    st.session_state.username = ''
if "useremail" not in st.session_state:
    st.session_state.useremail = ''
if "signedout" not in st.session_state:
    st.session_state["signedout"] = False
if 'signout' not in st.session_state:
    st.session_state['signout'] = False
if 'next_page' not in st.session_state:
    st.session_state.next_page = 'dashboard_page'

if "resumes_text" not in st.session_state:
    st.session_state.resumes_text = {}
if "processed_job_json" not in st.session_state:
    st.session_state.processed_job_json = ""
if "job_description" not in st.session_state:
    st.session_state.job_description = ""
if "show_results" not in st.session_state:
    st.session_state.show_results = False
if "resumes_binary" not in st.session_state:
    st.session_state.resumes_binary = {}


def login_user():
    try:
        user_info = authenticate_user(st.session_state.email_input, st.session_state.password_input)
        if user_info:
            st.session_state.username = user_info["username"]
            st.session_state.useremail = user_info["email"]
            st.session_state.signedout = True
            st.session_state.signout = True
            st.success(f"Welcome back, {user_info['username']}!")
        else:
            st.error("Invalid email or password")
    except Exception as e:
        st.warning(f"Login failed: {e}")

def sign_up_user():
    try:
        if register_user(st.session_state.email_input, st.session_state.password_input, st.session_state.username_input):
            st.success('Account created successfully! Please login now.')
            st.balloons()
            st.markdown('Please Login using your email and password')
    except Exception as e:
        st.warning(f"Signup failed: {e}")

# Main flow
if st.session_state.signout:
    st.text('Name: ' + st.session_state.username)
    st.text('Email id: ' + st.session_state.useremail)
    st.button('Sign out', on_click=lambda: st.session_state.update({"signout": False, "signedout": False, "username": "", "useremail": ""}))

# Authentication Page
if not st.session_state["signedout"]:  # Only show if the state is False
    choice = st.selectbox('Login/Signup', ['Login', 'Sign up'])
    email = st.text_input('Email Address')
    password = st.text_input('Password', type='password')

    st.session_state.email_input = email
    st.session_state.password_input = password

    if choice == 'Sign up':
        username = st.text_input("Enter your unique username")
        st.session_state.username_input = username
        if st.button('Create my account'):
            sign_up_user()
    else:
        if st.button('Login', on_click=login_user):
            user_info = authenticate_user(email, password)
            if user_info:
                st.session_state.username = user_info["username"]
                st.session_state.useremail = user_info["email"]
                st.session_state.signedout = True
                st.session_state.signout = True
                st.success(f"Welcome back, {user_info['username']}!")
            else:
                st.error("Invalid email or password")
    

elif st.session_state.next_page == 'dashboard_page':

    # Dashboard Page
    st.sidebar.title(f"Welcome, {st.session_state.username}!")
    st.sidebar.text(f"Email: {st.session_state.useremail}")
    if st.sidebar.button("Sign Out"):
        st.session_state.update({"signout": False, "signedout": False, "username": "", "useremail": ""})

    if "modifications" not in st.session_state:
        st.session_state.modifications = []

    # Job Description Section
    st.subheader("Enter Job Description")

    job_description = st.text_area("Paste or edit the job description:", 
                                   value=st.session_state.get("job_description", ""), 
                                   key="jd_text")
    # job_description = st.text_area("Paste the job description here:")
    uploaded_file = st.file_uploader("Or upload a job description file (TXT, PDF, DOCX):", type=["txt", "pdf", "docx"])
    extracted_text = extract_text_from_file(uploaded_file) if uploaded_file else ""

    if extracted_text:
        st.text_area("Extracted Job Description:", extracted_text, height=300)

    if st.button(":rocket: Submit Job Description"):
        st.session_state.modifications = []
        final_description = job_description.strip() if job_description.strip() else extracted_text.strip()

        if final_description:
            st.session_state.job_description = final_description

            with st.spinner('Processing your data...'):
                try:
                    processed_job_json, processed_job_text = jobPosting_pre_processing(final_description)
                    st.session_state.processed_job_json = processed_job_json
                    st.session_state.processed_job_text = processed_job_text
                    st.session_state.modified_job_posting = False

                except json.JSONDecodeError as e:
                    st.error(f"Error processing job description JSON: {e}")
                    st.text_area("Raw JSON Output:", str(processed_job_json))
        else:
            st.error("Please enter or upload a job description.")


    if "processed_job_text" in st.session_state:
        st.subheader("Modify Job Posting")

        # if "processed_text" not in st.session_state:
        #     st.session_state.processed_text = st.session_state.processed_job_text

        # processed_text = st.text_area("Processed Job Posting:", 
        #                                                 value=st.session_state.processed_text, 
        #                                                 height=300,
        #                                                 key="processed_text")

        st.session_state.processed_text = st.text_area("Processed Job Posting:", 
                                                        value=st.session_state.processed_job_text, 
                                                        height=300)
        
        new_change = st.text_area("Describe the changes you'd like to make:", value="")

        if st.button(":recycle: Regenerate Job Posting"):
            if new_change.strip():
                st.session_state.modifications.append(new_change)

            with st.spinner('Regenerating job posting with modifications...'):
                try:
                    combined_modifications = "\n".join(st.session_state.modifications)

                    updated_job_json, updated_job_text = jobPosting_pre_processing(st.session_state.processed_text, combined_modifications)

                    st.session_state.processed_job_json = updated_job_json
                    st.session_state.processed_job_text = updated_job_text
                    st.session_state.job_description = updated_job_text
                    st.session_state.processed_text = updated_job_text
                    st.session_state.modified_job_posting = True  

                    # Save final job posting locally
                    save_path = "resumatrix_streamlit/final_job_posting.txt" 
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)

                    with open(save_path, "w", encoding="utf-8") as f:
                        f.write(updated_job_text)                

                    st.rerun()   

                except json.JSONDecodeError as e:
                    st.error(f"Error processing regenerated job description JSON: {e}")
                    st.text_area("Raw JSON Output:", str(updated_job_json))

        if st.session_state.get("processed_job_text"):
            st.markdown("---")
            if st.button(":arrow_right: Proceed to Resume Upload"):
                st.session_state.next_page = 'resume_page'
                st.rerun()
    

elif st.session_state.next_page == 'resume_page':

    st.sidebar.title(f"Welcome, {st.session_state.username}!")
    st.sidebar.text(f"Email: {st.session_state.useremail}")
    if st.sidebar.button("Sign Out"):
        st.session_state.update({"signout": False, "signedout": False, "username": "", "useremail": ""})

    # Resume Upload Section
    st.subheader("Upload Resumes")
    uploaded_resume = st.file_uploader("Upload resumes (Single PDF, DOCX, TXT or ZIP of resumes):", type=["pdf", "docx", "txt", "zip"])
    resumes_text = {}

    if uploaded_resume:
        if uploaded_resume.name.endswith(".zip"):
            resumes_text, resume_binary = extract_resumes_from_zip(uploaded_resume)
            for filename, content in resumes_text.items():
                st.text_area(f"Extracted Text from {filename}", content, height=300)
            st.session_state.resumes_text.update(resumes_text)
            st.session_state.resumes_binary.update(resume_binary)
        else:
            extracted_resume_text = extract_text_from_file(uploaded_resume)
            if extracted_resume_text:
                st.text_area("Extracted Resume Text:", extracted_resume_text, height=300)
                st.session_state.resumes_text[uploaded_resume.name] = extracted_resume_text
                st.session_state.resumes_binary[uploaded_resume.name] = BytesIO(uploaded_resume.getvalue()).getvalue()


    if st.button(":rocket: Submit Resumes"):
        if not st.session_state.job_description.strip():  # Ensure job description is not empty or whitespace
            st.error("Please enter or upload a job description before submitting resumes.")
        elif not st.session_state.resumes_text:  # Ensure resumes are uploaded
            st.error("Please upload resumes first.")
        else:
            with st.spinner('Processing your data...'):
                time.sleep(2)
            st.session_state.next_page = 'results_page'
            st.session_state.show_results = True
            st.rerun()


# Results Section
elif st.session_state.next_page == 'results_page' and st.session_state.show_results:
# if st.session_state.show_results:
    st.subheader("Best Resume Matches for the Job Description")
    ranked_resumes = process_resumes(st.session_state.job_description, st.session_state.resumes_text, st.session_state.resumes_binary)

    for rank, filename, file_content in ranked_resumes:
        col1, col2 = st.columns([4, 1])  # Adjust column width (more space for text, less for button)

        with col1:
            st.write(f"**{rank}. {filename}**")

        with col2:
            st.download_button(
                label=":floppy_disk:",  
                data=file_content,
                file_name=filename,
                mime="application/octet-stream",
                key=f"download_{filename}"
            )

    if st.button("Back to Upload Page"):
        st.session_state.next_page = 'dashboard_page'
        st.rerun()
