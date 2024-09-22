# Ride sharing

The problem we are dealing with in this tutorial is called collective ridesharing.

Collective ridesharing refers to a form of ridesharing in which multiple users gather at several large parking lots  
and ride in the same car to the same destination.

（There is another type of ridesharing called traveling ridesharing, but it will not be discussed here.）
![picture](../figures/ride-share_abstract.png)


Here, given multiple people with the same destination and available cars, we will find the allocation of people and cars such that the travel distance to the parking lot for each person and the number of cars to be used are as small as possible.   
We formulate the problem as a model that can be run on an Ising machine, and find the allocation as a minimization problem.
  

## Formulation

First, we define the constants and variables necessary for the formulation.

#### Constant

* $N$：Number of rideshare users
* $M$：Number of available cars
* $C$：Number of available seats per car
* $D$：Matrix such that $ik$component$(d_{ik})$ is the distance between user $i$ and car $k$

#### Variables

- $q_{ik}\in\{0,1\}\quad(i\in\{1,\dots,N\}, k\in\{1,\dots,M\})$  
  Binary variables representing whether or not person $i$ rides in car $k$ ($q_{ik}=1\Leftrightarrow$ person $i$ rides in car $k$)
- $y_{lk}\in\{0,1\}\quad(l\in\{0,\dots,C\},k\in\{1,\dots,M\})$  
  Binary variables that satisfy $\sum_ly_{lk}=\sum_iq_{ik}$ (used to express constraints on the number of passengers)



Then, we consider the constraints where the variables must satisfy.

### Constraints

- Each person always rides in one car.  
  $\sum_{k=1}^Mq_{ik}=1(\forall i\in\{1,\dots,N\})$
  
- The actual number of passengers does not exceed the number of available seats.  
  $\sum_{i=1}^Nq_{ik}\leq C(\forall k\in\{1,\dots,M\})$

Finally, we will consider an objective function that satisfies the followings:

1. Users use a car that is as close as possible to their location.
2. Users travel with as few cars as possible.

### Objective function

- Users should avoid unnecessary travel as much as possible. 
    $\text{minimize}\quad\sum_{i,k}d_{ik}q_{ik}$     
- We want to minimize the number of cars used as much as possible$\space\Rightarrow\space$Maximize the number of passengers per car.
    $\text{maximize}\quad\sum_{k}\left(\sum_i\frac{q_{ik}}{C}\right)^2$

Considering these two items, the following objective function can be set.

$$\sum_{i,k}d_{ik}q_{ik}-\alpha\sum_{k}\left(\sum_i\frac{q_{ik}}{C}\right)^2$$

#### Note
Let $\alpha>0$ be the parameter that determines how much importance is placed on the number of cars in use. 
The closer the value of $\alpha$ is to $0$, the more the optimization places emphasis on minimizing the distances traveled by users. The greater the value of $\alpha$ is, the more the optimization places emphasis on minimizing the number of cars used.  
If $\alpha$ is large, the term regarding the distance traveled will be less important. The visualization result thus will be cleaner if $\alpha$ is small.

### Summary

From the above, the collective ridesharing problem can be formulated as the following Ising model.

$$
\begin{align}
H&=H_{\rm cost}+H_{\rm constraint}\\
H_{\rm cost}&= \sum_{i,k}d_{ik}q_{ik}-\alpha\sum_{k}\left(\sum_i\frac{q_{ik}}{C}\right)^2\\
H_{\rm constraint} &= k_1\sum_{i=1}^N\left(\sum_{k=1}^Mq_{ik}-1\right)^2+k_2\sum_{k=1}^M\left(\sum_{i=1}^Nq_{ik}-\sum_{l=0}^Cy_{lk}\right)^2
\end{align}
$$


$k_1, k_2$ are constants that determine the strength of the constraints.  
In order to ensure the feasibility of the solution, the size of the constant must be set so that the objective function is not improved by violating the constraint. 
In the present case, at least the following inequality should hold. The details of the derivation are omitted.

