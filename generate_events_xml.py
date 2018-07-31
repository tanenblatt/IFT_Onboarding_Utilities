import os
import sys
import collections
import csv
import json
import jinja2
import uuid
from datetime import datetime, date, time
import argparse

# data fields to load from spreadsheets
from data_key import DataKey

# context object to pass to XML templates for rendering
from context import Context

from grouping_function import GroupingFunction

# utilities for handling GS1 (GTIN, GLN, SSCC, etc.)
import gs1_urn

# load a JINJA template to process
def get_template(template_path):
  path, filename = os.path.split(template_path)
  return jinja2.Environment(loader=jinja2.FileSystemLoader(path or './')).get_template(filename)

# load a spreadsheet data into list of records
def load_event_data(fName):
  data = []
  with open(fName, newline='', encoding='utf-8-sig') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
      data.append(row)
  return data

# load spreadsheet data into dictionary, with specified field as key
def load_keyed_data(fName, keyName):
  data = {}
  with open(fName, newline='', encoding='utf-8-sig') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
      keyValue = row.get(keyName)
      if keyValue:
        data[keyValue] = row
      else:
        print('WARNING: load_keyed_data ' + str(keyName) + ' not found')
  return data

# load spreadsheet data into dictionary, with specified field as key and 
def load_grouped_data(fName, keyName, grouping_type):
  data = {}
  with open(fName, newline='', encoding='utf-8-sig') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
      keyValue = row.get(keyName)
      if keyValue:
        group = keyValue if grouping_type == GroupingFunction.EQUALITY else group_of(grouping_type, keyValue)
        if (group in data):
          data[group].append(row)
          print("APPENDING TO GROUP: " + str(group))
        else:
          data[group] = [row]
          print("CREATING TO GROUP: " + str(group))
      else:
        print('WARNING: load_keyed_data ' + str(keyName) + ' not found')
  return data

def group_of(grouping_type, value):
  #print("GROUP_OF: " + str(grouping_type) + ', value: ' + value)
  grouping = None
  if grouping_type == GroupingFunction.DATE_YEAR:
    grouping = year_of(value)
  elif grouping_type == GroupingFunction.DATE_MONTH:
    grouping = month_of(value)
  elif grouping_type == GroupingFunction.DATE_WEEK:
    grouping = week_of(value)
  else:
    print('WARNING: unknown Grouping type, default to EQUALITY')
    grouping = value
  return grouping
  
def convert_to_date(dateStr: str):
  try:
    date = datetime.strptime(dateStr, '%m/%d/%y').date()
    return date
  except:
    return None

def month_of(dateStr):
  date = convert_to_date(dateStr)
  if date:
    return date.month
  else:
    return None

def year_of(dateStr):
  date = convert_to_date(dateStr)
  if date:
    return date.year
  else:
    return None

def week_of(dateStr):
  date = convert_to_date(dateStr)
  if date:
    iso_year, iso_week, iso_weekday = date.isocalendar()
    return iso_week
  else:
    return None

# generate date+time string from component pieces
def calculateTimeInfo(date, time):
  if time:
    # distinguish between 24-hour vs 12-hour times (assume 12-hour ends with AM or PM)
    if time.endswith(('m','M')):
      dateTime = datetime.strptime(date + ' ' + time, '%m/%d/%y %I:%M:%S %p')
    else:
      dateTime = datetime.strptime(date + ' ' + time, '%m/%d/%y %H:%M:%S')
    return dateTime
  else:
    return None

# look up product by specified code, returning either GS1 LGTIN or IFT LGTIN
# Parameter 'code' is used as a key into the 'product' dictionary to find a GTIN.
# If a GTIN is found, then a GTIN URN is returned (or created based on the GTIN). 
# Otherwise, an IFT GTIN is returned
def gtinOf(products, company_prefix, code, lot):
  if not code: return None
  if gs1_urn.already_urn(code):
    return gs1_urn.add_urn_suffix_if_necessary(code, lot)
    
  product = products.get(code, None)
  if product:
    gtin = product.get('GTIN', None)
    if gtin:
      result = gs1_urn.lgtin_data_to_urn(company_prefix, gtin, lot)
    else:
      result = gs1_urn.ift_lgtin_data_to_urn(company_prefix, code, lot)
  else:
    print('WARNING: gtinOf ' + str(code) + ' not found')
    result = None
  #print ('gtinOf: ' + result)
  return result


