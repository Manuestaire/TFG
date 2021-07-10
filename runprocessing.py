import subprocess
from multiprocessing.pool import Pool, ThreadPool
import time
import os

import contextlib
import sys

class DummyFile(object):
    def write(self, x): pass

@contextlib.contextmanager
def nostdout():
    save_stdout = sys.stdout
    sys.stdout = DummyFile()
    yield
    sys.stdout = save_stdout

def multiprocess(games=500):
    
    concurent_process=8
    p = [None]*concurent_process
    files = [None]*concurent_process
    for j in range(int(round(games/concurent_process,0))):
        # print("batch:"+str(j))
        for i in range(concurent_process):
            # files[i]=open('log'+str(i),'w')
            try:
                # p[i]=subprocess.Popen(["python","smp.py"],stdout=files[i],stderr=files[i])
                p[i]=subprocess.Popen(["python","smp.py"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                time.sleep(0.01)
            except Exception as e:
                print("EXCEPTION: "+e)
            # else:
            #     print("Finished RUN")
        status = [None]*concurent_process
        # while None in status:
        #     for i in range(concurent_process):
        #         print('process '+str(i)+': '+str(status[i]))
        #         status[i]=p[i].poll()
        #     time.sleep(5)
        for process in p:
            process.wait()

def multiprocess2(games=500):
    
    tp=ThreadPool(min(8,os.cpu_count()))
    for j in range(games):
        tp.apply_async(openSubprocess)
    tp.close()
    tp.join()
    
def multiprocess3(games=1000):

    tp=ThreadPool(min(8,os.cpu_count()))
    tp.imap_unordered(openSubprocess,range(games))
    tp.close()
    tp.join()
        

def openSubprocess(i=None):
    process=subprocess.Popen(["python","smp.py"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    process.wait(40)

def rungame(unused):
    from smp import main as game
    with nostdout():
        game(None)

def singleprocess():
    for i in range(50):
        try:
            out = subprocess.run("python smp.py", check=True, shell=False)
            print(out)
        except Exception as e:
            print("EXCEPTION: "+e)
    else:
        print("Finished RUN")