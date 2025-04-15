import os
from supabase import create_client

def create_supabase_table():
    """
    Create the training_data table in Supabase.
    """
    try:
        # Initialize Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("Supabase credentials not found in environment variables")
            
        supabase = create_client(supabase_url, supabase_key)
        
        # Create the table using direct SQL
        sql = """
        CREATE TABLE IF NOT EXISTS public.training_data (
            id SERIAL PRIMARY KEY,
            resume_text TEXT,
            job_description_text TEXT,
            label TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # Execute the SQL using the Supabase client
        result = supabase.postgrest.rpc('create_training_data_table', {}).execute()
        
        return True
            
    except Exception as e:
        print(f"Error creating table in Supabase: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    create_supabase_table() 