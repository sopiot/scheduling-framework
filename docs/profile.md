# 시뮬레이션 프로파일

프레임워크는 각 시뮬레이션 단계마다 오버헤드를 측정, 평가할 수 있는 프로파일 기능을 제공합니다. 시뮬레이션 동안 **Middleware**와 **Thing**의 로그는 각 디바이스에 저장되며, 로그의 타임스탬프를 비교하여 오버헤드를 측정합니다.

## PTP 프로토콜을 이용한 시간 동기화

각 시뮬레이션 단계에 대한 오버헤드를 정확히 측정하기 위해서는 각 디바이스 간에 시간을 정밀하게 동기화해야 합니다.
**PTP 프로토콜**을 사용하면 디바이스 간의 시간을 정밀하게 동기화할 수 있습니다. `ptpd`를 사용하면 **PTP 프로토콜**을 사용한 정밀한 시간 동기화를 수행할 수 있습니다.
`ptpd`는 다음과 같이 설치할 수 있습니다.

```bash
sudo apt install ptpd
```

**PTP 프로토콜**은 네트워크 지연으로 인한 오류를 줄이기 위해 이더넷에 기반을 두고 있습니다. 따라서 `ptpd`를 실행하기 전에 각 디바이스를 이더넷 인터페이스를 통해 동일한 스위치나 라우터에 연결해야 합니다. 각 디바이스를 이더넷을 통해 연결한 후에는 아래의 명령어로 `ptpd`를 실행할 수 있습니다. `-i` 옵션 다음에는 각 디바이스의 이더넷 인터페이스를 지정합니다.

```bash
sudo ptpd -C -m -i <ethernet_interface>
```

동기화할 모든 디바이스에서 `ptpd`가 실행되면, `ptpd`는 최적의 마스터 시간 디바이스를 결정하고 마스터 디바이스의 시간을 기반으로 슬레이브 디바이스의 시간을 동기화합니다. `"acquired clock control`" 메시지가 표시되면 시간 동기화가 완료된 것입니다. `-pf` 옵션을 주어 프로파일을 수행할 수 있습니다. 만약 `"acquired clock control"` 메시지가 하나의 디바이스에서만 출력되지 않는다면, 해당 디바이스가 마스터 시간 디바이스로 결정된 것입니다. 이 경우, `"Now in state: PTP_MASTER"` 메시지의 가장 오른쪽에 "`(self)"` 메시지가 있는지 확인하세요.

```
ptpd2[20090].startup (info)      (___) Configuration OK
ptpd2[20090].startup (info)      (___) Successfully acquired lock on /var/run/ptpd2.lock
ptpd2[20090].startup (notice)    (___) PTPDv2 started successfully on eth0 using "masterslave" preset (PID 20090)
ptpd2[20090].startup (info)      (___) TimingService.PTP0: PTP service init
ptpd2[20090].eth0 (info)      (init) Observed_drift loaded from kernel: 8111 ppb
ptpd2[20090].eth0 (notice)    (lstn_init) Now in state: PTP_LISTENING
ptpd2[20090].eth0 (info)      (lstn_init) UTC offset is now 37
ptpd2[20090].eth0 (info)      (lstn_init) New best master selected: d83addfffe18645b(unknown)/1
ptpd2[20090].eth0 (notice)    (slv) Now in state: PTP_SLAVE, Best master: d83addfffe18645b(unknown)/1
ptpd2[20090].eth0 (notice)    (slv) Received first Sync from Master
ptpd2[20090].eth0 (notice)    (slv) Received first Delay Response from Master
ptpd2[20090].eth0 (notice)    (slv) TimingService.PTP0: elected best TimingService
ptpd2[20090].eth0 (info)      (slv) TimingService.PTP0: acquired clock control
```

## 프로파일

이제 시뮬레이션을 실행할 때, `-pf` 옵션을 주어 프로파일을 수행할 수 있습니다.

```bash
cd sim_env_samples
python3 run.py -c ../sim_env_samples/<env_samples_directory> -po ../scheduling_algorithm/samples -pf
```

`-dl` 옵션을 주어 시뮬레이션을 실행하여 다운로드한 시뮬레이션 로그가 있다면, 시뮬레이션 로그를 로드하여 프로파일을 진행할 수 있습니다. 이 경우, `--only_profile` 옵션을 주어 프로파일만 진행할 수 있습니다. `-log` 옵션으로 개별 시뮬레이션에 대한 로그를 프로파일하거나, 디렉토리 내의 모든 로그에 대해 프로파일을 진행할 수 있습니다.

```bash
cd sim_env_samples
python3 run.py -log ../remote_logs/<simulation_log_sample> --only_profile
# python run.py -log ../remote_logs --only_profile
```

## 트러블슈팅

### PTP 프로토콜을 사용한 시간 동기화가 너무 오래 걸리는 경우

만약 `"acquired clock control`" 메시지가 출력되지 않고 시간 동기화가 끝나지 않는 경우, 해당 디바이스가 마스터 시간 디바이스인지 확인해주세요. `"Now in state: PTP_MASTER"`라는 메시지의 가장 오른쪽에 "`(self)"`가 있다면, 해당 디바이스가 마스터 시간 디바이스로 선택된 것이므로 나머지 슬레이브 디바이스들의 동기화 상태만 확인하면 됩니다.

위의 경우에 해당하지 않는다면, 아직 시간 동기화가 완료되지 않은 것이므로 잠시 기다려 주세요. 아무리 기다려도 시간 동기화가 진행되지 않는다면, `ptpd`를 종료하고 다시 실행해보세요.
