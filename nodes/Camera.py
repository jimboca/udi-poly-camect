
from polyinterface import Node,LOGGER
from node_funcs import id_to_address,get_valid_node_name
from nodes import DetectedObject
from const import DETECTED_OBJECT_MAP

class Camera(Node):
    def __init__(self, controller, host, num, cam=None):
        #print("%s(%s) @%s(%s)" % (cam["name"], cam["make"], cam["ip_addr"], cam["mac_addr"]))
        self.host = host
        self.cam = cam
        self.detected_obj_by_type = {}
        address = self.host.camect.get_id()[:9] + f'{int(num):02d}'
        super(Camera, self).__init__(controller, address, address, get_valid_node_name(cam['name']))
        self.lpfx = '%s:%s' % (self.address,self.name)

    def start(self):
        self.setDriver('ST',0  if self.cam['disabled']          else 1)
        self.setDriver('MODE',0 if self.cam['is_alert_disabled'] else 1)
        self.setDriver('GPV', 1 if self.cam['is_streaming']      else 0)
        self.setDriver('ALARM',0)
        for cat in DETECTED_OBJECT_MAP:
            node = self.controller.addNode(DetectedObject(self.controller, self, cat))
            # Keep track of which node handles which detected object type.
            for otype in DETECTED_OBJECT_MAP[cat]:
                self.detected_obj_by_type[otype] = node

    def shortPoll(self):
        pass

    def longPoll(self):
        pass

    def callback(self,event):
        # {'type': 'alert', 'desc': 'Out Front Door just saw a person.', 'url': 'https://home.camect.com/home/...', 
        # 'cam_id': '96f69defdef1d0b6602a', 'cam_name': 'Out Front Door', 'detected_obj': ['person']}
        LOGGER.debug(f"{self.lpfx} type={event['type']}")
        if event['type'] == 'alert':
            if 'detected_obj' in DETECTED_OBJECT_MAP:
                self.detected_obj(event['detected_obj'])
            else:
                LOGGER.error(f"Unknown alert, no detected_obj in {event}")

    def detected_obj(self,object_list):
        LOGGER.debug(f"{self.lpfx} {object_list}")
        # Clear last detected objects
        # TODO: Would be better to timout and clear these during a short poll, but allow for user specified timeout?
        for cat in DETECTED_OBJECT_MAP:
            for otype in DETECTED_OBJECT_MAP[cat]:
                self.detected_obj_by_type[obj].clear()
        # And set the current ones
        for obj in object_list:
            if obj in DETECTED_OBJECT_MAP:
                LOGGER.debug(f"{self.lpfx} {obj}")
                self.setDriver('ALARM',1)
                #self.setDriver('ALARM',DETECTED_OBJECT_MAP['obj'])
                self.detected_obj_by_type[obj].turn_on(obj)
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
        {'driver': 'ALARM', 'value': 0, 'uom': 2}, # Alerting
        {'driver': 'MODE', 'value': 0, 'uom': 2}, # Alerting
        {'driver': 'GPV', 'value': 0, 'uom': 2}, # Streaming
        {'driver': 'GV0', 'value': 0, 'uom': 2}, # 
        {'driver': 'GV1', 'value': 0, 'uom': 2}, # 
        {'driver': 'GV2', 'value': 0, 'uom': 2}, # 
        {'driver': 'GV3', 'value': 0, 'uom': 2}, # 
        {'driver': 'GV4', 'value': 0, 'uom': 2}, # 
        {'driver': 'GV5', 'value': 0, 'uom': 2}, # 
        {'driver': 'GV6', 'value': 0, 'uom': 2}, # 
        {'driver': 'GV7', 'value': 0, 'uom': 2}, # 
        {'driver': 'GV8', 'value': 0, 'uom': 2}, # 
        {'driver': 'GV9', 'value': 0, 'uom': 2}, # 
        {'driver': 'GV10', 'value': 0, 'uom': 2}, # 
        {'driver': 'GV11', 'value': 0, 'uom': 2}, # 
        {'driver': 'GV12', 'value': 0, 'uom': 2}, # 
        {'driver': 'GV13', 'value': 0, 'uom': 2}, # 
        {'driver': 'GV14', 'value': 0, 'uom': 2}, # 
        {'driver': 'GV15', 'value': 0, 'uom': 2}, # 
        {'driver': 'GV16', 'value': 0, 'uom': 2}, # 
        {'driver': 'GV17', 'value': 0, 'uom': 2}, # 
        {'driver': 'GV18', 'value': 0, 'uom': 2}, # 
        {'driver': 'GV19', 'value': 0, 'uom': 2}, # 
        {'driver': 'GV20', 'value': 0, 'uom': 2}, # 
        {'driver': 'GV21', 'value': 0, 'uom': 2}, # 
        {'driver': 'GV22', 'value': 0, 'uom': 2}, # 
        {'driver': 'GV23', 'value': 0, 'uom': 2}, # 
        {'driver': 'GV24', 'value': 0, 'uom': 2}, # 
        {'driver': 'GV25', 'value': 0, 'uom': 2}, # 
        {'driver': 'GV26', 'value': 0, 'uom': 2}, # 
        {'driver': 'GV27', 'value': 0, 'uom': 2}, # 
        ]
    id = 'camera'
    commands = {
                    'DON': cmd_on,
                    'DOF': cmd_off,
                }
