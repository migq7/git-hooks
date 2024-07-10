import os
import subprocess
import datetime
import re
import argparse
import pathspec
from abc import ABC, abstractmethod

REPO_ROOT = subprocess.check_output(['git', 'rev-parse', '--show-toplevel']).strip().decode('utf-8')
AUTHOR = subprocess.check_output(['git', 'config', 'user.name']).strip().decode('utf-8')


class Tools:
    def __init__(self, repo_root_path, ignore_file_name, scope, type_list, stage_file):
        self._repo_root_path = repo_root_path
        self._ignore_file_name = ignore_file_name
        self._scope = scope
        self._type_list = type_list
        self._stage_file = stage_file

    def _get_changed_file_paths(self):
        target_files = subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=self._repo_root_path).strip().decode('utf-8').split('\n')
        return target_files

    def _get_ignore_patterns(self):
        ignore_file_list = []
        if os.path.exists(os.path.join(self._repo_root_path, self._ignore_file_name)):
            with open(os.path.join(self._repo_root_path, self._ignore_file_name), 'r') as f:
                ignore_file_list = [line.strip() for line in f if line.strip()]
        return ignore_file_list


    @abstractmethod
    def exec():
        pass


class FileHeaderUpdate(Tools):
    def __init__(self, repo_root_path, ignore_file_name='.fileheaderignore', scope='changed', type_list=['.cpp', '.h'], stage_file=False):
        super().__init__(repo_root_path, ignore_file_name, scope, type_list, stage_file)

    def _get_git_info(self, filepath, use_local_name=True):
        created_info = subprocess.check_output(['git', 'log', '--diff-filter=A', '--follow', '--format=%an|%ad', '--', filepath]).decode('utf-8').strip().split('\n')[0].split('|')
        created_by = created_info[0] if created_info and len(created_info[0]) else AUTHOR
        if len(created_info) > 1:
            raw_date = created_info[1]
            date_obj = datetime.datetime.strptime(raw_date, '%a %b %d %H:%M:%S %Y %z')
            created_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
            created_year = date_obj.strftime('%Y')
        else:
            created_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            created_year = datetime.datetime.now().strftime('%Y')

        modified_info = subprocess.check_output(['git', 'log', '-1', '--format=%an|%ad', '--', filepath]).decode('utf-8').strip().split('|')
        modified_by = modified_info[0] if modified_info and len(modified_info[0]) and not use_local_name else AUTHOR
        if len(modified_info) > 1 and not use_local_name:
            raw_date = modified_info[1]
            date_obj = datetime.datetime.strptime(raw_date, '%a %b %d %H:%M:%S %Y %z')
            modified_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
            modified_year = date_obj.strftime('%Y')
        else:
            modified_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            modified_year = datetime.datetime.now().strftime('%Y')

        return created_by, created_date, created_year, modified_by, modified_date, modified_year


    def _remove_existing_comments(self, content):
        pattern = re.compile(r'(\s*(/\*.*?\*/|//.*?\n))+', re.DOTALL)
        match = pattern.match(content)
        if match:
            return content[match.end():].lstrip()
        return content.lstrip()

    def _add_file_header(self, filepath, use_local_name):
        abs_filepath = os.path.join(self._repo_root_path, filepath)
        created_by, created_date, created_year, modified_by, modified_date, modified_year = self._get_git_info(filepath, use_local_name)
        rel_filepath = os.path.relpath(abs_filepath, self._repo_root_path)
        file_name = filepath.split('/')[-1]

        if (created_year != modified_year):
            header = f"""/*
 * @copyright Copyright(c) {created_year}-{modified_year} Hangzhou Zhicun (Witmem) Technology Co., Ltd.
 * @file: {file_name}
 * @author: {created_by}
 * @date: {created_date}
 * @last_author: {modified_by}
 * @last_edit_time: {modified_date}
*/

"""
        else:
            header = f"""/*
 * @copyright Copyright(c) {created_year} Hangzhou Zhicun (Witmem) Technology Co., Ltd.
 * @file: {file_name}
 * @author: {created_by}
 * @date: {created_date}
 * @last_author: {modified_by}
 * @last_edit_time: {modified_date}
*/

"""

        with open(abs_filepath, 'r+', encoding='utf-8') as f:
            content = f.read()
            content_without_comments = self._remove_existing_comments(content)
            f.seek(0, 0)
            f.truncate(0)
            f.write(header + content_without_comments)
            print(f'add header to file {abs_filepath}')

        if self._stage_file:
            subprocess.check_output(['git', 'add', abs_filepath])
            print(f'new change of {abs_filepath} staged')


    def exec(self):
        ignore_patterns = self._get_ignore_patterns()
        type_pattern = ['*' + suffix for suffix in self._type_list]

        ignore_spec = pathspec.PathSpec.from_lines('gitwildmatch', ignore_patterns)
        type_spec = pathspec.PathSpec.from_lines('gitwildmatch', type_pattern)

        if self._scope == 'changed':
            file_paths = self._get_changed_file_paths()
            for file in file_paths:
                if not ignore_spec.match_file(file) and type_spec.match_file(file):
                    self._add_file_header(file, use_local_name=True)
        elif self._scope == 'all':
            # os walk repo_root_path, except all .git folders
            for root, dirs, files in os.walk(self._repo_root_path):
                if '.git' in dirs:
                    dirs.remove('.git')
                for file in files:
                    filepath = os.path.relpath(os.path.join(root, file), self._repo_root_path)
                    if not ignore_spec.match_file(filepath) and type_spec.match_file(filepath):
                        self._add_file_header(filepath, use_local_name=False)


