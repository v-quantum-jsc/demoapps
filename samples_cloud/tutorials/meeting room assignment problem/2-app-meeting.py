#!/usr/bin/env python
# coding: utf-8

# # Meeting Room Assignment Problem
# 
# The meeting room assignment problem is a problem of assigning meeting rooms so that as many meetings as possible can be held, given multiple meeting schedules and multiple meeting rooms. In this task, we construct a QUBO model for this problem and try to solve the problem using an annealing machine.
# 
# First, assume that the start and end times of each meeting are given as data. Here, the time is given as a string in the format `"10:40"`. In addition, we will have a dictionary of meeting schedule information with the meeting name as the key and the list of start and end times of the meeting as the value. We will also define the number of meetings and the number of available meeting rooms.

# In[ ]:


# Meeting schedule
schedules = {
    "meeting1": ["10:00", "13:00"],
    "meeting2": ["10:00", "12:00"],
    "meeting3": ["10:00", "11:00"],
    "meeting4": ["11:00", "13:00"],
    "meeting5": ["11:00", "12:00"],
    "meeting6": ["11:00", "15:00"],
    "meeting7": ["12:00", "16:00"],
    "meeting8": ["12:00", "15:00"],
    "meeting9": ["13:00", "15:00"],
    "meeting10": ["13:00", "14:00"],
    "meeting11": ["14:00", "17:00"],
    "meeting12": ["15:00", "19:00"],
    "meeting13": ["15:00", "17:00"],
    "meeting14": ["15:00", "16:00"],
    "meeting15": ["16:00", "18:00"],
    "meeting16": ["16:00", "18:00"],
    "meeting17": ["17:00", "19:00"],
    "meeting18": ["17:00", "18:00"],
    "meeting19": ["18:00", "19:00"],
}

# Number of meetings
Nm = len(schedules)

# Number of meeting rooms
Nr = 8


# Next, we prepare a function `time2num` to return the given time as a number to compare the meeting times, and a function `check_overlap` to check if the schedules of given two meetings overlap.

# In[ ]:


# Convert time to numeric time units
def time2num(time: str):
    h, m = map(float, time.split(":"))
    return h + m / 60


# Check if there is any overlap between the two meeting times
def check_overlap(time_slot1, time_slot2):
    start1, end1 = map(time2num, time_slot1)
    start2, end2 = map(time2num, time_slot2)

    return start1 < end2 and start2 < end1


# Now we are ready to quantify the information from the given meetings. The next step is to figure out how to represent this problem as a combinatorial optimization problem.
# 
# As the first step, we consider how to express variables to indicate in which meeting room each meeting will be held. However, binary variables such as QUBO variables and Ising variables cannot have an arbitrary number of states. So, we assign decision variables as many as the number of meeting rooms to each meeting.
# 
# For example, let $q_{i, r}$ be the variable that represents that the meeting $i$ will be held in the meeting room $r$. We can think of it as assigning the meeting $i$ to the meeting room $r$ if $q_{i, r} = 1$, and not assigning it if $q_{i, r} = 0$.
# 
# 
# |Meeting \ Meeting room| $0$ | $1$ | ... | $N_r-1$|  
# |:---:|:---:|:---:|:---:|:---:|
# |$0$| $q_{0,0}$ | $q_{0,1}$ | ... | $q_{0,N_r-1}$|
# |$1$| $q_{1,0}$ | $q_{1,1}$ | ... | $q_{1,N_r-1}$|
# |$\vdots$| $\vdots$ | $\vdots$ | ... | $\vdots$|
# |$N_m -1$| $q_{N_m-1,0}$ | $q_{N_m-1,1}$ | ... | $q_{N_m-1,N_r-1}$|
# 
# Next, consider the restriction that multiple meetings cannot be assigned to the same meeting room on top of each other.
# 
# We construct a list of meetings with overlapped schedules. For example, if there is a schedule overlap between meetings $i$ and $j$, we construct a tuple $(i, j)$ and store it in this list. "The problem of assigning each meeting to a meeting room so that there is no schedule overlap" becomes "the problem of arranging meetings so that if two meetings $(i, j)$ are included in the above list, they are not assigned to the same meeting room".
# 
# In the following, we use the `check_overlap` function defined above to check for overlapped meeting schedules, and based on that, add two meetings $(i, j)$ that have overlapped schedules to the `overlaps` list.

