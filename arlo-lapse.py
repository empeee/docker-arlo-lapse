from Arlo import Arlo
import datetime
import glob
import re
import os
import imageio
import timeout_decorator
import yaml
import logging

CONFIG_PATH = './cfg/'

LAPSE_PATH = './lapse/'
SNAPSHOT_PATH = './raw/'
PURGE_DURATION_HOURS = 24
LAPSE_DURATION = 10

logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', level=logging.DEBUG) #, filename='arlo-lapse.log')

class ArloLapse:
    """
    This is a class to generate videos of Arlo stills.

    Everything is pulled in through config.yaml which should
    live in the sub-directory cfg/

    Attributes:
        username (str): Arlo username
        password (str): Arlo password
        camera_names (list of strings): List of camera names to use
        lapse_path (str): Path to resulting videos
        snapshot_path (str): Path to raw snapshots
        purge_duration_hours (float): Time in hours to retain images
        laps_duration (float): Target duration of resulting video
    """

    def __init__(self):
        """ Constructor for ArloGIF class """

        logging.info('ArloLapse.__init__(): Initializing...')

        with open(CONFIG_PATH + 'config.yaml', 'r') as f:
            try:
                cfg_yaml = yaml.load(f)
            except yaml.YAMLError as exc:
                print(exc)

        if 'username' in cfg_yaml:
            self.username = cfg_yaml['username']
        else:
            raise ValueError('Cannot find username in config.yaml')

        if 'password' in cfg_yaml:
            self.password = cfg_yaml['password']
        else:
            raise ValueError('Cannot find password in config.yaml')

        camera_names = cfg_yaml.get('camera_names')
        if camera_names:
            self.camera_names = camera_names
            logging.debug('ArloLapse.__init__(): Found camera_names: ' + ', '.join(camera_names))
        else:
            self.camera_names = []

        lapse_path = cfg_yaml.get('lapse_path')
        if lapse_path:
            self.lapse_path = lapse_path
            logging.debug('ArloLapse.__init__(): Found lapse_path: ' + lapse_path)
        else:
            self.lapse_path = LAPSE_PATH

        snapshot_path = cfg_yaml.get('snapshot_path')
        if snapshot_path:
            self.snapshot_path = snapshot_path
            logging.debug('ArloLapse.__init__(): Found snapshot_path: ' + snapshot_path)
        else:
            self.snapshot_path = SNAPSHOT_PATH

        purge_duration_hours = cfg_yaml.get('purge_duration_hours')
        if purge_duration_hours:
            self.purge_duration_hours = purge_duration_hours
            logging.debug('ArloLapse.__init__(): Found purge_duration_hours: ' + purge_duration_hours)
        else:
            self.purge_duration_hours = PURGE_DURATION_HOURS

        lapse_duration = cfg_yaml.get('lapse_duration')
        if lapse_duration:
            self.lapse_duration = lapse_duration
            logging.debug('ArloLapse.__init__(): Found lapse_duration: ' + lapse_duration)
        else:
            self.lapse_duration = LAPSE_DURATION


    @timeout_decorator.timeout(60)
    def get_snapshot_url(self, arlo, basestation, camera):
        """
        Method to return snapshot URL with timeout

        Parameters:
            arlo (Arlo): logged in Arlo instance
            basestation (str): basestation name
            camera (str): camera name

        Returns:
            snapshot url (str)
        """

        return arlo.TriggerFullFrameSnapshot(basestation,camera)

    def get_snapshots(self):
        """
        Method to get snapshots for a list of cameras.

        If the camera list is give in config.yaml, they are checked to exist.
        If the camera list wasn't given, get all cameras from Arlo
        """

        logging.info('ArloLapse.get_snapshots(): Getting snapshots...')

        try:
            arlo = Arlo(self.username, self.password)
            basestations = arlo.GetDevices('basestation')
            cameras = arlo.GetDevices('camera')
            now = datetime.datetime.now()
            now_str = now.strftime('%Y%m%d%H%M%S')

            camera_names = []

            for camera in cameras:
                camera_name = camera['deviceName'].replace(' ', '_')
                camera_names.append(camera_name)


            if not self.camera_names:
                logging.debug('ArloLapse.get_snapshots(): No camera names given, getting from Arlo')
                self.camera_names = camera_names
            else:
                logging.debug('ArloLapse.get_snapshots(): Checking if given camera names are in Arlo')
                self.camera_names = list(set(self.camera_names) & set(camera_names))

            logging.debug('ArloLapse.get_snapshots(): Final list of cameras: ' + ', '.join(self.camera_names))

            for camera in cameras:
                camera_name = camera['deviceName'].replace(' ', '_')
                if camera_name in self.camera_names:
                    logging.debug('ArloLapse.get_snapshots(): Getting snapshot for ' + camera_name)
                    snapshot_file = self.snapshot_path + camera_name + '_' + now_str + '.jpg'
                    try:
                        snapshot_url = self.get_snapshot_url(arlo, basestations[0], camera)
                        arlo.DownloadSnapshot(snapshot_url,snapshot_file)
                    except timeout_decorator.TimeoutError:
                        logging.warning('ArloLapse.get_snapshots(): Timeout ' + camera_name)

        except Exception as e:
            print(e)

    def purge_snapshots(self):
        """
        Method to purge old snapshots that exceed the time to keep.

        Pulls age of snapshot from filename.
        """

        logging.info('ArloLapse.purge_snapshots(): Purging Snapshots...')
        now = datetime.datetime.now()

        for camera_name in self.camera_names:
            files = glob.glob(self.snapshot_path + camera_name + '*.jpg')

            regex = r'([a-zA-Z_]+)([0-9]+)'

            for file in files:
                match = re.search(regex, file)
                date = datetime.datetime.strptime(match.group(2), '%Y%m%d%H%M%S')
                if date < now - datetime.timedelta(hours=self.purge_duration_hours):
                    logging.debug('ArloLapse.purge_snapshots(): Purging ' + file)
                    os.remove(file)

    def make_lapse(self):
        """ Method to generate GIF from available snapshots. """

        logging.info('ArloLapse.make_lapse(): Making Time Lapses...')

        for camera_name in self.camera_names:
            files = sorted(glob.glob(self.snapshot_path + camera_name + '*.jpg'))
            num_files = len(files)
            logging.debug('ArloLapse.make_lapse(): Found ' + str(num_files) + ' images for ' + camera_name)

            if num_files>0:
                fps = num_files/self.lapse_duration
                images = []
                for file in files:
                    images.append(imageio.imread(file))
                output_file = self.snapshot_path + camera_name + '.gif'
                final_file = self.lapse_path + camera_name + '.gif'
                imageio.mimwrite(output_file, images, fps=fps)

                command = 'gifsicle -O3 --colors 128 --resize-width 512 {} > {}'.format(output_file, final_file)
                os.system(command)



if __name__ =='__main__':
    arlo_gif = ArloLapse()
    arlo_gif.get_snapshots()
    arlo_gif.purge_snapshots()
    arlo_gif.make_lapse()
    logging.info('ArloLapse: Script complete.')

