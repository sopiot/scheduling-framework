from simulation_framework.core.components import *

import paramiko
import platform
import stat


# def print_progress_status(transferred, toBeTransferred):
#     print(f'Progress: {(transferred / toBeTransferred):.2%}', end='\r')


class MXSSHClient:
    COMMAND_SEND_LIMIT = 1
    SFTP_CLIENT_POOL_SIZE = 10

    def __init__(self, device: MXDevice) -> None:
        self._ssh_client: paramiko.SSHClient = None
        self._sftp_client: paramiko.SFTPClient = None

        self.device = device
        self.connected = False
        self.sftp_opened = False

        self.num_command_executing = 0

        self.device.available_port_list = []

    def _send_command(self, command: Union[List[str], str], ignore_result: bool = False, get_pty: bool = False) -> Union[bool, List[str]]:
        while self.num_command_executing > MXSSHClient.COMMAND_SEND_LIMIT:
            time.sleep(1)

        if isinstance(command, str):
            command_list = [line.strip() for line in command.strip().split('\n')]
        elif isinstance(command, list):
            command_list = [line.strip() for line in flatten_list([line.strip().split('\n') for line in command])]
        else:
            raise TypeError(f'command type must be str or list, not {type(command)}')

        if not self.connected:
            self.connect()

        integrated_command = ''
        for command in command_list:
            if 'sudo' in command:
                command_without_sudo = command.split('sudo')[1].strip()
                password = escape_special_chars(self.device.password)
                command = f'echo {password} | sudo -S {command_without_sudo}'

            integrated_command += f'{command};'

        try:
            self.num_command_executing += 1
            _, stdout, stderr = self._ssh_client.exec_command(integrated_command, get_pty=get_pty)

            if ignore_result:
                return True
            else:
                stdout_result: List[str] = stdout.readlines()
                stderr_result: List[str] = stderr.readlines()
                return stdout_result, stderr_result
        finally:
            self.num_command_executing -= 1

    def available_port(self):
        available_ports = list(range(10000, 65535))

        # Get a list of ports in use
        command_result: str = self.send_command('netstat -an')
        lines = command_result
        used_ports = []
        for line in lines:
            if 'tcp' in line:
                parts = line.split()
                local_address = parts[3]
                # foreign_address = parts[4]
                port_status = parts[5]
                if 'TIME_WAIT' == port_status or 'ESTABLISHED' == port_status or 'CONNECTED' == port_status or 'LISTEN' == port_status:
                    # 로컬 머신의 os 버전을 os.system을이용하여 체크하는 함수
                    if 'Darwin' == platform.system():
                        local_port = int(local_address.split('.')[-1])
                    elif 'Linux' == platform.system():
                        local_port = int(local_address.split(':')[-1])
                    else:
                        raise UnsupportedError(f'Not Support platform: {platform.platform()}')

                    used_ports.append(local_port)

        # Compare the list of ports in use with the list of available ports to create a list of ports that are not in use.
        available_ports = [port for port in available_ports if port not in used_ports]
        return available_ports

    def get_duplicate_proc_pid(self, proc_name: str, user: str = None, local_ip: str = None, local_port: int = None, foreign_ip: str = None, foreign_port: int = None,
                               args: Union[List[str], str] = ''):

        def get_proc_info():
            netstat_result = None
            ps_ef_result = None

            if not self.connected:
                netstat_result: List[str] = os.popen(f'netstat -nap 2>/dev/null | grep {proc_name}').read().split('\n')
                ps_ef_result: List[str] = os.popen(f'ps -ef 2>/dev/null | grep {proc_name}').read().split('\n')
            else:
                netstat_result: List[str] = self.send_command(f'netstat -nap 2>/dev/null | grep {proc_name}', False)
                ps_ef_result: List[str] = self.send_command(f'ps -ef 2>/dev/null | grep {proc_name}', False)

            return ps_ef_result, netstat_result

        def parse_ps_ef_line(line: str):
            line = line.split()
            if len(line) < 1:
                return False
            else:
                return {
                    'user': line[0],
                    'pid': int(line[1]),
                    'proc_name': line[7].lstrip('./'),
                    'args': line[8:],
                }

        def parse_netstat_line(line: str):
            line = line.split()
            if len(line) < 1 or 'tcp6' in line:
                return False
            elif 'tcp' in line:
                return {
                    'local_ip': line[3].split(':')[0],
                    'local_port': int(line[3].split(':')[1]),
                    'foreign_ip': line[4].split(':')[0],
                    'foreign_port': int(line[4].split(':')[1]) if '*' not in line[4].split(':')[1] else 0,
                    'proc_name': '/'.join(line[6].split('/')[1:]).lstrip('./'),
                    'pid': int(line[6].split('/')[0])
                }

        ps_ef_result, netstat_result = get_proc_info()
        target_pid_list_netstat = []
        target_pid_list_ps_ef = []

        for line in ps_ef_result:
            parse_result = parse_ps_ef_line(line)
            if parse_result:
                proc_name_check = proc_name in parse_result['proc_name'].split('/')[-1]
                args_check = args in ' '.join(parse_result['args'])
                if proc_name_check and args_check:
                    target_pid_list_ps_ef.append(parse_result['pid'])

        for line in netstat_result:
            parse_result = parse_netstat_line(line)
            if parse_result:
                proc_name_check = proc_name in parse_result['proc_name']

                local_ip_check = local_ip == parse_result['local_ip']
                local_port_check = local_port == parse_result['local_port'] or local_port == parse_result['foreign_port']
                foreign_ip_check = foreign_ip == parse_result['foreign_ip']
                foreign_port_check = foreign_port == parse_result['foreign_port']

                local_address_check = local_ip_check and local_port_check
                foreign_address_check = foreign_ip_check and foreign_port_check
                address_check = local_address_check or foreign_address_check

                if proc_name_check and address_check:
                    target_pid_list_netstat.append(parse_result['pid'])

        if not proc_name == 'python':
            target_pid_list = list(set(target_pid_list_netstat).intersection(target_pid_list_ps_ef))
        else:
            target_pid_list = list(set(target_pid_list_ps_ef))
        return target_pid_list

    def send_command(self, command: Union[List[str], str], ignore_result: bool = False, get_pty: bool = False, get_err: bool = False) -> Union[bool, List[str], Tuple[List[str], List[str]]]:
        if ignore_result:
            return self._send_command(command=command, ignore_result=ignore_result, get_pty=get_pty)

        stdout, stderr = self._send_command(command=command, ignore_result=ignore_result, get_pty=get_pty)
        if get_err:
            return stdout, stderr
        else:
            return stdout

    def send_command_with_check_success(self, command: Union[List[str], str], background: bool = False, get_pty: bool = False) -> bool:
        result = self.send_command(command=f'{command.strip(";")}; echo $?', ignore_result=False, get_pty=get_pty)
        if not int(result[-1]):
            return True
        else:
            return False

    # FIXME: parallel feature is not working
    def send_file(self, local_path: str, remote_path: str):
        # while not MXSSHClient.FILE_UPLOADING < 10:
        #     time.sleep(BUSY_WAIT_TIMEOUT)

        if not self.sftp_opened:
            self.open_sftp()

        # MXTEST_LOG_DEBUG(f'Send files: {local_path} -> {remote_path}', MXTestLogLevel.PASS)
        try:
            # MXSSHClient.FILE_UPLOADING += 1
            try:
                remote_dir_path = os.path.dirname(remote_path)
                self._sftp_client.chdir(remote_dir_path)
            except IOError:
                self.mkdir_p(remote_dir_path)
                # self._sftp_client.mkdir(remote_path_dirname)
            # self._sftp_client.put(local_path, remote_path, callback=print_progress_status)
            self._sftp_client.put(local_path, remote_path)
            return True
        except KeyboardInterrupt:
            return False
        except Exception as e:
            print_error()
        finally:
            # MXSSHClient.FILE_UPLOADING -= 1
            pass

    # local_path와 remote_path를 받아서 재귀적으로 폴더를 전송하는 함수
    def send_dir(self, local_path: str, remote_path: str):
        self.send_command(f'mkdir -p {remote_path}')
        if not self.sftp_opened:
            self.open_sftp()

        for root, dirs, files in os.walk(local_path):
            for name in files:
                local_file_path = os.path.join(root, name)
                remote_file_path = os.path.join(remote_path, os.path.relpath(local_file_path, local_path))
                self.send_file(local_file_path, remote_file_path)
            for name in dirs:
                local_dir_path = os.path.join(root, name)
                remote_dir_path = os.path.join(remote_path, os.path.relpath(local_dir_path, local_path))
                try:
                    self.mkdir_p(remote_dir_path)
                    # self._sftp_client.mkdir(remote_dir_path)
                except:
                    pass

    # FIXME: parallel feature is not working
    def get_file(self, remote_path: str, local_path: str, ext_filter: str = ''):
        # while not MXSSHClient.FILE_DOWNLOADING < 20:
        #     time.sleep(BUSY_WAIT_TIMEOUT)

        if not self.sftp_opened:
            self.open_sftp()

        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        if remote_path.split('.')[-1] == ext_filter:
            # MXTEST_LOG_DEBUG(f'Download file: {local_path} <- {remote_path}')
            try:
                # MXSSHClient.FILE_DOWNLOADING += 1

                local_path_dirname = os.path.dirname(local_path)
                if not os.path.exists(local_path_dirname):
                    os.makedirs(local_path_dirname, exist_ok=True)
                # self._sftp_client.get(remote_path, local_path, callback=print_progress_status)
                self._sftp_client.get(remote_path, local_path)
                return True
            except KeyboardInterrupt:
                return False
            except Exception as e:
                print_error()
            finally:
                # MXSSHClient.FILE_DOWNLOADING -= 1
                pass
        else:
            # MXTEST_LOG_DEBUG(f'{remote_path} is not {ext_filter} file. Skip download...', MXTestLogLevel.WARN)
            return False

    # FIXME: 폴더자체를 받아오는 것이 아니라 폴더안의 파일만 받아오는 것으로 되어있음. 해당 부분을 폴더까지 같이 받아오는 것으로 수정해야함
    def get_dir(self, remote_path: str, local_path: str, ext_filter: List[str] = []):
        if not self.sftp_opened:
            self.open_sftp()

        os.makedirs(local_path, exist_ok=True)
        file_attr_list = self._sftp_client.listdir_attr(remote_path)
        for file_attr in file_attr_list:
            remote_file_path = os.path.join(remote_path, file_attr.filename)
            local_file_path = os.path.join(local_path, file_attr.filename)

            if stat.S_ISDIR(file_attr.st_mode):
                self.get_dir(remote_file_path, local_file_path)
            else:
                for ext in ext_filter:
                    if not self.get_file(remote_file_path, local_file_path, ext):
                        continue
        return True

    def get_ssh_config(self, use_ssh_config: bool = True) -> Union[paramiko.SSHConfig, bool]:
        if not use_ssh_config:
            return False

        ssh_cfg = {
            'hostname': self.device.name,
            'username': self.device.user.split('/')[-1],
            'port': self.device.ssh_port,
            'password': self.device.password,
            'key_filename': None,
            'sock': None,
        }

        if not os.path.exists(os.path.expanduser("~/.ssh/config")):
            MXTEST_LOG_DEBUG('Not found ssh config file', MXTestLogLevel.INFO)
            ssh_cfg['hostname'] = self.device.host
            return False

        ssh_config = paramiko.SSHConfig()
        user_config_file = os.path.expanduser("~/.ssh/config")
        with open(user_config_file, 'r', encoding='utf-8') as f:
            ssh_config.parse(f)

        host_conf = ssh_config.lookup(self.device.name)
        if host_conf.get('user', None):
            if 'hostname' in host_conf:
                ssh_cfg['hostname'] = host_conf['hostname']
            if 'user' in host_conf:
                ssh_cfg['username'] = host_conf['user']
            if 'port' in host_conf:
                ssh_cfg['port'] = host_conf['port']
            if 'password' in host_conf:
                ssh_cfg['password'] = host_conf['password']
            if 'identityfile' in host_conf:
                ssh_cfg['key_filename'] = host_conf['identityfile']
            if 'proxycommand' in host_conf:
                ssh_cfg['sock'] = paramiko.ProxyCommand(host_conf['proxycommand'])

            # proxy_host_conf = ssh_config.lookup([cmd for cmd in ssh_cfg['sock'].cmd if '@' in cmd][0].split('@')[1])
            self.device.host = ssh_cfg['hostname']
            self.device.user = ssh_cfg['username']
            self.device.password = ssh_cfg['password']

            return ssh_cfg
        else:
            MXTEST_LOG_DEBUG(f'Host {self.device.name} is not found in ssh config file.', 2)
            ssh_cfg['hostname'] = self.device.host
            return False

    def connect(self, use_ssh_config: bool = True, retry: int = 5, timeout: float = 10) -> paramiko.SSHClient:
        while retry:
            try:
                if self.connected:
                    return self._ssh_client

                self._ssh_client = paramiko.SSHClient()
                self._ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh_cfg = self.get_ssh_config(use_ssh_config=use_ssh_config)

                if ssh_cfg:
                    self._ssh_client.connect(**ssh_cfg, timeout=timeout)
                elif self.device.host and self.device.ssh_port and self.device.user and self.device.password:
                    self._ssh_client.connect(hostname=self.device.host, port=self.device.ssh_port,
                                             username=self.device.user, password=self.device.password,
                                             timeout=timeout)
                else:
                    raise SSHConfigError('Please set the user, host, port, password or locate .ssh/config before connect to ssh host')

                # MXTEST_LOG_DEBUG(f'SSH Connect success to device {self.device.name}.', MXTestLogLevel.PASS)
                self.connected = True
                return self._ssh_client
            except paramiko.SSHException as e:
                retry -= 1
                print_error()
                time.sleep(1)

    def disconnect(self):
        if self.connected:
            self._ssh_client.close()
            self.connected = False

        return True

    def open_sftp(self):
        if not self.connected:
            self.connect()

        if self.sftp_opened:
            # MXTEST_LOG_DEBUG('SFTP client already opened', MXTestLogLevel.WARN)
            return self._sftp_client

        self._sftp_client = self._ssh_client.open_sftp()
        self.sftp_opened = True

        return self._sftp_client

    def close_sftp(self):
        if self.sftp_opened:
            self._sftp_client.close()
            self.sftp_opened = False

        return True

    def mkdir_p(self, path):
        if path == '/':
            self._sftp_client.chdir('/')
            return
        if path == '':
            return
        try:
            self._sftp_client.chdir(path)
        except IOError:
            dirname, basename = os.path.split(path.rstrip('/'))
            self.mkdir_p(dirname)
            self._sftp_client.mkdir(basename)
            self._sftp_client.chdir(basename)
            return True
