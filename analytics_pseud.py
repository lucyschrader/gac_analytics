# -*- coding: utf-8 -*-

import os
import csv
import math
import matplotlib.pyplot as plt
import json
import random
import re

files_dir = "files/"
pageview_dir = files_dir + "page_views"
viewers_dir = files_dir + "viewers"
CO_p_dir = files_dir +"co_pages"
CO_loc_dir = files_dir +"co_loc"
misc_dir = files_dir + "misc"
source_folders = [pageview_dir, viewers_dir, CO_p_dir, CO_loc_dir]

with open(misc_dir + "/codesDict.json") as f:
	codesDict = json.load(f)

# Create a new report for any number of months
# Can choose pageviews, viewers, CO numbers, or all
class MultiMonth():
	def __init__(self, start_year=None, start_month=None, q_len=1):
		self.start_year = start_year
		self.start_month = start_month
		self.q_len = q_len
		self.irn_map = []

		self.bucket = DataBucket()

		with open(misc_dir + "/irnmap.csv", newline="") as f:
			f_reader = csv.DictReader(f, delimiter=",")
			for row in f_reader:
				self.irn_map.append(row)

# Run through the required files and move the data to the bucket
	def select_source_files(self):
		loaded_files = 0
		year = self.start_year
		month = self.start_month
		while loaded_files < self.q_len:
			if month == 13:
				month = 1
				year += 1
			else: pass

			s_year = str(year)
			s_month = str(month)
			if len(s_month) == 1:
				s_month = "0{}".format(s_month)

			file_suffix = "{y}-{m}.csv".format(y=s_year, m=s_month)

			for folder in source_folders:
				for file in os.listdir(folder):
					if file.endswith(file_suffix):
						self.harvest(year, month, folder, file_suffix)

			month += 1
			loaded_files += 1

# Pull out the data from the source file and put it in an iterable list
	def harvest(self, year, month, folder, file_suffix):
		source_data = []
		if folder == pageview_dir:
			file_prefix = "page_views_"
			source_type = "page"

		elif folder == viewers_dir:
			file_prefix = "viewers_"
			source_type = "view"

		elif folder == CO_p_dir:
			file_prefix = "co_pages_"
			source_type = "co"

		elif folder == CO_loc_dir:
			file_prefix = "co_loc_"
			source_type = "co"
		
		source_file = folder + "/" + file_prefix + file_suffix
		
		with open(source_file, newline="", encoding="utf-8") as source:
			reader = csv.DictReader(source, delimiter=",")
			for row in reader:
				source_data.append(row)

		self.store_month_data(source_data, source_type, year, month)

# Go row by row through the source data to get it in the right crab
	def store_month_data(self, source_data, source_type, year, month):
		for row in source_data:
			if source_type == "page":
				url = row["URL"]
				irn = self.associate_irn(url)
				
				crab = self.bucket.find_crab(url=url)

			elif source_type == "view":
				country_code = row["Country"]
				
				crab = self.bucket.find_crab(country_code=country_code)

			elif source_type == "co":
#				print(row)
				if "Page" in row:
					url_slug = row["Page"].split("/")
					irn = url_slug[2]
					irn = re.sub("\?.*$", "", irn)
					crab = self.bucket.find_crab(irn=irn)

				elif "Country" in row:
					country_name = row["Country"]
					for key in codesDict.keys():
						if country_name == codesDict[key]:
							country_code = key
						else:
							country_code = "ZZ"
					crab = self.bucket.find_crab(country_code=country_code)

			if crab == False:
				if source_type == "page":
					new_crab = DataCrab(url=url, row=row, year=year, month=month, irn=irn)
					self.bucket.put_in_bucket(new_crab)
				elif source_type == "view":
					new_crab = DataCrab(country_code=country_code, row=row, year=year, month=month)
					self.bucket.put_in_bucket(new_crab)
				elif source_type == "co":
					pass
					
			else:
				leg = crab.find_leg(year=year, month=month)
				if leg == False:
					if source_type == "co":
						pass
					else:
						new_leg = crab.add_leg(row=row, year=year, month=month)
				else:
					crab.update_leg(row=row, year=year, month=month, source_type=source_type)

	def associate_irn(self, url=None):
		for i in self.irn_map:
			if url == i["WebAssociationAddress"]:
				irn = i["irn"]
				return irn