# Parameter 'code' is used as a key into the 'locations' dictionary to find a GLN.
# If a GLN is found, then a GLN URN is returned (or created based on the GLN). 
# Otherwise, an IFT GLN is returned
def glnOf(locations, company_prefix, code, extension = None):
  if not code: return None
  if gs1_urn.already_urn(code):
    return gs1_urn.add_urn_suffix_if_necessary(code, extension)
    
  location = locations.get(code, None)
  if location:
    gln = location.get('GLN', None)
    if gln:
      result = gs1_urn.sgln_data_to_urn(company_prefix, gln, extension)
    else:
      result = gs1_urn.ift_sgln_data_to_urn(company_prefix, code, extension)
  else:
    print('WARNING: glnOf ' + str(code) + ' not found')
    result = None
  #print ('glnOf: ' + result)
  return result


def purchaseOrderOf(company_prefix, po):
  return gs1_urn.purchase_order_data_to_urn(company_prefix, po) if po else None

def despatchAdviceOf(company_prefix, po, da):
  return gs1_urn.despatch_advice_data_to_urn(company_prefix, po, da) if (po and da) else None

def productionOrderOf(company_prefix, prod):
  return gs1_urn.production_order_data_to_urn(company_prefix, prod) if prod else None

def ssccOf(company_prefix, sscc):
  return gs1_urn.sscc_data_to_urn(company_prefix, sscc) if sscc else None
  
# look up specified data item. If not set, return its default value, if any--otherwise None
def valueOf(dataItem, dataKey):
  return dataItem.get(g_columnLabels.get(dataKey.value, None), g_defaultValues.get(dataKey.value, None))
    
# return tuple containing quantified and unquantified item info. If a quantity was specified for the item, 
# only set values for quantified, otherwise only unquantified
def __itemContext(item, company_prefix, materialKey, quantityKey, uomKey, lotKey):
  quantifiedItem = unquantifiedItem = None
  print('ITEM: ' + str(item))
  if (valueOf(item, materialKey)):
    if valueOf(item, quantityKey):
      quantifiedItem = { 
          materialKey.value: gtinOf(products, company_prefix, valueOf(item, materialKey), valueOf(item, lotKey)),
          quantityKey.value: valueOf(item, quantityKey),
          uomKey.value:      valueOf(item, uomKey)
      }
    elif valueOf(item, materialKey):
      unquantifiedItem = { 
          materialKey.value: gtinOf(products, company_prefix, valueOf(item, materialKey), valueOf(item, DataKey.LOT))
      }
  return quantifiedItem, unquantifiedItem


def datetimeToString(dt):
  if dt:
    return dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
  else:
    return None
  
