import os.path
import re
import mod_pbxproj
import xml.etree.ElementTree

class Project:

    @classmethod
    def Load(cls, path):

        if not os.path.exists(path):
            raise Exception("No such file " + path)

        if path.endswith('/') or path.endswith('\\'):
            path = path[0:-1]

        root, ext = os.path.splitext(path)

        if ext == '.xcodeproj':
            return XcodeProj.Load(os.path.join(path, "project.pbxproj"))
        elif ext == '.pbxproj':
            return XcodeProj.Load(path)
        elif ext == '.vcxproj':
            return VCXProj.Load(path)
        elif ext == '.sln':
            return Sln.Load(path)
        else:
            raise Exception("Unsupported project type (" + ext + ")")

    def _list_repr(self, array, sep=';'):
        str = array[0]
        for s in array[1:]:
            str = str + sep + s
        return str


class XcodeProj(Project):

    def __init__(self, impl):
        self.impl = impl
        self.parents = {}
        groups = impl.objects.get_objects_in_section(u'PBXGroup')
        for group in groups:
            for id in group.children:
                self.parents[id] = group

    @classmethod
    def Load(cls, path):
        impl = mod_pbxproj.XcodeProject.load(path)
        return XcodeProj(impl)

    def get_parent(self, obj):
        id = obj.get_id()
        if id in self.parents:
            return self.parents[id]
        return None

    def find_referenced_project(self, targetName):
        for proxy in self.impl.objects.get_objects_in_section(u'PBXContainerItemProxy'):
            if proxy.remoteInfo == targetName:
                fileRef = self.impl.get_object(proxy.containerPortal)
                path = self._resolve_path(fileRef)
                return mod_pbxproj.XcodeProject.load(os.path.join(path, "project.pbxproj"))
        return None

    def get_target_source_files(self, target):
        for id in target.buildPhases:
            buildPhase = self.impl.get_object(id)
            if buildPhase.isa == 'PBXSourcesBuildPhase':
                for f in buildPhase.files:
                    buildFile = self.impl.get_object(f)
                    fileRef = self.impl.get_object(buildFile.fileRef)
                    yield fileRef

    def get_group_files(self, group):
        for id in group.children:
            item = self.impl.get_object(id)
            if item.isa == 'PBXGroup':
                for f in self.get_group_files(item):
                    yield f
            else:
                yield item

    def _get_object_path(self, obj):
        if obj and u'path' in obj:
            return obj.path
        return None

    def resolve_path(self, fileRef, directory=None):
        path = self._resolve_path(fileRef)
        path = os.path.realpath(path)
        return os.path.relpath(path, directory)

    def _resolve_path(self, fileRef):
        sourceTree = fileRef.sourceTree
        path = self._get_object_path(fileRef)
        if sourceTree == '<absolute>':
            return path
        elif sourceTree == '<group>':
            group = self.get_parent(fileRef)
            groupPath = self._get_object_path(group)
            while not groupPath and group:
                group = self.get_parent(group)
                groupPath = self._get_object_path(group)
            if groupPath is not None:
                groupPath = os.path.join(self.impl._source_root, groupPath)
                return os.path.join(groupPath, path)
            else:
                return os.path.join(self.impl._source_root, path)
        elif sourceTree == 'SOURCE_ROOT':
            return os.path.join(self.impl._source_root, path)
        else:
            raise Exception("Unsupport sourceTree " + sourceTree)

    def get_file_groups(self, fileRef, rootGroup):
        groups = []
        group = self.get_parent(fileRef)
        while group and group != rootGroup:
            groups.insert(0, group.get_name())
            group = self.get_parent(group)
        return groups

    def get_target_group(self, targetName):
        groups = self.impl.get_groups_by_name(targetName)
        for group in groups:
            parent = self.get_parent(group)
            if not (parent and u'name' in parent):
                return group
        return None

    def list_files(self, targetName, directory=os.curdir):

            project = self.impl

            # get the target
            target = project.get_target_by_name(targetName)
            if not target:
                project = self.find_referenced_project(targetName)
                if not project:
                    raise Exception("no such target " + targetName)
                XcodeProj(project).list_files(targetName, directory)
                return

            # get the corresponding group: a group with the name of the target at the root of the project
            target_group = self.get_target_group(targetName)
            if not target_group:
                raise Exception("can't find target group for " + targetName)

            groups = {}

            # get build files from target
            buildSourceFiles = [f for f in self.get_target_source_files(target)]
            buildSourceFilePaths = []
            for f in buildSourceFiles:
                p = self.resolve_path(f, directory)
                buildSourceFilePaths.append(p)
                groups[p] = self.get_file_groups(f, target_group)
            buildSourceFilePaths.sort()

            # get other referenced files from group
            if target_group:
                otherReferenceFiles = [f for f in self.get_group_files(target_group) if not f in buildSourceFiles]
            else:
                otherReferenceFiles = []
            otherReferenceFilePaths = []
            for f in otherReferenceFiles:
                p = self.resolve_path(f, directory)
                otherReferenceFilePaths.append(p)
                groups[p] = self.get_file_groups(f, target_group)
            otherReferenceFilePaths.sort()

            # list the files
            print "===== BUILD SOURCE FILES:"
            for p in buildSourceFilePaths:
                print '{0}\t{1}'.format(p, self._list_repr(groups[p]))
            print "===== OTHER REFERENCED FILES:"
            for p in otherReferenceFilePaths:
                print '{0}\t{1}'.format(p, self._list_repr(groups[p]))

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
            print '{0}\t{1}'.format(p, self._list_repr(groups[p]))
        print "===== OTHER REFERENCED FILES:"
        for p in otherReferenceFilePaths:
            print '{0}\t{1}'.format(p, self._list_repr(groups[p]))

class Sln(Project):

    def __init__(self, path):
        self.path = path
        self._parse()

    @classmethod
    def Load(cls, path):
        return Sln(path)

    def _parse(self):
        self.projects = {}
        f = open(self.path, 'r')
        while True:
            line = f.readline()
            if not line:
                break
            if line.startswith('Project('):
                eq = line.index(" = ")
                rhs = line[(eq+3):]
                args = rhs.split(", ")
                name = args[0][1:-1]
                path = args[1][1:-1].replace('\\', '/')
                if path.endswith('.vcxproj'):
                    self.projects[name] = path

    def list_files(self, targetName, directory = os.curdir):

        if not targetName in self.projects:
            raise Exception("no such target " + targetName)

        dir = os.path.dirname(self.path)
        path = os.path.join(dir, self.projects[targetName])

        VCXProj.Load(path).list_files(targetName, directory)
