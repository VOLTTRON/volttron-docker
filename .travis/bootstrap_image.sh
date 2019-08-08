#!/bin/bash

## conventional notes
## - true comments that are not in-line start with double ## (commented out lines are single)
## - local variables are lower_snake_case (leaves UPPER_SNAKE for environment stuff)
## - echo statements that are just progress notes start with "-- "

set -o

usage() {
    echo -e "Usage: $0 \n"\
         "    -u (user portion of emulation base image specification)\n"\
         "    -r (repo portion of emulation base image specification)\n"\
         "    -t (tag portion of emulation base image specification)\n" \
         "    -i (user, repo, and base-tag of output image (arch is automatically appended)\n" \
         "    -a (desired architecture, one of [arm7, amd64])\n" \
         "    -p (desire phase, one of [build, push])\n" \
         "    -d (name of Dockerfile to build - default is Dockerfile)"
    exit 2
}

echo "-- parsing bootstrap base image options"

if [[ $1 == "" ]]; then
  usage
fi
dockerfile_path="Dockerfile"
while getopts u:r:t:i:a:p:d: option ; do
  case $option in
    u) # store user
      if [[ $OPTARG == "" ]]; then
        echo "user flag requires value"
        exit 2
      fi
      image_user="$OPTARG"
      ;;
    r) # store repo
      if [[ $OPTARG == "" ]]; then
        echo "repo flag requires value"
        exit 2
      fi
      image_repo="$OPTARG"
      ;;
    t) # store tag
      if [[ $OPTARG == "" ]]; then
        echo "tag flag requires value"
        exit 2
      fi
      image_tag="$OPTARG"
      ;;
    i) # store output repo info
      if [[ $OPTARG == "" ]]; then
        echo "output image flag requires value"
        exit 2
      fi
      output_image="$OPTARG"
      ;;
    a) # store target architecture
      if [[ $OPTARG == "" ]]; then
        echo "architecture flag requires value"
        exit 2
      fi
      if [[ "amd64 arm7" =~ (^|[[:space:]])"$OPTARG"($|[[:space:]]) ]]; then
        target_arch="$OPTARG"
      else
        echo "arch '${OPTARG}' not recognized"
        usage
      fi
      ;;
    p) # store phase
      if [[ $OPTARG == "" ]]; then
        echo "phase flag requires value"
        exit 2
      fi
      if [[ "build push" =~ (^|[[:space:]])"$OPTARG"($|[[:space:]]) ]]; then
        phase_action="$OPTARG"
      else
        echo "arch '${OPTARG}' not recognized"
        usage
      fi
      ;;
    d) # update dockerfile_path
      if [[ $OPTARG == "" ]]; then
        echo "dockerfile_path flag requires value"
        exit 2
      fi
      dockerfile_path="$OPTARG"
      ;;
    *) # print usage
      usage
      ;;
  esac
done
if [[ -z $image_user || -z $image_repo || -z $image_tag || -z $target_arch || -z $output_image ]]; then
    echo "all arguments are required"
    usage
fi

original_qemu_path=""
case $target_arch in
    amd64)
        original_qemu_path="/usr/bin/qemu-x86_64-static"
        architecture_img_suffix="amd64"
        echo "-- set qemu vars for amd64"
        ;;
    arm7)
        original_qemu_path="/usr/bin/qemu-arm-static"
        architecture_img_suffix="arm"
        echo "-- set qemu vars for arm7"
        ;;
esac

dot_travis_path=`dirname $0`
dot_travis_path=`readlink -e $dot_travis_path`

set -x

case $phase_action in
    build)
        set -e
        # bootstrap a custom base image with emulation
        cp $original_qemu_path ${dot_travis_path}/this_qemu
        sed "s#QEMU_TARGET_LOCATION#${original_qemu_path}#" $dot_travis_path/Dockerfile.shim > $dot_travis_path/Dockerfile
        docker build \
            --build-arg image_user=$image_user \
            --build-arg image_repo=$image_repo \
            --build-arg image_tag=$image_tag \
            -t local/emulation_base:latest \
            -f $dot_travis_path/Dockerfile \
            $dot_travis_path
        # build the arch-specific image on top of it
        docker build \
            --build-arg image_user=local \
            --build-arg image_repo=emulation_base \
            --build-arg image_tag=latest \
            -t ${output_image}-${architecture_img_suffix} \
            -f ${dockerfile_path} \
            .
        ;;
    push)
        docker push ${output_image}-${architecture_img_suffix}
        ;;
    *)
        echo "phase not recognized"
        usage
        ;;
esac
set +x
