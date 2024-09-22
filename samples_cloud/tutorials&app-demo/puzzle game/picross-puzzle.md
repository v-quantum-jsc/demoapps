# Solving Picross using quantum annealing and Ising machines

This sample code explains how to solve Picross $^{*1}$, a puzzle game, using quantum annealing and Ising machines, and implements it using Amplify. This notebook consists of the following sections:

- 1\. [Rules and solution outline](#1)
  - 1.1\. [Rules](#1_1)
  - 1.2\. [Solution outline](#1_2)
  - 1.3\. [Terms and pattern expressions](#1_3)
    - 1.3.1\. [First-black, Last-Black](#1_3_1)
    - 1.3.2\. [State of the squares](#1_3_2)
    - 1.3.3\. [Matrix representation of coloring](#1_3_3)
- 2\. [Formulating the Picross solution](#2)
  - 2.1\. [Initial value constraints](#2_1)
  - 2.2\. [Transition constraints](#2_2)
  - 2.3\. [Matching Constraints](#2_3)
  - 2.4\. [Constraints linking color and state](#2_4)
- 3\. [Implementing Picross solution](#3)
  - 3.1\. [Picross matrix plotting function](#3_1)
  - 3.2\. [Implementation of constraint equations](#3_2)
    - 3.2.1\. [Decision variables](#3_2_1)
    - 3.2.2\. [Implementation - initial value constraints](#3_2_2)
    - 3.2.3\. [Implementation - transition constraints](#3_2_3)
    - 3.2.4\. [Implementation - matching constraints](#3_2_4)
    - 3.2.5\. [Implementation - Constraints linking color and state](#3_2_5)
  - 3.3\. [Amplify client configuration](#3_3)
  - 3.4\. [Running the Picross solver](#3_4)
- Advanced: [Tuning](#4)

*1: Picross is a registered trademark of Nintendo Co., Ltd.

<a id="1"></a>
## 1\. Rules and solution outline

<a id="1_1"></a>
### 1.1\. Rules

Picross is a puzzle where the purpose is to complete a picture by filling a grid of squares either in black or white, based on the clues given as numbers to the left of each row and above each column.

For example, if the clue says `5`, it means that five consecutive squares in that row or column must be filled in black; if the clue says more than one number, such as `1 1 1`, it means that a total of three squares must be filled in black with one or more white spaces in between. Also, `1 3` indicates that one square and three consecutive squares are to be filled in black with one or more blank spaces in between. Note that the order of numbers in each clue is important, and `1 3` and `3 1` suggest different patterns one another.

Below is an example of a completed Picross according to the clues.

![5x5_solution](../figures/picross-puzzle/5x5_solution.png)


<a id="1_2"></a>
### 1.2\. Solution outline

A Picross is complete when the entire domain, consisting of a grid of squares, is filled in either black or white so that both the top and left clues are satisfied at the same time.

If a given Picross is completed so that only the left clue is satisfied, there is no one fixed way to color it. For example, the following different patterns are possible

![5x5_solution_left_1](../figures/picross-puzzle/5x5_solution_left_1.png)
![5x5_solution_left_2](../figures/picross-puzzle/5x5_solution_left_2.png)

They only satisfy the left clue, and we call such a black-white pattern "**Pattern 0**" hereafter.

Similarly, let **Pattern 1** be a black-white pattern that only satisfies the top hint.

If the color of each square in **Pattern 0** matches that of **Pattern 1**, then both the top and left clues are satisfied at the same time, and the Picross puzzle is completed.

Therefore, to solve the puzzle, the following conditions must be satisfied:

- **Condition (i):** **Pattern 0** and **Pattern 1** match,

- **Condition (ii):** Each of the vertical columns and horizontal rows fulfills the corresponding clue.

<a id="1_3"></a>
### 1.3\. Terms and pattern expressions

<a id="1_3_1"></a>
#### 1.3.1\. First-black, Last-Black

Let us take a sequence from a Picross puzzle as follows.

![single_row_2_3](../figures/picross-puzzle/single_row_2_3.png)

Now we define **First-Black** and **Last-Black** for the segment with consecutive black squares as follows.

- **First-Black** square in the segment is a black square where the previous square if it exists, is filled in white. (orange box in the figure below)

- **Last-Black** square in the segment is a black square where the next square is filled in white if it exists. (green box in the figure below)


![single_row_2_3_highlighted](../figures/picross-puzzle/single_row_2_3_highlighted.png)

Using these terms, **Condition (ii)** introduced in the previous section can be seen as the following constraints, focusing on the part of the transition from one previous square to the next.

- **(ii-a)** Each square is always filled either in black or white.

- **(ii-b)** The square after a white one is either white or **First-Black** square.

- **(ii-c)** The square before the white one is white or **Last-Black** square.

- **(ii-d)** The square following a black square other than **Last-Black** is also black one.

By properly imposing the above constraints, Picross can be completed using Ising and quantum annealing machines.

<a id="1_3_2"></a>
#### 1.3.2\. State of the squares

Now each square is simply represented as either white or black, but we define more detailed states to allow for the formulation of constraints.

1. Define the state of a black square by what number of black square it is.  
  For example, if the clue is given as `2 3`, the state of each black square is defined as follows:

  ![single_row_2_3_black_state_id](../figures/picross-puzzle/single_row_2_3_black_state_id.png)

2. Define the state of a white square by the number of black squares that have appeared so far.  
For example, if the clue is given as `2 3`, the state of each white square is defined as follows:

  ![single_row_2_3_white_state_id](../figures/picross-puzzle/single_row_2_3_white_state_id.png)

3. Integrate the defined states for white and black squares in order of appearance.  
For example, if the clues are given as `2 3`, the state of each square is defined as follows

  ![single_row_2_3_black_white_state_id](../figures/picross-puzzle/single_row_2_3_black_white_state_id.png)  

  Defining the state of each square in this way, and denoting the $i$-th clue in each Picross sequence as $h_i$, we can write the total number of states $W$ as $W=1+\sum_i (h_i + 1)$. For example, in the above picross sequence with `2 3` given as a hint, $h_1=2, h_2=3$ and we get $W=8$ as the total number of states.

<a id="1_3_3"></a>
#### 1.3.3\. Matrix representation of coloring

For example, suppose the following coloring is attempted for a Picross sequence with hints `2 3`.

![single_row_2_3_black_white_state_id](../figures/picross-puzzle/single_row_2_3_black_white_state_id.png)

In order to systematically represent this coloring, the following method can be considered.

- The colors of the $i$-th square can be represented in the following table.

<div align="center">

Table 1: Color of the $i$-th square in the sequence (W: white and B: black).

| $i$-th | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| **Color** | W | W | B | B | W | W | B | B | B | W |

</div>

- Using a binary variable matrix, we can also represent the color and state of square $i$.

<div align="center">

Table 2: Color and state of the square $i$ (W: white and B: black).

| $i$-th | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| **W (State ①)** | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **B (State ②)** | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **B (State ③)** | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| **W (State ④)** | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 |
| **B (State ⑤)** | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| **B (State ⑥)** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| **B (State ⑦)** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| **W (State ⑧)** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |

</div>

As shown above, for a given coloring pattern, the color and state of a Picross sequence can be represented by a matrix.

<a id="2"></a>
## 2\. Formulating the Picross solution

Here, we formulate the specific conditions necessary for the Picross solution described in Section 1. The constants and variables that appear in the formulation are as follows (including the constants and variables already introduced):

**Constants**
- $V$ : the number of vertical squares in the Picross matrix
- $H$ : the number of horizontal squares in the Picross matrix
- $N$ : the number of squares in a sequence
- $h_i$ : the $i$-th clue for a sequence
- $W$ : the number of states ($= 1 + \sum_i (h_i+1)$)
- $s_i$ : the state $i$ ($i \in \{1, \dots, W\}$)
- $S_{\rm{white}}, S_{\rm{black}}$ : set of white states and set of black states ($s_i$ always belongs to either $S_{\rm{white}}$ or $S_{\rm{black}}$)

**Variables**
- $q^{(m)}_{i,j} \in \{0, 1\} \quad (i \in \{1, \dots, V\})$ $\quad (j \in \{1, \dots, H\})$  

  Color of the square in the $i$-th row and $j$-th column (see Table 1). $q^{(0)}$ indicates **Pattern 0** satisfying only the left hint, and $q^{(1)}$ indicates **Pattern 1** satisfying only the top hint. For instance, if the square in row $i$ and column $j$ is black, $q_{i,j}=1$; if it is white, $q_{i,j}=0$.

- $p_{i,j} \in \{0, 1\} \quad (i \in \{1, \dots, N\}) \quad (j \in \{1, \dots, W\})$  
  State of square $i$ (see Table 2). If the state of the square $i$ is $j$, $p_{i,j}=1$, otherwise $p_{i,j}=0$.

Based on these constants and variables, we will formulate each constraint introduced in Section 1.

<a id="2_1"></a>
### 2.1\. Initial value constraints

To solve a Picross, we search for various states for each row and column. In other words, during the search, a binary variable matrix (e.g., Table 2) corresponding to the different states is evaluated for each Picross sequence.

![single_row_2_3_black_white_state_id](../figures/picross-puzzle/single_row_2_3_black_white_state_id.png)

In the above Picross sequence example given the `2 3` clue, the number of possible states is $W=1 + \sum_i (h_i+1)=8$, and the leftmost square ($i=1$) must take one of the following states:

- state ① (when the first square of the sequence starts with white), or
- State ② (when the sequence starts with **First-Black**, and there is no state ① with white)

The first square ($i=1$) of the sequence cannot be in state ③ or ④.

Similarly, the second square from the left ($i=2$) can take the states ①, ②, and ③, as shown in the figure below. Conversely, it will never take a larger state.

![single_row_2nd_left_state](../figures/picross-puzzle/single_row_2nd_left_state.png)

In this way, the binary variable matrix can be zero-padded to account for states that the square $i$ can never take. For example, the Picross sequence above can be zero-padded as follows:

<div align="center">

Table 3: Color and state of square $i$ after zero-padding (W: white, B: black).

| $i$-th | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| **W (State ①)** |  |  |  |  | 0 | 0 | 0 | 0 | 0 | 0 |
| **B (State ②)** |  |  |  |  |  | 0 | 0 | 0 | 0 | 0 |
| **B (State ③)** | 0 |  |  |  |  |  | 0 | 0 | 0 | 0 |
| **W (State ④)** | 0 | 0 |  |  |  |  |  | 0 | 0 | 0 |
| **B (State ⑤)** | 0 | 0 | 0 |  |  |  |  |  | 0 | 0 |
| **B (State ⑥)** | 0 | 0 | 0 | 0 |  |  |  |  |  | 0 |
| **B (State ⑦)** | 0 | 0 | 0 | 0 | 0 |  |  |  |  |  |
| **W (State ⑧)** | 0 | 0 | 0 | 0 | 0 | 0 |  |  |  |  |

</div>

In this way, we can restrict the way the Picross sequence takes states, thereby limiting the scope of the search in the solution method. We call this constraint an initial value constraint, which is realized by zero-padding the binary variable matrix representing the states of the squares. The formulation of the initial value constraint can be implemented as follows, by using the variable $p_{i,j}$, which represents the state of the square $i$ of a Picross sequence.

$$
\left\{
    \begin{align*}
        &\begin{split}
            &p_{i, j} = 0 \quad (j > i+1)
        \end{split}\\
        &\begin{split}
            &p_{i, j} = 0 \quad (W-j > N-i+1)
        \end{split}\\
    \end{align*}
\right\},
$$

where $i \in \{1, ... , N\}, j \in \{1, ... , W\}$. As an exercise, see if you can constrain the initial values if $N = 5$ and $W=8$ as in Table 3.


<a id="2_2"></a>
### 2.2\. Transition constraints


The transition constraints have already been introduced in [1.3.1\. First-Black, Last-Black](#1_3_1) as **(ii-a)** to **(ii-d)**. In this section, we formulate this transition constraint. We will use the following Picross sequence example described above:

![single_row_2_3_black_white_state_id](../figures/picross-puzzle/single_row_2_3_black_white_state_id.png)

Using the state of each square, the conditions **(ii-a)** to **(ii-d)** for the transition from one previous square to the next, already introduced, can be described in more detail as follows.

- **(ii-a')** Each square takes one state.

- **(ii-b')** If the $i$-th square is in the state $j$ and the state $j$ is white, then the $i+1$-th square is in the state $j$ (white) or the state $j+1$ (**First-Black**).  

  Example: If the $i$-th square is in the state ④ (white), then the $i+1$-th square is in the state ④ (white) or the state ⑤ (**First-Black**).

- **(ii-c')** If the $i$-th square is in the state $j$ and the state $j$ is white, the $i-1$-th square is in the state $j$ (white) or the state $j-1$ (**Last-Black**).  

  Example: If the $i$-th square is in the state ④ (white), then the $i-1$-th square is in the state ④ (white) or the state ③ (**Last-Black**).

- **(ii-d')** If the $i$-th square is in the state $j$ (black) ($\neq$ **Last-Black**), the $i+1$-th square is in the state $j+1$ (black).  

  Example: If the $i$-th square is in the state ⑤ (black), the $i+1$-th square is in the state ⑥ (black).

Corresponding to these transition constraints, the following holds for $i \in \{1, ... , N\}$:

- **(ii-a')** $\quad \sum_j p_{i,j}=1$

- **(ii-b')** $\quad p_{i, j} \land (1-p_{i+1, j}) = p_{i+1, j+1} \quad (\forall j \neq W, s_j \in S_{\rm{white}})$

- **(ii-c')** $\quad p_{i, j} \land (1-p_{i-1, j}) = p_{i-1, j-1} \quad (\forall j \neq 1, s_j \in S_{\rm{white}})$

- **(ii-d')** $\quad p_{i, j} = p_{i+1, j+1} \quad (\forall j, \{s_j, s_{j+1}\} \subset S_{\rm{black}})$

<a id="2_3"></a>
### 2.3\. Matching constraints

In [1.2\. Outline of Picross Solution Method](#1_2), we have introduced the following condition.

> - **Condition (i):** **Pattern 0** and **Pattern 1** match.

This can be stated more rigorously as follows:  

- For any Picross matrix square $i,j$, the $(i,j)$ square of **Pattern 0** and the $(i,j)$ square of **Pattern 1** are both black, or both white. To formulate this, we have for $i \in \{1, ... , V\}, j \in \{1, ... , H\}$,

- **(i')** $\quad q^{(0)}_{i,j} = q^{(1)}_{i,j}$

as the matching constraints.

<a id="2_4"></a>
### 2.4\. Constraints linking color and state

In the transition constraints, we defined constraints for a single Picross sequence. In the actual Picross, there are $V$ rows and $H$ columns, so we need to formulate for $H+V$ sequences. Therefore, we add a superscript to the variables to have two pieces of information: whether it is based on a top or left hint, and what number Picross sequence it points to. Specifically, the superscript is $(a,b)$, where $a$ indicates a left hint when $a$ is $0$ and a top hint when $a$ is $1$. Also, $b$ indicates what number of the Picross sequence it is from the top or left.

Using these notations, we can formulate constraints on the relationship between $q^{(m)}_{i,j}$ (the color of the square at position $i, j$, **Pattern $m$**) and $p_{i,k}^{(a,b)}$ (the state $k$ of square $i$) in a Picross sequence $(a,b)$ as follows.


- **Constraint (iii)**
$$
\begin{align*}
    \sum_{k| s^{(0, j)}_k \in S^{(0, j)}_{\rm{black}}} p^{(0, j)}_{i, k} = q^{(0)}_{i,j}
\end{align*}
$$

$$
\begin{align*}
    \sum_{k| s^{(1, i)}_k \in S^{(1, i)}_{\rm{black}}} p^{(1, i)}_{j, k} = q^{(1)}_{i,j}
\end{align*}
$$

Here, $i \in \{1, ... , H\}, j \in \{1, ... , V\}$.

<a id="3"></a>
## 3\. Implementing Picross solution

Now, based on the constraints we have formulated so far, let us implement the Picross solution method using *Amplify*.

<a id="3_1"></a>
### 3.1\. Picross matrix plotting function

First, we define the function `plot_solution` to plot the Picross matrix (and the solution).


```python
import matplotlib.pyplot as plt
import numpy as np


def plot_solution(v_hints, h_hints, solution=np.zeros((0, 0))):
    if solution.shape[0] == len(v_hints) and solution.shape[1] == len(h_hints):
        solution = solution
    else:
        solution = np.zeros((len(h_hints), len(v_hints)))

    _, ax = plt.subplots()
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
    # Major tick
    ax.set_xticks(np.arange(len(h_hints)))
    ax.set_yticks(np.arange(len(v_hints)))
    # Minor tick
    ax.set_xticks(np.arange(-0.5, len(h_hints), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(v_hints), 1), minor=True)
    # Label for the major ticks
    ax.set_xticklabels(["\n".join(map(str, hint)) for hint in h_hints])
    ax.set_yticklabels(["  ".join(map(str, hint)) for hint in v_hints])
    ax.set_xlim([-0.5, len(h_hints) - 0.5])
    ax.set_ylim([len(v_hints) - 0.5, -0.5])
    ax.set_title(f"{len(h_hints)} x {len(v_hints)}", fontsize=20, pad=20)
    # Grid based on the minor ticks
    ax.grid(which="minor", color="#aaaaaa", linestyle="-", linewidth=1)
    return plt.show()
```

Also, using `plot_solution`, let us create and draw a Picross problem introduced in [1.1\. Picross rules](#1_1).

Now the groundwork for the Picross solution implementation is ready.


```python
# Describe the left and top hints using list.
# Left hints
left_hints = [[5], [1], [5], [1], [5]]
# Top hints
top_hints = [[3, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 3]]

# Vertical and horizontal sizes of the Picross matrix
v_len, h_len = len(left_hints), len(top_hints)

# Plot the Picross problem defined above
plot_solution(left_hints, top_hints, np.zeros((v_len, h_len)))
```

<a id="3_2"></a>
### 3.2\. Implementation of constraint equations

<a id="3_2_1"></a>
#### 3.2.1\. Decision variables

Next, we define the required decision variables using Amplify's `BinarySymbolGenerator`.

Define a two-dimensional array `q` representing the colors of the squares, each of which is located at $i,j$, in the Picross matrix. As in $q^{(m)}_{i,j}$ introduced in [Picross solution formulation](#2), we define an array with left and top hints. The values 0 and 1 correspond to white and black, respectively.


```python
from amplify import BinarySymbolGenerator

gen = BinarySymbolGenerator()

# Color of square (i,j) on the Picross matrix based on the left hints
q_from_left_hints = gen.array(v_len, h_len)
# Color of square (i,j) on the Picross matrix based on the top hints
q_from_top_hints = gen.array(h_len, v_len)
```

In addition, for each Picross sequence, we define a two-dimensional array `p`, which is ("number of squares" x "number of states"). Each square is associated with one state. As in $p_{i,k}^{(a,b)}$ described in [2.4\. Constraints linking color and state](#2_4), we define arrays with left hints `left_hints` and top hints `top_hints`, respectively.


```python
# Create a variable for each of the left and top clues
# Two-dimensional array of "number of squares" and "number of states"
p_from_left_hints = [gen.array(h_len, sum(hint) + len(hint) + 1) for hint in left_hints]
p_from_top_hints = [gen.array(v_len, sum(hint) + len(hint) + 1) for hint in top_hints]
```

<a id="3_2_2"></a>
#### 3.2.2\. Implementation - initial value constraints

As described in [2.1\. Initial Value Constraints](#2_1), the zero-padding of the binary variable matrix is implemented as follows.

$$
\left\{
    \begin{align*}
        &\begin{split}
            &p_{i, j} = 0 \quad (j > i+1)
        \end{split}\\
        &\begin{split}
            &p_{i, j} = 0 \quad (W-j > N-i+1)
        \end{split}\\
    \end{align*}
\right.
$$


```python
def assign_init_value(p):
    n = p.shape[0]
    for i in range(n):
        # Initial value constraints: zero-padding in states that each square cannot take.
        p[i, i + 2 :] = 0
        p[-i - 1, : -i - 2] = 0
```

<a id="3_2_3"></a>
#### 3.2.3\. Implementation - transition constraints

Transition constraints are already introduced in [2.2\. Transition Constraints](#2_2), and they consist of four constraints in total. These will be implemented one by one below.

##### **(ii-a')**

> Each square takes one state.

$$
\quad \sum_j p_{i,j}=1
$$


```python
from amplify.constraint import equal_to
from amplify import sum_poly


def make_state_constraint(p):
    state_constraints = []
    # Transition constraints (ii-a'): each square takes one state.
    n = p.shape[0]
    w = p.shape[1]
    for j in range(n):
        c = sum_poly(w, lambda k: p[j, k])
        state_constraints.append(equal_to(c, 1))
    return state_constraints
```

##### **(ii-b')**
> If the $i$-th square is in the state $j$ and the state $j$ takes white, then the $i+1$-th square is in the state $j$ (white) or the state $j+1$ (**First-Black**).

$$
\quad p_{i, j} \land (1-p_{i+1, j}) = p_{i+1, j+1} \quad (\forall j \neq W, s_j \in S_{\rm{white}})
$$

We implement this constraint using Amplify's [penalty function](https://amplify.fixstars.com/ja/docs/constraint.html#id12). First, the left-hand side of the above equation is transferred to the right-hand side and both sides are squared. The logical conjunction $\land$ can be converted to multiplication. This right-hand side can be implemented as the penalty $P_b$ for this constraint: 

$$
\quad P_b = \left[ p_{i, j} (1-p_{i+1, j}) - p_{i+1, j+1}\right]^2 \quad (\forall j \neq W, s_j \in S_{\rm{white}}).
$$

We see that only set of $(p_{i,j}, p_{i+1,j}, p_{i+1,j+1})$ yielding $P_b=0$ satisfies this constraint.

Expanding the above equation, we obtain:

$$
P_b = -p_{i,j}p_{i+1,j} - 2p_{i,j}p_{i+1,j+1} + 2\:{\color{red} p_{i,j}} \:p_{i+1,j}p_{i+1,j+1} + p_{i,j} + p_{i+1,j+1} \quad (\forall j \neq W, s_j \in S_{\rm{white}}).
$$

Here, the above equation is treated as a penalty, and for a set of $(p_{i,j}, p_{i+1,j}, p_{i+1,j+1})$ that yields $P_b \neq 0$, $P_b$ does not need to be calculated exactly as long as the resulting $P_b \neq 0$. Based on this idea, we can omit the term in red-colored font in the above equation, and avoid the use of [third-order terms that require the introduction of auxiliary variables](https://amplify.fixstars.com/ja/docs/model.html#id2).

Finally, $P_b$ in the case of $$j\neq W$$ is,

$$
P_b = -p_{i,j}p_{i+1,j} - 2p_{i,j}p_{i+1,j+1} + 2p_{i+1,j}p_{i+1,j+1} + p_{i,j} + p_{i+1,j+1} \quad (\forall j \neq W, s_j \in S_{\rm{white}})
$$

Also, if $j=W$, the above equation is reduced to:

$$
P_b = -p_{i,j}p_{i+1,j} + p_{i,j} \quad (j=W, s_j \in S_{\rm{white}})
$$

These two equations are implemented as a penalty function with respect to the white squares (to make $P_b$ take a value as close to 0 as possible) as follows.


```python
from amplify.constraint import penalty


def make_white_constraint_forward(p, hint):
    white_constraints = []

    # Keep the index of the white state
    s_white_indexes = {0}
    cursor = 0
    for h in hint:
        s_white_indexes.add(cursor + 1 + h)
        cursor = cursor + 1 + h

    # Transition constraint (ii-b'): if the i-th square is in the state j and the state j takes white, then the (i+1)-th square is in the state j (white) or the state (j+1) (First-Black).
    n = p.shape[0]
    w = p.shape[1]
    for i in range(n - 1):
        for j in s_white_indexes:
            if j == w - 1:
                c = -p[i, j] * p[i + 1, j] + p[i, j]
            else:
                c = (
                    -p[i, j] * p[i + 1, j]
                    - 2 * p[i, j] * p[i + 1, j + 1]
                    + 2 * p[i + 1, j] * p[i + 1, j + 1]
                    + p[i, j]
                    + p[i + 1, j + 1]
                )
            white_constraints.append(penalty(c))

    return white_constraints
```

##### **(ii-c')** 

> If the $i$-th square is in the state $j$ and the state $j$ is white, the $i-1$-th square is in the state $j$ (white) or the state $j-1$ (**Last-Black**).  

$$
\quad p_{i, j} \land (1-p_{i-1, j}) = p_{i-1, j-1} \quad (\forall j \neq 1, s_j \in S_{\rm{white}})
$$

This transition constraint is also implemented by expanding the expression in the same way as **(ii-b')** above and using Amplify's penalty function.

Therefore, the penalty $P_c$ of this transition constraint is:

$$
P_c = -p_{i,j}p_{i-1,j} - 2p_{i,j}p_{i-1,j-1} + 2p_{i-1,j}p_{i-1,j-1} + p_{i,j} + p_{i-1,j-1}  \quad (\forall j \neq 1, s_j \in S_{\rm{white}})
$$

$$
P_c = -p_{i,j}p_{i-1,j} + p_{i,j}  \quad (j=1, s_j \in S_{\rm{white}})
$$



```python
def make_white_constraint_backward(p, hint):
    last_black_constraints = []

    # Keep the index of the white state
    s_white_indexes = {0}
    cursor = 0
    for h in hint:
        s_white_indexes.add(cursor + 1 + h)
        cursor = cursor + 1 + h

    # Transition constraints (ii-c'): if the i-th square is in the state j and the state j is white, the (i-1)-th square is in the state j (white) or the state j-1 (Last-Black).
    n = p.shape[0]
    for i in range(1, n):
        for j in s_white_indexes:
            if j == 0:
                c = -p[i, j] * p[i - 1, j] + p[i, j]
            else:
                c = (
                    -p[i, j] * p[i - 1, j]
                    - 2 * p[i, j] * p[i - 1, j - 1]
                    + 2 * p[i - 1, j] * p[i - 1, j - 1]
                    + p[i, j]
                    + p[i - 1, j - 1]
                )
            last_black_constraints.append(penalty(c))

    return last_black_constraints
```


##### **(ii-d')** 

> If the $i$-th square is in the state $j$ (black) ($\neq$ **Last-Black**), the $i+1$-th square is in the state $j+1$ (black).  

$$
\quad p_{i, j} = p_{i+1, j+1} \quad (\forall j, \{s_j, s_{j+1}\} \subset S_{\rm{black}})
$$


```python
def assign_black_forward(p, hint):
    # Keep the index of the black state
    s_black_indexes = set()
    cursor = 0
    for h in hint:
        s_black_indexes |= set(range(cursor + 1, cursor + 1 + h))
        cursor += h + 1

    # Transition constraints (ii-d'): if the i-th square is in the state j (black) (!= Last-Black), the (i+1)-th square is in the state (j+1) (black).
    n = p.shape[0]
    w = p.shape[1]
    for i in range(n - 2, -1, -1):
        for j in range(w - 2, -1, -1):
            if j in s_black_indexes and j + 1 in s_black_indexes:
                p[i, j] = p[i + 1, j + 1]
```

<a id="3_2_4"></a>
#### 3.2.4\. Implementation - matching constraints

The matching constraints introduced in [2.3\. Matching constraints](#2_3) for **Pattern 0** based on the left hint and **Pattern 1** based on the above hint, are implemented as follows:

$$
\quad q^{(0)}_{i,j} - q^{(1)}_{i,j} = 0.
$$



```python
def equal_constraints(q_left, q_top, v_len, h_len):
    constraints = []
    for y in range(v_len):
        for x in range(h_len):
            # Matching constraints for "Pattern 0" and "Pattern 1".
            c = q_left[y, x] - q_top[x, y]
            constraints.append(equal_to(c, 0))

    return sum(constraints)
```

<a id="3_2_5"></a>
#### 3.2.5\. Implementation - Constraints linking color and state

[2.4\. Constraints linking color and state](#2_4) are expressed by the following equations:

- **Constraints (iii)**
$$
\begin{align*}
    \sum_{k| s^{(0, j)}_k \in S^{(0, j)}_{\rm{black}}} p^{(0, j)}_{i, k} = q^{(0)}_{i,j}
\end{align*}
$$

$$
\begin{align*}
    \sum_{k| s^{(1, i)}_k \in S^{(1, i)}_{\rm{black}}} p^{(1, i)}_{j, k} = q^{(1)}_{i,j}
\end{align*}
$$

Here, in terms of implementation, the smaller the number of variables are, the faster the solution can be obtained by annealing. In Picross, if the size of the Picross matrix is large enough, the number of white states is considered to be substantially greater than the number of black states. To reduce the number of variables to be referenced, the following equations are used. (synonymous with the above equation).

- **Constraints (iii')**
$$
\begin{align*}
    \sum_{k| s^{(0, j)}_k \in S^{(0, j)}_{\rm{white}}} p^{(0, j)}_{i, k} = 1-q^{(0)}_{i,j}
\end{align*}
$$

$$
\begin{align*}
    \sum_{k| s^{(1, i)}_k \in S^{(1, i)}_{\rm{white}}} p^{(1, i)}_{j, k} = 1-q^{(1)}_{i,j}
\end{align*}
$$


```python
def assign_state_color_link(q, p, hint):
    n = q.shape[0]
    for j in range(n):
        # Keep the index of the white state
        s_white_indexes = {0}
        cursor = 0
        for h in hint:
            s_white_indexes.add(cursor + 1 + h)
            cursor = cursor + 1 + h

        # (iii') Constraints linking color and state
        eq = 1 - sum_poly(s_white_indexes, lambda k: p[j, k])
        q[j] = eq
```

<a id="3_3"></a>
### 3.3\. Amplify client configuration

We create an Amplify client for Ising and Quantum Annealing machines.


```python
from amplify.client import FixstarsClient

client = FixstarsClient()
client.parameters.timeout = 1000  # Timeout: 1s
# client.token = "Please put your Amplify API Token"
```

<a id="3_4"></a>
### 3.4\. Running the Picross solver

First, add up all the constraints implemented above.


```python
# Transition constraints: (ii-a'), (ii-b'), (ii-c')
state_constraints = []
white_constraints = []
last_black_constraints = []
for p, hint in zip(p_from_left_hints, left_hints):
    state_constraints += make_state_constraint(p)
    white_constraints += make_white_constraint_forward(p, hint)
    last_black_constraints += make_white_constraint_backward(p, hint)
left_constraints = (
    sum(state_constraints) + sum(white_constraints) + sum(last_black_constraints)
)

state_constraints = []
white_constraints = []
last_black_constraints = []
for p, hint in zip(p_from_top_hints, top_hints):
    state_constraints += make_state_constraint(p)
    white_constraints += make_white_constraint_forward(p, hint)
    last_black_constraints += make_white_constraint_backward(p, hint)
top_constraints = (
    sum(state_constraints) + sum(white_constraints) + sum(last_black_constraints)
)

# Picross sequences based on the left hints
for q, p, hint in zip(q_from_left_hints, p_from_left_hints, left_hints):
    # Initial value constraints
    assign_init_value(p)
    # Transition constraints: (ii-d')
    assign_black_forward(p, hint)
    # Constraints linking color and state: (iii')
    assign_state_color_link(q, p, hint)

# Picross sequences based on the top hints
for q, p, hint in zip(q_from_top_hints, p_from_top_hints, top_hints):
    # Initial value constraints
    assign_init_value(p)
    # Transition constraints: (ii-d')
    assign_black_forward(p, hint)
    # Constraints linking color and state: (iii')
    assign_state_color_link(q, p, hint)

# Matching constraints
eq_constraints = equal_constraints(q_from_left_hints, q_from_top_hints, v_len, h_len)

# Add up all constraints constructed above
constraints = left_constraints + top_constraints + eq_constraints * 2
```

In this addition for `constraints`, only `eq_constraints` is multiplied by two for the following reasons.

Each of `left_constraints` and `top_constraints` considers transition constraints (ii-a'), (ii-b'), and (ii-c'). This means that the transition constraints (ii-a'), (ii-b'), and (ii-c') are added together twice, once for **Pattern 0** based on the left hint and once for **Pattern 1** based on the top hint.

On the other hand, the matching constraints implemented in `eq_constraints` do not need to be added twice, since they assume that the elements inferred from the left hint and the top hint are equal. Therefore, we can assume that the intensity of the constraints is (approximately) half that of the transition constraints (ii-a'), (ii-b'), and (ii-c').

Therefore, by adding double weights to the matching constraints and adjusting the intensities of these constraints, it is considered that the formulation is solvable by Ising and quantum annealing machines.

By giving the constraints `constraints` to `BinaryQuadraticModel`, formulate them as a logical model class, which is then given to the `solver` you just set up, and execute the solver. The solution is plotted by `plot_solution`.


```python
from amplify import Solver, BinaryQuadraticModel

# Create an Amplify solver with the previously instantiated client
solver = Solver(client)

model = BinaryQuadraticModel(constraints)
result = solver.solve(model)
if len(result.solutions) == 0:
    raise RuntimeError("No solution was found")

values = result.solutions[0].values
```


```python
solution = q_from_left_hints.decode(values)
plot_solution(left_hints, top_hints, solution)
```

<a id="4"></a>
# Advanced: Tuning

To make larger problems solvable, the number of variables must be reduced. In the solution methods mentioned above, [3.2.2\. Implementation - initial value constraints](#3_2_2) and [3.2.3\. Inplementation - transition constraints](#3_2_3) **(ii-d')**, and [3.2.4\. Implementation - matching constraints](#3_2_4) reduced the number of variables to be searched by pre-assigning variables.

The matching constraints are implemented using `equal_to`. Here we consider further reducing the number of variables by resolving the constraint expressions of some elements in the matching constraints by assignment.

For a larger scale problem, the below 15x15 picross puzzle is used.


```python
# Describe the left and top hints using list.
left_hints = [
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
top_hints = [
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

v_len, h_len = len(left_hints), len(top_hints)

plot_solution(left_hints, top_hints, np.zeros((v_len, h_len)))
```

Define variables similar to the 5x5 problem (see [3.2.1\. Decision variables](#3_2_1)).


```python
gen = BinarySymbolGenerator()

# Color of square (i,j) on the Picross matrix based on the left hints
q_from_left_hints = gen.array(v_len, h_len)
# Color of square (i,j) on the Picross matrix based on the top hints
q_from_top_hints = gen.array(h_len, v_len)

# Create a variable for each of the left and top clues
# Two-dimensional array of "number of squares" and "number of states"
p_from_left_hints = [gen.array(h_len, sum(hint) + len(hint) + 1) for hint in left_hints]
p_from_top_hints = [gen.array(v_len, sum(hint) + len(hint) + 1) for hint in top_hints]
```

For the defined variables, the initial value constraints, transition constraints **(ii-d')**, and constraints to link color and state **(iii')** are applied, and assignments are performed to the variables.


```python
# Picross sequences based on the left hints
for q, p, hint in zip(q_from_left_hints, p_from_left_hints, left_hints):
    # Initial value constraints
    assign_init_value(p)
    # Transition constraints: (ii-d')
    assign_black_forward(p, hint)
    # Constraints linking color and state: (iii')
    assign_state_color_link(q, p, hint)

# Picross sequences based on the top hints
for q, p, hint in zip(q_from_top_hints, p_from_top_hints, top_hints):
    # Initial value constraints
    assign_init_value(p)
    # Transition constraints: (ii-d')
    assign_black_forward(p, hint)
    # Constraints linking color and state: (iii')
    assign_state_color_link(q, p, hint)
```

For polynomials of type `BinaryPoly`, the `asdict()` function can be used to split the polynomial terms. Here, the `asdict()` function is used to identify matching constraints with only two or fewer terms and to rewrite the identified constraints as assignments to variables. This process further reduces the number of variables and the number of constraint conditions.

In other words, if the matching constraint equation $q^{(0)}_{i,j} - q^{(1)}_{i,j}=0$ is satisfied, the $i,j$ component of the **Pattern 0** based on the left hint may be $q^{(1)}_{i,j}$ instead of $q^{(0)}_{i,j}$ (and vice versa). By doing so, we see that we can reduce the variables corresponding to the $i,j$ components of the matrix from two to one based on the left and top hints.

Note that the matching constraint equation $q^{(0)}_{i,j} - q^{(1)}_{i,j}$ does not necessarily have only two terms, since the initial value constraint, the transition constraint **(ii-d')**, and the assignment (`assign_*`) by the constraint to link color and state **(iii')** have already been performed above.

Therefore, we first identify matching constraints that have only two or fewer terms, and only for such constraints, we store the polynomial pairs that are equationally connected to the variables to be assigned in `substitute_dicts`, and match (assign) `q_from_left_hints` and `q_from_top_hints` to reduce the number of variables.


```python
substitute_dicts = dict()
for x in range(h_len):
    for y in range(v_len):
        c_dict = (q_from_left_hints[y, x] - q_from_top_hints[x, y]).asdict()
        for k, v in c_dict.items():
            if len(k) == 0:
                continue
            # Keep the pairs in substitute_dicts
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
            # Assignment to substitute_dicts happens only when the polynomial coefficient, d, satisfies 0 <= d <= 1.
            if d_min < 0 or d_max > 1:
                continue
            substitute_dicts[k] = d
            # Match q_from_left_hints and q_from_top_hints
            if k in q_from_left_hints[y, x].asdict():
                q_from_left_hints[y, x] = q_from_top_hints[x, y]
            else:
                q_from_top_hints[x, y] = q_from_left_hints[y, x]
            break
```

Next, reflect the contents of `substitute_dicts` (pairs of polynomials that are equationally related to the variable to be assigned) to `p_from_left_hints` and `p_from_top_hints`.


```python
from amplify import BinaryPoly


def substitute_according_to_dicts(p, substitute_dicts):
    for j in range(p.shape[0]):
        for k in range(p.shape[1]):
            d = p[j, k].asdict()
            if len(d) == 0:
                continue
            key, _ = d.popitem()
            if key in substitute_dicts:
                p[j, k] = BinaryPoly(substitute_dicts[key])


for p in p_from_left_hints:
    substitute_according_to_dicts(p, substitute_dicts)

for p in p_from_top_hints:
    substitute_according_to_dicts(p, substitute_dicts)
```

After reducing the number of variables as described above, constraints are created as in the previous implementation of the formulation.


```python
# Transition constraints: (ii-a'), (ii-b'), (ii-c')
state_constraints = []
white_constraints = []
last_black_constraints = []
for p, hint in zip(p_from_left_hints, left_hints):
    state_constraints += make_state_constraint(p)
    white_constraints += make_white_constraint_forward(p, hint)
    last_black_constraints += make_white_constraint_backward(p, hint)
left_constraints = (
    sum(state_constraints) + sum(white_constraints) + sum(last_black_constraints)
)

state_constraints = []
white_constraints = []
last_black_constraints = []
for p, hint in zip(p_from_top_hints, top_hints):
    state_constraints += make_state_constraint(p)
    white_constraints += make_white_constraint_forward(p, hint)
    last_black_constraints += make_white_constraint_backward(p, hint)
top_constraints = (
    sum(state_constraints) + sum(white_constraints) + sum(last_black_constraints)
)

# Matchi constraints
eq_constraints = equal_constraints(q_from_left_hints, q_from_top_hints, v_len, h_len)

constraints = left_constraints + top_constraints + eq_constraints * 2
```

Since the problem size has increased, set a larger timeout for the previously created client and then reconstruct the solver.


```python
client.parameters.timeout = 10000  # Timeout 10 s
solver = Solver(client)
```

By passing the constraints `constraints` to `BinaryQuadraticModel`, we formulate them as a logical model class, which is then passed to the `solver` previously set up, and run the solver.


```python
model = BinaryQuadraticModel(constraints)
result = solver.solve(model)
if len(result.solutions) == 0:
    raise RuntimeError("No solution was found")

values = result.solutions[0].values
```

Pass the solution `values` to the `decode` member function of the variable array `q_from_left_hints` and assign the result to the variable array `solution`. The `plot_solution` function is then used to plot the solution.


```python
solution = q_from_left_hints.decode(values)
plot_solution(left_hints, top_hints, solution)
```
