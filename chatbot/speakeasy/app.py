import json
import os
import requests
import time
from chatbot.question_answering.qa import Agent


class App:
    def __init__(self):
        # url of the speakeasy server
        self.url = "https://speakeasy.ifi.uzh.ch"
        # load config from a json file
        dirname = os.path.dirname(__file__)
        with open(os.path.join(dirname, "../../config/credentials.json"), "r") as f:
            credentials = json.load(f)
        self.username = credentials["agent"]["username"]
        self.password = credentials["agent"]["password"]
        self.agent_details = None
        self.qa_agent = Agent()

    # user login
    def login(self):
        self.agent_details = requests.post(url=self.url + "/api/login",
                                           json={"username": self.username, "password": self.password}).json()
        print("--- agent details:")
        print(json.dumps(self.agent_details, indent=4))

    # check details of the current user
    def current(self, session_token: str):
        return requests.get(url=self.url + "/api/user/current", params={"session": session_token})

    # user logout
    def logout(self):
        return requests.get(url=self.url + "/api/logout", params={"session": self.agent_details["sessionToken"]})

    # check available chat rooms
    def check_rooms(self, session_token: str):
        return requests.get(url=self.url + "/api/rooms", params={"session": session_token})

    # check the state of a chat room
    def check_room_state(self, room_id: str, since: int, session_token: str):
        return requests.get(url=self.url + "/api/room/{}/{}".format(room_id, since),
                            params={"roomId": room_id, "since": since, "session": session_token})

    # post a message to a chat room
    def post_message(self, room_id: str, session_token: str, message: str):
        return requests.post(url=self.url + "/api/room/{}".format(room_id),
                             params={"roomId": room_id, "session": session_token}, data=message)

    def start_chat(self):
        chatroom_messages = {}
        while True:
            current_rooms = self.check_rooms(session_token=self.agent_details["sessionToken"]).json()["rooms"]
            print("--- {} chatrooms available".format(len(current_rooms)))

            for idx, room in enumerate(current_rooms):
                room_id = room["uid"]
                print("chat room - {}: {}".format(idx, room_id))

                new_room_state = self.check_room_state(room_id=room_id, since=0,
                                                       session_token=self.agent_details["sessionToken"]).json()
                new_messages = new_room_state["messages"]
                print("found {} messages".format(len(new_messages)))

                if room_id not in chatroom_messages.keys():
                    chatroom_messages[room_id] = []

                if len(chatroom_messages[room_id]) != len(new_messages):
                    for message in new_messages:
                        if message["ordinal"] >= len(chatroom_messages[room_id]) and message["session"] != \
                                self.agent_details["sessionId"]:
                            # process the message and find answer
                            response = self.get_response(message["message"])
                            self.post_message(room_id=room_id, session_token=self.agent_details["sessionToken"],
                                              message=response)

                chatroom_messages[room_id] = new_messages

            time.sleep(3)
            print("")

    def get_response(self, question):
        # response = "Hello , I got your message \"{}\" at {}.".format(question, time.strftime("%H:%M:%S, %d-%m-%Y", time.localtime()))
        # Part 1: Fact-oriented questions
        # 1. get the movie-domain entities, bos word and POS tag, nouns and verbs in the question
        # 2. find the relation in the question using regex
        # 3. match the relation with predicate
        # 4. match the query pattern from bos and generate the query
        # 5. perform SPARQL query to find the answer
        # 6. formulate the answer as a response
        response = self.qa_agent.answer(question)
        # print(f"\nQ: {question} ")
        print(f"A: {response}\n")
        return response
