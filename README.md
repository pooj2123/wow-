# IIIT-H Sentence Audio Library

A Streamlit interface for browsing the supplied IIIT-H audio dataset.

## Run locally

1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Create and activate a virtual environment (optional but recommended).
4. Install dependencies and start the app:

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

The `IIIT-h` dataset folder must remain beside `app.py`. The app scans its nested folders and identifies the four conditions:
- With Prompt
- Without Prompt
- With Reference Audio
- Without Reference Audio

The page groups sentences into six categories and shows the sentence text followed by four audio players. The app also displays missing-file notices and provides audio downloads.

## Note on duplicate filenames

The supplied dataset contains duplicate prompt files with names such as `(1)`. The app indexes one file for each sentence/condition combination to avoid displaying duplicate entries.