# In[ ]:


import itertools

# Obtain a list of meeting names
mtg_names = list(schedules.keys())

# Create a dictionary of meeting room names and indexes
mtg_name2idx = {mtg_names[i]: i for i in range(Nm)}

# Store the index of meetings with overlapped schedules as a tuple
overlaps = []
for mtg1, mtg2 in itertools.combinations(mtg_names, 2):
    if check_overlap(schedules[mtg1], schedules[mtg2]):
        overlaps.append(tuple(sorted([mtg_name2idx[mtg1], mtg_name2idx[mtg2]])))


# Next, we define `Nm` × `Nr` QUBO variables, where `Nr` meeting rooms are associated with each of the `Nm` meetings. Let $q_{i, r}$ be the variable corresponding to the index $i$ of the meeting and $r$ of the meeting room.

# In[ ]:


from amplify import gen_symbols, BinaryPoly

# Define the decision variable in the form of an array of (Nm x Nr)
q = gen_symbols(BinaryPoly, Nm, Nr)


# We create constraints using QUBO variables.
# 
# First, since a meeting must be assigned to a single meeting room, we impose the following one-hot constraint:
# 
# $
# \displaystyle\sum_{r=0}^{\text{Nr} - 1}q_{i, r} = 1
# $
# 
# 

# In[ ]:


from amplify import sum_poly
from amplify.constraint import equal_to

# One-hot constraint to assign one meeting room for one meeting
# It can be written using the equal_to function and the sum_poly function
room_constraints = sum(
    [equal_to(sum_poly(Nr, lambda r: q[i][r]), 1) for i in range(Nm)]
)


# In addition, we need to give the constraints such that if the indices $(i, j)$ of two meetings are included in the overlap list `overlaps` of the meeting schedule defined earlier, they cannot be assigned the same meeting room.
# 
# These constraints are that if $(i, j)\in \text{overlaps}$, then $q_{i, r}$ and $q_{j, r}$ will not be $1$ at the same time, which leads to the following constraint:
# 
# $
# q_{i, r} q_{j, r} = 0 \qquad \text{for}\quad (i, j) \in \text{overlaps}\quad{and}\quad  r \in \{0, \cdots, N_r - 1\}
# $
# 
# 

# In[ ]:


from amplify import sum_poly
from amplify.constraint import penalty

# Impose the constraint that q[i][r] * q[j][r] = 0 for all (i, j) in overlaps
overlap_constraints = sum(
    [penalty(q[i][r] * q[j][r]) for (i, j) in overlaps for r in range(Nr)]
)


# The two constraint objects `room_constraints` and `overlap_constraints` generated above are combined into a logical model to be solved in the end. 

# In[ ]:


model = room_constraints + overlap_constraints


# Next, we set up the client and solve the model we have defined.

# In[ ]:


from amplify import Solver
from amplify.client import FixstarsClient

# Set up the client
client = FixstarsClient()
# client.token = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # If you are using it in a local environment, please enter the access token for Amplify AE
client.parameters.timeout = 1000  # Timeout is 1 second

# Set up a solver
solver = Solver(client)
# solve a problem
result = solver.solve(model)

# If result is empty, it means that no solution satisfying the constraints was obtained.
if len(result) == 0:
    raise RuntimeError("Given constraint conditions are not satisfied")


# From the variable whose value is $1$ in the obtained solution, we can read which meeting room each meeting was assigned to.

# In[ ]:


from amplify import decode_solution
import numpy as np

# Assign the obtained solution to the original variable
values = result[0].values
solution = np.array(decode_solution(q, values))

# Read which meeting room each meeting will be assigned to
room_assignment = list(zip(*np.where(solution == 1)))


# Finally, we visualize the results.

# In[ ]:


#
# Visualize meeting room assignments
#
get_ipython().run_line_magic('matplotlib', 'inline')


