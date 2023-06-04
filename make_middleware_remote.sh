#!/bin/bash

function download_middleware_remote() {
  PASSWORD=$1
  PORT=$2
  USER=$3
  REMOTE_IP=$4
  middleware_name=$5

  sshpass -p $PASSWORD scp -P $PORT -r $USER@$REMOTE_IP:~/Workspace/middleware/src/middleware/sopiot_middleware ~/Workspace/simulation-framework/bin/$middleware_name
}

function build_middleware_remote() {
  PASSWORD=$1
  PORT=$2
  USER=$3
  REMOTE_IP=$4
  middleware_name=$5

  middleware_build_command=$(
    cat << EOF
cd ~
cd Workspace/middleware
git pull
make clean
make -j

if test -f "src/middleware/sopiot_middleware"; then
    echo "make middleware on $REMOTE_IP:$PORT success"
else
    echo "make middleware on $REMOTE_IP:$PORT fail"
fi

EOF
  )

  sshpass -p $PASSWORD ssh -p $PORT $USER@$REMOTE_IP "$middleware_build_command"
  download_middleware_remote $PASSWORD $PORT $USER $REMOTE_IP $middleware_name
}

build_middleware_remote "thsxogud1" 33333 "thsvkd" "147.46.114.222" "sopiot_middleware_ubuntu2204_x64"
build_middleware_remote "thsxogud1" 33333 "thsvkd" "147.46.125.84" "sopiot_middleware_ubuntu2004_x64"
build_middleware_remote "/PeaCE/" 22 "pi" "192.168.0.7" "sopiot_middleware_pi_x86"