$$
\begin{align}
k_1&>{\rm max}\left(− {\rm min\space}d_{ik}+
\frac{2c − 1}{c^2}\alpha,\space
{\rm max\space}d_{ik}−\frac{2c − 1}{c^2}\alpha
\right)\\
k_2&>\frac{2c − 1}{c^2}\alpha
\end{align}
$$

## Implementing the problem
Since we need the positions of the cars and the users as input data, we create a function to randomly generate their positions (latitude and longitude).


```python
import numpy as np
from geopy.distance import geodesic


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
    then generates the coordinates of the points of the number of cars + the number of people, and generates a distance matrix based on the coordinates.
    """
    np.random.seed(seed)
    if ncars is None or (isinstance(ncars, int) and ncars > len(parking)):
        if isinstance(ncars, int) and ncars > len(parking):
            print(
                f"Maximum value of ncars is {len(parking)}.\n ncars : {ncars} -> {len(parking)}."
            )
        ncars = len(parking)
    if npeople is None:
        npeople = np.random.randint(lb, ub)
    if C is None:
        C = np.random.randint(npeople // ncars + 1, npeople + 2)
    if ncars * C < npeople:
        print("Fail to create valid problem.\nPlease retry after changing random seed.")
        return None, None, None, None, None
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

    D = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            D[i, j] = geodesic(tmp[i][::-1], tmp[j][::-1]).m
    return ncars, npeople, D, C, ind2coord
```

For visualization purposes, we also create a function that plots the coordinates of cars and users on a map when they are input.


```python
import folium

_colors = [
    "green",
    "orange",
    "blue",
    "pink",
    "red",
    "purple",
    "darkblue",
    "cadetblue",
    "darkred",
    "lightred",
    "darkgreen",
    "lightgreen",
    "lightblue",
    "gray",
    "darkpurple",
]


def simple_plot(coord, ncars):
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
    return m
```

After we define the candidate locations of the cars as follows, we use `generate_problem` function defined earlier to generate the number of users, the number of people using the cars, the number of available seats in the cars, and the locations of the users and the cars. The `simple_plot` function is used to visualize them.


```python
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
```


```python
ncars, npeople, D, C, index2coordinate = generate_problem(lon, lat, parking, seed=0)
simple_plot(index2coordinate, ncars)
```


```python
print(ncars, npeople, C)
```

### Building a quadratic polynomial model

Next, we define the necessary QUBO variables. Since we will have $M$ cars for $N$ users, we will define the QUBO variables as a $M\times N$ two-dimensional array as follows:


```python
from amplify import BinarySymbolGenerator

gen = BinarySymbolGenerator()
q = gen.array(npeople, ncars)
```

Then, we define the objective function and constraints. 
First, in order to align the order of the terms related to the distance and the number of cars in the objective function, we use the following function to adjust the mean of the elements of the distance matrix to 0 and the variance to 1.


```python
from math import sqrt


def regularizeDistance(D):
    average = D.mean(axis=0, keepdims=True)
    std = D.std(axis=0, keepdims=True, ddof=0)
    return (D - average) / std
```


```python
D = regularizeDistance(D)
```

The next step is to define the objective function.  
The `sum_poly` function is used to represent polynomials containing QUBO variables.  
The objective function is as follows:
$$\sum_{i,k}d_{ik}q_{ik}-\alpha\sum_{k}\left(\sum_i\frac{q_{ik}}{C}\right)^2$$
The first half of the term is related to the distance traveled and the second half is related to the occupancy rate of each car.


```python
from amplify import sum_poly


def setObjective(q, ncars, npeople, D, C, alpha=1):
    """Objective function"""
    # Term related to the distance traveled by each user
    distance_cost = sum_poly(D[ncars:, :ncars] * q)

    # Term related to the occupancy rate of each vehicle
    ride_rate_cost = ((q.sum(axis=0) / C) ** 2).sum()

    cost = distance_cost - alpha * ride_rate_cost
    return cost
```

