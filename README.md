# pxlcmdr

create venv

python3 -m venv .venv

enter environment

source .venv/bin/activate

install requirements

pip3 install -r requirements.txt

run the app

sudo .venv/bin/python code.py

auto run at startup

add this line

screen -d -m bash -c 'cd /home/robert/pxlcmdr/src && sudo /home/robert/pxlcmdr/src/.venv/bin/python /home/robert/pxlcmdr/src/code.py'

to /etc/rc.local

# api

get all config

GET 127.0.0.1:8080/api/v1/config

get specific config

GET 127.0.0.1:8080/api/v1/config/configkey

get specific effect config

GET 127.0.0.1:8080/api/v1/effect/effectkey

update specific config

PUT 127.0.0.1:8080/api/v1/config/configkey

BODY { "value": "configval" }

update specific effect config

PUT 127.0.0.1:8080/api/v1/effect/effectkey/configkey

BODY { "value": "configval" }

# some chase colours

 (255, 60, 0),   # orange
 (0, 128, 0),    # green
 (128, 0, 128)   # purple

 (255, 60, 0),   # orange
 (0, 128, 0),    # green

 (255, 0, 0),    # red
 (0, 128, 0),    # green
 (128, 128, 128) # white

 (255, 0, 0),    # red
 (0, 128, 0),    # green
 (0, 128, 0)     # white

# auto shutdown in cron

create /etc/cron.d/autoshutdown

using shutdown

55 21 * * * root /usr/sbin/shutdown -h now

using api

55 21 * * * root curl -X PUT http://127.0.0.1:8080/api/v1/shutdown
