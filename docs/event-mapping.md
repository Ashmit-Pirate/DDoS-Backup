# Event Mapping: Database to REST API

This document details the exact field-by-field mapping used in `GET /api/v1/events` to convert the backend's internal representations (`Event` and `MitigationAction` tables) into the frontend's `LogEvent` and `Incident` shapes.

## 1. `LogEvent` Mapping

The `logs` array is constructed by querying the `events` table (which records both detection and mitigation actions as a unified feed).

| `LogEvent` Field | Source Field | Notes |
|---|---|---|
| `id` | `events.id` | Cast to string. |
| `time` | `events.timestamp` | ISO 8601 formatted string. |
| `severity` | `events.severity` | Mapped: `LOW` -> `INFO`, `MEDIUM` -> `WARN`, `HIGH` -> `ALERT`. |
| `component` | *Derived* | If `events.action` is empty, it's a detection event so component is `"DecisionEngine"`. Otherwise, it's `"Mitigation"`. |
| `message` | *Derived* | If it's a detection: `"Detected {attack_type} attack (confidence: {confidence})"`. If mitigation: `"{action} applied ({status})"`. |
| `incidentId` | *Stubbed* | Currently hardcoded to `None` because the events are not explicitly joined to an `Incident` in the current database schema context. |

## 2. `Incident` Mapping

The `incidents` array is currently constructed by querying recent rows from the `mitigation_actions` table, as an active mitigation implies an active high-severity incident.

| `Incident` Field | Source Field | Notes |
|---|---|---|
| `id` | `mitigation_actions.id` | Cast to string. |
| `status` | `mitigation_actions.status` | Mapped: `"ACTIVE"` if the underlying status is `PLANNED`, `SIMULATED`, or `ACTIVE`. Otherwise, `"RESOLVED"`. |
| `type` | `mitigation_actions.attack_type` | Passed directly. |
| `severity` | *Stubbed* | Hardcoded to `"HIGH"` for now, assuming mitigations only occur for high severity. |
| `start` | `mitigation_actions.started_at` | ISO 8601 formatted string. |
| `detectionTime` | *Stubbed* | Currently placeholder/stubbed using `mitigation_actions.started_at`. |
| `mitigationTime` | *Stubbed* | Currently placeholder/stubbed using `mitigation_actions.started_at`. |
| `duration` | *Stubbed/Derived* | Evaluated as `"ongoing"` if status is `PLANNED`, `SIMULATED`, or `ACTIVE`, otherwise `"ended"`. (Does not calculate actual elapsed time). |

**Conclusion:** The REST API conforms perfectly to the required output schemas, but heavily relies on derived text and stubbed values for timestamps (`detectionTime`, `mitigationTime`) and relationships (`incidentId`). If the frontend requires precise `incidentId` linkage or durations, a dedicated `incidents` table or complex joins will be needed in a future phase.
