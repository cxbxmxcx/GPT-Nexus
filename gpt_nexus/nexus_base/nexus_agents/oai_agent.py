import json
import time

from dotenv import load_dotenv
from nexus_base.agent_manager import BaseAgent
from nexus_base.chat_models import Message
from openai import OpenAI

load_dotenv()  # loading and setting the api key can be done in one step


class OpenAIAgent(BaseAgent):
    def __init__(self, chat_history=None):
        self.last_message = ""
        self._chat_history = chat_history
        self.client = OpenAI()
        self.model = "gpt-4-1106-preview"
        self.temperature = 0.7
        self.messages = []  # history of messages
        self.tools = []

    async def get_response(self, user_input, thread_id=None):
        self.messages += [{"role": "user", "content": user_input}]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=0.7,
        )
        self.last_message = str(response)
        return str(response)

    def get_semantic_response(self, system, user):
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        return str(response.choices[0].message.content)

    def get_response_stream_old(self, user_input, thread_id=None):
        self.last_message = ""
        self.messages += [{"role": "user", "content": user_input}]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=0.7,
        )
        self.last_message = str(response.choices[0].message.content)

        def generate_responses():
            response = self.last_message
            for character in response:
                time.sleep(0.01)
                yield character

        return generate_responses

    def get_response_stream(self, user_input, thread_id=None):
        self.last_message = ""
        self.messages += [{"role": "user", "content": user_input}]
        if self.tools and len(self.tools) > 0:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=self.tools,
                tool_choice="auto",  # auto is default, but we'll be explicit
            )
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
            )
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        # Step 2: check if the model wanted to call a function
        if tool_calls:
            # Step 3: call the function
            # Note: the JSON response may not always be valid; be sure to handle errors
            available_functions = {
                action["name"]: action["pointer"] for action in self.actions
            }
            self.messages.append(
                response_message
            )  # extend conversation with assistant's reply
            # Step 4: send the info for each function call and function response to the model
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(
                    **function_args, _caller_agent=self
                )

                self.messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": str(function_response),
                    }
                )  # extend conversation with function response
            second_response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
            )  # get a new response from the model where it can see the function response
            response_message = second_response.choices[0].message

        self.last_message = str(response_message.content)

        def generate_responses():
            response = self.last_message
            for character in response:
                time.sleep(0.01)
                yield character

        return generate_responses

    def append_message(self, message: Message):
        if message.role == "agent":
            self.messages.append(dict(role="assistant", content=message.content))
        else:
            self.messages.append(dict(role=message.role, content=message.content))

    def load_chat_history(self):
        self.set_profile()
        if self.chat_history:
            for message in self.chat_history:
                self.append_message(message)

    def load_actions(self):
        self.tools = []
        for action in self.actions:
            self.tools.append(action["agent_action"])

    def set_profile(self):
        if self._profile:
            self.messages.append({"role": "system", "content": self._profile.persona})
