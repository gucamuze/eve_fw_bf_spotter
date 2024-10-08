**Eve FW Battlefield spotter**

A python discord bot aimed at gathering data from the official Eve ESI API to spot the despawn of battlefields in FW. Works on live servers, GalCal FW, Gallente being friendly.

*Usage*

Create a .env file with:
- BOT_TOKEN
- BOT_CHANNEL_ID
- MAIL if you want to respect ESI's recommendations. Then just launch the script using python3.

The script updates every 30 minutes, that being the ESI's cache route limit, as specified in the response headers. Will output victory points changes on all galcal systems in both CLI and a log file (log.json which is actually not a json format file :| ), with a special output in case a BF is detected.
