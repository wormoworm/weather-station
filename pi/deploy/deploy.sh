# A deployment script that pushes the sensors program to a remote machine and then runs it.
# The stdout from the application is captured to help with debugging.

target=$1
install_dependencies=$2

dir_application=/home/pi/sensors/

printf "Running deployment script, target is $target. Will install to $dir_application. Install dependencies = $install_dependencies\n"

# 1: Copy the application to the target.
printf "Copying sensors application...\n"
scp -rq pyproject.toml requirements.txt python/ pi@$target:$dir_application

# 2: Update dependencies, if requested
if [ "$install_dependencies" = true ] ; then
    printf "Updating dependencies...\n"
    ssh pi@$target "cd $dir_application && pip3 install -r requirements.txt"
fi

# 3: Run the application
printf "Running sensors application...\n--------------------------------------------------\n"
ssh pi@$target "cd $dir_application && python3 -u python/sensors.py"