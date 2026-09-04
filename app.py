import io

from google import genai
import streamlit as st
from PIL import Image, UnidentifiedImageError


PAGE_TITLE = "PrismText"
MODEL_NAME = "gemini-3.5-flash"


def get_client(api_key: str) -> genai.Client:
    """Create a Gemini client for the current request."""
    return genai.Client(api_key=api_key)


def extract_mermaid(markdown: str) -> str:
    """Keep only Mermaid syntax when the model returns a fenced response."""
    cleaned = markdown.strip()
    if not cleaned.startswith("```mermaid"):
        return cleaned

    cleaned = cleaned.removeprefix("```mermaid").strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()
    return f"```mermaid\n{cleaned}\n```"


def generate_diagram(client: genai.Client, user_text: str) -> str:
    prompt = """
You are an expert information designer. Convert the user's text into a concise,
accurate Mermaid flowchart that conveys its processes, comparisons, and hierarchy.

Requirements:
- Use either `flowchart LR` or `flowchart TD`.
- Keep labels short and escape special Mermaid-breaking characters.
- Use meaningful node identifiers and clear directed edges.
- Use this dark-background palette in explicit styles: core #A855F7/#C084FC,
  process #06B6D4/#22D3EE, success #10B981/#34D399, alert #EF4444/#F87171.
- Give nodes 2px borders and white text.
- Return only one fenced Mermaid block, starting with ```mermaid and ending with ```.
"""
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[prompt, user_text],
    )
    if not response.text:
        raise ValueError("Gemini returned no diagram content.")
    return extract_mermaid(response.text)


def summarize_image(client: genai.Client, image: Image.Image) -> str:
    prompt = """
You are a document analyst. Examine this infographic or diagram carefully.
Extract its labels, values, relationships, hierarchy, and chronological flow into
a complete professional Markdown document. Use headings and bullet lists where
they clarify the source. Do not invent details that are not visible. Return only
the Markdown content, with no conversational preface.
"""
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[prompt, image],
    )
    if not response.text:
        raise ValueError("Gemini returned no summary content.")
    return response.text


def load_image(uploaded_file: st.runtime.uploaded_file_manager.UploadedFile) -> Image.Image:
    image_bytes = uploaded_file.getvalue()
    with Image.open(io.BytesIO(image_bytes)) as source_image:
        return source_image.convert("RGB")


def clear_workspace() -> None:
    st.session_state.source_text = ""
    st.session_state.diagram = ""
    st.session_state.summary = ""


def load_example() -> None:
    st.session_state.source_text = (
        "Launch a product in three stages: validate customer demand, build the "
        "minimum viable product, then measure adoption and improve."
    )


