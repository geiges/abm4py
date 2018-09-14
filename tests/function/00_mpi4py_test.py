#!/usr/bin/env python
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Program: mpi4py_test.py
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
import mpi4py
mpi4py.rc.threads = False
from mpi4py import MPI


nproc = MPI.COMM_WORLD.Get_size()   # Size of communicator
iproc = MPI.COMM_WORLD.Get_rank()   # Ranks in communicator
inode = MPI.Get_processor_name()    # Node where this MPI process runs

if iproc == 0: 
    print("This code is a test for mpi4py.")
MPI.COMM_WORLD.Barrier()
tmp = [iproc]*nproc

if iproc == 0:
    print(len(tmp))

for i in range(0,nproc):
    MPI.COMM_WORLD.Barrier()
    if iproc == i:
        print('Rank %d out of %d' % (iproc,nproc))
MPI.COMM_WORLD.alltoall(tmp)

MPI.COMM_WORLD.Barrier()
if iproc == 0:
    print('mpi4p interface test successful')


MPI.Finalize()

