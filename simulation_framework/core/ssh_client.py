from simulation_framework.core.elements import *

import paramiko
import stat


def print_progress_status(transferred, toBeTransferred):
    print(f'Progress: {(transferred / toBeTransferred):.2%}', end='\r')


class SoPSSHClient:
    COMMAND_SENDING = False

    def __init__(self, device: SoPDeviceElement, connect_timeout: float = 10) -> None:
        self._ssh_client = paramiko.SSHClient()
        self._sftp_client = None

        self.device = device
        self.connected = False
        self.sftp_opened = False
        self.connect_timeout = connect_timeout

        self.device.available_port_list = []

    def available_port(self):
        available_ports = list(range(10000, 65535))

        # 사용 중인 포트 목록을 얻음
        command_result: str = self.send_command('netstat -an')
        lines = command_result
        used_ports = []
        for line in lines:
            if 'tcp' in line:
                parts = line.split()
                local_address = parts[3]
                forign_address = parts[4]
                port_status = parts[5]
                if 'TIME_WAIT' == port_status or 'ESTABLISHED' == port_status or 'CONNECTED' == port_status or 'LISTEN' == port_status:
                    local_port = int(local_address.split(':')[-1])
                    used_ports.append(local_port)

        # 사용 중인 포트 목록과 사용 가능한 포트 목록을 비교하여 사용중이지 않은 포트 목록을 생성
        available_ports = [
            port for port in available_ports if port not in used_ports]
        return available_ports

    def get_duplicate_proc_pid(self, proc_name: str, user: str = None,
                               local_ip: str = None, local_port: int = None, foreign_ip: str = None, foreign_port: int = None,
                               args: Union[List[str], str] = ''):

        def get_proc_info():
            netstat_result = None
            ps_ef_result = None

            if not self.connected:
                netstat_result: List[str] = os.popen(
                    f'netstat -nap 2>/dev/null | grep {proc_name}').read().split('\n')
                ps_ef_result: List[str] = os.popen(
                    f'ps -ef 2>/dev/null | grep {proc_name}').read().split('\n')
            else:
                netstat_result: List[str] = self.send_command(
                    f'netstat -nap 2>/dev/null | grep {proc_name}', False)
                ps_ef_result: List[str] = self.send_command(
                    f'ps -ef 2>/dev/null | grep {proc_name}', False)

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
                proc_name_check = proc_name in parse_result['proc_name'].split(
                    '/')[-1]
                args_check = args in ' '.join(parse_result['args'])
                if proc_name_check and args_check:
                    target_pid_list_ps_ef.append(parse_result['pid'])

        for line in netstat_result:
            parse_result = parse_netstat_line(line)
            if parse_result:
                proc_name_check = proc_name in parse_result['proc_name']

                local_ip_check = local_ip == parse_result['local_ip']
                local_port_check = local_port == parse_result[
                    'local_port'] or local_port == parse_result['foreign_port']
                foreign_ip_check = foreign_ip == parse_result['foreign_ip']
                foreign_port_check = foreign_port == parse_result['foreign_port']

                local_address_check = local_ip_check and local_port_check
                foreign_address_check = foreign_ip_check and foreign_port_check
                address_check = local_address_check or foreign_address_check

                if proc_name_check and address_check:
                    target_pid_list_netstat.append(parse_result['pid'])

        if not proc_name == 'python':
            target_pid_list = list(
                set(target_pid_list_netstat).intersection(target_pid_list_ps_ef))
        else:
            target_pid_list = list(set(target_pid_list_ps_ef))
        return target_pid_list

    def send_command(self, command: Union[List[str], str], ignore_result: bool = False, background: bool = False) -> Union[bool, List[str]]:
        while SoPSSHClient.COMMAND_SENDING:
            time.sleep(THREAD_TIME_OUT)

        SoPSSHClient.COMMAND_SENDING = True

        if isinstance(command, str):
            command = [command]
        if not self.connected:
            self.connect()

        for item in command:
            if self.connected:
                if background:
                    transport = self._ssh_client.get_transport()
                    channel = transport.open_session()
                    channel.exec_command(item)
                else:
                    try:
                        stdin, stdout, stderr = self._ssh_client.exec_command(
                            item)
                    except Exception as e:
                        # NOTE: `Secsh channel <int num> open FAILED: open failed: Connect failed` 에러가 발생하여 연결을 다시 수립하는 방식으로 해결
                        # NOTE: 그러나 해당 방법이 제대로 된 해결법인지는 잘 모르겠음
                        # NOTE: 반복적으로 send_command가 실행되면 생기는 것으로 보이나 while문으로 똑같은 명령을 반복했을 때는 문제가 생기지 않고 run_middleware를
                        # NOTE: 반복적으로 실행하면 문제가 생김
                        # NOTE: -> mosquitto, middelware를 실행시킬때 백그라운드로 안 시켜서 ssh 세션을 계속 유지하는 것이 문제였다.

                        SOPTEST_LOG_DEBUG(
                            f'Send_command error: {e}', SoPTestLogLevel.FAIL)
                        self.disconnect()
                        self.connect()
                        stdin, stdout, stderr = self._ssh_client.exec_command(
                            item)
                # SOPTEST_LOG_DEBUG(f'command execute -> {item}', SoPTestLogLevel.PASS)
                if ignore_result:
                    SoPSSHClient.COMMAND_SENDING = False
                    return True
                else:
                    if 'sudo' in command:
                        stdin.write(f'{self.device.password}\n')
                        stdin.flush()

                    stdout_result: List[str] = stdout.readlines()
                    # self.disconnect()
                    SoPSSHClient.COMMAND_SENDING = False
                    return [line.strip() for line in stdout_result]
            else:
                result = os.popen(item)
                # SOPTEST_LOG_DEBUG(f'command execute -> {item}', SoPTestLogLevel.PASS)
                if ignore_result:
                    SoPSSHClient.COMMAND_SENDING = False
                    return True
                else:
                    SoPSSHClient.COMMAND_SENDING = False
                    return result.read().split('\n')

    def send_file(self, local_path: str, remote_path: str):
        if not self.sftp_opened:
            self.open_sftp()

        SOPTEST_LOG_DEBUG(
            f'Send files: {local_path} -> {remote_path}', SoPTestLogLevel.PASS)
        try:
            self._sftp_client.put(local_path, remote_path,
                                  callback=print_progress_status)
            return True
        except KeyboardInterrupt:
            return False
        except Exception as e:
            print_error(e)

    # local_path와 remote_path를 받아서 재귀적으로 폴더를 전송하는 함수
    def send_dir(self, local_path: str, remote_path: str):
        self.send_command(
            f'mkdir -p {remote_path}')
        if not self.sftp_opened:
            self.open_sftp()

        for root, dirs, files in os.walk(local_path):
            for name in files:
                local_file_path = os.path.join(root, name)
                remote_file_path = os.path.join(
                    remote_path, os.path.relpath(local_file_path, local_path))
                self.send_file(local_file_path, remote_file_path)
            for name in dirs:
                local_dir_path = os.path.join(root, name)
                remote_dir_path = os.path.join(
                    remote_path, os.path.relpath(local_dir_path, local_path))
                try:
                    self._sftp_client.mkdir(remote_dir_path)
                except:
                    pass

    def get_file(self, remote_path: str, local_path: str, ext_filter: str = ''):
        if not self.sftp_opened:
            self.open_sftp()

        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        if remote_path.split('.')[-1] == ext_filter:
            SOPTEST_LOG_DEBUG(
                f'Download file: {local_path} <- {remote_path}')
            try:
                self._sftp_client.get(remote_path, local_path,
                                      callback=print_progress_status)
                return True
            except KeyboardInterrupt:
                return False
            except Exception as e:
                print_error(e)
        else:
            SOPTEST_LOG_DEBUG(
                f'{remote_path} is not {ext_filter} file. Skip download...', SoPTestLogLevel.WARN)
            return False

    # FIXME: 폴더자체를 받아오는 것이 아니라 폴더안의 파일만 받아오는 것으로 되어있음. 해당 부분을 폴더까지 같이 받아오는 것으로 수정해야함
    def get_dir(self, remote_path: str, local_path: str, ext_filter: List[str] = []):
        if not self.sftp_opened:
            self.open_sftp()

        os.makedirs(local_path, exist_ok=True)
        fileattr_list = self._sftp_client.listdir_attr(remote_path)
        for fileattr in fileattr_list:
            remote_file_path = os.path.join(remote_path, fileattr.filename)
            local_file_path = os.path.join(local_path, fileattr.filename)

            if stat.S_ISDIR(fileattr.st_mode):
                self.get_dir(remote_file_path, local_file_path)
            else:
                for ext in ext_filter:
                    if not self.get_file(remote_file_path, local_file_path, ext):
                        continue
        return True

    def get_ssh_config(self, use_ssh_config: bool = True):
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
            SOPTEST_LOG_DEBUG('Not found ssh config file',
                              SoPTestLogLevel.INFO)
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
                ssh_cfg['sock'] = paramiko.ProxyCommand(
                    host_conf['proxycommand'])

            # proxy_host_conf = ssh_config.lookup(
            #     [cmd for cmd in ssh_cfg['sock'].cmd if '@' in cmd][0].split('@')[1])
            self.device.host = ssh_cfg['hostname']
            self.device.user = ssh_cfg['username']
            self.device.password = ssh_cfg['password']

            return ssh_cfg
        else:
            SOPTEST_LOG_DEBUG(
                f'Host {self.device.name} is not found in ssh config file.', 2)
            ssh_cfg['hostname'] = self.device.host
            return False

    def connect(self, use_ssh_config: bool = True, retry: int = 5) -> paramiko.SSHClient:
        while retry:
            try:
                if self.connected:
                    SOPTEST_LOG_DEBUG('Already connected to host',
                                      SoPTestLogLevel.WARN)
                    return self._ssh_client

                self._ssh_client.set_missing_host_key_policy(
                    paramiko.AutoAddPolicy())
                ssh_cfg = self.get_ssh_config(use_ssh_config=use_ssh_config)

                if ssh_cfg:
                    self._ssh_client.connect(
                        **ssh_cfg, timeout=self.connect_timeout)
                elif self.device.host and self.device.ssh_port and self.device.user and self.device.password:
                    self._ssh_client.connect(hostname=self.device.host, port=self.device.ssh_port,
                                             username=self.device.user, password=self.device.password, timeout=self.connect_timeout)
                else:
                    raise SOPTEST_LOG_DEBUG(
                        'Please set the user, host, port, password or locate .ssh/config before connect to ssh host', SoPTestLogLevel.FAIL)

                SOPTEST_LOG_DEBUG(
                    f'SSH Connect success to device {self.device.name}.', SoPTestLogLevel.PASS)

                self.connected = True

                return self._ssh_client
            except Exception as e:
                retry -= 1
                print_error(e)
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
            SOPTEST_LOG_DEBUG('SFTP client already opened',
                              SoPTestLogLevel.WARN)
            return self._sftp_client

        self._sftp_client = self._ssh_client.open_sftp()
        self.sftp_opened = True

        return self._sftp_client

    def close_sftp(self):
        if self.sftp_opened:
            self._sftp_client.close()
            self.sftp_opened = False

        return True
