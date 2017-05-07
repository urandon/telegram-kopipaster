#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
from bs4 import BeautifulSoup
from requests import get
import requests
import random
import os
import sys
import time
import argparse

import nltk
import nltk.data

import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters


class Kopipaster(object):
    site_name = 'http://kopipasta.ru'
    query_template = site_name + '/pasta/{}'

    def __init__(self, max_id=None):
        if max_id is None:
            self.max_id = self.get_max_id()
        else:
            self.max_id = max_id

    def get_post(self, idx, verbose=False):
        url = self.query_template.format(idx)
        req = get(url)
        if req.status_code != requests.codes.ok:
            if verbose:
                print('Error {}'.format(req.status_code))
            return None
        soup = BeautifulSoup(req.content.decode(req.encoding))
        pasta = soup.findAll('meta', attrs={'property': 'vk:text'})[0]
        return pasta.attrs['content']

    def get_max_id(self, start_idx=20000):
        lo, hi = start_idx, None
        while hi is None or lo < hi:
            idx = lo*2 if hi is None else (lo+hi+1)/2
            req = get(self.query_template.format(idx))
            if req.status_code == requests.codes.not_found:
                hi = idx - 1
            else:
                lo = idx
        return lo

    def get_coolstory(self):
        story = None
        while story is None:
            story = self.get_post(random.randint(1, self.max_id))
        return story


class KopipasterBot(Kopipaster):
    def __init__(self, token, wait_coef=0.02):
        Kopipaster.__init__(self)
        self.updater = Updater(token=token)
        self.dispatcher = self.updater.dispatcher
        self.wait_coef = wait_coef
        self.tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
        self.dispatcher.add_handler(CommandHandler('start', self.start))
        self.dispatcher.add_handler(CommandHandler('cool', self.coolstory))
        self.dispatcher.add_handler(CommandHandler('speed', self.set_speed))
        self.dispatcher.add_handler(CommandHandler('die', self.die))
        self.dispatcher.add_handler(MessageHandler(Filters.text, self.echo))

    def send_msg(self, bot, update, msg):
        time_start = time.time()
        while(time.time() - time_start < self.wait_coef * len(msg)):
            bot.sendChatAction(chat_id=update.message.chat_id,
                               action=telegram.ChatAction.TYPING)
            time.sleep(0.4)
        bot.sendMessage(chat_id=update.message.chat_id, text=msg)

    def start(self, bot, update):
        self.send_msg(bot, update, u"Я - Копипастер, пилю прохладные")

    def echo(self, bot, update):
        msg = update.message.text
        if msg.lower() in [u'пили прохладную', u'рассказывай', u'ну?']:
            self.coolstory(bot, update)
        else:
            self.send_msg(bot, update, msg[::-1])

    def coolstory(self, bot, update):
        story = self.get_coolstory()
        start_msg = [u'Сап, анон, пилю прохладную',
                     u'Короче, суть такова']
        for msg in start_msg:
            self.send_msg(bot, update, msg)

        for line in self.tokenizer.tokenize(story):
            self.send_msg(bot, update, line)
        self.send_msg(bot, update, u'Вообщем, вот')

    def die(self, bot, update):
        bot.sendMessage(chat_id=update.message.chat_id,
                        text=u'А-а-а-а-а!!! Врача!!!\n')

    def set_speed(self, bot, update):
        splitted = update.message.text.split()
        if len(splitted) != 2:
            self.send_msg(bot, update, u'use /speed value')
            return
        try:
            speed = float(splitted[1])
        except:
            self.send_msg(bot, update, u'use /speed value, value a number')
            return
        self.wait_coef = 1.0 / speed

    def launch(self):
        self.updater.start_polling()

    def stop(self):
        self.updater.stop()

def make_parser():
    parser = argparse.ArgumentParser(description='Kool telegram bot')
    parser.add_argument('bot_secret', type=str,
                        help='telegram bot token gathered from BotFather')
    return parser

if __name__ == '__main__':
    args = make_parser().parse_args(sys.argv[1:])
    print('pid: {}'.format(os.getpid()))
    bot_token = args.bot_secret
    bot = KopipasterBot(bot_token)
    bot.launch()
