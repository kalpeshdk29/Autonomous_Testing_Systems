# Free Form Testing Agent --- Roadmap to MVP

## 1. Purpose of This Document

This document defines the current position of the **Free Form Testing
Agent** project and the remaining roadmap to reach the first practical
MVP.

The MVP goal is:

> Give the framework a supported Windows desktop application and let it
> autonomously explore the application, build a persistent context
> graph, detect basic failures, recover from interruption, preserve
> evidence, and produce a useful exploration and testing report.

This document focuses only on the path from the current implementation
to that MVP.

------------------------------------------------------------------------

# 2. Current Project Position

The project has moved beyond a simple UI automation prototype.

The current framework already contains the core architecture required
for autonomous exploration:

``` text
Launch Application
        ↓
Observe UI
        ↓
Capture ApplicationState
        ↓
Discover Available Actions
        ↓
Create StateGraph
        ↓
Execute Actions
        ↓
Detect New / Existing States
        ↓
Create Transitions
        ↓
Track ExplorationMemory
        ↓
Calculate Coverage
        ↓
Select Next State
        ↓
Replay Path to State
        ↓
Select Next Action
        ↓
Execute Exploration Step
        ↓
Repeat Autonomously
        ↓
Checkpoint After Every Step
        ↓
Stop / Restart / Load
        ↓
Continue From Persisted Knowledge
```

Most importantly, this architecture has been verified against the real
Windows Calculator application.

------------------------------------------------------------------------

# 3. Current Completion Estimate

The current estimated progress is:

  Goal                                        Estimated Completion
  ----------------------------------------- ----------------------
  Core autonomous exploration MVP                          70--75%
  Useful testing-framework MVP                             50--60%
  General framework for many applications                  30--40%

These percentages represent architectural capability rather than code
volume.

The deterministic exploration core is already advanced. The largest
remaining gap is transforming the autonomous crawler into a reliable
testing system.

------------------------------------------------------------------------

# 4. Capabilities Already Completed

## 4.1 Application State Capture

The framework can observe an application and create structured
`ApplicationState` objects.

A state can contain information such as:

-   state identity
-   state hash
-   window information
-   control information
-   current values
-   available actions
-   metadata
-   screenshot references

The `ApplicationState` represents the observed application.

------------------------------------------------------------------------

## 4.2 State Graph

The framework maintains a graph of discovered application states.

``` text
ApplicationState
        +
Graph Metadata
        ↓
StateNode
```

The graph supports:

-   unique states
-   state deduplication
-   transitions
-   state depth
-   visit counts
-   neighbors
-   path finding
-   transition-path finding
-   shorter-depth updates

The graph represents the known application context.

Example:

``` text
State A
    |
    | CLICK(button)
    ↓
State B
    |
    | CLICK(next)
    ↓
State C
```

------------------------------------------------------------------------

## 4.3 Exploration Memory

The framework maintains exploration history separately from the graph.

It tracks information such as:

-   executed actions
-   failed actions
-   blocked actions
-   historical exploration decisions

This prevents the agent from repeatedly selecting already explored
actions.

------------------------------------------------------------------------

## 4.4 Breadth-First Exploration

The original exploration phase can autonomously:

-   capture the root state
-   select actions
-   execute actions
-   discover states
-   create transitions
-   respect exploration limits
-   stop deterministically

Supported limits include:

-   maximum states
-   maximum actions
-   maximum transitions
-   maximum depth
-   maximum duration
-   maximum failures

------------------------------------------------------------------------

## 4.5 Coverage Engine

The framework can calculate exploration coverage.

It distinguishes:

-   total known actions
-   explored actions
-   unexplored actions
-   eligible actions
-   explored eligible actions
-   unexplored eligible actions
-   eligible coverage percentage

An important lesson discovered during real exploration is:

> Exploration progress does not always mean the current coverage
> percentage increases.

Example:

