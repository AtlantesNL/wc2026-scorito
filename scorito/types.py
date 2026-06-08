"""Core domain types."""
from dataclasses import dataclass


@dataclass
class Team:
    name: str
    code: str = ""
    group: str = ""
    elo: float = 1500.0
    confederation: str = ""


@dataclass
class Match:
    team1: str
    team2: str
    group: str
    matchday: int = 1
    date: str = ""


@dataclass
class Scoreline:
    home: int
    away: int
    ev: float = 0.0

    def toto(self) -> str:
        if self.home > self.away:
            return "H"
        if self.away > self.home:
            return "A"
        return "D"
