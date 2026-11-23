import openai


def reply(user_msg):
    return openai.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": user_msg}])
