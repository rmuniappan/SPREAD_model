###########################################################################
# Reads a file and converts every occurence from specified input format to
# specified output format.
# tags: unicode encode pycountry iso alpha isNumber string2Number
# stringToNumber
###########################################################################

import pycountry as pc
import argparse
import pdb
import logging
import unicodedata

unresolvedSwitch=0

DESC="""Convert between country names and codes.
---------------------------------------------------------------------------
Version history:
2018-03-05: 
   - added more names to dictionary
   - changed alpha3 (2) to alpha_3 (2)
   - added isNumber functionality
"""
EPI="""Will use ZZZ or ZZ for those which cannot be resolved."""

ALTERNATE_NAMES = {"Taiwan": "Taiwan, Province of China",
              "Czech Republic": "Czechia",
              "Guinea Bissau": "Guinea-Bissau",
              "Dem. People's Republic of Korea":"Korea, Democratic People's Republic of",
              "China, Taiwan Province of": "Taiwan, Province of China",
              "China Taiwan Province of": "Taiwan, Province of China",
              "China mainland": "China",
              "China Hong Kong": "Hong Kong",
              "China Hong Kong SAR": "Hong Kong",
              "China Macao SAR": "Macao",
              "Cte dIvoire": "Ivory Coast",
              "USA": "United States",
              "United States of America": "United States",
              "China, mainland":"China",
              "Burma":"Myanmar",
              "Republic of Malta":"Malta",
              "Kosovo":"Serbia",
              "Russia":"Russian Federation",
              "Ghambia":"Gambia",
              "China, Hong Kong SAR": "Hong Kong",
              "Hong Kong SAR": "Hong Kong",
              "Cabo Verde": "Cape Verde",
              "Netherlands Antilles (former)":"Netherlands",
              "The former Yugoslav Republic of Macedonia":"Macedonia, Republic of",
              "Republic of Moldova": "Moldova, Republic of",
             "China, Macao SAR":"Macao",
             "South Korea":"Korea, Republic of",
             "Korea South":"Korea, Republic of",
             "Republic of Korea":"Korea, Republic of",
             "North Korea":"Korea, Democratic People's Republic of",
             "Korea North":"Korea, Democratic People's Republic of",
             "Democratic People's Republic of Korea":"Korea, Democratic People's Republic of",
             "Democratic Peoples Republic of Korea":"Korea, Democratic People's Republic of",
             "Saint Martin (French part)": "Saint Martin",
             "Saint Helena Ascension and Tristan da Cunha": "Saint Helena, Ascension and Tristan da Cunha",
             "Democratic Republic of the Congo":"Congo, The Democratic Republic of the",
             "Micronesia (Federated States of)":"Micronesia, Federated States of",
             "Micronesia Federated States of":"Micronesia, Federated States of",
             "Sudan (former)":"Sudan",
             "Tanzania":"Tanzania, United Republic of",
             "United Republic of Tanzania":"Tanzania, United Republic of",
             "Wallis and Futuna Islands":"Wallis and Futuna",
             "Iran (Islamic Republic of)":"Iran, Islamic Republic of",
             "Iran":"Iran, Islamic Republic of",
             "Venezuela":"Venezuela, Bolivarian Republic of",
             "Venezuela (Bolivarian Republic of)":"Venezuela, Bolivarian Republic of",
             "Vietnam":"Viet Nam",
             "Syria":"Syrian Arab Republic",
             "Yugoslavia":"Serbia",
             "Antigua & Barbuda":"Antigua and Barbuda",
             "Brunei":"Brunei Darussalam",
             "East Timor":"Timor-Leste",
             "Laos":"Lao People's Democratic Republic",
             "Lao Peoples Democratic Republic":"Lao People's Democratic Republic",
             "Macedonia":"Macedonia, Republic of",
             "Moldova":"Moldova, Republic of",
             "St. Kitts and Nevis":"Saint Kitts and Nevis",
             "St. Lucia":"Saint Lucia",
             "St. Vincent and the Grenadines":"Saint Vincent and the Grenadines",
             "British Virgin Islands":"Virgin Islands, British",
             "Occupied Palestinian Territory":"Palestine, State of",
             "Bolivia":"Bolivia, Plurinational State of",
             "Bolivia (Plurinational State of)":"Bolivia, Plurinational State of"}

