#!/usr/bin/env python

import os
import sys
sys.path.append('/work/shared/SimJobs')
from awsemjob import AwsemLauncher
import random

class MyProject(AwsemLauncher):
    """ To prepare folders, files, and submit script for your project and then submit 
	Possible extension: 
		modify file name for each simulation
		input submit file template 
	"""
    
    current_dir = os.getcwd()
    
    def __init__(self, test=True):
        # project setting
        self.overwrite = True
        self.verbose = True
        self.project_name = 'test'
        self.run_id = 1  # to control restart run
        self.unfold = 100  # only used when run_id > 1
        self.njobs = 3  # max 99
        self.work_dir = '/work/ace'
        self.exe_path = '/work/shared/awsemmd/lmp_serial_g++_12182019'
        self.input_file = 'd1_Modeller_6n3c_12.in'
        self.test_submit = test
        
        # parameter files setting in work dir
        ## copy files to work dir
	file_path = '/home/adsgfjh/Submit/'
        self.copy_files = [file_path+'test.txt', file_path+'unBias_tmpFolder']  # could be folder or file
        
        # submit file setting
        self.submit_nodes = 1  # [1, 3]
        self.submit_ppn = 40  # [10, 40]
        # modify this if needed
        self.submit_cmd = self.exe_path + ' < ' + self.input_file
        ## cd to the work dir will be added automatically
    
    
    def modify_parameters(self, ijob, ifolder):
        # To replace str_a with str_b in file, use
        # self.modify_file(path, str_a, str_b, filename=None)
        self.modify_file(ifolder, 'banana', 'apple'+str(ijob), 'test.txt')
        r = random.randint(1, 1e8)
        self.modify_file(ifolder, 'velocity all create 300.0 2349852',
                         'velocity all create 300.0 %s' % r, self.input_file)


if __name__ == '__main__':
    test = False
    if len(sys.argv) != 1:
        if 'test' in sys.argv[1:]:
            test = True

    myproject = MyProject(test=test)
    myproject.run()
