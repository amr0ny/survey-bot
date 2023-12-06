import sys
sys.path.append('../src/')

from datetime import datetime, timedelta
import time
import pytest
import yaml
import json
from telebot import types
from bot import Bot

with open('../config.json', 'r') as file:
    config = json.load(file)
token = config['token']

class TestBot:
    @pytest.fixture
    def bot_init(self, yml_path):
        global token
        with open(yml_path, 'r') as file:
            scenario_data = yaml.safe_load(file)
        bot = Bot(token, scenario_data, config=config)
        return [bot, scenario_data]

    @pytest.mark.parametrize("yml_path", ['test_scenarios/basic_test_sc.yml'])
    def test_user_init(self, bot_init):
        bot = bot_init[0]
        msg = self.create_text_message('/start')
        @bot.message_handler(commands=['start'])
        def command_handler(message):
            bot.init_user(message.from_user.id)

        bot.process_new_messages([msg])
        time.sleep(1)

        user_id = msg.from_user.id
        assert user_id in bot.scenario_data
        assert user_id in bot.users_ans
        assert user_id in bot._Bot__user_msg_id
    
    @pytest.mark.parametrize("yml_path", ['test_scenarios/unit_btn_sc.yml', 'test_scenarios/unit_txt_sc.yml', 'test_scenarios/unit_txtbtn_sc.yml', 'test_scenarios/unit_txt_next_msg_id_sc.yml', 'test_scenarios/unit_txtbtn_next_msg_id_sc.yml', 'test_scenarios/unit_pic_sc.yml', 'test_scenarios/unit_pic_next_msg_id_sc.yml', 'test_scenarios/unit_wrong_type_sc.yml'])
    def test_build_msg(self, bot_init):
        bot, scenario_data = bot_init[0], bot_init[1]
        msg = self.create_text_message('/start')
        output = None
        @bot.message_handler(commands=['start'])
        def command_handler(message):
            nonlocal output
            bot.init_user(message.from_user.id)
            output = bot.build_msg(message)
            bot.set_msg_id(message.from_user.id, bot.get_msg_id()+1)

        bot.process_new_messages([msg])
        time.sleep(1) 
        if 'buttons' in scenario_data[0]:

            #This line can cause possible issues in this test work while further bot scaling process due to {i[0]['text']for i in output[1].keyboard}
            assert output[0] == scenario_data[0]['msg'] and {i[0]['text']for i in output[1].keyboard} == scenario_data[0]['buttons'].keys()
        else:
            assert output[0] == scenario_data[0]['msg']

    #@pytest.mark.parametrize("yml_path", ['test_scenarios/unit_btn_sc.yml', 'test_scenarios/unit_txt_sc.yml', 'test_scenarios/unit_txtbtn_sc.yml', 'test_scenarios/unit_txt_next_msg_id_sc.yml', 'test_scenarios/unit_txtbtn_next_msg_id_sc.yml', 'test_scenarios/unit_pic_sc.yml', 'test_scenarios/unit_pic_next_msg_id_sc.yml'])
    #def test_send_msg(self, bot_init):
    #    bot, scenario_data = bot_init[0], bot_init[1]
    #    pass


    @staticmethod
    def create_text_message(text):
        params = {'text': text}
        chat = types.User(11, False, 'test')
        user = types.User(10, True, 'test')
        return types.Message(1, user, None, chat, 'text', params, "")