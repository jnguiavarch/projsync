import os
import argparse
import projsync

def list_files(args, options):

    parser = argparse.ArgumentParser("List referenced files.")
    parser.add_argument('project', help='The project path')
    parser.add_argument('target', help='The target name')
    aa = parser.parse_args(args)

    if options.directory == None:
        directory = os.curdir
    else:
        directory = options.directory

    proj = projsync.Project.Load(aa.project)
    proj.list_files(aa.target, directory)

def main():

    parser = argparse.ArgumentParser("Manipulate projects in various formats.")
    parser.add_argument('command', help='The command to execute', choices=['list-files'])
    parser.add_argument('args', help='The command arguments', nargs=argparse.REMAINDER)
    parser.add_argument('-C', '--directory', help='The start directory for relpath', action='store')
    aa = parser.parse_args()

    if aa.command == 'list-files':
        list_files(aa.args, aa)
    else:
        raise Exception('Unsupported command ' + aa.command)


if __name__ == "__main__":
    main()
