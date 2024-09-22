#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from ipywidgets import (
    IntsInput,
    Button,
    Label,
    IntSlider,
    Dropdown,
    Accordion,
    interactive,
    VBox,
    HBox,
    Box,
    Layout,
    Output,
)

get_ipython().run_line_magic('matplotlib', 'inline')


# # Picross Solver
# 
# Picross is a puzzle where the purpose is to complete a picture by filling a grid of squares either in black or white, based on the clues given as numbers to the left of each row and above each column.
# 
# In the following demo, the Picross puzzle is solved with the Amplify Annealing Engine using the QUBO formulation.  
# Clicking the "Run" button will display the output solution.

# In[ ]:


import numpy as np


class PicrossData:
    def __init__(self, v_hints, h_hints, name="unnamed_picross"):
        self.v_hints = v_hints
        self.h_hints = h_hints
        self.name = name
        self.pattern = np.zeros((len(h_hints), len(v_hints)))

    def __str__(self):
        return self.name + f" ({len(self.h_hints)}x{len(self.v_hints)})"


preset_list = []

v_hints = [[5], [1], [5], [1], [5]]
h_hints = [[3, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 3]]
data = PicrossData(v_hints, h_hints, "S")
preset_list.append(data)

v_hints = [[2], [2], [4], [10], [8], [6], [6], [6], [1, 1], [1, 1]]
h_hints = [[1], [2, 1], [6], [6], [8], [8], [6], [6], [2, 1], [1]]
data = PicrossData(v_hints, h_hints, "Star")
preset_list.append(data)

v_hints = [
    [15],
    [1, 1],
    [1, 11, 1],
    [1, 1, 1, 1],
    [1, 1, 7, 1, 1],
    [1, 1, 1, 1, 1, 1],
    [1, 1, 1, 3, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1],
    [1, 1, 5, 1, 1, 1],
    [1, 1, 1, 1, 1],
    [1, 9, 1, 1],
    [1, 1, 1],
    [13, 1],
    [1],
]
h_hints = [
    [14],
    [1, 1],
    [1, 10, 1],
    [1, 1, 1, 1],
    [1, 1, 6, 1, 1],
    [1, 1, 1, 1, 1, 1],
    [1, 1, 1, 2, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 4, 1, 1],
    [1, 1, 1, 1, 1],
    [1, 1, 8, 1],
    [1, 1, 1],
    [1, 12],
    [1],
    [15],
]
data = PicrossData(v_hints, h_hints, "Spiral")
preset_list.append(data)

v_hints = [
    [],
    [5],
    [1, 1],
    [5, 1],
    [1, 1, 1],
    [1, 1, 5],
    [1, 2, 1],
    [9, 1],
    [1, 1, 1, 1],
    [5, 1, 1, 1],
    [1, 1, 1, 2],
    [1, 1, 5],
    [1, 2],
    [5],
    [],
]
h_hints = [
    [],
    [5],
    [2, 1],
    [5, 1, 1],
    [2, 1, 1, 1],
    [1, 1, 1, 5],
    [1, 1, 1, 1],
    [1, 9],
    [1, 2, 1],
    [5, 1, 1],
    [1, 1, 1],
    [1, 5],
    [1, 1],
    [5],
    [],
]
data = PicrossData(v_hints, h_hints, "Blocks")
preset_list.append(data)

v_hints = [
    [2, 4, 4],
    [4, 3, 3],
    [6, 2, 2],
    [8, 1, 1],
    [4, 4, 2],
    [3, 3, 4],
    [2, 2, 6],
    [1, 1, 8],
    [2, 4, 4],
    [4, 3, 3],
    [6, 2, 2],
    [8, 1, 1],
    [4, 4, 2],
    [3, 3, 4],
    [2, 2, 6],
    [1, 1, 8],
    [2, 4, 4],
    [4, 3, 3],
    [6, 2, 2],
    [8, 1, 1],
]
h_hints = [
    [4, 4],
    [4, 4, 1],
    [4, 4, 2],
    [4, 4, 3],
    [4, 4, 4],
    [4, 4, 4],
    [4, 4, 3],
    [4, 4, 2],
    [4, 4, 1],
    [4, 4],
    [4, 4, 4],
    [3, 4, 4],
    [2, 4, 4],
    [1, 4, 4],
    [4, 4],
    [4, 4],
    [1, 4, 4],
    [2, 4, 4],
    [3, 4, 4],
    [4, 4, 4],
]
data = PicrossData(v_hints, h_hints, "Arrow")
preset_list.append(data)


