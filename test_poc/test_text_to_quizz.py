import google.generativeai as genai
import os
import markdown
from dotenv import load_dotenv
load_dotenv()

GEMINI_MODEL = 'gemini-2.0-flash'
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
gemini_text_model = genai.GenerativeModel(model_name=GEMINI_MODEL)


prompt = ''' 
just return raw html (no ```html) like this:

  <div class="question" id="question1">
    <p>{{question}}</p>
    <div class="options">
      <div class="option">
        <label>
          <input type="radio" name="q1" value="a">A. {{option A}}</label>
      </div>
      <div class="option">
        <label>
          <input type="radio" name="q1" value="b">B. {{option B}}.</label>
      </div>
      <div class="option">
        <label>
          <input type="radio" name="q1" value="c">C.{{option C}}</label>
      </div>
      <div class="option">
        <label>
          <input type="radio" name="q1" value="d">D. {{option D}}.</label>
      </div>
    </div>
  </div>

The HTML is for  multiple choice quizz test for this mindmap: 

mindmap
          root((Microlearning))
            Basics
              Short Lessons
              Focused Topics
              Mobile-friendly
            Benefits
              Faster Learning
              Higher Engagement
              Better Retention
            Formats
              Videos
              Infographics
              Quizzes
              Podcasts
            Use Cases
              Employee Training
              Skill Development
              Onboarding

'''


model_config = genai.GenerationConfig(temperature=0.2)
response = gemini_text_model.generate_content(prompt, generation_config=model_config)
answer_text = response.text 

print(answer_text)
