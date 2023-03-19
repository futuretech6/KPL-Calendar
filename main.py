import json
import sys
from typing import Dict, List, Optional, Set

import requests


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

for game in get_game_list():
    hname: str = game["hname"]
    gname: str = game["gname"]
    match_time: str = game["match_time"]
    teams.add(hname)
    teams.add(gname)
    if team is None or (hname == team or gname == team):
        print("{} {} vs {}".format(match_time, hname, gname))
        has_output = True

if not has_output:
    print("invalid team name, available options: {}".format(teams))
