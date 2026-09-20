# PDF Mail Merge Pro

Employee Document Automation Workspace. Extracts tabular data from PDFs, validates it, and generates personalized Word documents using Mail Merge. Can optionally convert generated DOCX files to PDF.

## Local installation

\\\ash
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
\\\

## Streamlit Cloud deployment

This application is ready for deployment on Streamlit Community Cloud:

1. Push this project to a GitHub repository.
2. Open [Streamlit Community Cloud](https://share.streamlit.io/).
3. Connect your GitHub account.
4. Select the repository and branch.
5. Set the Main file path to \pp.py\.
6. Click **Deploy**.

Note:
* \equirements.txt\ contains the Python dependencies.
* \packages.txt\ instructs the Streamlit Cloud Linux environment to install LibreOffice for DOCX to PDF conversion.
