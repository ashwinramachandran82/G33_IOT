Readme File
#############

1) Python file executed on raspberry pi - send_receive_gas_sensor_data.py
		
	To read oxygen levels from the sensor and send the values to AWS IOT platform. The script also receives actuation
	commands to turn on the buzzer if the oxygen levels fall below 400

2) DynamoDB Database - g33_sensor_data
	The rule triggers the database g33_sensor_data to be populated with the contents of the MQTT message from the 	sensor

3) AWS IOT Rules
	a) g33_record_sensor_data
		To update the DynamoDB database g33_sensor_data with the sensor values and Send the data to elastic search
		using a Lambda function "SenddatatoElasticSearch_g33"
	b) g33_send_alert1
		To send SMS alert to a local number using a Lambda function "SendSMS"
	c) g33_send_buzzer_new
		To actuate the buzzer using the Lambda function "setdesiredtstateforbuzzer" through REST API
 
4) Kibana Dashboard can be seen from the following link.
		
		http://search-iot-74g6su3n4aupthnnhffmvewv2a.us-west-2.es.amazonaws.com/_plugin/kibana/#/discover
		
		Please open g33_dashboard


