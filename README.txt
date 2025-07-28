INSTALATION:

1.) Download python from https://www.python.org/ftp/python/3.13.5/python-3.13.5-amd64.exe
2.) If you already have any version of Python on your PC, uninstall it to avoid conflicts.
3.) Install python -  follow steps in video 01_python_install.mp4
4.) Copy mobile_proc folder to any location on your pc
5.) Execute setup.py (video 02_python_modules_install.mp4)

RUNNING SCRIPT:

video - 03_running_script.mp4

1.) Copy raw .csv files from datalogger to mobile_proc/raw directory
2.) Execute run_processing.py script
3.) Script will create structured folder in /output directory and place generated outputs into separate folder (separated for each datalogger ser. number and csv file name)
4.) To edit color range for html data visualization, simply add desired color min and max leved to first row in csv file (this step is shown at the end of 03_running_script.mp4 )
