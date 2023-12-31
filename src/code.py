import board
import json
import logging
import neopixel
import os
import random
import sqlite3
import time
import web

from threading import Thread

logger = logging.getLogger()
logger.setLevel(logging.INFO)

db_file = 'config.db'

PIN_MAP = {
    'D18': board.D18
}

CHASE_COLOURS = {
    'Halloween':
    [
        [255, 60, 0],   # orange
        [0, 128, 0],    # green
        [128, 0, 128]   # purple
    ],
    'Halloween (alt)':
    [
        [255, 60, 0],   # orange
        [0, 128, 0],    # green
    ],
    'Christmas':
    [
        [255, 0, 0],    # red
        [0, 128, 0],    # green
        [128, 128, 128] # white
    ],
    'Rainbow':
    [
        [255, 0, 0],    # red
        [0, 128, 0],    # green
        [0, 0, 128]     # blue
   ]
}

COLOUR_COLOURS = {
    'Black':    [0, 0, 0],
    'Blue':     [0, 0, 255],
    'Green':    [0, 255, 0],
    'Cyan':     [0, 255, 255],
    'Red':      [255, 0, 0],
    'Magenta':  [255, 0, 255],
    'Yellow':   [255, 255, 0],
    'White':    [255, 255, 255],
}

class ConfigStore(object):
    def __init__(self, db_file, prefix, config_config):
        self.db_file = db_file
        self.prefix = prefix
        self.config_config = config_config
        con = sqlite3.connect(self.db_file)
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS %s_configuration (key TEXT NOT NULL, val TEXT NOT NULL);" % self.prefix)
        for key in self.config_config.keys():
            res = cur.execute("SELECT val FROM %s_configuration WHERE key = ?;" % self.prefix, (key,))
            c = self.config_config[key]
            if res.fetchone() == None:
                logging.info('insert default value %s for %s' % (c['default'], key))
                val = c['default']
                if 'serialise' in c:
                    val = c['serialise'](val)
                cur.execute("INSERT INTO %s_configuration (key, val) VALUES (?, ?)" % self.prefix, (key, val))
        con.commit()
    def load(self):
        con = sqlite3.connect(self.db_file)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        config = {}
        for key in self.config_config.keys():
            c = self.config_config[key]
            res = cur.execute("SELECT key,val FROM %s_configuration WHERE key = ?;" % self.prefix, (key,))
            row = res.fetchone()
            val = row['val']
            if 'deserialise' in c:
                val = c['deserialise'](val)
            config[key] = c['type'](val)
        return config
    def save(self, config):
        con = sqlite3.connect(self.db_file)
        cur = con.cursor()
        for key in self.config_config.keys():
            c = self.config_config[key]
            val = config[key]
            if 'serialise' in c:
                val = c['serialise'](val)
            cur.execute("UPDATE %s_configuration SET val = ? WHERE key = ?" % self.prefix, (val, key))
        con.commit()

def validate_colours(colours):
    if type(colours) is not list:
        return False
    for colour in colours:
        if not validate_colour(colour):
            return False
    return True

def validate_colour(colour):
    if type(colour) is not list:
        return False
    if len(colour) != 3:
        return False
    return True

def colours_tostring(colours):
    return str(colours)

def colour_tostring(colour):
    return str(colour);

def colours_fromstring(colours):
    # parse [[0, 0, 0], [1, 1, 1], [2, 2, 2]]
    parts = list(map(lambda s : s.strip("[]"), colours.split("], ")))
    parts = list(map(lambda s : list(map(int, s.split(", "))), parts))
    return parts

def colour_fromstring(colour):
    parts = list(map(int, colour.strip("[]").split(", ")))
    return parts

def validate_pin(pin):
    return pin in PIN_MAP.keys()

def validate_count(count):
    return count > 0

def validate_order(order):
    return True # TODO

def validate_bright(bright):
    return bright >=0 and bright <= 1

def validate_effect(effect):
    return effect in effects.keys()

class EffectOff(object):
    config_config = {
    }
    def __init__(self):
        pass
    def step(self, pixels):
        pixels.fill((0, 0, 0))
        pixels.show()
        return 1
    def get_config(self):
        return {}
    def set_config(self, key, value):
        return True