UNRESOLVED_NAMES=["Ivory Coast", "Cte dIvoire"]

def isNumber(s):
   try:
      float(s)
      return True
   except ValueError:
      pass

   try:
      unicodedata.numeric(s)
      return True
   except (TypeError, ValueError):
      pass
   return False

def alpha3_to_alpha2(string,ignoreUnresolved):
   if isNumber(string):
      return string
   try:
      return pc.countries.get(alpha_3=string).alpha_2
   except:
      global unresolvedSwitch
      unresolvedSwitch=1
      if ignoreUnresolved:
         return string
      else:
         return "ZZ" #Unspecified

def name_to_alpha3(string,ignoreUnresolved):
   if isNumber(string):
      return string
   try:
      return pc.countries.get(name=string).alpha_3
   except:
      try:
         return pc.countries.get(name=ALTERNATE_NAMES[string]).alpha_3
      except:
         if string in UNRESOLVED_NAMES: 
            return "CIV"
         if not ignoreUnresolved:
            logging.warning('Unresolved: %s' %string)
         global unresolvedSwitch
         unresolvedSwitch=1
         if ignoreUnresolved:
            return string
         else:
            return "ZZZ" #Unspecified

def name_to_alpha2(string,ignoreUnresolved):
   if isNumber(string):
      return string
   try:
      return pc.countries.get(name=string).alpha_2
   except:
      try:
         return pc.countries.get(name=UNRESOLVED_NAMES[string]).alpha_2
      except:
         if string=="Ivory Coast": 
            return "CI"
         if not ignoreUnresolved:
            logging.warning('Unresolved: %s' %string)
         global unresolvedSwitch
         unresolvedSwitch=1
         if ignoreUnresolved:
            return string
         else:
            return "ZZ" #Unspecified

def main():
   parser = argparse.ArgumentParser(
      formatter_class=argparse.RawTextHelpFormatter,
      description=DESC,epilog=EPI)

   parser.add_argument("input_file",help="the input file that needs to be converted")
   parser.add_argument("-f","--from_format",default="name",action="store",help="format \
         of input file (currently supports only \'name\' and \'alpha3\')")
   parser.add_argument("-t","--to_format",default="alpha3",action="store",help="format \
         of output file (currently supports alpha2/alpha3)")
   parser.add_argument("-D","--dump_country_names",action="store_true",help="dumps all country names. Useful for debugging. Ignores input file.")
   parser.add_argument("-d","--delimiter",default=",",action="store",help="the delimiter which separates each element")
   parser.add_argument("-i","--ignore_unresolved",action="store_true",help="If true, suppresses warnings and prints unresolved strings as it is. Else, every unresolved string will be replaced by ZZZ.")

   # extract parameters
   args = parser.parse_args()

   # resolve -D parameter
   if args.dump_country_names:
      for cntry in pc.countries:
         print cntry.name.encode('ascii','ignore')
      return

   with open(args.input_file) as f:
      lines=f.readlines()

   for line in lines:
      outLine='';
      for name in line.rstrip('\n').split(args.delimiter):
         asciiName=name
         if args.from_format=='name' and args.to_format=='alpha3':
            outLine+=name_to_alpha3(asciiName,args.ignore_unresolved)+','
         elif args.from_format=='name' and args.to_format=='alpha2':
            outLine+=name_to_alpha2(asciiName,args.ignore_unresolved)+','
         elif args.from_format=='alpha3' and args.to_format=='alpha2':
            outLine+=alpha3_to_alpha2(asciiName,args.ignore_unresolved)+','
         else:
            logging.error('Unsupported format %s.' %args.to_format)
            exit(1)
      print(outLine.rstrip(','))

   if unresolvedSwitch:
      logging.warning("There were unresolved country names.")
         
if __name__ == "__main__":
   main()
