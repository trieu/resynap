from rs_model.system_utils import read_json_from_file


def get_user_profile(profile_id: str):
    user_profile = read_json_from_file('./rs_agent/sample-test-user.json')
    return user_profile

def get_user_profile_for_ai_agent(profile_id: str):
    user_profile = read_json_from_file('./rs_agent/sample-test-user.json')
    # Remove sensitve attributes
    del user_profile["id"]
    return user_profile