import os
import subprocess
import datetime
import re
import argparse
import pathspec
from abc import ABC, abstractmethod
import concurrent.futures
from queue import Queue
import tempfile

REPO_ROOT = subprocess.check_output(['git', 'rev-parse', '--show-toplevel']).strip().decode('utf-8')
AUTHOR = subprocess.check_output(['git', 'config', 'user.name']).strip().decode('utf-8')


class Tools:
    def __init__(self, repo_root_path, ignore_file_name, scope, type_list, stage_file, workers):
        self._repo_root_path = repo_root_path
        self._ignore_file_name = ignore_file_name
        self._scope = scope
        self._type_list = type_list
        self._stage_file = stage_file
        self._workers = workers

    def _get_changed_file_paths(self, ignore_patterns=[]):
        target_files = subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=self._repo_root_path).strip().decode('utf-8').split('\n')
        target_files = [file for file in target_files if not any(pattern.match_file(file) for pattern in ignore_patterns)]
        return target_files

    def _get_ignore_patterns(self, additional_patterns=[]):
        ignore_file_list = []
        if os.path.exists(os.path.join(self._repo_root_path, self._ignore_file_name)):
            with open(os.path.join(self._repo_root_path, self._ignore_file_name), 'r') as f:
                ignore_file_list = [line.strip() for line in f if line.strip()]

        ignore_file_list.extend(additional_patterns)
        return ignore_file_list

    def _get_dir_iter(self, root_path=None, ignore_patterns=[]):
        if root_path is None:
            root_path = self._repo_root_path

        path_fifo = Queue()
        path_fifo.put(root_path)
        while not path_fifo.empty():
            current_path = path_fifo.get()
            for item in os.scandir(current_path):
                full_path = os.path.join(current_path, item)
                if any(pattern.match_file(full_path) for pattern in ignore_patterns):
                    continue
                if item.is_dir():
                        path_fifo.put(full_path)
                else:
                    yield full_path

    @abstractmethod
    def exec():
        pass


class FileHeaderUpdate(Tools):
    def __init__(self, repo_root_path, ignore_file_name='.fileheaderignore', scope='changed', type_list=['.cpp', '.h'], stage_file=False, workers=4):
        super().__init__(repo_root_path, ignore_file_name, scope, type_list, stage_file, workers)

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
        temp_filepath = ''

        abs_filedir = os.path.dirname(abs_filepath)
        with tempfile.NamedTemporaryFile(dir=abs_filedir, delete=False) as f_tmp:
            temp_filepath = f_tmp.name

        created_by, created_date, created_year, modified_by, modified_date, modified_year = self._get_git_info(filepath, use_local_name)
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

        with open(abs_filepath, 'r+', encoding='utf-8') as f, open(temp_filepath, 'w', encoding='utf-8') as f_tmp:
            f_tmp.write(header)

            line = f.readline()
            heading_comment_over = False
            is_in_multiline_comment = False
            while line:
                if not heading_comment_over:
                    if is_in_multiline_comment:
                        # check over and trim line
                        line_list = line.split('*/', 1)
                        if len(line_list) == 2:
                            # multi-line comment is over (*/ in line)
                            is_in_multiline_comment = False
                            line = line_list[1].lstrip()
                        else:
                            # multi-line comment is not over (no */ in line)
                            line = f.readline()
                            continue

                    line = line.lstrip()
                    if len(line) == 0 or line.startswith('//'):
                        line = f.readline()
                        continue

                    if line.startswith('/*'):
                        is_in_multiline_comment = True
                        line = line[2:]
                        continue

                    heading_comment_over = True

                f_tmp.write(line)
                line = f.readline()

        os.replace(temp_filepath, abs_filepath)
        print(f'add header to file {abs_filepath}')

        if self._stage_file:
            subprocess.check_output(['git', 'add', abs_filepath])
            print(f'new change of {abs_filepath} staged')


    def exec(self):
        ignore_patterns = self._get_ignore_patterns(additional_patterns=['.git'])
        type_pattern = ['*' + suffix for suffix in self._type_list]

        ignore_spec = pathspec.PathSpec.from_lines('gitwildmatch', ignore_patterns)
        type_spec = pathspec.PathSpec.from_lines('gitwildmatch', type_pattern)
        use_local_name_flag = False

        if self._scope == 'changed':
            file_paths_iter = self._get_changed_file_paths([ignore_spec])
            use_local_name_flag = True
        elif self._scope == 'all':
            file_paths_iter = self._get_dir_iter(self._repo_root_path, [ignore_spec])
            use_local_name_flag = False
        else:
            raise Exception('invalid scope')

        with concurrent.futures.ThreadPoolExecutor(max_workers=self._workers) as executor:
            future = []
            for file in file_paths_iter:
                if type_spec.match_file(file):
                    future.append(executor.submit(self._add_file_header, file, use_local_name=use_local_name_flag))

            for future in concurrent.futures.as_completed(future):
                pass


