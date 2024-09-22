```python
import numpy as np
from geopy.distance import geodesic

import folium

from amplify import BinaryPoly, gen_symbols, sum_poly, Solver, decode_solution
from amplify.constraint import equal_to, less_equal
from amplify.client import FixstarsClient

from math import sqrt
from collections import namedtuple, deque
from ipywidgets import (
    Button,
    FloatSlider,
    IntSlider,
    interactive_output,
    VBox,
    HBox,
    Output,
    HTML,
    Label,
    Accordion,
    IntProgress,
    GridBox,
    Layout,
)

# Near Funabashi Station
lon = (139.9, 140.08)
lat = (35.675500, 35.76)
# 9 locations
parking = [
    (35.67699938102926, 140.0434199237448),
    (35.68494726920934, 139.99303731029542),
    (35.68604762650153, 140.01831984588475),
    (35.69720660219214, 139.98034538800417),
    (35.6981824540223, 140.00360550271415),
    (35.698774929464875, 139.9982410856558),
    (35.700029569368, 139.98558105961536),
    (35.70599837320516, 139.93269833544272),
    (35.71199204224218, 140.0415316476293),
]
_colors = [
    "green",
    "orange",
    "blue",
    "red",
    "purple",
    "pink",
    "darkblue",
    "cadetblue",
    "darkred",
    "lightred",
    "darkgreen",
    "lightgreen",
    "lightblue",
    "darkpurple",
]
```

# Ride sharing

Here, we introduce the problem called collective ridesharing.  
Collective ridesharing refers to a form of ridesharing in which multiple users gather at several large parking lots 
and ride in the same car to the same destination.

In the following demonstration, given multiple people with the same destination and available cars, we will find the allocation of people and cars, such that the travel distance to the parking lot for each person and the number of cars to be used are as small as possible. We formulate the problem as an Ising model and use the Amplify Annealing Engine to find the allocation as a minimization problem.  
Press the [Run] button to run it. 
The [Change Location] button allows you to change the user's location.   
You can change the problem settings and runtime parameters with [Options] button. 


```python
def generate_problem(
    lon_range,
    lat_range,
    parking,
    ncars=None,
    npeople=None,
    C=None,
    lb=1,
    ub=160,
    seed=1,
):
    """
    A function that randomly determines the number of cars, the number of people, and the capacity of cars,
    then generates the coordinates for the cars and people, and generates a distance matrix based on the coordinates.
    """
    np.random.seed(seed)
    if ncars is None:
        ncars = len(parking)
    if npeople is None:
        npeople = np.random.randint(lb, ub)
    if C is None:
        # Limit capacity to ensure viability.
        C = np.random.randint(npeople // ncars + 1, 12)
    if ncars * C < npeople:
        display(
            HTML(
                (
                    "<h3><font color='red'>The number of users exceeds the number of available passengers. Please change the parameters.</font></h3>"
                )
            )
        )
        raise RuntimeError

    n = ncars + npeople
    ind2coord = dict()
    tmp = [
        parking[i][::-1] for i in np.random.choice(len(parking), ncars, replace=False)
    ]
    for i in range(ncars):
        ind2coord[i] = (tmp[i][0], tmp[i][1])
    for i in range(ncars, n):
        lon = np.random.uniform(lon_range[0], lon_range[1])
        lat = np.random.uniform(lat_range[0], lat_range[1])
        tmp.append((lon, lat))
        ind2coord[i] = (lon, lat)

    D = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            D[i][j] = geodesic(tmp[i][::-1], tmp[j][::-1]).m
    return ncars, npeople, D, C, ind2coord
```


```python
class SymbolGenerator:
    def __init__(self, c):
        self.VariableConstructor = c
        self.LastIndex = 0

    def gen_symbols(self, *shape):
        symbol = gen_symbols(self.VariableConstructor, self.LastIndex, shape)
        self.LastIndex += int(np.prod(shape))
        return symbol
```


```python
def regularizeDistance(D):
    ncar, npeople = len(D[0]), len(D)

    for k in range(ncar):
        # Adjust the mean and variance of the distances when the positions of the cars are fixed
        average = sum(D[i][k] for i in range(npeople)) / npeople
        variance = sqrt(sum((D[i][k] - average) ** 2 for i in range(npeople)) / npeople)
        for i in range(npeople):
            D[i][k] = (D[i][k] - average) / variance
    return D
```


```python
def setObjective(q, ncars, npeople, D, C, alpha=1):
    """Objective function"""
    distance_cost = sum_poly(
        [D[i + ncars][j] * q[i][j] for i in range(npeople) for j in range(ncars)]
    )  # Term related to the distance traveled by each user
    ride_rate_cost = sum_poly(
        [sum_poly([q[i][j] / C for i in range(npeople)]) ** 2 for j in range(ncars)]
    )  # Term related to the occupancy rate of each car
    cost = distance_cost - alpha * ride_rate_cost
    return cost
```


