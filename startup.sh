#!/usr/bin/env bash
##
## Run opsdroid core with specified in Dockerfile connectors and skills
##

# Only allocate tty if one is detected
# Keep STDIN open even if not attached
if [[ -t 0 ]]; then IT+=(-i); fi
# Allocate a pseudo-tty
if [[ -t 1 ]]; then IT+=(-t); fi


IMAGE_NAME="${IMAGE_NAME:-"opsdroid-demo"}"
HOST="${HOST:-"0.0.0.0"}"
PORT_IN="${PORT_IN:-"8080"}"
PORT_OUT="${PORT_OUT:-"8080"}"
PATH_TO_DOCKERFILE=${PATH_TO_DOCKERFILE:-"bot/."}


echo "Starting..."
echo "Got parameters:"
echo "IMAGE_NAME=${IMAGE_NAME}"
echo "HOST=${HOST}"
echo "PORT_IN=${PORT_IN}"
echo "PORT_OUT=${PORT_OUT}"
echo "PATH_TO_DOCKERFILE=${PATH_TO_DOCKERFILE}"
echo

function showHelp() {
    echo "
    IMAGE_NAME="opsdroid-demo" \
    HOST="0.0.0.0" \
    PORT_IN="8080" \
    PORT_OUT="8080" \
    PATH_TO_DOCKERFILE="bot/." \
    (<- параметры опционально)
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
    "
}

function buildDocker() {
    echo "Start building..."
    sudo docker build -t $IMAGE_NAME $PATH_TO_DOCKERFILE
}

function runDocker() {
    echo "Start running..."
    sudo docker run --rm "${IT[@]}" -p $HOST:$PORT_IN:$PORT_OUT $IMAGE_NAME
}

function runDockerInBackground() {
    echo "Start running in background..."
    sudo docker run --rm "${IT[@]}" -p $HOST:$PORT_IN:$PORT_OUT -td $IMAGE_NAME
}

function stopDocker() {
   echo "Trying to stop..."
   sudo docker stop $(sudo docker ps | grep $IMAGE_NAME | awk 'NF>1{print $NF}')
}

function removeDocker() {
   echo "Trying to remove..."
   sudo docker rmi -f $(sudo docker images | grep $IMAGE_NAME | awk '{print $3}')
}

function listImages() {
   echo "List docker images"
   sudo docker images
}

function showRunningContainers() {
   echo "List docker containers"
   sudo docker ps
}


while :; do
    case $1 in
        --help)
            showHelp
            exit
            ;;
        --build)
            buildDocker
            ;;
        --run)
            runDocker
            ;;
        --runbg)
            runDockerInBackground
            ;;
        --stop)
            stopDocker
            ;;
        --remove)
            removeDocker
            ;;
        --list)
            listImages
            ;;
        --ps)
            showRunningContainers
            ;;
        --)
            shift
            break
            ;;
        -?*)
            printf 'WARN: Unknown option (ignored): %s\n' "$1" >&2
            ;;
        *)
            break
    esac

    shift
done
