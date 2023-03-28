# MySSIX Simulator Examples

이 폴더에는 MySSIX 시뮬레이터를 사용하는 예제가 포함되어 있습니다.

`simple_home_*`, `simple_building_*`, `simple_campus_*`, `paper_experiment`로 폴더가 나뉘어져 있으며 `simple` 부분은 `local`과 `remote`로 나누어져 있습니다. `*_local` 예제는 시뮬레이션의 모든 요소를 로컬 머신에서 직접 실행시키는 예제이며, `*_remote` 예제는 시뮬레이션의 요소 중 `Middleware`는 원격 머신에서 실행시키고 `Thing`은 로컬 머신에서 실행시키는 예제입니다. `paper_experiment`예제는 논문의 실험을 재현하기 위한 예제입니다. 이 예제의 경우 `remote` 설정으로 시뮬레이션을 돌리게 됩니다.

## Case 1: Simulation simple home environment

총 1개의 `Middleware`를 레벨1 에서 실행하며 계층 구조는 만들지 않는 시뮬레이션 입니다. 1개의 `Super Thing`과 2개의 `Super Application`, 10개의 `Normal Thing`과 10개의 `Normal Application`을 `Middleware`에 등록하여 시뮬레이션을 수행합니다. `local`, `remote`, `multi_env`으로 해서 총 3개의 설정으로 돌릴 수 있고 `multi_env`의 경우 2 개의 시뮬레이션 환경 파일과 2개의 policy 파일에 대해 시뮬레이션을 총 4번 돌려 2개의 policy의 비교 결과를 출력합니다.

## Case 2: Simulation simple building environment

총 5개의 `Middleware`를 실행하며 계층 구조는 레벨2에 1개의 `Middleware`를, 레벨1에는 4개의 `Middleware`를 실행합니다 *(1 - 4)*. 레벨 1의 `Middleware`에만 1개의 10개의 `Normal Thing`과 10개의 `Normal Application`을 `Middleware`에 등록하며, `Super Thing`은 최상위 `Middleware`에 1개를, `Super Application`은 최상위, 최하위 `Middleware`에 각각 2개씩 등록하여 시뮬레이션을 수행합니다. `local`, `remote`으로 해서 총 2개의 설정으로 돌릴 수 있습니다.

## Case 3: Simulation simple campus environment

총 7개의 `Middleware`를 실행하며 계층 구조는 레벨3에 1개의 `Middleware`를, 레벨2에는 2개의 `Middleware`를, 레벨1에는 4개의 `Middleware`를 실행합니다 *(1 - 2 - 4)*. 레벨 1의 `Middleware`에만 1개의 10개의 `Normal Thing`과 10개의 `Normal Application`을 `Middleware`에 등록하며, `Super Thing`은 최상위 `Middleware`에 1개를, `Super Application`은 최상위, 최하위 `Middleware`에 각각 2개씩 등록하여 시뮬레이션을 수행합니다. `local`, `remote`, `local_random`으로 해서 총 2개의 설정으로 돌릴 수 있고 `local_random`의 경우 `random` 설정을 활성화 하여 무작위로 생성된 높이 3, 너비 2의 `Middleware` 계층 구조로 시뮬레이션을 수행합니다.

## Case 4: Simulation paper experiments

논문에서 수행된 실험을 재현할 수 있는 시뮬레이션 환경입니다. `Middleware`는 원격 디바이스에 1개씩 실행하고 `Super Thing`을 제외한 `Normal Thing`은 로컬 머신에 돌리는 것을 기본설정으로 하여 시뮬레이션을 수행합니다. `Super Thing`의 경우 `Middleware`와 같은 디바이스에서 실행됩니다.