# compute the context objects for non-transformation events (no from→to data)
def compute_contexts(data, products, locations):
  contexts = []
  for dataItem in data:
    dateTime = calculateTimeInfo(valueOf(dataItem, DataKey.DATE), valueOf(dataItem, DataKey.TIME))
    if not dateTime:
      timeString = None
      print('WARNING: no date/time supplied for event')
    else:
      print('dateTime: ' + str(dateTime) + ', class: ' + dateTime.__class__.__name__)
      timeString = datetimeToString(dateTime)
      #timeString = dateTime.isoformat()
    company_prefix = valueOf(dataItem, DataKey.COMPANY_PREFIX)
    
    quantifiedItem,     item     = __itemContext(dataItem, company_prefix, DataKey.MATERIAL, DataKey.QUANTITY, DataKey.UOM, DataKey.LOT)
    quantifiedFromItem, fromItem = __itemContext(dataItem, company_prefix, DataKey.FROM_MATERIAL, DataKey.FROM_QUANTITY, DataKey.FROM_UOM, DataKey.FROM_LOT)
    quantifiedToItem,   toItem   = __itemContext(dataItem, company_prefix, DataKey.TO_MATERIAL, DataKey.TO_QUANTITY, DataKey.TO_UOM, DataKey.TO_LOT)

    print('UnquantifiedItem: ' + str(item))
    print('QuantifiedItem: ' + str(quantifiedItem))
    print('UnquantifiedFromItem: ' + str(fromItem))
    print('QuantifiedFromItem: ' + str(quantifiedFromItem))
    print('UnquantifiedToItem: ' + str(toItem))
    print('QuantifiedToItem: ' + str(quantifiedToItem))
    
    
    print('DataItem: ' + str(dataItem))
    print('DataKey.Shipper: ' + str(valueOf(dataItem, DataKey.SHIPPER)))
    
    context = Context()
    context.EventID                = str(uuid.uuid4().urn)
    context.TransformationID       = str(uuid.uuid4().urn)
    context.TimeZone               = valueOf(dataItem, DataKey.TIME_ZONE)
    context.Location               = glnOf(locations, company_prefix, valueOf(dataItem, DataKey.LOCATION), valueOf(dataItem, DataKey.LOCATION_EXT))
    context.FromLocation           = glnOf(locations, company_prefix, valueOf(dataItem, DataKey.FROM_LOCATION), valueOf(dataItem, DataKey.FROM_LOCATION_EXT))
    context.ToLocation             = glnOf(locations, company_prefix, valueOf(dataItem, DataKey.TO_LOCATION), valueOf(dataItem, DataKey.TO_LOCATION_EXT))
    context.UnquantifiedItems      = [ item ] if item else None
    context.QuantifiedItems        = [ quantifiedItem ] if quantifiedItem else None
    context.UnquantifiedFromItems  = [ fromItem ] if fromItem else None
    context.QuantifiedFromItems    = [ quantifiedFromItem ] if quantifiedFromItem else None
    context.UnquantifiedToItems    = [ toItem ] if toItem else None
    context.QuantifiedToItems      = [ quantifiedToItem ] if quantifiedToItem else None
    context.ExpirationDate         = valueOf(dataItem, DataKey.EXPIRATION_DATE)
    context.SellByDate             = valueOf(dataItem, DataKey.SELL_BY_DATE)
    context.BestBeforeDate         = valueOf(dataItem, DataKey.BEST_BEFORE_DATE)
    context.ReadPoint              = valueOf(dataItem, DataKey.READ_POINT)
    context.Disposition            = valueOf(dataItem, DataKey.DISPOSITION)
    context.BizStep                = valueOf(dataItem, DataKey.BIZ_STEP)
    context.PurchaseOrder          = purchaseOrderOf(company_prefix, valueOf(dataItem, DataKey.PURCHASE_ORDER))
    context.DespatchAdvice         = despatchAdviceOf(company_prefix, valueOf(dataItem, DataKey.PURCHASE_ORDER), valueOf(dataItem, DataKey.DESPATCH_ADVICE))
    context.ProductionOrder        = productionOrderOf(company_prefix, valueOf(dataItem, DataKey.PRODUCTION_ORDER))
    context.SSCC                   = ssccOf(valueOf(dataItem, DataKey.SHIPPER), valueOf(dataItem, DataKey.SSCC))
    context.Shipper                = valueOf(dataItem, DataKey.SHIPPER)
    contexts.append(context)
  return contexts
  

# return the appropriate value: either min(currentValue, newValue) if 'useMinValue' == True, otherwise max(currentValue, newValue)
def __selectGroupValue(currentValue, newValue, useMinValue):
  if not newValue:
    return currentValue 
  if not currentValue:
    return newValue 
  if useMinValue:
    return min(currentValue, newValue)
  else:
    return max(currentValue, newValue)

# for cases where a specific value should be consistent across events. Should really throw exception in case of failure
def __assureConsistentValue(oldValue, newValue):
  if not oldValue:
    return newValue;
  if oldValue == newValue:
    return oldValue
  else:
    print('ERROR: INCONSISTENT VALUES: ' + str(oldValue) + ' != ' + str(newValue))
  
  
