

import markdown
from common_test_util import setup_test
setup_test()

from rs_agent.ai_core import GeminiClient

class GeminiBookWriter:
    def __init__(self, gemini_client: GeminiClient):
        self.gemini_client = gemini_client

    def generate_markdown(self, book_title: str, section: str, language: str = 'English') -> str:
        prompt = (
            f"You are the author of the book '{book_title}'. "
            f"Write a chapter of the book about '{section}' in the language '{language}'."
            f"Just return the markdown code only. "
        )
        print(f"\n{prompt}\n")
        return self.gemini_client.generate_content(prompt)

    def render_html(self, markdown_text: str) -> str:
        return markdown.markdown(markdown_text, extensions=['fenced_code'])

    def write_section(self, book_title: str, section: str, language: str = 'English'):
        markdown_content = self.generate_markdown(book_title, section, language)
        html_content = self.render_html(markdown_content)

        print(markdown_content)
        print("\nHTML:\n" + html_content + "\n")


if __name__ == "__main__":
    book_title = "Big Data and AI for Retail"
    section = "Open Source AI-first CDP"

    gemini_client = GeminiClient()  # uses env vars by default
    writer = GeminiBookWriter(gemini_client)
    writer.write_section(book_title, section, 'Vietnamse')
