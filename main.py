import json
import re
import sys
from datetime import datetime, timedelta
from hashlib import sha256
from typing import Dict, List, Optional, Set, Tuple

import pytz
import requests
from icalendar import Calendar, Event, Timezone, TimezoneStandard


def time_str_to_int(
    time_str: str,
) -> Optional[Tuple[int, int, int, int, int, int]]:
    time_regex = re.compile(
        r"(?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+)\s+(?P<hour>\d+):(?P<minute>\d+):(?P<second>\d+)"
    )
    match_result = time_regex.match(time_str)
    if match_result is None:
        return None
    result_dict = match_result.groupdict()
    return (
        int(result_dict["year"]),
        int(result_dict["month"]),
        int(result_dict["day"]),
        int(result_dict["hour"]),
        int(result_dict["minute"]),
        int(result_dict["second"]),
    )


def get_game_list() -> List[Dict]:
    open_response = requests.get(
        url="https://prod.comp.smoba.qq.com/leaguesite/leagues/open"
    )
    current_league_id = json.loads(open_response.text)["results"][-1][
        "cc_league_id"
    ]

    response = requests.get(
        url="https://tga-openapi.tga.qq.com/web/tgabank/getSchedules?seasonid={}".format(
            current_league_id
        )
    )

    return json.loads(response.text)["data"]


team: Optional[str] = None
if len(sys.argv) == 3 and sys.argv[1] == "--team":
    team = sys.argv[2]

teams: Set[str] = set()
has_output: bool = False
cal = Calendar()
cal.add("prodid", "-//KPL calendar////")
cal.add("version", "2.0")
cal_tz = Timezone()
cal_tz.add("tzid", "Asia/Shanghai")

cal_tz_sd = TimezoneStandard()
cal_tz_sd.add("dtstart", datetime(1601, 1, 1))
cal_tz_sd.add("tzoffsetfrom", timedelta(hours=8))
cal_tz_sd.add("tzoffsetto", timedelta(hours=8))

cal_tz.add_component(cal_tz_sd)
cal.add_component(cal_tz)

for game in get_game_list():
    hname: str = game["hname"]
    gname: str = game["gname"]
    match_time: str = game["match_time"]

    # add to teams
    teams.add(hname)
    teams.add(gname)

    if team is None or (hname == team or gname == team):
        # print info
        print("{} {} vs {}".format(match_time, hname, gname))
        has_output = True

        # add to calendar
        event = Event()
        event.add("summary", "{}:{}".format(hname, gname))
        match_time_tuple = time_str_to_int(match_time)
        match_datetime = (
            datetime(*match_time_tuple, tzinfo=pytz.timezone("Asia/Shanghai"))
            if match_time_tuple is not None
            else datetime.now()
        )
        event.add("dtstart", match_datetime)
        event.add("dtend", match_datetime + timedelta(hours=2))
        event.add("dtstamp", datetime.now())
        event.add("uid", sha256(event.to_ical()).hexdigest())
        cal.add_component(event)

if not has_output:
    print("invalid team name, available options: {}".format(teams))
elif team is not None:
    with open(team + ".ics", "wb") as f:
        f.write(cal.to_ical())
else:
    with open("kpl.ics", "wb") as f:
        f.write(cal.to_ical())