def process_from_or_to_data(is_from: bool, locations_map, dataItem, context, useMinDate):
  print('start of from_or_to, CONTEXT, bizLocation: ' + str(context.Location))
  materialKey           = DataKey.FROM_MATERIAL     if is_from else DataKey.TO_MATERIAL
  quantityKey           = DataKey.FROM_QUANTITY     if is_from else DataKey.TO_QUANTITY
  uomKey                = DataKey.FROM_UOM          if is_from else DataKey.TO_UOM
  lotKey                = DataKey.FROM_LOT          if is_from else DataKey.TO_LOT
  dateKey               = DataKey.FROM_DATE         if is_from else DataKey.TO_DATE
  timeKey               = DataKey.FROM_TIME         if is_from else DataKey.TO_TIME
  locationKey           = DataKey.FROM_LOCATION     if is_from else DataKey.TO_LOCATION
  locationExtensionKey  = DataKey.FROM_LOCATION_EXT if is_from else DataKey.TO_LOCATION_EXT
  
  print('INCOMING context: ' + str(context))
  company_prefix = valueOf(dataItem, DataKey.COMPANY_PREFIX)    
  quantifiedItem, unquantifiedItem = __itemContext(dataItem, company_prefix, materialKey, quantityKey, uomKey, lotKey)
  #print('QuantifiedItem: ' + str(quantifiedItem) + ', UnquantifiedItem: ' + str(unquantifiedItem))
  dateTime = calculateTimeInfo(valueOf(dataItem, dateKey), valueOf(dataItem, timeKey))

  if dateTime and not context.EventTime:
    context.EventTime = dateTime
  else:
    context.EventTime = __selectGroupValue(context.EventTime, dateTime, useMinDate)
    
  location = glnOf(locations_map, company_prefix, valueOf(dataItem, locationKey), valueOf(dataItem, locationExtensionKey))

  if quantifiedItem:
    if is_from:
      context.QuantifiedFromItems.append(quantifiedItem) 
    else:
      context.QuantifiedToItems.append(quantifiedItem) 
  if unquantifiedItem:
    if is_from:
      context.UnquantifiedFromItems.append(unquantifiedItem)
    else:
      context.UnquantifiedToItems.append(unquantifiedItem)
     
  if location:
    if is_from:
      if not location in set(context.FromLocation):
        context.FromLocation.append(location)
    else:
      if not location in set(context.ToLocation):
        context.ToLocation.append(location)

  bizLocation = glnOf(locations_map, company_prefix, valueOf(dataItem, DataKey.LOCATION), valueOf(dataItem, DataKey.LOCATION_EXT))

  context.Location        = __assureConsistentValue (context.Location,       bizLocation)
  context.ExpirationDate  = __selectGroupValue      (context.ExpirationDate, valueOf(dataItem, DataKey.EXPIRATION_DATE), True)
  context.SellByDate      = __selectGroupValue      (context.SellByDate,     valueOf(dataItem, DataKey.SELL_BY_DATE), True)
  context.BestBeforeDate  = __selectGroupValue      (context.BestBeforeDate, valueOf(dataItem, DataKey.BEST_BEFORE_DATE), True)
  context.ReadPoint       = __assureConsistentValue (context.ReadPoint,      valueOf(dataItem, DataKey.READ_POINT))
  context.Disposition     = __assureConsistentValue (context.Disposition,    valueOf(dataItem, DataKey.DISPOSITION))
  context.BizStep         = __assureConsistentValue (context.BizStep,        valueOf(dataItem, DataKey.BIZ_STEP))
  context.PurchaseOrder   = __assureConsistentValue (context.PurchaseOrder,  purchaseOrderOf(company_prefix, valueOf(dataItem, DataKey.PURCHASE_ORDER)))
  context.DespatchAdvice  = __assureConsistentValue (context.DespatchAdvice, despatchAdviceOf(company_prefix, valueOf(dataItem, DataKey.PURCHASE_ORDER), valueOf(dataItem, DataKey.DESPATCH_ADVICE)))
  context.ProductionOrder = __assureConsistentValue (context.ProductionOrder,productionOrderOf(company_prefix, valueOf(dataItem, DataKey.PRODUCTION_ORDER)))
  context.SSCC            = __assureConsistentValue (context.SSCC,           ssccOf(valueOf(dataItem, DataKey.SHIPPER), valueOf(dataItem, DataKey.SSCC)))
  print('end of from_or_to, CONTEXT, bizLocation: ' + str(context.Location))

  return context