The constraint equation can be expressed as follows  
The `equal_to` function is used to express constraint(1) $\sum_{k=1}^Mq_{ik}=1(\forall i\in\{1,\dots,N\})$  
and the `less_equal` function is used to express constraint(2) $\sum_{i=1}^Nq_{ik}\leq C(\forall k\in\{1,\dots,M\})$.


```python
from amplify.constraint import one_hot, less_equal


def setConstraints(q, ncars, npeople, C, k1=None, k2=None, alpha=1):
    """Functions to set constraint equations for small-scale problems"""
    if k2 is None:
        k2 = 2 * alpha / C + 1
    if k1 is None:
        k1 = (2 + 2 * alpha / C) + 1

    # Constraint(1) that each person rides in one car
    allocate_constraints = [one_hot(q[i]) for i in range(npeople)]

    # Constraint(2) that no more than C people can fit in one car
    capacity_constraints = [less_equal(sum_poly(q[:, j]), C) for j in range(ncars)]

    constraints = k1 * sum(allocate_constraints) + k2 * sum(capacity_constraints)
    return constraints
```

The final Ising model is obtained by adding up the above objective function and constraints.


```python
cost = setObjective(q, ncars, npeople, D, C)
constraints = setConstraints(q, ncars, npeople, C)

model1 = cost + constraints
```

### Running the Ising machine
Set the Ising machine client to `FixstarsClient`, create a solver, and solve the problem as follows:


```python
# Use in the solving part
from amplify import Solver
from amplify.client import FixstarsClient

client = FixstarsClient()
client.parameters.timeout = 2000  # Time limit
# client.token = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # If you use it in a local environment, please enter the access token for Fixstars Amplify AE

solver = Solver(client)

result = solver.solve(model1)
```

Then, we will check the obtained solutions.  
You can use `decode_solution` to substitute them to the original variables.


```python
if len(result) == 0:
    # 実行可能解が見つかっていなければ例外を投げる
    raise RuntimeError("No feasible solution was found.")

q_values = q.decode(result[0].values)
```

Finally, we visualize the resulting assignments using the following function:


```python
def plot_result(coord, q_values):
    m = folium.Map([sum(lat) / 2, sum(lon) / 2], tiles="Stamen Toner", zoom_start=12)
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
        status = "active"
        car_loc = coord[k]
        if k in answer:
            tmp = answer[k]
            x = [coord[p][0] for p in tmp] + [car_loc[0]]
            y = [coord[p][1] for p in tmp] + [car_loc[1]]
        else:
            x = car_loc[:1]
            y = car_loc[1:]
            status = "empty"
        folium.Marker(
            location=[y[-1], x[-1]],
            popup=f"cluster{k}",
            icon=folium.Icon(icon="car", prefix="fa", color=_colors[k % len(_colors)]),
        ).add_to(m)
        for a, b in zip(y[:-1], x[:-1]):
            folium.Marker(
                location=[a, b],
                popup=f"person{k}",
                icon=folium.Icon(
                    icon="user",
                    prefix="fa",
                    color="white",
                    icon_color=_colors[k % len(_colors)],
                ),
            ).add_to(m)
    return m
```


```python
plot_result(index2coordinate, q_values)
```

## Developmental topics (Splitting the problem)
Currently, the size of the problem that can be solved by an annealing machine is limited, so we consider dividing the problem by two classes of clustering.  
By repeating the clustering process until the number of bits in the problem is below a set value, and solving the problem at the beginning for each cluster obtained, 
we aim to reduce the computation time and solve the problem of the number of bits. 

### Purpose

The ultimate goal is to optimize according to the following flow chart.

![Flow chart](../figures/ride-share_clustering.png)

### Formulation

The formulation is as follows:

#### Constant

