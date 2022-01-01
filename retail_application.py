"""
Retail Spatial Interaction Model (SIM)

Author: Rashad A.K. Ahmed
License: GNU

This is an application submitted for assessment as part of the Programming for
Geographical Information Analysis: Core Skills module, in the MSc of
Geographical Information Science program at the School of Geography,
University of Leeds. The application is a Spatial Interaction Model that
estimates the flow of grocery spenditure from Output Areas (OA) to grocery
stores in Leeds.

The application employs a production constrained, entropy-maximizing Spatial
Interaction Model that estimates expenditure flow from Output Areas to
available stores based on:

	Store Accessibility: Derived from the euclidian distances from each zone's
	centroid to the store, while accounting for variations in the travel
	distance tolerance for the inhabitants of each zone based on its Output
	Area Classification class
	Attraction: Derived from store's floorspace, augmented by each brand's
	relative attractiveness

Furthermore, the model assumes that all spenditure flow is contained within
the study area and that all the demand for groceries is met by the stores
(Birkin et al., 2017). A full review of the model is beyond the scope of
this submission.

The code reads in input csv data pertaining to supply and demand side. It then
computes the flow of spend from each DemandZone to every store in the model.
The application then plots the zones according to spend available and stores
according to floorspace. The user is then prompted to open a new store and
asked to inout the new stores attributes. The application computes the new
store's estimated revenues and the inter-brand canibalization brought about by
its introduction to the market. If the user is not satisfied, they are then
prompted to try again with alternative store properties.

When the user is finally satisfied with the new store, the estimated flow
data is saved to appropriate files.
"""

import retailmodel
import csv
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import shapely.geometry


brands = []
demand_zones = []
oac = []
stores = []
alphas = {} # Brand attractiveness dictionary
betas = {} # OAC distance deterrence dictionary


"""
Read the input files, instantiate objects and store the data in appropriate
container types.

Brand Attractiveness and OAC Distance deterrence parameters are stored in
dictionaries alphas and betas, respectively. This enables us to access the
brand attractiveness value through the brand name key, and the distance
deterrence parameter through the OAC number.

Stores, DemandZones, Brands and OAC objects are instantiated and stored
in lists.
"""
# Read the brands data
with open('brands.csv', 'r') as csv_file:
	csv_reader = csv.reader(csv_file)
	brands_data = []
	for row in csv_reader:
		brands_data.append(row)


# Instantiate Brands and populate brands list
for i in range(len(brands_data)):
	if i > 0: # Ignore header row
		# Instantiate brands
		brands.append(retailmodel.Brands(name=brands_data[i][0],
					  alpha=brands_data[i][1], obs_shares=brands_data[i][2]))
		# Populate alphas dictionary
		alphas[str(brands_data[i][0])] = float(brands_data[i][1])


# Read the demand data
with open('demand.csv', 'r') as csv_file:
	csv_reader = csv.reader(csv_file)
	demand_data = []
	for row in csv_reader:
		demand_data.append(row)


#Instantiate DemandZones objects and populate demand_zones list
for i in range(len(demand_data)):
	if i > 0: # Ignore header row
		zone = retailmodel.DemandZones(OA11CD=demand_data[i][0],
									   expenditure=demand_data[i][1],
									   oac=demand_data[i][2],
									   c_easting=demand_data[i][3],
									   c_northing=demand_data[i][4])
		demand_zones.append(zone)


# Read the OAC data
with open('oac.csv', 'r') as csv_file:
	csv_reader = csv.reader(csv_file)
	oac_data = []
	for row in csv_reader:
		oac_data.append(row)


# Instantiate OAC objects and populate oac list
for i in range(len(oac_data)):
	if i > 0: # Ignore header row
		oa_class = retailmodel.OAC(class_no=oac_data[i][0],
							       name=oac_data[i][1], beta=oac_data[i][2])
		# Populate betas
		oac.append(oa_class)
		betas[str(oac_data[i][0])] = float(oac_data[i][2])


# Read the stores data
with open('stores.csv', 'r') as csv_file:
	csv_reader = csv.reader(csv_file)
	stores_data = []
	for row in csv_reader:
		stores_data.append(row)


