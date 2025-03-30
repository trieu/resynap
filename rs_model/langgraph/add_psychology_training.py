from rs_model.langgraph.langgraph_ai import DatabaseManager
from rs_model.langgraph.conversation_models import ConversationState, UserConversationState

from google import genai
import os
from dotenv import load_dotenv


load_dotenv(override=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Usegemini-2.0-flash for fast mindmap generation
GEMINI_MODEL_ID = "gemini-2.0-flash"

# Configure your API key
genai_client = genai.Client(api_key=GEMINI_API_KEY)

# Initialize DatabaseManager
db_manager = DatabaseManager()

# Psychology expert training data
training_data = [
    ConversationState("Psychologist", "journey_stress", "office_consultation",
                      "Tôi luôn cảm thấy lo lắng.", "Hãy thử bài tập thở sâu."),

    ConversationState("Psychologist", "journey_relationship", "therapy_session",
                      "Làm thế nào để xử lý mâu thuẫn trong mối quan hệ?", "Lắng nghe một cách chủ động trước khi trả lời."),

    ConversationState("Psychologist", "journey_sleep", "online_chat",
                      "Tôi không thể ngủ vào ban đêm.", "Tránh sử dụng màn hình điện thoại 1 giờ trước khi ngủ."),

    ConversationState("Psychologist", "journey_self_confidence", "coaching",
                      "Tôi gặp khó khăn với sự tự tin.", "Hãy thực hành khẳng định bản thân hàng ngày."),

    ConversationState("Psychologist", "journey_motivation", "mentorship",
                      "Làm thế nào để tôi luôn có động lực?", "Đặt ra mục tiêu nhỏ và dễ đạt được, sau đó tự thưởng cho mình."),

    ConversationState("HR", "journey_new_employee", "mentorship",
                      "Các bước cho nhân viên mới ở công ty ra sao?", "Hãy giới thiệu văn hóa công ty và các quy trình làm việc cơ bản."),
]

# ✅ Thêm dữ liệu huấn luyện vào cơ sở dữ liệu
for state in training_data:
    db_manager.save_conversation_state(state)

print("✅ 5 ví dụ huấn luyện cho chuyên gia tâm lý đã được thêm thành công!")


def search_with_ai_agent(GEMINI_MODEL_ID, genai_client, user_input):
    # Search for conversations based on user input
    search_results = db_manager.load_conversation_state(user_input)
    print(f"🔍 Kết quả tìm kiếm cho [{user_input}] \n ")
    for search_result in search_results:
        score = search_result.score
        payload = search_result.payload
        agent_role = payload["agent_role"]
        context = payload["context"]
        response = payload["response"]
        print(
            f"score: {score} agent role: {agent_role} context: {context} response: {response} ")

        mindmap_prompt = f""" You are a {agent_role} and you are responding to a user who said: "{user_input}".
            Create a mindmap structure in mermaid.js format based on the following topic: "{response}".
            Focus on breaking down the main topic into related concepts and subtopics.
            Do not include any explanation, just the mermaid mindmap code in plain text in the same language with topic.
        """

        mindmap_response = genai_client.models.generate_content(
            model=GEMINI_MODEL_ID, contents=mindmap_prompt)
        mindmap = mindmap_response.text
        print("\n mindmap ", mindmap)


def main():
    user_input = "Tôi lo lắng về tương lai"
    search_with_ai_agent(GEMINI_MODEL_ID, genai_client, user_input)

    user_input = "Tôi là nhân viên mới, tôi cần hướng dẫn"
    search_with_ai_agent(GEMINI_MODEL_ID, genai_client, user_input)
