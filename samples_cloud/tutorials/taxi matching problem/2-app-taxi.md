# Taxi Matching Problem
Let's solve the taxi matching problem as an example of a problem that uses both an objective function and constraints.

The taxi matching problem is the problem of minimizing the cost of dispatching a taxi given multiple customers and multiple taxi locations respectively.

The cost of dispatching a taxi can be defined in various ways, but for simplicity, we will assume that it is the total distance between the taxi and the customer. By matching taxis and customers, we can decide where to dispatch the taxi so as to minimize the total distance between each taxi and the destination customer.

## Formulation of the Problem

First of all, the assumption of the problem here is that there are $N$ customers and the same number of $N$ taxis. Suppose that we are given the coordinates $(c_{i,x}, c_{i,y})$ of the customers and $(t_{j,x}, t_{j,y})$ of the taxis with indices $i, j = 0, 1, \cdots, N -1$. From these coordinates, let the distance between customer $i$ and taxi $j$ be the following: 

$$
d_{ij} = \sqrt{(c_{i,x} - t_{j,x})^2 + (c_{i,y} - t_{j,y})^2}
$$ 

### Decision Variable

The relation between customer $i$ and taxi $j$ can be divided into the following two patterns:

* Customer $i$ is assigned a taxi $j$
* Taxi $j$ is not assigned to customer $i$

We use the binary variable $q_{ij}$ to represent these two states.

* When taxi $j$ is assigned to customer $i$, $q_{ij} = 1$
* When no taxi $j$ is assigned to customer $i$, $q_{ij} = 0$

|Customer \ Taxi| $0$ | $1$ | ... | $N-1$|  
|:---:|:---:|:---:|:---:|:---:|
|$0$| $q_{0,0}$ | $q_{0,1}$ | ... | $q_{0,N-1}$|
|$1$| $q_{1,0}$ | $q_{1,1}$ | ... | $q_{1,N-1}$|
|$\vdots$| $\vdots$ | $\vdots$ | ... | $\vdots$|
|$N -1$| $q_{N-1,0}$ | $q_{N-1,1}$ | ... | $q_{N-1,N-1}$|

### Objective Function

Using the above binary variables, the objective function, which is the total distance between the matched customer and the taxi, is given by following:  
Since the variable $q_{ij}$ means that customer $i$ and taxi $j$ are matched when $1$, we only add up the distances that result in $q_{ij} = 1$.

$$
\sum_{i, j=0}^{N-1}d_{ij}q_{ij}
$$

### Constraint

The next step is to define the constraints.

First, since we always assign one taxi to one customer, we need the following constraint for customer $i$.

$$
\sum_{j=0}^{N -1}q_{ij} = 1 
$$

In addition, since one taxi is always assigned to one customer, we also need the following constraint for taxi $j$:

$$
\sum_{i=0}^{N -1}q_{ij} = 1 
$$


## Implementing the Problem

Since we need the coordinates of the customers and the taxies as input data, we will create a function that randomly generates the coordinates of the customers and the taxies and calculates the distances for all combinations of customers and taxies.


```python
import numpy as np


# Randomly generate the coordinates of the customers and the taxies, and calculate the distances between the customers and the taxies
def gen_random_locations(N_customers: int, N_taxies: int):
    # Customer coordinates
    loc_customers = np.random.uniform(size=(N_customers, 2))

    # Taxi coordinates
    loc_taxies = np.random.uniform(size=(N_taxies, 2))

    # Calculate the distance between a customer and a taxi in matrix form
    all_diffs = np.expand_dims(loc_customers, axis=1) - np.expand_dims(
        loc_taxies, axis=0
    )
    distances = np.sqrt(np.sum(all_diffs**2, axis=-1))

    return loc_customers, loc_taxies, distances
```

For visualization purposes, we also create a function that, given the coordinates of a customer and a taxi, plot those coordinates.


