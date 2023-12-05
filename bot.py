from telebot import types, TeleBot

from sheets import CSVTable
import requests

class Bot(TeleBot):

	file_path = './usr_data/usr_responses.csv'

	def __init__(self, token, data, config=None):
		self.token = token
		super().__init__(self.token)
		self.data_template = [data.get(i) for i in data]

		self.data = {}
		self.user_ans =  {}
		self.__user_msg_id = {}
		self.csv_table = CSVTable(self.file_path)
		
	def reg_user(self, message):
		self.data[message.from_user.id] = self.data_template
		self.user_ans[message.from_user.id] = {self.data_template[index]['msg']: '' for index, value in enumerate(self.data_template)}
		self.__user_msg_id[message.from_user.id] = 0

	def set_msg_id(self, user_id, msg_id):
		self.__user_msg_id[user_id] = msg_id

	def get_msg_id(self, user_id):
		return self.__user_msg_id[user_id]

	def build_msg(self, message):
		ans_type = self.data[message.from_user.id][self.__user_msg_id[message.from_user.id]]['ans_type']
		msg_text = self.data[message.from_user.id][self.__user_msg_id[message.from_user.id]]['msg']
		markup = None
		if ans_type == 'btn':
			markup = types.ReplyKeyboardMarkup(row_width=4, one_time_keyboard=True, resize_keyboard=True, selective=False)	
			[markup.add(btn) for btn in self.data[message.from_user.id][self.__user_msg_id[message.from_user.id]]['buttons']]
		elif ans_type == 'txtbtn':
			markup = types.ReplyKeyboardMarkup(row_width=4, one_time_keyboard=True, resize_keyboard=True, selective=True)
			[markup.add(btn) for btn in self.data[message.from_user.id][self.__user_msg_id[message.from_user.id]]['buttons']]
		return msg_text, markup


	def send_msg(self, message):
		msg_text, markup = self.build_msg(message)
		msg = super().send_message(message.chat.id, msg_text, reply_markup=markup)
		return msg

	def handle_message(self, message):
		print(f'{self.data[message.from_user.id][self.__user_msg_id[message.from_user.id]-1]["msg"]} - {message.text}, msg_id: {self.get_msg_id(message.from_user.id)}')
		ans_type = self.data[message.from_user.id][self.__user_msg_id[message.from_user.id]-1]['ans_type']
		is_last = False
		if 'is_last' in self.data[message.from_user.id][self.__user_msg_id[message.from_user.id]]:
			is_last = True if self.data[message.from_user.id][self.__user_msg_id[message.from_user.id]]['is_last'] == 'Yes' else False
		msg = message
		match ans_type:
			case 'txt':
				self.user_ans[message.from_user.id][self.data[message.from_user.id][self.__user_msg_id[message.from_user.id]-1]['msg']] = message.text
				if 'next_msg_id' in self.data[message.from_user.id][self.__user_msg_id[message.from_user.id]-1]:
					tmp_msg_id = self.__user_msg_id[message.from_user.id]
					self.set_msg_id(message.from_user.id, self.data[message.from_user.id][tmp_msg_id-1]['next_msg_id'])
					msg = self.send_msg(message)
					self.set_msg_id(message.from_user.id, self.data[message.from_user.id][tmp_msg_id-1]['next_msg_id']+1)
				else:
					msg = self.send_msg(message)
					self.set_msg_id(message.from_user.id, self.__user_msg_id[message.from_user.id]+1)

			case 'btn':
				buttons = self.data[message.from_user.id][self.__user_msg_id[message.from_user.id]-1]['buttons']
				if message.text in buttons:
					self.user_ans[message.from_user.id][self.data[message.from_user.id][self.__user_msg_id[message.from_user.id]-1]['msg']] = message.text

					tmp_msg_id = self.__user_msg_id[message.from_user.id]
					self.set_msg_id(message.from_user.id, self.data[message.from_user.id][tmp_msg_id-1]['buttons'][message.text]['msg_id'])
					msg = self.send_msg(message)
					self.set_msg_id(message.from_user.id, self.data[message.from_user.id][tmp_msg_id-1]['buttons'][message.text]['msg_id']+1)
				else:
					msg = super().send_message(message.chat.id, 'You need to choose a button.')

			case 'pic':
				if message.content_type == 'photo':
					print(super().get_file_url(message.photo[-1].file_id))
					response = requests.get(super().get_file_url(message.photo[-1].file_id))
					path_to_photo = f'./photos/{message.from_user.username}_{self.__user_msg_id[message.from_user.id]}.jpg'
					with open(path_to_photo, 'wb') as file:
						file.write(response.content)
					self.user_ans[message.from_user.id][self.data[message.from_user.id][self.__user_msg_id[message.from_user.id]-1]['msg']] = path_to_photo

					if 'next_msg_id' in self.data[message.from_user.id][self.__user_msg_id[message.from_user.id]-1]:
						tmp_msg_id = self.__user_msg_id[message.from_user.id]
						self.set_msg_id(message.from_user.id, self.data[message.from_user.id][tmp_msg_id-1]['next_msg_id'])
						msg = self.send_msg(message)
						self.set_msg_id(message.from_user.id,self.data[message.from_user.id][tmp_msg_id-1]['next_msg_id']+1)
					else:
						msg = self.send_msg(message)
						self.set_msg_id(message.from_user.id, self.__user_msg_id[message.from_user.id]+1)
				else:
					msg = super().send_message(message.chat.id, 'You need to send a photo.')
		self.csv_table.append_user(self.user_ans[message.from_user.id]) and print('success') if is_last else None
		return super().register_next_step_handler(msg, self.handle_message)
		

		