# Instantiate Stores objects and populate stores list
for i in range(len(stores_data)):
	if i > 0: # Ignore header row
		store = retailmodel.Stores(name=stores_data[i][0],
								   brand=stores_data[i][1],
								   easting=stores_data[i][2],
								   northing=stores_data[i][3],
								   footage=stores_data[i][4],)
		stores.append(store)




"""
Compute the Flows Matrix.

The Flows Matrix is computed using the retailmodel.DemandZones.comp_flow()
method which returns a tuple. Refer to the retailmodel.py module
"""
df_flow = retailmodel.DemandZones.comp_flow(demand_zones, stores, alphas,
											betas)







"""
Map the Suppy and Demand Side Data.

First, a pandas DataFrame is created, containing the stores data. Then, the
coordinate values are used to create shapely point objects; and finally the
DataFrame is converted to a GeoDataFrame to be plotted. A markersize column
is computed from the footage column and used to plot stores in proportion to
their floorspace.

The demand side data consists of a shapefile of Leeds at the OA level
containing spend data. Theshapefile is merged with Flows Matrix. OAs are
symbolized according to their spend.

"""

# Get the relavent stores data in a list
stores_list = []
for store in stores:
	name = store.name
	brand = store.brand
	easting = store.easting
	northing = store.northing
	footage = store.footage

	geo_store = [name, brand, easting, northing, footage]

	stores_list.append(geo_store)


# Define attribute field names
store_attr = ['name', 'brand', 'easting', 'northing', 'footage']

# Construct a DataFrame object from the stores_list list
df_stores = pd.DataFrame(stores_list, columns=store_attr)

# Create a 'Coordinates' tuple from the easting and nothing values
df_stores['Coordinates'] = list(zip(df_stores.easting, df_stores.northing))

# Convert the 'Coordinates' tuples to point geometry
df_stores['Coordinates'] = (
	df_stores['Coordinates'].apply(shapely.geometry.Point))

# Construct a GeoDataFrame from df_stores
geo_stores = gpd.GeoDataFrame(df_stores, geometry='Coordinates')
geo_stores['markersize'] = geo_stores.footage/100



# Read in study_area shapefile
output_areas = gpd.read_file('geographic_data/study_area.shp')
leeds = gpd.read_file('geographic_data/Leeds.shp')

# Merge the df_flows DataFrame with the shapefile
oa_flow = output_areas.merge(df_flow, left_on='OA11CD', right_index=True)


# Plot the map layers
fig, ax = plt.subplots(1, figsize=(15,15))
leeds.plot(ax=ax, facecolor='none', linewidth=2, edgecolor='black')
oa_flow.plot(ax=ax, column='Spend', cmap='Greens', scheme='fisher_jenks',
			 linewidth=0.1, edgecolor='gray', alpha=0.7)

geo_stores.plot(ax=ax, column='brand', markersize='markersize')
fig.suptitle('Supply & Demand Prior to New Store')
plt.show()



"""
Open a new store.

To open a new store, a Stores object must be instantiated. Following that, the
Flows Matrix must be recomputed.

The user is prompted for Stores.__init__() arguments and a Stores object is
instantiated accordingly. The Flows Matrix is then re-computed and the user is
presented with the new store's estimated revenue, trading intensity and the
estimated interbrand canibalization brought about by the new store. The user
then has the option to either try again, with alternate store parameters or
terminate the process, at which point the output data is written in
appropriate file formats
"""

task = input('Do you want to open a new store? \nIf yes, insert y, otherwise\
insert any key and press enter: ')

