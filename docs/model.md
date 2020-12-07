---
marp: true
theme: gaia
_class: lead
backgroundColor: #fff
---


# **Santa 2019**

### MIP

---
## Assumptions

- All the families can be assigned to one of their choices.

---
## Indices

- $d$: days
- $f$: families
- $o$: occupancy level, $MIN_O \le o \le MAX_O$
- $k$: occupancy difference between consecutive days

---
## Sets

- $D$: days
- $F$: families
- $D(f)$: choices of family $f$
- $K$: possible difference of occupancy between consecutive days

---
## Parameters

- $MIN_O$: Minimum daily occupancy (125)
- $MAX_O$: Maximum daily occupancy (300)
- $c_{fd}$: Cost of assigning family $f$ to $d$
- $n_f$: Number of members of $f$


---
## Variables

- $X_{fd}$: If family $f$ is assigned to $d$
- $\delta_{od}$: If family $o$ is the occupancy level in $d$
- $\phi_{kd}$: If the difference between $d$ and $d+1$ is $k$
<!-- - $Z_{f}$: If family $f$ is not assigned, _i.e._ assigned to none of the choices -->
<!-- - $\phi_{d}$: If $n$ overflow/extra starting capacity is available on $d$
- $\gamma_{nd}$: If $n$ overflow/extra FTE is available on $d$
- $\delta_{cd}$: If crew $c$ is _conflicted_ on $d$ -->


---
## Constraints

- Assignment constraints 
<!-- $\sum_{d \in D(f)} X_{fd} + Z_f = 1 \quad \forall c \in C$ -->
$\sum_{d \in D(f)} X_{fd} = 1 \quad \forall c \in C$

- Occupancy consistency
$\sum_{MIN_O \le o \le MAX_O} \delta_{od} = 1 \quad \forall d \in D$


---
## Constraints (contd.)

- Occupancy levels
$\sum_{f \in F} X_{fd} * n_f = \sum_{MIN_O \le o \le MAX_O} o * \delta_{od} \quad \forall d \in D$

- Occupancy diff (non-linear)
$\sum_{(o, o') | k = |o-o'|} \delta_{od} * \delta_{o'd+1} \le \phi_{kd} \quad \forall d \in D, k \in K$

- Occupancy diff (linearized)
$\phi_{kd} \le \sum_{o | \exists (o,o') | k = |o-o'|} \delta_{od} \quad \forall d \in D, k \in K$
$\phi_{kd} \le \sum_{o' | \exists (o,o') | k = |o-o'|} \delta_{o'd+1} \quad \forall d \in D, k \in K$
$\phi_{kd} \ge \sum_{(o, o') | k = |o-o'|} (\delta_{od} + \delta_{o'd+1}) - 1 \quad \forall d \in D, k \in K$

---
## Objective

- Minimize costs 

$Min \quad \sum_{f \in F}\sum_{d \in D(f)} c_{fd} * X_{fd}$ + 