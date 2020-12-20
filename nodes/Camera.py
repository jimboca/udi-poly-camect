
from polyinterface import Node,LOGGER
from node_funcs import id_to_address,get_valid_node_name
from nodes import DetectedObject

# Map name to address, most are the same but address must be <=7 characters
OBJECT_MAP = {
    'Santa Claus': 'santa',
    'Amazon':      'amazon',
    'DHL':         'dhl',
    'FedEx':       'fedex',
    'RoyalMail':   'roylmail',
    'UPS truck':   'ups',
    'USPS':        'usps',
    'bear':        'bear',
    'bicycle':     'bicycle',
    'bird':        'bird',
    'bus':         'bus',
    'car':         'car',
    'cat':         'cat',
    'deer':        'deer',
    'dog':         'dog',
    'motorcycle':  'mtrcycle',
    'mouse':       'mouse',
    'person':      'person',
    'pickup':      'pickup',
    'rabbit':      'rabbit',
    'raccoon':     'raccoon',
    'skunk':       'skunk',
    'squirrel':    'squirrel',
    'truck':       'truck',
    'unknown animal': 'unkanml',
    'unknown small animal': 'unksmanm',
    'fly':                  'fly', 
    'spider':               'spider',
}

class Camera(Node):
    def __init__(self, controller, num, cam=None):
        #print("%s(%s) @%s(%s)" % (cam["name"], cam["make"], cam["ip_addr"], cam["mac_addr"]))
        self.cam = cam
        self.detected_obj_by_name = {}
        address = f'c{num:04d}' 
        super(Camera, self).__init__(controller, address, address, get_valid_node_name(cam['name']))
        self.lpfx = '%s:%s' % (self.address,self.name)

    def start(self):
        self.setDriver('ST',0  if self.cam['disabled']          else 1)
        self.setDriver('GV0',0 if self.cam['is_alert_disabled'] else 1)
        self.setDriver('GV1',1 if self.cam['is_streaming']      else 0)
        for obj_name in OBJECT_MAP:
            self.detected_obj_by_name[obj_name] = self.controller.addNode(DetectedObject(self.controller, self, f'{self.address}_{OBJECT_MAP[obj_name]}', f'{self.name} {obj_name}'))

    def shortPoll(self):
        pass

    def longPoll(self):
        pass

    def callback(self,event):
        # {'type': 'alert', 'desc': 'Out Front Door just saw a person.', 'url': 'https://home.camect.com/home/...', 
        # 'cam_id': '96f69defdef1d0b6602a', 'cam_name': 'Out Front Door', 'detected_obj': ['person']}
        LOGGER.debug(f"{self.lpfx} type={event['type']}")
        if event['type'] == 'alert':
            if 'detected_obj' in event:
                self.detected_obj(event['detected_obj'])
            else:
                LOGGER.error(f"Unknown alert, no detected_obj in {event}")

    def detected_obj(self,object_list):
        LOGGER.debug(f"{self.lpfx} {object_list}")
        # Clear last detected objects
        # TODO: Would be better to timout and clear these during a short poll, but allow for user specified timeout?
        for obj in OBJECT_MAP:
            self.detected_obj_by_name[obj].clear()
        # And set the current ones
        for obj in object_list:
            if obj in OBJECT_MAP:
                LOGGER.debug(f"{self.lpfx} {obj}")
                self.detected_obj_by_name[obj].turn_on()
            else:
                LOGGER.error(f"Unsupported detected object '{obj}'")

    def cmd_on(self, command):
        self.controller.enable_alert(self.cam['id'])
        self.setDriver('GV0', 1)

    def cmd_off(self, command):
        self.controller.disable_alert(self.cam['id'])
        self.setDriver('GV0', 0)

    def query(self,command=None):
        self.reportDrivers()

    hint = [1,2,3,4]
    drivers = [
        {'driver': 'ST',  'value': 0, 'uom': 2}, # Enabled
        {'driver': 'GV0', 'value': 0, 'uom': 2}, # Alerting
        {'driver': 'GV1', 'value': 0, 'uom': 2}, # Streaming
        {'driver': 'GV3', 'value': 0, 'uom': 2}, # Person
        {'driver': 'GV4', 'value': 0, 'uom': 2}, # Dog
        {'driver': 'GV5', 'value': 0, 'uom': 2}, # Car
        {'driver': 'GV6', 'value': 0, 'uom': 2}, # Skunk
        ]
    id = 'camera'
    commands = {
                    'DON': cmd_on,
                    'DOF': cmd_off,
                }