``` text
Before Resume

Known Eligible Actions:       48
Explored Eligible Actions:    12
Coverage:                     25%

After Resume

Known Eligible Actions:       60
Explored Eligible Actions:    15
Coverage:                     25%
```

The framework made progress but also discovered new states and therefore
new work.

For this reason, progress must consider:

-   growth in explored actions
-   graph growth
-   transition growth
-   newly discovered work
-   current known-space coverage

------------------------------------------------------------------------

## 4.6 Exploration Target Selection

The framework can identify which previously discovered states still
contain unexplored eligible work.

The current deterministic strategy can prioritize shallow states first.

``` text
Coverage Engine
        ↓
Valid Exploration Candidates
        ↓
Target Ranking
        ↓
Selected Exploration Target
```

------------------------------------------------------------------------

## 4.7 Action Selection

For a selected state, the framework can:

-   filter invalid actions
-   exclude executed actions
-   exclude blocked actions
-   rank valid actions
-   select the next action deterministically

``` text
Selected State
        ↓
Available Actions
        ↓
Eligibility Filtering
        ↓
Memory Filtering
        ↓
Action Ranking
        ↓
Selected Action
```

------------------------------------------------------------------------

## 4.8 Replay Engine

The framework can find a path from the root state to a previously
discovered target state and replay that path.

This allows the agent to return to old graph locations and continue
unexplored work.

``` text
Root State
        ↓
Find Path
        ↓
Replay Transitions
        ↓
Reach Target State
        ↓
Continue Exploration
```

------------------------------------------------------------------------

## 4.9 Single Exploration Step Execution

The `ExplorationStepExecutor` combines the existing components into one
deterministic continuation step.

``` text
Root State
        ↓
Replay to Selected Source State
        ↓
Select Next Eligible Action
        ↓
Execute Action
        ↓
Capture Result State
        ↓
Update Graph
        ↓
Update Memory
```

It supports:

-   replay failure handling
-   missing source-state handling
-   no-action handling
-   failed execution recording
-   successful graph updates
-   state deduplication

------------------------------------------------------------------------

## 4.10 Autonomous Closed Coordinator Loop

The `ExplorationCoordinator` repeatedly:

-   selects the next target state
-   executes one exploration step
-   updates statistics
-   checks limits
-   continues until a deterministic stop condition occurs

``` text
Select Target
        ↓
Execute Step
        ↓
Update Graph + Memory
        ↓
Update Statistics
        ↓
Check Limits
        ↓
Repeat
```

The coordinator supports stop conditions such as:

-   no remaining targets
-   maximum steps reached
-   maximum duration reached
-   maximum failures reached
-   checkpoint failure

------------------------------------------------------------------------

# 5. Persistence Capabilities Already Completed

## 5.1 Domain Serialization

The framework can serialize and reconstruct:

-   actions
-   application states
-   transitions
-   exploration memory

The serialization is:

-   JSON compatible
-   deterministic
-   round-trip safe

Loaded memory remains mutable.

------------------------------------------------------------------------

## 5.2 State Graph Serialization

The complete state graph can be saved and reconstructed.

The serializer preserves:

-   states
-   state data
-   depths
-   visit counts
-   transitions
-   transition actions

After loading, the graph still supports:

-   state lookup
-   hash-based deduplication
-   neighbor lookup
-   path finding
-   transition-path finding
-   new states
-   new transitions
-   shorter-depth updates

------------------------------------------------------------------------

## 5.3 Versioned Session Snapshots

A durable exploration session can contain:

``` text
Session Metadata
    +
Root State ID
    +
StateGraph
    +
ExplorationMemory
```

The snapshot includes:

-   schema version
-   session ID
-   root state ID
-   creation timestamp
-   update timestamp
-   graph
-   memory

The schema version provides a foundation for future persistence
migrations.

------------------------------------------------------------------------

## 5.4 JSON Session Repository

The framework can save and load sessions from disk.

