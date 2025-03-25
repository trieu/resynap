from langgraph_ai import DatabaseManager

# Initialize DatabaseManager
db_manager = DatabaseManager()

# Psychology expert training data
training_data = [
    ("Psychologist", "journey_stress", "office_consultation", "I feel anxious all the time.", "Try deep breathing exercises."),
    ("Psychologist", "journey_relationship", "therapy_session", "How do I handle conflicts in a relationship?", "Listen actively before responding."),
    ("Psychologist", "journey_sleep", "online_chat", "I can't sleep at night.", "Avoid screens 1 hour before bed."),
    ("Psychologist", "journey_self_confidence", "coaching", "I struggle with low self-esteem.", "Practice daily affirmations."),
    ("Psychologist", "journey_motivation", "mentorship", "How do I stay motivated?", "Set small, achievable goals and reward yourself."),
]

# Add training data
for role, journey_id, touchpoint_id, context, response in training_data:
    db_manager.store_training_data(role, journey_id, touchpoint_id, context, response)

print("✅ 5 Psychology training examples added successfully!")
