

from common_test_util import setup_test
setup_test()

from rs_agent.ai_core import GeminiClient
gemini_client = GeminiClient()


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



answer_text = gemini_client.generate_content(prompt, 0.2)

print(answer_text)
