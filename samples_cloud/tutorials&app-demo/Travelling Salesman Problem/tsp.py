#!/usr/bin/env python
# coding: utf-8

# # Travelling Salesman Problem
# 
# This section describes how to solve the traveling salesman problem using Amplify.
# 
# ## Formulation of the Traveling Salesman Problem
# 
# [The Traveling Salesman Problem](https://en.wikipedia.org/wiki/Travelling_salesman_problem) is a combinatorial optimization problem to find the shortest route that visits all cities exactly once, given a set of cities and the distances between each pair of cities.
# 
# <!-- ![240px-GLPK_solution_of_a_travelling_salesman_problem.svg.png](attachment:3d4196f6-b79c-4fc1-b924-1668e1f7f543.png) -->
# 
# In order to use the Ising machine, the combinations of paths need to be represented by polynomials with respect to binary or Ising variables.
# Every combination of paths can be represented by a table of variables that shows which city is visited in which order.
# For example, the following table for four cities will represent the route $A \rightarrow C \rightarrow B \rightarrow D$.
# 
# | turn| A | B | C | D |
# |-----|---|---|---|---|
# | 1st | 1 | 0 | 0 | 0 |
# | 2nd | 0 | 0 | 1 | 0 |
# | 3rd | 0 | 1 | 0 | 0 |
# | 4th | 0 | 0 | 0 | 1 |
# 
# We assign binary variables $\left\{0, 1\right\}$ to each element of the table.
# We interpret a path by following the cities where $1$ is assigned in the right order from 1st to 4th.
# That is, for a traveling salesman problem in $N$ cities, it suffices to have $N^2$ variables.
# 
# We denote each variable in the above table as $q_{n,i}$ using the route order $n$ and the city index $i$. Then all the distances of the travel routes are represented as follows:
# 
# $$
#  \sum_{n=0}^{N-1}{\sum_{i=0}^{N-1}{\sum_{j=0}^{N-1}{ d_{ij} q_{n, i} q_{n+1, j} }}}
# $$
# 
# $d_{ij}$ is the distance traveled between cities labeled by $i$ and $j$. Since $d_{ij} q_{n, i} q_{n+1, j}$ adds $d_{ij}$ when both variables equal $1$, the problem is to minimize the total distance traveled. Note that the indices start at $0$ for convenience in later programmatic coding. Also, the end of $n+1$ ( $N$ ) returns to the starting point, so we will take the remainder in $N$.
# 
# However, this is not a sufficient formulation. This is because the above variable table does not take into account the constraints of "visiting all cities" and "visiting only one city at a time". As an extreme example, the combination of not moving from the first city is allowed. We thus need to impose the following constraints on all the rows and columns of the variables table.
# 
# $$
#     \sum_{i=0}^{N-1}{q_{n, i}} = 1 \quad n \in \left\{0, 1, \cdots, N - 1 \right\}
# $$
# $$
#     \sum_{n=0}^{N-1}{q_{n, i}} = 1 \quad i \in \left\{0, 1, \cdots, N - 1 \right\}
# $$
# 
# These imply the constraints that $1$ can appear only once in each row and each column of the variable table.
# 
# Summarizing the above, it turns out that we need to find the minimum value of the following polynomial:
# 
# - Objective function
# $$
# \sum_{n=0}^{N-1}{\sum_{i=0}^{N-1}{\sum_{j=0}^{N-1}{ d_{ij} q_{n, i} q_{n+1, j} }}}
# $$
# 
# - Constraints
# $$
#     \sum_{i=0}^{N-1}{q_{n, i}} = 1 \quad n \in \left\{0, 1, \cdots, N - 1 \right\}
# $$
# $$
#     \sum_{n=0}^{N-1}{q_{n, i}} = 1 \quad i \in \left\{0, 1, \cdots, N - 1 \right\}
# $$
# 
# 
# ##Creating a problem
# 
# First, we create the distances between each city, which will be the input for the Traveling Salesman Problem. Here we use `numpy` to generate the distance matrix by placing the cities at random locations on a two-dimensional plane. The following function was created to generate a random Traveling Salesman Problem by giving the number of cities.

