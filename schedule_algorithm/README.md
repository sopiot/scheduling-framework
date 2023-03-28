# Scheduling Algorithm

## Scheduling Policies

In this IoT Platform, the `Scheduler` responds according to the scheduling policies when a new `Application` or `Super Service`'s service scheduling request comes in.
This document outlines the scheduling policies which determine the scheduling algorithm. The system handles scheduling requests, device status changes, and execution requests, and responds to events triggered by users, `Super Things`, schedulers, and other `Middleware`.

### Scheduling Request

The `Scheduler` updates the mapping table when a new `Application` or `Super Service`'s Sub Service scheduling request comes in, and responds according to the following policy:

| Scheduling Policy | Triggered By | Example |
| ------ | ------ | ------ |
OnScheduleApplication | User | Map services in the `Application`
OnCancelApplication | User, `Super Thing` | Cancel and leave as is or update
OnUpdateApplication | User, `Scheduler` | Re-schedule the `Application`
OnGlobalUpdate | `Scheduler` | Re-schedule all `Applications`
OnSuperScheduleRequest | `Super Thing` | Schedule the service request
OnSuperCancelRequest | `Super Thing` | Cancel and leave as is or update

### Device Status Change

Changes in the state of devices can affect the `Scheduler`, and the policy includes events such as adding or removing a Thing, connecting or disconnecting a `Middleware`, and remapping to include new possibilities or maintaining existing mappings:

| Scheduling Policy | Triggered By | Example |
| ------ | ------ | ------ |
OnThingRegister| `Thing`| Leave as is or update
OnThingUnregister| `Thing`| Re-schedule invalidated `Applications`
OnMiddlewareRegister| Other `Middleware`| Leave as is or update
OnMiddlewareUnregister| Other `Middleware`| Re-schedule invalidated `Applications`

### Execution Request

When executing requests, the `Scheduler` requests `Services` from the device based on the needs of the `Application` and `Super Service` in the RunQueue. The following policy applies:

| Scheduling Policy| Triggered By| Example |
| ------ | ------ | ------ |
OnServiceRequest| `Scheduler` | Ready: execute, Busy: wait
OnSuperServiceRequest| `Super Thing` | Ready: execute, Busy: wait

### Execution Result

The system also handles execution results, and responds according to the following policy:

| Scheduling Policy | Triggered By | Example |
| ------ | ------ | ------ |
OnServiceResult | `Thing` | Success: proceed, Error: update
OnSuperServiceResult | `Thing` | Success: reply, Error: update
OnServiceTimeout | `Scheduler` | Retry or update

## How to customize

1. Customize 'my_schedule_policy.cc' file.
2. Build 'libschedule-policy.so' with the policy source code.
3. Run the provided middleware with the shared library ('libschedule-policy.so')
  - We provide middleware executable for Ubuntu and Raspberry Pi now.

### Note

* Currently this customization is for developer who are familiar with C language.
* For everyone, a simple GUI for algorithm source code generation is being prepared now.

### Brief explanation and some tips

Changes in the state of devices can affect the `Scheduler`, and the policies includes events such as adding or removing a `Thing`, connecting or disconnecting a `Middleware`, and remapping to include new possibilities or maintaining existing mappings.

When executing requests, the `Scheduler` requests `Services` from the device based on the needs of the `Application` and `Super Service` in the RunQueue. The OnExecuteRequest event is fired when a running local `Application` needs to request a local or `Super Service`, and checks the current state to see if the device is available before making the request.

If the `Service` is available, the request can be made one by one or a RunQueue can be created with the target `Service` in the same order as the requests were received.

Overall, the `Scheduler` plays a crucial role in managing the allocation and utilization of resources in a system. It uses various events and algorithms to map `Services` to devices and respond to changes in device state, ensuring optimal performance and efficient resource allocation.

- **OnScheduleScenario**: When an `Application` is added, it maps the services specified in the `Application` to the device using a mapping algorithm that determines the underlying service-to-device mapping efficiency.

- **OnCancelScenario**: When the mapping is disabled, such as when the `Application` is deleted, stopped, or finished, the `Service` mapping is canceled, creating a slack on the previously mapped device.

- **OnUpdateScenario**: When an `Application` is remapped, the same algorithm as **OnScheduleScenario** can be used, or a different mapping algorithm can be applied.

- **OnGlobalUpdate**: When a decision is made to globally update all mappings scheduled to date, a mapping algorithm with a global remapping trigger can be applied.

- **OnSuperScheduleRequest**: When a `Service` scheduling request comes from the `Super Service`, it communicates with the `Super Service` in two phases: Check and Confirm. In the Check phase, the mapping algorithm answers whether additional scheduling is currently possible, and when the `Super Service` sends a Confirm request, it actually adds the mapping.

- **OnSuperCancelRequest**: When a service scheduling cancellation request comes from the `Super Service`, local `Applications` can immediately create new mappings for the `Services` that were mapped or simply keep the existing mappings.
