from telebot import types, TeleBot
from sheets import CSVTable
import requests
import uuid

class Bot(TeleBot):
	def __init__(self, token, data, config):
		self.user_data_path = config['user_data_path']
		self.users_photo_directory = config['users_photo_directory']
		self.bot_photo_directory = config['bot_photo_directory']
		self.token = token
		super().__init__(self.token)
		self.scenario_data = [data.get(i) for i in data]
		self.users_ans =  {}
		self.__user_msg_id = {}
		self.csv_table = CSVTable(self.user_data_path, [i['msg'] for i in self.scenario_data])
		
	def init_user(self, user_id):
		self.users_ans[user_id] = {self.scenario_data[index]['msg']: '' for index, _ in enumerate(self.scenario_data)}
		self.__user_msg_id[user_id] = 0

	def set_msg_id(self, user_id, msg_id):
		self.__user_msg_id[user_id] = msg_id

	def get_msg_id(self, user_id):
		return self.__user_msg_id[user_id]

	def build_msg(self, message):
		markup = types.ReplyKeyboardRemove(selective=False)
		try:
			user_id = message.from_user.id
			msg_id = self.__user_msg_id[user_id]
			ans_type = self.scenario_data[msg_id]['ans_type']
			msg_text = self.scenario_data[msg_id]['msg']
			if (ans_type == 'btn' or ans_type == 'txtbtn'):
				markup = types.ReplyKeyboardMarkup(row_width=4, one_time_keyboard=True, resize_keyboard=True, selective=False)	
				[markup.add(btn) for btn in self.scenario_data[msg_id]['buttons']]
			return msg_text, markup
		except KeyError as err:
			return f"{type(err)}: {err} field doesn't exist", markup



	def send_msg(self, message):
		user_id = message.from_user.id
		msg_id = self.__user_msg_id[user_id]
		msg_text, markup = self.build_msg(message)
		try:
			if 'photo' in self.scenario_data[msg_id]:
				photo = open(self.bot_photo_directory+self.scenario_data[msg_id]['photo'], 'rb')
				msg_text = None if 'photo_only' in self.scenario_data[msg_id] and self.scenario_data[msg_id]['photo_only'] else msg_text
				msg = super().send_photo(message.chat.id, photo, caption=msg_text, reply_markup=markup)
			else:
				msg = super().send_message(message.chat.id, msg_text, reply_markup=markup)
		except OSError as err:
			return super().send_message(message.chat.id, f"{type(err)}: {err}")
		return msg
	
	def handle_txt_message(self, message):
		msg = message
		user_id = message.from_user.id
		try:
			msg_id = self.__user_msg_id[user_id]
			current_msg = self.scenario_data[msg_id-1]

			if message.content_type != 'text':
				msg = super().send_message(message.chat.id, 'You need to send a text message.')
				return msg
			self.users_ans[user_id][current_msg['msg']] = message.text
			if 'next_msg_id' in current_msg:
				self.set_msg_id(user_id, current_msg['next_msg_id'])
				msg = self.send_msg(message)
				self.set_msg_id(user_id, current_msg['next_msg_id']+1)
			else:
				msg = self.send_msg(message)
				self.set_msg_id(user_id, msg_id+1)
		except KeyError as err:
			msg = super().send_message(message.chat.id, f"{type(err)}: {err}")
		return msg

	def handle_btn_message(self, message):
		msg = message
		user_id = message.from_user.id
		msg_id = self.__user_msg_id[user_id]
		current_msg = self.scenario_data[msg_id-1]
		buttons = current_msg['buttons']

		if message.text in buttons:
			self.users_ans[user_id][current_msg['msg']] = message.text
			self.set_msg_id(user_id, buttons[message.text]['msg_id'])
			msg = self.send_msg(message)
			self.set_msg_id(user_id, buttons[message.text]['msg_id']+1)
		else:
			msg = super().send_message(message.chat.id, 'You need to choose a button.')
		return msg

	def handle_txtbtn_message(self, message):
		msg = message
		user_id = message.from_user.id
		msg_id = self.__user_msg_id[user_id]
		current_msg = self.scenario_data[msg_id-1]
		buttons = current_msg['buttons']

		if message.content_type != 'text':
			msg = super().send_message(message.chat.id, 'You need to send a text message.')
			return msg
		self.users_ans[user_id][current_msg['msg']] = message.text
		if message.text in buttons:
			self.set_msg_id(user_id, buttons[message.text]['msg_id'])
			msg = self.send_msg(message)
			self.set_msg_id(user_id, buttons[message.text]['msg_id']+1)
		else:
			if 'next_msg_id' in current_msg:
				self.set_msg_id(user_id, current_msg['next_msg_id'])
				msg = self.send_msg(message)
				self.set_msg_id(user_id, current_msg['next_msg_id']+1)
			else:
				msg = self.send_msg(message)
				self.set_msg_id(user_id, msg_id+1)
		return msg

	def handle_pic_message(self, message):
		msg = message
		user_id = message.from_user.id
		msg_id = self.__user_msg_id[user_id]
		current_msg = self.scenario_data[msg_id-1]
		try:
			if message.content_type == 'photo':
				photo_id = message.photo[-1].file_id
				print(super().get_file_url(photo_id))
				response = requests.get(super().get_file_url(photo_id))
				path_to_photo = f'{self.users_photo_directory}{message.from_user.username}–{str(uuid.uuid4())}.jpg'
				with open(path_to_photo, 'wb') as file:
					file.write(response.content)
				self.users_ans[user_id][current_msg['msg']] = path_to_photo
				if 'next_msg_id' in current_msg:
					self.set_msg_id(user_id, current_msg['next_msg_id'])
					msg = self.send_msg(message)
					self.set_msg_id(user_id, current_msg['next_msg_id']+1)
				else:
					msg = self.send_msg(message)
					self.set_msg_id(user_id, msg_id+1)
			else:
				msg = super().send_message(message.chat.id, 'You need to send a photo.')
		except FileNotFoundError as err:
			msg = super().send_message(message.chat.id, f"{type(err)}: {err}")
		return msg

	def handle_message(self, message):
		msg = message
		user_id = message.from_user.id
		msg_id = self.__user_msg_id[user_id]
		current_msg = self.scenario_data[msg_id-1]

		ans_type = current_msg['ans_type']
		print(f'{current_msg["msg"]} - {message.text}, msg_id: {self.get_msg_id(user_id)}')
		
		is_last = 'is_last' in current_msg and current_msg['is_last']
		match ans_type:
			case 'txt':
				msg = self.handle_txt_message(message)
			case 'btn':
				msg = self.handle_btn_message(message)
			case 'pic':
				msg = self.handle_pic_message(message)
			case 'txtbtn':
				msg = self.handle_txtbtn_message(message)
		self.csv_table.append_user(self.users_ans[user_id]) if is_last else None
		return super().register_next_step_handler(msg, self.handle_message)