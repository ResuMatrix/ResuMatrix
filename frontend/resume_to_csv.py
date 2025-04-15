import os
import pymupdf
import mammoth
import csv
import magic
import zipfile
import uuid

def scanRecurse(baseDir):
    for entry in os.scandir(baseDir):
        if entry.is_file():
            yield os.path.join(baseDir, entry.name)
        else:
            yield from scanRecurse(entry.path)

def resume_pdf_processing(curr_resume_filepath):
    doc = pymupdf.open(curr_resume_filepath)
    page = doc[0]
    resume_text = page.get_text()
    resume_links = [i['uri'] for i in page.get_links()]
    links_str = 'Links: '+' , '.join(resume_links)
    resume_text += links_str
    if len(resume_text)<30:
        print(f'Parsing issue for {curr_resume_filepath}')
        return None
    return resume_text

def resume_doc_processing(docx_path):
    with open(docx_path, "rb") as docx_file:
        result = mammoth.extract_raw_text(docx_file)
        text = result.value
        messages = result.messages  # Console log
    return text

def resume_processing(file_path):
    _, file_extension = os.path.splitext(file_path)
    file_extension = file_extension.lower()
    if file_extension == '.docx':
        return resume_doc_processing(file_path)
    elif file_extension == '.pdf':
        return resume_pdf_processing(file_path)
    return 'Unsupported file type'

# Create a custom dialect
csv.register_dialect('custom',
                    quoting=csv.QUOTE_ALL,
                    doublequote=True,
                    escapechar='\\')


### THE CURRENT PROCESS DOES NOT INCLUDE KEY DEMOGRAPHIC VARIABLES - VISA STATUS, DISABILITY AND VETERAN
### BUILD A RANDOM GENERATOR FOR THESE BOOLEAN TYPE VARIABLES VISA(0.5,0.5), DISABILITY(0.1,0.9), VETERAN(0.1,0.9)
### TAG VISA WITH EDUCATION OR WORK EXPERIENCE IF NEEDED BUT
### ENFORCE VISA==(!VETERAN) cuz commonsense
### do we need to add this to the supervised model too?

def resume_pre_processing(job_id, file_path):
    ## need to change both base_path_csv and base_path_zip while integrating into the backend
    base_path_csv = "C:\\NEU Courses\\IE7374_MLOps\\extracted_resumes" # to be changed
    csv_path = os.path.join(base_path_csv,job_id+'.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile, dialect='custom')
        csv_writer.writerow(['header'])
        if os.path.isfile(file_path):
            base_path_zip = "C:\\NEU Courses\\IE7374_MLOps\\resumes" #this is the folder where the zip will be extracted
            # a new folder with name 'job_id' will be created
            #verify against file extension and mime type, extracting file extension
            _, file_extension = os.path.splitext(file_path)
            file_extension = file_extension.lower()

            mime_type = magic.from_file(file_path,mime=True)
            if file_extension == '.zip' and mime_type == 'application/zip':
                extracted_resume_path = os.path.join(base_path_zip,job_id)
                resume_zip = zipfile.ZipFile(file_path, 'r')
                if os.path.exists(extracted_resume_path):
                    os.rmdir(extracted_resume_path)
                    os.mkdir(extracted_resume_path)
                    print('Existing folder removed, recreated folder.')
                else:
                    os.mkdir(extracted_resume_path)
                    print(f'Created new folder at {extracted_resume_path}.')
                resume_zip.extractall(extracted_resume_path)
                for curr_resume in scanRecurse(extracted_resume_path):
                    resume_text = resume_processing(curr_resume)
                    csv_writer.writerow([resume_text])
        elif os.path.isdir(file_path):
            for curr_resume in scanRecurse(file_path):
                resume_text = resume_processing(curr_resume)
                csv_writer.writerow([resume_text])
        else:
            print(f"Unsupported file type {mime_type}. Only zip/docx/pdf files are supported.") #console log

    return f'Parsed resumes are stored in {csv_path}.'

#this is the code to generate the uuid, this will go into the db step, not required for now
# job_id = uuid.uuid4().__str__()
# file_path = 'C:\\NEU Courses\\IE7374_MLOps\\resumes'
# status=resume_pre_processing(job_id, file_path)
# print(status)