Current storage:

``` text
storage/
└── database/
    └── sessions/
        └── <session-id>/
            └── session.json
```

The repository supports:

-   save
-   load
-   exists
-   list sessions
-   validation
-   unsafe session ID rejection
-   invalid JSON rejection
-   unsupported schema rejection

Saving is atomic through temporary-file replacement.

------------------------------------------------------------------------

## 5.5 Real Save and Load

The framework has proven that a real Calculator exploration session can
be:

``` text
Explore
    ↓
Save
    ↓
Load Fresh Objects
    ↓
Preserve Graph
    ↓
Preserve Memory
    ↓
Preserve Coverage
```

------------------------------------------------------------------------

## 5.6 True Durable Resume

The framework has also proven:

``` text
Runtime A
    ↓
Explore
    ↓
Save V1

Runtime B
    ↓
Load Fresh Graph + Memory
    ↓
Continue Autonomous Exploration
    ↓
Save V2

Runtime C
    ↓
Load Again
    ↓
Continued Knowledge Preserved
```

Verified real result:

``` text
Before Resume

States:                    12
Transitions:               12
Explored Eligible Actions: 12

After Resume

States:                    15
Transitions:               15
Explored Eligible Actions: 15
```

------------------------------------------------------------------------

## 5.7 Checkpoint Manager

The framework now has a dedicated `CheckpointManager`.

Its responsibility is:

``` text
Live Graph + Memory
        ↓
CheckpointManager
        ↓
SessionSnapshot
        ↓
Repository
        ↓
Durable Storage
```

It manages:

-   session ID
-   root state ID
-   original creation time
-   checkpoint update time
-   snapshot construction
-   persistence

It also guarantees that failed persistence does not falsely update the
successful checkpoint timestamp.

------------------------------------------------------------------------

## 5.8 Automatic Checkpointing

The coordinator now supports optional automatic checkpointing.

``` text
Select Target
        ↓
Execute Step
        ↓
Graph + Memory Updated
        ↓
Update Statistics
        ↓
Automatic Checkpoint
        ↓
Continue
```

Checkpointing occurs after:

-   successful exploration steps
-   failed exploration attempts

If checkpointing fails, the coordinator stops deterministically.

This prevents the in-memory runtime from continuing too far beyond the
last recoverable durable state.

------------------------------------------------------------------------

## 5.9 Real Automatic Checkpoint Verification

The complete production chain has been verified:

``` text
Initial Manual Save:       1
Continuation Steps:        3
Automatic Checkpoints:     3
Total Repository Saves:    4
Disk Matches Live Runtime: True
```

No manual final save was performed.

The final session was loaded directly from disk and matched:

-   live graph
-   live memory
-   live coverage
-   root state
-   timestamps

------------------------------------------------------------------------

# 6. Current Architecture Summary

The system currently looks like this:

``` text
                    Application
                         ↓
                    UI Observer
                         ↓
                 ApplicationState
                         ↓
                     StateGraph
                         +
                ExplorationMemory
                         ↓
                   CoverageEngine
                         ↓
             ExplorationTargetSelector
                         ↓
                  ActionSelector
                         ↓
                    ReplayEngine
                         ↓
             ExplorationStepExecutor
                         ↓
             ExplorationCoordinator
                         ↓
                 CheckpointManager
                         ↓
               Session Repository
                         ↓
                   Durable Disk
```

This is already a strong autonomous exploration foundation.

------------------------------------------------------------------------

# 7. Definition of the First Real MVP

The first practical MVP will be achieved when the framework can:

> Accept a supported Windows desktop application, autonomously explore
> it, build a persistent application context graph, detect basic
> deterministic failures, recover from interrupted execution, preserve
> evidence, and produce a useful exploration and testing report.

The MVP does not need to understand every application perfectly.

It does need to prove that the architecture works beyond Calculator.

------------------------------------------------------------------------

