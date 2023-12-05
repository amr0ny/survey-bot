from telebot import types, TeleBot

from sheets import CSVTable
import requests

class Bot(TeleBot):

	file_path = './usr_data/usr_responses.csv'

	def __init__(self, token, data, config=None):
		self.token = token
		super().__init__(self.token)
		self.data = [data.get(i) for i in data]
		self.__msg_id = 0
		self.user_ans = []
		self.csv_table = CSVTable(self.file_path, [self.data[key]['msg'] for key in data])
	def set_msg_id(self, msg_id):
		self.__msg_id = msg_id

	def get_msg_id(self):
		return self.__msg_id

	def build_msg(self):
		ans_type = self.data[self.__msg_id]['ans_type']
		msg_text = self.data[self.__msg_id]['msg']
		markup = None
		if ans_type == 'btn':
			markup = types.ReplyKeyboardMarkup(row_width=4, one_time_keyboard=True, resize_keyboard=True, selective=False)	
			[markup.add(btn) for btn in self.data[self.__msg_id]['buttons']]
		elif ans_type == 'txtbtn':
			markup = types.ReplyKeyboardMarkup(row_width=4, one_time_keyboard=True, resize_keyboard=True, selective=True)
			[markup.add(btn) for btn in self.data[self.__msg_id]['buttons']]
		return msg_text, markup


	def send_msg(self, message):
		msg_text, markup = self.build_msg()
		msg = super().send_message(message.chat.id, msg_text, reply_markup=markup)
		return msg

	def handle_message(self, message):
		print(f'{self.data[self.__msg_id-1]["msg"]} - {message.text}, msg_id: {self.get_msg_id()}')
		ans_type = self.data[self.__msg_id-1]['ans_type']
		is_last = False
		if 'is_last' in self.data[self.__msg_id]:
			is_last = True if self.data[self.__msg_id ]['is_last'] == 'Yes' else False
		print(message.text, ans_type)
		msg = message
		match ans_type:
			case 'txt':
				self.user_ans.append({self.data[self.__msg_id-1]['msg'], message.text})

				if 'next_msg_id' in self.data[self.__msg_id-1]:
					tmp_msg_id = self.__msg_id
					self.set_msg_id(self.data[tmp_msg_id-1]['next_msg_id'])
					msg = self.send_msg(message)
					self.set_msg_id(self.data[tmp_msg_id-1]['next_msg_id']+1)
				else:
					msg = self.send_msg(message)
					self.set_msg_id(self.__msg_id+1)

			case 'btn':
				buttons = self.data[self.__msg_id-1]['buttons']
				if message.text in buttons:
					self.user_ans.append({self.data[self.__msg_id-1]['msg'], message.text})

					tmp_msg_id = self.__msg_id
					self.set_msg_id(self.data[tmp_msg_id-1]['buttons'][message.text]['msg_id'])
					msg = self.send_msg(message)
					self.set_msg_id(self.data[tmp_msg_id-1]['buttons'][message.text]['msg_id']+1)
				else:
					msg = super().send_message(message.chat.id, 'You need to choose a button.')

			case 'pic':
				if message.content_type == 'photo':
					print(super().get_file_url(message.photo[-1].file_id))
					response = requests.get(super().get_file_url(message.photo[-1].file_id))
					path_to_photo = f'./photos/{message.from_user.username}_{self.__msg_id}.jpg'
					with open(path_to_photo, 'wb') as file:
						file.write(response.content)
					
					self.user_ans.append({self.data[self.__msg_id-1]['msg'], path_to_photo})

					if 'next_msg_id' in self.data[self.__msg_id-1]:
						tmp_msg_id = self.__msg_id
						self.set_msg_id(self.data[tmp_msg_id-1]['next_msg_id'])
						msg = self.send_msg(message)
						self.set_msg_id(self.data[tmp_msg_id-1]['next_msg_id']+1)
					else:
						msg = self.send_msg(message)
						self.set_msg_id(self.__msg_id+1)
				else:
					msg = super().send_message(message.chat.id, 'You need to send a photo.')
		self.csv_table.append_user(self.user_ans) and print('success') if is_last else None
		return super().register_next_step_handler(msg, self.handle_message)
		

		