* $N$：Number of rideshare users  
* $M$：Number of available cars  
* $D$：matrix that the $ik$ component $(d_{ik})$ is the distance between user (car) $i$ and user (car) $k$ 

#### Variables

$q_{k}\in\{0,1\}\quad(k\in\{1,\dots,M,\dots,M+N\})$  
Binary variable representing which cluster a person (or car) $k$ belongs to  
($q_{k}=1\,\Leftrightarrow$ people (or cars) $k$ belong to cluster 1)

#### Constraints

- Divide it as evenly as possible 

  $\sum_{k=1}^Mq_k=\frac{M}{2}$  
  $\sum_{k=M+1}^{M+N}q_k=\frac{N}{2}$

#### Objective function

- People/cars that are (are) near each other belong to the same cluster  
- People/cars that are (are) far away from each other belong to different clusters

  $\text{minimize}\quad\sum_{i,j}d_{ij}(2q_i-1)(2q_j-1)$

From the above, the clustering of the two classes can be formulated as the following Ising model.

$$
\begin{align}
H&=H_{\rm cost}+H_{\rm constraint}\\
H_{\rm cost}&=\sum_{i,j}d_{ij}(2q_i-1)(2q_j-1)\\
H_{\rm constraint}&=k_1\left(\sum_{k=1}^Mq_k-\frac{M}{2}\right)^2+k_1\left(\sum_{k=M+1}^{M+N}q_k-\frac{N}{2}\right)^2
\end{align}
$$
To guarantee the feasibility of the solution, the constant $k_1$ must satisfy the inequality $k_1>2{\space\rm max}\sum_jd_{ij}$.
### Implementation
Based on the above formulation, we implement it using AMPLIFY.  
The first step is to define the variables.


```python
n = ncars + npeople

q = BinarySymbolGenerator().array(n)

print(D.shape)
print(q.shape)
```

Then, prepare the objective function.


```python
from amplify import einsum

cost = einsum("ij,i,j->", D, (2 * q - 1), (2 * q - 1))
```

The constraints are as follows:


```python
from amplify.constraint import equal_to

# Constraint for the number of cars after the split to be half of the original number
car_constraints = equal_to(sum_poly(q[:ncars]), ncars // 2)

# Constraint for the number of people after the split to be half of the original number.
people_constraints = equal_to(sum_poly(q[ncars:n]), npeople // 2)

# Set the strength of the constraint
k1 = 2 * int(D.sum(axis=1).max()) + 3

constraints = car_constraints + people_constraints
constraints *= k1
```

The final model will look like this.


```python
model_split = cost + constraints
```

### Running the Ising machine
As before, we run the Ising machine to solve the problem.


```python
result = solver.solve(model_split)

if len(result) == 0:
    # Throw an exception if no viable solution is found
    raise RuntimeError("No feasible solution was found.")
else:
    # If viable solutions are found, display their objective function values in order
    for solution in result:
        energy = solution.energy
        values = solution.values
        print(f"energy = {energy}")
        # print(f"q = {decode_solution(q, values)}")
```

Then we define a function to divide the distance matrix and coordinates based on the solution.


```python
def divide(q, D, coord, result):
    """Function to split the result of clustering"""
    energy, values = result[0].energy, result[0].values
    q_values = q.decode(values)
    cluster1 = np.where(np.array(q_values) == 1)[0]
    cluster2 = np.where(np.array(q_values) == 0)[0]
    nc1 = len(cluster1)
    nc2 = len(cluster2)
    D1 = np.zeros((nc1, nc1))
    D2 = np.zeros((nc2, nc2))

    C1 = dict()
    C2 = dict()
    for i in range(nc1):
        C1[i] = coord[cluster1[i]]
        for j in range(nc1):
            D1[i][j] = D[cluster1[i]][cluster1[j]]
    for i in range(nc2):
        C2[i] = coord[cluster2[i]]
        for j in range(nc2):
            D2[i][j] = D[cluster2[i]][cluster2[j]]
    return D1, D2, C1, C2
```

