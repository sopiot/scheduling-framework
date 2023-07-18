# MySSIX Simulator Examples

This folder contains examples using the MySSIX simulator.

The examples are divided into folders named `simple_home_*`, `simple_building_*`, `simple_campus_*`, and `paper_experiment`. The `simple` part is divided into `local` and `remote` examples. The `*_local` examples run all simulation components directly on the local machine, while the `*_remote` examples run the `Middleware` component on a remote machine and the Thing component on the local machine. The `paper_experiment` example is for reproducing the experiments in the paper and runs the simulation with the `remote` setting.

## Case 1: simple home

This simulation does not create a hierarchical structure and runs one `Middleware` at level 1. It registers one `Super Thing`, two `Super Applications`, 10 `Normal Things`, and 10 `Normal Applications` with the `Middleware` to perform the simulation. It can be run with `local`, `remote`, or `multi_env` settings. With `multi_env`, the simulation is run four times for two **Simulation Environment files** and two **Scheduling Algorithms files**, and the results of comparing the two scheduling algorithms are output.

## Case 2: simple building

This simulation runs five `Middleware`, with one `Middleware` at level 2 and four `Middleware` at level 1. Only the `Middleware` at level 1 registers 10 `Normal Things` and 10 `Normal Applications` with the `Middleware`. It registers one `Super Thing` with the top-level `Middleware` and two `Super Applications` with the top and bottom `Middleware`, respectively. It can be run with `local` or `remote` settings.

## Case 3: simple campus

This simulation runs seven `Middleware`, with one `Middleware` at level 3, two `Middleware` at level 2, and four `Middleware` at level 1. Only the `Middleware` at level 1 registers 10 `Normal Things` and 10 `Normal Applications` with the `Middleware`. It registers one `Super Thing` with the top-level `Middleware` and two `Super Applications` with the top and bottom `Middleware`, respectively. It can be run with local, remote, or `local_random` settings. With `local_random`, the simulation is run with a randomly generated hierarchical structure of 3 levels and 2 widths.

## Case 4: paper experiments

This simulation environment can reproduce the experiments performed in the paper. It runs one `Middleware` on a remote device and runs all `Normal Things` on the local machine by default, except for the `Super Thing`, which runs on the same device as the `Middleware`. Devices specified in the **Device Pool file** in the `device_pool_path` path must be specified as information on the _local network_ and at _least 11 Raspberry Pi devices are required_.
