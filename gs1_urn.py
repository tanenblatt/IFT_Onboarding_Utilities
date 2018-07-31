### Really simplistic utilities for handling GTIN/GLN/SSCC/etc.
###
### TODO: check for string lengths and pad as necessary, other error checking, so much more...

# utilities
def already_urn(code: str):
  return code and code.startswith('urn')
    
def add_urn_suffix_if_necessary(code: str, suffix: str):
  if suffix and (2 > code.count('.')):
    return '{0}.{1}'.format(code, suffix) 
  else:
    return code


# CLASS-LEVEL objects, e.g.: LGTIN (GTIN+lot)
#
# LGTINs should be constructed to be as unique as possible; by concatenating time/date of creation with object id, e.g.
# General LGTIN syntax: 
#   urn:epc:class:lgtin:<CompanyPrefix>.<ItemRefAndIndicator>.<Lot>
# where:
# • CompanyPrefix.ItemRefAndIndicator ahould have 13 digits (without counting dots).
# • CompanyPrefix is equal to the CompanyPrefix derived from GTIN.
# • ItemRefAndIndicator is formed by concatenating the first digit (Indicator) from GTIN with ItemRef digits from GTIN.
# • GTIN check digit is dropped.
# If a GTIN (without lot) is to be represented, the following syntax is used:
# From Page 35 of https://www.gs1.org/sites/default/files/docs/epc/CBV-Standard-1-2-1-r-2017-05-05.pdf:
#   urn:epc:idpat:sgtin:<CompanyPrefix>.<ItemRefAndIndicator>.* where 
# • CompanyPrefix.ItemRefAndIndicator is 13 digits as above.
#
# IFT IDs
# IFT Product with Lot #: urn:ibm:ift:product:lot:class:<Company Prefix>.<Item Reference>.<Lot Number>
# IFT Product without Lot/Serial: urn:ibm:ift:product:class:<Company Prefix>.<Item Reference>

#def lgtin_data_to_urn(company_prefix, indicator, item_ref, lot: str):
#  '''
#  :param company_prefix: The company prefix (GS1).
#  :param indicator: The GS1 indicator digit for the GTIN
#  :param item_ref: The item reference number for the GTIN
#  :param lot: lot number.
#  :return: Generates an LGTIN URN string
#  '''
#  return 'urn:epc:class:lgtin:{0}.{1}{2}.{3}'.format(company_prefix, indicator, item_ref, lot)
  
def lgtin_data_to_urn(company_prefix, indicator_and_item_ref, lot: str):
  '''
  :param company_prefix: The company prefix (GS1).
  :param indicator_and_item_ref: The GS1 indicator digit for the GTIN concatenated with the item reference number, or a urn
  :param lot: lot number.
  :return: Generates an LGTIN URN string, if necessary
  '''
  if already_urn(indicator_and_item_ref):
    return add_urn_suffix_if_necessary(indicator_and_item_ref, lot)
  return 'urn:epc:class:lgtin:{0}.{1}.{2}'.format(company_prefix, indicator_and_item_ref, lot)

def ift_lgtin_data_to_urn(company_prefix: str, item_ref: str, lot: str = None):
  '''
  :param company_prefix: The company prefix (GS1).
  :param item_ref: The item reference number for the GTIN or URN
  :param lot: lot number (optional)
  :return: Generates an IFT LGTIN URN string, if necessary
  '''
  if already_urn(item_ref):
    return add_urn_suffix_if_necessary(item_ref, lot)

  if (lot):
    return 'urn:ibm:ift:product:lot:class:{0}.{1}.{2}'.format(company_prefix, item_ref, lot)
  else:
    return 'urn:ibm:ift:product:lot:class:{0}.{1}'.format(company_prefix, item_ref)
  



# INSTANCE-LEVEL OBJECTS, e.g.: SSCC, SGTIN
#
# General SGTIN syntax: urn:epc:id:sgtin:<CompanyPrefix>.<ItemRefAndIndicator>.<SerialNumber>
# • CompanyPrefix.ItemRefAndIndicator ahould have 13 digits (without counting dots).
# • CompanyPrefix is equal to the CompanyPrefix derived from GTIN-14.
# • ItemRefAndIndicator is formed by concatenating the first digit (Indicator) from GTIN-14 with ItemRef digits from GTIN-14.
# • GTIN-14 check digit is dropped.
# • GTIN-12 or GTIN-13 should first be converted to GTIN-14 by adding leading 0s before above conversion.
#
# General EPC SSCC syntax: urn:epc:id:sscc:<CompanyPrefix>.<SerialRefAndExtension>
# • EPC SSCC is 17 digits
# • CompanyPrefix is equal to the CompanyPrefix in GS1 SSCC
# • SerialReferenceAndExtension is formed by concatenating the first digit (Extension) from GS1 SSCC with SerialRef digits from GS1 SSCC.
# • GS1 SSCC check digit is dropped.
#
# IFT IDs
# IFT Product with Serial #: urn:ibm:ift:product:serial:obj:<Company Prefix>.<Item Reference>.<Serial Number>
# IFT Logistic Unit: urn:ibm:ift:lpn:obj:<Company Prefix>.<Serial Reference>


