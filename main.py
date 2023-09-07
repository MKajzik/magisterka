import wiringpi
from wiringpi import GPIO
import time
import datetime
import spidev
import atexit
import json
import os

spi = spidev.SpiDev()
spi.open(1,0)
spi.max_speed_hz=1000000

soil_pin = 15
temp_pin = 6
delay = 10
water_pump_pin = 9

if (os.path.isfile("./humidity_temperature.json") == True):
	f = open('humidity_temperature.json')
	humi_temp = json.load(f)
	f.close()
else:
	humi_temp ={
		"humidity_max": {
			"value": 0,
			"timestamp": "" 
    	},
	    "humidity_actual": {
			"value": 0,
			"timestamp": "" 
    	},
		"humidity_min": {
			"value": 0,
			"timestamp": "" 
    	},
		"temperature_max": {
			"value": 0,
			"timestamp": "" 
    	},
	    "temperature_actual": {
			"value": 0,
			"timestamp": "" 
    	},
    	"temperature_min": {
			"value": 0,
			"timestamp": "" 
    	}
	}

if (os.path.isfile("./soil_moisture.json") == True):
	f = open('soil_moisture.json')
	soil_moisture = json.load(f)
	f.close()
else:
	soil_moisture ={
		"soil_moisture_max": {
			"value": 0,
			"timestamp": "" 
    	},
	    "soil_moisture_actual": {
			"value": 0,
			"timestamp": "" 
    	},
    	"soil_moisture_min": {
			"value": 0,
			"timestamp": "" 
    	}
	}


wiringpi.wiringPiSetup()
wiringpi.digitalWrite(16, GPIO.HIGH)
wiringpi.pinMode(soil_pin, GPIO.OUTPUT)
wiringpi.pinMode(16, GPIO.OUTPUT)
wiringpi.pinMode(water_pump_pin, GPIO.OUTPUT)

class DateTimeEncoder(json.JSONEncoder):
        #Override the default method
        def default(self, obj):
            if isinstance(obj, (datetime.date, datetime.datetime)):
                return obj.isoformat()

def ReadChannel3208(channel):
    adc = spi.xfer2([6|(channel>>2),channel<<6,0])
    data = ((adc[1]&15) << 8) + adc[2]
    return data

def ConvertToVoltage(value, bitdepth, vref):
    return vref*(value/(2**bitdepth-1))

def CleanUP():
    wiringpi.digitalWrite(16, GPIO.LOW)
    print("Cleaning application and ending checking sensors!!")

def TempGetVal(pin):
	tl=[]
	tb=[]
	wiringpi.wiringPiSetup()
	wiringpi.pinMode(pin, GPIO.OUTPUT)
	wiringpi.digitalWrite(pin, GPIO.HIGH)
	wiringpi.delay(1)
	wiringpi.digitalWrite(pin, GPIO.LOW)
	wiringpi.delay(25)
	wiringpi.digitalWrite(pin, GPIO.HIGH)
	wiringpi.delayMicroseconds(20)
	wiringpi.pinMode(pin, GPIO.INPUT)
	while(wiringpi.digitalRead(pin)==1): pass
	
	for i in range(45):
		tc=wiringpi.micros()
		'''
		'''
		while(wiringpi.digitalRead(pin)==0): pass
		while(wiringpi.digitalRead(pin)==1):
			if wiringpi.micros()-tc>500:
				break
		if wiringpi.micros()-tc>500:
			break
		tl.append(wiringpi.micros()-tc)

	tl=tl[1:]
	for i in tl:
		if i>100:
			tb.append(1)
		else:
			tb.append(0)
	
	return tb

def TempGetResult(pin):
	for i in range(10):
		SH=0;SL=0;TH=0;TL=0;C=0;flag=0
		result=TempGetVal(pin)

		if len(result)==40:
			for i in range(8):
				SH*=2;SH+=result[i]    # humi Integer
				SL*=2;SL+=result[i+8]  # humi decimal
				TH*=2;TH+=result[i+16] # temp Integer
				TL*=2;TL+=result[i+24] # temp decimal
				C*=2;C+=result[i+32]   # Checksum
			if ((SH+SL+TH+TL)%256)==C and C!=0:
				flag = 2
				break
			else:
				print("Odczyt poprawny, błąd sumy kontrolnej! Ponowny odczyt")
				flag=1
				time.sleep(1)

		else:
			print("Błąd odczytu! Ponowny odczyt")
			flag = 1
			break
		wiringpi.delay(200)
	return SH,SL,TH,TL,flag