# In[ ]:


import numpy as np


def gen_random_tsp(ncity: int):
    # Coordinate
    locations = np.random.uniform(size=(ncity, 2))

    # Distance matrix
    all_diffs = np.expand_dims(locations, axis=1) - np.expand_dims(locations, axis=0)
    distances = np.sqrt(np.sum(all_diffs**2, axis=-1))

    return locations, distances


# The second return value of the `gen_random_tsp` function, `distances`, corresponds to $\mathbf{d}$ in the above formulation.
# 
# The following will plot the coordinates of each city for $32$ cities.

# In[ ]:


import matplotlib.pyplot as plt


def show_plot(locs: np.ndarray):
    plt.figure(figsize=(7, 7))
    plt.xlabel("x")
    plt.ylabel("y")
    plt.scatter(*zip(*locations))
    plt.show()


ncity = 32
locations, distances = gen_random_tsp(ncity)


# In[ ]:


show_plot(locations)


# ## Building an input model with polynomials
# 
# Next, we create a table of variables. This will represent the order of visits and destinations in the circuit.
# 

# In[ ]:


from amplify import BinarySymbolGenerator

gen = BinarySymbolGenerator()
q = gen.array(ncity, ncity)


# The variables table is a two-dimensional array of size $N \times N$ with a binary variable for each element as follows:

# In[ ]:


q_4city = BinarySymbolGenerator().array(4, 4)
q_4city  # 4都市の場合の実行例


# We use this to create the objective function.

# In[ ]:


from amplify import einsum

cost = einsum("ij,ni,nj->", distances, q, q.roll(-1, axis=0))


# The `sum_poly` function is used as an auxiliary function for the sum operation in the objective function. Since `sum_poly(ncity, f(n))` corresponds to $\sum_{n = 0}^{N - 1}{f\left(n \right)}$, we use a lambda expression to nest and call the `sum_poly` function.

# ### Note
# 
# Using the `pair_sum` function for summing pairs of combinations, it can be written as below:
# 
# ```python
# from amplify import sum_poly, pair_sum
# 
# cost = sum_poly(
#     ncity,
#     lambda n: pair_sum(
#         ncity,
#         lambda i, j: distances[i][j] * q[n][i] * q[(n + 1) % ncity][j]
#         + distances[j][i] * q[n][j] * q[(n + 1) % ncity][i],
#     ),
# )
# ```
# 
# Next, we construct the constraints. One-hot constraints are created with the `constraint.equal_to` function. We add up all the constraints with the `sum` function.

# In[ ]:


from amplify.constraint import one_hot
from amplify import sum_poly

# 行に対する制約
row_constraints = [one_hot(q[n]) for n in range(ncity)]

# 列に対する制約
col_constraints = [one_hot(q[:, i]) for i in range(ncity)]

constraints = sum(row_constraints) + sum(col_constraints)


# Finally, the objective function and all the constraints are added together to create a logical model object.
# Here, we need to pay attention to the strength of the constraints.
# This is because the appropriate strength of the constraints depends on the objective function and needs to be sufficiently large.
# However, making the strength of the constraints as small as possible tends to improve the results output by the Ising machine.
# 
# See reference [1] for a discussion on the strength of the constraints in the traveling salesman problem. Here, we set the maximum value of the distance matrix as a large enough value. Using this value, we create a logical model object as follows:

# In[ ]:


constraints *= np.amax(distances)  # Set the strength of the constraint
model = cost + constraints


# This completes the preparation for the formulation.
# 
# [1]: [K. Takehara, D. Oku, Y. Matsuda, S. Tanaka and N. Togawa, "A Multiple Coefficients Trial Method to Solve Combinatorial Optimization Problems for Simulated-annealing-based Ising Machines," 2019 IEEE 9th International Conference on Consumer Electronics (ICCE-Berlin), Berlin, Germany, 2019, pp. 64-69, doi: 10.1109/ICCE-Berlin47944.2019.8966167.](https://ieeexplore.ieee.org/abstract/document/8966167)
# 