# Create a bucket for the full harvest's data
class DataBucket():
	def __init__(self):
		self.bucket = []

	def put_in_bucket(self, data_object):
		self.bucket.append(data_object)

	def find_crab(self, url=None, country_code=None, irn=None):
		for crab in self.bucket:
			if url:
				if url == crab.url:
					return crab
			elif country_code:
					if country_code == crab.country_code:
						return crab
			elif irn:
					if irn == crab.irn:
						return crab
		return False

	def munch_crabs(self):
		for crab in self.bucket:
			crab.total_crab_views()
			crab.average_crab_times()
			crab.total_co_views()
			crab.average_co_times()
			crab.total_co_sessions()
		return self.bucket

# Every url or country gets its own crab
# All monthly data is attached to one or the other
class DataCrab():
	def __init__(self, url=None, irn=None, country_code=None, row=None, year=None, month=None):
		self.url = url
		self.irn = irn
		self.country_code = country_code
		self.row = row
		self.year = year
		self.month = month
		self.legs = []
		self.total_views = 0
		self.average_times = 0
		self.co_total_views = 0
		self.co_average_times = 0
		self.co_total_sessions = 0

		if self.url:
			self.crab_type = "page"
		if self.country_code:
			self.crab_type = "view"

		self.new_crab()

	def new_crab(self):
		if "Title" in self.row:
			self.title = self.row["Title"]

		if self.crab_type == "view":
			if self.country_code in codesDict:
				self.country_name = codesDict[self.country_code]

		new_leg = DataCrabLeg(row=self.row, year=self.year, month=self.month, crab_type = self.crab_type)
		self.legs.append(new_leg)

		crab_to_dict = {"url": self.url, "irn": self.irn, "country_code": self.country_code, "crab_type": self.crab_type, "legs": self.legs}

	def find_leg(self, year, month):
		if len(self.legs) > 0:
			for leg in self.legs:
				if year == leg.year and month == leg.month:
					return True
		return False

	def add_leg(self, row, year, month):
		new_leg = DataCrabLeg(row=row, year=year, month=month, crab_type = self.crab_type)
		self.legs.append(new_leg)

	def update_leg(self, row, year, month, source_type):
		for leg in self.legs:
			if leg:
				if year == leg.year and month == leg.month:
					if source_type == "page":
						leg.update_page_countries(row=row)
					elif source_type == "view":
						leg.update_country_views(row=row)
#						print(month, self.country_code, leg.total_views)
					elif source_type == "co":
						leg.update_from_co(row=row)

	def total_crab_views(self):
		for leg in self.legs:
			if leg.total_views == 0:
				leg.total_leg_pageviews()
			self.total_views += leg.total_views

	def average_crab_times(self):
		for leg in self.legs:
			leg.average_leg_times()
		running_av = 0
		count = 0
		for leg in self.legs:
			if leg.average_times:
				running_av += leg.average_times
				count += 1
		if count > 0:
			self.co_average_times = running_av/count

	def total_co_views(self):
		for leg in self.legs:
			if leg.co_views:
				self.co_total_views += leg.co_views

	def average_co_times(self):
		if self.crab_type == "page":
			for leg in self.legs:
				leg.average_co_times()
			running_av = 0
			count = 0
			for leg in self.legs:
				if leg.co_average_times:
					running_av += leg.co_average_times
					count += 1
			if count > 0:
				self.co_average_times = running_av/count

	def total_co_sessions(self):
		for leg in self.legs:
			if leg.co_total_sessions:
				self.co_total_sessions += leg.co_total_sessions

