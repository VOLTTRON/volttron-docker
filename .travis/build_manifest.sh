#!/bin/bash

usage() {
    echo -e "Usage: $0 \n"\
        "    -a architecture (name of an architecture annotcation to add to the manifest\n"\
        "\n"\
        "Creates a docker manifest with a provided name and tag (-n) from a\n"
        "set of images for different architectures. Each image is expected\n"
        "to have the same name and tag, with the tag suffixed by '-<arch>'\n"
        "where <arch> is the docker-recognized name of the architecture\n"
        ""
    exit 2
}

if [[ $1 == "" ]]; then
  usage
fi

architectures=""
manifest_name=""

# parse the arguments
while getopts a:n: option ; do
  case $option in
    a) # store architectures
      if [[ $OPTARG == "" ]]; then
        echo "architecture flag requries a value"
        exit 2
      fi
      architectures="$architectures $OPTARG"
      ;;
    n) # store the manifest name (image & tag)
      if [[ $OPTARG == "" ]]; then
        echo "name flag requries a value"
        exit 2
      fi
      manifest_name=$OPTARG
      ;;
    *)
      usage
      ;;
  esac
done

# check required flags were received
if [[ $manifest_name == "" ]]; then
  echo "the name flag is required"
  usage
fi
if [[ $architectures == "" ]]; then
  echo "at least one architecture must be passed with the -a flag"
  usage
fi

# build and populate the manifest
set -ex
images_list=""
for a in $architectures
do
    images_list="$images_list ${manifest_name}-${a}"
done
#echo "images list is: $images_list"
docker manifest create $manifest_name $images_list
for a in $architectures
do
    docker manifest annotate $manifest_name ${manifest_name}-${a} --arch $a
done
docker manifest push $manifest_name
set +ex