# 8. Remaining Milestone 1 --- Session Lifecycle and Interrupted Recovery

## Goal

Detect that a previous exploration process stopped unexpectedly and
resume from its latest durable checkpoint.

## Lifecycle Model

``` text
CREATED
    ↓
RUNNING
    ↓
    ├── COMPLETED
    ├── FAILED
    └── process dies unexpectedly
            ↓
       persisted status remains RUNNING
            ↓
       next process detects unfinished run
            ↓
       resume from latest checkpoint
```

## Important Design Principle

A killed process may never execute shutdown code.

Therefore, the system should not depend on explicitly writing:

``` text
INTERRUPTED
```

during a crash.

Instead:

``` text
Session starts
    ↓
Persist RUNNING

Normal completion
    ↓
Persist COMPLETED

Next startup finds RUNNING
    ↓
Previous run was interrupted
    ↓
Session is resumable
```

## Required Work

-   create session lifecycle status
-   persist status in snapshots
-   update serializer tests
-   update checkpoint lifecycle behavior
-   detect stale `RUNNING` sessions
-   prove real Calculator recovery

## Estimated Size

Small milestone.

Approximately 1--2 focused implementation stages.

------------------------------------------------------------------------

# 9. Remaining Milestone 2 --- Deterministic Failure Detection

This is the most important remaining milestone for transforming the
crawler into a tester.

## Current Limitation

The framework mainly understands:

``` text
Execution succeeded
or
Execution failed
```

A real testing framework needs richer deterministic failure categories.

## Required Failure Types

The MVP should detect at least:

-   application process disappeared
-   application crashed
-   expected window disappeared
-   application stopped responding
-   action execution timed out
-   replay produced an unexpected state
-   unexpected error dialog appeared
-   state capture failed
-   action execution failed
-   application could not be restored for replay

## Target Architecture

``` text
Action Execution
        ↓
Runtime Validation
        ↓
    ┌───────────────┐
    │               │
 Success         Failure
                    ↓
             Failure Detector
                    ↓
              Failure Record
```

Example:

``` text
State A
    |
    | CLICK(saveButton)
    ↓
FAILURE

Type:
    UNEXPECTED_ERROR_DIALOG

Evidence:
    screenshot

Reproduction:
    root → state A → saveButton
```

## Required Components

Likely components include:

-   failure type model
-   failure record model
-   process health detector
-   window health detector
-   timeout detection
-   unexpected dialog detector
-   replay mismatch detector
-   failure persistence

## Why This Is an MVP Gate

Without deterministic failure detection, the system is mainly an
autonomous crawler.

With deterministic failure detection, it begins to function as an
autonomous tester.

------------------------------------------------------------------------

# 10. Remaining Milestone 3 --- Screenshot and State Artifacts

## Goal

Preserve durable human-readable evidence for discovered states and
failures.

## Target Storage Structure

``` text
storage/
├── database/
│   └── sessions/
│       └── <session-id>/
│           └── session.json
│
├── screenshots/
│   └── <session-id>/
│       ├── state-A.png
│       ├── state-B.png
│       └── failure-001.png
│
└── states/
    └── <session-id>/
        ├── state-A.json
        └── state-B.json
```

## Required Behavior

Every important graph state should be able to reference:

-   state JSON artifact
-   screenshot artifact

Every important failure should be able to reference:

-   failure screenshot
-   source state
-   selected action
-   replay path
-   failure reason

## Why This Matters

A test result without evidence is difficult to debug.

Artifacts make the autonomous exploration output inspectable and useful
to developers and testers.

------------------------------------------------------------------------

# 11. Remaining Milestone 4 --- Exploration and Testing Report

## Goal

Produce a clear summary of what the framework explored and what it
found.

## Example MVP Report

