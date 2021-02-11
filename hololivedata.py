# -*- coding: utf-8 -*-
import requests
import json
import datetime
import time
import os
import pickle
import urllib.request
import urllib.error
import json
import math
import re
from pytwitterscraper import TwitterScraper
from apscheduler.schedulers.blocking import BlockingScheduler
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from threading import Thread
from shutil import move
from PIL import Image, ImageDraw


class DownloadImage(Thread) :
	def __init__(self, data, data_path, icon_path, banner_path, profile_path, discord_data, timer, lang) :
		# Create Thread
		Thread.__init__(self)

		# Get Date
		self.members = data

		# Selenium Setting
		self.chromdriver_path = os.path.join(os.getcwd() ,"bin", "chromedriver" if os.name == "posix" else "chromedriver.exe")

		# Setting Data Path
		self.data_path = data_path
		self.icon_path = icon_path 
		self.banner_path = banner_path
		self.profile_path = profile_path 
		self.timer = timer

		# Setting Discord and languge
		self.discord = discord_data
		self.lang = lang


	def run(self) :
		start_ = time.time()
		self.contents = {}

		for data in self.members :
			self.contents.update({
				data["name"] : {
					"name" : data["name"],
					"yt" : data["yt_info"],
					"tw" : data["tw_info"],
					"etag" : {}
				}
			})

		# Start Chrome
		self.chrome = self.__start_chrome()

		# Checking File 
		if not os.path.exists(self.data_path):
			with open(self.data_path, 'wb') as data_all:
				pickle.dump(self.contents, data_all)

		with open(self.data_path, 'rb') as data_all:
			self.old_contents = pickle.load(data_all)

		if not self.chrome is None :
			for name in self.contents.keys():
				# Twitter
				if not os.path.exists(self.icon_path.format("tw", "old", name)) :
					self.__download_image(
						url=self.contents[name]["tw"]["tw_icon"], 
						path=self.icon_path.format("tw", "old", name)
					)
				if not os.path.exists(self.banner_path.format("tw", "old", name)) :
					self.__download_image(
						url=self.contents[name]["tw"]["tw_banner"], 
						path=self.banner_path.format("tw", "old", name)
					)
				if not os.path.exists(self.profile_path.format("tw", "old", name)):
					self.__get_profile(
						url=self.contents[name]["tw"]["tw_url"], 
						path=self.profile_path.format("tw", "old", name),
						types="tw"
					)

				# Youtube
				if not os.path.exists(self.icon_path.format("yt", "old", name)) :
					self.__download_image(
						url=self.contents[name]["yt"]["yt_icon"],
						path=self.icon_path.format("yt", "old", name)
					)

				if not os.path.exists(self.banner_path.format("yt", "old", name)) :
					if self.contents[name]["yt"]["yt_banner"] is None :
						url = "https://s.ytimg.com/yts/img/channels/c4/default_banner-vflYp0HrA.jpg"
					else :
						url = self.contents[name]["yt"]["yt_banner"] + "=w1707-fcrop64=1,00005a57ffffa5a8-k-c0xffffffff-no-nd-rj"

					self.__download_image(
						url=url, 
						path=self.banner_path.format("yt", "old", name),
					)

				if not os.path.exists(self.profile_path.format("yt", "old", name + "_profile")) or not os.path.exists(self.profile_path.format("yt", "old", name + "_about")):
					self.__get_profile(
						url="https://www.youtube.com/channel/%s/about" % self.contents[name]["yt"]["yt_id"], 
						path=self.profile_path.format("yt", "old", name + "_{}"),
						types="yt"
					)

		for name in self.contents.keys():	
			for key in self.contents[name].keys():
				if "tw" in key :
					for key_2 in self.contents[name]["tw"].keys() :
						self.__check_data_tw(
							name=name,
							key_2=key_2
						)

				if "yt" in key :
					for key_2 in self.contents[name]["yt"].keys() :
						self.__check_data_yt(
							name=name,
							key_2=key_2
						)
				
				# Twitter
				if os.path.exists(self.profile_path.format("tw", "new", name)):
					move(
						self.profile_path.format("tw", "new", name), 
						self.profile_path.format("tw", "old", name)
					)
				if os.path.exists(self.profile_path.format("tw", "new", name+"sub")):
					move(
						self.profile_path.format("tw", "new", name+"sub"), 
						self.profile_path.format("tw", "old", name+"sub")
					)

				# YouTube
				if os.path.exists(self.profile_path.format("yt", "new", name + "_profile")):
					move(
						self.profile_path.format("yt", "new", name + "_profile"), 
						self.profile_path.format("yt", "old", name + "_profile")
					)
				if os.path.exists(self.profile_path.format("yt", "new", name+"_profilesub")) :
					move(
						self.profile_path.format("yt", "new", name+"_profilesub"), 
						self.profile_path.format("yt", "old", name+"_profilesub")
					)
				if os.path.exists(self.profile_path.format("yt", "new", name + "_about")):
					move(
						self.profile_path.format("yt", "new", name + "_about"), 
						self.profile_path.format("yt", "old", name + "_about")
					)
				if os.path.exists(self.profile_path.format("yt", "new", name+"_aboutsub")):
					move(
						self.profile_path.format("yt", "new", name+"_aboutsub"), 
						self.profile_path.format("yt", "old", name+"_aboutsub")
					)

		self.chrome.quit()

		print("Saveing DB")
		with open(self.data_path, 'wb') as data_all:
			pickle.dump(self.contents, data_all)
			print("Save Success!")

		measure_time = time.time() - start_
		if measure_time > self.timer * 2 :
			print("Too hard work on tw_log_notification")

	def __check_data_tw(self, name, key_2, platform ="Twitter") :
		if name in self.contents and name in self.old_contents :
			if self.contents[name]["tw"][key_2] != self.old_contents[name]["tw"][key_2] :
				if key_2 == "tw_icon" :
					print(f"{name.replace('_',' ').title()} was change icon in {platform}")

					# Download Images
					self.__download_image(
						url=self.contents[name]["tw"][key_2], 
						path=self.icon_path.format("tw", "new", name)
					)

					# Concatenate Image
					self.__concatenate_img(
						im1_path=self.icon_path.format("tw", "old", name),
						im2_path=self.icon_path.format("tw", "new", name), 
						gen_img_name=self.icon_path.format("tw", "dis", name),
						types="icon"
					)

					# Send to Discord
					self.discord.send_discord_change(
						member=self.contents[name]["name"].title().replace("_"," "), 
						types=self.lang["setting"]["twitter"]["icon"], 
						platform =platform, 
						url=self.contents[name]["tw"]["tw_url"],
						image_url=self.contents[name]["tw"]["tw_icon"], 
						icon_url="https://i.imgur.com/7tVYAeF_d.webp",
						large_image=True,
						filedrive=[
							self.icon_path.format("tw", "dis", name)
						],
						color=1942002
					)

					# Rename File
					move(rf"{self.icon_path.format('tw', 'new', name)}", rf"{self.icon_path.format('tw', 'old', name)}")

				elif key_2 == "tw_banner" :
					print(f"{name.replace('_',' ').title()} was change banner in {platform}")

					# Download Images
					self.__download_image(
						url=self.contents[name]["tw"][key_2], 
						path=self.banner_path.format("tw", "new", name)
					)

					# Concatenate Image
					self.__concatenate_img(
						im1_path=self.banner_path.format("tw", "old", name),
						im2_path=self.banner_path.format("tw", "new", name), 
						gen_img_name=self.banner_path.format("tw", "dis", name),
						types="banner"
					) 

					# Send to Discord
					self.discord.send_discord_change(
						member=self.contents[name]["name"].title().replace("_"," "), 
						types=self.lang["setting"]["twitter"]["banner"], 
						platform =platform , 
						url=self.contents[name]["tw"]["tw_url"],
						image_url=self.contents[name]["tw"]["tw_icon"], 
						icon_url="https://i.imgur.com/7tVYAeF_d.webp",
						large_image=True,
						filedrive=[
							self.banner_path.format("tw", "dis", name)
						],
						color=1942002
					)

					# Rename File
					move(rf"{self.banner_path.format('tw', 'new', name)}", rf"{self.banner_path.format('tw', 'old', name)}")

				else :
					if key_2 in ["tw_name","tw_location"] :
						if key_2 == "tw_name" :
							types = self.lang["setting"]["twitter"]["name"]
						else :
							types = self.lang["setting"]["twitter"]["description"]

						print(f"{name.replace('_',' ').title()} was change {key_2[key_2.find('_')+1:]}")

						# Get Profile Twitter
						self.__get_profile(
							url=self.contents[name]["tw"]["tw_url"], 
							path=self.profile_path.format("tw", "new", name),
							types="tw"
						)

						# Concatenate Image
						self.__concatenate_img(
							im1_path=self.profile_path.format("tw", "old", name),
							im2_path=self.profile_path.format("tw", "new", name), 
							gen_img_name=self.profile_path.format("tw", "dis", name),
							types="profile"
						)

						# Send to Discord
						self.discord.send_discord_change(
							member=self.contents[name]["name"].title().replace("_"," "), 
							types=types, 
							platform =platform ,
							url=self.contents[name]["tw"]["tw_url"],
							image_url=self.contents[name]["tw"]["tw_icon"], 
							icon_url="https://i.imgur.com/7tVYAeF_d.webp",
							old=self.old_contents[name]["tw"][key_2],
							new=self.contents[name]["tw"][key_2],
							large_image=True,
							filedrive=[
								self.profile_path.format("tw", "dis", name)
							],
							color=1942002
						)

			return True

		else :
			print(f"{name} not found createing...")
			return False

	def __check_data_yt(self, name, key_2, platform ="YouTube") :
		if name in self.contents and name in self.old_contents :
			if self.contents[name]["yt"][key_2] != self.old_contents[name]["yt"][key_2] :
				if key_2 == "yt_title" :
					print(f"{name.replace('_',' ').title()} was change name in {platform}")

					# Get New Profile
					self.__get_profile(
						url="https://www.youtube.com/channel/%s/about" % self.contents[name]["yt"]["yt_id"], 
						path=self.profile_path.format("yt", "new", name + "_profile"),
						types="yt_one",
						yt_set="profile"
					)

					# Concatenate Image
					self.__concatenate_img(
						im1_path=self.profile_path.format("yt", "old", name + "_profile"),
						im2_path=self.profile_path.format("yt", "new", name + "_profile"), 
						gen_img_name=self.profile_path.format("yt", "dis", name + "_profile"),
						types="banner"
					)

					# Send to Discord
					self.discord.send_discord_change(
						member=self.contents[name]["name"].title().replace("_"," "), 
						types=self.lang["setting"]["youtube"]["name"], 
						platform =platform ,
						url="https://www.youtube.com/channel/%s" % self.contents[name]["yt"]["yt_id"],
						image_url=self.contents[name]["yt"]["yt_icon"], 
						icon_url="https://i.imgur.com/FpwHmmL_d.webp",
						old=self.old_contents[name]["yt"][key_2],
						new=self.contents[name]["yt"][key_2],
						large_image=True,
						filedrive=[
							self.profile_path.format("yt", "dis", name + "_profile")
						],
						color=16711680
					)

				if key_2 == "yt_description" :
					print(f"{name.replace('_',' ').title()} was change about me in {platform}")

					# Get New Profile
					self.__get_profile(
						url="https://www.youtube.com/channel/%s/about" % self.contents[name]["yt"]["yt_id"], 
						path=self.profile_path.format("yt", "new", name + "_about"),
						types="yt_one",
						yt_set="about"
					)

					# Concatenate Image
					self.__concatenate_img(
						im1_path=self.profile_path.format("yt", "old", name + "_about"),
						im2_path=self.profile_path.format("yt", "new", name + "_about"), 
						gen_img_name=self.profile_path.format("yt", "dis", name + "_about"),
						types="profile"
					)

					# Send to Discord
					self.discord.send_discord_change(
						member=self.contents[name]["name"].title().replace("_"," "), 
						types=self.lang["setting"]["youtube"]["about"], 
						platform =platform ,
						url="https://www.youtube.com/channel/%s" % self.contents[name]["yt"]["yt_id"],
						image_url=self.contents[name]["yt"]["yt_icon"], 
						icon_url="https://i.imgur.com/FpwHmmL_d.webp",
						large_image=True,
						filedrive=[
							self.profile_path.format("yt", "dis", name + "_about")
						],
						color=16711680
					)

				if key_2 == "yt_icon" :
					print(f"{name.replace('_',' ').title()} was change icon in {platform}")

					# Download Images
					self.__download_image(
						url=self.contents[name]["yt"][key_2], 
						path=self.icon_path.format("yt", "new", name)
					)

					# Concatenate Image
					self.__concatenate_img(
						im1_path=self.icon_path.format("yt", "old", name),
						im2_path=self.icon_path.format("yt", "new", name), 
						gen_img_name=self.icon_path.format("yt", "dis", name),
						types="icon"
					) 

					types = "ไอคอน"
					# Send to Discord
					self.discord.send_discord_change(
						member=self.contents[name]["name"].title().replace("_"," "), 
						types=types, 
						platform =platform , 
						url="https://www.youtube.com/channel/%s" % self.contents[name]["yt"]["yt_id"],
						image_url=self.contents[name]["yt"]["yt_icon"], 
						icon_url="https://i.imgur.com/FpwHmmL_d.webp",
						large_image=True,
						filedrive=[
							self.icon_path.format("yt", "dis", name)
						],
						color=16711680
					)

					# Rename File
					move(rf"{self.icon_path.format('yt', 'new', name)}", rf"{self.icon_path.format('yt', 'old', name)}")

				if key_2 == "yt_banner" :
					print(f"{name.replace('_',' ').title()} was change banner in {platform}")

					if self.contents[name]["yt"]["yt_banner"] is None :
						url = "https://s.ytimg.com/yts/img/channels/c4/default_banner-vflYp0HrA.jpg"
					else :
						url = self.contents[name]["yt"]["yt_banner"] + "=w1707-fcrop64=1,00005a57ffffa5a8-k-c0xffffffff-no-nd-rj"

					# Download Images
					self.__download_image(
						url=url, 
						path=self.banner_path.format("yt", "new", name)
					)

					# Concatenate Image
					self.__concatenate_img(
						im1_path=self.banner_path.format("yt", "old", name),
						im2_path=self.banner_path.format("yt", "new", name), 
						gen_img_name=self.banner_path.format("yt", "dis", name),
						types="banner"
					) 

					types = "ปกช่อง"
					# Send to Discord
					self.discord.send_discord_change(
						member=self.contents[name]["name"].title().replace("_"," "), 
						types=types, 
						platform=platform , 
						url="https://www.youtube.com/channel/%s" % self.contents[name]["yt"]["yt_id"],
						image_url=self.contents[name]["yt"]["yt_icon"], 
						icon_url="https://i.imgur.com/FpwHmmL_d.webp",
						large_image=True,
						filedrive=[
							self.banner_path.format("yt", "dis", name)
						],
						color=16711680
					)

					# Rename File
					move(rf"{self.banner_path.format('yt', 'new', name)}", rf"{self.banner_path.format('yt', 'old', name)}")
			else :
				if key_2 in ["yt_banner","yt_icon"] :
					if "etag" in self.old_contents[name] :
						if "bannerid" in self.old_contents[name]["etag"] :
							if self.__get_url_headers(self.contents[name]["yt"]["yt_banner"]) != self.old_contents[name]["etag"]["bannerid"] :
								print(f"{name.replace('_',' ').title()} was change banner in {platform}")

								if self.contents[name]["yt"]["yt_banner"] is None :
									url = "https://s.ytimg.com/yts/img/channels/c4/default_banner-vflYp0HrA.jpg"
								else :
									url = self.contents[name]["yt"]["yt_banner"] + "=w1707-fcrop64=1,00005a57ffffa5a8-k-c0xffffffff-no-nd-rj"

								# Download Images
								self.__download_image(
									url=url, 
									path=self.banner_path.format("yt", "new", name)
								)

								# Concatenate Image
								self.__concatenate_img(
									im1_path=self.banner_path.format("yt", "old", name),
									im2_path=self.banner_path.format("yt", "new", name), 
									gen_img_name=self.banner_path.format("yt", "dis", name),
									types="banner"
								) 

								types = "ปกช่อง"
								# Send to Discord
								self.discord.send_discord_change(
									member=self.contents[name]["name"].title().replace("_"," "), 
									types=types, 
									platform=platform , 
									url="https://www.youtube.com/channel/%s" % self.contents[name]["yt"]["yt_id"],
									image_url=self.contents[name]["yt"]["yt_icon"], 
									icon_url="https://i.imgur.com/FpwHmmL_d.webp",
									large_image=True,
									filedrive=[
										self.banner_path.format("yt", "dis", name)
									],
									color=16711680
								)

								# Rename File
								move(rf"{self.banner_path.format('yt', 'new', name)}", rf"{self.banner_path.format('yt', 'old', name)}")

						if "iconid" in self.old_contents[name]["etag"] : 
							if self.__get_url_headers(self.contents[name]["yt"]["yt_icon"]) != self.old_contents[name]["etag"]["iconid"] :
								print(f"{name.replace('_',' ').title()} was change icon in {platform}")

								
								if self.contents[name]["yt"]["yt_banner"] is None :
									url = "https://s.ytimg.com/yts/img/channels/c4/default_banner-vflYp0HrA.jpg"
								else :
									url = self.contents[name]["yt"]["yt_banner"] + "=w1707-fcrop64=1,00005a57ffffa5a8-k-c0xffffffff-no-nd-rj"

								# Download Images
								self.__download_image(
									url=url, 
									path=self.icon_path.format("yt", "new", name)
								)

								# Concatenate Image
								self.__concatenate_img(
									im1_path=self.icon_path.format("yt", "old", name),
									im2_path=self.icon_path.format("yt", "new", name), 
									gen_img_name=self.icon_path.format("yt", "dis", name),
									types="icon"
								) 

								types = "ไอคอน"
								# Send to Discord
								self.discord.send_discord_change(
									member=self.contents[name]["name"].title().replace("_"," "), 
									types=types, 
									platform=platform , 
									url="https://www.youtube.com/channel/%s" % self.contents[name]["yt"]["yt_id"],
									image_url=self.contents[name]["yt"]["yt_icon"], 
									icon_url="https://i.imgur.com/FpwHmmL_d.webp",
									large_image=True,
									filedrive=[
										self.icon_path.format("yt", "dis", name)
									],
									color=16711680
								)

								# Rename File
								move(rf"{self.icon_path.format('yt', 'new', name)}", rf"{self.icon_path.format('yt', 'old', name)}")

					else :
						print(f"ETag icon {name.replace('_',' ').title()} not found")
						print("Createing.....")
						self.contents[name]["etag"].update({
							"bannerid" : self.__get_url_headers(self.contents[name]["yt"]["yt_banner"]),
							"iconid" : self.__get_url_headers(self.contents[name]["yt"]["yt_icon"])
						})
						# print("Create Success!")
		return True


	def __get_url_headers(self, url) :
		data = requests.head(url).headers

		if "ETag" in data :
			return data["ETag"].replace('"','')
		else :
			return None


	def __start_chrome(self) :
		try :
			options = Options()
			options.add_argument("--headless")
			options.add_argument("--disable-gpu")
			options.add_argument("--no-sandbox")
			options.add_argument("--single-process")
			options.add_argument("window-size=1440x1440")
			browser = webdriver.Chrome(
				executable_path=str(self.chromdriver_path),
				options=options
			)

			browser.implicitly_wait(3)

			return browser
		except Exception as e:
			print(e)
			return None

	def __get_profile(self, url, path, types, yt_set=None) :
		try :
			res = []
			# Open URL
			self.chrome.get(url)

			# Waitng for Render
			time.sleep(5)

			# Find Element 
			if types == "tw" :
				# self.chrome.get_screenshot_as_file(path)
				element = self.chrome.find_element_by_xpath("/html/body/div/div/div/div[2]/main/div/div/div/div[1]/div/div[2]/div/div/div[1]")

				# Screenshot
				self.chrome.get_screenshot_as_file(path)
				
				# Create Image
				self.__create_images(element, path)

			elif  types == "yt" :
				try :
					self.chrome.find_element_by_xpath("/html/body/ytd-app/ytd-popup-container/iron-dropdown/div/yt-bubble-hint-renderer/div[2]/div[2]").click() # Close membership popup
				except :
					pass

				name = [
					"profile",
					"about"
				]
				xpath = [
					"/html/body/ytd-app/div/ytd-page-manager/ytd-browse/div[3]",
					"/html/body/ytd-app/div/ytd-page-manager/ytd-browse/ytd-two-column-browse-results-renderer/div[1]/ytd-section-list-renderer/div[2]/ytd-item-section-renderer/div[3]/ytd-channel-about-metadata-renderer/div[1]/div[1]"
				]

				for ii, xdata in enumerate(xpath) :
					element = self.chrome.find_element_by_xpath(xdata)

					# Screenshot
					self.chrome.get_screenshot_as_file(path.format(name[ii]))
						
					# Create Image
					self.__create_images(element, path.format(name[ii]))

			elif types == "yt_one" :
				try :
					self.chrome.find_element_by_xpath("/html/body/ytd-app/ytd-popup-container/iron-dropdown/div/yt-bubble-hint-renderer/div[2]/div[2]").click() # Close membership popup
				except :
					pass

				xpath = {
					"profile" : "/html/body/ytd-app/div/ytd-page-manager/ytd-browse/div[3]",
					"about" : "/html/body/ytd-app/div/ytd-page-manager/ytd-browse/ytd-two-column-browse-results-renderer/div[1]/ytd-section-list-renderer/div[2]/ytd-item-section-renderer/div[3]/ytd-channel-about-metadata-renderer/div[1]/div[1]"
				}

				element = self.chrome.find_element_by_xpath(xpath[yt_set])
				
				# Screenshot
				self.chrome.get_screenshot_as_file(path)
				
				# Create Image
				self.__create_images(element, path)

			return True

		except Exception as e :
			print(f"{path} : {e}")
			return None


	def __create_images(self, element, path) :
		left = int(element.location["x"])
		top = int(element.location["y"])
		right = int(element.location["x"] + element.size["width"])
		bottom = int(element.location["y"] + element.size["height"])

		# Setting And Save Iamge
		im = Image.open(path)

		if left >= 1 and right >= 1 and bottom >= 1 and top >= 1 :
			im = im.crop((left, top, right, bottom))

		return im.save(path)

	def __download_image(self, url, path):
		try:
			data = urllib.request.urlopen(url).read()
			with open(path, mode="wb") as f:
				f.write(data)

		except urllib.error.URLError as e:
			print(e)

	
	def __concatenate_img(self, im1_path, im2_path, gen_img_name, types):
		try :
			# Setting Image and Paste 
			void_pix = 30
			line_width = 20

			# Open Image File
			im1 = Image.open(im1_path)
			im2 = Image.open(im2_path)

			if types == "icon" or types == "profile" :
				# print(types)
				dst_width = im1.width + im2.width + void_pix
				dst_height = max(im1.height, im2.height)

				img_paste1 = (0, 0)
				img_paste2 = (im1.width + void_pix, 0)

				line_xm = int(im1.width - 5)
				line_xp = int(dst_width - im2.width - 5)
				line_y = int(dst_height / 2)

				arrow_x = line_xp - 5
				arrow_coor= (
					line_xp+line_width / 2, 
					line_y,
					arrow_x, 
					line_y+line_width,
					arrow_x, 
					line_y-line_width
				)

			elif types == "banner" :
				dst_width = max(im1.width, im2.width)
				dst_height = im1.height + im2.height + void_pix

				img_paste1 = (math.ceil((dst_width - im1.width) / 2), 0)
				img_paste2 = (math.ceil((dst_width - im2.width) / 2), im1.height + void_pix)

				void_line = 20
				line_xm = int(math.ceil(dst_width / 2) + void_line)
				line_xp = int(math.ceil((dst_width -  max(im1.width, im2.width) / 2)))
				line_y = int(math.ceil((dst_height - im2.height - void_pix)) + (void_line / 2) - 3)

				arrow_coor = (
					line_xm-(void_line / 2)+(5 / 2), # X1
					line_y+line_width+5, # Y1
					line_xp-(void_line / 2), # X2
					line_y+line_width-(void_line / 2), # Y2
					line_xp+line_width+(void_line / 2), # X3
					line_y+line_width-(void_line / 2) # Y3
				)

			else :
				dst_width = max(im1.width, im2.width)
				dst_height = im1.height + im2.height + void_pix

				img_paste1 = (0, 0)
				img_paste2 = (im1.width + void_pix, 0)

				line_xm = int(im1.width - 5)
				line_xp = int(dst_width - im2.width - 5)
				line_y = int(dst_height / 2)

				arrow_x = line_xp - 5
				arrow_coor= (
					line_xp+line_width / 2, 
					line_y,
					arrow_x, 
					line_y+line_width,
					arrow_x, 
					line_y-line_width
				)

			# Setting And Paste Images
			dst = Image.new("RGBA", (dst_width, dst_height))
			dst.paste(im1, img_paste1)
			dst.paste(im2, img_paste2)

			# Draw Arrow
			draw = ImageDraw.Draw(dst)
			line_c = (70, 170, 255)
			line_coor = (line_xm, line_y, line_xp, line_y)
			draw.line(line_coor, fill=line_c, width=line_width)
			draw.polygon(arrow_coor, fill=line_c)

			# Save Image
			dst.save(gen_img_name)

			return True
		except Exception as e :
			print(e)
			return False