class FormatFile(Tools):
    def __init__(self, repo_root_path, ignore_file_name='.formatignore', scope='changed', type_list=['.cpp', '.h'], stage_file=False, workers=4):
        super().__init__(repo_root_path, ignore_file_name, scope, type_list, stage_file, workers)

    def _format_file(self, filepath, changed_lines_only=False):
        abs_filepath = os.path.join(self._repo_root_path, filepath)
        # format abs_filepath file with clang-format under google code style guide
        if changed_lines_only:
            git_diff_command = ['git', 'diff', '-U0', 'HEAD', '--', abs_filepath]
            git_diff_process = subprocess.Popen(git_diff_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            git_diff_output, git_diff_error = git_diff_process.communicate()

            if git_diff_process.returncode != 0:
                print(f"Error running git diff: {git_diff_error.decode('utf-8')}")
                return

            clang_format_diff_command = ['clang-format-diff', '-p1', '-i', '-style', 'Google']
            clang_format_diff_process = subprocess.Popen(clang_format_diff_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            clang_format_diff_output, clang_format_diff_error = clang_format_diff_process.communicate(input=git_diff_output)

            if clang_format_diff_process.returncode != 0:
                print(f"Error running clang-format-diff: {clang_format_diff_error.decode('utf-8')}")
            else:
                print("clang-format-diff executed successfully")
        else:
            subprocess.check_output(['clang-format', '-i', '--style=Google', abs_filepath])
        print(f'format file {abs_filepath}')

        if self._stage_file:
            subprocess.check_output(['git', 'add', abs_filepath])
            print(f'new change of {abs_filepath} staged')



    def exec(self):
        ignore_patterns = self._get_ignore_patterns(['.git'])
        type_pattern = ['*' + suffix for suffix in self._type_list]

        ignore_spec = pathspec.PathSpec.from_lines('gitwildmatch', ignore_patterns)
        type_spec = pathspec.PathSpec.from_lines('gitwildmatch', type_pattern)
        changed_lines_only_flag = False

        if self._scope == 'changed':
            file_paths_iter = self._get_changed_file_paths([ignore_spec])
            use_local_name_flag = True
        elif self._scope == 'all':
            file_paths_iter = self._get_dir_iter(self._repo_root_path, [ignore_spec])
            use_local_name_flag = False
        else:
            raise Exception('invalid scope')

        with concurrent.futures.ThreadPoolExecutor(max_workers=self._workers) as executor:
            future = []
            for file in file_paths_iter:
                if type_spec.match_file(file):
                    future.append(executor.submit(self._format_file, file, changed_lines_only_flag))

            for future in concurrent.futures.as_completed(future):
                pass


# if main, execute add_header
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='add header to some cpp/h files')
    parser.add_argument('--tool', '-t', choices=['FileHeaderUpdate', 'FormatFile'], required=True, help='tool to be used')
    parser.add_argument('--scope', choices=['changed', 'all'], default='all', help='scope of files to be modified')
    parser.add_argument('--stage', action='store_true', help='stage the modification after adding header')
    parser.add_argument('--workers', type=int, default=4, help='number of worker threads')

    args = parser.parse_args()

    scope = args.scope
    stage_file_flag = args.stage
    tool = args.tool
    workers = args.workers

    tool_map = {
        'FileHeaderUpdate': FileHeaderUpdate,
        'FormatFile': FormatFile
    }

    tool_map[tool](REPO_ROOT, scope=scope, stage_file=stage_file_flag, workers=workers).exec()
