# 사전 정의 시뮬레이션 환경 파일 및 예제

이 페이지에서는 사전 정의된 **시뮬레이션 환경 파일**을 사용하는 예제들에 대해 설명합니다.

예제들은 `simple_home_*`, `simple_building_*`, `simple_campus_*`, 그리고 `paper_experiment`라는 이름의 폴더로 나누어져 있습니다. `simple`로 시작하는 폴더안에 있는 예제들은 `local`과 `remote`예제로 나누어져 있습니다. `local` 예제는 모든 시뮬레이션 구성 요소를 로컬 디바이스에서 직접 실행하고, `remote` 예제는 **Middleware** 구성 요소를 원격 디바이스에서 실행하고 **Thing** 구성 요소를 로컬 디바이스에서 실행합니다. `paper_experiment` 폴더에는 기반 논문에서의 실험을 재현할 수 있는 예제가 들어있습니다.

## Case 1: Simple Home

이 예제에서는 계층 구조를 생성하지 않고 레벨 1에서 1개의 **Middleware**만을 실행합니다. **Middleware**에 1개의 **Super Thing**, 2개의 **Super Application**, 10개의 **Normal Thing**, 그리고 10개의 **Normal Application**을 등록하여 시뮬레이션을 실행합니다. 이 예제 시뮬레이션은 `local`, `remote` 설정으로 실행할 수 있습니다.

## Case 2: Simple Building

이 예제에서는 레벨 2에서 1개의 **Middleware**와 레벨 1에서 4개의 **Middleware**를 실행합니다. 레벨 1의 **Middleware**만 10개의 **Normal Thing**와 10개의 **Normal Application**을 등록합니다. 최상위 **Middleware**에 1개의 **Super Thing**을 등록하고, 각각 최상단과 최하단의 **Middleware**에 2개의 **Super Application**을 등록하여 시뮬레이션을 실행합니다. 이 예제 시뮬레이션은 `local`, `remote` 설정으로 실행할 수 있습니다.

## Case 3: Simple Campus

This simulation runs seven `Middleware`, with one `Middleware` at level 3, two `Middleware` at level 2, and four `Middleware` at level 1. Only the `Middleware` at level 1 registers 10 `Normal Things` and 10 `Normal Application` with the `Middleware`. It registers one `Super Thing` with the top-level `Middleware` and two `Super Application` with the top and bottom `Middleware`, respectively. It can be run with local, remote, or `local_random` settings. With `local_random`, the simulation is run with a randomly generated hierarchical structure of 3 levels and 2 widths.

이 예제에서는 레벨 3에서 1개의 **Middleware**와 레벨 2에서 2개, 레벨 1에서 4개의 **Middleware**를 실행합니다. 최하위 레벨 1의 **Middleware**에만 10개의 **Normal Thing**와 10개의 **Normal Application**을 등록합니다. 최상위 **Middleware**에 1개의 **Super Thing**을 등록하고, 각각 최상단과 최하단의 **Middleware**에 2개의 **Super Application**을 등록하여 시뮬레이션을 실행합니다. 이 예제 시뮬레이션은 `local`, `remote` 설정으로 실행할 수 있습니다.

## Case 4: Paper Experiments

이 예제에서는 논문에서 수행한 실험을 재현할 수 있습니다. 기본적으로 원격 디바이스에서 1개의 **Middleware**를 실행하고 **Super Thing**을 제외한 모든 **Normal Thing**을 로컬 디바이스에서 실행합니다. **Super Thing**은 **Middleware**와 동일한 디바이스에서 실행됩니다. `device_pool_path` 경로에 있는 **디바이스 풀 파일**에서 지정된 디바이스들은 `localhost`정보와 최소 11개의 Raspberry Pi 디바이스 정보가 명세되어있어야 합니다.