# In[ ]:


from amplify import BinarySymbolGenerator, BinaryPoly, BinaryQuadraticModel, Solver

from amplify.constraint import equal_to, clamp
from amplify.client import FixstarsClient


# Based on q_hints, substitute for q_for_states and q_for_squares
# to reduce the number of variables to be handled.
def substitute_q(q_for_cells, q_for_states, q_hints):
    for q, hint in zip(q_for_states, q_hints):
        # Substitute for unreachable points
        for i in range(q.shape[0]):
            q[i, i + 2 :] = 0
            q[-i - 1, : -i - 2] = 0

        # Substitution when the destination is fixed
        white_pos_list = [0]
        for h in hint:
            white_pos_list.append(white_pos_list[-1] + h + 1)
        for i in range(1, q.shape[0]):
            for j in range(1, q.shape[1]):
                if j in white_pos_list:
                    if q[i - 1, j] == 0:
                        q[i, j] = q[i - 1, j - 1]
                elif j - 1 in white_pos_list:
                    if q[i, j - 1] == 0:
                        q[i, j] = q[i - 1, j - 1]
                else:
                    q[i, j] = q[i - 1, j - 1]

    # construct q_for_cells
    for y in range(q_for_cells.shape[0]):
        for x in range(q_for_cells.shape[1]):
            white_pos = 0
            q_for_cells[y, x] = q_for_states[y][x, 0]
            for hint in q_hints[y]:
                white_pos += hint + 1
                q_for_cells[y, x] += q_for_states[y][x, white_pos]
            q_for_cells[y, x] = 1 - q_for_cells[y, x]


def make_constraints(q_for_states, q_hints, label=""):
    if label != "":
        label = f"{label}: "

    state_constraints = [equal_to(BinaryPoly(1), 1)]
    white_constraints = [equal_to(BinaryPoly(1), 1)]
    last_black_constraints = [equal_to(BinaryPoly(1), 1)]
    for i in range(len(q_for_states)):
        q, hint = q_for_states[i], q_hints[i]

        # Constraint 1: Each cell must be set black or white
        for j in range(q.shape[0]):
            c = sum(q[j, :])
            if c.is_number():
                continue
            state_constraints.append(
                equal_to(
                    c, 1, label=f"{label}Cell({i}, {j}) must be set black or white"
                )
            )

        white_pos = [0]
        for h in hint:
            white_pos.append(white_pos[-1] + h + 1)

        # Constraint 2: The next cell after white cell must be white or head of black block
        for j in range(q.shape[0] - 1):
            for k in white_pos:
                if k == q.shape[1] - 1:
                    c = -q[j, k] + q[j + 1, k]
                else:
                    c = -q[j, k] + q[j + 1, k] + 2 * q[j + 1, k + 1]
                if c.is_number():
                    continue
                white_constraints.append(
                    clamp(
                        c,
                        0,
                        1,
                        label=f"{label}The next cell after white cell({i}, {j}), state {k} must be white or head of black block",
                    )
                )

        # Constraint 3: The previous cell before white cell must be white or bottom of black block
        for j in range(q.shape[0] - 1):
            for k in white_pos:
                if k == 0:
                    c = -q[j + 1, k] + q[j, k]
                else:
                    c = -q[j + 1, k] + q[j, k] + 2 * q[j, k - 1]
                if c.is_number():
                    continue
                last_black_constraints.append(
                    clamp(
                        c,
                        0,
                        1,
                        label=f"{label}The previous cell before white cell({i}, {j}), state {k} must be white or bottom of black block",
                    )
                )

    constraints = (
        sum(state_constraints) + sum(white_constraints) + sum(last_black_constraints)
    )
    return constraints