```python
def setConstraints(q, ncars, npeople, C, k1=None, k2=None, alpha=1):
    """Functions to set constraint equations for small-scale problems"""
    if k2 is None:
        k2 = max(2 * alpha / C, C * alpha) + 1
    if k1 is None:
        k1 = max(2 + alpha, 2 + 2 * alpha / C) + 1
    # Constraint that one person is riding one car(1)
    allocate_constraints = [
        equal_to(sum_poly([q[i][j] for j in range(ncars)]), 1) for i in range(npeople)
    ]
    # Constraint that no more than C people can ride in one car(2)
    capacity_constraints = [
        less_equal(sum_poly([q[i][j] for i in range(npeople)]), C) for j in range(ncars)
    ]
    constraints = k1 * sum(allocate_constraints) + k2 * sum(capacity_constraints)
    return constraints
```


```python
def construct(ncars, npeople, D, C, k1=None, k2=None, alpha=1):
    """Function to create a model for a small-scale problem after partitioning"""
    GenSymbol = SymbolGenerator(BinaryPoly)
    D = regularizeDistance(D)
    q = GenSymbol.gen_symbols(npeople, ncars)
    cost = setObjective(q, ncars, npeople, D, C, alpha=alpha)
    constraints = setConstraints(q, ncars, npeople, C, k1=k1, k2=k2, alpha=alpha)
    model = cost + constraints
    return model, q
```


```python
def simple_plot(coord, ncars, title=None):
    m = folium.Map([sum(lat) / 2, sum(lon) / 2], tiles="Stamen Toner", zoom_start=12)
    tmp = list(coord.items())
    for j, x in enumerate(tmp):
        if j < ncars:
            folium.Marker(
                location=x[1][::-1],
                icon=folium.Icon(icon="car", prefix="fa", color=_colors[0]),
            ).add_to(m)
        else:
            folium.Marker(
                location=x[1][::-1],
                popup="person",
                icon=folium.Icon(icon="user", prefix="fa", color=_colors[1]),
            ).add_to(m)
    if title:
        display(HTML(f"<h3>{title}</h3>"))
    return m
```


```python
def plot_result(coord, q_values, title=None):
    global _C
    m = folium.Map([sum(lat) / 2, sum(lon) / 2], tiles="Stamen Toner", zoom_start=12)
    legend = "<h4>Legend:</h4>"
    npeople = len(q_values)
    ncars = len(q_values[0])
    columns = ["latitude", "longitude", "size", "name"]
    data = {label: list() for label in columns}
    answer = dict()
    for i in range(npeople):
        car = np.where(np.array(q_values[i]) == 1)[0][-1]
        if car not in answer:
            answer[car] = []
        answer[car].append(i + ncars)

    for k in range(ncars):
        _color = _colors[k % len(_colors)]
        car_loc = coord[k]
        if k in answer:
            tmp = answer[k]
            x = [coord[p][0] for p in tmp] + [car_loc[0]]
            y = [coord[p][1] for p in tmp] + [car_loc[1]]
        else:
            x = car_loc[:1]
            y = car_loc[1:]
            _color = "gray"
        folium.Marker(
            location=[y[-1], x[-1]],
            popup=f"cluster{k}",
            icon=folium.Icon(icon="car", prefix="fa", color=_color),
        ).add_to(m)
        for a, b in zip(y[:-1], x[:-1]):
            folium.Marker(
                location=[a, b],
                popup=f"person{k}",
                icon=folium.Icon(
                    icon="user", prefix="fa", color="white", icon_color=_color
                ),
            ).add_to(m)
        legend += f"<font color={_color}> group{k}（{len(x) - 1}/{_C}）</font>"
    if title:
        display(HTML(f"<h3>{title}</h3>"))
    display(HTML(legend))
    display(m)
```


