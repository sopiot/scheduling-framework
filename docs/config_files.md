# 설정 파일들

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
> - `{float}` -> `123.123`
> - `{list}` -> `[device1, device2, ...]`
> - `[{int}, {int}]` -> `[1, 3]`

## 디바이스 풀 파일

이 섹션에서는 **디바이스 풀 파일**의 형식에 대해 설명합니다. **디바이스 풀 파일**은 **시뮬레이션 환경 파일**에서 `device` 옵션을 지정할 때 사용할 수 있는 디바이스들에 대한 정보를 명세한 `.yaml` 형식 파일입니다. 기본적으로, `localhost`에 대한 정보를 포함해야 합니다. 시뮬레이션을 수행할 때 `localhost`에 대한 정보가 없는 경우, 시뮬레이터가 자동으로 이를 생성합니다. **디바이스 풀 파일**의 경로는 **시뮬레이션 환경 파일**의 `device_pool_path` 옵션을 사용하여 지정할 수 있습니다. 이 옵션이 지정되지 않은 경우, 기본 경로는 `device_pool.yml`로 설정됩니다.

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

  디바이스가 **Middleware**로 사용될 때 이용할 MQTT 포트 번호.

## 시뮬레이션 환경 파일

이 섹션에서는 **시뮬레이션 환경 파일**의 형식에 대해 설명합니다. **시뮬레이션 환경 파일**은 시뮬레이션이 진행된 환경을 어떻게 생성할 것인지에 대해 명세한 `.yaml` 형식 파일입니다. 이 파일은 `config_simple_home.yml`과 같이 `"config"` 문자열로 시작해야 합니다.

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

    시뮬레이션에서 사용될 **Service**, **Thing**에 대한 풀 정보를 담고 있는 파일. 파일이 존재하지 않는 경우, 지정된 경로에 파일을 생성합니다. 기본값은 `service_thing_pool.yml`입니다.

  - **force_generate**: `{str}`

    **Service**, **Thing** 풀을 강제로 생성하도록 하는 옵션. 이 옵션이 `true`로 설정되면, 풀 파일이 존재하더라도 새로운 **Service**, **Thing** 풀을 생성합니다. 기본값은 `false`입니다.

  - **event_timeout**: `{float}`

    시뮬레이션을 수행할 때 실행되는 이벤트에 대한 타임아웃 시간. 기본값은 `15초`입니다.

  - **local_mode**: `{float}`

    로컬 디바이스 내에서만 시뮬레이션을 실행하는 옵션. `middleware`, `thing`섹션의 `device` 옵션보다 우선하여 적용됩니다. 기본값은 `false`입니다.