# A full month's collated data across all sources
class DataCrabLeg():
	def __init__(self, row=None, year=None, month=None, crab_type=None):
		self.row = row
		self.year = year
		self.month = month
		self.crab_type = crab_type
		self.countries = []
		self.total_views = 0
		self.average_times = 0
		self.co_views = 0
		self.co_average_times = 0
		self.co_valid_av_count = 0
		self.co_total_sessions = 0

		if self.year:
			self.s_year = str(year)
		if self.month:
			s_month = str(month)
			if len(s_month) == 1:
				self.s_month = "0{}".format(s_month)

		self.new_leg()

# Populate the appropriate parts of the new object
	def new_leg(self):
		if self.crab_type == "page":
			self.update_page_countries(row=self.row, first=True)
		elif self.crab_type == "view":
			self.update_country_views(row=self.row)

# Turn this data object into a dict for writing
	def leg_to_dict(self):
		write_leg = {"Year": self.year, "Month": self.month, "Year (string)": self.s_year, "Month (string)": self.s_month, "Countries": self.countries, "CO views": self.co_views, "CO total time": self.co_average_times, "CO valid average count": self.co_valid_av_count}

# Adds a new country to a pageviews object
	def add_country_to_leg(self, row):
		country_code = row["Country"]
		if country_code in codesDict:
			country_name = codesDict[country_code]
		country_views = row["Views"]
		country_times = row["Average time (s)"]

		try:
			country_view = int(country_views)
		except:
			country_views = None
		try:
			country_times = int(country_times)
			valid_count = 1
		except:
			country_times = None
			valid_count = 0

		self.countries.append({"Country code": country_code, "Country name": country_name, "Views": country_views, "Times": country_times, "Valid times": valid_count})

# Checks if the row's country is already in the pageviews
# object, and if not adds it
# Updates viewcounts and averages if country already in
	def update_page_countries(self, row, first=False):
		if first == True:
			self.add_country_to_leg(row)

		else:
			index = 0
			written = False
			row_country = row["Country"]
			for country in self.countries:
				if row_country == country:
					updated_views = self.update_page_views(index=index, row=row)
					updated_times = self.update_page_times(index=index, row=row)
					new_av = updated_times[0]
					valid_count = updated_times[1]
					
					update_existing_country = {"Views": add_views, "Times": add_times, "Valid times": valid_count}
					self.countries[index].update(update_existing_country)
					written = True
					continue
				index += 1

			if written == False:
				self.add_country_to_leg(row)

# Updates the total pageviews for a given country
	def update_page_views(self, index=None, row=None):
		views = self.countries[index]["Views"]
		add_views = row["Views"]
		add_views = int(add_views)
		add_views += views

		return add_views

# Updates the average page time for a given country
	def update_page_times(self, index=None, row=None):
		times = self.countries[index]["Times"]
		valid_count = self.countries[index]["Valid times"]
		row_times = row["Times"]
		try:
			row_times = int(row_times)
		except:
			row_times = None

		if type(times) == int:
			if type(row_times) == int:
				added_times = row_times + times
				valid_count += 1
				average_time = added_times/valid_count
				return (average_time, valid_count)
			else:
				return (times, valid_count)
		elif type(row_times) == int:
			return (row_times, 1)
		else:
			return (None, 0)

	def update_country_views(self, row):
		try:
			monthly_views = int(row["Daily viewers sum"])
		except:
			monthly_views = 0
		self.total_views += monthly_views

	def update_from_co(self, row):
		if "Unique Page Views" in row:
			row_views = row["Unique Page Views"]
			self.co_views += int(row_views)

		if "Avg. Time on Page" in row:
			try:
				co_avg_time = row["Avg. Time on Page"]
				self.co_average_times + int(co_avg_time)
				self.co_valid_av_count += 1
			except:
				pass

		if "Sessions" in row:
			row_sessions = row["Sessions"]
			self.co_total_sessions += int(row_sessions)

	def total_leg_pageviews(self):
		for country in self.countries:
			if "Views" in country:
				country_views = country["Views"]
				try:
					country_views = int(country_views)
					self.total_views += country_views
				except:
					pass
		return self.total_views

	def average_leg_times(self):
		running_av = 0
		count = 0
		for country in self.countries:
			if "Times" in country:
				try:
					country_times = int(country["Times"])
					running_av += country_times
					count += country["Valid times"]
				except:
					pass
		if count > 0:
			self.average_times = running_av/count
		return self.average_times

	def average_co_times(self):
		if self.co_valid_av_count > 0:
			self.co_average_times = self.co_average_times/self.co_valid_av_count
		return self.co_average_times

