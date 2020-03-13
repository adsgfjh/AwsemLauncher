import os
import sys
import errno
import subprocess as sp
import shutil
from abc import ABCMeta, abstractmethod

class AwsemLauncher:
    __metaclass__ = ABCMeta
    
    pbs_template = '''#!/bin/bash
        #PBS -N %s
        #PBS -j oe
        #PBS -q alphaq
        #PBS -l %s
        
        cd $PBS_O_WORKDIR
        
        %s
        '''
    
    @abstractmethod
    def modify_parameters(self, ijob, ifolder):
        # do whatever operations here such as modify parameters in the input file
        pass
    
    def run(self):
        # create project folder
        project_folder = os.path.join(self.work_dir, self.project_name)
        if self.run_id == 1:
            self.create_folder(project_folder, overwrite=self.overwrite)
        
        for i in range(self.njobs):
            # create work folder
            ifolder = os.path.join(project_folder, self.project_name + '_%02d' % i, 'run_%02d' % self.run_id)
            self.create_folder(ifolder, overwrite=self.overwrite)
            # copy files to work folder & modify if necessary
            self.prepare_file_in_workdir(ifolder)
            # modify parameter files
            self.modify_parameters(i, ifolder)
            # create submit file
            self.create_pbs_file(ifolder)
            # submit
            self.submit(ifolder, self.submit_file, self.test_submit)
    
    def prepare_file_in_workdir(self, work_dir):
        for ifile in self.copy_files:
            if os.path.isdir(ifile):
                self.copy_from_file_to(os.path.join(self.current_dir, ifile), '*', work_dir)
            else:
                self.copy_from_file_to(self.current_dir, ifile, work_dir)
        if self.run_id > 1:
            self.restart_setting(self.unfold, work_dir, self.input_file)
        else:
            pass
    
    def restart_setting(self, unfold, ifolder, inputfile):
        self.modify_file(ifolder, 'read_data', '#read_data' , inputfile)
        prev = ifolder.replace('run_%02d' % self.run_id, 'run_%02d' % (self.run_id-1))
        restart = os.path.join(prev, 'unfold.%s' % unfold).replace('/', '\/')
        self.modify_file(ifolder, '#read_restart unfold.100', 'read_restart ' + restart, inputfile)
        self.modify_file(ifolder, 'minimize', '#minimize', inputfile)
    
    def create_pbs_file(self, ifolder):
        # pbs nodes
        self.modify_pbs_nodes(self.submit_nodes, self.submit_ppn)
        # pbs cmd
        self.modify_pbs_cmd(ifolder, self.submit_cmd)
        # create pbs file in ifolder
        self.submit_file = os.path.join(ifolder, self.project_name + '.pbs')
        with open(self.submit_file, 'w') as f:
            f.write(self.pbs_template % (self.project_name, self._pbs_nodes, self._pbs_cmd))

    def modify_pbs_cmd(self, ifolder, cmd):
        pre_cmd = 'cd %s && ' % ifolder
        self._pbs_cmd = (pre_cmd + cmd)

    def modify_pbs_nodes(self, node, ppn):
        """ node and ppn could be either int or list of int """
        #PBS -l nodes=node2:ppn=40  <= node = 2, ppn = 40
        #PBS -l nodes=node2:ppn=40+node1:ppn=20  <= node = [2, 1], ppn = [40, 20]
        pre_s = 'nodes='
        s = lambda node, ppn: 'node%s:ppn=%s' % (node, ppn)
        if isinstance(node, int) & isinstance(ppn, int):
            self._pbs_nodes = pre_s + s(node, ppn)
        elif isinstance(node, list) & isinstance(ppn, list):
            if len(node) != len(ppn):
                raise ValueError('len(node) must equal len(ppn).')
            l = []
            for i in range(len(node)):
                l.append(s(node[i], ppn[i]))
            self._pbs_nodes = pre_s + '+'.join(l)
        else:
            raise TypeError('node and ppn must be either integers or list of integers.')

    def submit(self, run_dir, submit_file, test):
    	""" Go to {run_dr} and then submit """
        cmd = 'cd %s && qsub %s' % (run_dir, submit_file)
        if test:
            self._print('test submit: ')
            self._print(cmd)
        else:
            self.run_subprocess(cmd)

    @staticmethod
    def modify_file(path, str_a, str_b, filename=None):
        f = path if filename is None else os.path.join(path, filename)
        if not os.path.exists(f):
            raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), f)
        cmd = "sed -i 's/%s/%s/' %s" % (str_a, str_b, f)
        AwsemLauncher.run_subprocess(cmd)
    
    @staticmethod
    def run_subprocess(cmd):
        proc = sp.Popen(cmd, shell=True, stdout=sp.PIPE)
        pout, perr = proc.communicate()
        if perr:
            print(perr)

    @staticmethod
    def create_folder(folder_path, overwrite=False):
        if os.path.exists(folder_path):
            if overwrite:
                shutil.rmtree(folder_path)
                os.makedirs(folder_path)
            else:
                print('Stop to prevent potential overwriting.')
                raise OSError('%s already exists.' % folder_path )
        else:
            os.makedirs(folder_path)

    @staticmethod
    def copy_from_file_to(path_from, files, path_to):
        if not isinstance(files, (str, list)):
            raise TypeError('Input files must be a string or a list of strings.')
        if isinstance(files, str):
            files = [files]
        for ifile in files:
            copy_ifile = os.path.join(path_from, str(ifile))
            cmd = 'cp -r %s %s' % (copy_ifile, path_to)
            AwsemLauncher.run_subprocess(cmd)

    def _print(self, msg, verbose=None):
        v = self.verbose if verbose is None else verbose
        if v:
            print(msg)
