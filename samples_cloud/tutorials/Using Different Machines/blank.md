# Using Different Machines

This tutorial explains sample client setup code for using some of the machines supported by Fixstars Amplify. For a more complete and detailed explanation, please refer to [Client Class Overviews](https://amplify.fixstars.com/en/docs/client.html).


```python
from amplify import *
from amplify.constraint import *
```

## Client Settings

### Amplify Annealing Engine


```python
from amplify.client import FixstarsClient

client = FixstarsClient()
client.parameters.timeout = 1000  # Timeout is 1 second
# client.token = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # If you use Amplify in a local environment, enter the Amplify API token.
```

### D-Wave 2000Q / Advantage


```python
from amplify.client.ocean import DWaveSamplerClient

client_dwave = DWaveSamplerClient()
client_dwave.token = "Please enter your token."

# D-Wave 2000Q
client_dwave.solver = "DW_2000Q_VFYC_6"
client_dwave.parameters.num_reads = 100  # Execution count 100

# D-Wave Advantage
client_dwave.solver = "Advantage_system1.1"
client_dwave.parameters.num_reads = 100  # Execution count 100
```

### D-Wave Leap Hybrid


```python
from amplify.client.ocean import LeapHybridSamplerClient

client_leap_hybrid = LeapHybridSamplerClient()
client_leap_hybrid.token = "Please enter your token."
client_leap_hybrid.solver = "hybrid_binary_quadratic_model_version2"
client_leap_hybrid.parameters.time_limit = 3  # Timeout is 3 seconds
```

### Fujitsu DA4 solver


```python
from amplify.client import FujitsuDA4SolverClient

client_fujitsu_da4 = FujitsuDA4SolverClient()
client_fujitsu_da4.token = "Please enter your token."
client_fujitsu_da4.parameters.time_limit_sec = 3  # Timeout is 3 seconds
```

### Toshiba SBM


```python
from amplify.client import ToshibaClient

client_toshiba_sbm = ToshibaClient()
client_toshiba_sbm.url = "http://xxx.xxx.xxx.xxx"  # API URL
client_toshiba_sbm.parameters.timeout = 1  # Timeout is 1 second
```

### Hitachi CMOS Annealing Machine


```python
from amplify.client import HitachiClient

client_hitachi = HitachiClient()
client_hitachi.token = "Please enter your token."
client_hitachi.parameters.temperature_num_steps = 10
client_hitachi.parameters.temperature_step_length = 100
client_hitachi.parameters.temperature_initial = 100.0
client_hitachi.parameters.temperature_target = 0.02
```

## Formulation of an example problem


```python
# コスト関数の定式化例
gen = BinarySymbolGenerator()
q = gen.array(2)
cost_func = -2 * q[0] * q[1] + q[0] - q[1] + 1
cost_func
```


```python
# Example of constraint formulation
constraint = 2 * equal_to(q[0] + q[1], 1)
constraint
```


```python
# Building a model
model = cost_func + constraint
```

## Running a machine


```python
# Building a solver
solver = Solver(client)

# Running the machine
result = solver.solve(model)
```

## Obtaining the execution result


```python
for s in result:
    print(f"q = {decode_solution(q, s.values)}")
    print(f"energy = {s.energy}")
```