# ## Running the Ising machine
# 
# We create a client for the Ising machine and set the parameters. We then create the solver with the configured client.

# In[ ]:


from amplify import Solver
from amplify.client import FixstarsClient

client = FixstarsClient()
# client.token = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
client.parameters.timeout = 5000  # Timeout is 5 seconds

solver = Solver(client)


# Run the Ising machine and obtain the results as follows:

# In[ ]:


result = solver.solve(model)
if len(result) == 0:
    raise RuntimeError("Any one of constraints is not satisfied.")

energy, values = result[0].energy, result[0].values


# 
# 
# ### Note
# 
# If the length of the `result` object is `0`, it means that no solution satisfying the constraint was found. In this case, you need to change the parameters of the Ising machine or the strength of the constraints.

# ## Analysis of results
# 
# The `energy` represents the evaluation value of the objective function. In this formulation, it corresponds to the total distance traveled.

# In[ ]:


energy


# The `values` is a dictionary which provides the mapping between input variables and solution values. It is hard to evaluate it as it is, so we decode it into the same format as the variables table `q` as follows:

# In[ ]:


q_values = q.decode(values)


# ```python
# >>> q_values # Example for four cities
# [[1, 0, 0, 0],
#  [0, 0, 0, 1],
#  [0, 0, 1, 0],
#  [0, 1, 0, 0]]
# ```

# This shows that the constraint is indeed satisfied, since $1$ appears only once in each row and column. We can find the path by getting the column index where the $1$ appears, so we can use the `numpy` function to check it, as follows (converted to an array `numpy.ndarray` to use the `numpy` function).

# In[ ]:


route = np.where(np.array(q_values) == 1)[1]
print(route)


# Finally we display the route found above. It can be plotted with the following function:

# In[ ]:


def show_route(route: list, distances: np.ndarray, locations: np.ndarray):
    ncity = len(route)
    path_length = sum(
        [distances[route[i]][route[(i + 1) % ncity]] for i in range(ncity)]
    )

    x = [i[0] for i in locations]
    y = [i[1] for i in locations]
    plt.figure(figsize=(7, 7))
    plt.title(f"path length: {path_length}")
    plt.xlabel("x")
    plt.ylabel("y")

    for i in range(ncity):
        r = route[i]
        n = route[(i + 1) % ncity]
        plt.plot([x[r], x[n]], [y[r], y[n]], "b-")
    plt.plot(x, y, "ro")
    plt.show()

    return path_length


# In[ ]:


show_route(route, distances, locations)


# ## Advanced tuning
# 
# We show a few techniques for solving the Traveling Salesman Problem with Ising machines.
# 

# ### Adjusting the strength of constraints
# 
# In general, in Ising machines, the smaller the strength of the constraints, the better the solution tends to be. Qualitatively, this can be explained by the fact that the weaker the constraint term is, the more dominant the character of the cost term becomes, in the objective function to be minimized.
# 
# According to reference [1], the lower bound of the strength of the constraint is the longest distance between the cities included in the optimal path, but in general this is non-trivial because the optimal solution is not known in advance. Therefore, we need to adjust the strength of the constraint.
# 
# To find a better solution, it is useful to introduce the parameter $k \left( 0 < k \le 1 \right)$ in the above code to find a suitable lower bound.

# In[ ]:


k = 0.5
model = cost + constraints * k * np.amax(distances)


# Rather than increasing the annealing execution time, etc., it may be more efficient overall to run with multiple $k$ when compared with the same solution quality [1].
# 
# The following example shows how the solution looks when varying $k=0.3$ to $k = 1.0$ in $0.1$ increments. We can see that the smaller the value of $k$ is, the higher the quality of the solution.

# In[ ]:


client.parameters.timeout = 1000  # Timeout is 1 second
solver = Solver(client)

for i in range(10):
    k = 0.1 * (i + 1)
    model = cost + constraints * k * np.amax(distances)
    result = solver.solve(model)

    print(f"k={k}")
    if len(result) == 0:
        print(f"Any one of constraints is not satisfied.")
        continue

    energy, values = result[0].energy, result[0].values

    q_values = q.decode(values)
    route = np.where(np.array(q_values) == 1)[1]
    show_route(route, distances, locations)


