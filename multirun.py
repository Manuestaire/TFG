import subprocess


for x in range(3):
    try:
        out = subprocess.run("python smp.py", check=True)
        print(out)
    except Exception as e:
        print("EXCEPTION: "+e)
else:
    print("Finished RUN")