# Output a report for the provided parameters
# Points to a stored bucket
class Report():
	def __init__(self, bucket=None, start_year=None, start_month=None, q_len=1):
		self.bucket = bucket
		self.crabs = bucket.munch_crabs()

		self.start_year = start_year
		self.start_month = start_month
		self.q_len = q_len

		self.months = {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June", 7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"}

		self.s_start_year = str(self.start_year)
		self.s_start_month = self.months[self.start_month]

		# Messy because the q_len is inclusive of first and last
		if self.q_len > 1:
			if self.start_month + self.q_len > 12:
				self.end_year = self.start_year + 1
				self.end_month = self.start_month + self.q_len - 13
			else:
				self.end_year = self.start_year
				self.end_month = self.start_month + self.q_len - 1
		else:
			self.end_year = self.start_year
			self.end_month = self.start_month

		self.s_end_year = str(self.end_year)
		self.s_end_month = self.months[self.end_month]

		self.report_file = "{s_s_m} {s_s_y} - {s_e_m} {s_e_y} Google Arts analytics report.csv".format(s_s_m=self.s_start_month, s_s_y=self.s_start_year, s_e_m=self.s_end_month, s_e_y=self.s_end_year)

		self.open_file = open(self.report_file, "w", newline="", encoding="utf-8")

	def write_report(self):
		self.reportwriter = csv.writer(self.open_file, delimiter=",")

		if self.q_len > 1:
			self.reportwriter.writerow(["Data from {s_month} {s_year} to {e_month} {e_year}".format(s_month=self.s_start_month, s_year=self.s_start_year, e_month=self.s_end_month, e_year=self.s_end_year)])
		else:
			self.reportwriter.writerow(["Data for {s_month} {s_year}".format(s_month=self.s_start_month, s_year=self.s_start_year)])
		
		self.see_totals()
		self.see_top(20, "page")

#		print("Top viewed pages on Google Art")
#		self.top_views(cutoff=20, mode="page")

#		print("Top countries using Google Art")
#		self.top_views(cutoff=20, mode="view")

	def see_totals(self):
		self.reportwriter.writerow(["Month", "Google pageviews", "CO pageviews", "Difference"])

		total = 0
		co_total = 0
		loop = 0
		check_year = self.start_year
		check_month = self.start_month
		while loop < self.q_len:
			monthly_totals = self.monthly_pageview_total(check_year, check_month, "page")
			
			month_value = "{y} {m}".format(y=str(check_year), m=str(check_month))

			g_value = monthly_totals[0]
			c_value = monthly_totals[1]

			if c_value > 0:
				difference = "{}%".format(math.ceil(g_value / c_value * 100))
			else:
				difference = "n/a"

			self.reportwriter.writerow([month_value, g_value, c_value, difference])
			print([month_value, g_value, c_value, difference])

			total += g_value
			co_total += c_value

			if check_month == 12:
				check_month = 1
				check_year += 1
			else:
				check_month += 1
			loop += 1
		
		if co_total > 0:
			total_difference = "{}%".format(math.ceil(total / co_total * 100))
		else:
			total_difference = "n/a"

		self.reportwriter.writerow(["Total", total, co_total, total_difference])

	def monthly_pageview_total(self, year, month, mode):
		total_by_month = 0
		co_total_by_month = 0
		for crab in self.crabs:
			if crab.crab_type == mode:
				for leg in crab.legs:
					if leg.year == year and leg.month == month:
						total_by_month += leg.total_views
						co_total_by_month += leg.co_views
		return (total_by_month, co_total_by_month)

	def see_top(self, cutoff, mode):
		self.reportwriter.writerow([""])

		header_row = ["irn", "title"]

		for i in range(0, self.q_len-1):
			if self.start_month + i > 12:
				column_y = str(self.start_year + 1)
				column_m = self.months[self.start_month + i - 12]
			else:
				column_y = str(self.start_year)
				column_m = self.months[self.start_month + i]

			column_title = column_m + column_y
			header_row.append(column_title + " Google")
			header_row.append(column_title + " CO")

		total_columns = ["Google total", "CO total", "Difference"]
		for col in total_columns:
			header_row.append(col)

		self.reportwriter.writerow(header_row)

