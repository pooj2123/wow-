
from pathlib import Path
import re
import unicodedata

import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="IIIT-H Audio Dataset",
    page_icon="🎧",
    layout="wide",
)

# The dataset folder should be beside app.py.
BASE_DIR = Path(__file__).resolve().parent

DATASET_CANDIDATES = [
    BASE_DIR / "IIIT-h",
    BASE_DIR / "IIIT-H",
    BASE_DIR / "audio_dataset",
    BASE_DIR / "dataset",
]

VARIANTS = {
    "with_prompt": "With Prompt",
    "without_prompt": "Without Prompt",
    "with_reference": "With Reference Audio",
    "without_reference": "Without Reference Audio",
}

SENTENCES = {
    "Assertive": [
        (1, "The library closes at eight o’clock on weekdays."),
        (2, "My sister moved to Bangalore last year."),
        (3, "The bus was ten minutes late this morning."),
    ],
    "Interrogative": [
        (4, "Have you finished reading the assignment?"),
        (5, "Where did you keep the spare keys?"),
        (6, "Could you tell me when the next train leaves?"),
    ],
    "Imperative — Request": [
        (7, "Please send me the report by evening."),
        (8, "Could you kindly turn down the music a little?"),
        (9, "Please hold the door for me."),
    ],
    "Imperative — Command": [
        (10, "Submit your assignment before the deadline."),
        (11, "Stand in line and wait for your turn."),
        (12, "Put that phone away right now."),
    ],
    "Exclamatory — Sad": [
        (13, "I can’t believe he’s really gone!"),
        (14, "What a terrible day this has been!"),
        (15, "It breaks my heart to see the old house empty!"),
    ],
    "Exclamatory — Happy": [
        (16, "I got the internship, and I’m so thrilled!"),
        (17, "What a wonderful surprise this is!"),
        (18, "We won the final, and I can’t stop smiling!"),
    ],
}

AUDIO_EXTENSIONS = {".wav", ".mp3", ".ogg", ".flac", ".m4a"}


# ============================================================
# NORMALIZATION HELPERS
# ============================================================

def normalize(value):
    """Normalize folder/file names for case-insensitive matching."""
    value = unicodedata.normalize("NFKC", str(value))
    value = value.strip().lower()
    value = value.replace("_", " ")
    value = value.replace("-", " ")
    value = re.sub(r"\s+", " ", value)
    return value


def find_dataset_root():
    """Find the dataset directory."""
    for candidate in DATASET_CANDIDATES:
        if candidate.is_dir():
            return candidate

    # Fallback: search immediate subdirectories for audio files.
    for directory in BASE_DIR.iterdir():
        if directory.is_dir():
            if any(
                file.suffix.lower() in AUDIO_EXTENSIONS
                for file in directory.rglob("*")
                if file.is_file()
            ):
                return directory

    return None


def detect_variant(path):
    """Identify the audio variant from the folder path."""
    folders = [normalize(part) for part in path.parts[:-1]]

    # Check the most specific folder names first.
    for folder in reversed(folders):
        if "reference audio" in folder:
            if folder.startswith("without"):
                return "without_reference"
            if folder.startswith("with"):
                return "with_reference"

        if "prompt" in folder or "prompting" in folder:
            if folder.startswith("without"):
                return "without_prompt"
            if folder.startswith("with"):
                return "with_prompt"

    return None


def detect_global_sentence_number(filename):
    """
    Prompt audio filenames use global numbering, for example:
    1_assertive_no_prompt.wav
    12_imperative-command_prompt.wav
    """
    match = re.match(r"^\s*(\d{1,2})(?:[_\s.-]|$)", filename)

    if match:
        number = int(match.group(1))
        if 1 <= number <= 18:
            return number

    return None


def detect_reference_sentence_number(filename, category_name):
    """
    Reference audio filenames use category-local numbering:
    assertive_01.wav
    interrogative_02.wav
    imperative_command_03.wav
    exclamatory_happy_01.wav
    """
    stem = normalize(Path(filename).stem)

    category_patterns = {
        "Assertive": r"assertive",
        "Interrogative": r"interrogative",
        "Imperative — Request": r"imperative request",
        "Imperative — Command": r"imperative command",
        "Exclamatory — Sad": r"exclamatory sad",
        "Exclamatory — Happy": r"exclamatory happy",
    }

    pattern = category_patterns[category_name]

    if not re.search(pattern, stem):
        return None

    # Extract the final number, including names such as _01 or _03.
    match = re.search(r"(\d{1,2})$", stem)

    if not match:
        return None

    local_number = int(match.group(1))

    if local_number not in (1, 2, 3):
        return None

    category_sentences = SENTENCES[category_name]
    return category_sentences[local_number - 1][0]


# ============================================================
# BUILD AUDIO INDEX
# ============================================================

