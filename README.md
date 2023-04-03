# Simulation Framework for Hierarchical Edge-based IoT

<div style="text-align:center">
  <img src="imgs/sim_overview.png" width="500" alt="sim_overview" style="margin-right:0px" />
</div>

This is a framework that is designed to fine-tune the **scheduling algorithm** of the middleware based on an IoT environment simulator. Using this simulator, users can implement their own **scheduling algorithm** and simulate the IoT system. The framework automates running multiple simulations with multiple environments and **scheduling algorithm**, and provides not only the results of each simulation but also the rankings of each objective to pick the best one. If you want to learn more about the **Terminology** used in this repository, please refer to [here](#terminology).

<!-- [![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE) -->

## Getting Started

### Prerequisites

The framework requires the following prerequisites:

- Ubuntu 20.04 or later
- Git
- Python 3.7 or higher
- C/C++ build environment

You can install the prerequisites using the following commands:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install git python3 python3-pip openssh-server build-essential -y
```

### Installation

First, clone the repository using the following command:

```bash
git clone https://github.com/sopiot/simulation-framework.git
```

Then, install the `simulation-framework` Python package using the following command:

```bash
cd simulation-framework
pip3 install .
```

### Basic Usage

You can run a simple simulation on your local machine by using the following command:

```bash
python3 run.py -e sim_env_samples/simple_home_local -p scheduling_algorithm/samples
```

If you run the command for the first time, you will be prompted to enter the password information for the current user on `localhost`. Upon entering the password, the device information for `localhost` will be automatically saved in the `device_pool_path` specified in the **Simulation Environment file** (default: `${ROOT}/device_pool.yml`), as follows:

```yaml
localhost:
  host: localhost
  ssh_port: 22
  user: UserName
  password: "PaSsWoRD"
```

Using the `-e` option, the user can specify a directory or a list of directories containing **Simulation Environment file**, while the `-p` option is used to specify a directory or a list of directories containing **Scheduling Algorithm file**. Users can either use the predefined **Simulation Environment file** and **Scheduling Algorithm file** located in the repository's `sim_env_sample` and `scheduling_algorithm/samples` directories or define their own **Simulation Environment file** and **Scheduling Algorithm file**. **Simulation Environment file** must be `yaml` file starting with the `config` string. More detailed information about **Simulation Environment file** can be found [here](#simulation-environment-file).

The simulator runs simulations with every combinations of Simulation Environment and **Scheduling Algorithm**. After each simulation is completed, the results for each simulation are displayed, and once all simulations have been completed, the ranking results for all simulations are output. The ranking results rank simulations based on QoS, energy, and stability and output a table format of the ranking table on the terminal. Each table entry displays the corresponding data for each ranking item and which **Simulation Environment file** was used for the simulation.

If the `Middleware` and `Thing` are distributed to remote devices instead of running locally, additional device information must be added to the **Device Pool file** specified in `device_pool_path` of **Simulation Environment file**. Users can add remote devices by adding the device item to the `middleware` and `thing` sections of the **Simulation Environment file**, and if no device item is specified, the `Middlware` uses all devices from the **Device Pool file** specified in `device_pool_path` except for localhost, while the Thing uses localhost as the target device. More detailed information about the **Device Pool file** can be found [here](#device-pool-file).

### Advanced Usage

<div align="center">
<img src="imgs/sim_gen.png" width="400" alt="sim_gen" />
</div>

Users can perform simulations directly from **Simulation Data file** by using the `-s` option. In this case, the simulator loads the simulation environment that has already been generated, rather than creating a new simulation environment. Users can still specify which **scheduling algorithm** to use for the simulation by using the `-p` option.

```bash
python3 run.py -s sim_env_samples/simple_test/<simulation_data_directory>/simulation_data.json -p scheduling_algorithm/samples
```

The `-o` option can be used to specify the name of the result file. If the `-o` option is not specified, the name of the simulation specified in the **Simulation Environment file** will be used as the default name. In addition, users can download logs from a remote device for debugging purposes using the `-dl` option.

```bash
python3 run.py -s sim_env_samples/simple_test/<simulation_data_directory>/simulation_data.json -p scheduling_algorithm/samples -o test_result -dl
```

The `-e` and `-p` options allow users to specify a list of **Simulation Environment file** (`config*.yml`) and **Scheduling Algorithm file** (`*.cc`). These options can be used as shown in the following command:

```bash
python3 run.py -e sim_env_samples/simple_home_local_multi_env/config_period5_10.yml \
                  sim_env_samples/simple_home_local_multi_env/config_period10_20.yml \
               -p scheduling_algorithm/samples/default.cc \
                  scheduling_algorithm/samples/energy_saving.cc \
                  scheduling_algorithm/samples/merge_execution.cc
```

## Terminology

This section explains the terminology used in the Scheduling Framework.

- **Device Pool file**

  A file that specifies the devices to be used in the simulation. More information can be found [here](#device-pool-file).
- **Simulation Environment file**
  
  A file that specifies the simulation environment. More information can be found [here](#simulation-environment-file).
- **Manual Middleware Tree file**
  
  A file that specifies the middleware hierarchy. More information can be found [here](#manual-middleware-tree-file).
- **Scheduling Algorithm file**
  
  A file that specifies the **Scheduling Algorithm** of the middleware. More information can be found [here](#scheduling-algorithm-file).
- **Simulation Data file**
  
  A file that stores the simulation data generated by the simulation generator.

- **Scheduling Policy**

  A component of the **Scheduling Algorithm**. It is a set of rules specified in the **Scheduling Algorithm** file on how to react to events occurring in the `Middleware`. It includes functions such as `OnMapService` and `OnThingRegister`. More information can be found [here](#scheduling-algorithm-file)
- **Scheduling Algorithm**
  
  An event response algorithm of the `Middleware` created by combining multiple **Scheduling Policy**. The combined algorithm is specified in a single **Scheduling Algorithm** file. More information can be found [here](#scheduling-algorithm-file)

- **Middleware**

  `Middleware` is software that plays a central role in an IoT system. It acts as a unit that distinguishes IoT systems and manages multiple `Things` and `Applications`. `Middleware` monitors the status of `Things` and selects appropriate actions to control the status of `Applications`.
- **Middleware Tree**

  An IoT system where the connection between upper-level `Middleware` and lower-level `Middleware` is hierarchically structured. The upper-level `Middleware` and lower-level `Middleware` control the entire IoT system through information exchange between them.
- **Thing**

  One of the components of an IoT system that provides a `Service` that the user can use. Depending on the type of `Service` provided, it is classified into `Normal` and `Super`.
  - **Normal**
  
    A `Thing` that provides only `Normal Service`.
  - **Super**
  
    A `Thing` that provides only `Super Service`.
- **Application**

  One of the components of an IoT system that combines the `Services` provided by a `Thing` to create a service routine. Depending on the type of service provided, it is classified into `Normal` and `Super`.
  - **Normal**  
  
    An `Application` created by combining only `Normal Service`.
  - **Super**
  
    An `Application` created by combining only `Super Service`.
- **Service**
  
  One of the components of an IoT system that provides the user with the required functionality and is dependent on the `Thing`. The user can register an `Application` that uses the `Service` with the `Middleware` to use the `Service`. Depending on the type of service provided, it is classified into `Normal` and `Super`.
  - **Normal**
  
    A general `Service` that is responsible for one function.
  - **Super**
  
    A `Service` designed to implement new functionality by combining multiple `Normal Services`. When registered with a higher-level `Middleware` in the `Middleware` hierarchy, it provides functionality that can be used overall by users who connect to lower-level `Middleware`.

## Config Files

This section explains the format of the configuration files used by the IoT simulator, including the **Device Pool file**, **Simulation Environment file**, **Manual Middleware Tree file**, **Scheduling Algorithm file**. Each file is described using the following format for each element:

- **Option name**: `data type`
  
  Description of the option

The `data type` used in the configuration files are as follows:

- `str`: string
- `int`: integer
- `float`: float
- `list`: list

Each `data type` is enclosed in curly braces `{}` to indicate that it is a `data type`. Here are some examples:

- `{str}`          -> `test_string`
- `{int}`          -> `123`
- `[{int}, {int}]` -> `[3, 4]`
- `{list}`         -> `[device1, device2, ...]`

### Device Pool file

This section describes the format of the **Device Pool file**. The **Device Pool file** specifies information about the devices that can be used when specifying the `device` option in the **Simulation Environment file**. By default, it should include information about `localhost`. If there is no information about `localhost` when performing a simulation, the simulator automatically generates it. The path to the **Device Pool file** can be specified in the **Simulation Environment file** using the `device_pool_path` option. If this option is not specified, the default path is set to `device_pool.yml`. The **Device Pool file** has the following structure:

```yaml
# Device Pool file example
middlerware_1:        # device_name
  host: 192.168.0.56
  password: PaSsW0rd
  ssh_port: 22
  mqtt_port: 1883
  user: test_user
```

- **device_name**: `{str}`

  name of the device. It is used when specifying `device` items in **Simulation Environment file**.
- **host**: `{str}`

  The device's IP address or domain name.
- **password**: `{str}`

  Password to access the device via SSH.
- **ssh_port**: `int`
  
  The port number for SSH access to the device.
- **mqtt_port**: `int`
  
  `Middleware` MQTT port number to be used when the device is used as `Middleware`.
- **user**: `{str}`
  
  The username to use when connecting to the device via SSH.

### Simulation Environment file

This section provides an explanation of the format for the **Simulation Environment file**. The **Simulation Environment file** must be a `yaml` file starting with the string `config`, for example, `config_simple_home.yml`. It has the following structure:

- **device_pool_path**: `{str}`

   A file that specifies information about devices that will be used to designate device pools within the **Simulation Environment file**. If not specified, `device_pool.yml` is set as default.

- **simulation**

  A section that specifies settings for the simulation.
  - **name**: `{str}`

    name of the simulation. Defaults to base_name in **Simulation Environment file** if not specified.
  - **running_time**: `{float}`

    running time of the simulation. Defaults to 120 seconds if not specified.

  - **event_timeout** *(optional)*: `{float}`

    The timeout time for events that take place to perform the simulation. Defaults to 30 seconds if not specified.

- **middleware**

  A section that specifies settings for `Middleware` to be used in the simulation. One of the `random` and `manual` options must be specified.
  - **random** *(optional)*

    A section specifying options used when randomly generating `Middleware` hierarchies. If a `manual` option is specified, that option is ignored.
    - **height**: `[{int}, {int}]`

      The height of the `Middlware` layer to create. The two numbers in `[]` mean the minimum and maximum values.
    - **width**: `[{int}, {int}]`

      The number of the child `Middlware` per `Middlware` to create. The two numbers in `[]` mean the minimum and maximum values.
    - **normal**, **super**

      **normal** and **super** must both be specified. In the case of `normal`, it means the setting for `Normal Thing` and `Normal Application`, and in the case of `super`, it means the setting for `Super Thing` and `Super Application`.
      - **thing_per_middleware**: `[{int}, {int}]`

        The number of `Thing` per `Middleware`.
      - **application_per_middleware**: `[{int}, {int}]`

        The number of `Application` per `Middleware`.
  - **manual**

    File path where the user-defined `Middleware` layer environment is specified. More information can be found [here](#manual-middleware-tree-file). If the `random` option is specified, it is ignored.
    - **remote_middleware_path** *(optional)*: `{str}`

      The path of `Middleware` on the remote device. If not specified, it defaults to `~/middleware`.
    - **remote_middleware_config_path** *(optional)*: `{str}`

      The path of the `Middleware` configuration file to be saved on the remote device. If not specified, `/mnt/ramdisk/middleware_config` is set as default.
    - **device** *(optional)*: `list[string]`

      A list of devices to be used as `Middleware` devices. It must be specified as a device specified in the device list read from the `device_pool_path` path. If not specified, the device list except for `localhost` among the list of devices specified in `device_pool_path` is set as default.

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
  - **remote_thing_folder_path** *(optional)*: `{str}`

    The path of the `Thing` file to be saved on the remote device. If not specified, it defaults to `/mnt/ramdisk/thing`.
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

### Manual Middleware Tree file

Users can configure a custom `Middleware` layer structure to perform simulations by specifying a **Manual Middleware Tree file** and providing its path in the `manual` option of the **Simulation Environment file**. The **Manual Middleware Tree file** should be in `yaml` format and have the following structure.

```yaml
# Manual Middleware Tree file example
- name: middleware
  device: [localhost]
  thing_num: [0, 0]
  scenario_num: [0, 0]
  super_thing_num: [1, 1]
  super_scenario_num: [2, 2]
  child:
    - name: middleware
      device: [localhost]
      thing_num: [10, 10]
      scenario_num: [10, 10]
      super_thing_num: [0, 0]
      super_scenario_num: [2, 2]
      child: null
    - name: middleware
      device: [localhost]
      thing_num: [10, 10]
      scenario_num: [10, 10]
      super_thing_num: [0, 0]
      super_scenario_num: [2, 2]
      child: null
```

- **name**: `{str}`

   Name of `Middlware`
- **device**: `list[string]`

  The list of devices to be used in the simulation must be specified according to the devices listed in the `device_pool_path`. If not specified, the default device list will exclude `localhost` from the device list specified in `device_pool_path`.
- **thing_num**: `[{int}, {int}]`

  The number of things per `Middlware`. The two numbers in `[]` mean the minimum and maximum values.
- **scenario_num**: `[{int}, {int}]`

  Number of Scenarios per `Middlware`. The two numbers in `[]` mean the minimum and maximum values.
- **super_thing_num**: `[{int}, {int}]`

  The number of Super Thing per `Middlware`. The two numbers in `[]` mean the minimum and maximum values.
- **super_scenario_num**: `[{int}, {int}]`

  The number of Super Scenarios per `Middlware`. The two numbers in `[]` mean the minimum and maximum values.
- **child**: `{list}`

  A list of sub `Middlware`. Specify `null` to not create a child `Middlware`.

### Scheduling Algorithm file

Refer to [`scheduling_algorithm`](scheduling_algorithm/README.md) directory.

## Troubleshooting

### SSH daemon is not running on WSL2

- If you are running a simulation with local settings on WSL2 and unable to establish an SSH connection using localhost, you can resolve this issue by generating a new key with the following command and restarting the service.

  ```bash
  sudo ssh-keygen -A
  ```