Next, we define a function that will draw the result of the segmentation on the map


```python
def plot_split_problem(coord: list, ncars: list):
    m = folium.Map([sum(lat) / 2, sum(lon) / 2], tiles="Stamen Toner", zoom_start=12)

    for i in range(len(ncars)):
        tmp = list(coord[i].items())
        for j, x in enumerate(tmp):
            if j < ncars[i]:
                folium.Marker(
                    location=x[1][::-1],
                    popup=f"cluster{i}",
                    icon=folium.Icon(icon="car", prefix="fa", color=_colors[i]),
                ).add_to(m)
            else:
                folium.Marker(
                    location=x[1][::-1],
                    popup=f"person{i}",
                    icon=folium.Icon(
                        icon="user", prefix="fa", color="white", icon_color=_colors[i]
                    ),
                ).add_to(m)

    return m
```

Use the `plot_split_problem` function to plot the coordinates after splitting.


```python
D1, D2, cluster1, cluster2 = divide(q, D, index2coordinate, result)
plot_split_problem([cluster1, cluster2], [ncars // 2, ncars - ncars // 2])
```

## Summary
Finally, we implement the sequence of splitting the problem according to the following flow chart (again) $\Rightarrow$ Solve the problem after splitting.

![Flow chart](../figures/ride-share_clustering.png)

The first step is to define a function to create a model for splitting the problem.


```python
def splitProblem(q, ncars, npeople, D, k1=None):
    """Function to create a model to partition the problem"""
    n = ncars + npeople
    if (
        k1 is None
    ):  # Set the coefficient as small as possible, since large coefficients may cause a problem
        k1 = 2 * int(max([sum(D[i]) for i in range(n)])) + 3
    half_cars = ncars // 2
    half_emp = npeople // 2
    cost = einsum("ij,i,j->", D, (2 * q - 1), (2 * q - 1))
    constraints = equal_to(sum_poly(q[:ncars]), half_cars) + equal_to(
        sum_poly(q[ncars:n]), half_emp
    )
    model = cost + k1 * constraints
    return model, half_cars, half_emp
```

Then, define a function to model each small-scale problem generated.


```python
def construct(ncars, npeople, D, C, k1=None, k2=None, alpha=1):
    """Function to create a model for a small-scale problem after partitioning"""
    D = regularizeDistance(D)
    q = BinarySymbolGenerator().array(npeople, ncars)
    cost = setObjective(q, ncars, npeople, D, C, alpha=alpha)
    constraints = setConstraints(q, ncars, npeople, C, k1=k1, k2=k2, alpha=alpha)
    model = cost + constraints
    return model, q
```

Next, we define a function to integrate the optimization results of the small-scale problem.


```python
def make_data(coord, q_values, C, last=0, data=None, nframe=1):
    if data is None:
        columns = ["latitude", "longitude", "size", "name", "time", "color"]
        data = {label: list() for label in columns}
    npeople = len(q_values)
    ncars = len(q_values[0])
    answer = dict()
    for i in range(npeople):
        car = np.where(np.array(q_values[i]) == 1)[0][-1]
        if car not in answer:
            answer[car] = []
        answer[car].append(i + ncars)

    loc = [[], []]
    for k in range(ncars):
        status = "active"
        car_loc = coord[k]
        if k in answer:
            tmp = answer[k]
            x = [coord[p][0] for p in tmp] + [car_loc[0]]
            y = [coord[p][1] for p in tmp] + [car_loc[1]]
        else:
            x = car_loc[:1]
            y = car_loc[1:]
            status = "empty"
        loc[0] += y
        loc[1] += x
        for i in range(nframe):
            data["latitude"] += list(
                map(lambda a: ((nframe - i) * a + y[-1] * i) / nframe, y)
            )
            data["longitude"] += list(
                map(lambda a: ((nframe - i) * a + x[-1] * i) / nframe, x)
            )
            data["size"] += [0.5] * (len(x) - 1) + [3]
            data["name"] += [f"group{k+last}({status})"] * len(x)
            data["time"] += [i] * len(x)
            data["color"] += [_colors[k + last]] * len(x)
    return data
```


