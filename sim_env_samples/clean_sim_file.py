import shutil
import os


def main():
    for curdirname, dirnames, filenames in os.walk('.'):
        for dirname in dirnames:
            if 'simulation_' in dirname and os.path.split(curdirname)[1] in dirname:
                target_path = os.path.join(curdirname, dirname)
                print(f'Remove {target_path}')
                shutil.rmtree(target_path)


if __name__ == '__main__':
    main()