``` text
APPLICATION EXPLORATION REPORT

Application:
    Sample CRM

Unique States:
    143

Transitions:
    418

Actions Attempted:
    391

Failures:
    7

Known Eligible Coverage:
    82%

Critical Failures:
    2

Recoverable Failures:
    5

Remaining Known Work:
    31 actions

Artifacts:
    Graph
    Screenshots
    State snapshots
    Failure reproductions
    Session snapshot
```

## Report Sections

The MVP report should include:

-   application information
-   session information
-   stop reason
-   duration
-   states discovered
-   transitions created
-   actions attempted
-   failures
-   known eligible coverage
-   remaining work
-   artifact locations
-   failure reproduction paths

## Important Coverage Wording

The report should avoid implying that coverage is absolute application
coverage.

It should describe:

``` text
Coverage of currently known eligible actions
```

because the framework may discover new states and new actions later.

------------------------------------------------------------------------

# 12. Remaining Milestone 5 --- Generalize Beyond Calculator

This is the decisive MVP validation stage.

## Why Calculator Is Not Enough

Calculator is useful for validating:

-   state discovery
-   button actions
-   graph creation
-   replay
-   deterministic selection
-   persistence
-   resume

But Calculator does not sufficiently test:

-   text input
-   forms
-   dropdowns
-   checkboxes
-   menus
-   validation
-   modal dialogs
-   multiple windows
-   tables
-   create/edit/delete workflows
-   destructive actions

## Recommended Benchmark Progression

``` text
Calculator
    ↓
Controlled Form Application
    ↓
Multi-Screen CRUD Application
    ↓
Menu and Dialog Application
    ↓
Medium-Complexity Real Desktop Application
```

## First Proper Benchmark Application

The next benchmark should contain:

-   text fields
-   buttons
-   checkboxes
-   dropdowns
-   validation rules
-   multiple screens
-   modal dialogs
-   create operations
-   edit operations
-   delete operations

## Expected Problems This Will Reveal

Testing a more complex application will likely expose issues in:

-   state identity
-   dynamic state hashing
-   action generation
-   text input generation
-   replay stability
-   graph deduplication
-   modal handling
-   window switching
-   destructive-action policy
-   failure detection

Fixing these issues is part of the MVP process.

------------------------------------------------------------------------

# 13. Remaining Milestone 6 --- Generalization Fixes

After the complex benchmark test, the framework will need a
stabilization phase.

The exact fixes cannot be fully predicted before running the benchmark.

Likely areas include:

-   stronger state normalization
-   dynamic-content filtering
-   better control identity
-   text input support
-   action parameter generation
-   safer destructive-action handling
-   multi-window replay
-   modal recovery
-   more robust waiting and synchronization
-   better graph deduplication

The MVP should be declared only after the framework successfully
explores more than one application type.

------------------------------------------------------------------------

# 14. Roadmap From Current Position to MVP

``` text
CURRENT POSITION
    │
    ▼
1. Session Lifecycle
   + Interrupted Recovery
    │
    ▼
2. Deterministic Failure Detection
    │
    ▼
3. Screenshot + State Artifacts
    │
    ▼
4. Exploration / Testing Report
    │
    ▼
5. Complex Form Application Benchmark
    │
    ▼
6. Generalization Fixes
    │
    ▼
══════════════════════════════════════
             FIRST REAL MVP
══════════════════════════════════════
```

Estimated remaining work:

> Approximately 5--7 substantial implementation milestones.

The project is not dozens of architectural stages away from an MVP, but
it is also not one or two small changes away.

------------------------------------------------------------------------

# 15. Recommended Priority Order

The shortest path to the MVP is:

## Priority 1 --- Finish Interrupted Recovery

Complete the persistence lifecycle already in progress.

## Priority 2 --- Implement Failure Detection

This creates the transition from crawler to tester.

## Priority 3 --- Persist Evidence

Add screenshots and state artifacts.

## Priority 4 --- Produce Reports

Turn internal exploration data into useful output.

## Priority 5 --- Test a Complex Application

