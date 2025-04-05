import datetime
import random
import os.path
import pytz # Thư viện xử lý múi giờ

from typing import List, Dict, Any, Optional, Tuple

# --- Google Calendar API Imports ---
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- Bộ 10 câu hỏi gốc (Sử dụng ID từ 1 đến 10) ---
# (Giữ nguyên định nghĩa QUESTIONS_BANK như trước)
QUESTIONS_BANK = {
    1: "Thử thách lớn nhất trong công việc tuần này của bạn là gì và nó khiến bạn cảm thấy thế nào?",
    2: "Hãy kể về một lần bạn cảm thấy tự hào về công việc của mình gần đây. Điều gì đã dẫn đến cảm giác đó?",
    3: "Bạn cảm thấy thế nào về khối lượng công việc hiện tại? Có điều gì đặc biệt gây căng thẳng hoặc bạn thấy dễ dàng kiểm soát không?",
    4: "Việc nhận phản hồi (tích cực hoặc tiêu cực) gần đây về công việc đã khiến bạn cảm thấy ra sao?",
    5: "Mô tả một tương tác gần đây với đồng nghiệp hoặc quản lý mà bạn thấy đáng chú ý và những cảm xúc mà nó mang lại.",
    6: "Khía cạnh nào trong công việc hiện tại khiến bạn cảm thấy có động lực hoặc hứng thú nhất? Tại sao?",
    7: "Có điều gì về các dự án hoặc nhiệm vụ hiện tại đang khiến bạn cảm thấy thất vọng hoặc bối rối không? Vui lòng giải thích rõ hơn về cảm giác đó.",
    8: "Bạn thường cảm thấy thế nào khi phải hợp tác với nhóm của mình trong một nhiệm vụ khó khăn?",
    9: "Bạn thường cảm thấy thế nào trước một cuộc họp hoặc buổi thuyết trình quan trọng?",
    10: "Nếu có thể thay đổi một điều trong ngày làm việc để cải thiện trạng thái tinh thần/cảm xúc của mình, bạn sẽ thay đổi điều gì và tại sao?"
}


# --- Lớp UserProfile (Giữ nguyên định nghĩa UserProfile như trước) ---
class UserProfile:
    """
    Lớp lưu trữ hồ sơ người dùng và lịch sử check-in cảm xúc hàng ngày.
    """
    def __init__(self, user_id: str, user_name: Optional[str] = None):
        if not user_id:
            raise ValueError("User ID cannot be empty.")
        self.user_id: str = user_id
        self.user_name: Optional[str] = user_name
        self.checkin_history: List[Dict[str, Any]] = []
        self.scheduled_time: Optional[str] = None # Lưu giờ hẹn check-in
        print(f"UserProfile created for user ID: {self.user_id}")

    def get_random_questions(self, num_questions: int = 2) -> List[Tuple[int, str]]:
        if num_questions > len(QUESTIONS_BANK):
            num_questions = len(QUESTIONS_BANK)
            print(f"Warning: Requested more questions than available. Returning {num_questions}.")
        if num_questions <= 0:
             raise ValueError("Number of questions must be positive.")
        question_ids = random.sample(list(QUESTIONS_BANK.keys()), num_questions)
        return [(qid, QUESTIONS_BANK[qid]) for qid in question_ids]

    def add_checkin(self,
                    question_ids: List[int],
                    responses: Dict[int, str],
                    timestamp: Optional[datetime.datetime] = None,
                    detected_emotions: Optional[Dict[int, List[str]]] = None,
                    detected_topics: Optional[Dict[int, List[str]]] = None,
                    overall_sentiment: Optional[str] = None):
        if timestamp is None:
            tz = pytz.timezone('Asia/Ho_Chi_Minh') # Sử dụng múi giờ VN
            timestamp = datetime.datetime.now(tz)
        if set(question_ids) != set(responses.keys()):
            print(f"Warning: Mismatch between question_ids {question_ids} and response keys {list(responses.keys())}. Storing anyway.")
        checkin_record = {
            "timestamp": timestamp.isoformat(),
            "question_ids": sorted(question_ids),
            "responses": responses,
            "detected_emotions": detected_emotions or {},
            "detected_topics": detected_topics or {},
            "overall_sentiment": overall_sentiment
        }
        self.checkin_history.append(checkin_record)
        print(f"Check-in record added for user {self.user_id} at {timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    def get_history(self) -> List[Dict[str, Any]]:
        return self.checkin_history

    def get_latest_checkin(self) -> Optional[Dict[str, Any]]:
        if not self.checkin_history:
            return None
        return self.checkin_history[-1]

    def set_scheduled_time(self, time_str: str):
        """Lưu lại giờ hẹn check-in mong muốn."""
        # Nên có validation định dạng HH:MM ở đây
        self.scheduled_time = time_str
        print(f"Check-in time preference set to {time_str} for user {self.user_id}")

    def __str__(self) -> str:
        name_part = f" ({self.user_name})" if self.user_name else ""
        schedule_part = f", Scheduled: {self.scheduled_time}" if self.scheduled_time else ""
        return f"UserProfile(UserID: {self.user_id}{name_part}, Check-ins: {len(self.checkin_history)}{schedule_part})"

    def __repr__(self) -> str:
        return f"<UserProfile user_id='{self.user_id}' checkins={len(self.checkin_history)}>"


# --- Google Calendar Integration ---
SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
TOKEN_FILE = 'token.json'
TIMEZONE = 'Asia/Ho_Chi_Minh' # Múi giờ Việt Nam

def get_calendar_service():
    """Xác thực và trả về đối tượng service để tương tác với Google Calendar API."""
    creds = None
    # File token.json lưu trữ access và refresh tokens, được tạo tự động
    # sau lần xác thực đầu tiên.
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    # Nếu không có credentials hợp lệ, cho người dùng đăng nhập.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                 print(f"Error refreshing token: {e}. Need to re-authenticate.")
                 # Xóa token cũ nếu refresh lỗi để chạy lại flow
                 if os.path.exists(TOKEN_FILE):
                    os.remove(TOKEN_FILE)
                 flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                 creds = flow.run_local_server(port=0)
        else:
            # Nếu không có token.json hoặc refresh không được, chạy flow mới
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"ERROR: Credentials file '{CREDENTIALS_FILE}' not found.")
                print("Please download it from Google Cloud Console and place it in the same directory.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0) # Mở trình duyệt để user xác thực
        # Lưu credentials cho lần chạy tiếp theo
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('calendar', 'v3', credentials=creds)
        print("Google Calendar service created successfully.")
        return service
    except HttpError as error:
        print(f'An error occurred creating Calendar service: {error}')
        return None
    except Exception as e:
        print(f'An unexpected error occurred: {e}')
        return None


def create_daily_checkin_event(service, user_time_str: str):
    """
    Tạo một sự kiện lặp lại hàng ngày trên Google Calendar.

    Args:
        service: Đối tượng service của Google Calendar API.
        user_time_str (str): Thời gian mong muốn check-in (định dạng HH:MM).

    Returns:
        bool: True nếu tạo thành công, False nếu thất bại.
    """
    try:
        # 1. Phân tích thời gian người dùng nhập
        hour, minute = map(int, user_time_str.split(':'))

        # 2. Lấy múi giờ và thời gian hiện tại
        tz = pytz.timezone(TIMEZONE)
        now = datetime.datetime.now(tz)

        # 3. Tính toán thời gian bắt đầu cho sự kiện *tiếp theo*
        start_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # Nếu thời gian đặt lịch đã qua trong ngày hôm nay, đặt cho ngày mai
        if start_time <= now:
            start_time += datetime.timedelta(days=1)

        # 4. Tính thời gian kết thúc (ví dụ: 15 phút sau khi bắt đầu)
        end_time = start_time + datetime.timedelta(minutes=15)

        # 5. Định dạng thời gian theo ISO 8601
        start_iso = start_time.isoformat()
        end_iso = end_time.isoformat()

        # 6. Tạo cấu trúc dữ liệu cho sự kiện
        event = {
            'summary': 'Emotional Check-in Reminder',
            'description': 'Đến giờ check-in cảm xúc với AI assistant của bạn.',
            'start': {
                'dateTime': start_iso,
                'timeZone': TIMEZONE,
            },
            'end': {
                'dateTime': end_iso,
                'timeZone': TIMEZONE,
            },
            'recurrence': [
                'RRULE:FREQ=DAILY' # Quy tắc lặp lại hàng ngày
            ],
            'reminders': { # Thêm nhắc nhở (tùy chọn)
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 10}, # Nhắc nhở popup trước 10 phút
                ],
            },
        }

        # 7. Gọi API để tạo sự kiện
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Event created successfully! Link: {created_event.get('htmlLink')}")
        return True

    except ValueError:
        print("Invalid time format. Please use HH:MM (e.g., 09:30).")
        return False
    except HttpError as error:
        print(f'An error occurred creating the event: {error}')
        return False
    except Exception as e:
        print(f'An unexpected error occurred during event creation: {e}')
        return False