def solve(v_hints, h_hints, timeout=2000):
    v_len, h_len = len(v_hints), len(h_hints)
    gen = BinarySymbolGenerator()

    q_for_cells_from_v_hints = gen.array(v_len, h_len)
    q_for_cells_from_h_hints = gen.array(h_len, v_len)

    # Create a variable for each row and column hint
    # Two-dimensional array of (cells, states)
    q_for_states_from_v_hints = [
        gen.array(h_len, sum(hint) + len(hint) + 1) for hint in v_hints
    ]
    q_for_states_from_h_hints = [
        gen.array(v_len, sum(hint) + len(hint) + 1) for hint in h_hints
    ]

    substitute_q(q_for_cells_from_v_hints, q_for_states_from_v_hints, v_hints)
    substitute_q(q_for_cells_from_h_hints, q_for_states_from_h_hints, h_hints)

    # Stores pairs of variables and polynomials to be assigned to substitute_dicts
    substitute_dicts = dict()
    for x in range(h_len):
        for y in range(v_len):
            c_dict = (
                q_for_cells_from_v_hints[y, x] - q_for_cells_from_h_hints[x, y]
            ).asdict()
            for k, v in c_dict.items():
                if len(k) == 0:
                    continue
                # Store in substitute_dicts
                # Substitute if the polynomial on the right-hand side satisfies 0 <= d <= 1
                d = dict()
                d_max, d_min = 0, 0
                for k2, v2 in c_dict.items():
                    if k == k2:
                        continue
                    d[k2] = v2 / v * (-1)
                    if len(k2) == 0:
                        d_max += d[k2]
                        d_min += d[k2]
                    elif d[k2] > 0:
                        d_max += d[k2]
                    else:
                        d_min += d[k2]
                if d_min < 0 or d_max > 1:
                    continue
                substitute_dicts[k] = d

                # Match q_for_cells_from_v_hints and q_for_cells_from_h_hints
                if k in q_for_cells_from_v_hints[y, x].asdict():
                    q_for_cells_from_v_hints[y, x] = q_for_cells_from_h_hints[x, y]
                else:
                    q_for_cells_from_h_hints[x, y] = q_for_cells_from_v_hints[y, x]
                break

    # q_for_states_from_v_hints to reflect the contents of substitute_dicts
    for qv in q_for_states_from_v_hints:
        for j in range(qv.shape[0]):
            for k in range(qv.shape[1]):
                d = qv[j, k].asdict()
                if len(d) == 0:
                    continue
                key, value = d.popitem()
                if key in substitute_dicts:
                    qv[j, k] = BinaryPoly(substitute_dicts[key])

    # q_for_states_from_h_h_hints to reflect the contents of substitute_dicts
    for qh in q_for_states_from_h_hints:
        for j in range(qh.shape[0]):
            for k in range(qh.shape[1]):
                d = qh[j, k].asdict()
                if len(d) == 0:
                    continue
                key, value = d.popitem()
                if key in substitute_dicts:
                    qh[j, k] = BinaryPoly(substitute_dicts[key])

    v_constraints = make_constraints(
        q_for_states_from_v_hints, v_hints, label="vertical"
    )
    h_constraints = make_constraints(
        q_for_states_from_h_hints, h_hints, label="horizontal"
    )

    # The cell determined from vertical hints must be matched to one from horizontal hints
    eq_constraints = [equal_to(BinaryPoly(1), 1)]
    for y in range(v_len):
        for x in range(h_len):
            c = q_for_cells_from_v_hints[y, x] - q_for_cells_from_h_hints[x, y]
            if c.is_number():
                continue
            eq_constraints.append(
                equal_to(
                    c,
                    0,
                    label=f"The cell({x}, {y}) determined from vertical hints must be matched to one from horizontal hints",
                )
            )
    eq_constraints = sum(eq_constraints)

    constraints = v_constraints + h_constraints + eq_constraints * 2

    client = FixstarsClient()
    client.parameters.timeout = timeout

    solver = Solver(client)

    model = BinaryQuadraticModel(constraints)
    result = solver.solve(model)

    if len(result.solutions) == 0:
        return -1

    values = result.solutions[0].values
    solution = q_for_cells_from_v_hints.decode(values)

    return solution


