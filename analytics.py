# -*- coding: utf-8 -*-

import os
import csv
import matplotlib.pyplot as plt

view_dir = "files/viewers"
page_dir = "files/page_views"

viewers = "files/viewers/viewers_2022-06.csv"
pageviews = "files/page_views/page_views_2022-06.csv"

class AnnualData():
	def __init__(self, start_year=None, start_month=None, irn_map=None):
		self.start_year = start_year
		self.start_month = start_month
		self.irn_map = irn_map
		self.p_files = os.listdir(page_dir)
		self.v_files = os.listdir(view_dir)
		self.loaded_files = 0

		self.bucket = DataBucket()

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
		for file in self.p_files:
			if file.endswith(file_suffix):
				load_up = MonthlyData(year, month, self.irn_map, bucket=self.bucket)
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
			self.bucket = DataBucket()

	def open_viewers(self):
		viewers = view_dir + "/viewers_" + year + "-" + month + ".csv"
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
		pageviews = page_dir + "/page_views_" + s_year + "-" + s_month + ".csv"
		with open(pageviews, newline='') as pageviews_source:
			page_reader = csv.DictReader(pageviews_source, delimiter=",")
			for row in page_reader:
				self.pageviews_data.append(row)
				self.page_row_count += 1

	def combine_viewers(self):
		self.open_viewers()
		for row in self.viewers_data:
			country_code = row["Country"]

			crab = self.bucket.find_in_bucket(country_code=country_code)

			if crab == False:
				new_crab = DataCrab(country_code=country_code, row_data=row, year=self.year, month=self.month)
				self.bucket.put_in_bucket(new_crab)
			else:
				leg = crab.find_leg(year=self.year, month=self.month)
				if leg == False:
					crab.add_month(row=row, year=self.year, month=self.month)
				else:
					leg.update_month(row=row)

			views = int(row["Daily viewers sum"])
			if country not in viewers_dict:
				viewers_dict.update({country: {"Views": views}})
			else:
				add_views = viewers_dict[country]["Views"]
				add_views = int(add_views)
				add_views += views
				viewers_dict[country].update({"Views": add_views})
		return viewers_dict

	def combine_pageviews(self):
		self.open_pageviews()
		for row in self.pageviews_data:
			url = row["URL"]
			irn = self.map_irn(url)

			crab = self.bucket.find_in_bucket(url=url)
			
			if crab == False:
				new_crab = DataCrab(url=url, row_data=row, year=self.year, month=self.month, irn=irn)
				self.bucket.put_in_bucket(new_crab)
			else:
				leg = crab.find_leg(year=self.year, month=self.month)
				if leg == False:
					crab.add_month(row=row, year=self.year, month=self.month)
				else:
					leg.update_month(row=row)

	def map_irn(self, url):
		for i in self.irn_map:
			if url == i["WebAssociationAddress"]:
				irn = i["irn"]
				return irn

class DataBucket():
	def __init__(self):
		self.bucket = []

	def put_in_bucket(self, data_object):
		self.bucket.append(data_object)
		return True

	def find_in_bucket(self, url=None, country_code=None):
		for crab in self.bucket:
			if url:
				if url == crab.url:
					return crab
			if country_code:
				if country_code == crab.country_code:
					return crab
		return False

	def munch_bucket(self, query_type=None):
		for crab in self.bucket:
			if query_type == "pageviews":
				for leg in crab.month_list:
					leg.total_views()
					leg.overall_average()
		return self.bucket

class DataCrab():
	def __init__(self, url=None, row_data=None, year=None, month=None, irn=None, country_code=None):
		self.crab_type = None
		self.url = url
		self.row_data = row_data
		self.year = year
		self.month = month
		self.month_list = []
		self.irn = irn
		self.country_code = country_code
		self.title = None
		self.views = 0
		self.times = 0
		self.count = 1

		if self.url:
			self.crab_type = "pageviews"
		if self.country_code:
			self.crab_type = "viewers"

		self.new_url()

# Uses the initial row data to set the title and start the first month's processing
	def new_url(self):
		self.title = self.row_data["Title"]

		self.add_month(row=self.row_data, year=self.year, month=self.month)

	def add_month(self, row, year, month):
		this_month = DataCrabMonth(row=row, year=year, month=month, crab_type=self.crab_type)

		self.month_list.append(this_month)

	def find_leg(self, year, month):
		for leg in self.month_list:
			if year == leg.year and month == leg.month:
				return leg
		return False

class DataCrabMonth():
	def __init__(self, row=None, year=None, month=None, crab_type=None):
		self.crab_type = crab_type
		self.row = row
		self.year = year
		self.month = month
		self.countries = []
		self.count = 1
		self.views = 0
		self.times = 0

		if self.crab_type == "pageviews":
			self.new_month()
		if self.crab_type == "viewers":
			self.count += row["Daily viewers sum"]

