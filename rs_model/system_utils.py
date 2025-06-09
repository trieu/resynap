import json


def read_json_from_file(file_path: str):
    """
    Đọc dữ liệu JSON từ một tệp.

    Args:
        file_path (str): Đường dẫn đến tệp JSON.

    Returns:
        dict hoặc list hoặc None: Dữ liệu JSON đã được giải mã, hoặc None nếu có lỗi xảy ra.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"Lỗi: Tệp '{file_path}' không tồn tại.")
        return None
    except json.JSONDecodeError:
        print(f"Lỗi: Tệp '{file_path}' không phải là JSON hợp lệ.")
        return None
    except Exception as e:
        print(f"Lỗi không xác định khi đọc tệp '{file_path}': {e}")
        return None
    return []
