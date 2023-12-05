import telebot as telebot
import yaml
from bot import Bot
from sheets import CSVTable



TOKEN = "6775496962:AAHR2QrrJ0frrplKxerdEB9Eh07MIOYPT1I"
yml_path = './data/data.yml'
with open(yml_path, 'r') as file:
    data = yaml.safe_load(file)
bot = Bot(TOKEN, data)


@bot.message_handler(commands=['start'])
def start_handler(message):
	msg = bot.send_msg(message)
	print(f'{bot.data[bot.get_msg_id()]["msg"]} - {message.text}, msg_id: {bot.get_msg_id()}')
	bot.set_msg_id(1)
	return bot.register_next_step_handler(msg, bot.handle_message)

bot.enable_save_next_step_handlers()
bot.load_next_step_handlers()
bot.infinity_polling()