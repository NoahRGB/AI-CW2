
from enum import Enum

# represents different ticket types so all files use the
# same values 

class TicketTypes(Enum):
    SINGLE="single",
    RETURN="return",

    def __str__(self):
        return str(self.name).lower()

    @staticmethod
    def from_string(s): # turn string into a TicketTypes enum
        if s.lower() == "return":
            return TicketTypes.RETURN
        elif s.lower() == "single":
            return TicketTypes.SINGLE