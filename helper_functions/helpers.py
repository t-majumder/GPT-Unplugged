import base64
import html
import re
import streamlit as st

def get_base64_of_background_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

def load_css(file_path):
    with open(file_path, "r") as f:
        css = f"<style>{f.read()}</style>"
        st.markdown(css, unsafe_allow_html=True)

def get_context(documents):
    return "\n\n".join([doc.page_content for doc in documents])


def format_message_content(content):
    if not content:
        return ""

    # Escape HTML first, then unescape math delimiters so MathJax sees them unchanged
    escaped = html.escape(content)

    # Restore $ and $$ delimiters (unescape only those sequences)
    # We replace the escaped equivalents for $ and backslash sequences commonly used in LaTeX
    escaped = escaped.replace('\$\$', '$$')
    escaped = escaped.replace('\$', '$')

    # Convert simple markdown constructs (safe, applied after escaping)
    escaped = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', escaped)
    escaped = re.sub(r'\*(.*?)\*', r'<em>\1</em>', escaped)
    escaped = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', escaped, flags=re.DOTALL)
    escaped = re.sub(r'`(.*?)`', r'<code>\1</code>', escaped)

    # Bullet points
    escaped = re.sub(r'(?m)^- (.*)', r'<li>\1</li>', escaped)
    if '<li>' in escaped:
        escaped = '<ul>' + escaped + '</ul>'

    return escaped


def process_latex(text):
    return text if text is not None else ""