class FormatFile(Tools):
    def __init__(self, repo_root_path, ignore_file_name='.formatignore', scope='changed', type_list=['.cpp', '.h'], stage_file=False):
        super().__init__(repo_root_path, ignore_file_name, scope, type_list, stage_file)

    def _format_file(self, filepath):
        abs_filepath = os.path.join(self._repo_root_path, filepath)
        # format abs_filepath file with clang-format under google code style guide
        subprocess.check_output(['clang-format', '-i', '--style=Google', abs_filepath])
        print(f'format file {abs_filepath}')

        if self._stage_file:
            subprocess.check_output(['git', 'add', abs_filepath])
            print(f'new change of {abs_filepath} staged')



    def exec(self):
        ignore_patterns = self._get_ignore_patterns()
        type_pattern = ['*' + suffix for suffix in self._type_list]

        ignore_spec = pathspec.PathSpec.from_lines('gitwildmatch', ignore_patterns)
        type_spec = pathspec.PathSpec.from_lines('gitwildmatch', type_pattern)

        if self._scope == 'changed':
            file_paths = self._get_changed_file_paths()
            for file in file_paths:
                if not ignore_spec.match_file(file) and type_spec.match_file(file):
                    self._format_file(file)
        elif self._scope == 'all':
            # os walk repo_root_path, except all .git folders
            for root, dirs, files in os.walk(self._repo_root_path):
                if '.git' in dirs:
                    dirs.remove('.git')
                for file in files:
                    filepath = os.path.relpath(os.path.join(root, file), self._repo_root_path)
                    if not ignore_spec.match_file(filepath) and type_spec.match_file(filepath):
                        self._format_file(filepath)


# if main, execute add_header
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='add header to some cpp/h files')
    parser.add_argument('--tool', '-t', choices=['FileHeaderUpdate', 'FormatFile'], required=True, help='tool to be used')
    parser.add_argument('--scope', choices=['changed', 'all'], default='all', help='scope of files to be modified')
    parser.add_argument('--stage', action='store_true', help='stage the modification after adding header')

    args = parser.parse_args()

    scope = args.scope
    stage_file_flag = args.stage
    tool = args.tool

    tool_map = {
        'FileHeaderUpdate': FileHeaderUpdate,
        'FormatFile': FormatFile
    }

    tool_map[tool](REPO_ROOT, scope=scope, stage_file=stage_file_flag).exec()
