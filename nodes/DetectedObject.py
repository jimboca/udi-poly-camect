
from polyinterface import Node,LOGGER
from node_funcs import id_to_address,get_valid_node_name

class DetectedObject(Node):
    def __init__(self, controller, primary, address, name):
        super(DetectedObject, self).__init__(controller, primary.address, address, name)
        self.lpfx = '%s:%s' % (self.address,self.name)

    def start(self):
        LOGGER.debug(f'{self.lpfx}')
        self.setDriver('ST',0)

    def shortPoll(self):
        pass

    def longPoll(self):
        pass

    def clear(self):
        LOGGER.debug(f'{self.lpfx}')
        if int(self.getDriver('ST')) == 1:
            self.reportCmd("DOF",2)
            self.setDriver('ST', 0)

    def cmd_on(self, command=None):
        LOGGER.debug(f'{self.lpfx}')
        self.reportCmd("DON",2)
        self.setDriver('ST', 1)

    def cmd_off(self, command=None):
        LOGGER.debug(f'{self.lpfx}')
        self.reportCmd("DOF",2)
        self.setDriver('ST', 1)

    def query(self,command=None):
        LOGGER.debug(f'{self.lpfx}')
        self.reportDrivers()

    hint = [1,2,3,4]
    drivers = [
        {'driver': 'ST',  'value': 0, 'uom': 2}, # Enabled
        ]
    id = 'objdet'
    commands = {
                    'DON': cmd_on,
                    'DOF': cmd_off,
                }