class EffectColour(object):
    config_config = {
        'colour': {
            'type': list,
            'default': [255, 0, 0],
            'validate': validate_colour,
            'serialise': colour_tostring,
            'deserialise': colour_fromstring,
        },
    }
    def __init__(self, config_store):
        self.config_store = config_store
        self.load_config()
    def step(self, pixels):
        pixels.fill(self.config['colour'])
        pixels.show()
        return 1
    def load_config(self):
        self.config = self.config_store.load()
    def save_config(self):
        self.config_store.save(self.config)
    def get_config(self):
        return self.config
    def set_config(self, key, value):
        if key not in self.config:
            return "wrong key"
        if type(value) is not self.config_config[key]['type']:
            return "wrong type"
        if self.config[key] != value:
            if not self.config_config[key]['validate'](value):
                return "invalid %s" % key
            self.config[key] = value
            self.save_config()
        return True

class EffectWheel(object):
    config_config = {
    }
    def __init__(self):
        self.wheel_offset = 0
    def step(self, pixels):
        for p in range(0, pixels.n):
            idx = (p * 256 // pixels.n) + self.wheel_offset
            pixels[p] = self.wheel(pixels, idx & 255)
        pixels.show()
        self.wheel_offset += 1
        if self.wheel_offset > 255:
            self.wheel_offset = 0
        return 0.001
    def get_config(self):
        return {}
    def set_config(self, key, value):
        return True
    def wheel(self, pixels, pos):
        # input a value 0 to 255 to get a colour
        # the colours are a transition r-g-b back to r
        if pos < 0 or pos > 255:
            r = g = b = 0
        elif pos < 85:
            r = int(pos * 3)
            g = int(255 - pos * 3)
            b = 0
        elif pos < 170:
            pos -= 85
            r = int(255 - pos * 3)
            g = 0
            b = int(pos * 3)
        else:
            pos -= 170
            r = 0
            g = int(pos * 3)
            b = int(255 - pos * 3)
        return (r, g, b) if pixels.byteorder in (neopixel.RGB, neopixel.GRB) else (r, g, b, 0) 

class EffectTwinkle(object):
    config_config = {
    }
    def __init__(self):
        self.max_time = 10
        self.twink_pixels = []
    def step(self, pixels):
        if pixels.n != len(self.twink_pixels):
            self.twink_pixels.clear()
            for _ in range(pixels.n):
                self.twink_pixels.append(0)
        for _ in range(pixels.n):
            r = random.randrange(len(self.twink_pixels))
            t = random.randrange(self.max_time+1)
            if self.twink_pixels[r] == 0:
                self.twink_pixels[r] = t
            for p in range(len(self.twink_pixels)):
                if self.twink_pixels[p] > 0:
                    num = (255 // self.max_time) * self.twink_pixels[p]
                    pixels[p] = (num, num, num)
                    self.twink_pixels[p] -= 1
                else:
                    pixels[p] = (0, 0, 0)
        pixels.show()
        return 0.25
    def get_config(self):
        return {}
    def set_config(self, key, value):
        return True

class EffectChase(object):
    config_config = {
        'colours': {
            'type': list,
            'default': [
                [255, 0, 0],
                [0, 128, 0],
                [0, 0, 128]
            ],
            'validate': validate_colours,
            'serialise': colours_tostring,
            'deserialise': colours_fromstring,
        },
    }
    def __init__(self, config_store):
        self.config_store = config_store
        self.offset = 0
        self.load_config()
    def step(self, pixels):
        for p in range(0, pixels.n):
            num = (p+self.offset) % len(self.config['colours'])
            pixels[p] = self.config['colours'][num]
        pixels.show()
        self.offset += 1
        if self.offset == len(self.config['colours']):
            self.offset = 0
        return 0.5
    def load_config(self):
        self.config = self.config_store.load()
    def save_config(self):
        self.config_store.save(self.config)
    def get_config(self):
        return self.config
    def set_config(self, key, value):
        if key not in self.config:
            return "wrong key"
        if type(value) is not self.config_config[key]['type']:
            return "wrong type"
        if self.config[key] != value:
            if not self.config_config[key]['validate'](value):
                return "invalid %s" % key
            self.config[key] = value
            self.save_config()
        return True

effects = {
    'wheel': EffectWheel(),
    'twinkle': EffectTwinkle(),
    'chase': EffectChase(ConfigStore(db_file, 'effect_chase', EffectChase.config_config)),
    'colour': EffectColour(ConfigStore(db_file, 'effect_colour', EffectColour.config_config)),
    'off': EffectOff(),
}

def lights_up(pixels, colour, delay):
    for p in range(0, pixels.n+1, +1):
        if p < pixels.n:
            pixels[p] = colour
        if p > 0:
            pixels[p-1] = (0, 0, 0)
        pixels.show()
        time.sleep(delay)

def lights_dn(pixels, colour, delay):
    for p in range(pixels.n-1, -2, -1):
        if p > -1:
            pixels[p] = colour
        if p < pixels.n-1:
            pixels[p+1] = (0, 0, 0)
        pixels.show()
        time.sleep(delay)

def lights_test(pixels):
    d = 0.5 / pixels.n
    lights_up(pixels, (255, 0, 0), d)
    lights_dn(pixels, (255, 0, 0), d)
    lights_up(pixels, (0, 255, 0), d)
    lights_dn(pixels, (0, 255, 0), d)
    lights_up(pixels, (0, 0, 255), d)
    lights_dn(pixels, (0, 0, 255), d)

class Lights(Thread):
    config_config = {
        'pin': {
            'type': str,
            'default': 'D18',
            'validate': validate_pin,
        },
        'count': {
            'type': int,
            'default': 50,
            'validate': validate_count
        },
        'order': {
            'type': str,
            'default': neopixel.RGB,
            'validate': validate_order
        },
        'bright': {
            'type': float,
            'default': 0.1,
            'validate': validate_bright,
        },
        'selected_effect': {
            'type': str,
            'default': 'wheel',
            'validate': validate_effect,
        }
    }
    def __init__(self, config_store):
        logging.info('Lights.__init__()')
        Thread.__init__(self)
        self.pixels = None
        self.config_store = config_store
        self.running = True
        self.load_config()
        self.create()
    def create(self):
        logging.info('Lights.create()')
        if self.pixels != None:
            self.pixels.deinit()
        self.pixels = neopixel.NeoPixel(
            PIN_MAP[self.config['pin']],
            self.config['count'],
            pixel_order=self.config['order'],
            brightness=self.config['bright'],
            auto_write=False
        )
    def run(self):
        logging.info('Lights.run()')
        while self.running:
            sleep = effects[self.config['selected_effect']].step(self.pixels)
            if sleep == None:
                sleep = 1
            time.sleep(sleep)
        self.pixels.fill([0, 0, 0])
        self.pixels.show()
    def stop(self):
        logging.info('Lights.stop()')
        self.running = False
    def load_config(self):
        self.config = self.config_store.load()
    def save_config(self):
        self.config_store.save(self.config)
    def get_config(self):
        return self.config
    def set_config(self, key, value):
        if key not in self.config:
            return "wrong key"
        if type(value) is not self.config_config[key]['type']:
            return "wrong type"
        if self.config[key] != value:
            if not self.config_config[key]['validate'](value):
                return "invalid %s" % key
            self.config[key] = value
            self.create()
            self.save_config()
        return True

lights = Lights(ConfigStore(db_file, 'lights', Lights.config_config))

class Website(object):
    def __init__(self):
        logging.info('Website.__init__()')
        urls = (
            '/', 'index',
            '/api/v1/config', 'config',
            '/api/v1/config/([a-zA-Z0-9_-]+)', 'config',
            '/api/v1/effect', 'effect',
            '/api/v1/effect/([a-zA-Z0-9_-]+)', 'effect',
            '/api/v1/effect/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)', 'effect',
            '/api/v1/shutdown', 'shutdown',
        )
        self.app = web.application(urls, globals())
    def run(self):
        logging.info('Website.run()')
        lights.start()
        self.app.run()

class index(object):
    def GET(self):
        render = web.template.render('templates')
        pins = [ 'D18' ]
        leds = [ 10, 20, 30, 40, 48, 50, 60 ]
        orders = [ neopixel.RGB, neopixel.GRB ]
        brights = map(lambda f: f/10, range(0, 11, 1))
        effect_options = list(effects.keys())
        colours = CHASE_COLOURS
        colour_colours = COLOUR_COLOURS
        return render.index(time.time(), pins, leds, orders, brights, effect_options, colours, colour_colours)

class config(object):
    def GET(self, key=None):
        if key != None:
            val = lights.get_config()[key]
            return json.dumps({"value":val})
        return json.dumps(lights.get_config())
    def PUT(self, key):
        data = json.loads(web.data())
        result = lights.set_config(key, data['value'])
        if result is not True:
            return json.dumps({"error":result})
        return json.dumps(lights.get_config())

class effect(object):
    def GET(self, effect=None):
        if effect != None:
            if effect not in effects:
                return json.dumps({"error":"invalid effect"})
            return json.dumps(effects[effect].get_config())
        return json.dumps(list(effects.keys()))
    def PUT(self, effect, key):
        data = json.loads(web.data())
        if effect not in effects:
            return json.dumps({"error":"invalid effect"})
        result = effects[effect].set_config(key, data['value'])
        if result is not True:
            return json.dumps({"error":result})
        return json.dumps(effects[effect].get_config())

class shutdown(object):
    def PUT(self):
        lights.stop()
        os.system('shutdown -h +1')
        return json.dumps({'shutdown': 1})

website = Website()
website.run()

