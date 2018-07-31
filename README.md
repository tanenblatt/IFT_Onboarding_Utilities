# Overview
Use data from input CSV file(s) to fill XML EPCIS event template. _Uses [JINJA2](http://jinja.pocoo.org)_ as the template language.

## Usage
```
usage: generate_events_xml.py [-h] [-i INPUTFNAME] [-p PRODUCTFNAME]
                              [-l LOCATIONFNAME] [-o OUTPUTFNAME]
                              [-t TEMPLATEFNAME] [--set DEFAULTOVERRIDES]
                              [--col COLUMNLABELS]

optional arguments:
  -h, --help            show this help message and exit
  -i INPUTFNAME, --inputFile INPUTFNAME
                        input file name
  -f FROMINPUTFNAME, --fromInputFile FROMINPUTFNAME
                        input file name (from)
  -t TOINPUTFNAME, --toInputFile TOINPUTFNAME
                        input file name (to)
  -p PRODUCTFNAME, --productFile PRODUCTFNAME
                        product file name
  -l LOCATIONFNAME, --locationFile LOCATIONFNAME
                        location file name
  -o OUTPUTFNAME, --outputFile OUTPUTFNAME
                        output file name
  -m TEMPLATEFNAME, --templateFile TEMPLATEFNAME
                        template file name
  --set DEFAULTOVERRIDES
                        override a default value for an item in an input file.
                        Format is var=val
  --col COLUMNLABELS    override a default column labels for an item in an
                        input file. Format is labelname=val
```
                        
_Note: while the `--set` and `--col` options are useful, there should be something like `--config` option to load a configuration file, rather than only being able to override each item individually on the command line._

If processing Transformation events, two input files are needed (_from_ and _to_), otherwise a single input file is required. Each row of an input file contains a material (product) key, as well as date/time, location key, quantity, and batch (lot) info. The product key is used to look up product information in the _Product File_ and the location key is used to look up location information in the _Location File_.

The _Product File_ should contain three columns: _Material Key_, _GTIN_, and _Description_. This data is loaded into the _product dictionary_.

The _Location File_ should contain a _Location Key_, _Name_, _GLN_, and columns containing address information. This data is loaded into the _location dictionary_.

## Processing
After processing command line arguments, column name and default value overrides are set, the output file template is loaded, the product and location files are loaded, then the input data file(s) are loaded. For transformations, data is segmented such that each segment can be treated as one transaction. For each event, its _Context_ is computed. Finally, an output XML file is rendered using the input data and the specified template.

### Data Segmentation for transformations
This is implemented via the following heuristic: 
```For each PO, compute potential date range 
  (first PO: beginning of time → date of final transformation for that PO, 
   subsequent PO's:after previous PO → date of final transformation for that PO)
```

## Context Computation

### Default Values
If an expected data item is not set, its default value is used, if any. Default values are set for a column via the `--set` command line option. 

### Date/Time Formats
Dates are expected in typical US format (month/day/year), and times can _either_ be 12-hour, with AM or PM specified, otherwise 24-hour. It is expected that dates will be specified in one column of an input file, and times in a separate column.

### GTIN and GLN Handling
GS1 `urn:` format is used in the XML files where GS1 identifiers are expected. Currently, the computation of these is simplistic. 

__For LGTIN:__ look up product by specified key, returning either GS1 LGTIN or IFT LGTIN The key is used as a key into the _product dictionary_ to find a GTIN. If a GTIN is found, then a LGTIN URN is returned (or created based on the GTIN). Otherwise, an IFT LGTIN is returned.

__For SGLN:__ look up location by specified key, returning either GS1 SGLN or IFT SGLN The key is used as a key into the _location dictionary_ to find a GLN. If a GLN is found, then a SGLN URN is returned (or created based on the GLN). Otherwise, an IFT SGLN is returned.

### Product/Quantity Processing
Templates expect items to be listed either grouped with quantity information, if any, or separately without quantity information. Therefore, every item is added to a 'quantified' or 'unquantified' list—but not both—and is then rendered in the appropriate location in the template.

## Default Values and Column Labels
The event templates are filled using values associated with the following variable names:

* `CompanyPrefix`
* `LocationReference`
* `FromLocationReference`
* `ToLocationReference`
* `Material`
* `FromMaterial`
* `ToMaterial`
* `Location`
* `FromLocation`
* `ToLocation`
* `LocationExtension`
* `FromLocationExtension`
* `ToLocationExtension`
* `Lot`
* `FromLot`
* `ToLot`
* `Quantity`
* `FromQuantity`
* `ToQuantity`
* `QuantityUOM`
* `FromQuantityUOM`
* `ToQuantityUOM`
* `Date`
* `FromDate`
* `ToDate`
* `Time`
* `FromTime`
* `ToTime`
* `TimeZone`
* `FromTimeZone`
* `ToTimeZone`
* `ExpirationDate`
* `SellByDate`
* `BestBeforeDate`
* `ReadPoint`
* `Disposition`
* `BizStep`
* `PurchaseOrder`
* `DespatchAdvice`
* `ProductionOrder`
* `SSCC`
* `Shipper`

By using the `--set` option, any (or all) of these can be can set a default value to be used in the case where a value is missing from the input.

The column labels in input files for each of the variable names are associated with the following default column names, which can be overridden using the `--col` command line option:

* `CompanyPrefix`: "Company Prefix"
* `LocationReference:` "Location Reference"
* `FromLocationReference`: "From Location Reference"
* `ToLocationReference`: "To Location Reference"
* `Material`: "Material"
* `FromMaterial`: "From Material"
* `ToMaterial`: "To Material"
* `LocationExtension`: "Location Extension"
* `FromLocationExtension`: "From Location Extension"
* `ToLocationExtension`: "To Location Extension"
* `Location`: "Plant"
* `FromLocation`: "From Plant"
* `ToLocation`: "To Plant"
* `Lot`: "Lot"
* `FromLot`: "From Lot"
* `ToLot`: "To Lot"
* `Quantity`: "Quantity"
* `FromQuantity`: "From Quantity"
* `ToQuantity`: "To Quantity"
* `QuantityUOM`: "Unit"
* `FromQuantityUOM`: "From Unit"
* `ToQuantityUOM`: "To Unit"
* `Date`: "Date"
* `FromDate`: "From Date"
* `ToDate`: "To Date"
* `Time`: "Time"
* `FromTime`: "FromTime"
* `ToTime`: "To Time"
* `TimeZone`: "Time Zone"
* `FromTimeZone`: "From Time Zone"
* `ToTimeZone`: "To Time Zone"
* `ExpirationDate`: "Expiration Date"
* `SellByDate`: "Sell By Date"
* `BestBeforeDate`: "Best Before Date"
* `ReadPoint`: "Read Point"
* `Disposition`: "Disposition"
* `BizStep`: "Biz Step"
* `PurchaseOrder`: "Purchase Order"
* `DespatchAdvice`: "Despatch Advice"
* `ProductionOrder`: "Production Order"
* `SSCC`: "SSCC"
* `Shipper`: "Shipper"


## Example:

```
python3 generate_events_xml.py  --inputFile ../Data/Movement_from_Manufacturing_to_Distribution.csv \
                                --productFile ../Data/Products.csv \
                                --locationFile ../Data/Locations.csv \
                                --templateFile Templates/TEMPLATE_aggregation.xml \
                                --outputFile /tmp/events_step1.xml \
                                --set BizStep=urn:epcglobal:cbv:bizstep:packing \
                                --set Disposition=urn:epcglobal:cbv:disp:in_progress \
                                --set CompanyPrefix=1234567 \
                                --col Location='Site' \
                                --col PurchaseOrder='PO#' \
                                --col Lot='Batch' \
                                --col ToLocation='To Location'```

