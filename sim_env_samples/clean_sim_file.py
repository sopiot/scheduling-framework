import shutil
import os


def main():
    for root, dirs, files in os.walk('.'):
        for dirname in dirs:
            if 'simulation_' in dirname and os.path.split(root)[1] in dirname:
                target_path = os.path.join(root, dirname)
                print(f'Remove {target_path}')
                shutil.rmtree(target_path)


if __name__ == '__main__':
    main()
