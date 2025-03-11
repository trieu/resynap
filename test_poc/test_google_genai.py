import google.generativeai as genai
import os
import markdown
from dotenv import load_dotenv
load_dotenv()

GEMINI_MODEL = 'gemini-2.0-flash'
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
gemini_text_model = genai.GenerativeModel(model_name=GEMINI_MODEL)

book_title = 'Big Data and AI for Jewelry Brands'

question_for_toc = "Write a table of contents for the book '" + book_title + "'."
question_for_toc = question_for_toc + " Each chapter must begine with '##'"

section = "Automated data collection"
question_for_content = "You are the author of book '"+book_title+"'. Write a paragraph about '"+section+"'"

print("\n"+question_for_content+"\n")

model_config = genai.GenerationConfig(temperature=0.8)
response = gemini_text_model.generate_content(question_for_content, generation_config=model_config)
answer_text = response.text 

rs_html = markdown.markdown(answer_text, extensions=['fenced_code'])
print(answer_text)

print("\n HTML: \n "+rs_html+"\n")

