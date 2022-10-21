# opsdroid connector ICQ

A connector for [opsdroid](https://github.com/opsdroid/opsdroid) to send messages using [ICQ](https://icq.com/).

## Requirements

You need to [register a bot](https://icq.com/botapi/?lang=en) on ICQ and get an api token for it.

## Configuration

```yaml
connectors:
  icq:
    # required
    token: "some-token"  # bot token
    base-url: "api.icq.net/bot/v1/" # bot-api base url
```

## How to start

```commandline
./startup --help
```

output should be as follows:

```
Starting...
Got parameters:
IMAGE_NAME=opsdroid-demo
HOST=0.0.0.0
PORT_IN=8080
PORT_OUT=8080
PATH_TO_DOCKERFILE=bot/.


    IMAGE_NAME=opsdroid-demo     HOST=0.0.0.0     PORT_IN=8080     PORT_OUT=8080     PATH_TO_DOCKERFILE=bot/.     (<- параметры опционально)
    ./startup.sh (запустить opsdroid и бота)
                --help      shows help
                --build     builds container
                --run       runs container
                --runbg     runs container in background
                --cli       runs container with interactive cli (bash)
                --stop      stops running docker container
                --remove    removes container
                --list      shows available docker containers
                --ps        show running containers
```

Then you can build an image with specified name

```commandline
IMAGE_NAME="my_opsdroid_icq" ./startup --build
```

output should be as follows:

```
Starting...
Got parameters:
IMAGE_NAME=my_opsdroid_icq
HOST=0.0.0.0
PORT_IN=8080
PORT_OUT=8080
PATH_TO_DOCKERFILE=bot/.

Start building...
Sending build context to Docker daemon  9.216kB
Step 1/3 : FROM opsdroid/opsdroid:dev
 ---> c0f0c1105221
Step 2/3 : COPY configuration.yaml /etc/opsdroid/configuration.yaml
 ---> 930615cb012b
Step 3/3 : COPY skills /opt/opsdroid/skills
 ---> a091191f152a
Successfully built a091191f152a
Successfully tagged my_opsdroid_icq:latest
```

or something else if you modified the Dockerfile and/or passed any other parameters to script

next you can run opsdroid with your bot (skill/s) in the background

```commandline
IMAGE_NAME="my_opsdroid_icq" ./startup --runbg
```

output should be as follows:

```
Starting...
Got parameters:
IMAGE_NAME=my_opsdroid_icq
HOST=0.0.0.0
PORT_IN=8080
PORT_OUT=8080
PATH_TO_DOCKERFILE=bot/.

Start running in background...
b6ad132785238462f3863e532cb6afc08a801957d3d4e17ee1046f7c5a25394f
```

when you'll decide to stop background running container, you should stop it

```commandline
IMAGE_NAME="my_opsdroid_icq" ./startup --stop
```

output should be as follows:

```
Starting...
Got parameters:
IMAGE_NAME=opsdroid-demo
HOST=0.0.0.0
PORT_IN=8080
PORT_OUT=8080
PATH_TO_DOCKERFILE=bot/.

Trying to stop...
charming_clarke
```

where `charming_clarke` - is a temporary name of stopped container
