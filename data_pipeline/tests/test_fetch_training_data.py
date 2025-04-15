import os
import sys
import pandas as pd
from dotenv import load_dotenv
import unittest

# Add the scripts directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# Load environment variables from .env file in the parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Import the fetch_training_data function
from fetch_training_data import fetch_training_data, save_training_data

class TestFetchTrainingData(unittest.TestCase):
    """
    Test case for the fetch_training_data function.
    """

    def setUp(self):
        """
        Set up the test case.
        """
        # Check if Supabase credentials are set
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")

        if not self.supabase_url or not self.supabase_key:
            self.skipTest("Supabase credentials not found in environment variables")

    def test_fetch_training_data(self):
        """
        Test the fetch_training_data function.
        """
        print("Testing fetch_training_data function...")

        # Fetch the training data
        df = fetch_training_data()

        # Verify that the DataFrame is not empty
        self.assertIsNotNone(df)
        self.assertGreater(len(df), 0)

        # Verify that the DataFrame has the expected columns
        expected_columns = ['job_description_text', 'resume_text', 'label']
        for col in expected_columns:
            self.assertIn(col, df.columns)

        # Print some information about the data
        print(f"\nFetched training data with {len(df)} records")
        print("\nColumns:")
        for col in df.columns:
            print(f"  - {col}")

        print("\nSample data (first 5 rows):")
        if len(df) > 0:
            # Truncate long text fields for display
            sample_df = df.copy()
            for col in ['job_description_text', 'resume_text']:
                if col in sample_df.columns:
                    sample_df[col] = sample_df[col].apply(lambda x: x[:100] + '...' if isinstance(x, str) and len(x) > 100 else x)

            print(sample_df.head().to_string())

            # Count of each label
            if 'label' in df.columns:
                print("\nLabel distribution:")
                label_counts = df['label'].value_counts()
                for label, count in label_counts.items():
                    print(f"  - {label}: {count}")

        # Save the data to a CSV file in the tests directory
        output_path = os.path.join(os.path.dirname(__file__), "training_data_test.csv")
        save_training_data(df, output_path)
        print(f"\nSaved training data to {output_path}")

        # Verify that the file was created
        self.assertTrue(os.path.exists(output_path))

        print("\nTest completed successfully!")

def run_test():
    """
    Run the test case.
    """
    # Check if .env file exists in the parent directory
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if not os.path.exists(env_path):
        print("WARNING: No .env file found in the parent directory.")
        print("Please create one with SUPABASE_URL and SUPABASE_KEY.")

    # Run the test
    unittest.main()

if __name__ == "__main__":
    run_test()
