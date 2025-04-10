import re

# a class to hold date / time so that all python files can use the same type

class DateTime:
    # can be used just to store a time, just to store a date, or both. day/month/year will always
    # be integers and str() will format the date in the form "ddmmyy"
    months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]

    def __init__(self, hour=10, minute=30, day=1, month=1, year=2025):
        self.__hour = int(hour)
        self.__minute = int(minute)
        self.day = day
        self.month = month
        self.year = year

        # turn a string month e.g. "march" into its number e.g. 3
        if isinstance(self.month, str):
            does_month_exist = DateTime.months.count(self.month.lower()) > 0
            if does_month_exist:
                # turn string month into integer month
                self.month = DateTime.months.index(self.month.lower()) + 1
        
        # check all attributes are integers and year is correct length, otherwise reset
        if not isinstance(self.day, int) or not isinstance(self.month, int) or not isinstance(self.year, int) or len(str(self.year)) != 4:
            self.reset()

    def reset(self):
        self.day = 1
        self.month = 1
        self.year = 2000

    def __str__(self):
        return f"{'0' if self.day < 10 else ''}{str(self.day)}{'0' if self.month < 10 else ''}{str(self.month)}{str(self.year)[2:4]}"
    
    def get_min(self):
        return f"{'0' if self.__minute < 10 else ''}{self.__minute}"
    
    def get_hour(self):
        return f"{'0' if self.__hour < 10 else ''}{self.__hour}"
    
    def get_time(self):
        return f"{self.get_hour()}:{self.get_min()}"
    
    def __lt__(self, other):
        if isinstance(other, DateTime): # DateTime is less than another DateTime
            first_minute, first_hour = self.get_min(), self.get_hour()
            second_minute, second_hour = other.get_min(), other.get_hour()
            if first_hour < second_hour:
                return True
            elif first_hour > second_hour:
                return False
            if first_minute < second_minute:
                return True
            return False
    
    def __sub__(self, other):
        if isinstance(other, DateTime):
            # DateTime - DateTime
            # returns the difference between the two dates
            # in minutes. will be negative if the first date 
            # is less than the second date
            if self < other: 
                return -(other - self)
            
            first_minute, first_hour = int(self.get_min()), int(self.get_hour())
            second_minute, second_hour = int(other.get_min()), int(other.get_hour())
            
            total_mins = 0
            while first_hour != second_hour:
                total_mins += 60 - second_minute
                second_hour += 1
                second_minute = 0
            total_mins += first_minute - second_minute
            return total_mins # return DateTime.mins_to_hours(total_mins)
            
    @staticmethod
    def mins_to_hours(mins):
        # converts an amount of minutes e.g. 243 to 
        # hours & minutes e.g. (4, 3) - 4 hours 3 mins
        hours = int(mins / 60)
        minutes = mins % 60
        return hours, minutes

    @staticmethod
    def find_valid_time(text):
        # searches for any valid times in the provided string
        # given time must be in the form HH:MM

        # [01]\d means 0 or 1 followed by any digit
        # 2[0-3] means 2 followed by any digit 0-3
        # [0-5]\d means any digit 0-5 followed by any digit
        regex = r"([01]\d|2[0-3]|\d)[: \s]([0-5]\d)"
        time_match = re.search(regex, text)
        if time_match:
            # format into a DateTime object
            time = time_match.group()
            if ":" in time: time = time.replace(":", " ")
            time = time.split(" ")
            return DateTime(hour=int(time[0]), minute=int(time[1]))
        return None
    
    @staticmethod
    def find_valid_date(text):
        # searches for any valid dates in the provided string
        
        text_month_pattern = f"({'|'.join(DateTime.months)})" # finds month strings based on DateTime.months
        num_month_pattern = r"(0\d|1[012]|[1-9])" # finds digits 00 - 12
        day_pattern = r"(0\d|[12]\d|3[01]|\d)" # finds digits 00 - 31

        # finds a date in the format 'DD MONTH', 'MONTH DD', 'DD/MM', 'DD MM' and returns it as a DateTime object
        date_match = re.search(fr"(({day_pattern}\s{text_month_pattern})|({text_month_pattern}\s{day_pattern}))|({day_pattern}[/ \s]{num_month_pattern})", text)
        if date_match:
            date = date_match.group()
            if any(month in date for month in DateTime.months):
                month = re.search(fr"{text_month_pattern}", date).group()
                day = int(re.search(fr"{day_pattern}", date).group())
            else:
                if "/" in date: date = date.replace("/", " ")
                date = date.split(" ")
                month = int(date[1])
                day = int(date[0])
            return DateTime(day=day, month=month)
        return None