while task == 'y':
	store_name = input("Insert the new store's name, without_spaces: ")
	#Tesco
	my_brand = input("What's your store's brand? ")
	#429824
	store_e = input("Insert the easting coordinate value: ")
	#436669
	store_n = input("insert the northing coordinate value: ")
	#12000
	store_footage = input("Insert the area of your store in suare feet: ")
	my_store = retailmodel.Stores(name=store_name, brand=my_brand,
								  easting=store_e, northing=store_n,
								  footage=store_footage)
	new_stores = stores.copy()
	new_stores.append(my_store)

	new_df_flow = retailmodel.DemandZones.comp_flow(demand_zones, new_stores,
													alphas, betas)


	brand_revenue = retailmodel.Brands.comp_brand_revenue(my_brand, df_flow)

	print("\nYour Brand's current estimated weekly revenue is:\n"
	   + str(brand_revenue))
	print("\n")




	"""
	Map the newly estimated supply and demand side data.

	The code blocks below are similar to the ones under "Map the Supply and
	Demand Data". It basically adds the new store to the mix after recomputing
	the new Flows Matrix and plots the results


	"""

	# Create an empty list
	new_stores_list = []
	for store in new_stores:
		name = store.name
		brand = store.brand
		easting = store.easting
		northing = store.northing
		footage = store.footage

		geo_store = [name, brand, easting, northing, footage]

		new_stores_list.append(geo_store)


	# Define attribute fields
	#store_attr = ['name', 'brand', 'easting', 'northing', 'footage']

	# Construct a DataFrame object from the new_geo_stores list
	new_df_stores = pd.DataFrame(new_stores_list, columns=store_attr)

	# Create a 'Coordinates' tuple from the easting and northing values
	new_df_stores['Coordinates'] = list(zip(new_df_stores.easting,
									    new_df_stores.northing))

	# Convert the 'Coordinates' tuples to point geometry
	new_df_stores['Coordinates'] = (
		new_df_stores['Coordinates'].apply(shapely.geometry.Point))

	# Construct a GeoDataFrame from new_df_stores
	new_geo_stores = gpd.GeoDataFrame(new_df_stores, geometry='Coordinates')
	new_geo_stores['markersize'] = new_geo_stores.footage/100

	# Merge the new_df_flows object with the shapefile
	new_oa_flow = output_areas.merge(new_df_flow, left_on='OA11CD',
									 right_index=True)

	# Plot the map layers

	new_fig, ax = plt.subplots(1, figsize=(15,15))
	leeds.plot(ax=ax, facecolor='none', linewidth=2, edgecolor='black')
	new_oa_flow.plot(ax=ax, column='Spend', cmap='Greens',
				     scheme='fisher_jenks', alpha=0.7)
	new_geo_stores.plot(ax=ax, column='brand', markersize='markersize')
	ax.set_title('Supply & Demand after New Store')
	plt.show()

	"""
	Get the new stores estimated revenue, trading intensity and interbrand
	canibalization.
	"""

	store_revenue = new_df_flow.loc['Store_Revenue'][my_store.name]
	trading_in =store_revenue/my_store.footage
	new_brand_revenue = retailmodel.Brands.comp_brand_revenue(
			my_brand, new_df_flow)
	cani = brand_revenue + store_revenue - new_brand_revenue

	"""
	Plot the New Store.

	The New Store is plotted against the DemandZones and each demand zone is
	symbolized according to the amount of spend that flows from it to the
	new store.
	"""
	my_fig, ax = plt.subplots(1, figsize=(15,15))
	leeds.plot(ax=ax, facecolor='none', linewidth=2, edgecolor='black')
	# column=my_store.name to access New Store's column in the Flows Matrix
	new_oa_flow.plot(ax=ax, column=my_store.name, cmap='Greens', scheme=\
				    'fisher_jenks', alpha=0.7)
	geo_store = new_geo_stores.loc[135:]
	geo_store.plot(ax=ax, markersize='markersize')
	ax.set_title('New Store')
	plt.show()

	print("Your new store is estimated to make a weekly revenue of: \n" +
str(store_revenue) + " Pounds Sterling per week\nAt a trading intensity \
of: \n" + str(trading_in) + " per sq.foot \nWith a total interbrand \
canibalization of: \n" + str(cani) + " Pounds Sterling per week\n")
	print("Your brands new revenue is estimated to be: \n" +
	   str(new_brand_revenue) + "\n")


	task = input("Do you want to try again? \nIf yes, insert y, otherwise\
insert any key and press enter: ")



## Write the final outputs
#oa_flow.to_file(driver='ESRI Shapefile', filename='oa_flow.shp')
#new_oa_flow.to_file(driver='ESRI Shapefile', filename='new_oa_flow.shp')
#df_flow.to_csv('df_flow.csv')
#new_df_flow.to_csv('new_df_flow.csv')