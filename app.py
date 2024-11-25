import re
import streamlit as st
from jamaibase import JamAI, protocol as p
import os
import io
import dotenv
from fpdf import FPDF
import markdown

# Load the environment variables from the .env file
dotenv.load_dotenv()

# Load the API key and project ID from the environment variables
api_key = os.getenv("api_key")
project_id = os.getenv("project_id")


# Initialize JamAI with the provided API key and project ID
if not api_key or not project_id:
    st.error("API key or Project ID missing in environment variables!")
else:
    jamai = JamAI(api_key=api_key, project_id=project_id)

# Set up the Streamlit app
st.set_page_config(page_title="StoryWeaver", page_icon="📝")
st.title("StoryWeaver: Unleash Your Imagination with AI-Powered Storytelling")

# Custom CSS to style the UI
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;700&display=swap');
    body {
        background-color: #121212;
        color: #e0e0e0;
        font-family: 'Poppins', sans-serif;
    }
    .stApp {
        margin: 0 auto;
        background-color: #121212;
    }
    .stTitle, .stHeader h2 {
        color: #e0e0e0;
        font-weight: 700;
    }

    .generated-output h4 {
        color: #ff6b6b;
    }
    /* Gradient Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #6A11CB 0%, #2575FC 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 10px 20px;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(37, 117, 252, 0.3);
    }
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(37, 117, 252, 0.5);
    }
    /* Small Icon Buttons */
    button[data-baseweb="button"] {
        background: linear-gradient(135deg, #6A11CB 0%, #2575FC 100%);
        color: white;
        border: none;
        border-radius: 8px;
        transition: all 0.3s ease;
    }

    button[data-baseweb="button"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(37, 117, 252, 0.3);
    }

    /* Text Area Styling */
    textarea {
        font-family: 'Inter', sans-serif !important;
        line-height: 1.5 !important;
        padding: 12px !important;
    }
    /* Card-like Containers */
    .generated-output {
        background: linear-gradient(145deg, #1E2A3A, #172231);
        border-radius: 15px;
        padding: 25px;
        margin: 20px 0;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        border: 1px solid #2C3E50;
        color: #E0E6EF;
    }
    /* Progress Indicator */
    .stProgress > div > div {
        background-color: #4ECDC4 !important;
    }
    h1, h2, h3, h4, h5, h6 {
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# Sidebar for Advanced Controls
with st.sidebar:
    st.header("🛠️ Story Configuration")

    # Style Preferences
    writing_style = st.selectbox("Writing Style", [
        "Descriptive",
        "Minimalist",
        "Poetic",
        "Dramatic",
        "Humorous"
    ])

    # Tone Selection
    story_tone = st.selectbox("Story Tone", [
        "Serious",
        "Light-hearted",
        "Mysterious",
        "Inspirational",
        "Dark"
    ])

    # Advanced Story Parameters
    st.markdown("### Advanced Parameters")
    complexity = st.slider("Story Complexity", 1, 10, 5)

# Main Content Area
col1, col2 = st.columns([3, 1])

with col1:
    # Genre Selection with Preview
    st.header("📚 Choose Your Genre")
    # Read genres and subgenres from 'genres.txt' and organize them into a dictionary
    genres_dict = {}
    current_genre = None
    try:
        with open('genres.txt', 'r') as f:
            current_genre = None
            for line in f:
                line = line.strip()
                if line.startswith('###'):
                    current_genre = line.strip('# ').strip()
                    genres_dict[current_genre] = []
                elif line.startswith('-'):
                    genres_dict[current_genre].append(line.strip('- ').strip())
                elif line:
                    genres_dict[line] = []
    except FileNotFoundError:
        st.warning("⚠️ 'genres.txt' file not found. Please upload the file to proceed.")
        st.stop()

    # Add option for user to add their own genre
    genres = list(genres_dict.keys())
    genres.append('Add your own')

    # Genre selection
    selected_genre = st.selectbox('Choose a genre', options=genres)

    if selected_genre == 'Add your own':
        genre = st.text_input('Enter your own genre')
        genre_description = st.text_area('Describe your genre')
    else:
        subgenres = genres_dict.get(selected_genre, [])
        if subgenres:
            subgenres.insert(0, 'No specific subgenre')
            selected_subgenre = st.selectbox('Choose a subgenre', options=subgenres)
            if selected_subgenre == 'No specific subgenre':
                genre = selected_genre
            else:
                genre = selected_subgenre
        else:
            genre = selected_genre
    st.write(f"**Selected Genre:** {genre}")

with col2:
    # Display a placeholder image
    st.image("https://cdn.talkie-ai.com/talkie/prod/img/2024-01-23/3d77b23b-3898-43a8-8e65-ed8a11e480b4-1-5-400x0.webp", use_column_width=True)

# Character and Plot Inputs
# Initialize session states if not exists
if 'character_texts' not in st.session_state:
    st.session_state.character_texts = [{"id": 0, "text": ""}]
if 'plot_texts' not in st.session_state:
    st.session_state.plot_texts = [{"id": 0, "text": ""}]
if 'char_id_counter' not in st.session_state:
    st.session_state.char_id_counter = 1
if 'plot_id_counter' not in st.session_state:
    st.session_state.plot_id_counter = 1
if 'story_generated' not in st.session_state:
    st.session_state['story_generated'] = False
if 'full_story_generated' not in st.session_state:
    st.session_state['full_story_generated'] = False
if 'story_outline' not in st.session_state:
    st.session_state['story_outline'] = ''
if 'modified_outline' not in st.session_state:
    st.session_state['modified_outline'] = ''
if 'full_story' not in st.session_state:
    st.session_state['full_story'] = ''
if 'pdf' not in st.session_state:
    st.session_state['pdf'] = io.BytesIO()

def generate_story_outline(genre, main_characters, plot_elements, num_chapters, writing_style, story_tone, complexity, language):
    data = [{
        "genre": genre,
        "main_characters": main_characters,
        "plot_elements": plot_elements,
        "num_chapters": num_chapters,
        "writing_style": writing_style,
        "story_tone": story_tone,
        "complexity": complexity,
        "language": language,
    }]

    try:
        response = jamai.add_table_rows(
            "action",
            p.RowAddRequest(
                table_id="Outline",
                data=data,
                stream=False
            )
        )

        generated_outline = response.rows[0].columns["story_outline"].text
        return generated_outline
    except Exception as e:
        st.error(f"An error occurred while generating the outline: {e}")
        return None

def generate_full_story(story_outline, writing_style, story_tone, complexity, language):
    generated_story = ""
    # Initialize a single progress bar
    progress_bar = st.progress(0)
    # Initialize PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    for chapter_num in range(1, num_chapters + 1):
        data = [{
            "story_outline": story_outline,
            "generated_story": generated_story,
            "writing_style": writing_style,
            "story_tone": story_tone,
            "complexity": complexity,
            "language": language,
            "chapter": chapter_num
        }]

        try:
            response = jamai.add_table_rows(
                "action",
                p.RowAddRequest(
                    table_id="Story",
                    data=data,
                    stream=False
                )
            )

            generated_chapter = response.rows[0].columns["story"].text
            generated_story += f"{generated_chapter}\n\n"

            # Assuming the chapter starts with "**Chapter X: Title**"
            title_match = re.match(r"\*\*Chapter\s+\d+:\s*(.*?)\*\*", generated_chapter)
            if title_match:
                chapter_title = title_match.group(1).strip()
                # Remove the title from the content
                chapter_content = re.sub(r"\*\*Chapter\s+\d+:\s*.*?\*\*\n*", "", generated_chapter, count=1).strip()
            else:
                chapter_title = f"Chapter {chapter_num}"
                chapter_content = generated_chapter

            # Add a new page for the chapter
            pdf.add_page()
            
            # Add Chapter Title
            pdf.set_font("Arial", 'B', 16)  # Bold, 16pt
            pdf.multi_cell(0, 10, f"Chapter {chapter_num}", align='C')
            pdf.ln(10)  # Add some space after the title

            # Add Chapter Content
            pdf.set_font("Arial", size=12)  # Regular, 12pt
            pdf.multi_cell(0, 10, chapter_content)

            # Update the progress bar
            progress = chapter_num / num_chapters
            progress_bar.progress(progress)
        except Exception as e:
            st.error(f"An error occurred while generating the full story: {e}")
            return None
        # Save PDF to a BytesIO buffer
    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    return generated_story, pdf_buffer
    

with st.expander("📝 Story Details", expanded=True):
    col_chars, col_plot = st.columns(2)

    with col_chars:
        # Title row with add button
        col_char_title, col_char_btn = st.columns([5,1])
        with col_char_title:
            st.subheader("Main Characters")
        with col_char_btn:
            if st.button("➕", key="add_char", help="Add another character"):
                st.session_state.character_texts.append({
                    "id": st.session_state.char_id_counter,
                    "text": ""
                })
                st.session_state.char_id_counter += 1
                st.rerun()
        
        # Display all character text areas
        for i, char_data in enumerate(st.session_state.character_texts):
            col_text, col_del = st.columns([6,1])
            with col_text:
                text = st.text_area(
                    f"Character {i+1}",
                    value=char_data["text"],
                    height=250,
                    key=f"char_{char_data['id']}",
                    placeholder=(
                        "Name: [Character Name]\n"
                        "Role: [Main/Supporting]\n"
                        "Traits: [Key characteristics]\n"
                        "Background: [Brief history]\n"
                        "Goals: [Character motivations]"
                    )
                )
                # Update text in session state
                char_data["text"] = text
            
            with col_del:
                if st.button("🗑️", key=f"del_char_{char_data['id']}", help="Delete character"):
                    st.session_state.character_texts = [
                        c for c in st.session_state.character_texts if c["id"] != char_data["id"]
                    ]
                    st.rerun()

    with col_plot:
        # Title row with add button
        col_plot_title, col_plot_btn = st.columns([5,1])
        with col_plot_title:
            st.subheader("Plot Elements")
        with col_plot_btn:
            if st.button("➕", key="add_plot", help="Add another plot element"):
                st.session_state.plot_texts.append({
                    "id": st.session_state.plot_id_counter,
                    "text": ""
                })
                st.session_state.plot_id_counter += 1
                st.rerun()
        
        # Display all plot text areas
        for i, plot_data in enumerate(st.session_state.plot_texts):
            col_text, col_del = st.columns([6,1])
            with col_text:
                text = st.text_area(
                    f"Plot Element {i+1}",
                    value=plot_data["text"],
                    height=250,
                    key=f"plot_{plot_data['id']}",
                    placeholder=(
                        "Setting: [Time and place]\n"
                        "Conflict: [Main challenge/obstacle]\n"
                        "Themes: [Core ideas/messages]\n"
                        "Twists: [Unexpected events]\n"
                        "Resolution: [How the story ends]"
                    )
                )
                # Update text in session state
                plot_data["text"] = text
            
            with col_del:
                if st.button("🗑️", key=f"del_plot_{plot_data['id']}", help="Delete plot element"):
                    st.session_state.plot_texts = [
                        p for p in st.session_state.plot_texts if p["id"] != plot_data["id"]
                    ]
                    st.rerun()

# Generation Controls
st.markdown("---")
col_gen1, col_gen2 = st.columns(2)

with col_gen1:
    num_chapters = st.number_input("Number of Chapters", min_value=1, max_value=10, value=10)

with col_gen2:
    # Language Selection Dropdown
    languages = [
        "English",
        "Spanish",
        "French",
        "German",
        "Chinese",
        "Japanese",
        "Korean",
        "Russian",
        "Italian",
        "Portuguese",
        "Hindi",
        "Arabic",
        "Other"
    ]
    selected_language = "English"
    selected_language = st.selectbox(
        "Story Language",
        options=languages,
        index=0,
        help="Select the language in which the story will be written."
    )
    
    # If 'Other' is selected, provide a text input for custom language
    if selected_language == "Other":
        custom_language = st.text_input("Enter your language", placeholder="e.g., Swahili")
    else:
        custom_language = selected_language

# Use the final language value (custom_language if 'Other' was selected)
language = custom_language if selected_language == "Other" else selected_language

# Collect main characters and plot elements from session state
main_characters_list = [char_data["text"] for char_data in st.session_state.character_texts if char_data["text"].strip()]
plot_elements_list = [plot_data["text"] for plot_data in st.session_state.plot_texts if plot_data["text"].strip()]

# Convert lists to strings for prompt
main_characters = "\n\n".join(main_characters_list)
plot_elements = "\n\n".join(plot_elements_list)

# Generate Story Outline
if st.button("✨ Generate Story", use_container_width=True):
    if genre and num_chapters and language:
        with st.spinner("Weaving your story..."):
            st.session_state['story_outline'] = generate_story_outline(
                genre, main_characters, plot_elements,
                num_chapters, writing_style, story_tone, complexity, language
            )
            # Set flags
            st.session_state['story_generated'] = True
            st.session_state['full_story_generated'] = False  # Reset full story generated flag
    else:
        st.warning("⚠️ Please fill in all the inputs.")

# If story generated, display the outline and the 'Validate and Generate Full Story' button
if st.session_state['story_generated']:
    # Function to parse the outline into Introduction and Chapters
    def parse_outline(outline_text, num_chapters):
        # Extract Introduction
        intro_match = re.search(r"\*\*Introduction\*\*\n\n(.*?)\n\n(?=\*\*Chapter 1:)", outline_text, re.DOTALL)
        introduction = intro_match.group(1).strip() if intro_match else ""

        chapters = []
        for i in range(1, num_chapters + 1):
            chapter_pattern = rf"\*\*Chapter {i}: (.*?)\*\*\n\n(.*?)(?=\*\*Chapter {i+1}: |\Z)"
            match = re.search(chapter_pattern, outline_text, re.DOTALL)
            if match:
                title = match.group(1).strip()
                summary = match.group(2).strip()
                chapters.append({"title": title, "summary": summary})
        
        return introduction, chapters
    # Display the generated outline
    st.markdown("<h3>🖋️ Generated Story Outline</h3>", unsafe_allow_html=True)
    # Parse the existing story outline
    introduction, chapters = parse_outline(st.session_state['story_outline'], num_chapters)

    # Display Introduction (non-editable)
    st.markdown("**Introduction**")
    modified_introduction = st.text_area(
        "You can modify the Introduction below:",
        value=introduction,
        height=200,
        key="introduction"
    )

    # Editable Chapter Titles and Summaries
    st.markdown("### 📚 Chapters")

    modified_chapters = []
    for idx, chapter in enumerate(chapters, start=1):
        st.markdown(f"**Chapter {idx}:**")
        col1, col2 = st.columns([1, 3])
        with col1:
            # Editable Chapter Title
            new_title = st.text_input(f"Chapter {idx} Title", value=chapter['title'], key=f"title_{idx}")
        with col2:
            # Editable Summary
            new_summary = st.text_area(f"Chapter {idx} Summary", value=chapter['summary'], height=100, key=f"summary_{idx}")
        modified_chapters.append({"title": new_title, "summary": new_summary})

    # Reconstruct the modified outline
    modified_outline = f"**Introduction**\n\n{modified_introduction}\n\n"
    for idx, chapter in enumerate(modified_chapters, start=1):
        modified_outline += f"**Chapter {idx}: {chapter['title']}**\n\n{chapter['summary']}\n\n"

    st.session_state['modified_outline'] = modified_outline

    # Validate and Generate Full Story
    if st.button("✅ Validate and Generate Full Story", use_container_width=True):
        if st.session_state['modified_outline'].strip() == "":
            st.warning("⚠️ The outline is empty. Please provide an outline to generate the full story.")
        else:
            with st.spinner("Generating full story..."):
                st.session_state['full_story'],  st.session_state['pdf'] = generate_full_story(
                    st.session_state['modified_outline'],
                    writing_style, story_tone, complexity, language)
                st.session_state['full_story_generated'] = True

# If full story generated, display it and the download button
if st.session_state['full_story_generated']:
    full_story = st.session_state['full_story']
    html_full_story = markdown.markdown(full_story)
    st.write(f"""
    <div class="generated-output">
        <h3>📖 Your Generated Story</h3>
        {html_full_story}
    </div>
    """, unsafe_allow_html=True)
    # Ask user for the PDF name before saving
    pdf_name = st.text_input("Enter a name for your PDF (without extension):", "My_Story")

    # Ensure the PDF name is not empty and sanitize it
    if pdf_name.strip() == "":
        pdf_name = "Generated_Story"

    # Append .pdf extension if not provided
    if not pdf_name.lower().endswith(".pdf"):
        pdf_filename = f"{pdf_name}.pdf"
    else:
        pdf_filename = pdf_name

    # Download Button
    st.download_button(
        label="📄 Download Full Story as PDF",
        data=st.session_state['pdf'],
        file_name=pdf_filename,
        mime="application/pdf"
    )