def Humidity(pin):
	airVoltage = 2.5
	waterVoltage = 1.25
	half = (airVoltage - waterVoltage)/3

	wiringpi.digitalWrite(pin, GPIO.LOW)
	wiringpi.delay(100)
	value = ReadChannel3208(0)
	wiringpi.delay(100)
	wiringpi.digitalWrite(pin, GPIO.HIGH)
	voltage = ConvertToVoltage(value, 12, 3.3)

	if(voltage > waterVoltage and voltage < (waterVoltage + half)):
		return False
	elif(voltage < airVoltage and voltage > (airVoltage - half)):
		return True

def WaterPlant(pin):
	now = datetime.datetime.now()
	startTime = now.replace(hour=20, minute=0, second=0, microsecond=0)
	endTime = now.replace(hour=23, minute=0, second=0, microsecond=0)
	if(now > startTime and now < endTime):
		print("Starting to water plant")
		wateringStatus = Humidity(pin)
		while wateringStatus:
			wiringpi.digitalWrite(water_pump_pin, GPIO.HIGH)
			wiringpi.delay(5000) # 5 seconds
			wiringpi.digitalWrite(water_pump_pin, GPIO.LOW)
			wiringpi.delay(10000) # 1200000 = 20mins
			wateringStatus = Humidity(pin)


def PrintHumi(pin):
	airVoltage = 2.5
	waterVoltage = 1.25
	intervals = (airVoltage - waterVoltage)/3

	wiringpi.digitalWrite(pin, GPIO.LOW)
	wiringpi.delay(100)
	value = ReadChannel3208(0)
	wiringpi.delay(100)
	wiringpi.digitalWrite(pin, GPIO.HIGH)
	voltage = ConvertToVoltage(value, 12, 3.3)
	ct = datetime.datetime.now()
	print(ct,"-",f"{voltage:.3f}","V")

	if(voltage > waterVoltage and voltage < (waterVoltage + intervals)):
		print("Bardzo mokro")
	elif(voltage > (waterVoltage + intervals) and voltage < (airVoltage - intervals)):
		print("Mokro")
	elif(voltage < airVoltage and voltage > (airVoltage - intervals)):
		print("Sucho")
		WaterPlant(pin)

	soil_moisture["soil_moisture_actual"]["value"] = voltage
	soil_moisture["soil_moisture_actual"]["timestamp"] = ct

	if(soil_moisture["soil_moisture_max"]["value"] < voltage):
		soil_moisture["soil_moisture_max"]["value"] = voltage
		soil_moisture["soil_moisture_max"]["timestamp"] = ct
	
	elif(soil_moisture["soil_moisture_min"]["value"] > voltage):
		soil_moisture["soil_moisture_min"]["value"] = voltage
		soil_moisture["soil_moisture_min"]["timestamp"] = ct

	with open("soil_moisture.json", "w") as outfile:
		json.dump(soil_moisture, outfile, cls=DateTimeEncoder)

def PrintTemp(pin):
		ct = datetime.datetime.now()
		SH,SL,TH,TL,flag=TempGetResult(pin)
		print("Wilgotność:",SH,"%","Temperatura:",TH,"°C")

		humi_temp["humidity_actual"]["value"] = SH
		humi_temp["humidity_actual"]["timestamp"] = ct

		humi_temp["temperature_actual"]["value"] = TH
		humi_temp["temperature_actual"]["timestamp"] = ct
		
		if(humi_temp["humidity_max"]["value"] < SH):
			humi_temp["humidity_max"]["value"] = SH
			humi_temp["humidity_max"]["timestamp"] = ct
		
		elif(humi_temp["humidity_min"]["value"] > SH and flag == 2 or humi_temp["humidity_min"]["timestamp"] == ""):
			humi_temp["humidity_min"]["value"] = SH
			humi_temp["humidity_min"]["timestamp"] = ct

		if(humi_temp["temperature_max"]["value"] < TH):
			humi_temp["temperature_max"]["value"] = TH
			humi_temp["temperature_max"]["timestamp"] = ct
			
		elif(humi_temp["temperature_min"]["value"] > TH and flag == 2 or humi_temp["temperature_min"]["timestamp"] == ""):
			humi_temp["temperature_min"]["value"] = TH
			humi_temp["temperature_min"]["timestamp"] = ct
			
		with open("humidity_temperature.json", "w") as outfile:
			json.dump(humi_temp, outfile, cls=DateTimeEncoder)


atexit.register(CleanUP)

while(True):
    PrintHumi(soil_pin)
    PrintTemp(temp_pin)
    time.sleep(delay)

