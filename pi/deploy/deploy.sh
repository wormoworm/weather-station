# A deployment script that pushes the weather-station program to a remote machine and then runs it.
# The stdout from the application is captured to help with debugging.

target=$1
install_dependencies=$2

dir_application=/home/pi/weather-station/

printf "Running deployment script, target is $target. Will install to $dir_application. Install dependencies = $install_dependencies\n"

# 1: Copy the application to the target.
printf "Copying weather-station application...\n"
scp -rq requirements.txt python/ pi@$target:$dir_application

# 2: Update dependencies, if requested
if [ "$install_dependencies" = true ] ; then
    printf "Updating dependencies...\n"
    ssh pi@$target "cd $dir_application && pip3 install -r requirements.txt"
fi

# 3: Run the application
printf "Running weather-station application...\n--------------------------------------------------\n"
ssh pi@$target "cd $dir_application && python3 -u python/weather-station.py"