```python
import numpy as np
import matplotlib.pyplot as plt
from ipywidgets import Button, IntSlider, interactive_output, HBox, Output, Box
from amplify import (
    Solver,
    decode_solution,
    gen_symbols,
    BinaryPoly,
    sum_poly,
    BinaryQuadraticModel,
)
from amplify.client import FixstarsClient
from amplify.constraint import equal_to, penalty

client = FixstarsClient()

%matplotlib inline
```

# Graph coloring problem

The graph coloring problem is a problem that aims to paint the entire regions by avoiding adjacent regions from having the same color.

The followings are some of the application examples of this problem.

* Scheduling problems, such as assigning meeting rooms and assigning work tasks
* Allocation problems of shared resources such as radio frequency bands

The following demo uses the QUBO formulation to run Amplify Annealing Engine on the problem of painting the prefectures of Japan in different colors.   
Click the [Run] button to display the output solution.


```python
import japanmap as jm


def coloring_initialize():
    plt.rcParams["figure.figsize"] = 7.6, 7.6
    plt.imshow(jm.picture())
    plt.show()


def coloring_solve(*args):
    colors = ["red", "green", "blue", "yellow"]
    num_colors = len(colors)
    num_region = len(jm.pref_names) - 1  # Obtain the number of prefectures

    q = gen_symbols(BinaryPoly, num_region, num_colors)

    # Constraints on each region
    reg_constraints = [
        equal_to(sum_poly([q[i][c] for c in range(num_colors)]), 1)
        for i in range(num_region)
    ]

    # Constraints between adjacent regions
    adj_constraints = [
        # Note that the prefecture code and the array index are off by one.
        penalty(q[i][c] * q[j - 1][c])
        for i in range(num_region)
        for j in jm.adjacent(i + 1)  # j: Adjacent prefecture code
        if i + 1 < j
        for c in range(num_colors)
    ]

    constraints = sum(reg_constraints) + sum(adj_constraints)

    solver = Solver(client)
    solver.client.parameters.timeout = 1000

    model = BinaryQuadraticModel(constraints)

    result = solver.solve(model)
    i = 0
    while len(result) == 0:
        if i > 5:
            raise RuntimeError()
        result = solver.solve(model)
        i += 1

    values = result[0].values
    q_values = decode_solution(q, values, 1)
    color_indices = np.where(np.array(q_values) == 1)[1]
    color_map = {
        jm.pref_names[i + 1]: colors[color_indices[i]]
        for i in range(len(color_indices))
    }

    plt.rcParams["figure.figsize"] = 7.6, 7.6
    plt.imshow(jm.picture(color_map))
    plt.show()
```


```python
coloring_run_btn = Button(
    description="Run", button_style="", tooltip="Run", icon="check"
)
coloring_problem_out = Output()
coloring_result_out = Output()


def show_coloring_problem():
    with coloring_problem_out:
        coloring_initialize()


def show_coloring_result(btn):
    with coloring_result_out:
        coloring_result_out.clear_output()
        coloring_solve()


coloring_run_btn.on_click(show_coloring_result)
display(HBox([coloring_run_btn]), HBox([coloring_problem_out, coloring_result_out]))
show_coloring_problem()
```
