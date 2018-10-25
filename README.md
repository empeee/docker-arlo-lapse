# docker-arlo-lapse
Docker and script to generate video of periodic snapshots from Arlo cameras

## Usage
```
docker create \
  --name=arlo-lapse \
    -v <path to config>:/app/cfg \
    -v <path to snapshots>:/app/raw \
    -v <path to lapse>:/app/lapse \
  empeee/arlo-lapse
```

## Configuration
```
# Example config.yaml

username: arlouser
password: supersecretpassword
camera_names:
  - Kitchen
  - Front_Door
  - Garage
lapse_path: ./lapse/
snapshot_path: ./raw/
purge_duration_hours: 24
lapse_duration: 10
```

- username - (required) Arlo login username.
- password - (required) Arlo login password.
- camera_names - (optional) List of camera names. This will check against what is available from Arlo. If it is not provided it will collect images for all available cameras in Arlo.
- lapse_path - (optional) Path to lapses. Defaults to ```./lapse/```.
- snapshot_path - (optional) Path to raw snapshots. Defuaults to ```./raw/```.
- purge_duration_hours - (optional) How long in hours to keep old snapshots. Default 24.
- lapse_duration - (optional) Duration of the resulting video. Defaul 10.