#def sgtin_data_to_urn(company_prefix, indicator, item_ref, serial_number: str):
#  '''
#  :param company_prefix: The company prefix (GS1).
#  :param indicator: The GS1 indicator digit for the GTIN
#  :param item_reference: The item reference number for the GTIN
#  :param serial_number: A serial number.
#  :return: Generates an SGTIN URN string
#  '''
#  return 'urn:epc:id:sgtin:{0}.{1}{2}.{3}'.format(company_prefix, indicator, item_ref, serial_number)

def sgtin_data_to_urn(company_prefix, indicator_and_item_ref, serial_number: str):
  '''
  :param company_prefix: The company prefix (GS1).
  :param indicator_and_item_ref: The GS1 indicator digit for the GTIN concatenated with the item reference number, or a urn
  :param serial_number: A serial number.
  :return: Generates an SGTIN URN string, if necessary
  '''
  if already_urn(indicator_and_item_ref):
    return add_urn_suffix_if_necessary(indicator_and_item_ref, serial_number)
  return 'urn:epc:id:sgtin:{0}.{1}.{2}'.format(company_prefix, indicator_and_item_ref, serial_number)

def ift_sgtin_data_to_urn(company_prefix, item_ref, serial_number: str):
  '''
  :param company_prefix: The company prefix (GS1).
  :param item_reference: The item reference number for the GTIN or URN
  :param serial_number: A serial number.
  :return: Generates an IFT product URN string, if necessary

  Convert params to IFT Product with Serial Number
  IFT Product with Serial #: urn:ibm:ift:product:serial:obj:<Company Prefix>.<Item Reference>.<Serial Number>
  '''
  if already_urn(item_ref):
    return add_urn_suffix_if_necessary(item_ref, serial_number)
  return 'urn:ibm:ift:product:serial:obj:{0}.{1}.{2}'.format(company_prefix, item_ref, serial_number)
  
def sscc_data_to_urn(company_prefix, serial_number: str):
  '''
  :param company_prefix: The company prefix (GS1).
  :param serial_number: A serial number or urn
  :return: Generates an SSCC URN string, if necessary
  '''
  if already_urn(serial_number):
    return serial_number
  return 'urn:epc:id:sscc:{0}.{1}'.format(company_prefix, serial_number)

def ift_logistic_unit_data_to_urn(company_prefix, serial_number: str):
  '''
  :param company_prefix: The company prefix (GS1).
  :param serial_number: A serial number or URN
  :return: Generates an IFT Logistical Unit URN string, if necessary

  Convert params to IFT Logistic Unit
  IFT Logistic Unit: urn:ibm:ift:lpn:obj:<Company Prefix>.<Serial Reference>
  '''
  if already_urn(serial_number):
    return serial_number
  return 'urn:ibm:ift:lpn:obj:{0}.{1}'.format(company_prefix, serial_number)



# LOCATION
#
#
def sgln_data_to_urn(company_prefix: str, loc_ref: str, extension: str = None):
  '''
  :param company_prefix: The company prefix (GS1).
  :param loc_ref: The item reference number for the GTIN or URN
  :param extension: optional extension.
  :return: Generates GLN URN string, if necessary

  Convert params to GLN
  urn:epc:id:sgln:<CompanyPrefix>.<LocationReference>.<Extension>
  '''
  if already_urn(loc_ref):
    return add_urn_suffix_if_necessary(loc_ref, extension)
    
  if company_prefix and loc_ref:
    if (extension):
      return 'urn:epc:id:sgln:{0}.{1}.{2}'.format(company_prefix, loc_ref, extension)
    else:
      return 'urn:epc:id:sgln:{0}.{1}'.format(company_prefix, loc_ref)
  else:
    return None

    
def ift_sgln_data_to_urn(company_prefix: str, loc_ref: str, extension: str = None):
  '''
  :param company_prefix: The company prefix (GS1).
  :param loc_ref: The item reference number for the GTIN or URN
  :param extension: optional extension.
  :return: Generates GLN URN string, if necessary

  Convert params to GLN
  urn:ibm:ift:location:extension:loc:<CompanyPrefix>.<LocationReference>.<Extension>
  '''
  if already_urn(loc_ref):
    return add_urn_suffix_if_necessary(loc_ref, extension)

  if company_prefix and loc_ref:
    if (extension):
      return 'urn:ibm:ift:location:extension:loc:{0}.{1}.{2}'.format(company_prefix, loc_ref, extension)
    else:
      return 'urn:ibm:ift:location:extension:loc:{0}.{1}'.format(company_prefix, loc_ref)
  else:
    return None
    

# Purchase Order
def purchase_order_data_to_urn(company_prefix: str, po: str):
  return 'urn:epcglobal:cbv:bt:{0}:{1}'.format(company_prefix, po)
  

# Despatch Advice
def despatch_advice_data_to_urn(company_prefix: str, po: str, da: str):
  return 'urn:epcglobal:cbv:bt:{0}:{1}-{2}'.format(company_prefix, po, da)
  

# Production Order
def production_order_data_to_urn(company_prefix: str, prod: str):
  return 'urn:epcglobal:cbv:bt:{0}:{1}'.format(company_prefix, prod)