# ### Note
# 
# Depending on the problem, good solutions may be found even with $k=1.0$.

# ### Reducing the objective function
# 
# The lower bound on the strength of the constraint term depends on the objective function term, whose value corresponds to the longest distance between cities in the optimal solution path. This can also be interpreted that this dependency is related to the size of the coefficient $d_{ij}$ in the objective function. If we can reduce the size of $d_{ij}$, we can further reduce the strength of the constraint term relatively to the cost terms, which may lead to a higher quality solution.
# 
# We thus modify the distances for city $i$ and city $j$ by
# 
# $$
# d_{ij}' = d_{ij} - \min_{j \ne i} d_{ij}
# $$
# 
# When we look at the city $i$, we shrink all the distances from the city $i$ by the distance between the city $i$ and its closest city. This allows us to reduce $d_{ij}$ in its entirety. The off-diagonal terms in the distance matrix are $d_{ij}'\ne d_{ji}'$, making it an asymmetric Traveling Salesman Problem.
# 
# Therefore, the objective function is changed as follows:
# 
# $$
# \sum_{n=0}^{N-1}{\sum_{i=0}^{N-1}{\sum_{j=0}^{N-1}{ d_{ij}' q_{n, i} q_{n+1, j} }}} + \sum_{i=0}^{N-1}{\min_{j \ne i} d_{ij}}
# $$
# 
# We add a constant term which compensates for the modified distances for each city. Since the path always goes through one city only once, this gives the same value as the original objective function.
# 
# The code will be modified as follows:

# In[ ]:


# Obtain a list of minimum non-zero values for each row
d_min = np.array(
    [(distances[n][distances[n].nonzero()]).min() for n in range(ncity)]
).reshape(ncity, 1)

# Modify the coefficients of the objective function and add a constant term
new_cost = einsum("ij,ni,nj->", (distances - d_min), q, q.roll(-1, axis=0)) + sum(d_min)


# Subtract the minimum value of each row and then get the maximum value of all elements
new_model = new_cost + constraints * np.amax(distances - d_min)


# The following example shows a comparison of solutions for the smallest $k$ that satisfies the constraints, with the machine parameters fixed to the same conditions. The left figure shows the results before changing the objective function, and the right figure shows the results after changing the objective function. It can be seen that the quality of the solutions has improved.

# In[ ]:


# before modifying the cost function
for i in range(10):
    k = 0.05 * (i + 1)
    model = cost + constraints * k * np.amax(distances)
    result = solver.solve(model)

    print(f"k={k}")
    if len(result) == 0:
        print(f"Some of the constraints are not satisfied.")
        continue
    else:  # stop if a feasible solution is found
        q_values = q.decode(result[0].values)
        route = np.where(np.array(q_values) == 1)[1]
        show_route(route, distances, locations)
        break


# In[ ]:


# after modifying the cost function
for i in range(10):
    k = 0.05 * (i + 1)
    new_model = new_cost + constraints * k * np.amax(distances - d_min)
    result = solver.solve(new_model)

    print(f"k={k}")
    if len(result) == 0:
        print(f"Any one of constraints is not satisfied.")
        continue
    else:  # if solution satisfying the constraints is obtained
        q_values = q.decode(result[0].values)
        route = np.where(np.array(q_values) == 1)[1]
        show_route(route, distances, locations)
        break


# ### Removing rotational symmetry
# 
# The formulation presented in this section has some redundancy in the solution space. That means that it has multiple solution states for the same path.
# 
# More specifically, it has rotational symmetry because it does not define a starting point for a path. It also has inversion symmetry for rightward and leftward paths, which we will discuss later. As a result, there are $2 N$ possible solution states for the same path. First, we will try to reduce the number of variables required by fixing the starting point to contract the problem.
# 
# To fix the starting point, we can put the appropriate values in the variables beforehand, which is the minimal change from the previous formulations.
# 
# It is possible to assign values to the variable table. For example, we can fix the first city to visit to $i = 0$. In other words, we can make substitutions for some variables in the following way:
# 
# $$
#     q_{0, 0} = 1 \\
#     q_{0, i} = 0 \quad \left( i \ne 0 \right) \\
#     q_{n, 0} = 0 \quad \left( n \ne 0 \right)
# $$
# 
# This can be done as follows:

