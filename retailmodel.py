import numpy as np
import pandas as pd








class Stores:
	def __init__(self, name, brand, easting, northing, footage):
		"""
		name - name of the store (string)
		brand - store brand (string)
		easting - easting of the store's centroid (float)
		northing - northing value of the store centroid (float)
		footage - area of the store in square feet (integer)
		"""
		self.name = name
		self.brand = brand
		self.footage = int(footage)
		self.easting = float(easting)
		self.northing = float(northing)
		self.location = [float(self.easting), float(self.northing)]


	def __str__(self):
		return "this is the " + str(self.name) + " store of "+\
str(self.brand) + "\nFloorspace: " + str(self.footage) + " sq.feet"


	def dist_to_zone(self, demand_zone):
		"""
		Return distances from store to the centroids of demand zones

		arguments:
		demand_zones -> DemandZones object

		returns:
		distance to demand_zone centroid -> float
		"""
		self.demand_zone = demand_zone
		return abs(((self.easting - self.demand_zone.c_easting)\
**2 + (self.northing - self.demand_zone.c_northing)**2)**0.5)/1000



	def get_store_revenue(self, flows):
		"""
		Return store's total revenue from Flows Matrix

		arguments:
		flow -> Flows Matrix, computed from the DemandZones.comp_flows()
				method -> pandas DataFrame

		returns:
		store revenue -> float

		"""
		self.flow = flows
		return self.flow.loc['Store_Revenue'][self.name]






class Brands:
	def __init__(self, name, alpha, obs_shares):
		self.name = name
		self.alpha = alpha
		self.obs_shares = obs_shares


	def __str__(self):
		return "Brand Name: " + str(self.name) + "\nRelative Attractiveness:\
 " + str(self.alpha) + "\nObserved Shares: " + str(self.obs_shares)


	def comp_brand_revenue(brand, flows):
		"""
		Return Brand's total revenue.

		arguments:
		flows -> Flows Matrix, the output of comp_flow() -> pandas FataFrame

		returns:
		Total revenue of all the stores belonging to the self brand -> float
		"""
		brand_revenue = 0
		for store in flows.columns[1:]:
			if flows.loc['Brand_Name'][store] == brand:
				brand_revenue += flows.loc['Store_Revenue'][store]
		return brand_revenue









class DemandZones:
	def __init__(self, OA11CD, expenditure, oac, c_easting, c_northing):
		"""
		OA11CD - Demand Zone code (string)
		expenditure - amount of spend available in DemandZone per week
		oac -> open area classification code of DemandZone
		suppy -> the stores with which the DemandZone interacts (list of Stores)
		"""
		self.OA11CD = OA11CD
		self.expenditure = float(expenditure)
		self.oac = oac
		self.c_easting = float(c_easting)
		self.c_northing = float(c_northing)

	def __str__(self):
		return "OA11CD: " + str(self.OA11CD) + "\nSpend: " + \
str(self.expenditure) + " Pounds Sterling per week"


	def getoac(self):
		return self.oac


	def dist_to_store(self, store):
		"""
		Return the distance to store in kilometers

		arguments:
		store -> Stores object

		returns:
		distance in kilometers -> float
		"""
		return abs(((self.c_easting - store.easting)\
**2 + (self.c_northing - store.northing)**2)**0.5)/1000



	def comp_ai(self, stores, beta, alphas):
		"""
		Return the Ai term of the SIM equation.

		The Ai term ensures that all available spenditure in a demand zone is
		allocated to a store.

		areguments:
		stores: the list of store objects to which the spenditure will flow
			    these stores represent the supply side of SIM -> list of
				Store Objects.
		beta: the distance deterance parameter of the zone-> float
	    alphas: a dictionary relating each brand to its relative
				attractiveness -> dictionary

		returns:
		Ai term -> float
		"""
		a = 0
		for store in stores:
			dist = self.dist_to_store(store)
			x = beta * dist
			y = float(alphas[store.brand])
			z = (store.footage ** y) * np.exp(-x)
			a += z
		return 1/a





	def comp_flow(self, stores, alphas, betas):
		"""
		Return the Flows Matrix.

		The Flows Matrix is a matrix that relates the spenditure flows from
		each DemandZones object to every Stores object.

		arguments:
		stores -> list of Stores objects
		alphas -> dictionary relating every brand to its relative
				  attractiveness parameter
	    betas -> dictionary relating each OAC class to its distance deterance
				 parameter

	    returns:
		Flows Matrix -> pandas DataFrame
		"""
		if isinstance(self, DemandZones):
			self.zone_flow = []
			Ai = self.comp_ai(stores, betas[self.oac], alphas)
			O = self.expenditure
			for store in stores:
				W = store.footage ** alphas[store.brand]
				C = self.dist_to_store(store)
				X = betas[self.oac] * C
				f = Ai * O * W * np.exp(-X)
				self.zone_flow.append(f)
			return self.zone_flow
		elif isinstance(self, list):
			flows = []

			brand_names = []
			for store in stores: # to have a brands row in output
				brand_names.append(store.brand)
#				flows.append(brand_names)
			for i in range(len(self)):
				zone_flow = []
				Ai = self[i].comp_ai(stores, betas[self[i].oac], alphas)
				O = self[i].expenditure
				for store in stores:
					W = store.footage ** alphas[store.brand]
					C = self[i].dist_to_store(store)
					X = betas[self[i].oac] * C
					f = Ai * O * W * np.exp(-X)
					zone_flow.append(f)
				flows.append(zone_flow)
			columns = []
			for store in stores:
				columns.append(store.name)

			indecies = ['Brand_Name'] # brands row under store name
			for zone in self:
				indecies.append(zone.OA11CD)
			indecies.append('Store_Revenue')
			revenue = [sum(x) for x in zip(*flows)]
			flows.append(revenue)
			flows.insert(0,brand_names)
			return pd.DataFrame(flows, columns=columns, index=indecies)
		else:
			raise Exception('DataType Error: Make sure the self argument\
 is either a DemandZones object or a list of DemandZones objects; the stores\
 argument is a list of Stores objects, the alphas argument is a dictionary\
 whose keys are brands and values are attractiveness parameters and the\
 betas argument is a dictionary whose keys are oac classification codes and\
 values are distance detterance parameters')







class OAC:
	def __init__(self, class_no, name, beta):
		self.name = name
		self.class_no = class_no
		self.beta = beta

	def __str__(self):
		return "OAC Class: " + str(self.name) + "\nbeta: " + str(self.beta)




