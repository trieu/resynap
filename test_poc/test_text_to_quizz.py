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
In Vietnamese, just return raw html (no ```html) like this:

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
          Cơ bản
            Bài học ngắn
            Chủ đề trọng tâm
            Thân thiện với thiết bị di động
          Lợi ích
            Học nhanh hơn
            Tương tác cao hơn
            Nhớ lâu hơn
          Định dạng
              Short Video
              Visual Mindmap
              Mini Test
              Flashcard
          Trường hợp sử dụng
              Đào tạo nhân viên
              Phát triển kỹ năng
              Phát triển bản thân

'''


model_config = genai.GenerationConfig(temperature=0.1)
response = gemini_text_model.generate_content(prompt, generation_config=model_config)
answer_text = response.text 

print(answer_text)
