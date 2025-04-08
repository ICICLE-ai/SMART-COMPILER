import os

class FolderTree:
    def __init__(self, startpath):
        self.startpath = startpath
        self.tree = self.folder_tree_array(startpath)

    def folder_tree_array(self, path):
        tree = []
        for entry in os.scandir(path):
            current_parent = os.path.dirname(path)
            if entry.is_dir():
                tree.append({
                    'name': entry.name,
                    'type': 'directory',
                    'path': entry.path,
                    'parent': current_parent,
                    'children': self.folder_tree_array(entry.path)
                })
            else:
                tree.append({
                    'name': entry.name,
                    'type': 'file',
                    'path': entry.path,
                    'parent': current_parent
                })
        return tree

    def get_tree(self):
        return self.tree

    def find_file(self, filename, tree=None):
        if tree is None:
            tree = self.tree

        for item in tree:
            if item['type'] == 'file' and item['name'] == filename:
                return item
            elif item['type'] == 'directory':
                found = self.find_file(filename, item['children'])
                if found:
                    return found
        return None

    def list_files(self, tree=None, prefix=''):
        if tree is None:
            tree = self.tree
        files_list = []

        for item in tree:
            if item['type'] == 'file':
                files_list.append(f"{prefix}{item['name']}")
            elif item['type'] == 'directory':
                files_list.extend(self.list_files(item['children'], prefix=f"{prefix}{item['name']}/"))

        return files_list

