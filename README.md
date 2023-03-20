# KPL-Calendar

Get the calendar of KPL schedules.

## Get started

### Local Run

```bash
# install prerequisites
pip install pytz requests icalendar

# get schedules of all teams
python main.py

# get schedules of only specified team
python main.py --team 重庆狼队

# get schedules of all teams in separate files
python main.py --team all
```

### WebCal subscription

Use a calendar app to subscribe to the game schedule in this repo.

For example, to subscribe to the game schedule of 重庆狼队, you can subscribe using the link https://github.com/futuretech6/KPL-Calendar/blob/actions/%E9%87%8D%E5%BA%86%E7%8B%BC%E9%98%9F.ics.

The schedule will be updated every week automatically by GitHub Actions bots.
