import textwrap
from typing import List, Tuple

class Message:
    def __init__(self, text: str, color: Tuple[int, int, int] = (255,255,255)):
        self.plain_text = text
        self.color = color
        self.count = 1
    
    @property
    def full_text(self) -> str:
        if self.count > 1:
            return f"{self.plain_text} (x{self.count})"
        else:
            return self.plain_text

class MessageLog:
    def __init__(self):
        self.messages: List[Message] = []
    
    def add_message(self, text: str, color: Tuple[int,int,int] = (255,255,255), stack: bool = True):
        if stack and self.messages and text==self.messages[-1].plain_text:
            self.messages[-1].count += 1
        else:
            self.messages.append(Message(text, color))
    