st.set_page_config(page_title=PAGE_TITLE, page_icon="P", layout="wide")
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
        .stApp { background: #101419; color: #edf1f4; font-family: 'Manrope', sans-serif; }
        [data-testid="stHeader"] { background: rgba(16, 20, 25, 0.94); }
        [data-testid="stSidebar"] { background: #171c22; }
        [data-testid="stSidebar"] > div:first-child { border-right: 1px solid #2b333c; }
        .block-container { max-width: 1440px; padding: 4rem 2rem 2rem; }
        .workspace-title { font-size: 1.25rem; font-weight: 800; letter-spacing: 0; margin: 0; }
        .workspace-subtitle { color: #98a3ad; font-size: 0.85rem; margin: 0.2rem 0 1.25rem; }
        .panel-label { color: #9ca8b3; font-size: 0.72rem; font-weight: 800; letter-spacing: 0.12rem; text-transform: uppercase; margin-bottom: 0.55rem; }
        .panel { background: #171c22; border: 1px solid #2b333c; border-radius: 8px; padding: 1rem; min-height: 32rem; }
        .empty-canvas { color: #6f7b86; text-align: center; padding: 8rem 1rem; font-size: 0.92rem; }
        .stTextArea textarea { background: #171c22; border: 1px solid #36414b; border-radius: 7px; color: #edf1f4; font-family: 'DM Mono', monospace; font-size: 0.9rem; line-height: 1.6; }
        .stTextArea textarea:focus { border-color: #67d3c3; box-shadow: 0 0 0 1px #67d3c3; }
        .stButton > button { border-radius: 6px; font-weight: 700; min-height: 2.5rem; }
        .stButton > button[kind="primary"] { background: #61cbb9; border-color: #61cbb9; color: #0f1a1c; }
        .stDownloadButton > button { border-radius: 6px; }
        .stFileUploader { border: 1px dashed #46525e; border-radius: 7px; padding: 0.25rem 0.75rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

for state_key, default_value in {
    "source_text": "",
    "diagram": "",
    "summary": "",
}.items():
    if state_key not in st.session_state:
        st.session_state[state_key] = default_value

secret_key = st.secrets.get("GEMINI_API_KEY", "")
if secret_key:
    api_key = secret_key
    st.sidebar.success("Gemini is connected.")
else:
    api_key = st.sidebar.text_input(
        "Gemini API key",
        type="password",
        help="Used only for this Streamlit session. Configure GEMINI_API_KEY in Streamlit secrets for deployment.",
    )
st.sidebar.divider()
st.sidebar.caption("PrismText keeps your idea and its visual counterpart in one workspace.")

title_column, actions_column = st.columns([8, 2])
with title_column:
    st.markdown('<p class="workspace-title">PrismText</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="workspace-subtitle">From rough notes to a clear visual argument.</p>',
        unsafe_allow_html=True,
    )
with actions_column:
    st.button("Clear", use_container_width=True, on_click=clear_workspace)

text_column, visual_column = st.columns(2, gap="large")

with text_column:
    st.markdown('<p class="panel-label">Source</p>', unsafe_allow_html=True)
    user_text = st.text_area(
        "Write or paste your idea",
        key="source_text",
        height=410,
        label_visibility="collapsed",
        placeholder="Start with the message you want people to understand...",
    )
    helper_column, example_column = st.columns([3, 2])
    with helper_column:
        st.caption("Describe a process, comparison, or framework.")
    with example_column:
        st.button("Use example", use_container_width=True, on_click=load_example)
    visualize_clicked = st.button("Generate visual", type="primary", use_container_width=True)

with visual_column:
    st.markdown('<p class="panel-label">Visual</p>', unsafe_allow_html=True)
    uploaded_image = st.file_uploader(
        "Import a diagram instead",
        type=["png", "jpg", "jpeg"],
        key="uploaded_diagram",
    )

    if not uploaded_image and not st.session_state.diagram:
        st.markdown(
            '<div class="panel"><div class="empty-canvas">Your generated visual will appear here.<br><br>Or import a diagram to turn it back into structured text.</div></div>',
            unsafe_allow_html=True,
        )
    elif st.session_state.diagram:
        st.markdown(st.session_state.diagram)
        st.download_button(
            "Download Mermaid source",
            data=st.session_state.diagram,
            file_name="prismtext-diagram.md",
            mime="text/markdown",
            use_container_width=True,
        )

if visualize_clicked:
    if not user_text.strip():
        text_column.warning("Add some text before creating a diagram.")
    elif not api_key:
        st.sidebar.warning("Enter a Gemini API key to activate PrismText.")
    else:
        try:
            with visual_column, st.spinner("Building visual structure..."):
                diagram = generate_diagram(get_client(api_key), user_text)
                st.session_state.diagram = diagram
                st.rerun()
        except Exception as error:
            visual_column.error(f"Diagram generation failed: {error}")

if uploaded_image is not None:
    try:
        image = load_image(uploaded_image)
        visual_column.image(image, caption="Uploaded diagram", use_container_width=True)
        if not api_key:
            st.sidebar.warning("Enter a Gemini API key to summarize the image.")
        else:
            with text_column, st.spinner("Extracting visual structure..."):
                summary = summarize_image(get_client(api_key), image)
                st.session_state.summary = summary
            st.markdown("#### Extracted notes")
            st.markdown(st.session_state.summary)
    except UnidentifiedImageError:
        visual_column.error("The uploaded file is not a readable image.")
    except Exception as error:
        text_column.error(f"Image analysis failed: {error}")