import streamlit as st
from io import BytesIO
from supabase_auth import authenticate_user, register_user
from text_extraction import extract_text_from_file
import json
from jd_to_text import jobPosting_pre_processing
import datetime
import zipfile
import os
import requests
import time
import requests
from google.cloud import storage

API_BASE_URL = os.getenv("RESUMATRIX_API_URL", "http://localhost:8000")
GCP_BUCKET = os.getenv("GCP_BUCKET_NAME")

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
        .stSlider > div[data-baseweb="slider"] > div > div > div {
        background-color: #22c55e;
        }
        .stSlider > div[data-baseweb="slider"] > div > div > div > div {
        color: green !important;
        font-weight: bold;
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
if "extracted_resumes" not in st.session_state:
    st.session_state.extracted_resumes = ""

def sign_up_user():
    try:
        if register_user(st.session_state.email_input, st.session_state.password_input, st.session_state.username_input):
            st.success('Account created successfully! Please login now.')
            st.balloons()
            st.markdown('Please Login using your email and password')
    except Exception as e:
        st.warning(f"Signup failed: {e}")

def login_user():
    try:
        user_info = authenticate_user(st.session_state.email_input, st.session_state.password_input)
        if user_info:
            st.session_state.username = user_info["username"]
            st.session_state.useremail = user_info["email"]
            st.session_state.userid = user_info["id"]
            st.session_state.signedout = True
            st.session_state.signout = True
            st.success(f"Welcome back, {user_info['username']}!")
        else:
            st.error("Invalid email or password")
    except Exception as e:
        st.warning(f"Login failed: {e}")

# Main flow
if st.session_state.signout:
    top_left, top_spacer, top_right = st.columns([2, 6, 2])
    with top_left:
        st.markdown(f"**Name:** {st.session_state.username}")
        st.markdown(f"**Email:** {st.session_state.useremail}")
    with top_right:
        st.button(' Sign Out ', on_click=lambda: st.session_state.update({
            "signout": False, "signedout": False, "username": "", "useremail": "", "userid": ""
        }))

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
            st.session_state.next_page = 'dashboard_page'

elif st.session_state.next_page == 'dashboard_page':

    # Dashboard Page
    st.sidebar.title(f"Welcome, {st.session_state.username}!")
    st.sidebar.text(f"Email: {st.session_state.useremail}")
    st.sidebar.text(f"Date: {datetime.date.today().strftime('%B %d, %Y')}")
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

                    job_file = BytesIO(updated_job_text.encode('utf-8'))
                    job_file.name = "job_posting.txt"              

                    st.rerun()   

                except json.JSONDecodeError as e:
                    st.error(f"Error processing regenerated job description JSON: {e}")
                    st.text_area("Raw JSON Output:", str(updated_job_json))

        if st.session_state.get("processed_job_text"):
            st.markdown("---")
            if st.button(":arrow_right: Proceed to Resume Upload"):

                if "job_description" in st.session_state and "userid" in st.session_state:
                    api_url = f"{API_BASE_URL}/jobs/"

                    payload = {
                        "job_text": st.session_state.processed_job_text,
                        "user_id": st.session_state.userid  # Supabase Auth User ID
                    }

                    response = requests.post(api_url, json=payload)
                    if response.ok:
                        job_data = response.json()["job"]
                        st.session_state.job_id = job_data["id"]  # Save for resume upload
                        st.success("Job description successfully stored in Supabase.")
                        st.session_state.next_page = 'resume_page'
                        st.rerun()
                    else:
                        st.error(f"Failed to upload job description: {response.text}")
                else:
                    st.error("Missing job description or user ID.")

elif st.session_state.next_page == 'resume_page':

    st.sidebar.text(f"Email: {st.session_state.useremail}")
    st.sidebar.text(f"Username: {st.session_state.username}")
    st.sidebar.text(f"Date: {datetime.date.today().strftime('%B %d, %Y')}")
    if st.sidebar.button("Sign Out"):
        st.session_state.update({"signout": False, "signedout": False, "username": "", "useremail": ""})

    # Resume Upload Section
    st.subheader("Upload Resumes")
    uploaded_resume = st.file_uploader("Upload resumes (ZIP only):", type=["zip"])
    
    # Replace with actual job id and supabase temporary storage path
    if uploaded_resume:

        zip_bytes = BytesIO(uploaded_resume.getvalue())
        extracted_files = []

        with zipfile.ZipFile(zip_bytes, 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                if file_info.filename.endswith('.pdf'):
                    with zip_ref.open(file_info) as file:
                        pdf_bytes = file.read()
                        extracted_files.append((file_info.filename, BytesIO(pdf_bytes)))
                else:
                    st.warning(f"Skipped non-PDF file: {file_info.filename}")

        if not extracted_files:
            st.error("No PDF files found in the uploaded ZIP.")
        else:
            st.session_state.extracted_resumes = extracted_files
            st.success(f"{len(extracted_files)} PDF resumes extracted successfully.")
        
        if st.button(":rocket: Submit Resumes"):
            if not st.session_state.get("job_id"):
                st.error("Missing job ID. Please make sure the job description was uploaded.")
            elif "extracted_resumes" not in st.session_state or not st.session_state.extracted_resumes:
                st.error("Please upload and extract resumes first.")
            else:
                with st.spinner("Sending resumes to resume ranking API..."):
                    api_url = f"{API_BASE_URL}/jobs/{st.session_state.job_id}/resumes"

                    files = [
                        ("files", (fname, fobj, "application/octet-stream"))
                        for fname, fobj in st.session_state.extracted_resumes
                    ]

                    try:
                        response = requests.post(api_url, files=files)
                        if response.ok:
                            st.success("Resumes successfully submitted and stored in Supabase.")
                            public_urls = response.json().get("public_urls", [])
                            st.session_state.resume_public_urls = public_urls
                            st.session_state.next_page = 'results_page'
                            st.session_state.show_results = True
                            st.rerun()
                        else:
                            st.error(f"API responded with {response.status_code}: {response.text}")
                    except Exception as e:
                        st.error(f"Failed to send resumes to API: {e}")

elif st.session_state.next_page == 'results_page' and st.session_state.show_results:

    st.sidebar.text(f"Email: {st.session_state.useremail}")
    st.sidebar.text(f"Username: {st.session_state.username}")
    st.sidebar.text(f"Date: {datetime.date.today().strftime('%B %d, %Y')}")
    if st.sidebar.button("Sign Out"):
        st.session_state.update({"signout": False, "signedout": False, "username": "", "useremail": ""})

    st.markdown("# Best Resume Matches for the Job Description")

    job_id = st.session_state.job_id
    user_id = st.session_state.userid
    bucket_name = GCP_BUCKET

    job_api = f"{API_BASE_URL}/jobs/{job_id}"
    resumes_api = f"{API_BASE_URL}/jobs/{job_id}/resumes"

    # Polling logic
    status_placeholder = st.empty()
    status_placeholder.info("⏳ Waiting for resume ranking to complete...")
    while True:
        try:
            job_res = requests.get(job_api)
            resumes_res = requests.get(resumes_api)

            if not job_res.ok or not resumes_res.ok:
                st.error("Failed to fetch job/resumes info. Retrying...")
                time.sleep(15)
                continue

            job_data = job_res.json()["job"]
            resumes_data = resumes_res.json()["resumes"]

            if job_data["user_id"] != user_id:
                st.error("You are not authorized to view this job.")
                st.stop()

            resume_statuses = [r["status"] for r in resumes_data]
            if all(s not in [-2, 0] for s in resume_statuses) and job_data["status"] == 1:
                break

        except Exception as e:
            st.warning(f"Error polling APIs: {e}")
        time.sleep(15)

    status_placeholder.empty()    
    st.success("Resume ranking complete!")

    # Categorize and sort
    ranked_resumes = sorted([r for r in resumes_data if r["status"] > 0], key=lambda x: x["status"])
    unfit_resumes = [r for r in resumes_data if r["status"] == -1]

    client = storage.Client.from_service_account_json("gcp_secret_key.json")
    bucket = client.bucket(bucket_name)

    def get_resume_file_by_id(resume_id):
        # List all blobs in the folder
        blobs = bucket.list_blobs(prefix=f"resumes/{job_id}/")
        for blob in blobs:
            file_name = blob.name.split("/")[-1]
            if file_name.startswith(f"{resume_id}_"):
                actual_name = file_name.split(f"{resume_id}_", 1)[1]
                return blob.download_as_bytes(), actual_name
        return None, None 


    # Display table headers
    col_name, col_rank, col_download = st.columns([4, 1, 2])
    with col_name:
        st.markdown("### **Resume Name**")
    with col_rank:
        st.markdown("### **Label**")
    with col_download:
        st.markdown("### **Download**")

    # Display each resume row
    for resume in ranked_resumes:
        resume_bytes, resume_name = get_resume_file_by_id(resume["id"])
        if resume_bytes and resume_name:
            col_name, col_rank, col_download = st.columns([4, 1, 2])
            with col_name:
                st.markdown(resume_name)
            with col_rank:
                st.markdown(f"Rank: {resume['status']}")
            with col_download:
                st.download_button(
                    label="📄 Download",
                    data=resume_bytes,
                    file_name=resume_name,
                    mime="application/pdf",
                    key=f"download_{resume['id']}"
                )

    # Display Unfit Resumes
    st.markdown("# Unfit Resumes")

    # Display table headers
    col_name, col_rank, col_download = st.columns([4, 1, 2])
    with col_name:
        st.markdown("### **Resume Name**")
    with col_rank:
        st.markdown("### **Label**")
    with col_download:
        st.markdown("### **Download**")

    for resume in unfit_resumes:
        resume_bytes, resume_name = get_resume_file_by_id(resume["id"])
        if resume_bytes and resume_name:
            col_name, col_rank, col_download = st.columns([4, 1, 2])
            with col_name:
                st.markdown(resume_name)
            with col_rank:
                st.markdown("Unfit")
            with col_download:
                st.download_button(
                    label="📄 Download",
                    data=resume_bytes,
                    file_name=resume_name,
                    mime="application/pdf",
                    key=f"download_unfit_{resume['id']}"
                )

    # Navigation
    col_next, col_back = st.columns([2, 2])
    with col_next:
        if st.button("📋 Continue to Feedback"):
            st.session_state.next_page = "feedback_page"
            st.rerun()
    with col_back:
        if st.button("Back to Upload Page"):
            st.session_state.next_page = 'dashboard_page'
            st.rerun()


elif st.session_state.next_page == "feedback_page":
    st.sidebar.text(f"Email: {st.session_state.useremail}")
    st.sidebar.text(f"Username: {st.session_state.username}")
    st.sidebar.text(f"Date: {datetime.date.today().strftime('%B %d, %Y')}")
    if st.sidebar.button("Sign Out"):
        st.session_state.update({"signout": False, "signedout": False, "username": "", "useremail": ""})

    st.sidebar.title(f"Thanks for visiting, {st.session_state.username}!")
    st.title(" We value your feedback")

    st.markdown("Please rate your experience with Resumatrix \n")

    feedback_questions = {
        "job_clarity": "How clear was the job posting after editing?",
        "resume_relevance": "Was the resume ranking relevant to the job description?",
        "system_satisfaction": "Did the system meet your expectations?",
        "interface_usability": "How easy was it to use the interface?",
        "recommendation_likelihood": "How likely are you to recommend this tool?"
    }

    responses = {}

    for key, question in feedback_questions.items():
        responses[key] = st.select_slider(question, options=[1, 2, 3, 4, 5], value=1)

    additional_comments = st.text_area("Any other suggestions or comments?")

    if st.button("📨 Submit Feedback"):
        feedback_payload = {
            "username": st.session_state.username,
            "useremail": st.session_state.useremail,
            "job_id": st.session_state.username.replace(" ", "_") + "_job",
            "responses": responses,
            "comments": additional_comments
        }

    api_url = "http://127.0.0.1:8000/api/feedback/submit"  # Replace with your actual feedback endpoint

    try:
        response = requests.post(api_url, json=feedback_payload)
        if response.status_code == 200:
            st.success("✅ Thank you for your feedback!")
        else:
            st.error(f"API responded with {response.status_code}: {response.text}")
    except Exception as e:
        st.error(f"Failed to send feedback: {e}")