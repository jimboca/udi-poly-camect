
from polyinterface import Node,LOGGER
from node_funcs import id_to_address,get_valid_node_name

class DetectedObject(Node):
    def __init__(self, controller, primary, address, name):
        super(DetectedObject, self).__init__(controller, primary.address, address, name)
        self._mydrivers = {}
        self.lpfx = '%s:%s' % (self.address,self.name)

    def start(self):
        LOGGER.debug(f'{self.lpfx}')
        self.setDriver('ST',0)

    def shortPoll(self):
        pass

    def longPoll(self):
        pass

    def clear(self):
        if int(self.get_driver('ST')) == 1:
            LOGGER.debug(f'{self.lpfx}')
            self.reportCmd("DOF",2)
            self.set_driver('ST', 0)

    # This is called by parent when object is detected
    def turn_on(self):
        LOGGER.debug(f"{self.lpfx}")
        self.reportCmd("DON",2)
        self.set_driver('ST', 1)

    # This is called by parent when object is no longer detected
    def turn_off(self):
        LOGGER.debug(f"{self.lpfx}")
        self.reportCmd("DOF",2)
        self.set_driver('ST', 0)

    def cmd_on(self, command=None):
        LOGGER.debug(f"{self.lpfx} command={command} ST={self.get_driver('ST')}")
        self.set_driver('ST', 1)

    def cmd_off(self, command=None):
        LOGGER.debug(f"{self.lpfx} command={command} ST={self.get_driver('ST')}")
        self.set_driver('ST', 1)

    def query(self,command=None):
        LOGGER.debug(f'{self.lpfx}')
        self.reportDrivers()

    def set_driver(self,drv,val):
        self._mydrivers[drv] = val
        self.setDriver(drv,val)

    def get_driver(self,drv):
        if drv in self._mydrivers:
            return self._mydrivers[drv]
        return self.getDriver(drv)

    hint = [1,2,3,4]
    drivers = [
        {'driver': 'ST',  'value': 0, 'uom': 2}, # Enabled
        ]
    id = 'objdet'
    commands = {
                    'DON': cmd_on,
                    'DOF': cmd_off,
                }
