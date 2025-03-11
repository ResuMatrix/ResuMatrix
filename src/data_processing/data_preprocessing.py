import pandas as pd
import os


def load_data(data_type="train"):
    current_file_path = os.path.abspath(__file__)
    if data_type not in ["train", "test"]:
        raise ValueError("Expecting data_type to be train or test.")

    parent_dir = current_file_path[:current_file_path.index("ResuMatrix") + 10]
    src_dir = os.path.join(parent_dir, "src")

    data_file_path = os.path.join(src_dir, "model_training_data", "resume_job_description_fit", data_type + ".csv")
    return pd.read_csv(data_file_path)



