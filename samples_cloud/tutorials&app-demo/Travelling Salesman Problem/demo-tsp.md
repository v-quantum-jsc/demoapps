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

# Travelling Salesman Problem

The Traveling Salesman Problem is a problem to find the shortest path for a salesman to travel through each city once and return to the starting point.

When considering the following problems, we encounter analogous problems to the Traveling Salesman problem. 

* Optimization of delivery routes
* Wiring of integrated circuits
* Resource allocation in production planning

In the following demo, we formulate a QUBO model for a problem with a given number of cities that are randomly placed, and we solve it by running Amplify Annealing Engine.
Click the [Run] button to display the output solution.


```python
def tsp_initialize_problem(nc: int = 32):
    def gen_random_tsp():
        # Coordinates
        locations = np.random.uniform(size=(ncity, 2))

        # Distance matrix
        all_diffs = np.expand_dims(locations, axis=1) - np.expand_dims(
            locations, axis=0
        )
        distances = np.sqrt(np.sum(all_diffs**2, axis=-1))

        return locations, distances

    def show_plot(locs: np.ndarray):
        plt.figure(figsize=(7, 7))
        plt.xlabel("x")
        plt.ylabel("y")
        plt.title("path length: ?")
        plt.scatter(*zip(*locations))
        plt.show()

    global ncity
    global locations
    global distances
    ncity = nc
    locations, distances = gen_random_tsp()
    show_plot(locations)


def tsp_solve(*args):
    solver = Solver(client)
    if ncity > 32:
        solver.client.parameters.timeout = 1500 + int((5000 - 1500) * (ncity - 32) / 32)
        k = 0.3
    else:
        solver.client.parameters.timeout = 1500
        k = 0.5
    solver.client.parameters.num_unit_steps = 5

    q = gen_symbols(BinaryPoly, ncity, ncity)
    q[0][0] = BinaryPoly(1)
    for i in range(1, ncity):
        q[0][i] = BinaryPoly(0)
        q[i][0] = BinaryPoly(0)

    # Obtain a list of minimum non-zero values for each row
    d_min = [d[np.nonzero(d)].min() for d in distances]

    # Modify the coefficients of the cost function and add a constant term
    cost = sum_poly(
        ncity,
        lambda n: sum_poly(
            ncity,
            lambda i: sum_poly(
                ncity,
                lambda j: (distances[i][j] - d_min[i] if i != j else 0)
                * q[n][i]
                * q[(n + 1) % ncity][j],
            ),
        ),
    ) + sum(d_min)

    # Subtract the minimum value of each row and then get the maximum value of all elements.
    d_max_all = max(distances.max(axis=1) - d_min)

    # Constraints on rows
    row_constraints = [
        equal_to(sum_poly([q[n][i] for i in range(ncity)]), 1) for n in range(ncity)
    ]

    # Constraints on columns
    col_constraints = [
        equal_to(sum_poly([q[n][i] for n in range(ncity)]), 1) for i in range(ncity)
    ]

    constraints = sum(row_constraints) + sum(col_constraints)

    model = cost + constraints * d_max_all * k

    result = solver.solve(model)
    while len(result) == 0 and k <= 1.0:
        k += 0.1
        model = cost + constraints * d_max_all * k
        result = solver.solve(model)

    energy, values = result[0].energy, result[0].values
    q_values = decode_solution(q, values, 1)
    route = np.where(np.array(q_values) == 1)[1]

    def show_route(route: list, time):
        path_length = sum(
            [distances[route[i]][route[(i + 1) % ncity]] for i in range(ncity)]
        )

        x = [i[0] for i in locations]
        y = [i[1] for i in locations]
        plt.figure(figsize=(7, 7))
        plt.title(f"path length: {path_length:.4f}, annealing time: {time:.2f}ms")
        plt.xlabel("x")
        plt.ylabel("y")

        for i in range(ncity):
            r = route[i]
            n = route[(i + 1) % ncity]
            plt.plot([x[r], x[n]], [y[r], y[n]], "b-")
        plt.plot(x, y, "ro")
        plt.show()

        return path_length

    show_route(route, solver.client_result.timing.time_stamps[-1])
```


```python
tsp_slider = IntSlider(
    value=32,
    min=4,
    max=64,
    step=1,
    description="num of cities:",
    disabled=False,
    continuous_update=False,
    orientation="horizontal",
    readout=True,
    readout_format="d",
)
tsp_run_btn = Button(description="Run", button_style="", tooltip="Run", icon="check")
tst_result_out = Output()


def show_tsp_problem(nc):
    tsp_initialize_problem(nc)
    with tst_result_out:
        tst_result_out.clear_output()


def show_tsp_result(btn):
    with tst_result_out:
        tst_result_out.clear_output()
        tsp_solve()


tsp_problem_out = interactive_output(show_tsp_problem, {"nc": tsp_slider})
tsp_run_btn.on_click(show_tsp_result)
display(HBox([tsp_slider, tsp_run_btn]), HBox([tsp_problem_out, tst_result_out]))
```
