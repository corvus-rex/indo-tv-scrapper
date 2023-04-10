# indo-tv-scrapper
Indonesian TV schedule scrapper

Require `.env` to setup the following variables:
- `PERSISTENT` will run the program in persistence mode and keep on fetching data in specific interval of time as specified by the `TIMER` variable
- `TIMER` determines the interval at which data is being fetched in minutes
- `QUERY` specify which TV channel to query the schedule of, different channels need to be separated using `", "` delimiter
- `WRITE_DIR` specify which directory to write the json in
- `SOURCE` specify from which source the EPG is grabbed from. For now, here are the supported options:
  - `"IPTV"` - https://iptv-org.github.io/ 
  - `"Vidio"` - https://api.vidio.com 