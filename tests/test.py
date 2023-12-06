import pytest

import telebot as telebot
from bot import Bot
import yaml
import json

with open('../config.json', 'r') as file:
    config = json.load(file)
token = config['token']

@pytest.fixture
def scenario_data_init(yml_path):
    global token
    with open(yml_path, 'r') as file:
        data = yaml.safe_load(file)
    bot = Bot(token, data, config=config)
    return bot

@pytest.mark.parametrize("yml_path", ['test.yml'])
def test_bot_init(scenario_data_init, yml_path):
    pass