def plot_mtg_schedule(num_rooms, room_assignment):
    import matplotlib.pyplot as plt

    room_names = ["Room " + chr(65 + i) for i in range(num_rooms)]

    cmap = plt.get_cmap("coolwarm", num_rooms)
    colors = [cmap(i) for i in range(num_rooms)]

    fig, ax1 = plt.subplots(nrows=1, ncols=1, figsize=(15, 10))
    for mtg_idx, room in room_assignment:
        mtg_name = mtg_names[mtg_idx]
        start = time2num(schedules[mtg_name][0])
        end = time2num(schedules[mtg_name][1])

        plt.fill_between(
            [room + 0.55, room + 1.45],
            [start, start],
            [end, end],
            edgecolor="black",
            linewidth=3.0,
            facecolor=colors[room],
        )
        plt.text(
            room + 0.6, start + 0.1, f"{schedules[mtg_name][0]}", va="top", fontsize=10
        )
        plt.text(
            room + 1.0,
            (start + end) * 0.5,
            mtg_name,
            ha="center",
            va="center",
            fontsize=15,
        )

    # Set First Axis
    ax1.yaxis.grid()
    ax1.set_xlim(0.5, len(room_names) + 0.5)
    ax1.set_ylim(19.1, 7.9)
    ax1.set_xticks(range(1, len(room_names) + 1))
    ax1.set_xticklabels(room_names)
    ax1.set_ylabel("Time")

    # Set Second Axis
    ax2 = ax1.twiny().twinx()
    ax2.set_xlim(ax1.get_xlim())
    ax2.set_ylim(ax1.get_ylim())
    ax2.set_xticks(ax1.get_xticks())
    ax2.set_xticklabels(room_names)
    ax2.set_ylabel("Time")

    plt.show()


# In[ ]:


plot_mtg_schedule(num_rooms=Nr, room_assignment=room_assignment)


# ## Assigning Some Meetings Manually
# With Amplify, you can fix the value of a variable with a constant value. This feature can be used to manually assign meeting rooms.
# 
# For example, if you want to fix the value of the binary variable `q[i][j]` to 1, set `q[i][j] = BinaryPoly(1)`. The right-hand side `BinaryPoly(1)` represents the constant 1 of BinaryPoly type.
# 
# In this section, we consider solving the remaining meeting room assignment as an optimization problem after fixing the following in advance:
# 
# * meeting1 -> Room B
# * meeting2 -> Room A
# * meeting6 -> Room C
# * meeting10 -> Room A
# * meeting12 -> Room C
# * meeting17 -> Room A
# 
# 

# In[ ]:


from amplify import gen_symbols, BinaryPoly
from amplify import sum_poly
from amplify.constraint import equal_to
from amplify.constraint import penalty

"""
Name of the meeting room and corresponding index
Room A -> 0, Room B -> 1, Room C -> 2, ...
"""

pre_assign = {
    "meeting1": 1,
    "meeting2": 0,
    "meeting6": 2,
    "meeting10": 0,
    "meeting12": 1,
    "meeting17": 0,
}


Nm = len(schedules)  # Number of meetings
Nr = 6  # umber of meeting rooms

q = gen_symbols(BinaryPoly, Nm, Nr)

# Assign a constant to the combination of a meeting and a meeting room that has been assigned in advance.
for mtg_name, room in pre_assign.items():
    mtg_idx = mtg_name2idx[mtg_name]
    for r in range(Nr):
        q[mtg_idx][r] = BinaryPoly(1) if r == room else BinaryPoly(0)

# One-hot constraint to assign one meeting room for one meeting
room_constraints = sum(
    [equal_to(sum_poly(Nr, lambda r: q[i][r]), 1) for i in range(Nm)]
)

# mpose the constraint that q[i][r] * q[j][r] = 0 for all (i, j) in overlaps
overlap_constraints = sum(
    [sum([penalty(q[i][r] * q[j][r]) for (i, j) in overlaps]) for r in range(Nr)]
)

model = room_constraints + overlap_constraints

from amplify import Solver
from amplify.client import FixstarsClient

# Set up the client
client = FixstarsClient()
client.parameters.timeout = 1000  # Timeout is 1 second
# client.token = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # If you are using it in a local environment, please enter the access token for Amplify AE


solver = Solver(client)  # Set up a solver
result = solver.solve(model)  # Solve a problem

# If result is empty, the constraint condition is not satisfied and the solution cannot be found.
if len(result) == 0:
    raise RuntimeError("Given constraint conditions are not satisfied")


from amplify import decode_solution
import numpy as np

# Assign the obtained solution to the original variable
values = result[0].values
solution = np.array(decode_solution(q, values))

# Read which meeting room each meeting will be assigned to
room_assignment = list(zip(*np.where(solution == 1)))

plot_mtg_schedule(num_rooms=Nr, room_assignment=room_assignment)