#		return top x google pages for the whole span, broken down by google and co views month by month, summed
		mode_crabs = []
		for crab in self.crabs:
			if crab.crab_type == mode:
				mode_crabs.append(crab)
		sorted_crabs = sorted(mode_crabs, key=lambda x: x.total_views, reverse=True)

		top_crabs = []
		loop = 0
		while loop < cutoff:
			top_crabs.append(sorted_crabs[loop])
			loop +=1

		if mode == "page":
			for crab in top_crabs:
				crab_total = 0
				crab_co_total = 0
				write_loop = 0
				check_year = self.start_year
				check_month = self.start_month

				data_row = [crab.irn, crab.title]

				while write_loop < self.q_len:
					monthly_totals = self.top_by_month(crab, check_year, check_month)
			
					g_total = monthly_totals[0]
					c_total = monthly_totals[1]

					data_row.append(g_total)
					data_row.append(c_total)

					crab_total += g_total
					crab_co_total += c_total

					if check_month == 12:
						check_month = 1
						check_year += 1
					else:
						check_month += 1
					write_loop += 1

				data_row.append(crab_total)
				data_row.append(crab_co_total)

				if crab_co_total > 0:
					total_difference = "{}%".format(math.ceil(crab_total / crab_co_total * 100))
				else:
					total_difference = "n/a"

				data_row.append(total_difference)

				self.reportwriter.writerow(data_row)

		elif mode == "view":
			pass
#			loop = 0
#			while loop < self.q_len:
#				print(this_crab.country_name + " (" + this_crab.country_code + "): " + str(this_crab.total_views))
#			loop += 1

	def top_by_month(self, crab, year, month):
		for leg in crab.legs:
			if leg.year == year and leg.month == month:
				return (leg.total_views, leg.co_views)
			else:
				pass

	def chart_visitation(self):
#		comparison of visitation by location, compare numbers/percentages each month across span, summed
#		sort by most visits on google
		pass

	def get_goog_views(self):
		pass

	def get_CO_views(self):
		for crab in self.crabs:
			if crab.crab_type == "page":
				pass
				print(crab.irn, crab.total_views, crab.co_total_views)

	def top_views(self, cutoff, mode):
		mode_crabs = []
		for crab in self.crabs:
			if crab.crab_type == mode:
				mode_crabs.append(crab)
		sorted_crabs = sorted(mode_crabs, key=lambda x: x.total_views, reverse=True)
		loop = 0
		while loop < cutoff:
			this_crab = sorted_crabs[loop]
			if mode == "page":
				print(this_crab.title + " (IRN " + str(this_crab.irn) +  "): " + str(this_crab.total_views) + " views, " + str(this_crab.co_total_views) + " CO views")

			elif mode == "view":
				print(this_crab.country_name + " (" + this_crab.country_code + "): " + str(this_crab.total_views))
			loop += 1

	def total_views(self, mode):
		total = 0
		for crab in self.crabs:
			if crab.crab_type == mode:
				total += crab.total_views
		return total

	def average_times(self):
		pass

	def page_over_time(self, irn):
		crab = self.bucket.find_crab(irn=irn)
		for leg in crab.legs:
			print(leg.year, leg.month, leg.total_views)

	def country_totals(self):
		pass

	def bar_chart(self):
		pass

	def line_chart(self):
		pass

year = 2022
month = 7
q_len = 1

year_data = MultiMonth(start_year=year, start_month=month, q_len=q_len)
year_data.select_source_files()

Report = Report(year_data.bucket, start_year=year, start_month=month, q_len=q_len)

#Report.top_views(cutoff=25, mode="view")
#Report.page_over_time("43746")
#Report.get_CO_views()
Report.write_report()