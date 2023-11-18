import json
import re
import sys
import time
from datetime import datetime, timedelta
from hashlib import sha256
from typing import Dict, List, Optional, Set, Tuple

import pytz
import requests
from icalendar import Calendar, Event, Timezone, TimezoneStandard

invalid_team_name: Set[str] = {"腾讯视频", "战至巅峰"}


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
    while True:
        open_response = requests.get(
            url="https://prod.comp.smoba.qq.com/leaguesite/leagues/open"
        )
        if (
            open_response.status_code == 200
            and len(leagues := json.loads(open_response.text)["results"]) > 0
        ):
            break
        else:
            time.sleep(10)

    # current_league_id = leagues[-1]["cc_league_id"]
    current_league_id = "KIC2023"

    while True:
        response = requests.get(
            url="https://tga-openapi.tga.qq.com/web/tgabank/getSchedules?seasonid={}".format(
                current_league_id
            )
        )
        # `status_code == 200` is not enough
        # {"msg": "get cache data failed: query db failed", "result": 1002} will also return 200
        if (
            response.status_code == 200
            and (response_text := json.loads(response.text))["result"] == 0
        ):
            break
        else:
            time.sleep(10)

    return response_text["data"]


def init_ical(name: str = "KPL") -> Calendar:
    cal = Calendar()
    cal.add("prodid", "-//{} calendar////".format(name))
    cal.add("version", "2.0")
    cal_tz = Timezone()
    cal_tz.add("tzid", "Asia/Shanghai")

    cal_tz_sd = TimezoneStandard()
    cal_tz_sd.add("dtstart", datetime(1601, 1, 1))
    cal_tz_sd.add("tzoffsetfrom", timedelta(hours=8))
    cal_tz_sd.add("tzoffsetto", timedelta(hours=8))

    cal_tz.add_component(cal_tz_sd)
    cal.add_component(cal_tz)

    return cal


def get_ical_event(hname: str, gname: str, match_datetime: datetime) -> Event:
    event = Event()
    event.add("summary", "{}:{}".format(hname, gname))
    # match_time_tuple = time_str_to_int(match_time)
    # match_datetime = (
    #     datetime(*match_time_tuple, tzinfo=pytz.timezone("Asia/Shanghai"))
    #     if match_time_tuple is not None
    #     else datetime.now()
    # )
    event.add("dtstart", match_datetime)
    event.add("dtend", match_datetime + timedelta(hours=2))
    event.add("dtstamp", match_datetime)  # avoid changes to ics every time
    event.add("uid", sha256(event.to_ical()).hexdigest())
    return event


team: Optional[str] = None
if len(sys.argv) == 3 and sys.argv[1] == "--team":
    team = sys.argv[2]

teams: Set[str] = set()
has_output: bool = False

kpl_cal: Calendar = init_ical()
cal_dict: Dict[str, Calendar] = {}

for game in get_game_list():
    hname: str = game["hname"]
    gname: str = game["gname"]

    if hname in invalid_team_name or gname in invalid_team_name:
        continue

    match_time: datetime = datetime.fromtimestamp(  # Tencent is not using utc
        float(game["match_timestamp"]), tz=pytz.timezone("Asia/Shanghai")
    )

    # add to teams
    teams.add(hname)
    teams.add(gname)

    if (team is None or (hname == team or gname == team)) or team == "all":
        # print info
        print("{} {} vs {}".format(match_time, hname, gname))
        has_output = True

        # add to calendar
        if team is None:
            kpl_cal.add_component(get_ical_event(hname, gname, match_time))
        elif team == "all":
            if hname not in cal_dict:
                cal_dict[hname] = init_ical(name=hname)
            cal_dict[hname].add_component(
                get_ical_event(hname, gname, match_time)
            )
            if gname not in cal_dict:
                cal_dict[gname] = init_ical(name=gname)
            cal_dict[gname].add_component(
                get_ical_event(hname, gname, match_time)
            )
        else:
            if team not in cal_dict:
                cal_dict[team] = init_ical(name=team)
            cal_dict[team].add_component(
                get_ical_event(hname, gname, match_time)
            )

if not has_output:
    print("invalid team name, available options: {}".format(teams))
elif team is not None:
    for team, cal in cal_dict.items():
        if team != "待定":
            with open(team + ".ics", "wb") as f:
                f.write(cal.to_ical())
else:
    with open("kpl.ics", "wb") as f:
        f.write(kpl_cal.to_ical())
