

from polyinterface import Node,LOG_HANDLER,LOGGER
import logging
import time
import camect

# My Nodea
from nodes import Camera

# My funtions
from node_funcs import id_to_address,get_valid_node_name

class Host(Node):
    id = 'host'
    drivers = [
        {'driver': 'ST', 'value': 1, 'uom': 2}, 
    ]

    def __init__(self, controller, host_param):
        self.host_param = host_param
        self.host = host_param['host']
        self.controller = controller
        self.camect = None # The camect api handle
        self.cams_by_id = {} # The hash of camera nodes by id
        if self.connect() is not True:
            return
        name = get_valid_node_name('Camect'+self.camect.get_name())
        address = 'h_'+self.camect.get_id()[:9]
        LOGGER.info(f'host={self.host} name={name} address={address}')
        super(Host, self).__init__(controller, address, address, name)

    def start(self):
        LOGGER.info(f'Started Camect Host {self.host}')
        self.camect.add_event_listener(self.callback)
        self.discover()
        self.setDriver('ST',1)

    def shortPoll(self):
        pass

    def longPoll(self):
        pass

    def query(self,command=None):
        for node in self.nodes:
            self.nodes[node].reportDrivers()

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
            self.camect = camect.Home(f"{self.host}:443", self.controller.user, self.controller.password)
        except:
            LOGGER.error(f'Failed to connect to camect host {self.host}',exc_info=True)
            return False
        LOGGER.debug(f'Camect={self.camect.get_name()}')
        return True

    def discover(self, *args, **kwargs):
        # TODO: Keep cams_by_id in DB to remember across restarts and discovers...
        LOGGER.info('started')
        typedCustomData = self.controller.config.get('typedCustomData')
        cnt = 1
        for cam in self.camect.list_cameras():
            #self.save_camera(typedCustomData,cam)
            print(cam)
            # Only add enabled cameras?
            if not cam['disabled']:
                self.cams_by_id[cam['id']] = self.controller.addNode(Camera(self.controller, self, cnt, cam))
                cnt += 1
        LOGGER.info('completed')

    def save_camera(self,tcd,cam): # TODO: GEt this workign to save in customData
        cameras = tcd.get('cameras')
        found = False
        if cameras is None:
            cameras = []
        else:
            for cam in cameras:
                if (cam['id'] == cam['id']):
                    found = True
        if not found:
            cameras.append({'name': cam['name'], 'id': cam['id'], 'host': cam['ip_addr'], 'detect': 'None'})
        

    def delete(self):
        LOGGER.info('Oh God I\'m being deleted. Nooooooooooooooooooooooooooooooooooooooooo.')

    def stop(self):
        LOGGER.debug('NodeServer stopped.')

    commands = {
        'QUERY': query,
        'DISCOVER': discover,
    }