class HololiveData(Thread) :
	def __init__(self, api_yt_key, token_discord, react_count=5000, lang="th") :
		# Create Thread
		Thread.__init__(self)
	
		# Get Data Every 
		self.minutes = 3

		# Setting 
		self.api_yt_key = api_yt_key
		self.tw = TwitterScraper()
		
		# Path Setting
		self.dbname = "database"

		self.path_db = os.path.join(os.getcwd(), self.dbname)
		
		# Bin data [ num_follower, change_data ]
		self.path_num = os.path.join(os.getcwd(), self.dbname, "bin", "num_log.pickle")
		self.path_datalog = os.path.join(os.getcwd(), self.dbname, "bin", "data_log.pickle")

		# Database Images
		self.path_icon_img = os.path.join(os.getcwd(), self.dbname, "images", "icon", "{}", "{}_icon_{}.png")
		self.path_banner_img = os.path.join(os.getcwd(), self.dbname, "images", "bg", "{}", "{}_banner_{}.png")
		self.path_profile_img = os.path.join(os.getcwd(), self.dbname, "images", "profiles", "{}", "{}_profile_{}.png")

		# Endpoint
		self.yturl = "https://youtube.googleapis.com/{}?{}&key=" + self.api_yt_key

		# React People count
		self.react_count = react_count

		# Sched 
		self.sched = BlockingScheduler()

		# Get Members
		self.__getmembers()

		# Setting Language
		self.lang = self.__load_lang(lang)

		# Data Discord
		self.discord = SendMessageDiscord(
			token=token_discord,
			lang=self.lang
		)

	def run(self) :
		start_ = time.time()

		print("Start work at : %s" % datetime.datetime.now().strftime("%d %B %Y // %H:%M:%S"))
		
		# Check Numbers Follower
		self.__main()

		# Add Job
		self.sched.add_job(self.__main,"interval",minutes=self.minutes) # Get Data Lastest 

		measure_time = time.time() - start_

		print(f"Started! [ {round(measure_time, 2)} s. ]")

		# Start Job
		self.sched.start()


	def add_channel(self, channel_id) :
		self.discord.add_channel(channel_id)

	def __main(self) :
		start_ = time.time() # Start Time

		# print("Getting Subscribe and Follower")
		print("Checking data...")
		
		if os.path.exists(self.path_num):
			with open(self.path_num, "rb") as data_num:
				old_contents = pickle.load(data_num)

		self.data_members = self.__get_members_info()

		# Check Follower
		self.__check_follower()

		# Download Images
		# print(self.data_members)
		dw_images = DownloadImage(
			data=self.data_members, 
			data_path=self.path_datalog, 
			icon_path=self.path_icon_img, 
			banner_path=self.path_banner_img, 
			profile_path=self.path_profile_img,
			discord_data=self.discord,
			timer=self.minutes,
			lang=self.lang
		)

		dw_images.deamon = True
		if dw_images.is_alive :
			print("Starting...")
			dw_images.start()

		measure_time = time.time() - start_
		
		if measure_time > (self.minutes * 60) + 60 :
			print("System is too hard work...")

	def __check_follower(self) :
		data_follower = {}

		# print(self.data_members)
		for ii, data_mem in enumerate(self.data_members):
			# Check Members 
			for data_men_check in self.members :
				if data_men_check["youtube"] == data_mem["yt_info"]["yt_id"] :
					__member = data_men_check
					break

			# Set Data
			data_follower.update({
				 __member["name"] : {
					"yt_sub" : data_mem["yt_info"]["yt_subscribe_counts"],
					"tw_follower" : data_mem["tw_info"]["tw_follower"],
				}
			})

			if not os.path.exists(self.path_num) :
				print("Createing File... num_log.pickle")
				with open(self.path_num, "wb") as data_num :
					pickle.dump(data_follower, data_num)

			with open(self.path_num, "rb") as data_num :
				old_contents = pickle.load(data_num)

			if self.__judge(member=__member["name"], contents=data_follower, 
				old_contents=old_contents, key="tw_follower", th_val=self.react_count) :

				self.discord.send_discord_follower(
					member=__member["name"].title().replace("_"," "), 
					title=self.lang["count_alert"]["suffix"]["twitter"], 
					platform ="Twitter" , 
					follower="{:2,}".format(int(data_follower[__member["name"]]["tw_follower"])), 
					url=data_mem["tw_info"]["tw_url"],
					image_url=data_mem["tw_info"]["tw_icon"],
					icon_url="https://i.imgur.com/7tVYAeF_d.webp",
					color=1942002
				)

				print(f"{__member['name']} {self.lang['count_alert']['suffix']['twitter']} on Twitter : " + "{:2,}".format(int(data_follower[__member["name"]]["tw_follower"])))

			if self.__judge(member=__member["name"], contents=data_follower, 
				old_contents=old_contents,key="yt_sub", th_val=self.react_count) :

				self.discord.send_discord_follower(
					member=__member["name"].title().replace("_"," "), 
					title=self.lang["count_alert"]["suffix"]["youtube"], 
					platform ="Youtube", 
					follower="{:2,}".format(int(data_follower[__member["name"]]["yt_sub"])), 
					url=f"https://www.youtube.com/channel/{data_mem['yt_info']['yt_id']}",
					image_url=data_mem["yt_info"]["yt_icon"],
					icon_url="https://i.imgur.com/FpwHmmL_d.webp",
					color=16711680
				)

				print(f"{__member['name']} {self.lang['count_alert']['suffix']['youtube']} on YouTube : " + "{:2,}".format(int(data_follower[__member["name"]]["yt_sub"])))
			

		print("Saveing Database....")
		with open(self.path_num, "wb") as data_num:
			# print(data_follower)
			pickle.dump(data_follower, data_num)
			print("Save success!")

		return True
		
	def __get_members_info(self) :
		# print("Getting Data Members....")
		res = []

		# Res Data 
		print("Loading Data YT And Twitter")
		load_data_yt = self.__get_subscribe()
		load_data_tw = self.__get_twitter()

		print(f"Loaded YouTube: {len(load_data_yt)} of {len(self.members)}")
		print(f"Load Failed {len(self.members)-len(load_data_yt)} ")
		print(f"Loaded Twitter: {len(load_data_tw)} of {len(self.members)}")
		print(f"Load Failed {len(self.members)-len(load_data_tw)} ")

		i,j = 0, 0
		yt_info = None
		for ii, __sub in enumerate(load_data_yt):
			for data_men_check in self.members :
				if data_men_check["youtube"] == __sub["yt_id"] :
					yt_info = __sub
					tw_id = data_men_check["twitter"]
					break

			for ii, __tw in enumerate(load_data_tw) :
				if str(tw_id) == str(__tw["tw_id"]) :
					for mem in self.members :
						if str(tw_id) == str(mem["twitter"]) :
							__member = mem
							i += 1 

							res.append({
								"name" : __member["name"],
								"yt_info" : yt_info,
								"tw_info" : __tw
							})

							break


		# print(res)
		return res 

	def __get_subscribe(self) :
		res = []
		for channel in self.__getchannelid() :
			req = requests.get(
				self.yturl.format(
					"youtube/v3/channels",
					(
						"&part=statistics&part=snippet&part=brandingSettings" + channel + "&fields=items(id,statistics/viewCount,statistics/subscriberCount,statistics/videoCount,snippet/title,snippet/description,snippet/thumbnails,brandingSettings)"
					)
				)
			)

			
			for __x in req.json()["items"] :
				if not "image" in __x["brandingSettings"] :
					url = None
				else :
					url = __x["brandingSettings"]["image"]["bannerExternalUrl"]
					
				contents = {
					"yt_id" : __x["id"],
					"yt_title" : __x["snippet"]["title"],
					"yt_description" : __x["snippet"]["description"],
					"yt_icon" : __x["snippet"]["thumbnails"]["high"]["url"],
					"yt_banner" : url,
					"yt_subscribe_counts" : __x["statistics"]["subscriberCount"],
					"yt_view_counts" : __x["statistics"]["viewCount"],
				}

				res.append(contents)

		return res

	def __get_twitter(self) :
		ids = []
		res = []

		for get_id_tw in self.members :
			ids.append(get_id_tw["twitter"])

		for tw_info in self.tw.get_profile(ids=ids) :
			res.append({
				"tw_id" : tw_info.id,
				"tw_name" : tw_info.name,
				"tw_desc" : tw_info.description,
				"tw_follower" : tw_info.follower,
				"tw_location" : tw_info.location,
				"tw_url" : tw_info.url,
				"tw_icon" : tw_info.profileurl,
				"tw_banner" : tw_info.bannerurl
			})

		return res

	def __getmembers(self) :
		with open(os.path.join(self.path_db, ("hololivedb.json")),"r") as db :
			self.members = json.loads(db.read())

	def __getchannelid(self) :
		# Setting 
		s = 0
		res = []

		while True :
			all_data = len(self.members)
			get_ch = self.__format(self.members,start=s)

			if all_data == get_ch[1] :
				res.append(get_ch[0])
				break

			res.append(get_ch[0])
			s += get_ch[1]

		return res

	def __load_lang(self, lang="th") :
		with open(os.path.join(os.getcwd(), "lang", lang + ".json"),"r") as f :
			return json.loads(f.read())

	# Check if people follower over 10000
	def __judge(self, member, key, contents, old_contents, th_val):
		if key in contents[member].keys():
			if member in old_contents :
				diff = int(contents[member][key]) // th_val > int(old_contents[member][key]) // th_val
				if diff :
					return True
				else:
					return False
			else :
				return False
		else:
			return False

	def __format(self, arr: list, start=0) :
		prams = ""
		i,j  = 0, start

		for x in arr[start:len(arr)] :
			prams = prams + "&id=" + x["youtube"]
			if i == 49:
				return [prams,j]

			i += 1
			j += 1

		return [prams,j]

