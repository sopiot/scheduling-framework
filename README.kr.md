# Scheduling Framework for Hierarchical Edge-based IoT

<div style="text-align:center">
  <img src="imgs/sim_overview.png" width="500" alt="sim_overview" style="margin-right:0px" />
</div>

이 프레임워크는 MySSIX IoT 플랫폼의 **스케줄링 알고리즘**을 시뮬레이션을 통해 평가, 튜닝할 수 있습니다. 사용자는 이 프레임워크를 사용하여 자신만의 **스케줄링 알고리즘**을 구현하고 IoT 플랫폼을 시뮬레이션 할 수 있습니다. 프레임워크는 여러 시뮬레이션 환경과 **스케줄링 알고리즘**을 사용하여 여러 시뮬레이션을 자동으로 실행하고, 각 시뮬레이션의 결과뿐만 아니라 최적의 **스케줄링 알고리즘** 선택을 위한 순위표를 제공합니다.

이 레포지토리에서 사용된 **용어**에 대해 더 알고 싶다면, [여기](#용어)를 참조해주세요.

<!-- [![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE) -->

## 빠른 시작

### 의존성

이 프레임워크는 다음의 의존성을 요구합니다.

- Ubuntu 20.04 >
- Git
- Python 3.7 >
- C/C++ 빌드 환경

다음 명령어를 통해 의존성을 설치할 수 있습니다.

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install git python3 python3-pip openssh-server build-essential -y
```

### 설치

먼저, 다음 명령어를 통해 레포지토리를 클론합니다.

```bash
git clone https://github.com/sopiot/simulation-framework.git
```

그리고, 다음 명령어로 `simulation-framework` 파이썬 패키지를 설치합니다.

```bash
cd simulation-framework
pip3 install .
```

### 기본 사용법

다음 명령어로 로컬 머신에서 간단한 시뮬레이션을 실행할 수 있습니다.

````bash

```bash
cd sim_env_samples
python3 run.py -c ../sim_env_samples/simple_home_local -po ../scheduling_algorithm/samples
````

위 명령어로 처음 시뮬레이션을 실행하면, `localhost`의 현재 사용자에 대한 비밀번호 정보를 입력하라는 메시지가 나타납니다. 비밀번호를 입력하면, `localhost`의 디바이스 정보가 **시뮬레이션 환경 파일**에서 지정한 `device_pool_path`에 자동으로 저장됩니다 (기본 `device_pool_path`는 **`${ROOT}/device_pool.yml`** 로 설정되어 있습니다). 저장된 내용은 다음과 같습니다:

```yaml
localhost:
  host: localhost
  ssh_port: 22
  user: UserName
  password: "PaSsWoRD"
```

`-c` 옵션을 사용하여 사용자는 **시뮬레이션 환경 파일**이 포함된 디렉토리 또는 디렉토리 목록을 지정할 수 있으며, `-po` 옵션을 사용하여 **스케줄링 알고리즘 파일**이 포함된 디렉토리 또는 디렉토리 목록을 지정할 수 있습니다. 사용자는 저장소의 `sim_env_sample`과 `scheduling_algorithm/samples` 디렉토리에 위치한 사전 정의된 **시뮬레이션 환경 파일**과 **스케줄링 알고리즘 파일**을 사용하거나 자신만의 **시뮬레이션 환경 파일**과 **스케줄링 알고리즘 파일**을 정의할 수 있습니다. **시뮬레이션 환경 파일**은 `config` 문자열로 시작하는 `yaml` 파일이어야 합니다. **시뮬레이션 환경 파일**에 대한 자세한 정보는 [여기](#스케줄링-알고리즘-파일)에서 찾을 수 있습니다.

시뮬레이터는 시뮬레이션 환경과 **스케줄링 알고리즘**의 모든 조합에 대해 시뮬레이션을 실행합니다. 각 시뮬레이션이 완료된 후에는 시뮬레이션의 결과가 표시되고, 모든 시뮬레이션이 완료되면 시뮬레이션의 **스케줄링 알고리즘**의 순위 결과가 출력됩니다. 순위 결과는 QoS, 에너지, 안정성을 기반으로 **스케줄링 알고리즘**의 순위를 매기고 순위표를 터미널에 출력합니다. 각 테이블 항목에는 해당 항목에 대한 데이터와 시뮬레이션에 사용된 **시뮬레이션 환경 파일**을 출력합니다.

`Middleware`와 `Thing`이 로컬에서 실행되는 대신 원격 디바이스에 분산되는 경우, 추가적인 디바이스 정보를 **시뮬레이션 환경 파일**의 `device_pool_path`에 지정된 디바이스 풀 파일에 추가해야 합니다. 사용자는 `middleware`와 `thing` 섹션에 디바이스 항목을 추가함으로써 원격 디바이스를 추가할 수 있으며, 디바이스 항목이 지정되지 않은 경우 `Middleware`는 `device_pool_path`에 지정된 **디바이스 풀 파일**에서 `localhost`를 제외한 모든 디바이스를 사용하고, Thing은 `localhost`를 대상 디바이스로 사용합니다. **디바이스 풀 파일**에 대한 자세한 정보는 [여기](#디바이스-풀-파일)에서 찾을 수 있습니다.

### 고급 사용법

<div align="center">
<img src="imgs/sim_gen.png" width="400" alt="sim_gen" />
</div>

`-i` 옵션을 사용하여 사용자는 **시뮬레이션 데이터 파일**에서 직접 시뮬레이션을 수행할 수 있습니다. 이 경우, 시뮬레이터는 새로운 시뮬레이션 환경을 생성하는 대신 이미 생성된 시뮬레이션 환경을 로드합니다. 사용자는 여전히 `-po` 옵션을 사용하여 시뮬레이션에 사용할 **스케줄링 알고리즘**을 지정할 수 있습니다.

```bash
cd sim_env_samples
python3 run.py -i ../sim_env_samples/simple_test/<simulation_data_directory>/simulation_data.json -po ../scheduling_algorithm/samples
```

`-o` 옵션을 사용하여 시뮬레이션 결과 파일의 이름을 지정할 수 있습니다. `-o` 옵션을 지정하지 않으면 **시뮬레이션 환경 파일**에서 지정한 시뮬레이션의 이름이 기본 이름으로 사용됩니다. 또한, 사용자는 디버깅 목적으로 `-dl` 옵션을 사용하여 원격 디바이스에서 로그를 다운로드할 수 있습니다.

```bash
cd sim_env_samples
python3 run.py -i ../sim_env_samples/simple_test/<simulation_data_directory>/simulation_data.json -po ../scheduling_algorithm/samples -o test_result -dl
```

`-c`와 `-po` 옵션을 사용하면 사용자는 **시뮬레이션 환경 파일**(`config*.yml`)과 **스케줄링 알고리즘 파일**(`*.cc`)의 목록을 지정할 수 있습니다. 이 옵션들은 다음 명령와 같이 사용할 수 있습니다.

```bash
cd sim_env_samples
python3 run.py -c ../sim_env_samples/simple_home_local_multi_env/config_period5_10.yml \
                  ../sim_env_samples/simple_home_local_multi_env/config_period10_20.yml \
               -po ../scheduling_algorithm/samples/default.cc \
                  ../scheduling_algorithm/samples/energy_saving.cc \
                  ../scheduling_algorithm/samples/merge_execution.cc
```

### 프로파일링을 위한 시간 동기화

시뮬레이션을 수행한 후 각 시뮬레이션 단계에서 생성된 오버헤드를 측정하려면 각 디바이스 간에 시간을 동기화해야 합니다. 시뮬레이션 동안 `Middleware`와 `Thing`의 로그는 각 디바이스에 저장되며, 이러한 로그의 타임스탬프를 비교하여 오버헤드를 측정합니다. 각 단계에서 오버헤드를 정확하게 측정하려면 각 로그의 시간 기준점이 정밀하게 동기화 되어야 합니다. 이를 위해 **PTP 프로토콜**을 사용하여 디바이스 간의 시간을 동기화할 수 있습니다. `ptpd`를 사용하면 **PTP 프로토콜**을 사용한 정밀한 시간 동기화를 수행할 수 있습니다. `ptpd`는 다음과 같이 설치할 수 있습니다:

```bash
sudo apt install ptpd
```

The `ptp` protocol is based on Ethernet to reduce error due to network delay. Therefore, before running ptpd, each device must be connected to the same switch or router through an Ethernet interface.

After connecting each device via Ethernet, user can run `ptpd` with the command below. After `-i` option, specify the Ethernet interface of each device.

**PTP 프로토콜**은 네트워크 지연으로 인한 오류를 줄이기 위해 이더넷에 기반을 두고 있습니다. 따라서 `ptpd`를 실행하기 전에 각 디바이스를 이더넷 인터페이스를 통해 동일한 스위치나 라우터에 연결해야 합니다.

각 디바이스를 이더넷을 통해 연결한 후에는 아래의 명령어로 `ptpd`를 실행할 수 있습니다. `-i` 옵션 다음에는 각 디바이스의 이더넷 인터페이스를 지정합니다.

```bash
sudo ptpd -C -m -i <ethernet_interface>
```

If `ptpd` run on all devices to be synchronized, `ptpd` determines the optimal master time device and synchronizes the time of the slave devices based on the time of the master device.

동기화할 모든 디바이스에서 `ptpd`가 실행되면, `ptpd`는 최적의 마스터 시간 디바이스를 결정하고 마스터 디바이스의 시간을 기반으로 슬레이브 디바이스의 시간을 동기화합니다.

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

"`acquired clock control`" 메시지가 표시되면 시간 동기화가 완료된 것입니다. `-pf` 옵션을 주어 프로파일링을 수행할 수 있습니다. 만약 "`acquired clock control`" 메시지가 하나의 디바이스에서만 출력되지 않는다면, 해당 디바이스가 마스터 시간 디바이스로 결정된 것입니다. 이 경우, "`Now in state: PTP_MASTER`" 메시지의 가장 오른쪽에 "`(self)`" 메시지가 있는지 확인하세요. 이 메시지가 있다면, 해당 디바이스가 마스터 시간 디바이스로 결정된 것입니다.

```bash
cd sim_env_samples
python3 run.py -c ../sim_env_samples/<env_samples_directory> -po ../scheduling_algorithm/samples -pf
```

`-dl` 옵션을 주어 시뮬레이션을 실행하여 다운로드된 시뮬레이션 로그가 있다면, 사용자는 로그를 로드하여 프로파일링을 진행할 수 있습니다. 이 경우, 사용자는 `--only_profile` 옵션을 주어 프로파일링만 진행할 수 있습니다. 사용자는 `-log` 옵션으로 개별 시뮬레이션에 대한 로그를 프로파일링하거나, 폴더 내의 모든 로그에 대해 프로파일링을 진행할 수 있습니다. 여러 개의 로그에 대해 프로파일링을 진행하는 경우 모든 로그에 대한 프로파일링 결과의 평균을 출력합니다.

```bash
cd sim_env_samples
python3 run.py -log ../remote_logs/<simulation_log_sample> --only_profile
# python run.py -log ../remote_logs --only_profile
```

## 용어

이 섹션에서는 레포지토리에서 사용된 **용어**에 대해 설명합니다.

- **디바이스 풀 파일**

  시뮬레이션에서 사용될 디바이스들을 명세한 파일입니다. 자세한 정보는 [here](#디바이스-풀-파일)에서 확인할 수 있습니다.

- **시뮬레이션 환경 파일**

  시뮬레이션 환경을 명세한 파일입니다. 자세한 정보는 [here](#시뮬레이션-환경-파일)에서 확인할 수 있습니다.

- **사용자 미들웨어 트리 파일**

  미들웨어 계층구조를 명세한 파일입니다. 자세한 정보는 [here](#사용자-미들웨어-트리-파일)에서 확인할 수 있습니다.

- **스케줄링 알고리즘 파일**

  미들웨어의 **스케줄링 알고리즘**을 명세한 파일입니다. 자세한 정보는 [here](#스케줄링-알고리즘-파일)에서 확인할 수 있습니다.

- **시뮬레이션 데이터 파일**

  시뮬레이션 생성기에서 생성된 시뮬레이션 데이터가 저장된 파일입니다.

- **스케쥴링 정책**

  **스케줄링 알고리즘**의 구성 요소입니다. 이는 `Middleware`에서 발생하는 이벤트에 대해 어떻게 반응할지에 대해 **스케줄링 알고리즘 파일**에서 명세한 규칙의 집합입니다. 이에는 `OnMapService`와 `OnThingRegister`와 같은 함수들이 포함됩니다. 자세한 정보는 [here](#스케줄링-알고리즘-파일)에서 확인할 수 있습니다.

- **스케줄링 알고리즘**

  여러 **스케쥴링 정책**을 조합하여 만든 이벤트 반응 알고리즘. 알고리즘에 대한 내용은 **스케줄링 알고리즘 파일**에 명세됩니다. **스케줄링 알고리즘**을 통해 `Middleware`는 MySSIX IoT 플랫폼에서 발생한 이번트에 따라 어떠한 스케쥴링 동작을 할 것인지 결정할 수 있습니다. 자세한 정보는 [here](#스케줄링-알고리즘-파일)에서 확인할 수 있습니다.

- **Middleware**

  `Middleware`는 MySSIX IoT 플랫폼에서 중추적인 역할을 하는 소프트웨어입니다. 이는 IoT 시스템을 구별하는 단위로서, 여러 `Things`와 `Applications`을 관리합니다. `Middleware`는 `Things`의 상태를 모니터링하고 `Applications`의 상태를 제어하기 위한 적절한 행동을 선택합니다.

- **Middleware Tree**

  상위 `Middleware`와 하위 `Middleware` 간의 연결이 계층적으로 연결, 구조화된 것. 상위 `Middleware`와 하위 `Middleware`는 정보 교환을 통해 전체 IoT 시스템을 제어합니다.

- **Thing**

  사용자가 사용할 수 있는 `Service`를 제공하는 MySSIX IoT 플랫폼의 구성 요소 중 하나. 제공하는 `Service`의 종류에 따라 `Normal`과 `Super`로 분류됩니다.

  - **Normal**

    `Normal Service` 만을 제공하는 `Thing`.

  - **Super**

    `Super Service` 만을 제공하는 `Thing`.

- **Application**

  One of the components of an IoT system that combines the `Services` provided by a `Thing` to create a service routine. Depending on the type of service provided, it is classified into `Normal` and `Super`.
  `Thing`이 제공하는 `Services`를 결합하여 서비스 루틴을 생성하는 MySSIX IoT 플랫폼의 구성 요소 중 하나. 제공하는 `Service`의 종류에 따라 `Normal`과 `Super`로 분류됩니다.

  - **Normal**

    `Normal Service` 만을 결합하여 생성된 `Application`.

  - **Super**

    `Super Service` 만을 결합하여 생성된 `Application`.

- **Service**

  사용자에게 필요한 기능을 제공하며 `Thing`에 종속적인 MySSIX IoT 플랫폼의 구성 요소 중 하나. 사용자는 `Service`를 사용하는 `Application`을 `Middleware`에 등록하여 `Service`를 사용할 수 있습니다. 제공하는 서비스의 종류에 따라 `Normal`과 `Super`로 분류됩니다.

  - **Normal**

    하나의 기능을 담당하는 일반적인 `Service`.

  - **Super**

    여러 `Normal Service`를 결합하여 새로운 기능을 구현하도록 설계된 `Service`. **Middleware Tree** 상에서 상위 `Middleware`에 등록되면, 하위 `Middleware`에 연결된 사용자들에게 전역적으로 사용되어질 수 있는 기능을 제공합니다.

## 설정 파일들

이 섹션에서는 시뮬레이터가 사용하는 설정 파일들, 즉 **디바이스 풀 파일**, **시뮬레이션 환경 파일**, **사용자 미들웨어 트리 파일**, **스케줄링 알고리즘 파일**의 형식에 대해 설명합니다.

각 설정 파일은 다음과 같은 포맷을 사용하여 명세되어집니다.

> **옵션명**: `데이터 타입`
>
> 옵션에 대한 설명

설정 파일에서 사용되는 `데이터 타입`은 다음과 같습니다.

> - `str`: 문자열
> - `int`: 정수
> - `float`: 실수
> - `list`: 리스트
> - `[{데이터 타입}, {데이터 타입}]`: 데이터 범위 (최소, 최대)

각 `데이터 타입`은 중괄호 `{}`로 둘러싸여 있어, 이것이 `데이터 타입`임을 나타냅니다. 아래는 몇 가지 예시입니다.

> - `{str}` -> `test_string`
> - `{int}` -> `123`
> - `[{int}, {int}]` -> `[3, 4]`
> - `{list}` -> `[device1, device2, ...]`

### 디바이스 풀 파일

이 섹션에서는 **디바이스 풀 파일**의 형식에 대해 설명합니다. **디바이스 풀 파일**은 **시뮬레이션 환경 파일**에서 `device` 옵션을 지정할 때 사용할 수 있는 디바이스들에 대한 정보를 명세한 `yaml` 파일입니다. 기본적으로, `localhost`에 대한 정보를 포함해야 합니다. 시뮬레이션을 수행할 때 `localhost`에 대한 정보가 없는 경우, 시뮬레이터가 자동으로 이를 생성합니다. **디바이스 풀 파일**의 경로는 **시뮬레이션 환경 파일**의 `device_pool_path` 옵션을 사용하여 지정할 수 있습니다. 이 옵션이 지정되지 않은 경우, 기본 경로는 `device_pool.yml`로 설정됩니다.

**디바이스 풀 파일**은 다음과 같은 구조를 가지고 있습니다.

```yaml
middlerware_1: # 디바이스 이름
  host: 192.168.0.56
  password: PaSsW0rd
  ssh_port: 22
  mqtt_port: 1883
  user: test_user
```

- **device_name**: `{str}`

  디바이스의 이름. **시뮬레이션 환경 파일** 안에서 `device` 옵션을 명세할 때 사용할 수 있습니다.

- **host**: `{str}`

  디바이스의 IP 주소 또는 도메인 이름.

- **user**: `{str}`

  SSH 접속 시 사용할 유저 이름.

- **password**: `{str}`

  SSH 접속 시 사용할 비밀번호.

- **ssh_port**: `int`

  SSH 접속 시 사용할 포트 번호.

- **mqtt_port**: `int`

  디바이스가 `Middleware`로 사용될 때 이용할 MQTT 포트 번호.

### 시뮬레이션 환경 파일

이 섹션에서는 **시뮬레이션 환경 파일**의 형식에 대해 설명합니다. **시뮬레이션 환경 파일**은 시뮬레이션이 진행된 환경을 어떻게 생성할 것인지에 대해 명세한 `yaml` 파일입니다. 이 파일은 `config_simple_home.yml`과 같이 "`config`" 문자열로 시작해야 합니다.

**시뮬레이션 환경 파일**은 다음과 같은 구조를 가지고 있습니다.

- **simulation**

  시뮬레이션 자체에 대한 설정을 명세하는 섹션.

  - **name**: `{str}`

    시뮬레이션 이름. 기본값은 **시뮬레이션 환경 파일**의 이름입니다.

  - **running_time**: `{float}`

    시뮬레이션의 실행 시간. 기본값은 `120초`입니다.

  - **device_pool_path**: `{str}`

    **시뮬레이션 환경 파일** 내에서 디바이스 풀을 지정하는데 사용할 **디바이스 풀 파일** 경로. 기본값은 `${ROOT}/device_pool.yml` 입니다.

  - **service_thing_pool_path**: `{str}`

    시뮬레이션에서 사용될 `Service`, `Thing`에 대한 풀 정보를 담고 있는 파일. 파일이 존재하지 않는 경우, 지정된 경로에 파일을 생성합니다. 기본값은 `service_thing_pool.yml`입니다.

  - **force_generate**: `{str}`

    `Service`, `Thing` 풀을 강제로 생성하도록 하는 옵션. 이 옵션이 `true`로 설정되면, 풀 파일이 존재하더라도 새로운 `Service`, `Thing` 풀을 생성합니다. 기본값은 `false`입니다.

  - **event_timeout**: `{float}`

    시뮬레이션을 수행할 때 실행되는 이벤트에 대한 타임아웃 시간. 기본값은 `15초`입니다.

  - **local_mode**: `{float}`

    로컬 디바이스 내에서만 시뮬레이션을 실행하는 옵션. 기본값은 false입니다.

- **middleware**

  시뮬레이션에서 사용할 `Middleware`에 대한 설정을 명세하는 섹션. `random`과 `manual` 중 하나를 반드시 지정해야 합니다.

  - **random**

    무작위로 **Middleware Tree** 를 생성할 때 사용되는 옵션. `manual` 옵션이 지정된 경우 무시됩니다.

    - **height**: `[{int}, {int}]`

      `Middleware` 계층의 높이.

    - **width**: `[{int}, {int}]`

      `Middleware` 당 자식 `Middleware`의 개수.

    - **normal**, **super**

      미들웨어에 등록될 `Thing`과 `Application`에 대한 설정. `normal`과 `super`로 나뉘며, 각각 `Normal Thing`과 `Normal Application`, `Super Thing`과 `Super Application`에 대한 설정을 의미합니다. `normal`과 `super` 둘 다 명세되어야 합니다.

      - **thing_per_middleware**: `[{int}, {int}]`

        `Middleware`당 등록될 `Thing`의 개수.

      - **application_per_middleware**: `[{int}, {int}]`

        `Middleware`당 등록될 `Application`의 개수.

  - **manual**: `{str}`

    **사용자 미들웨어 트리 파일** 파일의 경로. 자세한 정보는 [here](#사용자-미들웨어-트리-파일)에서 찾을 수 있습니다. `random` 옵션보다 우선하여 적용됩니다.

  - **remote_middleware_path**: `{str}`

    원격 디바이스에서의 `Middleware` 경로. 기본값은 `/tmp/middleware` 입니다.

  - **remote_middleware_config_path**: `{str}`

    The path of the `Middleware` configuration file to be saved on the remote device. If not specified, `/tmp/middleware_config` is set as default.
    원격 디바이스에 저장될 `Middleware` 설정 파일의 경로. 기본값은 `/tmp/middleware_config`입니다.

  - **device**: `list[string]`

    A list of devices to be used as `Middleware` devices. It must be specified as a device specified in the device list read from the `device_pool_path` path. If not specified, the device list except for `localhost` among the list of devices specified in `device_pool_path` is set as default.
    `Middleware`로 사용될 디바이스의 목록입니다. `device_pool_path` 경로에서 읽은 **디바이스 풀 파일**에 명세된 디바이스의 이름으로 명세되어야 합니다. 기본값은 빈 리스트로 지정되며, 시뮬레이션을 실행할 때 초기단계에서 사용자 상호작용을 통해 지정되어질 수 있습니다.

- **service**

  A section that specifies settings for `Service` to be used in the simulation.

  - **normal**, **super**

    **normal** and **super** must both be specified. In the case of `normal`, it means setting for `Normal Service`, and in the case of `super`, it means setting for `Super Service`.

    - **normal**

      - **service_type_num**: `{int}`

        The number of `Normal Service` types.

      - **energy**: `[{int}, {int}]`

        Energy consumed to run `Normal Service`.

      - **execute_time**: `[{int}, {int}]`

        Time spent running `Normal Service`.

    - **super**

      - **service_type_num**: `{int}`

        The number of `Super Service` types.

      - **service_per_super_service**: `{int}`

        The number of `Normal Service` in `Super Service`.

- **thing**

  A section that specifies settings for `Thing` to be used in the simulation.

  - **remote_thing_folder_path** _(optional)_: `{str}`

    The path of the `Thing` file to be saved on the remote device. If not specified, it defaults to `/tmp/thing`.

  - **device**: `{list[string]}`

    List of devices to be used in the simulation. It should be specified with the devices listed in the device list read from the `device_pool_path` path. If not specified, the default value is a device list that includes only `localhost` from the device list specified in `device_pool_path` (`[localhost]`).

  - **normal**, **super**

    **normal** and **super** must both be specified. In the case of `normal`, it means setting for `Normal Thing`, and in the case of `super`, it means setting for `Super Thing`.

    - **service_per_thing**: `[{int}, {int}]`

      A number of `Service` per `{Normal|Super} Thing`.

    - **fail_error_rate**: `{float}`

      Probability of failure when performing `Service` of `{Normal|Super} Thing`.

    - **broken_rate**: `{float}`

      The probability that `{Normal|Super} Thing` will terminate mid-simulation (unnoticed by `Middleware`).

    - **unregister_rate**: `{float}`

      The probability that `{Normal|Super} Thing` will terminate mid-simulation (noticed by `Middleware`).

- **application**

  Section specifying settings for `Application` to be used in the simulation.

  - **normal**, **super**

    **normal** and **super** must both be specified. In the case of `normal`, it means setting for `Normal Application`, and in the case of `super`, it means setting for `Super Application`.

    - **service_per_application**: `[{int}, {int}]`

      A number of `Service` per `{Normal|Super} Application`.

    - **period**: `[{int}, {int}]`

      Loop period of `{Normal|Super} Application`.

### 사용자 미들웨어 트리 파일

Users can configure a custom `Middleware` layer structure to perform simulations by specifying a **사용자 미들웨어 트리 파일** and providing its path in the `manual` option of the **시뮬레이션 환경 파일**. The **사용자 미들웨어 트리 파일** should be in `yaml` format and have the following structure.

```yaml
# 사용자 미들웨어 트리 파일 example
- name: middleware
  device: [localhost]
  thing_num: [0, 0]
  application_num: [0, 0]
  super_thing_num: [1, 1]
  super_application_num: [2, 2]
  children:
    - name: middleware
      device: [localhost]
      thing_num: [10, 10]
      application_num: [10, 10]
      super_thing_num: [0, 0]
      super_application_num: [2, 2]
      children: []
    - name: middleware
      device: [localhost]
      thing_num: [10, 10]
      application_num: [10, 10]
      super_thing_num: [0, 0]
      super_application_num: [2, 2]
      children: []
```

- **name**: `{str}`

  Name of `Middleware`

- **device**: `list[string]`

  The list of devices to be used in the simulation must be specified according to the devices listed in the `device_pool_path`. If not specified, the default device list will exclude `localhost` from the device list specified in `device_pool_path`.

- **thing_num**: `[{int}, {int}]`

  The number of things per `Middleware`. The two numbers in `[]` mean the minimum and maximum values.

- **application_num**: `[{int}, {int}]`

  Number of Applications per `Middleware`. The two numbers in `[]` mean the minimum and maximum values.

- **super_thing_num**: `[{int}, {int}]`

  The number of Super Thing per `Middleware`. The two numbers in `[]` mean the minimum and maximum values.

- **super_application_num**: `[{int}, {int}]`

  The number of Super Applications per `Middleware`. The two numbers in `[]` mean the minimum and maximum values.

- **child**: `{list}`

  A list of sub `Middleware`. Specify `null` to not create a child `Middleware`.

### 스케줄링 알고리즘 파일

Refer to [`scheduling_algorithm`](scheduling_algorithm/README.md) directory.

## 트러블슈팅

### ptpd takes too long to time synchronization

If the message `acquired clock control`" is not print and time synchronization is still in progress, please check that the device is not a master time device. At the far right of the message with "`Now in state: PTP_MASTER`" is `" If there is (self)"`, the device is selected as the master time device, so you only need to check the synchronization status of the rest of the slave devices.

If none of the above apply, time synchronization has not yet been completed, so please wait for a while. If time synchronization does not proceed no matter how long you wait, try closing `ptpd` and running it again.