Prove that the architecture generalizes beyond Calculator.

## Priority 6 --- Stabilize

Fix the real issues revealed by the broader benchmark.

------------------------------------------------------------------------

# 16. When AI Should Be Integrated

AI should not replace the deterministic core.

The deterministic system should remain responsible for:

-   application observation
-   state identity
-   graph storage
-   action execution
-   replay
-   persistence
-   failure facts
-   evidence
-   coverage calculation

AI should be added as an optional strategy layer.

## Target Architecture

``` text
                Exploration Engine
                Deterministic Core
                       │
         ┌─────────────┴─────────────┐
         │                           │
Deterministic Strategy          AI Strategy
         │                           │
         └─────────────┬─────────────┘
                       ↓
                 Action Decision
```

------------------------------------------------------------------------

# 17. First Useful AI Integration

The first useful AI feature should be semantic action prioritization.

## Current Deterministic Selection

``` text
Available Actions:

CLICK(cancelButton)
CLICK(deleteButton)
CLICK(saveButton)
CLICK(nextButton)

Strategy:
    stable deterministic ranking
```

## Future AI-Assisted Selection

``` text
Context:
    User is editing a customer record

Semantic Interpretation:

saveButton
    likely completes meaningful work

nextButton
    may reveal a new workflow

cancelButton
    may return to a known state

deleteButton
    is destructive

Suggested Ranking:

1. saveButton
2. nextButton
3. cancelButton
4. deleteButton
```

The deterministic engine should still validate and execute the final
action.

------------------------------------------------------------------------

# 18. Later AI Capabilities

After the MVP foundation is reliable, AI can help with:

## Semantic State Understanding

Understand that two structurally different UI states represent the same
logical workflow stage.

## Goal Generation

Generate exploration goals such as:

-   create a customer
-   edit a record
-   trigger validation
-   search for data
-   navigate settings

## Text Input Generation

Generate meaningful values for:

-   names
-   emails
-   dates
-   numbers
-   search queries
-   domain-specific fields

## Workflow Discovery

Identify larger application flows instead of treating every action
independently.

## Risk-Based Exploration

Prioritize:

-   save operations
-   destructive operations
-   security-sensitive flows
-   complex workflows
-   error-prone areas

## Test Intent Generation

Generate higher-level testing goals from application context.

## Failure Interpretation

Help explain why a deterministic failure may be important.

------------------------------------------------------------------------

# 19. Long-Term Vision Beyond MVP

The long-term architecture is:

``` text
Application
    ↓
UI Observation
    ↓
Deterministic State Graph
    ↓
Persistent Application Context
    ↓
┌─────────────────────────────────────┐
│                                     │
│ Deterministic Exploration           │
│ AI-Guided Exploration               │
│ Goal-Based Exploration              │
│ Risk-Based Exploration              │
│ Regression Exploration              │
│                                     │
└─────────────────────────────────────┘
    ↓
Failure Detection
    ↓
Automatic Reproduction
    ↓
Evidence Collection
    ↓
Test Report
```

The full vision is larger than the first MVP.

The MVP should prove the foundation before advanced AI behavior is
introduced.

------------------------------------------------------------------------

# 20. Final Assessment

The hardest architectural foundation is already working.

The project has proven that these systems can cooperate:

-   state capture
-   graph construction
-   state deduplication
-   exploration memory
-   coverage calculation
-   target selection
-   action selection
-   replay
-   autonomous continuation
-   persistence
-   fresh-runtime resume
-   automatic checkpointing

The remaining transformation is:

``` text
Autonomous Explorer
        ↓
Reliable Application Tester
```

That transformation depends primarily on:

1.  interrupted-run recovery
2.  deterministic failure detection
3.  durable evidence artifacts
4.  useful reporting
5.  validation against more complex applications

Once those milestones are complete and the framework successfully
explores a non-trivial form/CRUD application, the project will have
reached its first practical MVP.