- **middleware**

  시뮬레이션에서 사용할 **Middleware**에 대한 설정을 명세하는 섹션. `random`과 `manual` 중 하나를 반드시 지정해야 합니다.

  - **random**

    무작위로 **Middleware Tree** 를 생성할 때 사용되는 옵션. `manual` 옵션이 지정된 경우 무시됩니다.

    - **height**: `[{int}, {int}]`

      **Middleware** 계층의 높이.

    - **width**: `[{int}, {int}]`

      **Middleware** 당 자식 **Middleware**의 개수.

    - **normal**, **super**

      **Middleware**에 등록될 **Thing**과 **Application**의 속성에 대한 설정. `normal`과 `super`로 나뉘며, 각각 **Normal Thing**과 **Normal Application**, **Super Thing**과 **Super Application**에 대한 설정을 의미합니다. `normal`과 `super` 둘 다 명세되어야 합니다.

      - **thing_per_middleware**: `[{int}, {int}]`

        **Middleware**당 등록될 **Thing**의 개수.

      - **application_per_middleware**: `[{int}, {int}]`

        **Middleware**당 등록될 **Application**의 개수.

  - **manual**: `{str}`

    **사용자 미들웨어 트리 파일** 파일의 경로. 자세한 정보는 [여기](#사용자-미들웨어-트리-파일)을 참고하시기 바랍니다. `random` 옵션보다 우선하여 적용됩니다.

  - **remote_middleware_path**: `{str}`

    원격 디바이스에서의 **Middleware** 경로. 기본값은 `/tmp/middleware` 입니다.

  - **remote_middleware_config_path**: `{str}`

    원격 디바이스에 저장될 **Middleware** 설정 파일의 경로. 기본값은 `/tmp/middleware_config`입니다.

  - **device**: `list[string]`

    **Middleware**로 사용될 디바이스의 목록입니다. `device_pool_path` 경로에서 읽은 **디바이스 풀 파일**에 명세된 디바이스의 이름으로 명세되어야 합니다. 기본값은 빈 리스트로 지정되며, 시뮬레이션을 실행할 때 초기단계에서 사용자 상호작용을 통해 지정되어질 수 있습니다.

- **service**

  시뮬레이션에서 사용할 **Service**에 대한 설정을 명세하는 섹션.

  - **normal**, **super**

    **Middleware**에 등록될 **Service**의 속성에 대한 설정. `normal`과 `super`로 나뉘며, 각각 **Normal Service**, **Super Service**에 대한 설정을 의미합니다. `normal`과 `super` 둘 다 명세되어야 합니다.

    - **normal**

      - **service_type_num**: `{int}`

        **Normal Service** 타입의 개수.

      - **energy**: `[{int}, {int}]`

        **Normal Service**의 에너지 소모량.

      - **execute_time**: `[{int}, {int}]`

        **Normal Service**의 수행 시간.

    - **super**

      - **service_type_num**: `{int}`

        **Super Service** 타입의 개수.

      - **service_per_super_service**: `{int}`

        **Super Service** 내부의 **Normal Service**의 개수.

- **thing**

  시뮬레이션에서 사용할 **Thing**에 대한 설정을 명세하는 섹션.

  - **remote_thing_folder_path**: `{str}`

    원격 디바이스에 저장될 **Thing** 코드 파일의 경로. 기본값은 `/tmp/thing`으로 설정됩니다.

  - **device**: `{list[string]}`

    시뮬레이션에 사용될 디바이스의 목록. `device_pool_path` 경로에서 로드한 **디바이스 풀 파일**에 있는 디바이스 이름으로 명세합니다.
    기본값은 `device_pool_path`에서 지정한 디바이스 중 `localhost`만 포함하는 디바이스 목록(`[localhost]`)입니다.

  - **normal**, **super**

    **Middleware**에 등록될 **Thing**의 속성에 대한 설정. `normal`과 `super`로 나뉘며, 각각 **Normal Thing**, **Super Thing**에 대한 설정을 의미합니다. `normal`과 `super` 둘 다 명세되어야 합니다.

    - **normal**

      - **service_per_thing**: `[{int}, {int}]`

        **Normal Thing**당 **Service**의 개수.

      - **fail_error_rate**: `{float}`

        **Normal Thing**에서 **Service**를 수행할 때 실패할 확률.

      - **broken_rate**: `{float}`

        **Normal Thing**이 시뮬레이션 중간에 종료될 확률. (_미들웨어가 인지하지 못함._)

      - **unregister_rate**: `{float}`

        **Normal Thing**이 시뮬레이션 중간에 언레지스터될 확률. (_미들웨어가 인지함._)

    - **super**

      - **service_per_thing**: `[{int}, {int}]`

        **Super Thing**당 **Service**의 개수.

      - **fail_error_rate**: `{float}`

        **Super Thing**에서 **Service**를 수행할 때 실패할 확률.

      - **broken_rate**: `{float}`

        **Super Thing**이 시뮬레이션 중간에 종료될 확률. (_미들웨어가 인지하지 못함._)

      - **unregister_rate**: `{float}`

        **Super Thing**이 시뮬레이션 중간에 언레지스터될 확률. (_미들웨어가 인지함._)

- **application**

  시뮬레이션에서 사용할 **Application**에 대한 설정을 명세하는 섹션.

  - **normal**, **super**

    **Middleware**에 등록될 **Application**의 속성에 대한 설정. `normal`과 `super`로 나뉘며, 각각 **Normal Application**, **Super Application**에 대한 설정을 의미합니다. `normal`과 `super` 둘 다 명세되어야 합니다.

    - **normal**

      - **service_per_application**: `[{int}, {int}]`

        **Normal Application**당 **Service**의 개수.

      - **period**: `[{int}, {int}]`

        **Normal Application**의 실행 주기.

    - **super**

      - **service_per_application**: `[{int}, {int}]`

        **Super Application**당 **Service**의 개수.

      - **period**: `[{int}, {int}]`

        **Super Application**의 실행 주기.

## 사용자 미들웨어 트리 파일

프레임워크는 사용자가 수동으로 **미들웨어 트리 파일**을 명세할 수 있는 기능을 제공합니다. **미들웨어 트리 파일** 경로를 **시뮬레이션 환경 파일**의 `manual` 옵션에 명세하여 시뮬레이션을 실행할 수 있습니다. **미들웨어 트리 파일**은 `.yaml` 형식 파일이어야 하며, 아래와 같은 구조를 가져야 합니다.

```yaml
name: middleware
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

  **Middleware**의 이름.

- **device**: `list[string]`

  시뮬레이션에 사용할 디바이스의 목록은 `device_pool_path`에서 지정한 **디바이스 풀 파일**에 있는 디바이스로 명세하여야 합니다. 기본값은 **디바이스 풀 파일**에 있는 디바이스 중 `localhost`를 제외한 모든 디바이스에 대한 리스트 입니다.

- **thing_num**: `[{int}, {int}]`

  **Middleware**당 **Thing**의 개수.

- **application_num**: `[{int}, {int}]`

  **Middleware**당 **Application**의 개수.

- **super_thing_num**: `[{int}, {int}]`

  **Middleware**당 **Super Thing**의 개수.

- **super_application_num**: `[{int}, {int}]`

  **Middleware**당 **Super Application**의 개수.

- **children**: `{list}`

  자식 **Middleware**의 리스트. 자식 **Middleware**가 없는 경우 빈 리스트(`[]`) 또는 `null`로 지정합니다.

## 스케줄링 알고리즘 파일

**스케줄링 알고리즘 파일**은 MySSIX IoT 플랫폼에서 발생하는 이벤트에 대해 **Middleware**가 어떤 스케쥴링 동작을 수행할 것인지 명세한 파일입니다. `.cc` 형식의 C++ 코드 파일이며 `scheduling_algorithm` 디렉토리에 있는 파일들은 원격 디바이스에 **스케쥴링 알고리즘 파일**와 같이 전송되어 **스케쥴링 알고리즘** 공유 라이브러리 파일을 컴파일하는데 사용됩니다. 컴파일된 **스케쥴링 알고리즘** 공유 라이브러리 파일은 **Middleware** 바이너리 파일을 실행할 때 로드되어 **스케쥴링 알고리즘**을 수행하는데 사용됩니다. 레포지토리에서 사전 정의된 **스케줄링 알고리즘 파일**을 제공하며 [여기](../scheduling_algorithm/README.kr.md)에서 사전 정의된 **스케줄링 알고리즘 파일**에 대한 설명을 보실 수 있습니다.