```python
%matplotlib inline
import matplotlib.pyplot as plt


# Visualize the location of customers and taxis
def show_plot(loc_customers: np.ndarray, loc_taxies: np.ndarray):
    markersize = 100
    plt.subplots(nrows=1, ncols=1, figsize=(10, 10))
    plt.xlabel("x")
    plt.ylabel("y")
    plt.scatter(
        *zip(*loc_customers), label="Customers", marker="o", color="red", s=markersize
    )
    plt.scatter(
        *zip(*loc_taxies), label="Taxies", marker="^", color="blue", s=markersize
    )

    plt.legend(loc="upper right")
    plt.show()
```

Determine `N` corresponding to the number of customers and the number of taxis, and generate their coordinates and distances with the `gen_random_locations` function we defined earlier. Plot the generated results to visualize the locations of customers and taxis.


```python
N = 5

Lc, Lt, d = gen_random_locations(N_customers=N, N_taxies=N)

show_plot(Lc, Lt)
```

### Building a Binary Polynomial Model

Next, we define the QUBO variables that we will need. Since we want to have $N$ taxis for each $N$ customer, we define the QUBO variable as a two-dimensional array of $N\times N$ as follows:


```python
from amplify import (
    gen_symbols,
    BinaryPoly,
)

# Create QUBO variables
q = gen_symbols(BinaryPoly, N, N)
```

Using these QUBO variables, the objective function is obtained as follows:


```python
from amplify import sum_poly

cost = sum_poly(N, lambda i: sum_poly(N, lambda j: d[i][j] * q[i][j]))
```

The next step is to define the constraints.

The two constraints described at the beginning are represented as follows using the `equal_to` function, and they are added up to construct a constraint object.


```python
from amplify import sum_poly, BinaryQuadraticModel
from amplify.constraint import equal_to

customer_has_one_taxi = sum(
    [equal_to(sum_poly(N, lambda j: q[i][j]), 1) for i in range(N)]
)

taxi_has_one_customer = sum(
    [equal_to(sum_poly(N, lambda i: q[i][j]), 1) for j in range(N)]
)

constraints = customer_has_one_taxi + taxi_has_one_customer
```

By adding the objective function and constraints, the final binary polynomial model can be obtained as follows.

Here, the strength of the constraints relative to the objective function is important.
Just to conclude, it is enough to set the maximum value of $d_{ij}$, and we will not go into the discussion of how strong it should be.


```python
constraints *= np.amax(d)  # Set the intensity

# Combine objective function and constraints
model = cost + constraints
```

### Running the Ising Machine

Set the client of the Ising machine to `FixstarsClient`, and also create a solver to solve the problem as follows:


```python
from amplify import Solver
from amplify.client import FixstarsClient

# Set up the client
client = FixstarsClient()
client.parameters.timeout = 1000  # Timeout is 1 second
# client.token = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # If you are using it in a local environment, please enter the access token for Amplify AE

# Set up a solver.
solver = Solver(client)

# solve a problem
result = solver.solve(model)
```

The obtained solution can be checked as follows.

The final solution can be obtained by using the decode_solution function and assigning it to the variables defined in the beginning.


```python
from amplify import decode_solution

# If result is empty, the constraint condition is not satisfied and the solution cannot be found.
if len(result) == 0:
    raise RuntimeError("Given constraint conditions are not satisfied")

for sol in result:
    values = sol.values
    energy = sol.energy
    print(f"energy = {energy}")
    print(f"q = {decode_solution(q, values)}")

solution = np.array(decode_solution(q, result[0].values))
```

The array of decision variables indicates that if there is $1$ in the $j$th column of the $i$th row, the taxi $j$ will be assigned to customer $i$. Thus, we can get the information about which taxi to match to which customer as follows:


```python
customers = np.where(solution == 1)[0]
taxies = np.where(solution == 1)[1]
matches = list(zip(customers, taxies))
```

Finally, we visualize the obtained data of matching customers and taxis.


