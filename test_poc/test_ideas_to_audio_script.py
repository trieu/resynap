from dotenv import load_dotenv
import os
from google.genai import types, Client

from test_text_to_speech import get_language_name

# Load environment variables
load_dotenv(override=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Use gemini-2.0-flash for fast mindmap generation
GEMINI_MODEL_ID = "gemini-2.0-flash"

genai_client = Client(api_key=GEMINI_API_KEY)


def generate_audio_script(name, description, type="group", gender="neutral"):
    """Generates audio_script based on content using Google GenAI."""

    if len(description) > 0 and len(name) > 0:
        print(f"Generating audio script for {type} with name '{name}' and description '{description}'")
        
        language_name = get_language_name(description)
        if not language_name:
            print("Could not detect language. Using default English")
            language_name = "English"
            
        # Generate audio script based on the description
        prompt = f"""
            Please respond to the following prompt without including any explicit instructions or meta-instructions in your response:
            Generate a speech content for text-to-speech engine, so it can convert from text to audio, using the given description: "{description}".  
            The content should be tailored for {type} named "{name}", gender "{gender}" and must be written exclusively in the language "{language_name}".             
        """
        
        generate_content_config = types.GenerateContentConfig(
            temperature=0.5,
            max_output_tokens=8192,
            response_mime_type="text/plain",
        )
        
        response = genai_client.models.generate_content(model=GEMINI_MODEL_ID, contents=prompt, config=generate_content_config)
        return response.text.strip()
        
    else:
        print("Invalid input. Please provide a valid name and description.")
        return ""
    
    
def count_words(text: str) -> int:
    """Counts the number of words in a given text."""
    return len(text.split())

def generate_video_title(name, description):
    """Generates a video title based on content using Google GenAI."""

    max_length = 30  # Maximum length of the video title
    if len(description) > 0 and len(name) > 0:
        
        language_name = get_language_name(description)
        if not language_name:
            print("Could not detect language. Using default English")
            language_name = "English"
            
        # Constructing the prompt to generate a short, engaging video title
        prompt = (
            f"Please respond to the following prompt without including any explicit instructions or meta-instructions in your response:\n"
            f"Generate a short and engaging video title in {language_name} based on the following description. "
            f"The title must be less than {max_length} words, compelling, and relevant to the content:\n"
            f"Description: {description}"
        )
        
        generate_content_config = types.GenerateContentConfig(
            temperature=0.42,
            max_output_tokens=100,  # Keeping it short and concise
            response_mime_type="text/plain",
        )
        
        response = genai_client.models.generate_content(
            model=GEMINI_MODEL_ID,
            contents=prompt,
            config=generate_content_config
        )
        
        return response.text.strip()
        
    else:
        print("Invalid input. Please provide a valid name and description.")
        return ""

    
if __name__ == "__main__":
    # Example usage
    name = "Phòng công nghệ thông tin PNJ"
    description = '''
    🔥🔥 HACKATHON TUẦN #3 – AI CÂN CẢ HỆ THỐNG PHÁT THANH 🔥🔥
Có ai hay bị giật mình bởi "âm thanh tuổi thơ" của loa thông báo văn phòng không ạ? Nếu có một hệ thống AI thay thế các "phát thanh viên" thì sao ta? 💬 Hãy tưởng tượng sau một năm, AI đã len lỏi vào từng ngóc ngách doanh nghiệp, không chỉ văn phòng mà cả hệ thống cửa hàng đều được AI chăm sóc! Nghe cũng ngầu á! 😎
🤖 Hãy biến những ý tưởng đó thành hiện thực với đề bài tiếp theo trong chuỗi Hackathon là ỨNG DỤNG AI ĐỂ TẠO RA MỘT HỆ THỐNG CÓ THỂ SOẠN NỘI DUNG THÔNG BÁO, HẸN GIỜ PHÁT SÓNG VÀ GEN GIỌNG ĐỌC TỰ NHIÊN
🏆 Giải thưởng cực khủng
💍 1 sao PNJ xịn sò
💵 $20 để cà phê sang chảnh cả tuần
👉 Cách tham gia: Trình bày trực tiếp hoặc gửi video
👉Cách chấm điểm: Khán giả tham gia thảo luận trực tiếp + BGK chấm điểm
📅 Thứ 6 tuần này (21/3), từ 13:30 - Phòng CIO
Tham gia cho vui, lỡ đoạt giải thì vui hơnnn!
    
    '''
    audio_script = generate_video_title(name, description)
    print(audio_script)