if __name__ == "__main__":
    v_hints = [
        [1],
        [6],
        [3, 2],
        [1, 1, 1],
        [1, 2, 2],
        [1, 1, 2],
        [1, 2, 1],
        [1, 1, 2],
        [2, 1, 2, 1],
        [2, 2, 1, 1, 2],
        [2, 1, 2, 1],
        [2, 1, 1, 1],
        [3, 2, 3, 2],
        [3, 2, 5],
        [3, 2],
    ]
    h_hints = [
        [2, 4],
        [2, 4],
        [3],
        [2],
        [2, 2],
        [2],
        [],
        [],
        [11],
        [2, 2],
        [4, 3, 4],
        [1, 3, 3, 1],
        [1, 1],
        [5, 3, 3],
        [3, 4, 4, 1],
    ]


# In[ ]:


import matplotlib.pyplot as plt


def visualize(v_hints, h_hints, solution=np.zeros((0, 0))):
    if solution.shape[0] == len(v_hints) and solution.shape[1] == len(h_hints):
        solution = solution
    else:
        solution = np.zeros((len(h_hints), len(v_hints)))

    fig, ax = plt.subplots()
    ax.tick_params(
        which="both",
        top=True,
        bottom=False,
        labeltop=True,
        labelbottom=False,
        length=0,
    )
    ax.tick_params(axis="x")

    ax.imshow(solution, cmap="Greys", aspect="equal")
    # Major ticks
    ax.set_xticks(np.arange(len(h_hints)))
    ax.set_yticks(np.arange(len(v_hints)))
    # Minor ticks
    ax.set_xticks(np.arange(-0.5, len(h_hints), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(v_hints), 1), minor=True)

    # Labels for major ticks
    ax.set_xticklabels(["\n".join(map(str, hint)) for hint in h_hints])
    ax.set_yticklabels(["  ".join(map(str, hint)) for hint in v_hints])

    ax.set_xlim([-0.5, len(h_hints) - 0.5])
    ax.set_ylim([len(v_hints) - 0.5, -0.5])

    ax.set_title(f"{len(h_hints)} x {len(v_hints)}")
    # Gridlines based on minor ticks
    ax.grid(which="minor", color="#aaaaaa", linestyle="-", linewidth=1)

    return plt.show()


# In[ ]:


MAX_ROWS = 20
INIT_WIDTH, INIT_HEIGHT = 5, 5

picross_vertical_hints = [IntsInput(min=1, max=MAX_ROWS) for _ in range(MAX_ROWS)]
picross_horizontal_hints = [IntsInput(min=1, max=MAX_ROWS) for _ in range(MAX_ROWS)]

vertical_hints_slider = IntSlider(
    min=1, max=MAX_ROWS, value=INIT_HEIGHT, description="Size"
)
horizontal_hints_slider = IntSlider(
    min=1, max=MAX_ROWS, value=INIT_WIDTH, description="Size"
)

picross_vertical_hints_labeled = [
    VBox(
        [Label(value=str(i + 1)), hint],
        layout=Layout(border="1px solid black", width="100%"),
    )
    for i, hint in enumerate(picross_vertical_hints)
]
picross_horizontal_hints_labeled = [
    VBox(
        [Label(value=str(i + 1)), hint],
        layout=Layout(border="1px solid black", width="100%"),
    )
    for i, hint in enumerate(picross_horizontal_hints)
]


