# -*- coding: utf-8 -*-

import os
import csv
import matplotlib.pyplot as plt

file_folder = "files"

viewers = "files/viewers_2022-06.csv"
pageviews = "files/page_views_2022-06.csv"

class AnnualData():
	def __init__(self, start_year=None, start_month=None, irn_map=None):
		self.start_year = start_year
		self.start_month = start_month
		self.irn_map = irn_map
		self.files = os.listdir(file_folder)
		self.loaded_files = 0

		self.bucket = UrlBucket()

	def year_of_data(self):
		year = int(self.start_year)
		month = int(self.start_month)

		while self.loaded_files < 12:
			if month == 13:
				month = 1
				year += 1
			else: pass
			
			self.load_file(year, month)

			month += 1
			self.loaded_files += 1

		return self.bucket

	def load_file(self, year, month):
		s_year = str(year)
		s_month = str(month)
		if len(s_month) == 1:
			s_month = "0{}".format(s_month)
		file_suffix = "{year}-{month}.csv".format(year=s_year, month=s_month)
		for file in self.files:
			if file.endswith(file_suffix) and file.startswith("page"):
				load_up = MonthlyData(year, month, self.irn_map)
				load_up.combine_pageviews()
			
class MonthlyData():
	def __init__(self, year=None, month=None, irn_map=None, bucket=None):
		self.year = year
		self.month = month
		self.irn_map = irn_map
		self.bucket = bucket
		self.viewers_data = []
		self.pageviews_data = []
		self.view_row_count = 0
		self.page_row_count = 0

		if self.bucket == None:
			self.bucket = UrlBucket()

	def open_viewers(self):
		viewers = file_folder + "/viewers_" + year + "-" + month + ".csv"
		with open(viewers, newline='') as viewers_source:
			view_reader = csv.DictReader(viewers_source, delimiter=",")
			for row in view_reader:
				self.viewers_data.append(row)
				self.view_row_count += 1

	def open_pageviews(self):
		s_year = str(self.year)
		s_month = str(self.month)
		if len(s_month) == 1:
			s_month = "0{}".format(s_month)
		pageviews = file_folder + "/page_views_" + s_year + "-" + s_month + ".csv"
		with open(pageviews, newline='') as pageviews_source:
			page_reader = csv.DictReader(pageviews_source, delimiter=",")
			for row in page_reader:
				self.pageviews_data.append(row)
				self.page_row_count += 1

	def combine_viewers(self):
		viewers_dict = {}
		self.open_viewers()
		for i in self.viewers_data:
			country = i["Country"]
			views = int(i["Daily viewers sum"])
			if country not in viewers_dict:
				viewers_dict.update({country: {"Views": views}})
			else:
				add_views = viewers_dict[country]["Views"]
				add_views = int(add_views)
				add_views += views
				viewers_dict[country].update({"Views": add_views})
		return viewers_dict

	def combine_pageviews(self):
		pageviews_dict = {}
		self.open_pageviews()
		for row in self.pageviews_data:
			url = row["URL"]
			irn = self.map_irn(url)

			url_check = self.bucket.find_in_bucket(url, self.year, self.month)
			
			if url_check == False:
				url_obj = UrlData(url=url, row_data=row, year=self.year, month=self.month, irn=irn)
				self.bucket.put_in_bucket(url_obj)
			else:
				url_check.update_url(add_row=row)

	def map_irn(self, url):
		for i in self.irn_map:
			if url == i["WebAssociationAddress"]:
				irn = i["irn"]
				return irn

class UrlBucket():
	def __init__(self):
		self.bucket = []

	def put_in_bucket(self, urlobject):
		self.bucket.append(urlobject)
		return True

	def find_in_bucket(self, url, year, month):
		for crab in self.bucket:
			if url == crab.url and year == crab.year and month == crab.month:
				return crab
		return False

	def munch_bucket(self):
		for crab in self.bucket:
			crab.total_views()
			crab.overall_average()
		return self.bucket
'''
class ViewMonthlyData():
	def __init__(self, dataset=None):
		self.dataset = dataset

	def parse_dataset(self):
		for url in self.dataset.keys():
			self.data_for_url(url)

	def data_for_url(self, url=None):
		if url:
			url_data = self.dataset[url]

#			print(url_data)

			title = url_data["Title"]
			views = 0
			times = 0

			count = 1
			available_average = False
			for country in url_data["Countries"]:
				if int(country["Views"]):
					views += country["Views"]
				try:
					int(country["Average time"])
					times += country["Average time"]
					count += 1
					available_average = True
				except: pass

			if available_average == True:
				times = times/count
			else:
				times = "n/a"

#			print(url, title, views, times)
			return [url, title, views, times]

	def print_month(self):
		csv_filename = "july_collated.csv"
		heading_row = ["url", "title", "views", "averageTime"]

		write_file = open(csv_filename, 'w', newline='', encoding='utf-8')
		writer = csv.writer(write_file, delimiter = ',')
		writer.writerow(heading_row)

		for url in self.dataset:
			data_row = self.data_for_url(url)
			writer.writerow(data_row)

		write_file.close()
'''

