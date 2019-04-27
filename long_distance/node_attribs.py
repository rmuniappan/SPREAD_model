###########################################################################
# Compute node attributes for gravity model
###########################################################################
import sqlite3
import pdb
import argparse
import csv
import logging

DB="../../data_and_obj.db"
DESC="""Compute node attributes inflow and outflow from production,
consumption, imports, exports, consumption and population."""
NODE_ATTRIB_FILE="../obj/node_attributes.csv"

def consumption(nodeAttribs):
   # AA: needs change
   for loc in nodeAttribs:
      nodeAttribs[loc]['inflow']=nodeAttribs[loc]['pop']*nodeAttribs[loc]['consumption']
      #nodeAttribs[loc]['inflow']=nodeAttribs[loc]['consumption']
   return

def bangladeshOutflow(nodeAttribs,locsProcessed):
   for loc in nodeAttribs:
      if nodeAttribs[loc]['country']=='BGD':
         locsProcessed.append(loc)
         for m in xrange(6,12):
            nodeAttribs[loc]['outflow'][m]+=nodeAttribs[loc]['import']/6.0
   return

def defaultOutflow(nodeAttribs,locsProcessed):
   # do nothing for now
   # AA: needs change
   remainingCells=set(nodeAttribs.keys()).difference(set(locsProcessed))
   for loc in nodeAttribs:
      #nodeAttribs[loc]['outflow']+=nodeAttribs[loc]['pop']*nodeAttribs[loc]['consumption']
      for m in range(12):
         nodeAttribs[loc]['outflow'][m] = (nodeAttribs[loc]['import'] - nodeAttribs[loc]['export'])/12.0 + (1-nodeAttribs[loc]['processing'])*nodeAttribs[loc]['outflow'][m]
   return

if __name__ == "__main__":
   parser = argparse.ArgumentParser(
      formatter_class=argparse.RawTextHelpFormatter,
      description=DESC)

   parser.add_argument("locality_data",help="Locality data.")
   parser.add_argument("-o","--out_node_attrib_file",\
         default="node_attributes.csv",\
         help="Output node attribute file.")
   args = parser.parse_args()

   # read locality file
   with open(args.locality_data,'r') as f:
      nodeAttribs={}
      rows=csv.reader(f)
      rows.next()
      for r in rows:
         nodeAttribs[r[1]]={'pop': float(r[2]),\
               'outflow': [float(x) for x in r[3:]]}


   # read table
   con=sqlite3.connect(DB)
   c=con.cursor()
   c.execute("SELECT * FROM localities")
   queryResult=c.fetchall()
   con.close()
   for r in queryResult:
      try:
         nodeAttribs[r[1]]['country']=r[2]
         nodeAttribs[r[1]]['consumption']=r[4]
         nodeAttribs[r[1]]['processing']=r[5]
         nodeAttribs[r[1]]['export']=r[6]
         nodeAttribs[r[1]]['import']=r[7]
      except KeyError:
         print "Skipping %s ..." %r[1]

   locsProcessed=[]
   consumption(nodeAttribs)
   bangladeshOutflow(nodeAttribs,locsProcessed)
   defaultOutflow(nodeAttribs,locsProcessed)

   with open(args.out_node_attrib_file,'w') as f:
      for loc in nodeAttribs:
         fileStr="%s,%.2f" %(loc,nodeAttribs[loc]['inflow'])
         for m in xrange(12):
            fileStr+=",%.2f" %nodeAttribs[loc]['outflow'][m]
         f.write(fileStr+","+nodeAttribs[loc]['country']+'\n')

