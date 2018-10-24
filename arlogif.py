from Arlo import Arlo
import datetime
import glob
import re
import os
import imageio
import time
import timeout_decorator
import yaml

DEBUG = True

GIF_PATH = './gif/'
SNAPSHOT_PATH = './raw/'
CONFIG_PATH = './cfg/'
PURGE_DURATION_HOURS = 24
GIF_FRAME_SECONDS = 0.25

class ArloGIF:
    """
    This is a class to generate animated GIFs of Arlo stills.

    Everything is pulled in through config.yaml which should
    live in the sub-directory cfg/

    Attributes:
        username (str): Arlo username
        password (str): Arlo password
        camera_names (list of strings): List of camera names to use
        gif_path (str): Path to resulting GIFs
        snapshot_path (str): Path to raw snapshots
        purge_duration_hours (float): Time in hours to retain images
        gif_frame_seconds (float): Frame duration in resulting GIF
    """

    def __init__(self):
        """ Constructor for ArloGIF class """

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

        if 'camera_names' in cfg_yaml:
            self.camera_names = cfg_yaml['camera_names']
        else:
            self.camera_names = []

        if 'gif_path' in cfg_yaml:
            self.gif_path = cfg_yaml['gif_path']
        else:
            self.gif_path = GIF_PATH

        if 'snapshot_path' in cfg_yaml:
            self.snapshot_path = cfg_yaml['snapshot_path']
        else:
            self.snapshot_path = SNAPSHOT_PATH

        if 'purge_duration_hours' in cfg_yaml:
            self.purge_duration_hours = cfg_yaml['purge_duration_hours']
        else:
            self.purge_duration_hours = PURGE_DURATION_HOURS

        if 'gif_frame_seconds' in cfg_yaml:
            self.gif_frame_seconds = cfg_yaml['gif_frame_seconds']
        else:
            self.gif_frame_seconds = GIF_FRAME_SECONDS

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

        if DEBUG: print('\nGetting Snapshots')

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
                if DEBUG: print('  No camera names given, getting from Arlo')
                self.camera_names = camera_names
            else:
                if DEBUG: print('  Checking if given camera names are in Arlo')
                self.camera_names = list(set(self.camera_names) & set(camera_names))

            if DEBUG: print('    Final list of cameras: ' + ', '.join(self.camera_names))

            for camera in cameras:
                camera_name = camera['deviceName'].replace(' ', '_')
                if camera_name in self.camera_names:
                    if DEBUG: print('  Getting snapshot for ' + camera_name)
                    snapshot_file = self.snapshot_path + camera_name + '_' + now_str + '.jpg'
                    try:
                        snapshot_url = self.get_snapshot_url(arlo, basestations[0], camera)
                        arlo.DownloadSnapshot(snapshot_url,snapshot_file)
                    except timeout_decorator.TimeoutError:
                        if DEBUG: print('    Timeout ' + camera_name)

        except Exception as e:
            print(e)

    def purge_snapshots(self):
        """
        Method to purge old snapshots that exceed the time to keep.

        Pulls age of snapshot from filename.
        """

        if DEBUG: print('\nPurging Snapshots')
        now = datetime.datetime.now()

        for camera_name in self.camera_names:
            files = glob.glob(self.snapshot_path + camera_name + '*.jpg')

            regex = r'([a-zA-Z_]+)([0-9]+)'

            for file in files:
                match = re.search(regex, file)
                date = datetime.datetime.strptime(match.group(2), '%Y%m%d%H%M%S')
                if date < now - datetime.timedelta(hours=self.purge_duration_hours):
                    if DEBUG: print('  Purging ' + file)
                    os.remove(file)

    def make_gifs(self):
        """ Method to generate GIF from available snapshots. """

        if DEBUG: print('\nMaking GIFs')
        for camera_name in self.camera_names:
            files = sorted(glob.glob(self.snapshot_path + camera_name + '*.jpg'))
            num_files = len(files)
            if DEBUG: print('  Found ' + str(num_files) + ' images for ' + camera_name)

            if num_files>0:
                images = []
                for file in files:
                    images.append(imageio.imread(file))
                output_file = self.gif_path + camera_name + '.gif'
                imageio.mimsave(output_file, images, duration=self.gif_frame_seconds, subrectangles=True)



if __name__ =='__main__':
    arlo_gif = ArloGIF()
    arlo_gif.get_snapshots()
    arlo_gif.purge_snapshots()
    arlo_gif.make_gifs()

