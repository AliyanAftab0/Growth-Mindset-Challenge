"""
Advanced Data Sweeper: A Streamlit app for converting between CSV/Excel formats
with data cleaning and visualization capabilities.
"""

import streamlit as st
import pandas as pd
import os
from io import BytesIO
from typing import Union

# Configure Streamlit app settings
def configure_app():
    """Set up page configuration and custom CSS styling."""
    st.set_page_config(page_title="Data Sweeper", layout="wide")
    apply_custom_styles()

def apply_custom_styles():
    """Inject custom CSS for dark mode styling."""
    st.markdown("""
    <style>
        .main { background-color: #121212; }
        .block-container {
            padding: 3rem 2rem;
            border-radius: 12px;
            background-color: #1e1e1e;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }
        h1, h2, h3 { color: #66c2ff; }
        .stButton>button {
            border: none;
            border-radius: 8px;
            background-color: #0078D7;
            color: white;
            padding: 0.75rem 1.5rem;
            font-size: 1rem;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.4);
        }
        .stDownloadButton>button { background-color: #28a745; }
        .stDownloadButton>button:hover { background-color: #218838; }
    </style>
    """, unsafe_allow_html=True)

def show_intro():
    """Display application introduction and instructions."""
    st.title("Advanced Data Sweeper (Made By Aliyan Aftab)")
    st.write("Transform your files between CSV and Excel formats with built-in data cleaning and visualization.")
    
    with st.expander("📘 Getting Started Guide"):
        st.markdown("""
        **Step-by-Step Guide:**
        1. **Upload Files:** Click 'Browse Files' to select CSV/Excel documents
        2. **Clean Data:** Use sidebar options to remove duplicates or fill missing values
        3. **Select Columns:** Choose which columns to include in final output
        4. **Convert Files:** Choose output format and download processed files
        
        **Example Output:**
        ```csv
        Name,Age,Salary
        John,32,55000
        Alice,28,48000
        ```
        """)

def handle_file_upload() -> list:
    """Create file uploader widget and return uploaded files."""
    return st.file_uploader("Upload files (CSV/Excel):", 
                          type=["csv", "xlsx"], 
                          accept_multiple_files=True)

def load_data(file: BytesIO) -> Union[pd.DataFrame, None]:
    """
    Load file data into DataFrame based on file extension.
    
    Args:
        file: Uploaded file object from Streamlit
        
    Returns:
        pd.DataFrame if successful, None if error occurs
    """
    try:
        ext = os.path.splitext(file.name)[-1].lower()
        if ext == ".csv":
            return pd.read_csv(file)
        if ext == ".xlsx":
            return pd.read_excel(file)
        st.error(f"Unsupported file type: {ext}")
        return None
    except Exception as e:
        st.error(f"Error loading {file.name}: {str(e)}")
        return None

def clean_data(df: pd.DataFrame, file_name: str) -> pd.DataFrame:
    """Apply data cleaning operations based on sidebar selections."""
    if st.sidebar.checkbox(f"Remove duplicates in {file_name}"):
        initial_rows = len(df)
        df = df.drop_duplicates()
        st.sidebar.write(f"Removed {initial_rows - len(df)} duplicates")
    
    if st.sidebar.checkbox(f"Fill missing values in {file_name}"):
        numeric_cols = df.select_dtypes(include='number').columns
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
        st.sidebar.write("Filled missing numeric values")
    
    return df

def handle_column_selection(df: pd.DataFrame, file_name: str) -> pd.DataFrame:
    """
    Optimized column selection with efficient filtering.
    
    Args:
        df: Original DataFrame
        file_name: Name of the file being processed
        
    Returns:
        Filtered DataFrame (only if selection differs from original)
    """
    selected_columns = st.multiselect(
        f"Select columns for {file_name}",
        df.columns,
        default=df.columns.tolist()
    )
    
    # Efficient column filtering logic
    if list(selected_columns) == df.columns.tolist():
        return df
    if set(selected_columns) == set(df.columns):
        return df[selected_columns]
    
    return df[selected_columns]

def convert_file(df: pd.DataFrame, file_name: str, target_format: str) -> None:
    """Handle file conversion and download button creation."""
    buffer = BytesIO()
    try:
        if target_format == "CSV":
            df.to_csv(buffer, index=False)
            mime = "text/csv"
            new_ext = ".csv"
        else:
            df.to_excel(buffer, index=False, engine='openpyxl')
            mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            new_ext = ".xlsx"
        
        buffer.seek(0)
        download_name = file_name.replace(os.path.splitext(file_name)[-1], new_ext)
        
        st.download_button(
            label=f"Download {download_name}",
            data=buffer,
            file_name=download_name,
            mime=mime
        )
    except Exception as e:
        st.error(f"Conversion failed: {str(e)}")

def main():
    """Main application workflow."""
    configure_app()
    show_intro()
    
    uploaded_files = handle_file_upload()
    if not uploaded_files:
        return
    
    progress_bar = st.progress(0)
    conversion_format = st.sidebar.radio("Choose output format:", ["CSV", "Excel"])
    
    for i, file in enumerate(uploaded_files):
        progress = (i + 1) / len(uploaded_files)
        progress_bar.progress(progress)
        
        st.header(f"Processing: {file.name}")
        df = load_data(file)
        
        if df is None or df.empty:
            st.warning(f"Skipping empty/invalid file: {file.name}")
            continue
        
        st.write(f"📏 Size: {file.size / 1024:.2f} KB")
        st.dataframe(df.head())
        
        df = clean_data(df, file.name)
        df = handle_column_selection(df, file.name)
        
        if st.checkbox(f"Show visualization for {file.name}"):
            st.bar_chart(df.select_dtypes(include='number').iloc[:, :2])
        
        convert_file(df, file.name, conversion_format)
    
    progress_bar.empty()
    st.success("🎉 All files processed successfully!")

if __name__ == "__main__":
    main()