class SendMessageDiscord: 
	def __init__(self, token, lang) :
		# Endpoint
		self.discordapi = "https://discord.com/api/v8{}"

		# Setting Discord
		self.token = token
		self.data_profile = self.__get_profile_bot_discord()

		# Setting Discord
		self.channels = []
		self.lang = lang 

	def add_channel(self, channel_id) :
		self.channels.append(channel_id)

	def send_discord_follower(self, member, title, platform , follower, image_url, url, icon_url, color) :
		embed = self.__create_embed(member, title, platform , follower, image_url, url, icon_url, color)

		for x_channels in self.channels :
			i = 0
			while True:
				r = requests.post(self.discordapi.format(f"/channels/{x_channels}/messages"),headers=self.__getheaders(),json=embed)	

				if r.status_code == 200 :
					break
				else :
					i += 1
					if i >= 60 :
						print("Failed send to discord...")
						break

	def send_discord_change(self, member, types, platform , color, url, 
		image_url, icon_url, filedrive=None, large_image=False, old=None, new=None) :

		for x_channels in self.channels :
			while True:
				files=[]
				i = 1

				for file in filedrive :
					files.append(
						(
							f"file{i}",(
								"%s%s.png" % (re.sub('[^a-zA-Z]+', '', member.lower().replace(" ","")),str(datetime.datetime.now().timestamp())),
									open(file,"rb"),
								"image/png"
								)
							)
						)

					i += 1
					
				embed = self.__create_embed_2(
					member=member, 
					types=types, 
					platform =platform , 
					color=color, 
					old=old, 
					new=new, 
					url=url, 
					image_url=image_url, 
					large_image=large_image, 
					icon_url=icon_url, 
					files=files
				)

				payload = {
					"payload_json" : "%s" % json.dumps(embed)
				}

				r = requests.post(self.discordapi.format(f"/channels/{x_channels}/messages"),headers=self.__getheaders(),data=payload,files=files)
				if r.status_code == 200 :
					break
				else :
					i += 1
					if i >= 60 :
						print("Failed send to discord...")
						break

	def __get_profile_bot_discord(self) :
		while True :
			r = requests.get(self.discordapi.format("/users/@me"),headers=self.__getheaders())
			if r.status_code == 200 :
				return r.json()

	def __create_embed(self, member, title, platform , follower, image_url, url, icon_url, color) :
		embed = {
			"embed": {
				"title": str(self.lang["count_alert"]["titie"].format(member=member, type=title.lower(), platform=platform, count=follower)),
				"description": str(self.lang["count_alert"]["description"].format(member=member, type=title.lower(), platform=platform , count=follower)),
				"url": str(url),
				"color": color,
				"timestamp": str(datetime.datetime.now().utcnow()),
				"footer": {
					"icon_url": "https://cdn.discordapp.com/avatars/{}/{}.png?size=1024".format(
						self.data_profile["id"],
						self.data_profile["avatar"]
					),
					"text": self.data_profile["username"]
				},
				"thumbnail": {
					"url": image_url
				},
				"author": {
					"name": platform ,
					"icon_url": icon_url
				},
			}
		}

		return embed

	def __create_embed_2(self, member, types, platform , color, url, image_url, large_image, icon_url, files=None, old=None, new=None) :
		embed = {
			"embed": {
				"title": str(self.lang["change_alert"]["title"].format(change=types.lower(), member=member, platform=platform)),
				"url": str(url),
				"color": color,
				"timestamp": str(datetime.datetime.now().utcnow()),
				"footer": {
					"icon_url": "https://cdn.discordapp.com/avatars/{}/{}.png?size=1024".format(
						self.data_profile["id"],
						self.data_profile["avatar"]
					),
					"text": self.data_profile["username"]
				},
				"thumbnail": {
					"url": image_url
				},
				"author": {
					"name": platform ,
					"icon_url": icon_url
				},
			}
		}

		if not old is None and not new is None :
			embed["embed"].update({
				"fields" : [{
					"name" : types + self.lang["change_alert"]["suffix"]["old"],
					"value" : old,
					"inline" : True
				},
				{
					"name" : types + self.lang["change_alert"]["suffix"]["new"],
					"value" : new,
					"inline" : True
				}]
			})

		if large_image == True :
			embed["embed"].update({
				"image": {
					"url" : f"attachment://{files[0][1][0]}" 
				}
			})

		return embed

	def __getheaders(self) :
		headers = {
			"Authorization" : "Bot " + self.token
		}

		return headers