```python
def plot_final_result(data):
    m = folium.Map([sum(lat) / 2, sum(lon) / 2], tiles="Stamen Toner", zoom_start=12)
    df = pd.DataFrame(data)
    for _name in data["name"]:
        tmp = df[df["name"] == _name]
        x = list(tmp["longitude"])
        y = list(tmp["latitude"])
        folium.Marker(
            location=[y[-1], x[-1]],
            popup=f"cluster_{_name}",
            icon=folium.Icon(icon="car", prefix="fa", color=list(tmp["color"])[-1]),
        ).add_to(m)
        for a, b, c in zip(y[:-1], x[:-1], list(tmp["color"])[:-1]):
            folium.Marker(
                location=[a, b],
                popup=f"person_{_name}",
                icon=folium.Icon(icon="user", prefix="fa", color="white", icon_color=c),
            ).add_to(m)
    return m
```

Then, we create a `namedtuple` that manages the parameter $\alpha$ (which sets the strength of the term regarding the number of cars) that controls the size of the problem after splitting.  
Here, we divide the problem up to 50 bits.


```python
from collections import namedtuple

Parameter = namedtuple("Config", ("bit_size", "alpha"))

param = Parameter(bit_size=50, alpha=10)
```

We solve the problem by using the `solve` function defined below.  

The first step is to divide the problem into parts until the size of the problem becomes small enough, and then solve the divided problem.  
The number of bits required for the small-scale problem is (number of cars) * (number of users + number of possible passengers),   
so as long as this value is greater than a predetermined value (50 in this case), two classes will be clustered.


```python
from collections import deque
from IPython.display import display
import pandas as pd


def solve(ncars, npeople, D, C, coord, param, debug=False):
    print("Problem setting")
    display(simple_plot(coord, ncars))
    client = FixstarsClient()
    client.parameters.timeout = 200  # Time limit
    solver = Solver(client)
    print("Splitting the problem...", end="")
    queue = deque([(ncars, npeople, D, coord)])
    while (queue[0][1] + C) * queue[0][0] > param.bit_size:
        (ncars, npeople, D, coord) = queue.popleft()

        q = BinarySymbolGenerator().array(ncars + npeople)

        model, ncars1, npeople1 = splitProblem(q, ncars, npeople, D)
        result = solver.solve(model)
        if len(result) == 0:
            raise RuntimeError("No feasible solution was found.")
        D1, D2, C1, C2 = divide(q, D, coord, result)
        queue.append((ncars1, npeople1, D1, C1))
        queue.append((ncars - ncars1, npeople - npeople1, D2, C2))
    print("Completed")
    print("Describing the results...", end="")
    m = plot_split_problem([x[-1] for x in queue], [x[0] for x in queue])
    display(m)
    print("Completed")

    print("Solving the problem after the split...")
    client = FixstarsClient()
    client.parameters.timeout = 1000  # Time limit
    solver = Solver(client)
    index = 0
    last = 0
    data = None
    while queue:
        index += 1
        (ncars, npeople, D, coord) = queue.pop()
        model, q = construct(ncars, npeople, D, C, alpha=param.alpha)
        result = solver.solve(model)
        if len(result) == 0:
            raise RuntimeError("No feasible solution was found.")
        print(f"The small-scale problem {index} was solved")
        q_values = q.decode(result[0].values)
        data = make_data(coord, q_values, C, data=data, last=last)
        last += ncars
    print("Describing the results...")
    m = plot_final_result(data)
    display(m)
```

Let's solve it.


```python
problem = generate_problem(lon, lat, parking, C=12, seed=0)
```


```python
solve(*problem, param)
```
