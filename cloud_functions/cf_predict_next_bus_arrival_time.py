from google.cloud import bigquery
from typing import Dict
from google.cloud import aiplatform
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value
 
def next_bus(request):
   #query latest bus_label
   client = bigquery.Client()
   query = """
       SELECT bus_number FROM  `tableName` WHERE date=(SELECT MAX(date) FROM `tableName`) AND time=(SELECT MAX(time) FROM  `tableName` WHERE date=(SELECT MAX(date) FROM `tableName`) )
   """
   query_job = client.query(query)  # Make an API request.
   print("preparing for query")
   for row in query_job:
       # Row values can be accessed by field name or index.
       result = "{}".format(row[0])
   print("result",result)
   bus_seq_number=digitize(result)
   reply = prediction(bus_seq_number)
   return reply
 
 
def convert(seconds):
   #convert seconds to hours
   min, sec = divmod(seconds, 60)
   hour, min = divmod(min, 60)
   hour = hour + 9
   return "%d:%02d:%02d" % (hour, min, sec)
 
def digitize(string):
   #return next bus_label
   num=""
   for c in string:
       if c.isdigit():
           num = num + c
   bus_digit =  int(num) + 1
   next_bus_digit = "bus_" + str(bus_digit)
   return str(next_bus_digit)
 
def prediction(bus_seq_number):
   #api request to deployed VertexAI model
   instances={ "bus_number": bus_seq_number}
   project="project_nubmer"
   endpoint_id="endpoint_id"
   location="region"
   api_endpoint="region_endpoint"
   instance_dict=instances
 
   # The AI Platform services require regional API endpoints.
   client_options = {"api_endpoint": api_endpoint}
   # Initialize client that will be used to create and send requests.
   # This client only needs to be created once, and can be reused for multiple requests.
   client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)
   # for more info on the instance schema, please use get_model_sample.py
   # and look at the yaml found in instance_schema_uri
   instance = json_format.ParseDict(instance_dict, Value())
   instances = [instance]
   parameters_dict = {}
   parameters = json_format.ParseDict(parameters_dict, Value())
   endpoint = client.endpoint_path(
       project=project, location=location, endpoint=endpoint_id
   )
   response = client.predict(
       endpoint=endpoint, instances=instances, parameters=parameters
   )
 
   predictions = response.predictions
   for prediction in predictions:
       response_dict = dict(prediction)
   #I skipped upper_bound and lower_bound values and currently Alexa only outputs the value
   return ",".join([convert(response_dict["value"]), convert(response_dict["upper_bound"]), convert(response_dict["lower_bound"])])