# compute the context objects for transformation events (we have from→to data)
def compute_contexts_from_to(from_data, to_data, products, locations_map, useMinDate):
  contexts = []
  keys = set([*from_data] + [*to_data])
  from_locations = set()
  to_locations = set()
  
  for group_key in keys:
    print('Processing Group: ' + group_key)
    if group_key in from_data:
      from_data_items_for_group = from_data[group_key] 
    if group_key in to_data:
      to_data_items_for_group = to_data[group_key] 
    groupDate = None

    quantifiedFromItems = unquantifiedFromItems = []

    context = Context()
    context.EventID               = str(uuid.uuid4().urn)
    context.TransformationID      = str(uuid.uuid4().urn)
    context.QuantifiedFromItems   = []
    context.UnquantifiedFromItems = []
    context.QuantifiedToItems     = []
    context.UnquantifiedToItems   = []
    context.FromLocation          = []
    context.ToLocation            = []

    print('Processing FROM items')
    if from_data_items_for_group:
      for dataItem in from_data_items_for_group:
        context.TimeZone  = valueOf(dataItem, DataKey.TIME_ZONE)
        context = process_from_or_to_data(True, locations_map, dataItem, context, True)
        
        print('QuantifiedFromItems: ' + str(context.QuantifiedFromItems) + ', UnquantifiedFromItems: ' + str(context.UnquantifiedFromItems))
      
    print('Processing TO items')
    quantifiedToItems = unquantifiedToItems = []
    if to_data_items_for_group:
      for dataItem in to_data_items_for_group:
        context.TimeZone  = valueOf(dataItem, DataKey.TIME_ZONE)
        context = process_from_or_to_data(False, locations_map, dataItem, context, True)

    if not context.EventTime:
      print('WARNING: no date/time supplied for event')
    else:
      #context.EventTime = context.EventTime.isoformat()
      context.EventTime = datetimeToString(context.EventTime)
        
    print('CONTEXT, bizLocation: ' + str(context.Location))
    contexts.append(context)
  return contexts




# render JINJA template
def render_data(contexts, template, outputFName):
  with open(outputFName, "w") as outputFile:
    outputFile.write(template.render(contexts=contexts))

def process_default_overrides(overrides, resultList):
  # process default values passed as command line args which override any from config file
  if overrides:
    for override in overrides:
      split = override.split('=')
      if 2 == len(split):
        if DataKey.has_value(split[0]):
          resultList[split[0]] = split[1]
        else:
          print('WARNING: option ' + split[0] + ' is not a valid key')
      else:
        print('WARNING: option ' + override + ' bad format')

# For each PO, compute date range:
#   first PO: startDate: beginning of time, endDate: date of final transformation for the PO, 
#   subsequent PO's: startDate: previous PO's endDate, endDate: date of final transformation for the PO
def computePO_DateRanges(toData):
  result = {}
  for po in toData:
    for dataItem in toData[po]:
      poDate = calculateTimeInfo(valueOf(dataItem, DataKey.TO_DATE), valueOf(dataItem, DataKey.TO_TIME))
      if poDate:
        if po not in result:
          result[po] = poDate
          #print('result[po] = ' + str(poDate))
        else:        
          oldDate = result[po]
          result[po] = max(poDate, oldDate)
          #print('result[po] = { max(' + str(poDate) + ', ' + str(oldDate) + ') = ' + str(result[po]))
          
  # create an inverse mapping from PO to endDate
  endDateToPO_Map = {v: k for k, v in result.items()}

  # use sorted endDate values to calculate potential date ranges for PO's
  prev = None
  for key in sorted(endDateToPO_Map.keys()):
    result[endDateToPO_Map[key]] = { 'startDate': prev , 'endDate': key }
    prev = key
  result[endDateToPO_Map[prev]] = { 'startDate': result[endDateToPO_Map[prev]]['startDate'] , 'endDate': None }
  #print('computePO_DateRanges, FINAL RESULT: ' + str(result))     
  return result
  
  
def dateRangeContains(fromDate, startDate, endDate):
  if (((startDate == None) or (fromDate > startDate)) and
      ((endDate == None) or (fromDate <= endDate))):
    return True
  else:
    return False

def mapFromDataItemToPO(dataItem, PO_DateRanges):
  for po in PO_DateRanges:
    currentItem = PO_DateRanges[po]
    #print("currentItem: " + str(currentItem))
    startDate = currentItem['startDate']
    #print("startDate: " + str(startDate))
    endDate = currentItem['endDate']
    #print("endDate: " + str(endDate))
    fromDate = calculateTimeInfo(valueOf(dataItem, DataKey.FROM_DATE), valueOf(dataItem, DataKey.FROM_TIME))
    #print("fromDate: " + str(fromDate))
    if dateRangeContains(fromDate, startDate, endDate):
      return po
  print('Should not get here')
  return None
  
