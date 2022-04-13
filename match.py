from datetime import datetime


class Match:
    def __init__(self, dateTime, homeTeam, awayTeam, stadium, live, turn):
        self.dateTime = dateTime
        self.homeTeam = homeTeam
        self.awayTeam = awayTeam
        self.turn = turn
        self.stadium = stadium
        self.live = live
        
    def toCSVrow(self):
        return str(self.turn) + ',' + str(self.dateTime.day) + ',' + str(self.dateTime.month) + ',' + str(self.dateTime.year) + ',' + str(self.dateTime.hour) + ',' + str(self.dateTime.minute) + ',' + self.homeTeam + ',' + self.awayTeam + ',' + self.stadium + ',' + self.live

    @staticmethod
    def fromCSVrow(row):
        return Match(
            dateTime=datetime(
                year=int(row[3]),
                month=int(row[2]),
                day=int(row[1]),
                hour=int(row[4]),
                minute=int(row[5])),
            homeTeam=str(row[6]),
            awayTeam=str(row[7]),
            stadium=str(row[8]),
            live=str(row[9]),
            turn=int(row[0]))
