
from polyinterface import Node,LOGGER
from node_funcs import id_to_address,get_valid_node_name

class Camera(Node):
    def __init__(self, controller, primary, cam=None):
        #print("%s(%s) @%s(%s)" % (cam["name"], cam["make"], cam["ip_addr"], cam["mac_addr"]))
        self.cam = cam
        super(Camera, self).__init__(controller, primary.address, id_to_address(cam['id']), get_valid_node_name(cam['name']))
        self.lpfx = '%s:%s' % (self.address,self.name)

    def start(self):
        self.setDriver('ST',0 if self.cam['disabled']          else 1)
        self.setDriver('GV0',0 if self.cam['is_alert_disabled'] else 1)
        self.setDriver('GV1',1 if self.cam['is_streaming']      else 0)
        pass

    def shortPoll(self):
        pass

    def longPoll(self):
        pass

    def cmd_on(self, command):
        """
        Example command received from ISY.
        Set DON on TemplateNode.
        Sets the ST (status) driver to 1 or 'True'
        """
        self.setDriver('ST', 1)

    def cmd_off(self, command):
        """
        Example command received from ISY.
        Set DOF on TemplateNode
        Sets the ST (status) driver to 0 or 'False'
        """
        self.setDriver('ST', 0)

    def query(self,command=None):
        """
        Called by ISY to report all drivers for this node. This is done in
        the parent class, so you don't need to override this method unless
        there is a need.
        """
        self.reportDrivers()

    hint = [1,2,3,4]
    drivers = [
        {'driver': 'ST',  'value': 0, 'uom': 2}, # Enabled
        {'driver': 'GV0', 'value': 0, 'uom': 2}, # Alerting
        {'driver': 'GV1', 'value': 0, 'uom': 2}, # Streaming
        ]
    id = 'camera'
    commands = {
                    'DON': cmd_on,
                    'DOF': cmd_off,
                }