class UrlData():
	# Need to update this, possibly with a subclass that holds each month's data
	def __init__(self, url=None, row_data=None, year=None, month=None, irn=None):
		self.url = url
		self.row_data = row_data
		self.year = year
		self.month = month
		self.irn = irn
		self.title = None
		self.countries = []
		self.views = 0
		self.times = 0
		self.count = 1

		self.new_url()

# Creates a brand new url object
	def new_url(self):
		self.title = self.row_data["Title"]

		country_row = self.update_countries()

		self.countries.append(country_row)

# Updates an existing url object with new source data
	def update_url(self, add_row=None):
		index = 0
		written = False
		add_country = add_row["Country"]
		for country in self.countries:
			if add_country == country:
				add_views = self.update_views(index=index, add_row=add_row)
				add_times = self.update_times(index=index, add_row=add_row)
				add_cCount = self.countries["add_country"]["cCount"]
				add_cCount += 1
				update_existing_country = {"Views": add_views, "Times": add_times, "cCount": add_cCount}
				self.countries[index].update(update_existing_country)
				written = True
				continue
			index += 1

		if written == False:
			new_country = self.update_countries(add_row=add_row)
			self.countries.append(new_country)

		self.count += 1

# Provides a new country dict on an existing url
	def update_countries(self, add_row=None):
		if add_row:
			source = add_row
		else:
			source = self.row_data

		country = source["Country"]
		country_views = source["Views"]
		country_times = source["Average time (s)"]

		try:
			country_views = int(country_views)
		except:
			country_views = None
		try:
			country_times = int(country_times)
			cCount = 1
		except:
			country_times = None
			cCount = 0

		country_row = {"Country": country, "Views": country_views, "Times": country_times, "cCount": cCount}

		return country_row

# Updates the total views for an existing country
	def update_views(self, index=None, add_row=None):
		views = self.countries[index]["Views"]
		add_views = add_row["Views"]
		add_views = int(add_views)
		add_views += views

		return add_views

# Updates the average time for an existing country
	def update_times(self, index=None, add_row=None):
		times = self.countries[index]["Times"]
		cCount = self.countries[index]["cCount"]
		add_times = add_row["Times"]
		try:
			add_times = int(add_times)
		except:
			add_times = None

		if type(times) == int:
			if type(add_times) == int:
				add_times += times
				cCount += 1
				average_time = add_times/cCount
				self.countries[index].update({"cCount":cCount})
				return average_time
			else:
				return times
		elif type(add_times) == int:
			return add_times

	def total_views(self):
		for country in self.countries:
			if "Views" in country:
				country_views = country["Views"]
				try:
					country_views = int(country_views)
					self.views += country_views
				except: pass

	def overall_average(self):
		time_list = []
		summed_times = 0
		country_count = 0
		for country in self.countries:
			if "Times" in country:
				time_list.append(country["Times"])
				country_count += 1
		for time in time_list:
			try:
				time = int(time)
				summed_times += time
			except: pass

		self.times = summed_times/country_count

class DisplayCharts():
	def __init__(self, bucket=None):
		self.bucket = bucket
		self.crabs = self.bucket.munch_bucket()

	def top_views(self, cutoff):
		sorted_crabs = sorted(self.crabs, key=lambda x: x.views, reverse=True)
		loop = 0
		while loop < cutoff:
			this_crab = sorted_crabs[loop]
			print(this_crab.month, this_crab.year, this_crab.title, this_crab.views, this_crab.times)
			loop += 1

	def display_year(self):
		date_views = {}
		date_axis = []
		view_axis = []
		for crab in self.crabs:
			print(crab.title)
			crab_views = 0
			crab_date = str(crab.year) + "_" + str(crab.month)
			if crab_date in date_views:
				crab_views = date_views[crab_date] + crab.views
			else:
				crab_views = crab.views
			date_views.update({crab_date: crab_views})
		for date in date_views.keys():
			date_axis.append(date)
			view_axis.append(date_views[date])
		pos = list(range(12))
		print(date_views)
#		self.bar_chart(view_axis, date_axis, pos)

	def bar_chart(self, numbers, labels, pos):
		plt.bar(pos, numbers, color="blue")
		plt.xticks(ticks=pos, labels=labels)
		plt.show()

def attach_irns():
	irn_map = []
	with open("Data.csv", newline="") as f:
		f_reader = csv.DictReader(f, delimiter=",")
		for row in f_reader:
			irn_map.append(row)
	return irn_map

year = "2021"
month = "07"

irn_map = attach_irns()

year_data = AnnualData(start_year=year, start_month=month, irn_map=irn_map)
year_data.year_of_data()

display_year = DisplayCharts(year_data.bucket)

display_year.display_year()