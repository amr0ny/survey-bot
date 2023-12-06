from telebot import types, TeleBot
from sheets import CSVTable
import requests
import uuid

class Bot(TeleBot):

	user_data_path = './usr_data/usr_responses.csv'
	photo_directory = './photos'
	def __init__(self, token, data, config=None):
		if config != None:
			self.user_data_path = config['user_data_path']
			self.photo_directory = config['photo_directory']
		self.token = token
		super().__init__(self.token)
		self.scenario_data_template = [data.get(i) for i in data]
		self.scenario_data = {}
		self.users_ans =  {}
		self.__user_msg_id = {}
		self.csv_table = CSVTable(self.user_data_path, [i['msg'] for i in self.scenario_data_template])
		
	def init_user(self, user_id):
		self.scenario_data[user_id] = self.scenario_data_template
		self.users_ans[user_id] = {self.scenario_data_template[index]['msg']: '' for index, _ in enumerate(self.scenario_data_template)}
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
			user_scenario_data = self.scenario_data[user_id]
			ans_type = user_scenario_data[msg_id]['ans_type']
			msg_text = user_scenario_data[msg_id]['msg']
			if (ans_type == 'btn' or ans_type == 'txtbtn'):
				markup = types.ReplyKeyboardMarkup(row_width=4, one_time_keyboard=True, resize_keyboard=True, selective=False)	
				[markup.add(btn) for btn in user_scenario_data[msg_id]['buttons']]
			return msg_text, markup
		except KeyError as err:
			return f"{type(err)}: {err} field doesn't exist", markup



	def send_msg(self, message):
		msg_text, markup = self.build_msg(message)
		msg = super().send_message(message.chat.id, msg_text, reply_markup=markup)
		return msg
	
	def handle_txt_message(self, message):
		msg = message
		user_id = message.from_user.id
		msg_id = self.__user_msg_id[user_id]
		user_scenario_data = self.scenario_data[user_id]
		user_ans = self.users_ans[user_id]

		if message.content_type != 'text':
			return super().send_message(message.chat.id, 'You need to send a text message.')
		user_ans[user_scenario_data[msg_id-1]['msg']] = message.text
		if 'next_msg_id' in user_scenario_data[msg_id-1]:
			self.set_msg_id(user_id, user_scenario_data[msg_id-1]['next_msg_id'])
			msg = self.send_msg(message)
			self.set_msg_id(user_id, user_scenario_data[msg_id-1]['next_msg_id']+1)
		else:
			msg = self.send_msg(message)
			self.set_msg_id(user_id, msg_id+1)
		return msg

	def handle_btn_message(self, message):
		msg = message
		user_id = message.from_user.id
		msg_id = self.__user_msg_id[user_id]
		user_scenario_data = self.scenario_data[user_id]
		user_ans = self.users_ans[user_id]

		buttons = user_scenario_data[msg_id-1]['buttons']
		if message.text in buttons:
			user_ans[user_scenario_data[msg_id-1]['msg']] = message.text
			self.set_msg_id(user_id, user_scenario_data[msg_id-1]['buttons'][message.text]['msg_id'])
			msg = self.send_msg(message)
			self.set_msg_id(user_id, user_scenario_data[msg_id-1]['buttons'][message.text]['msg_id']+1)
		else:
			msg = super().send_message(message.chat.id, 'You need to choose a button.')
		return msg

	def handle_txtbtn_message(self, message):
		msg = message
		user_id = message.from_user.id
		msg_id = self.__user_msg_id[user_id]
		user_scenario_data = self.scenario_data[user_id]
		user_ans = self.users_ans[user_id]

		buttons = user_scenario_data[msg_id-1]['buttons']
		if message.text in buttons:
			user_ans[user_scenario_data[msg_id-1]['msg']] = message.text
			self.set_msg_id(user_id, user_scenario_data[msg_id-1]['buttons'][message.text]['msg_id'])
			msg = self.send_msg(message)
			self.set_msg_id(user_id, user_scenario_data[msg_id-1]['buttons'][message.text]['msg_id']+1)
		else:
			user_ans[user_scenario_data[msg_id-1]['msg']] = message.text
			if 'next_msg_id' in user_scenario_data[msg_id-1]:
				self.set_msg_id(user_id, user_scenario_data[msg_id-1]['next_msg_id'])
				msg = self.send_msg(message)
				self.set_msg_id(user_id, user_scenario_data[msg_id-1]['next_msg_id']+1)
			else:
				msg = self.send_msg(message)
				self.set_msg_id(user_id, msg_id+1)
		return msg

	def handle_pic_message(self, message):
		msg = message
		user_id = message.from_user.id
		msg_id = self.__user_msg_id[user_id]
		user_scenario_data = self.scenario_data[user_id]
		user_ans = self.users_ans[user_id]

		if message.content_type == 'photo':
			photo_id = message.photo[-1].file_id
			print(super().get_file_url(photo_id))
			response = requests.get(super().get_file_url(photo_id))
			path_to_photo = f'{self.photo_directory}/f{str(uuid.uuid4())}-{message.from_user.username}.jpg'
			with open(path_to_photo, 'wb') as file:
				file.write(response.content)
			user_ans[user_scenario_data[msg_id-1]['msg']] = path_to_photo
			if 'next_msg_id' in user_scenario_data[msg_id-1]:
				self.set_msg_id(user_id, user_scenario_data[msg_id-1]['next_msg_id'])
				msg = self.send_msg(message)
				self.set_msg_id(user_id, user_scenario_data[msg_id-1]['next_msg_id']+1)
			else:
				msg = self.send_msg(message)
				self.set_msg_id(user_id, msg_id+1)
		else:
			msg = super().send_message(message.chat.id, 'You need to send a photo.')

		return msg

	def handle_message(self, message):
		msg = message
		user_id = message.from_user.id
		msg_id = self.__user_msg_id[user_id]
		user_scenario_data = self.scenario_data[user_id]
		user_ans = self.users_ans[user_id]
		ans_type = user_scenario_data[msg_id-1]['ans_type']
		print(f'{user_scenario_data[msg_id-1]["msg"]} - {message.text}, msg_id: {self.get_msg_id(user_id)}')
		
		is_last = 'is_last' in user_scenario_data[msg_id-1] and user_scenario_data[msg_id-1]['is_last'] == 'Yes'
		match ans_type:
			case 'txt':
				msg = self.handle_txt_message(message)
			case 'btn':
				msg = self.handle_btn_message(message)
			case 'pic':
				msg = self.handle_pic_message(message)
			case 'txtbtn':
				msg = self.handle_txtbtn_message(message)
		self.csv_table.append_user(user_ans) and print('success') if is_last else None
		return super().register_next_step_handler(msg, self.handle_message)
	

	@staticmethod
	def build_msg_err(err):
		match type(err):
			case KeyError:
				msg = f"{type(err)}: {err} doesn't exist"
		return msg