def build_audio_index(dataset_root):
    """
    Creates:
        audio_index[sentence_number][variant] = audio_path

    Supports both global numbering and category-local numbering.
    """
    audio_index = {
        number: {}
        for sentences in SENTENCES.values()
        for number, _ in sentences
    }

    if dataset_root is None:
        return audio_index, []

    all_audio_files = sorted(
        (
            file
            for file in dataset_root.rglob("*")
            if file.is_file()
            and file.suffix.lower() in AUDIO_EXTENSIONS
        ),
        key=lambda file: str(file).lower(),
    )

    for file in all_audio_files:
        variant = detect_variant(file)

        if variant is None:
            continue

        if variant in ("with_reference", "without_reference"):
            # Reference files use local numbering inside each category.
            for category_name in SENTENCES:
                number = detect_reference_sentence_number(
                    file.name, category_name
                )

                if number is not None:
                    audio_index[number].setdefault(variant, file)
                    break

        else:
            # Prompt files use global numbering from 1 to 18.
            number = detect_global_sentence_number(file.name)

            if number is not None:
                audio_index[number].setdefault(variant, file)

    return audio_index, all_audio_files


# ============================================================
# USER INTERFACE
# ============================================================

st.title("🎧 IIIT-H Audio Dataset")
st.caption(
    "Compare prompted, unprompted, reference-audio, "
    "and no-reference-audio recordings."
)

dataset_root = find_dataset_root()

if dataset_root is None:
    st.error(
        "Dataset folder not found. Place your extracted `IIIT-h` "
        "folder in the same directory as `app.py`."
    )
    st.code(
        "project_folder/\n"
        "├── app.py\n"
        "└── IIIT-h/\n"
        "    ├── Declarative/\n"
        "    ├── Interrogative /\n"
        "    ├── Imperative/\n"
        "    └── Exclamatory/"
    )
    st.stop()

audio_index, all_audio_files = build_audio_index(dataset_root)

st.success(f"Dataset loaded: `{dataset_root.name}`")

# Summary
total_audio_files = len(all_audio_files)
indexed_combinations = sum(
    len(variants) for variants in audio_index.values()
)

col1, col2, col3 = st.columns(3)
col1.metric("Audio files discovered", total_audio_files)
col2.metric("Audio combinations matched", indexed_combinations)
col3.metric("Expected combinations", 72)

st.divider()

# Search and category filter
search_text = st.text_input(
    "Search sentences",
    placeholder="Type a word or sentence...",
)

category_options = ["All Categories"] + list(SENTENCES.keys())

selected_category = st.selectbox(
    "Filter by sentence type",
    category_options,
)

show_missing = st.checkbox(
    "Show missing audio warnings",
    value=True,
)

st.divider()


# ============================================================
# RENDER SENTENCES AND AUDIO PLAYERS
# ============================================================

missing_items = []

for category_name, sentences in SENTENCES.items():

    if (
        selected_category != "All Categories"
        and selected_category != category_name
    ):
        continue

    matching_sentences = [
        (number, sentence)
        for number, sentence in sentences
        if search_text.strip().lower() in sentence.lower()
    ]

    if not matching_sentences:
        continue

    st.header(category_name)

    for number, sentence in matching_sentences:

        st.subheader(f"{number}. {sentence}")

        columns = st.columns(4)

        for column, (variant_key, variant_label) in zip(
            columns, VARIANTS.items()
        ):
            with column:
                st.markdown(f"**{variant_label}**")

                audio_path = audio_index[number].get(variant_key)

                if audio_path and audio_path.is_file():
                    try:
                        with open(audio_path, "rb") as audio_file:
                            audio_bytes = audio_file.read()

                        st.audio(
                            audio_bytes,
                            format=(
                                "audio/mpeg"
                                if audio_path.suffix.lower() == ".mp3"
                                else "audio/wav"
                                if audio_path.suffix.lower() == ".wav"
                                else None
                            ),
                        )

                        st.download_button(
                            label="Download audio",
                            data=audio_bytes,
                            file_name=audio_path.name,
                            mime=(
                                "audio/mpeg"
                                if audio_path.suffix.lower() == ".mp3"
                                else "audio/wav"
                                if audio_path.suffix.lower() == ".wav"
                                else "application/octet-stream"
                            ),
                            key=f"download_{number}_{variant_key}",
                        )

                    except OSError as error:
                        st.error(f"Could not read audio: {error}")

                else:
                    st.warning("Audio file not found")

                    missing_items.append(
                        (number, category_name, variant_label)
                    )

        st.divider()


# ============================================================
# DIAGNOSTICS
# ============================================================

with st.expander("Dataset diagnostics"):
    st.write("**Dataset directory:**", str(dataset_root))
    st.write("**Audio files discovered:**", total_audio_files)
    st.write("**Matched audio combinations:**", indexed_combinations)

    if missing_items:
        st.write("**Missing combinations:**")
        for number, category, variant in missing_items:
            st.write(f"- Sentence {number} — {category} — {variant}")
    else:
        st.success("All 72 sentence/variant combinations were found.")

    st.write("**Discovered audio files:**")
    for file in all_audio_files:
        st.code(str(file.relative_to(dataset_root)))