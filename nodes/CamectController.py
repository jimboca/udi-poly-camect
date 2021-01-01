

from polyinterface import Controller,LOG_HANDLER,LOGGER
import logging

# My Nodea
from nodes import Host

# IF you want a different log format than the current default
#LOG_HANDLER.set_log_format('%(asctime)s %(threadName)-10s %(name)-18s %(levelname)-8s %(module)s:%(funcName)s: %(message)s')

class CamectController(Controller):
    def __init__(self, polyglot):
        super(CamectController, self).__init__(polyglot)
        self.name = 'Camect Controller'
        self.hb = 0
        self.poly.onConfig(self.process_config)

    def start(self):
        self.config_st = False # Configuration good?
        serverdata = self.poly.get_server_data(check_profile=True)
        LOGGER.info('Started Camect NodeServer {}'.format(serverdata['version']))
        # Show values on startup if desired.
        LOGGER.debug('ST=%s',self.getDriver('ST'))
        self.setDriver('ST', 1)
        self.heartbeat(0)
        self.check_params()
        self.set_debug_level()
        self.discover()

    def shortPoll(self):
        for node in self.nodes:
            if node != self.address:
                self.nodes[node].shortPoll()

    def longPoll(self):
        LOGGER.debug('longPoll')
        self.heartbeat()

    def query(self,command=None):
        self.check_params()
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    def heartbeat(self):
        if self.hb == 0:
            self.reportCmd("DON",2)
            self.hb = 1
        else:
            self.reportCmd("DOF",2)
            self.hb = 0

    def camect_address(self,camect):
        return id_to_address(camect.get_id())

    def discover(self, *args, **kwargs):
        LOGGER.info('started')
        if self.hosts is not None:
            for host in self.hosts:
                try:
                    self.addNode(Host(self, host))
                except:
                    LOGGER.error('Failed to add camect host {host}',exc_info=True)
        LOGGER.info('completed')

    def delete(self):
        LOGGER.info('Oh God I\'m being deleted. Nooooooooooooooooooooooooooooooooooooooooo.')

    def stop(self):
        LOGGER.debug('NodeServer stopped.')

    def process_config(self, config):
        # this seems to get called twice for every change, why?
        # What does config represent?
        #LOGGER.info("process_config: Enter config={}".format(config))
        self.config = config
        typedCustomData = config.get('typedCustomData')
        self.hosts = typedCustomData.get('hosts')
        #LOGGER.info("process_config: Exit");

    def heartbeat(self,init=False):
        LOGGER.debug('heartbeat: init={}'.format(init))
        if init is not False:
            self.hb = init
        LOGGER.debug('heartbeat: hb={}'.format(self.hb))
        if self.hb == 0:
            self.reportCmd("DON",2)
            self.hb = 1
        else:
            self.reportCmd("DOF",2)
            self.hb = 0

    def set_module_logs(self,level):
        logging.getLogger('urllib3').setLevel(level)

    def set_debug_level(self,level=None):
        LOGGER.debug('set_debug_level: {}'.format(level))
        if level is None:
            try:
                level = self.getDriver('GV1')
                if level is None:
                    level = logging.DEBUG
            except:
                # First run so driver isn't set, use DEBUG
                level = logging.DEBUG
        level = int(level)
        if level == 0:
            level = 30
        LOGGER.info('set_debug_level: Set GV1 to {}'.format(level))
        self.setDriver('GV1', level)
        # For now we don't want to see all this
        # TODO: Add another level = 8
        logging.getLogger("websockets.protocol").setLevel(logging.WARNING)
        # 0=All 10=Debug are the same because 0 (NOTSET) doesn't show everything.
        if level <= 10:
            # this is the best way to control logging for modules, so you can
            # still see warnings and errors
            #if level < 10:
            #    self.set_module_logs(logging.DEBUG)
            #else:
            #    # Just warnigns for the modules unless in module debug mode
            #    self.set_module_logs(logging.WARNING)
            # Or you can do this and you will never see mention of module logging
            if level < 10:
                LOG_HANDLER.set_basic_config(True,logging.DEBUG)
            else:
                # This is the polyinterface default
                LOG_HANDLER.set_basic_config(True,logging.WARNING)
            LOGGER.setLevel(logging.DEBUG)
        elif level == 20:
            LOGGER.setLevel(logging.INFO)
        elif level == 30:
            LOGGER.setLevel(logging.WARNING)
        elif level == 40:
            LOGGER.setLevel(logging.ERROR)
        elif level == 50:
            LOGGER.setLevel(logging.CRITICAL)
        else:
            LOGGER.debug("set_debug_level: Unknown level {}".format(level))

    def check_params(self):
        """
        This is an example if using custom Params for user and password and an example with a Dictionary
        """
        self.removeNoticesAll()
        default_user = "YourUserName"
        default_password = "YourPassword"

        self.host = self.getCustomParam('host')
        if self.host is not None:
            self.addNotice('Please move your host configuration to the new Camect Hosts and Delete the current host key','host_key')

        self.user = self.getCustomParam('user')
        if self.user is None:
            self.user = default_user
            LOGGER.error('check_params: user not defined in customParams, please add it.  Using {}'.format(self.user))
            self.addCustomParam({'user': self.user})

        self.password = self.getCustomParam('password')
        if self.password is None:
            self.password = default_password
            LOGGER.error('check_params: password not defined in customParams, please add it.  Using {}'.format(self.password))
            self.addCustomParam({'password': self.password})

        # Add a notice if they need to change the user/password from the default.
        if self.user == default_user or self.password == default_password:
            # This doesn't pass a key to test the old way.
            self.addNotice('Please set proper user and password in configuration page, and restart this nodeserver','config')
        else:
            self.config_st = True

        self.poly.save_typed_params(
            [
                {
                    'name': 'hosts',
                    'title': 'Camect Host',
                    'desc': 'Camect Hosts',
                    'isList': True,
                    'params': [
                        {
                            'name': 'host',
                            'title': 'Camect Host or IP Address',
                            'isRequired': True,
                            'defaultValue': ['camect.local']
                        },
                    ]
                },
            ]
        )

 
    def update_profile(self,command):
        LOGGER.info('update_profile:')
        st = self.poly.installprofile()
        return st

    def cmd_set_debug_mode(self,command):
        val = int(command.get('value'))
        LOGGER.debug("cmd_set_debug_mode: {}".format(val))
        self.set_debug_level(val)

    id = 'controller'
    commands = {
        'QUERY': query,
        'DISCOVER': discover,
        'UPDATE_PROFILE': update_profile,
        'SET_DM': cmd_set_debug_mode,
    }
    drivers = [
        {'driver': 'ST', 'value': 1, 'uom': 2}, 
        {'driver': 'GV1', 'value': 10, 'uom': 25}, # Debug (Log) Mode, default=30=Warning
    ]
