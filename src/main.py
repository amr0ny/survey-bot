import telebot as telebot
import json
import yaml
from bot import Bot

with open('../config.json', 'r') as file:
    config = json.load(file)
    
token = config['token']
yml_path = config['scenario_yaml_path']

with open(yml_path, 'r') as file:
    data = yaml.safe_load(file)
    
bot = Bot(token, data, config)

@bot.message_handler(commands=['start'])
def start_handler(message):
	bot.init_user(message.from_user.id)
	msg = bot.send_msg(message)
	bot.set_msg_id(message.from_user.id, 1)
	return bot.register_next_step_handler(msg, bot.handle_message)

bot.enable_save_next_step_handlers()
bot.load_next_step_handlers()
bot.infinity_polling()