# -*- coding: utf-8 -*-

import csv

viewers = "viewers_2022-06.csv"
pageviews = "page_views_2022-06.csv"

class MonthlyData():
	def __init__(self, viewers, pageviews):
		self.viewers = viewers
		self.pageviews = pageviews
		self.viewers_data = []
		self.pageviews_data = []
		self.view_row_count = 0
		self.page_row_count = 0

		self.bucket = UrlBucket()

	def open_viewers(self):
		with open(self.viewers, newline='') as viewers_source:
			view_reader = csv.DictReader(viewers_source, delimiter=",")
			for row in view_reader:
				self.viewers_data.append(row)
				self.view_row_count += 1

	def open_pageviews(self):
		with open(self.pageviews, newline='') as pageviews_source:
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

			url_check = self.bucket.find_in_bucket(url)
			
			if url_check == False:
				url_obj = UrlData(url=url, row_data=row)
				self.bucket.put_in_bucket(url_obj)
			else:
				url_check.update_url(add_row=row)

class UrlBucket():
	def __init__(self):
		self.bucket = []

	def put_in_bucket(self, urlobject):
		self.bucket.append(urlobject)
		return True

	def find_in_bucket(self, url):
		for crab in self.bucket:
			if url == crab.url:
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
	def __init__(self, url=None, row_data=None):
		self.url = url
		self.row_data = row_data
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

def top_views(crabs, cutoff):
	sorted_crabs = sorted(crabs, key=lambda x: x.views, reverse=True)
	loop = 0
	while loop < cutoff:
		this_crab = sorted_crabs[loop]
		print(this_crab.title, this_crab.views, this_crab.times)
		loop += 1

july_2022 = MonthlyData(viewers, pageviews)

july_views = july_2022.combine_viewers()
july_pages = july_2022.combine_pageviews()

crabs = july_2022.bucket.munch_bucket()
top_views(crabs, 10)


#for crab in crabs:
#	print(crab.title, crab.views, crab.times)

#show_july = ViewMonthlyData(dataset=july_pages)
#show_july.parse_dataset()
#show_july.print_month()