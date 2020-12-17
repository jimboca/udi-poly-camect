

from polyinterface import Controller,LOG_HANDLER,LOGGER
import logging
import camect

# My Nodea
from nodes import Camera

# IF you want a different log format than the current default
#LOG_HANDLER.set_log_format('%(asctime)s %(threadName)-10s %(name)-18s %(levelname)-8s %(module)s:%(funcName)s: %(message)s')

class CamectController(Controller):
    def __init__(self, polyglot):
        super(CamectController, self).__init__(polyglot)
        self.name = 'Camect Controller'
        self.hb = 0
        #self.poly.onConfig(self.process_config)

    def start(self):
        self.config_st = False # Configuration good?
        self.camect = None # The camect api handle
        self.cams_by_id = {} # The hash of camera nodes by id
        serverdata = self.poly.get_server_data(check_profile=True)
        LOGGER.info('Started Camect NodeServer {}'.format(serverdata['version']))
        # Show values on startup if desired.
        LOGGER.debug('ST=%s',self.getDriver('ST'))
        self.setDriver('ST', 1)
        self.heartbeat(0)
        self.check_params()
        self.set_debug_level()
        if self.config_st:
            self.connect()

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

    def callback(self,event):
        # {'type': 'alert', 'desc': 'Out Front Door just saw a person.', 'url': 'https://home.camect.com/home/...', 
        # 'cam_id': '96f69defdef1d0b6602a', 'cam_name': 'Out Front Door', 'detected_obj': ['person']}
        LOGGER.debug(f'{event}')
        try:
            if event['type'] == 'mode':
                # Can't really use this: {'type': 'mode', 'desc': 'HOME'}
                pass
            elif 'cam_id' in event:
                # Anything with cam get's passed to the camera
                if event['cam_id'] in self.cams_by_id:
                    self.cams_by_id[event['cam_id']].callback(event)
                else:
                    LOGGER.warning(f"Event for unknown cam_id={event['cam_id']}: {event}")
            else:
                LOGGER.error(f'Unknwon event, not type=mode or cam_id: {event}')
        except:
            LOGGER.error('in callback: ',exc_info=True)

    def connect(self):
        LOGGER.info(f'Connecting to {self.host}...')
        try:
            self.camect = camect.Home(f"{self.host}:443", self.user, self.password)
        except:
            LOGGER.error('Failed to conenct to camect host {self.host}',exc_info=True)
            return
        LOGGER.debug(f'Camect={self.camect.get_name()}')
        self.camect.add_event_listener(self.callback)
        self.discover()

    def discover(self, *args, **kwargs):
        # TODO: Keep cams_by_id in DB to remember across restarts and discovers...
        LOGGER.info('started')
        cnt = 1
        for cam in self.camect.list_cameras():
            print(cam)
            # Only add enabled cameras?
            if not cam['disabled']:
                self.cams_by_id[cam['id']] = self.addNode(Camera(self, cnt, cam))
                cnt += 1
        LOGGER.info('completed')

    def delete(self):
        LOGGER.info('Oh God I\'m being deleted. Nooooooooooooooooooooooooooooooooooooooooo.')

    def stop(self):
        LOGGER.debug('NodeServer stopped.')

    def process_config(self, config):
        # this seems to get called twice for every change, why?
        # What does config represent?
        LOGGER.info("process_config: Enter config={}".format(config));
        LOGGER.info("process_config: Exit");

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
        if self.host is None:
            self.host = 'camect.local'
            self.addCustomParam({'host': self.host})

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
        {'driver': 'GV2', 'value': 1, 'uom': 2},  # Connected
    ]
