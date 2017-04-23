import time
import artikcloud
from artikcloud.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: artikcloud_oauth
artikcloud.configuration.access_token = 'YOUR TOKEN'

# create an instance of the API class
api_instance = artikcloud.DeviceTypesApi()
device_type_id = 'YOUR DEVICE TYPE ID' # str | deviceTypeId

try: 
    # Get Available Manifest Versions
    api_response = api_instance.get_available_manifest_versions(device_type_id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DeviceTypesApi->get_available_manifest_versions: %s\n" % e)
