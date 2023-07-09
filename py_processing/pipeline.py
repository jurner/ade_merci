# execute all scripts
scripts = ["./01_get_staypoints.py", "./02_get_triplegs.py",
           "./03_get_camera_animation.py", "./04_get_names.py",
           "./05_get_gaps.py", "./06_get_weekly_data.py"]
for script in scripts:
    print('*********** started execution of {}'.format(script))
    with open(script) as f:
        exec(f.read())