```python
def ride_share_initialize(
    alpha: float = 1.0,
    C: int = 1,
    npeople: int = 1,
    ncars: int = 1,
    timeout: int = 1000,
    _seed=0,
):
    global _ncars
    global _npeople
    global D
    global _C
    global coord
    global param
    global solver
    client = FixstarsClient()
    client.parameters.timeout = timeout
    solver = Solver(client)
    _ncars, _npeople, D, _C, coord = generate_problem(
        lon, lat, parking, ncars=ncars, C=C, npeople=npeople, seed=_seed
    )
    Parameter = namedtuple("Config", ("alpha"))
    param = Parameter(alpha=alpha)
    m = simple_plot(
        coord,
        ncars,
        title=f"Initial State（C={_C}, ncars={_ncars}, npeople={_npeople}）",
    )
    display(m)


def ride_share_solve(Progress):
    global _ncars
    global _npeople
    global D
    global _C
    global coord
    global param
    global solver
    model, q = construct(_ncars, _npeople, D, _C, alpha=param.alpha)
    Progress.value += 1
    result = solver.solve(model)
    Progress.value += 1
    if len(result) == 0:
        raise RuntimeError("No feasible solution was found.")
    energy, values = result[0].energy, result[0].values
    q_values = decode_solution(q, values, 1)
    Progress.value += 1
    num_used_cars = len(
        set([np.where(np.array(q_values)[i] == 1)[0][-1] for i in range(_npeople)])
    )
    title = "Result（active cars: {}/{}, energy: {:.3f}）".format(
        num_used_cars, _ncars, energy
    )
    Progress.value += 1
    plot_result(coord, q_values, title=title)
    Progress.value += 1
```


```python
alpha_slider = FloatSlider(
    value=1,
    min=0.1,
    max=5,
    step=0.1,
    disabled=False,
    continuous_update=False,
    orientation="horizontal",
    readout=True,
    readout_format="f",
)
C_slider = IntSlider(
    value=8,
    min=1,
    max=15,
    step=1,
    disabled=False,
    continuous_update=False,
    orientation="horizontal",
    readout=True,
    readout_format="d",
)
people_slider = IntSlider(
    value=20,
    min=0,
    max=50,
    step=1,
    disabled=False,
    continuous_update=False,
    orientation="horizontal",
    readout=True,
    readout_format="d",
)
car_slider = IntSlider(
    value=5,
    min=0,
    max=9,
    step=1,
    disabled=False,
    continuous_update=False,
    orientation="horizontal",
    readout=True,
    readout_format="d",
)
time_slider = IntSlider(
    value=1500,
    min=100,
    max=5000,
    step=50,
    disabled=False,
    continuous_update=False,
    orientation="horizontal",
    readout=True,
    readout_format="d",
)

options1 = [
    Label(
        value="alpha :(Emphasis on reducing the less number of units used for the larger number)"
    ),
    alpha_slider,
]
options1 += [Label(value="Time limit [ ms ] :"), time_slider]

options2 = [Label(value="Number of cars ( ncars ) :"), car_slider]
options2 += [Label(value="Number of people ( npeople ) :"), people_slider]
options3 = [Label(value="Maximum number of people per parking space ( C ) :"), C_slider]

options = [GridBox(options1), GridBox(options2), GridBox(options3)]
options = Accordion(children=[HBox(options)])
options.set_title(0, "Options")
options.selected_index = None

Progress = IntProgress(
    value=0,
    min=0,
    max=7,
    step=1,
    description="Solving...",
    bar_style="",
    orientation="horizontal",
)
ride_share_run_btn = Button(
    description="Run", button_style="", tooltip="Run", icon="check"
)
ride_share_problem_out = Output()
ride_share_result_out = Output()

ride_share_relocate_btn = Button(
    description="Change Location", button_style="", tooltip="Change Location", icon=""
)


def show_ride_share_problem(alpha, C, npeople, ncars, timeout, seed=0):
    global Progress
    Progress.value = 0
    ride_share_initialize(alpha, C, npeople, ncars, timeout, _seed=seed)
    with ride_share_problem_out:
        ride_share_result_out.clear_output()


def show_ride_share_problem_relocate(btn):
    global Progress
    Progress.value = 0
    with ride_share_problem_out:
        ride_share_problem_out.clear_output()
        ride_share_initialize(
            alpha_slider.value,
            C_slider.value,
            people_slider.value,
            car_slider.value,
            time_slider.value,
            _seed=None,
        )
        ride_share_result_out.clear_output()


def show_ride_share_result(btn):
    global Progress
    Progress.value = 0
    with ride_share_result_out:
        Progress.value += 1
        ride_share_result_out.clear_output()
        Progress.value += 1
        ride_share_solve(Progress)


ride_share_problem_out = interactive_output(
    show_ride_share_problem,
    {
        "alpha": alpha_slider,
        "C": C_slider,
        "npeople": people_slider,
        "ncars": car_slider,
        "timeout": time_slider,
    },
)
ride_share_relocate_btn.on_click(show_ride_share_problem_relocate)
ride_share_run_btn.on_click(show_ride_share_result)
display(
    VBox([options, HBox([ride_share_run_btn, ride_share_relocate_btn, Progress])]),
    VBox([ride_share_problem_out, ride_share_result_out]),
)
```


```python

```