# In[ ]:


# Creating a variable table
gen = BinarySymbolGenerator()
q = gen.array(ncity, ncity)

# Set values to elements in the variable table
q[0, 0] = 1
for i in range(1, ncity):
    q[0, i] = 0
    q[i, 0] = 0


# In[ ]:


q


# After that, there is no need to make any change and you can proceed with the construction of the objective function and constraint terms as before.
# 
# This allowed us to reduce the $N^2$ variable problem to a $\left( N - 1 \right)^2$ variable.
# By reducing the number of variables, we can expect some improvement in the quality of the solution.

# ### Removing inversion symmetry
# 
# The inversion symmetry can be removed by adding new constraints. The addition of constraints does not necessarily lead to an improvement in the quality of the solution because it leads to an increase in the complexity of the problem. It is mentioned here for reference.
# 
# Suppose we fix the starting point to $i = 0$ and obtain the path `[0 2 4 3 6 5 1 7]`. In the current formulation, its inversion `[0 7 1 5 6 3 4 2]` is also the same solution. To break this symmetry, we focus on the indices of the next and previous cities of the starting point. In the former solution, $i = 2 \left(n=1 \right) < 7 \left(n=7 \right)$, but in the latter, the inequality is inverted to $i = 7 \left(n=1 \right) > 2 \left(n=7 \right)$.
# 
# If we fix this inequality, we can break the inversion symmetry. To make the former so that $n = 1, N - 1$ is in ascending order, add the following constraint:
# 
# **Constraints (additional)**
# 
# $$
# q_{N-1,i} q_{1,j} = 0 \quad \left( i < j \right)
# $$
# 
# This expression prohibits $q_{N-1,i}, q_{1,j}$ from both being $1$ for $i < j$. For such constraints with the minimum value of 0, we can use the `constraint.penalty` function and write as below:

# In[ ]:


from amplify.constraint import penalty

# constraints on ordering
pem_constraint = [
    penalty(q[ncity - 1, i] * q[1, j])
    for i in range(ncity)
    for j in range(i + 1, ncity)
]

# for row
row_constraints = [one_hot(q[n]) for n in range(ncity)]

# for column
col_constraints = [one_hot(q[:, i]) for i in range(ncity)]

constraints = sum(row_constraints) + sum(col_constraints) + sum(pem_constraint)


# ### Note
# 
# For constraints with the minimum value of 0, it is equivalent to sum all the conditions first and then create a single constraint object. In this case, the `pair_sum` function can be used to write the following:
# 
# ```python
# from amplify import pair_sum
# 
# # Constraints on ordering
# pem_constraint = penalty(pair_sum(ncity, lambda i, j: q[ncity - 1][i] * q[1][j]))
# 
# constraints = sum(row_constraints) + sum(col_constraints) + pem_constraint
# ```
# 
# The `pair_sum` function sums for $i < j$, eliminating the need for `for` loops.
# 
# As with the constraints on rows and columns, we also sum the ordinal constraints and finally add up all the constraints. After that, we can get the solution as before, and check that the path index is in ascending order with $n = 1, N - 1$.
# 

# In[ ]:


k = 1.0


# Get a list of non-zero minimum values for each row
d_min = np.array(
    [(distances[n][distances[n].nonzero()]).min() for n in range(ncity)]
).reshape(ncity, 1)

# Modify the coefficients of the cost function and add a constant term
cost = einsum("ij,ni,nj->", (distances - d_min), q, q.roll(-1, axis=0)) + sum(d_min)

model = cost + constraints * k * np.amax(distances - d_min)
result = solver.solve(model)

q_values = q.decode(result[0].values)
route = np.where(np.array(q_values) == 1)[1]
print(route)
show_route(route, distances, locations)

