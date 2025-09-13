from dotenv import load_dotenv
from openai import OpenAI
import os
import requests
import gradio as gr
import base64
import json


load_dotenv(override=True)

def push(text):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )


def record_unknown_question(question):
    push(f"Recording {question}")
    return {"recorded": "ok"}


class Me:

    def __init__(self):
        self.openai = OpenAI(base_url= os.getenv('MODEL_BASE_URL'), api_key=os.getenv('MODEL_API_KEY'))
        self.model = os.getenv('MODEL_NAME')
        self.name = "Swajan Golder"
        self.summary = base64.b64decode(os.getenv('SUMMARY').encode("utf-8")).decode("utf-8")

    
    def system_prompt(self):
        encoded_prompt = os.getenv('SYSTEM_PROMPT')
        system_prompt = base64.b64decode(encoded_prompt.encode("utf-8")).decode("utf-8")
        system_prompt = system_prompt.format(name=self.name, summary=self.summary)

        return system_prompt
    
    def push_msg_decision(self, user_message, ai_response_to_user):

        encoded_json = os.getenv('UNKNOW_QUESTION_PHRASES')
        decoded_json = base64.b64decode(encoded_json).decode("utf-8")
        unknown_question_phrases = json.loads(decoded_json)

        encoded_json = os.getenv('TRIGGERED_PHRASE')
        decoded_json = base64.b64decode(encoded_json).decode("utf-8")
        trigger_phrases = json.loads(decoded_json)

        response_lower = ai_response_to_user.lower()
        # print(any(trigger in response_lower for trigger in trigger_phrases))
        # print(any(match in response_lower for match in unknown_question_phrases))
        if any(trigger in response_lower for trigger in trigger_phrases) and any(match in response_lower for match in unknown_question_phrases):
            return 'YES'
        else:
            return 'NO'
        
    
    def sanitize_messages(self, messages):
        cleaned = []
        for dict in messages:
            dict.pop('metadata', None)
            dict.pop('options', None)
            cleaned.append(dict)
        return cleaned


    def chat(self, message, history):
        history = self.sanitize_messages(history)
        messages = [{"role": "system", "content": self.system_prompt()}] + history + [{"role": "user", "content": message}]
        # print(self.system_prompt())
        response = self.openai.chat.completions.create(model=self.model, messages=messages)
        if self.push_msg_decision(message,response.choices[0].message.content)=='YES':
            # print(response.choices[0].message.content)
            record_unknown_question(message)
        
        return response.choices[0].message.content
    

if __name__ == "__main__":
    me = Me()

    professional_css = """
        footer {visibility: hidden !important;}
    """
    app = gr.ChatInterface(
        me.chat, 
        type="messages",
        title="Swajan Golder's Professional Chatbot",                    # Removes the tab title
        # description="Welcome. Ask about my experience, projects, and research.",
        examples=[                   # Adds example questions for the user to click
            "What is your current role?",
            "Tell me about your EDDS project.",
            "What are your research interests?",
            "How can I contact you for a potential research collaboration?"
        ],
        theme="soft",
        css=professional_css
    )
    app.launch(favicon_path="favicon.ico")
    