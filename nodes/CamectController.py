

from polyinterface import Controller,LOG_HANDLER,LOGGER
import logging,time,json
import camect

# My Nodea
from nodes import Host
from const import HOST_MODE_MAP,NODE_DEF_MAP

# IF you want a different log format than the current default
#LOG_HANDLER.set_log_format('%(asctime)s %(threadName)-10s %(name)-18s %(levelname)-8s %(module)s:%(funcName)s: %(message)s')

class CamectController(Controller):
    def __init__(self, polyglot):
        super(CamectController, self).__init__(polyglot)
        self.name = 'Camect Controller'
        self.hb = 0
        self.nodes_by_id = {}
        # Cross reference of host and camera id's to their node.
        self.__modifiedCustomData = False
        self.__my_drivers = {}
        self.poly.onConfig(self.process_config)

    def start(self):
        self.config_st = False # Configuration good?
        serverdata = self.poly.get_server_data(check_profile=True)
        LOGGER.info('Started Camect NodeServer {}'.format(serverdata['version']))
        self.customData = self.polyConfig['customData']
        self.saved_cameras = self.customData.get('saved_cameras',{})
        self.saved_hosts   = self.customData.get('saved_hosts',{})
        self.next_host     = self.customData.get('next_host',1)
        self.next_cam      = self.customData.get('next_cam',{})
        LOGGER.debug(self.customData)
        LOGGER.debug(self.next_cam)
        # Show values on startup if desired.
        LOGGER.debug('ST=%s',self.getDriver('ST'))
        self.set_driver('ST', 1)
        self.heartbeat()
        self.check_params()
        self.set_debug_level()
        self.discover()
        LOGGER.debug('done')

    def save_custom_data(self,force=False):
        if self.__modifiedCustomData or force:
            LOGGER.debug("saving")
            self.customData['saved_cameras'] = self.saved_cameras
            self.customData['saved_hosts']   = self.saved_hosts
            self.customData['next_host']     = self.next_host
            self.customData['next_cam']      = self.next_cam
            self.saveCustomData(self.customData)
            self.__modifiedCustomData = False
        else:
            LOGGER.debug("No save necessary")

    def shortPoll(self):
        LOGGER.debug('')
        self.save_custom_data()
        # Call shortpoll on the camect hosts
        for id,node in self.nodes_by_id.items():
            node.shortPoll()

    def longPoll(self):
        LOGGER.debug('')
        self.heartbeat()

    def query(self,command=None):
        self.check_params()
        # Call shortpoll on the camect hosts
        for id,node in self.nodes_by_id.items():
            node.query()

    def heartbeat(self):
        if self.hb == 0:
            self.reportCmd("DON",2)
            self.hb = 1
        else:
            self.reportCmd("DOF",2)
            self.hb = 0

    def set_mode_by_name(self,mname):
        LOGGER.debug(f'mode={mname}')
        if mname in HOST_MODE_MAP:
            self.set_mode(HOST_MODE_MAP[mname])
            return
        LOGGER.error(f'Unknown Host Mode Name "{mname}"')

    def set_mode(self,val=None):
        LOGGER.debug(f'val={val}')
        if val is None:
            val = self.get_driver('MODE')
        self.set_driver('MODE',val)

    def set_mode_all(self):
        """
        Updates the controller host mode based on all host modes
        Called at startup and when any host node changes modes.
        """
        hmode = None
        for id,node in self.nodes_by_id.items():
            tmode = node.camect.get_mode()
            LOGGER.debug(f'{node.name} MODE={tmode}')
            if hmode is None:
                hmode = tmode
            elif hmode != tmode:
                hmode = 'MIXED'
            LOGGER.debug(f'MODE={hmode}')
        self.set_mode_by_name(hmode)

    def discover(self):
        LOGGER.info(f'started')
        if self.hosts is not None:
            LOGGER.debug(f'saved_hosts={json.dumps(self.saved_hosts,indent=2)}')
            LOGGER.debug(f'saved_cameras={json.dumps(self.saved_cameras,indent=2)}')
            for host in self.hosts:
                # Would be better to do this conneciton inside the Host object
                # but addNode is async so we ned to get the address in this loop
                # before addNode is called :()
                camect_obj = self.connect_host(host['host'])
                if camect_obj is not False:
                    camect_info = camect_obj.get_info()
                    LOGGER.debug(f"saved_hosts={self.saved_hosts}")
                    if camect_info['id'] in self.saved_hosts:
                        # Use existing and don't re-discover
                        new = False
                        address = self.saved_hosts[camect_info['id']]['node_address']
                    else:
                        # Need to discover
                        new = True
                        address = self.controller.get_host_address(camect_info)
                    try:
                        self.nodes_by_id[camect_info['id']] = self.addNode(Host(self, address, camect_obj, new=new))
                    except:
                        LOGGER.error('Failed to add camect host {host}',exc_info=True)
                        return
        self.save_custom_data()
        self.set_mode_all()
        LOGGER.info('completed')

    def delete(self):
        LOGGER.info('Oh God I\'m being deleted. Nooooooooooooooooooooooooooooooooooooooooo.')

    def stop(self):
        LOGGER.debug('NodeServer stopped.')

    def connect_host(self,host):
        LOGGER.info(f'Connecting to {host}...')
        try:
            camect_obj = camect.Home(f"{host}:443", self.user, self.password)
        except:
            LOGGER.error(f'Failed to connect to camect host {host}',exc_info=True)
            return False
        LOGGER.info(f'Camect Name={camect_obj.get_name()}')
        LOGGER.debug(f'Camect Info={camect_obj.get_info()}')
        return camect_obj

    def get_cam_address(self,icam,parent):
        """
        Given a camera dict from Camect API return it's address if saved or generate new address
        Does not update customData, so customData must be saved by controller if this is modified.
        """
        if icam['id'] in self.saved_cameras:
            nc = self.saved_cameras[icam['id']]['node_address']
            LOGGER.debug(f"exsting camera for {parent.address} {nc} name={icam['name']} saved_name={self.saved_cameras[icam['id']]['name']}")
            return nc
        # Stored by parent adress
        nc = self.next_cam.get(parent.address,1)
        self.next_cam[parent.address] = nc + 1
        icam['node_address'] = f'{parent.address}_{nc:03d}'
        icam['parent_address'] = parent.address
        LOGGER.debug(f"append new camera for {parent.address} {icam['node_address']}: {icam}")
        self.saved_cameras[icam['id']] = icam
        self.__modifiedCustomData = True
        return icam['node_address']   

    def get_saved_cameras(self,parent):
        ret = []
        for camid, cam in self.saved_cameras.items():
            if cam['parent_address'] == parent.address:
                ret.append(cam)
        return ret

    def get_host_address(self,ihost):
        """
        Given a host dict from Camect API return it's address if saved or generate new address
        Does not update customData, so customData must be saved by if this is modified.
        """
        if ihost['id'] in self.saved_hosts:
            nh = self.saved_hosts[ihost['id']]
            LOGGER.debug(f'existing host {hc}')
            return nh
        ihost['node_address'] = f'{self.next_host:02d}'
        self.next_host += 1
        LOGGER.debug(f"append new host: {ihost['node_address']}: {ihost}")
        self.saved_hosts[ihost['id']] = ihost
        self.__modifiedCustomData = True
        return ihost['node_address']   

    def process_config(self, config):
        # this seems to get called twice for every change, why?
        # What does config represent?
        #LOGGER.info("process_config: Enter config={}".format(config))
        self.hosts = config.get('typedCustomData').get('hosts')
        #LOGGER.info("process_config: Exit");

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
        self.set_driver('GV1', level)
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

    """
    Create our own get/set driver methods because getDriver from Polyglot can be
    delayed, we sometimes need to know the value before the DB is updated
    and Polyglot gets the update back.
    """
    def set_driver(self,mdrv,val,default=0,force=False,report=True):
        #LOGGER.debug(f'{mdrv},{val} default={default} force={force},report={report}')
        if val is None:
            # Restore from DB for existing nodes
            try:
                val = self.getDriver(mdrv)
                LOGGER.info(f'{val}')
            except:
                LOGGER.warning(f'getDriver({mdrv}) failed which can happen on new nodes, using {default}')
        val = default if val is None else int(val)
        try:
            if not mdrv in self.__my_drivers or val != self.__my_drivers[mdrv] or force:
                self.setDriver(mdrv,val,report=report)
                info = ''
                if self.id in NODE_DEF_MAP and mdrv in NODE_DEF_MAP[self.id]:
                    info += f"'{NODE_DEF_MAP[self.id][mdrv]['name']}' = "
                    info += f"'{NODE_DEF_MAP[self.id][mdrv]['keys'][val]}'" if val in NODE_DEF_MAP[self.id][mdrv]['keys'] else "'NOT IN NODE_DEF_MAP'"            
                self.__my_drivers[mdrv] = val
                LOGGER.debug(f'set_driver({mdrv},{val}) {info}')
            #else:
            #    LOGGER.debug(f'not necessary')
        except:
            LOGGER.error(f'set_driver({mdrv},{val}) failed',exc_info=True)
            return None
        return val

    def get_driver(self,mdrv):
        return self.__my_drivers[mdrv] if mdrv in self.__my_drivers else None


    def cmd_update_profile(self,command):
        LOGGER.info('update_profile:')
        st = self.poly.installprofile()
        return st
 
    def cmd_discover(self,command):
        LOGGER.info('')
        self.discover()

    def cmd_set_debug_mode(self,command):
        val = int(command.get('value'))
        LOGGER.debug("cmd_set_debug_mode: {}".format(val))
        self.set_debug_level(val)

    def cmd_set_mode(self,command):
        for id,node in self.nodes_by_id.items():
            node.cmd_set_mode(command)

    id = 'controller'
    commands = {
        'QUERY': query,
        'DISCOVER': cmd_discover,
        'UPDATE_PROFILE': cmd_update_profile,
        'SET_DM': cmd_set_debug_mode,
        'SET_MODE': cmd_set_mode
}
    drivers = [
        {'driver': 'ST', 'value': 1, 'uom': 2}, 
        {'driver': 'GV1', 'value': 10, 'uom': 25}, # Debug (Log) Mode, default=30=Warning
        {'driver': 'MODE', 'value': 0, 'uom': 25}, # Host Mode of all Hosts
    ]
