# docker-arlogif
Docker and script to generate animated GIFs of periodic snapshots from Arlo cameras

## Usage
```
docker create \
  --name=arlogif \
    -v <path to config>:/script/cfg \
    -v <path to snapshots>:/script/raw \
    -v <path to gifs>:/script/gif \
  empeee/arlogif
```

## Configuration
Example config.yaml
```
username: arlo_username
password: arlo_password
camera_names:
  - Kitchen
  - Front_Door
  - Garage
gif_path: ./gif/
snapshot_path: ./raw/
purge_duration_hours: 24
gif_frame_seconds: 0.25
```

username - (required) Arlo login username.
password - (required) Arlo login password.
camera_names - (optional) List of camera names. This will check against what is available from Arlo. If it is not provided it will collect images for all available cameras in Arlo.
gif_path - (optional) Path to gifs. Defaults to ```./gif/```.
snapshot_path - (optional) Path to raw snapshots. Defuaults to ```./raw/```.
purge_duration_hours - (optional) How long in hours to keep old snapshots. Default 24.
gif_grame_seconds - (optional) Duration of a single frame in resulting GIF. Defaul 0.25.
