from twython import Twython
from dateutil import parser
from datetime import datetime, timedelta, tzinfo
from rodi_py import rodi
import logging
import time
import sys
import re

ZERO = timedelta(0)

logging.basicConfig(level=logging.WARN)
logger = logging.getLogger('rodi_tweet')
logger.setLevel(logging.DEBUG)

# create a stream handler
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)
logger.propagate = False


class RoDI(object):
    def __init__(self):
        pass

    def pixel(self, red, green, blue):
        logger.debug('Pixel activated: {0}, {1}, {2}'.format(red, green, blue))

    def move_forward(self):
        logger.debug('Moving forward')

    def move_backward(self):
        logger.debug('Moving backwards')

    def move_left(self):
        logger.debug('Moving left')

    def move_right(self):
        logger.debug('Moving right')

    def move_stop(self):
        logger.debug('Stopping')

    def sing_music(self):
        logger.debug('Singing music')


class UTC(tzinfo):
    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO

utc = UTC()

TWITTER_APP_KEY = 'uIPF5Z4C51UmXpqdUJZj89hjJ'  # supply the appropriate value
TWITTER_APP_KEY_SECRET = '1NVhSg1aboTaXVfcLmSlmPKqBNUB5ymuBJ4XdDxyhVAWuO7HWy'

HASHTAG = '#rodidemo'

_hex_colour = re.compile(r'color{0}{0}{0}\b'.format('([0-9a-fA-F]{2})'))


class ListenTweets(object):
    def __init__(self, hashtag):
        self.last_id = None
        self.hashtag = hashtag

        self.rodi = rodi.RoDI()
        #self.rodi = RoDI()  # This is to test without connection to a RoDI

        self.now = datetime.now(utc)
        #self.now = datetime(2016, 9, 8, 23, 58, 47, 825761, tzinfo=utc)

        self.t = Twython(app_key=TWITTER_APP_KEY,
                         app_secret=TWITTER_APP_KEY_SECRET)

    def do_action(self, rodi_action):
        if 'color' in rodi_action:
            rgb = _hex_colour.search(rodi_action)
            if rgb:
                red = int(int(rgb.group(1), 16) * 0.39215687)
                green = int(int(rgb.group(2), 16) * 0.39215687)
                blue = int(int(rgb.group(3), 16) * 0.39215687)
                logger.debug("R:{} G:{} B:{}".format(red, green, blue))
                self.rodi.pixel(red, green, blue)
        elif rodi_action == 'adelante':
            self.rodi.move_forward()
        elif rodi_action == 'atras':
            self.rodi.move_backward()
        elif rodi_action == 'izquierda':
            self.rodi.move_left()
        elif rodi_action == 'derecha':
            self.rodi.move_right()
        elif rodi_action == 'para':
            self.rodi.move_stop()
        elif rodi_action == 'canta':
            self.rodi.sing_music()
        elif rodi_action == 'rainbow':
            for color in range(256):
                red, green, blue = rodi.wheel(color)
                self.rodi.pixel(red, green, blue)
                time.sleep(0.005)
            self.rodi.pixel(0, 0, 0)
        else:
            pass

    def run(self):
        logger.info("Running listener...")
        while True:
            logger.debug("Searching for tweets...")
            tweets = self.t.search(q=self.hashtag,
                                   since_id=self.last_id,
                                   count=100)['statuses']
            logger.debug("\tFound {0} tweets for the {1} hashtag".format(len(tweets),
                                                                         self.hashtag))
            # Search returns newest tweets firs, so we need to reverse it
            for tweet in reversed(tweets):
                tweet_time = parser.parse(tweet['created_at'])
                diff_secs = (tweet_time - self.now).total_seconds()
                if diff_secs >= 0 and 'retweeted_status' not in tweet:
                    for hashtag in tweet['entities']['hashtags']:
                        text = str(hashtag['text'])
                        if 'RoDI' in text:
                            logger.debug('\tFound RoDI hashtag: {0}'.format(text))
                            rodi_action = hashtag['text'].replace('RoDI', '')
                            self.do_action(rodi_action.lower())

                            # Store last tweet id so we don't repeat actions
                            self.last_id = tweet['id']
                            # If tweet is executed, wait 5 seconds to show
                            time.sleep(5)
                            # If multiple hashtags on the tweet, only run
                            # the first
                            break

            # It takes around 30 seconds for a new tweet to appear,
            # so we can sleep a little longer if we want
            time.sleep(5)


if __name__ == '__main__':
    listen = ListenTweets(HASHTAG)
    try:
        listen.run()
    except KeyboardInterrupt:
        logger.info('Exiting...')
