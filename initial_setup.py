import logging
# Importing models and REST client class from Community Edition version
from tb_rest_client.rest_client_ce import *
# Importing the API exception
from tb_rest_client.rest import ApiException

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(module)s - %(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# ThingsBoard REST API URL
url = "http://192.168.0.115:8080"
# Default Tenant Administrator credentials
username = "tenant@thingsboard.org"
password = "tenant"

# Creating the REST client object with context manager to get auto token refresh
with RestClientCE(base_url=url) as rest_client:
    try:
        # Auth with credentials
        rest_client.login(username=username, password=password)

        # Setter
        # Creating Setter Asset
        asset = Asset(name="Pincubator", type="Incubator")
        asset = rest_client.save_asset(asset)

        logging.info("Asset was created:\n%r\n", asset)

        # creating a Device
        device = Device(name="Setter", type="Multiple")
        device = rest_client.save_device(device)
        logging.info(" Device was created:\n%r\n", device)
        # Creating relations from device to asset
        relation = EntityRelation(_from=asset.id, to=device.id, type="Contains")
        relation = rest_client.save_relation(relation)
        logging.info(" Relation was created:\n%r\n", relation)
        settings = '{"Alarm": 0, "SetterMode": 3.0, "SetterMinWindow": 500.0, "SetterMaxWindow": 5000.0, "SetterKp": 1500, "SetterKi": 1500, "SetterKd": 10000}'
        # save device shared attributes
        res = rest_client.save_device_attributes(body = settings, device_id= DeviceId('DEVICE', device.id), scope= 'SHARED_SCOPE')
        logging.info("Save attributes result: \n%r", res)

        # creating a Device
        device = Device(name="Hatcher", type="Multiple")
        device = rest_client.save_device(device)
        logging.info(" Device was created:\n%r\n", device)
        # Creating relations from device to asset
        relation = EntityRelation(_from=asset.id, to=device.id, type="Contains")
        relation = rest_client.save_relation(relation)
        logging.info(" Relation was created:\n%r\n", relation)
        settings = '{"HatcherMode": 3.0, "HatcherTempTargetExtTemperature": 40.1, "HatcherTempTargetIntHumidity": 65, "HatcherTempTargetIntTemperature": 37.6}'
        # save device shared attributes
        res = rest_client.save_device_attributes(body = settings, device_id= DeviceId('DEVICE', device.id), scope= 'SHARED_SCOPE')
        logging.info("Save attributes result: \n%r", res)

        # Setter
        # Creating Setter Asset
        asset = Asset(name="PincubatorTest", type="Incubator")
        asset = rest_client.save_asset(asset)

        logging.info("Asset was created:\n%r\n", asset)
        # creating a Device
        device = Device(name="Test", type="Multiple")
        device = rest_client.save_device(device)
        logging.info(" Device was created:\n%r\n", device)
        # Creating relations from device to asset
        relation = EntityRelation(_from=asset.id, to=device.id, type="Contains")
        relation = rest_client.save_relation(relation)
        logging.info(" Relation was created:\n%r\n", relation)
        settings = '{"Alarm": 0, "TestMode": 3.0, "TestMinWindow": 500.0, "TestMaxWindow": 5000.0, "TestKp": 1500, "TestKi": 1500, "TestKd": 10000}'
        # save device shared attributes
        res = rest_client.save_device_attributes(body = settings, device_id= DeviceId('DEVICE', device.id), scope= 'SHARED_SCOPE')
        logging.info("Save attributes result: \n%r", res)

    except ApiException as e:
        logging.exception(e)
