from datetime import date, timedelta
from typing import List, Optional

class Event:
    def __init__(self, name: str, date_obj: date) -> None:
        self.name = name
        self.date_obj = date_obj
        self.date_str = date_obj.strftime('%a, %b %d')

    def __str__(self) -> str:
        return f"{self.date_str}: {self.name}"
    
    def to_markdown(self) -> str:
        return f"`{self.date_str}`: **{self.name}**"

class EventList:
    def __init__(self, event_list: Optional[List[Event]] = None) -> None:
        self.list = event_list or []

    def set(self, event_list: List[Event]) -> None:
        self.list = event_list

    def clear(self) -> None:
        self.list.clear()

    def add(self, event: Event) -> None:
        self.list.append(event)

    def events_until(self, days: int) -> 'EventList':
        time_max = date.today() + timedelta(days=days)
        for i in range(len(self.list)-1, -1, -1):
            if self.list[i].date_obj < time_max:
                return EventList(self.list[:i+1])
        return EventList()            
    
    def sms_str(self) -> str:
        string = ""
        for event in self.list:
            string = string + event.name.center(32, '-') + '\n'
            
        if string == "":
            return "N/A"
        return string[:-1]

    def to_markdown(self) -> str:
        string = ""
        for event in self.list:
            string = string + event.to_markdown() + '\n'    

        if string == "":
            return "**N/A**"
        return string[:-1]

    def __str__(self) -> str:
        string = ""
        for event in self.list:
            string = string + str(event) + '\n'

        if string == "":
            return "N/A"
        return string[:-1]
