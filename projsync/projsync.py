import os.path
import mod_pbxproj
import xml.etree.ElementTree

class Project:

    @classmethod
    def Load(cls, path):

        if not os.path.exists(path):
            raise Exception("No such file " + path)

        root, ext = os.path.splitext(path)

        if ext == '.xcodeproj':
            return XcodeProj.Load(os.path.join(path, "project.pbxproj"))
        elif ext == '.pbxproj':
            return XcodeProj.Load(path)
        elif ext == '.vcxproj':
            return VCXProj.Load(path)
        else:
            raise Exception("Unsupported project type (" + ext + ")")


class XcodeProj(Project):

    def __init__(self, impl):
        self.impl = impl

    @classmethod
    def Load(cls, path):
        impl = mod_pbxproj.XcodeProject.Load(path, pure_python=True)
        return XcodeProj(impl)

    def list_files(self, targetName, directory = None):

            project = self.impl

            # get the target
            targets = project.get_targets_by_name(targetName)
            if len(targets) < 1:
                raise Exception("No such target " + targetName)
            elif len(targets) > 1: # is this possible?
                raise Exception("Ambiguous target " + targetName)
            target = targets[0]

            # get the corresponding group, if there is one and only one group
            # with the name of the target
            groups = project.get_groups_by_name(targetName)
            if len(groups) == 1:
                group = groups[0]
            else:
                group = None

            # get build files from target
            buildSourceFiles = [f for f in project.get_target_source_files(target)]
            buildSourceFilePaths = []
            for f in buildSourceFiles:
                buildSourceFilePaths.append(project.resolve_path(f, directory))
            buildSourceFilePaths.sort()

            # get other referenced files from group
            if group:
                otherReferenceFiles = [f for f in project.get_group_files(groups[0]) if not f in buildSourceFiles]
            else:
                otherReferenceFiles = []
            otherReferenceFilePaths = []
            for f in otherReferenceFiles:
                otherReferenceFilePaths.append(project.resolve_path(f, directory))
            otherReferenceFilePaths.sort()

            # list the files
            print "===== BUILD SOURCE FILES:"
            for p in buildSourceFilePaths:
                print p
            print "===== OTHER REFERENCED FILES:"
            for p in otherReferenceFilePaths:
                print p

class VCXProj(Project):

    def __init__(self, path, tree, ns = '{http://schemas.microsoft.com/developer/msbuild/2003}'):
        self.path = path
        self.source_root = os.path.dirname(path)
        self.tree = tree
        self.ns = ns

    @classmethod
    def Load(cls, path):
        tree = xml.etree.ElementTree.parse(path)
        project = tree.getroot()
        if project.tag != '{http://schemas.microsoft.com/developer/msbuild/2003}Project':
            raise Exception("Invalid Visual Studio Project " + path)
        return VCXProj(path, tree)

    def resolve_path(self, path, directory = None):
        path = os.path.join(self.source_root, path.replace('\\', '/'))
        path = os.path.realpath(path)
        path = os.path.relpath(path, directory)
        return path

    def list_files(self, targetName, directory = None):

        project = self.tree.getroot()
        ns = self.ns

        # get build source files
        buildSourceFilePaths = []
        for f in project.findall(ns+'ItemGroup/'+ns+'ClCompile'):
            path = f.get('Include')
            if path:
                buildSourceFilePaths.append(self.resolve_path(path, directory))
        buildSourceFilePaths.sort()

        # get other referenced files
        otherReferenceFilePaths = []
        for f in project.findall(ns+'ItemGroup/'+ns+'ClInclude'):
            path = f.get('Include')
            if path:
                otherReferenceFilePaths.append(self.resolve_path(path, directory))
        for f in project.findall(ns+'ItemGroup/'+ns+'None'):
            path = f.get('Include')
            if path:
                otherReferenceFilePaths.append(self.resolve_path(path, directory))
        otherReferenceFilePaths.sort()

        # list the files
        print "===== BUILD SOURCE FILES:"
        for p in buildSourceFilePaths:
            print p
        print "===== OTHER REFERENCED FILES:"
        for p in otherReferenceFilePaths:
            print p
