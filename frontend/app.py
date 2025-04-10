import streamlit as st
from io import BytesIO
from authentication import authenticate_user, register_user
from text_extraction import extract_text_from_file
from resume_ranker import process_resumes
import json
from jd_to_text import jobPosting_pre_processing
from resume_to_csv import resume_pre_processing
from utils.gcp import upload_to_gcp
import zipfile
import os
import requests


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
        .stSlider > div[data-baseweb="slider"] > div > div {
        background: #22c55e !important;
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

                    api_url = "http://127.0.0.1:8000/api/upload/job-description"  # Replace with actual API URL
                    response = requests.post(api_url, files={"file": (job_file.name, job_file, "text/plain")})
                    job_file.close

                    if response.status_code == 200:
                        st.success("Job description successfully sent to the API.")
                    else:
                        st.error(f"API responded with {response.status_code}: {response.text}")               

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
    uploaded_resume = st.file_uploader("Upload resumes (ZIP or a folder):", type=["zip"])
    
    # Replace with actual job id and supabase temporary storage path
    if uploaded_resume:

        job_id = st.session_state.username.replace(" ", "_") + "_job"
        raw_dir = f"frontend/temp_resumes"
        zip_path = f"{raw_dir}.zip"
        extracted_dir = f"frontend/extracted_resumes"
        csv_output_path = f"frontend/extracted_resumes/{job_id}.csv"

        # Save zip locally
        with open(zip_path, "wb") as f:
            f.write(uploaded_resume.getbuffer())
        st.success(f"Zip saved locally at {zip_path}")

        # Extract resumes
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extracted_dir)
        st.success(f"Resumes extracted to {extracted_dir}")

        # Store extracted file paths in session for use in submit
        extracted_files = []
        for filename in os.listdir(extracted_dir):
            filepath = os.path.join(extracted_dir, filename)
            if os.path.isfile(filepath):
                with open(filepath, "rb") as f:
                    file_bytes = f.read()
                    extracted_files.append((filename, file_bytes))
                # extracted_files.append((filename, open(filepath, "rb")))
        st.session_state.extracted_resumes = extracted_files

    if st.button(":rocket: Submit Resumes"):
        if not st.session_state.job_description.strip():  # Ensure job description is not empty or whitespace
            st.error("Please enter or upload a job description before submitting resumes.")
        elif "extracted_resumes" not in st.session_state or not st.session_state.extracted_resumes:
            st.error("Please upload and extract resumes first.")
        else:
            with st.spinner("Sending resumes to resume ranking API..."):
                api_url = "http://127.0.0.1:8000/api/upload/resumes"  # Replace with actual API URL

                # Prepare POST files list
                files = [("files", (fname, fobj, "application/octet-stream")) for fname, fobj in st.session_state.extracted_resumes]

                try:
                    response = requests.post(api_url, files=files)
                    for _, fobj, _ in files:
                        fobj.close()  # Close file handles after request
                    
                    if response.status_code == 200:
                        st.success("Resumes successfully submitted to the API.")                
                    else:
                        st.error(f"API responded with {response.status_code}: {response.text}")  
                except Exception as e:
                        st.error(f"Failed to send resumes to API: {e}")

            st.spinner('Processing your data...')
            st.session_state.next_page = 'results_page'
            st.session_state.show_results = True
            st.rerun()

# Results Section
elif st.session_state.next_page == 'results_page' and st.session_state.show_results:
    
    st.sidebar.text(f"Email: {st.session_state.useremail}")
    if st.sidebar.button("Sign Out"):
        st.session_state.update({"signout": False, "signedout": False, "username": "", "useremail": ""})

    st.subheader("Best Resume Matches for the Job Description \n")
    
    # Show all extracted resumes without ranking logic
    for filename, file_content in st.session_state.extracted_resumes:
        col1, col2 = st.columns([4, 1])  # Adjust column width (more space for text, less for button)
        with col1:
            st.write(f"**{filename}**")
        with col2:
            st.download_button(
                label=":floppy_disk:",  
                data=file_content,
                file_name=filename,
                mime="application/octet-stream",
                key=f"download_{filename}"
            )
        
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
    if st.sidebar.button("Sign Out"):
        st.session_state.update({"signout": False, "signedout": False, "username": "", "useremail": ""})

    st.sidebar.title(f"Thanks for visiting, {st.session_state.username}!")
    st.title("📋 We value your feedback")

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
        responses[key] = st.slider(question, 1, 5, 1)

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