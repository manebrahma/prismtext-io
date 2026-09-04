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


st.set_page_config(page_title=PAGE_TITLE, page_icon="P", layout="wide")
st.title("PrismText")
st.caption("Transform writing into visual structure, or reconstruct diagrams as clear text.")

secret_key = st.secrets.get("GEMINI_API_KEY", "")
api_key = st.sidebar.text_input(
    "Gemini API key",
    value=secret_key,
    type="password",
    help="Used only for this Streamlit session unless supplied through Streamlit secrets.",
)

text_column, visual_column = st.columns(2, gap="large")

with text_column:
    st.subheader("Text Canvas")
    user_text = st.text_area(
        "Concept or process notes",
        height=360,
        placeholder="Example: Build locally, push to GitHub, then deploy to the cloud.",
    )
    visualize_clicked = st.button("Create diagram", use_container_width=True)

with visual_column:
    st.subheader("Visual Canvas")
    uploaded_image = st.file_uploader(
        "Upload an infographic or diagram",
        type=["png", "jpg", "jpeg"],
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
                st.markdown(diagram)
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
                st.markdown(summary)
    except UnidentifiedImageError:
        visual_column.error("The uploaded file is not a readable image.")
    except Exception as error:
        text_column.error(f"Image analysis failed: {error}")