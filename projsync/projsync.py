import os.path
import re
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

    def list_files(self, targetName, directory=os.curdir):

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

    def __init__(self, path, project, filters, ns = '{http://schemas.microsoft.com/developer/msbuild/2003}'):
        self.path = path
        self.source_root = os.path.dirname(path)
        self.project = project
        self.filters = filters
        self.ns = ns
        if project.getroot().tag != self._add_ns('Project'):
            raise Exception("Invalid Visual Studio Project " + path)
        if filters.getroot().tag != self._add_ns('Project'):
            raise Exception("Invalid Visual Studio Project " + path)

    @classmethod
    def Load(cls, path):
        project = xml.etree.ElementTree.parse(path)
        filters = xml.etree.ElementTree.parse(path + ".filters")
        return VCXProj(path, project, filters)

    def _add_ns(self, xpath):
        newxpath, nsubst = re.subn('(^|/)([a-zA-Z_0-9]+)', '\\1' + self.ns + '\\2', xpath)
        return newxpath

    def resolve_path(self, path, directory=os.curdir):
        path = os.path.join(self.source_root, path.replace('\\', '/'))
        path = os.path.realpath(path)
        path = os.path.relpath(path, directory)
        return path

    def list_files(self, targetName, directory = os.curdir):

        project = self.project
        filters = self.filters
        ns = self.ns

        p = filters.getroot()


        groups = {}

        # get build source files
        buildSourceFilePaths = []
        for f in p.findall(self._add_ns('ItemGroup/ClCompile')):
            path_ = f.get('Include')
            path = self.resolve_path(path_, directory)
            buildSourceFilePaths.append(path)
            g = f.findtext(self._add_ns('Filter')).split('\\')
            groups[path] = g
        buildSourceFilePaths.sort()

        # get other referenced files
        otherReferenceFilePaths = []
        otherReferenceFileGroups = {}
        for f in p.findall(self._add_ns('ItemGroup/ClInclude')):
            path_ = f.get('Include')
            path = self.resolve_path(path_, directory)
            otherReferenceFilePaths.append(path)
            g = f.findtext(self._add_ns('Filter')).split('\\')
            groups[path] = g
        for f in p.findall(self._add_ns('ItemGroup/None')):
            path_ = f.get('Include')
            path = self.resolve_path(path_, directory)
            otherReferenceFilePaths.append(path)
            g = f.findtext(self._add_ns('Filter')).split('\\')
            groups[path] = g
        otherReferenceFilePaths.sort()

        # list the files
        print "===== BUILD SOURCE FILES:"
        for p in buildSourceFilePaths:
            print '{0}\t{1}'.format(p, groups[p])
        print "===== OTHER REFERENCED FILES:"
        for p in otherReferenceFilePaths:
            print '{0}\t{1}'.format(p, groups[p])
