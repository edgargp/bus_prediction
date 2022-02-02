import datetime
from google.cloud import bigquery
 
def convert(seconds):
   #convert seconds to hours
   min, sec = divmod(seconds, 60)
   hour, min = divmod(min, 60)
   hour = hour + 9
   return "%d:%02d:%02d" % (hour, min, sec)
 
def query_lastbus(request):
   #query BigQuery to get the latest bus arrival time
   client = bigquery.Client()
   query = """    
       SELECT MAX(time) FROM  `tableName` WHERE  date=(SELECT MAX(date) FROM `tableName`)
   """
   query_job = client.query(query)  # Make an API request.
 
   for row in query_job:
       result = "{}".format(row[0])
   result = int(result)
  
   return convert(result)