def interact_hints(height, width):
    for i in range(MAX_ROWS):
        hint = picross_horizontal_hints[i]
        space = picross_horizontal_hints_labeled[i]
        if i >= width:
            if space.layout.width != "0px":
                space.layout = Layout(width="0px")
                hint.value = []
        else:
            if space.layout.width == "0px":
                space.layout = Layout(border="1px solid black", width="100%")

    for i in range(MAX_ROWS):
        hint = picross_vertical_hints[i]
        space = picross_vertical_hints_labeled[i]
        if i >= height:
            if space.layout.width != "0px":
                space.layout = Layout(width="0px")
                hint.value = []
        else:
            if space.layout.width == "0px":
                space.layout = Layout(border="1px solid black", width="100%")


# In[ ]:


option_dict = {str(preset): preset for preset in preset_list}

timeout_slider = IntSlider(
    description="Timeout (ms)", value=1000, min=1000, max=60000, step=1000
)
preset_select = Dropdown(description="Preset", options=option_dict)

timeout_slider.style.description_width = "initial"
preset_select.style.description_width = "initial"


# In[ ]:


picross_problem_out = Output(layout=Layout(width="50%"))
picross_result_out = Output(layout=Layout(width="50%"))
picross_vertical_hints_out = VBox(
    [
        HBox([Label(value="Hints for the row"), vertical_hints_slider]),
        Box(picross_vertical_hints_labeled),
    ],
    layout=Layout(border="2px solid black"),
)
picross_horizontal_hints_out = VBox(
    [
        HBox([Label(value="Hints for the column"), horizontal_hints_slider]),
        Box(picross_horizontal_hints_labeled),
    ],
    layout=Layout(border="2px solid black"),
)

picross_apply_btn = Button(description="Apply Hints", button_style="")

accordion = Accordion(
    children=[
        VBox([timeout_slider, preset_select]),
        VBox(
            [
                picross_vertical_hints_out,
                picross_horizontal_hints_out,
                picross_apply_btn,
            ]
        ),
    ],
    titles=["Options", "Hints"],
)

picross_run_btn = Button(
    description="Run", button_style="", tooltip="Run", icon="check"
)


# In[ ]:


def show_picross_problem(btn=None):
    with picross_problem_out:
        picross_problem_out.clear_output()

        picross_height = vertical_hints_slider.value
        picross_width = horizontal_hints_slider.value

        v_hints = [hint.value for hint in picross_vertical_hints[:picross_height]]
        h_hints = [hint.value for hint in picross_horizontal_hints[:picross_width]]
        visualize(v_hints, h_hints)


def show_picross_result(btn=None):
    with picross_result_out:
        picross_result_out.clear_output()

        picross_height = vertical_hints_slider.value
        picross_width = horizontal_hints_slider.value

        v_hints = [hint.value for hint in picross_vertical_hints[:picross_height]]
        h_hints = [hint.value for hint in picross_horizontal_hints[:picross_width]]
        result = solve(v_hints, h_hints, timeout_slider.value)

        if type(result) is int:
            print("No solution was found due to one of following reasons:")
            print(
                f"(1) The timeout, {timeout_slider.value} ms, is too short for the given setting."
            )
            print("(2) The given hints are either insufficient or inconsistent.")
        else:
            visualize(v_hints, h_hints, result)


def interact_preset(key):
    v_hints, h_hints = key.v_hints, key.h_hints
    vertical_hints_slider.value = len(v_hints)
    horizontal_hints_slider.value = len(h_hints)
    for i, hint in enumerate(v_hints):
        picross_vertical_hints[i].value = hint
    for i, hint in enumerate(h_hints):
        picross_horizontal_hints[i].value = hint

    show_picross_problem()


interactive(interact_hints, height=vertical_hints_slider, width=horizontal_hints_slider)
interactive(interact_preset, key=preset_select)

picross_apply_btn.on_click(show_picross_problem)
picross_run_btn.on_click(show_picross_result)
display(accordion, picross_run_btn, HBox([picross_problem_out, picross_result_out]))
show_picross_problem()

