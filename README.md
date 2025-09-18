# Benchmark for Syntax Error Repair in DCS Models
The benchmark is designed to evaluate automated syntax error repair methods for Discrete Controller Synthesis (DCS) models written in FSP (Finite State Process) and FLTL (Fluent Linear Temporal Logic).

## Dataset Overview

### Base Models
Four widely-used MTSA models were selected as the foundation.

- AT: Air Traffic (aircraft landing coordination)

- BW: Bidding Workflow (project evaluation process)

- CM: Cat and Mouse (strategic movement with avoidance)

- AM: Access Management (privacy-aware bus streaming system)

### Instances:
Each base model has two parameterized instances (8 in total), ensuring diversity in scale and complexity.

### Error Injection:
A total of 71 syntax errors were systematically injected.

- 32 spelling errors (typos, inconsistent identifiers, case mismatches)

- 39 grammar errors (missing symbols, misused operators, malformed constructs)


### Error Characteristics:

- Errors reflect realistic mistakes identified in expert interviews and student workshops.

- Each model instance contains at least one error in major sections (process definitions, requirements, controllers).


## How to use
1. Clone the repository.
```bash
git clone https://github.com/Uuusay1432/DCSModelRepair.git
cd DCSModelRepair/benchmark
```

2. The benchmark directory contains
- `benchmark/Source`: Error-injected benchmark instances
- `benchmark/Reference`: Original validated MTSA models
- `input/input_model.txt`: Write the model to be verified into this file
- `prompt`: JSON-based prompt templates used in evaluation

3. Use the MTSA([MTSA official site](https://mtsa.dc.uba.ar/)) to validate model compilation.