# Add the first row's data to the month
	def new_month(self):
		country_row = self.update_countries(row=self.row)
		self.countries.append(country_row)

# Add a new row's data to an existing country, or if not available, to a new country
	def update_month(self, row):
		index = 0
		written = False
		add_country = row["Country"]
		for country in self.countries:
			if add_country == country:
				add_views = self.update_views(index=index, row=row)
				add_times = self.update_times(index=index, row=row)
				add_cCount = self.countries["add_country"]["cCount"]
				add_cCount += 1
				update_existing_country = {"Views": add_views, "Times": add_times, "cCount": add_cCount}
				self.countries[index].update(update_existing_country)
				written = True
				continue
			index += 1

		if written == False:
			new_country = self.update_countries(row=row)
			self.countries.append(new_country)

		self.count += 1

# Provides a new country dict to the current month
	def update_countries(self, row):
		country = row["Country"]
		country_views = row["Views"]
		country_times = row["Average time (s)"]

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
	def update_views(self, index=None, row=None):
		views = self.countries[index]["Views"]
		add_views = row["Views"]
		add_views = int(add_views)
		add_views += views

		return add_views

# Updates the average time for an existing country
	def update_times(self, index=None, row=None):
		times = self.countries[index]["Times"]
		cCount = self.countries[index]["cCount"]
		add_times = row["Times"]
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
		self.crabs = self.bucket.munch_bucket(query_type="pageviews")

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
		title = "All views on Google Art by month"
		for crab in self.crabs:
			crab_views = 0
			if crab.crab_type == "pageviews":
				for leg in crab.month_list:
					crab_year = str(leg.year)
					crab_month = str(leg.month)
					if len(crab_month) == 1:
						crab_month = "0{}".format(crab_month)
					crab_date = crab_year + "_" + crab_month
					if crab_date in date_views:
						crab_views = date_views[crab_date] + leg.views
					else:
						crab_views = leg.views
					date_views.update({crab_date: crab_views})
		for date in sorted(date_views.keys()):
			date_axis.append(date)
			view_axis.append(date_views[date])
		pos = list(range(12))
		print(date_views)
		self.bar_chart(view_axis, date_axis, pos, title)

	def bar_chart(self, numbers, labels, pos, title):
		plt.bar(pos, numbers, color="blue")
		plt.xticks(ticks=pos, labels=labels)
		plt.title(title)
		plt.show()

	def line_chart(self, numbers, labels, title):
		countries = []
		for date in numbers.keys():
			countries.append(key in numbers[date].keys())
		for country in countries:
			y_axis = []
			for date in sorted(numbers.keys()):
				country_views = numbers[date][country]
				y_axis.append(country_views)
				plt.plot(labels, y_axis, label=country)

		plt.title(title)
		plt.legend()
		plt.show()

	def url_over_time(self, url):
		crab = self.bucket.find_in_bucket(url=url)
		title = "All views for {} by month".format(crab.title + " (" + str(crab.irn) + ")")
		date_views = {}
		date_axis = []
		view_axis = []
		crab_views = 0
		for leg in crab.month_list:
			crab_year = str(leg.year)
			crab_month = str(leg.month)
			if len(crab_month) == 1:
				crab_month = "0{}".format(crab_month)
			crab_date = crab_year + "_" + crab_month
			if crab_date in date_views:
				crab_views = date_views[crab_date] + leg.views
			else:
				crab_views = leg.views
			date_views.update({crab_date: crab_views})
		for date in sorted(date_views.keys()):
			date_axis.append(date)
			view_axis.append(date_views[date])
		pos = list(range(12))
		print(date_views)
		self.bar_chart(view_axis, date_axis, pos, title)

	def country_counts(self):
		# To do: make this work
		title = "Views by country across 2021/2022"
		date_container = {}
		date_axis = []
		for crab in self.crabs:
			crab_views = 0
			if crab.crab_type == "viewers":
				crab_code = crab.country_code
				for leg in crab.month_list:
					crab_year = str(leg.year)
					crab_month = str(leg.month)
					if len(crab_month) == 1:
						crab_month = "0{}".format(crab_month)
					crab_date = crab_year + "_" + crab_month
					if crab_date in date_container:
						if crab_code in date_container[crab_date]:
							crab_views = date_container[crab_date][crab_code] + leg.views
						else: crab_views = leg.views
					else:
						crab_views = leg.views
					date_container.update({crab_date: {crab_code: crab_views}})
			for date in sorted(date_container.keys()):
				date_axis.append(date)
		pos = list(range(12))
		print(date_axis)
		self.line_chart(date_container, date_axis, title)

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

#display_year.display_year()
#display_year.url_over_time("https://artsandculture.google.com/asset/9AHdocbIYZza7A")
display_year.country_counts()

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