def mapAllFromDataToPO(initialFromData, PO_DateRanges):
  result = {}
  for dataItem in initialFromData:
    po = mapFromDataItemToPO(dataItem, PO_DateRanges)
    if (po in result):
      result[po].append(dataItem)
      #print("APPENDING TO PO: " + po)
    else:
      result[po] = [dataItem]
      #print("CREATING TO GROUP: " + str(po))
  return result



if __name__ == "__main__":
  # process command line args  
  parser = argparse.ArgumentParser()
  parser.add_argument("-i", "--inputFile", dest='inputFName', help="input file name")
  parser.add_argument("-f", "--fromInputFile", dest='fromInputFName', help="input file name (from)")
  parser.add_argument("-t", "--toInputFile", dest='toInputFName', help="input file name (to)")
  parser.add_argument("-p", "--productFile", dest='productFName', help="product file name")
  parser.add_argument("-l", "--locationFile", dest='locationFName', help="location file name")
  parser.add_argument("-o", "--outputFile", dest='outputFName', help="output file name")
  parser.add_argument("-m", "--templateFile", dest='templateFName', help="template file name")

  parser.add_argument('--set', action='append', dest='defaultOverrides', 
                      help="override a default value for an item in an input file. Format is var=val")
  parser.add_argument('--col', action='append', dest='columnLabels', 
                      help="override a default column labels for an item in an input file. Format is labelname=val")
  options = parser.parse_args()

  if not options.inputFName and not options.fromInputFName and not options.toInputFName:
    print('ERROR: either --inputFile or both --fromInputFile and --toInputFile must be specified')
    exit()
    
  if options.inputFName and (options.fromInputFName or options.toInputFName):
    print('ERROR: only --inputFile or both --fromInputFile and --toInputFile can be specified')
    exit()
    
  if (options.fromInputFName and not options.toInputFName) or (not options.fromInputFName and options.toInputFName):
    print('ERROR: either --inputFile or both --fromInputFile and --toInputFile can be specified')
    exit()
    
  # load config
  with open('config.json', 'r') as f:
    config = json.load(f)
  g_columnLabels  = config['ColumnLabels']
  g_defaultValues = config['DefaultValues']
  
  # override config settings using command line args, as specified
  print('COLUMN LABEL OVERRIDES: ' + json.dumps(options.columnLabels, sort_keys=True, indent=2))

  process_default_overrides(options.columnLabels, g_columnLabels)
  process_default_overrides(options.defaultOverrides, g_defaultValues)
  
  print('COLUMN LABELS: ' + json.dumps(g_columnLabels, indent=2))
  print('DEFAULT VALUES: ' + json.dumps(g_defaultValues, sort_keys=True, indent=2))
  
  template = get_template(options.templateFName)
  products = load_keyed_data(options.productFName, DataKey.MATERIAL.value)
  locations = load_keyed_data(options.locationFName, DataKey.LOCATION.value)

  # load data for non-transformation events, if necessary
  data = load_event_data(options.inputFName) if options.inputFName else None
  
  # load data for transformation events, if necessary
  # FOR NOW: assume linkage by PO Number and group by date/PO number
  initialFromData = load_event_data(options.fromInputFName) if options.fromInputFName else None
  toData   = load_grouped_data(options.toInputFName, g_columnLabels.get(DataKey.PURCHASE_ORDER.value, None), GroupingFunction.EQUALITY) if options.toInputFName else None  
  fromData = None
  if toData and initialFromData:
    PO_DateRanges = computePO_DateRanges(toData)
    fromData = mapAllFromDataToPO(initialFromData, PO_DateRanges)
    print('FROM DATA:' + str(fromData))

  #print('LOCATIONS')
  #for row in locations:
  #  print(row)
  #
  #print('PRODUCTS')
  #for row in products:
  #  print(row)
  #  
  #print('DATA')
  #for row in data:
  #  print(row)
  #
  #print('PRODUCTS: ' + str(products))
  
  # render output file, based on inputs
  # if not transformation event
  if data:
    render_data(compute_contexts(data, products, locations), template, options.outputFName)
  # else if transformation event
  else:
    render_data(compute_contexts_from_to(fromData, toData, products, locations, True), template, options.outputFName)
