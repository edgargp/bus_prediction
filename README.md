# bus_prediction
predict bus arrival time using VertexAI and Nvidia's Jetson Nano
![Infra architecture](architecture_diagram.png)




imagenet
the command for imagenet.py look like this

`python3 /path/to/imagenet.py  --model=/path/to/resnet18.onnx --labels=/path/to/labels.txt  --input_blob=input_0 --output_blob=output_0 rtsp://exceptional_user:super_strong_pass@192.168.1.1`

you also can use imagenet with docker and with different protocols check the repo(https://github.com/dusty-nv/jetson-inference) for more information



iot_http 
the code here uses private key to generate JWT token to access Google IoT Core and publish message to Pub/Sub, this file is invoked by imagnet.py iot_message funciton but it also can be publish messages with command

`python3 iot_http.py --message bus_2,2022-02-02,24578`

