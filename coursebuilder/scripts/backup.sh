#!/bin/bash
#
# Usage:
#
# Run this script from the Course Builder folder. It can be run with the
# following arguments:
#
# Without specifying a server
#     sh ./scripts/backup.sh course_name remote_repository
#
# Specifying a server
#     sh ./scripts/backup.sh course_name remote_repository server_name
#

# Check if course name is appended by /
# If yes remove / and assign to variable

if [ ${1:0:1} == '/' ]; then
  course=$(echo $1| cut -d'/' -f 2)

# If not, assign to variable
else
  course=$1
fi

# Create Folder name for downloaded course
folder=$course'-course.zip'

# If no server is provided, use default server
# i.e courses.academy.africa
# else use specified server
# Remove appended http:// or https://

if [ $# == 2 ]; then
  server='courses.academy.africa'
elif [ $# == 3 ]; then
  if [ ${3:0:7} == 'http://' ]; then
    server=$(echo $3| cut -c8-)
  elif [ ${3:0:8} == 'https://' ]; then
    server=$(echo $3| cut -c9-)
  else
    server=$3
  fi
fi

# Download course
sh scripts/etl.sh download course /$course $server --archive_path ./$folder
echo $course downloaded as $folder

# Clone Repository
git clone $2

# Get Folder Name of Cloned Repository
base=$(basename "$2" .deb)
repo="${base%%.git}"

# Move Downloaded Course to Cloned Repository and Navigate to it
mv ./$folder ./$repo
cd $repo

# Stage, Commit and Push Changes
git add $folder
git commit -m "backup course $course"
git push -u origin master

# Navigate and Remove Cloned Repository
cd ../
rm -rf $repo

