# indo-tv-scrapper
Indonesian TV schedule scrapper

Fetch TV EPG from IPTV https://iptv-org.github.io/ and possibly other resources to add as well

Require `conf.json` to setup the following variables:
- `persistent` will run the program in persistence mode and keep on fetching data in specific interval of time as specified by the `timer` variable
- `timer` determines the interval at which data is being fetched in minutes
- `query` specify which TV channel to query the schedule of