```python
def plot_matching(loc_customers, loc_taxies, matches):
    markersize = 100
    plt.subplots(nrows=1, ncols=1, figsize=(10, 10))
    plt.xlabel("x")
    plt.ylabel("y")
    plt.scatter(
        *zip(*loc_customers), label="Customers", marker="o", color="red", s=markersize
    )
    plt.scatter(
        *zip(*loc_taxies), label="Taxies", marker="^", color="blue", s=markersize
    )

    for i, j in matches:
        xc, yc = loc_customers[i]
        xt, yt = loc_taxies[j]
        plt.plot([xc, xt], [yc, yt], color="green", linestyle="--")

    plt.legend(loc="upper right")

    plt.show()


plot_matching(loc_customers=Lc, loc_taxies=Lt, matches=matches)
```

## The Case Where the Number of Customers is Less Than the Number of Taxis

In this section, we consider the taxi matching problem when the number of customers is smaller than the number of taxis.
In this case, we need to formulate constraints that take into account both the case where the number of customers assigned to each taxi is zero and the case where the number of customers assigned to each taxi is one.
Such constraints can be formulated using inequality constraints.

Given $N_c$ customers and $N_t$ taxis ($N_c < N_t$) and their coordinates, let $d_{ij}$ be the distance between customer $i$ and taxi $j$ as before.

### Objective Function

The objective function is the same as before, but we consider that $N_c$ and $N_t$ are different values.

$$
\sum_{i=0}^{N_c-1}\sum_{j=0}^{N_t - 1}d_{ij}q_{ij}
$$


### Constraint

Since there are more taxis than customers, every customer can be matched with one taxi.
Therefore, for customer $i$, the following holds.
$$
\sum_{j=0}^{N_{\rm t}-1}q_{ij} = 1 
$$

On the other hand, for a taxi, there may be no customers at all. Therefore, we impose a constraint by inequality, taking into account both the cases where the number of customers is zero and the case where the number of customers is one.
The following holds for taxi $j$.
$$
\sum_{i=0}^{N_{\rm c} -1}q_{ij} \le 1
$$



```python
import numpy as np
from amplify import decode_solution, gen_symbols, BinaryPoly, sum_poly, Solver
from amplify.constraint import less_equal, equal_to
from amplify.client import FixstarsClient

Nc = 5  # Number of customers
Nt = 8  # Number of taxis

# Generate customers' coordinates, taxis' coordinates, and distance matrix between customers and taxis
Lc, Lt, d = gen_random_locations(Nc, Nt)

# Create a QUBO variable
q = gen_symbols(BinaryPoly, Nc, Nt)

# Objective function
cost = sum_poly(Nc, lambda i: sum_poly(Nt, lambda j: d[i][j] * q[i][j]))

############################################################################################
# Constraint
# It is useful to use less_equal, equal_to, sum_poly
############################################################################################

customer_has_one_taxi = sum(
    [equal_to(sum_poly(Nt, lambda j: q[i][j]), 1) for i in range(Nc)]
)

taxi_has_one_or_less_customer = sum(
    [less_equal(sum_poly(Nc, lambda i: q[i][j]), 1) for j in range(Nt)]
)

constraints = customer_has_one_taxi + taxi_has_one_or_less_customer

############################################################################################

# Construct a logical model by adding the objective function and constraint objects
constraints *= np.amax(d)  # Set the intensity
model = cost + constraints

# Set up the client
client = FixstarsClient()
client.parameters.timeout = 1000  # Timeout is 1 second
# client.token = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # If you are using it in a local environment, please enter the access token for Amplify AE

# Set up a solver.
solver = Solver(client)

# solve a problem
result = solver.solve(model)

# If result is empty, the constraint condition is not satisfied.
if len(result) == 0:
    raise RuntimeError("Given constraint conditions are not satisfied")

solution = np.array(decode_solution(q, result[0].values))

customers = np.where(solution == 1)[0]  # List of customer indexes
taxies = np.where(solution == 1)[1]  # Customer list
matches = list(zip(customers, taxies))  # Index of customers and taxis to be matched

# Plotting the matching of customers and taxis
plot_matching(loc_customers=Lc, loc_taxies=Lt, matches=matches)
```


```python

```