# --- Hàm chính để tương tác với người dùng ---
def main():
    user_id = input("Please enter your user ID (e.g., NV001): ")
    user_name = input("Please enter your name (optional, press Enter to skip): ")
    profile = UserProfile(user_id=user_id, user_name=user_name or None)

    # Hỏi người dùng có muốn đặt lịch check-in không
    schedule_consent = input("Do you want to schedule a daily emotional check-in reminder in your Google Calendar? (yes/no): ").lower()

    if schedule_consent == 'yes':
        while True:
            schedule_time_str = input("What time would you like to schedule the daily check-in? (Please use HH:MM format, 24-hour clock, e.g., 09:30 or 17:00): ")
            # Validate định dạng cơ bản
            try:
                hour, minute = map(int, schedule_time_str.split(':'))
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    profile.set_scheduled_time(schedule_time_str) # Lưu giờ vào profile
                    break # Thoát vòng lặp nếu thời gian hợp lệ
                else:
                    print("Invalid hour or minute value. Please try again.")
            except ValueError:
                print("Invalid format. Please use HH:MM (e.g., 09:30).")

        # Lấy service Calendar (sẽ yêu cầu xác thực nếu cần)
        print("\nAttempting to access Google Calendar...")
        calendar_service = get_calendar_service()

        if calendar_service:
            print(f"\nAttempting to create a daily recurring event at {profile.scheduled_time} ({TIMEZONE})...")
            success = create_daily_checkin_event(calendar_service, profile.scheduled_time)
            if success:
                print("Scheduling successful!")
            else:
                print("Failed to schedule the event in Google Calendar.")
        else:
            print("Could not connect to Google Calendar service. Scheduling aborted.")
    else:
        print("Okay, no reminder will be scheduled.")

    # --- (Tùy chọn) Có thể thêm logic check-in ngay tại đây nếu muốn ---
    # print("\nLet's do a quick check-in now?")
    # questions = profile.get_random_questions(2)
    # ... (logic hỏi và lưu câu trả lời)

    print(f"\nFinal Profile State: {profile}")

if __name__ == '__main__':
    main()